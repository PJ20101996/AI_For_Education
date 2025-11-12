from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2, docx, numpy as np, tiktoken, os

# ✅ Load environment variables
load_dotenv()

app = FastAPI()

# ✅ Serve static uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["AI_project"]
users = db["users"]
embeddings_collection = db["doc_embeddings"]

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Helper: Extract text ---
def extract_text(file_path: str, file_type: str):
    text = ""
    if file_type == "pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif file_type in ["doc", "docx"]:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file_type in ["txt", "csv"]:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""
    return text.strip()

# --- Helper: Count tokens using tiktoken ---
def count_tokens(text: str):
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# --- Helper: Create embeddings ---
def create_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding)

# --- Helper: Chunk large text ---
def chunk_text(text, chunk_size=3000):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

# --- Helper: Vector search using MongoDB ---
def vector_search(query_embedding, top_k=5):
    all_docs = list(embeddings_collection.find({}))
    if not all_docs:
        return []
    
    similarities = []
    for doc in all_docs:
        stored_vector = np.array(doc["embedding"])
        score = np.dot(query_embedding, stored_vector) / (np.linalg.norm(query_embedding) * np.linalg.norm(stored_vector))
        similarities.append((doc["text"], score))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [doc[0] for doc in similarities[:top_k]]

# ✅ Request Model
class User(BaseModel):
    name: str = None
    email: str
    password: str

# ✅ Signup route
@app.post("/signup")
def signup(user: User):
    if users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists!")
    users.insert_one(user.dict())
    return {"message": "Signup successful!"}

# ✅ Login route
@app.post("/login")
def login(user: User):
    found = users.find_one({"email": user.email, "password": user.password})
    if not found:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful!", "email": found["email"], "name": found.get("name", "User")}

# ✅ Upload and Summarize route
@app.post("/upload")
async def upload_file(email: str = Form(...), file: UploadFile = File(...)):
    user = users.find_one({"email": email})
    if not user:
        return {"message": "User not found!"}

    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    file_type = file.filename.split(".")[-1].lower()
    file_url = f"http://127.0.0.1:8000/uploads/{file.filename}"

    upload_info = {
        "filename": file.filename,
        "filepath": file_path,
        "fileurl": file_url,
        "filetype": file_type
    }
    users.update_one({"email": email}, {"$push": {"uploads": upload_info}})

    # --- Extract text and count tokens ---
    extracted_text = extract_text(file_path, file_type)
    total_tokens = count_tokens(extracted_text)

    if total_tokens == 0:
        return {"message": "File uploaded, but no readable text found.", "fileurl": file_url}

    # --- CASE 1: Normal Summarization ---
    if total_tokens <= 800000:
        summary_prompt = f"""
You are an expert summarizer AI that provides accurate, structured, and human-like summaries.

Analyze the following document carefully and provide a professional summary.
Focus on:
- The main objective or topic
- Key arguments, facts, or sections
- Important names, dates, or numbers
- Conclusions or recommendations
- Tone or intent of the author (if clear)

Output format:
🧠 Summary:
(Write 5–10 bullet points capturing key insights.)

Avoid repetition. Use plain and clear English.

Document Content:
{extracted_text[:4000]}
"""

        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are an expert summarizer AI specialized in extracting meaning from documents."},
                {"role": "user", "content": summary_prompt}
            ]
        )

        summary = response.choices[0].message.content.strip()
        users.update_one(
            {"email": email},
            {"$push": {"summaries": {"filename": file.filename, "summary": summary}}}
        )

        return {
            "message": f"✅ File '{file.filename}' summarized normally.",
            "summary": summary,
            "tokens": total_tokens,
            "fileurl": file_url
        }

    # --- CASE 2: RAG Summarization for large docs ---
    else:
        chunks = chunk_text(extracted_text)
        embeddings_collection.delete_many({"filename": file.filename, "email": email})

        for chunk in chunks:
            emb = create_embedding(chunk)
            embeddings_collection.insert_one({
                "email": email,
                "filename": file.filename,
                "embedding": emb.tolist(),
                "text": chunk
            })

        query = "Summarize the main key points of this large document."
        query_emb = create_embedding(query)
        retrieved_chunks = vector_search(query_emb, top_k=5)
        combined_text = "\n\n".join(retrieved_chunks)

        summary_prompt = f"""
You are an expert summarizer AI that provides accurate, structured, and human-like summaries.

Analyze the following retrieved context and provide a professional summary.
Focus on:
- The main objective or topic
- Key arguments, facts, or sections
- Important names, dates, or numbers
- Conclusions or recommendations
- Tone or intent of the author (if clear)

Output format:
🧠 Summary:
(Write 5–10 bullet points capturing key insights.)

Avoid repetition. Use plain and clear English.

Document Content:
{combined_text[:4000]}
"""

        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are an expert summarizer AI specialized in extracting meaning from long documents using RAG."},
                {"role": "user", "content": summary_prompt}
            ]
        )

        summary = response.choices[0].message.content.strip()
        users.update_one(
            {"email": email},
            {"$push": {"summaries": {"filename": file.filename, "summary": summary, "RAG": True}}}
        )

        return {
            "message": f"✅ File '{file.filename}' processed using RAG due to large size.",
            "summary": summary,
            "tokens": total_tokens,
            "fileurl": file_url
        }
