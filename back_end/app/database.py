"""
MongoDB database configuration and connection
"""
from pymongo import MongoClient
import os

# MongoDB connection URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Initialize MongoDB client
client = MongoClient(MONGO_URI)

# Database
db = client["AI_project"]

# Collections
users_collection = db["users"]
embeddings_collection = db["doc_embeddings"]


def get_users_collection():
    """Get users collection"""
    return users_collection


def get_embeddings_collection():
    """Get embeddings collection"""
    return embeddings_collection


def close_connection():
    """Close MongoDB connection"""
    client.close()
