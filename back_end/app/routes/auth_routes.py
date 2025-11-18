from fastapi import APIRouter, HTTPException
from app.schemas.user_schema import User
from app.config.database import users_collection
from app.models.user_model import create_user
from app.config.database import users_collection

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists!")
    users_collection.insert_one(create_user(user.email, user.name, user.password))
    return {"message": "Signup successful!"}

@router.post("/login")
def login(user: User):
    found = users_collection.find_one({"email": user.email, "password": user.password})
    if not found:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "message": "Login successful!",
        "email": found["email"],
        "name": found.get("name", "User")
    }
