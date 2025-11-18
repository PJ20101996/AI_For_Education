from fastapi import APIRouter, HTTPException
from app.config.database import users_collection, embeddings_collection, openai_client
from app.utils.helpers import (
    create_embedding,
    vector_search,
    chunk_text,
    count_tokens,
)


router = APIRouter(prefix="/chat")


# Initialize chat history if missing
def ensure_chat_history(email, filename):
    users_collection.update_one(
        {"email": email, "chat_history.filename": {"$ne": filename}},
        {"$push": {"chat_history": {"filename": filename, "messages": []}}}
    )


@router.post("/query")
def ask_question(payload: dict):
    email = payload.get("email")
    filename = payload.get("filename")
    question = payload.get("question")

    if not all([email, filename, question]):
        raise HTTPException(status_code=400, detail="Missing parameters")

    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ensure_chat_history(email, filename)

    # Retrieve last 10 messages from chat history
    history_doc = next(
        (h for h in user.get("chat_history", []) if h["filename"] == filename),
        None
    )
    messages = history_doc.get("messages", [])[-10:] if history_doc else []

    # Retrieve relevant document chunks using RAG
    query_embedding = create_embedding(question)
    retrieved_chunks = vector_search(query_embedding, email, filename, top_k=5)


    rag_context = "\n\n".join(retrieved_chunks)

    # Construct conversation prompt
    conversation = [
        {"role": "system", "content": "You answer questions based on provided document context only. If information is missing, say you cannot find it."},
        {"role": "system", "content": f"Document Content:\n{rag_context}"}
    ]

    # Attach historical conversation to maintain context
    for msg in messages:
        conversation.append({"role": msg["role"], "content": msg["content"]})

    conversation.append({"role": "user", "content": question})

    # Call LLM
    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=conversation
    )

    answer = response.choices[0].message.content.strip()

    # Store updated chat history
    users_collection.update_one(
        {"email": email, "chat_history.filename": filename},
        {"$push": {"chat_history.$.messages": {"role": "user", "content": question}}}
    )
    users_collection.update_one(
        {"email": email, "chat_history.filename": filename},
        {"$push": {"chat_history.$.messages": {"role": "assistant", "content": answer}}}
    )

    return {"answer": answer}
