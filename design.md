# Design Notes – Room Service Assistant
This document summarizes how the room-service assistant is structured and why certain choices were made. 
The goal was to keep the project small enough to understand at a glance, but still handle the requirements 
like dietary preferences, unavailable items, and basic conversation flow.

---

## 1. Overview
The system is a simple Flask API that talks to MongoDB.  
Incoming messages go through a few checks: identifying what the guest wants, checking the menu, 
and then deciding whether the agent can confirm the order or needs to ask a follow-up question.

Files:
- `app.py` – main API and the basic “agent” logic.
- `db_init.py` – sets up sample menu items.
- `examples/` – conversation samples.
- MongoDB stores menu items, conversations, and orders.

---

## 2. How the Agent Works

When the guest sends a message:
1. The text is scanned for dietary keywords (vegan, vegetarian, gluten, etc.).  
   This is a simple text check, nothing fancy.

2. The message is matched against menu items.  
   The matching uses keywords from the item name or the tags attached to each item.

3. The system decides one of the following:
   - No item matches → ask the guest what they meant.
   - Too many matches → list the possible items.
   - Item conflicts with dietary preference → warn the guest.
   - Item out of stock → suggest alternatives.
   - Otherwise → confirm the order.

4. Conversation history is stored so the agent can keep context.

---

## 3. Why This Approach
- The assignment didn’t require a large model or heavy NLP, so I stuck with readable logic.
- Storing the conversation in MongoDB keeps the API stateless and easier to test.
- The rule-based approach avoids unpredictable behavior and makes debugging easier.
- The code is intentionally straightforward so another engineer can follow it without effort.

---

## 4. Notes for Future Upgrades
If this were expanded further, the next logical improvements would be:
- Better preference handling (e.g., guest profile or room profile).
- Replace the rule-based matching with a proper intent/slot extractor.
- Add delivery timing rules.
- Add a front-end to make demos easier.

For now, the current setup meets the assignment requirements without adding overhead.
