"""
FastAPI endpoints for user authentication and file upload/summarization
"""
from fastapi import APIRouter, HTTPException, UploadFile, Form, File
import os

from schemas.user_schema import User
from database import users_collection, embeddings_collection
from utils.helper import (
    extract_text,
    count_tokens,
    create_embedding,
    chunk_text,
    vector_search,
    generate_summary
)

# Create API router
router = APIRouter()

# Upload directory configuration
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/signup")
def signup(user: User):
    """
    User signup endpoint

    Args:
        user: User model with name, email, and password

    Returns:
        Success message

    Raises:
        HTTPException: If user already exists
    """
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists!")
    users_collection.insert_one(user.dict())
    return {"message": "Signup successful!"}


@router.post("/login")
def login(user: User):
    """
    User login endpoint

    Args:
        user: User model with email and password

    Returns:
        Success message with user details

    Raises:
        HTTPException: If credentials are invalid
    """
    found = users_collection.find_one({"email": user.email, "password": user.password})
    if not found:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "message": "Login successful!",
        "email": found["email"],
        "name": found.get("name", "User")
    }


@router.post("/upload")
async def upload_file(email: str = Form(...), file: UploadFile = File(...)):
    """
    Upload and summarize file endpoint

    Supports both normal summarization and RAG-based summarization for large files.

    Args:
        email: User email
        file: Uploaded file

    Returns:
        Summary and file information

    Raises:
        HTTPException: If user not found or file processing fails
    """
    user = users_collection.find_one({"email": email})
    if not user:
        return {"message": "User not found!"}

    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    file_type = file.filename.split(".")[-1].lower()
    file_url = f"http://127.0.0.1:8000/uploads/{file.filename}"

    # Store upload info in database
    upload_info = {
        "filename": file.filename,
        "filepath": file_path,
        "fileurl": file_url,
        "filetype": file_type
    }
    users_collection.update_one({"email": email}, {"$push": {"uploads": upload_info}})

    # Extract text and count tokens
    extracted_text = extract_text(file_path, file_type)
    total_tokens = count_tokens(extracted_text)

    if total_tokens == 0:
        return {"message": "File uploaded, but no readable text found.", "fileurl": file_url}

    # CASE 1: Normal Summarization (for files <= 800k tokens)
    if total_tokens <= 800000:
        summary = generate_summary(extracted_text, is_rag=False)
        users_collection.update_one(
            {"email": email},
            {"$push": {"summaries": {"filename": file.filename, "summary": summary}}}
        )

        return {
            "message": f"✅ File '{file.filename}' summarized normally.",
            "summary": summary,
            "tokens": total_tokens,
            "fileurl": file_url
        }

    # CASE 2: RAG Summarization for large documents
    else:
        chunks = chunk_text(extracted_text)
        embeddings_collection.delete_many({"filename": file.filename, "email": email})

        # Create embeddings for all chunks
        for chunk in chunks:
            emb = create_embedding(chunk)
            embeddings_collection.insert_one({
                "email": email,
                "filename": file.filename,
                "embedding": emb.tolist(),
                "text": chunk
            })

        # Retrieve relevant chunks using vector search
        query = "Summarize the main key points of this large document."
        query_emb = create_embedding(query)
        retrieved_chunks = vector_search(query_emb, embeddings_collection, top_k=5)
        combined_text = "\n\n".join(retrieved_chunks)

        # Generate summary from retrieved chunks
        summary = generate_summary(combined_text, is_rag=True)
        users_collection.update_one(
            {"email": email},
            {"$push": {"summaries": {"filename": file.filename, "summary": summary, "RAG": True}}}
        )

        return {
            "message": f"✅ File '{file.filename}' processed using RAG due to large size.",
            "summary": summary,
            "tokens": total_tokens,
            "fileurl": file_url
        }
