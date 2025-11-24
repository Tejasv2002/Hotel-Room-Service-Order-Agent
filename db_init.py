from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hotel_room_service")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# sample menu
menu = [
    {"name": "Caesar Salad", "price": 9.5, "tags": ["vegetarian"], "available": True, "stock": 10},
    {"name": "Grilled Chicken Sandwich", "price": 12.0, "tags": ["contains-meat"], "available": True, "stock": 5},
    {"name": "Vegan Buddha Bowl", "price": 13.0, "tags": ["vegan", "gluten-free"], "available": True, "stock": 4},
    {"name": "Club Sandwich", "price": 11.0, "tags": ["contains-meat"], "available": True, "stock": 2},
    {"name": "Pancakes", "price": 8.0, "tags": ["vegetarian"], "available": True, "stock": 6},
    {"name": "Gluten-Free Pasta", "price": 14.0, "tags": ["gluten-free", "vegetarian"], "available": True, "stock": 3},
    {"name": "Peanut Butter Cookies", "price": 4.0, "tags": ["contains-nuts"], "available": True, "stock": 0}
]

# reset collections (useful during development)
db.menu.drop()
db.conversations.drop()
db.orders.drop()

db.menu.insert_many(menu)
print("Inserted sample menu items into MongoDB (database: %s)" % DB_NAME)
print("Collections menu, conversations and orders were reset.")
