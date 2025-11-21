from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

# Read environment variable from Render dashboard
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "AI_project")

if not MONGO_URI:
    raise Exception("❌ MONGO_URI environment variable not set!")

try:
    client = MongoClient(MONGO_URI)
    # Test connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas successfully")
    
    db = client[MONGO_DB_NAME]
    users_collection = db["users"]
    embeddings_collection = db["doc_embeddings"]
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    raise

# Uploads Directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# OpenAI Client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
