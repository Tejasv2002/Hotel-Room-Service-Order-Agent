# Hotel Room Service Order Agent

A compact Python + MongoDB demo for a hotel room-service agent.  
Focus areas: natural-language order handling, dietary preferences, multi-turn clarifications, availability checks, and context retention.

## What's included
- `app.py` — Flask demo server with simple agent logic.
- `db_init.py` — populate MongoDB with sample menu items and resets collections.
- `examples/conversations.md` — sample flows to demonstrate behavior.
- `design.md` — short design notes and decisions.
- `requirements.txt`, `.env.example`, `.gitignore`, `LICENSE`.

## Quick start in local
1. Ensure MongoDB is running locally (default `mongodb://localhost:27017`).
2. Create and activate a Python venv:
   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   pip install -r requirements.txt


Design Document — Hotel Room Service Order Agent
Goals
Convert guest natural-language requests into orders.
Respect dietary preferences (vegetarian, vegan, gluten-free, etc).
Ask short clarifying questions when intent is ambiguous.
Keep conversation state in MongoDB so sessions can be resumed.
High-level architecture

Flask app (app.py) exposes two endpoints:
POST /message — handle guest messages and agent replies.
GET /conversation/<id> — fetch stored conversation history.

MongoDB collections:
menu — menu items and tags (dietary, availability, stock).
conversations — message history and simple metadata.
orders — placed orders (simulated).
Logic style: simple rule-based parsing + keyword matching for predictability.

Important choices
Use explainable rules so results are traceable and easy to read.
Persist every message to MongoDB to support resume/replay.
Keep multi-turn clarifications short — ask a single focused question.
Failure modes and mitigations
Mis-detected diet preference: agent echoes detected preferences before confirming order.
Out-of-stock items: agent proposes alternatives using tag overlap.

