"""
Helper functions for text extraction, embeddings, and vector search
"""
import PyPDF2
import docx
import numpy as np
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text(file_path: str, file_type: str) -> str:
    """
    Extract text from various file types (PDF, DOCX, TXT, CSV)

    Args:
        file_path: Path to the file
        file_type: Type of file (pdf, doc, docx, txt, csv)

    Returns:
        Extracted text as string
    """
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


def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken

    Args:
        text: Input text

    Returns:
        Number of tokens
    """
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def create_embedding(text: str) -> np.ndarray:
    """
    Create embeddings using OpenAI API

    Args:
        text: Input text to embed

    Returns:
        Numpy array of embeddings
    """
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding)


def chunk_text(text: str, chunk_size: int = 3000) -> list:
    """
    Split large text into chunks

    Args:
        text: Input text
        chunk_size: Size of each chunk in words

    Returns:
        List of text chunks
    """
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def vector_search(query_embedding: np.ndarray, embeddings_collection, top_k: int = 5) -> list:
    """
    Perform vector similarity search using cosine similarity

    Args:
        query_embedding: Query vector
        embeddings_collection: MongoDB collection with embeddings
        top_k: Number of top results to return

    Returns:
        List of most similar text chunks
    """
    all_docs = list(embeddings_collection.find({}))
    if not all_docs:
        return []

    similarities = []
    for doc in all_docs:
        stored_vector = np.array(doc["embedding"])
        score = np.dot(query_embedding, stored_vector) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(stored_vector)
        )
        similarities.append((doc["text"], score))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return [doc[0] for doc in similarities[:top_k]]


def generate_summary(text: str, is_rag: bool = False) -> str:
    """
    Generate summary using OpenAI API

    Args:
        text: Text to summarize
        is_rag: Whether this is RAG-based summarization

    Returns:
        Generated summary
    """
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
{text[:4000]}
"""

    system_message = "You are an expert summarizer AI specialized in extracting meaning from documents."
    if is_rag:
        system_message = "You are an expert summarizer AI specialized in extracting meaning from long documents using RAG."

    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": summary_prompt}
        ]
    )

    return response.choices[0].message.content.strip()
