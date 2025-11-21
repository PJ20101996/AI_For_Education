import PyPDF2, docx, numpy as np, tiktoken
from app.config.database import openai_client, embeddings_collection
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os
import platform

# Extract Text from File
def extract_text(file_path: str, file_type: str):
    text = ""
    try:
        if file_type == "pdf":
            reader = PyPDF2.PdfReader(open(file_path, "rb"))
            for page in reader.pages:
                text += page.extract_text() or ""

        elif file_type in ["doc", "docx"]:
            document = docx.Document(file_path)
            for para in document.paragraphs:
                text += para.text + "\n"

        elif file_type in ["txt", "csv"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
    except:
        return ""
    return text.strip()

# Token counter
def count_tokens(text: str):
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# Create Embedding
def create_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding)

# Text Chunking
def chunk_text(text, chunk_size=3000):
    words = text.split()
    return [" ".join(words[i:i + chunk_size])
            for i in range(0, len(words), chunk_size)]

# Vector Search (Cosine Similarity)
def vector_search(query_embedding, email, filename, top_k=5):
    all_docs = list(embeddings_collection.find({
        "email": email,
        "filename": filename
    }))

    if not all_docs:
        return []

    similarities = []
    for doc in all_docs:
        emb = np.array(doc["embedding"])
        score = np.dot(query_embedding, emb) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(emb)
        )
        similarities.append((doc["text"], score))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return [text for text, _ in similarities[:top_k]]

def generate_summary(text, is_rag=False):
    prompt = f"""
You are an expert summarizer AI.
Provide a professional and concise summary focusing on:

• Main objective or topic
• Key points or observations
• Important names, numbers, or results (if any)

Avoid repetition.
Keep it clean and easy to understand.

Document:
{text[:4000]}
    """

    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You summarize documents accurately."},
            {"role": "user", "content": prompt}
        ]
    )

    summary = response.choices[0].message.content.strip()
    return summary



# Configure paths based on OS
# On Windows, use specific paths; on Linux, rely on system PATH
if platform.system() == "Windows":
    POPPLER_PATH = r"C:\poppler-25.07.0\Library\bin"
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    # On Linux (Render), Poppler and Tesseract should be in system PATH
    POPPLER_PATH = None  # Will use system PATH
    # Tesseract should be available in PATH on Linux

def extract_text_with_ocr(file_path):
    text = ""

    try:
        # OCR for PDFs
        if file_path.lower().endswith(".pdf"):
            if POPPLER_PATH:
                pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)
            else:
                # On Linux, Poppler should be in system PATH
                pages = convert_from_path(file_path)
            for page in pages:
                text += pytesseract.image_to_string(page)

        # OCR for Images (jpg, jpeg, png)
        elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(file_path)
            text += pytesseract.image_to_string(image)
    except Exception as e:
        print(f"OCR error: {e}")
        return ""

    return text.strip() if text else ""
