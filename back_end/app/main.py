from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth_routes, upload_routes, chat_routes


app = FastAPI(title="AI Summarizer API")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_routes.router, tags=["Auth"])
app.include_router(upload_routes.router, tags=["Upload"])
app.include_router(chat_routes.router, tags=["Chatbot"])


@app.get("/")
def home():
    return {"message": "🔥 AI Summarizer Backend Running!"}
