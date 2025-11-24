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
