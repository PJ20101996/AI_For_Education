from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["AI_project"]
users_collection = db["users"]
embeddings_collection = db["doc_embeddings"]

# Uploads Directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# OpenAI Client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
