import os
import re
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

# load .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hotel_room_service")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

app = Flask(__name__)

# --- Helper functions -------------------------------------------------
def detect_dietary_prefs(text):
    """
    Very small heuristic detector for common preferences.
    Returns a list like ['vegetarian', 'vegan', 'gluten-free'].
    """
    prefs = []
    text_l = text.lower()
    # a few heuristics to catch typical mentions
    if ("vegetarian" in text_l or " veg " in text_l or text_l.strip().endswith(" veg")) and "non" not in text_l:
        prefs.append("vegetarian")
    if "vegan" in text_l:
        prefs.append("vegan")
    if "gluten" in text_l:
        prefs.append("gluten-free")
    if "dairy-free" in text_l or "lactose" in text_l:
        prefs.append("dairy-free")
    if "nut" in text_l:
        prefs.append("nut-free")
    return prefs

def find_candidate_items(text):
    """
    Simple word intersection + tag checks against menu items.
    Keeps rules readable so behavior is obvious during evaluation.
    """
    menu = list(db.menu.find({}))
    candidates = []
    words_in_text = set(re.findall(r"\w+", text.lower()))
    for item in menu:
        name = item.get("name", "").lower()
        name_words = set(re.findall(r"\w+", name))
        # match when any meaningful word intersects
        if len(name_words & words_in_text) >= 1:
            candidates.append(item)
            continue
        # match by tags explicitly mentioned
        for t in item.get("tags", []):
            if t.lower() in text.lower():
                candidates.append(item)
                break
        else:
            # fuzzy fallback: if a longer word from the item name appears in text
            long_words = [w for w in name_words if len(w) > 3]
            if any(w in text.lower() for w in long_words):
                candidates.append(item)
    return candidates

def dietary_conflict(item, prefs):
    """
    Return a list of conflicting preference keys.
    E.g., item tags do not include 'vegan' while prefs contains 'vegan'.
    """
    item_tags = set(item.get("tags", []))
    conflicts = []
    for p in prefs:
        if p == "vegan" and "vegan" not in item_tags:
            conflicts.append(p)
        if p == "vegetarian" and ("vegetarian" not in item_tags and "vegan" not in item_tags):
            conflicts.append(p)
        if p == "gluten-free" and "gluten-free" not in item_tags:
            conflicts.append(p)
        if p == "dairy-free" and "dairy-free" not in item_tags:
            conflicts.append(p)
        if p == "nut-free" and "nut-free" not in item_tags:
            conflicts.append(p)
    return list(set(conflicts))

# --- API endpoints ---------------------------------------------------
@app.route("/message", methods=["POST"])
def message():
    """
    POST JSON:
    {
      "conversation_id": "<optional>",
      "guest_id": "<optional>",
      "text": "I want pancakes"
    }
    """
    payload = request.get_json() or {}
    text = payload.get("text", "")
    if not text:
        return jsonify({"error": "empty text"}), 400

    conv_id = payload.get("conversation_id") or str(uuid.uuid4())
    guest_id = payload.get("guest_id", None)

    # load or create conversation record
    conv = db.conversations.find_one({"conversation_id": conv_id})
    if not conv:
        conv = {
            "conversation_id": conv_id,
            "guest_id": guest_id,
            "messages": [],
            "created_at": datetime.utcnow()
        }
        db.conversations.insert_one(conv)

    # store guest message
    db.conversations.update_one(
        {"conversation_id": conv_id},
        {"$push": {"messages": {"role": "guest", "text": text, "ts": datetime.utcnow()}}}
    )

    # detect prefs and find candidate items
    prefs = detect_dietary_prefs(text)
    candidates = find_candidate_items(text)

    # No candidates: ask a clarifying question
    if not candidates:
        reply = {
            "text": "Could you tell me which meal or dish you'd like? For example: 'Caesar salad', 'club sandwich', or 'pancakes'.",
            "need_clarify": True,
            "conversation_id": conv_id
        }
        db.conversations.update_one({"conversation_id": conv_id}, {"$push": {"messages": {"role": "agent", "text": reply['text'], "ts": datetime.utcnow()}}})
        return jsonify(reply)

    # Multiple candidates: ask which one
    if len(candidates) > 1:
        names = [c['name'] for c in candidates]
        reply_text = f"I found multiple items that match: {', '.join(names)}. Which one would you like?"
        reply = {"text": reply_text, "candidates": names, "need_clarify": True, "conversation_id": conv_id}
        db.conversations.update_one({"conversation_id": conv_id}, {"$push": {"messages": {"role": "agent", "text": reply_text, "ts": datetime.utcnow()}}})
        return jsonify(reply)

    # Single candidate: check conflicts and availability
    item = candidates[0]
    conflicts = dietary_conflict(item, prefs)
    if conflicts:
        reply_text = f"Note: this item may conflict with preferences: {', '.join(conflicts)}. Would you like me to suggest alternatives that fit your preferences?"
        reply = {"text": reply_text, "conflicts": conflicts, "need_clarify": True, "conversation_id": conv_id}
        db.conversations.update_one({"conversation_id": conv_id}, {"$push": {"messages": {"role": "agent", "text": reply_text, "ts": datetime.utcnow()}}})
        return jsonify(reply)

    # Check stock/availability
    stock = item.get('stock', None)
    if stock is not None and stock <= 0:
        alt = list(db.menu.find({
            "available": True,
            "stock": {"$gt": 0},
            "tags": {"$in": item.get("tags", [])}
        }).limit(3))
        if alt:
            alt_names = [a['name'] for a in alt]
            reply_text = f"Sorry, {item['name']} is currently unavailable. May I suggest: {', '.join(alt_names)}?"
            reply = {"text": reply_text, "alternatives": alt_names, "need_clarify": True, "conversation_id": conv_id}
            db.conversations.update_one({"conversation_id": conv_id}, {"$push": {"messages": {"role": "agent", "text": reply_text, "ts": datetime.utcnow()}}})
            return jsonify(reply)
        else:
            reply_text = f"Sorry, {item['name']} is currently unavailable and I have no close alternatives. Would you like something else?"
            reply = {"text": reply_text, "need_clarify": True, "conversation_id": conv_id}
            db.conversations.update_one({"conversation_id": conv_id}, {"$push": {"messages": {"role": "agent", "text": reply_text, "ts": datetime.utcnow()}}})
            return jsonify(reply)

    # Simulate placing order
    order = {
        "order_id": str(uuid.uuid4()),
        "item": item['name'],
        "item_id": str(item.get('_id')),
        "placed_at": datetime.utcnow(),
        "status": "confirmed"
    }
    db.orders.insert_one({"conversation_id": conv_id, "order": order})
    db.conversations.update_one({"conversation_id": conv_id}, {"$push": {"messages": {"role": "agent", "text": f"Order confirmed: {item['name']}", "ts": datetime.utcnow()}}})

    # decrement stock if applicable
    if item.get('stock') is not None:
        db.menu.update_one({"_id": item['_id']}, {"$inc": {"stock": -1}})

    return jsonify({"text": f"Order confirmed: {item['name']}", "order": order, "conversation_id": conv_id})


@app.route("/conversation/<conv_id>", methods=["GET"])
def get_conversation(conv_id):
    conv = db.conversations.find_one({"conversation_id": conv_id}, {"_id": 0})
    if not conv:
        return jsonify({"error": "conversation not found"}), 404
    # convert datetimes to ISO strings for JSON
    for m in conv.get("messages", []):
        if isinstance(m.get("ts"), datetime):
            m["ts"] = m["ts"].isoformat()
    return jsonify(conv)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=True)
