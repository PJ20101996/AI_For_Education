from pymongo import MongoClient

# Replace with your MongoDB URI
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)

db = client["ai_summarizer"]       # Database name
users_collection = db["users"]     # Collection (table)
