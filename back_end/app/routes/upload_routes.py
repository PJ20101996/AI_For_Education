from fastapi import APIRouter, UploadFile, Form, File, HTTPException
import os, hashlib
from app.config.database import users_collection, embeddings_collection
from app.utils.helpers import (
    extract_text,
    extract_text_with_ocr,
    count_tokens,
    create_embedding,
    chunk_text,
    generate_summary
)

router = APIRouter(prefix="/file")


def file_hash(content: bytes):
    return hashlib.sha256(content).hexdigest()


@router.post("/upload")
async def upload_file(email: str = Form(...), file: UploadFile = File(...)):
    try:
        user = users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found!")

        UPLOAD_DIR = "uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        content = await file.read()
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as f:
            f.write(content)

        file_type = file.filename.split(".")[-1].lower()
        file_url = f"http://127.0.0.1:8000/uploads/{file.filename}"

        # Step 1: Normal extract
        extracted_text = extract_text(file_path, file_type)

        # Step 2: If failed → try OCR
        if not extracted_text or len(extracted_text) < 50:
            print("🔍 Running OCR for scanned/image document...")
            extracted_text = extract_text_with_ocr(file_path)

        # Step 3: If still no text → stop process safely
        if not extracted_text or len(extracted_text) < 20:
            return {
                "message": "⚠️ File uploaded but no readable text found.",
                "fileurl": file_url,
                "tokens": 0
            }

        total_tokens = count_tokens(extracted_text)

        # Save file reference
        users_collection.update_one(
            {"email": email},
            {"$push": {"uploads": {
                "filename": file.filename,
                "fileurl": file_url,
                "tokens": total_tokens
            }}}
        )

        # Remove old embeddings for this exact file
        embeddings_collection.delete_many({"email": email, "filename": file.filename})

        # Store embeddings always
        chunks = chunk_text(extracted_text)
        for chunk in chunks:
            emb = create_embedding(chunk)
            embeddings_collection.insert_one({
                "email": email,
                "filename": file.filename,
                "embedding": emb.tolist(),
                "text": chunk
            })

        # Summarize extracted text
        summary = generate_summary(extracted_text)

        users_collection.update_one(
            {"email": email},
            {"$push": {"summaries": {
                "filename": file.filename,
                "summary": summary
            }}}
        )

        return {
            "message": "Uploaded & summarized successfully!",
            "summary": summary,
            "fileurl": file_url,
            "tokens": total_tokens
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
