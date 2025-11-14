"""
Pydantic models for data validation and serialization
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List


class User(BaseModel):
    """User model for signup and login"""
    name: Optional[str] = None
    email: str
    password: str


class UploadInfo(BaseModel):
    """Upload information model"""
    filename: str
    filepath: str
    fileurl: str
    filetype: str


class Summary(BaseModel):
    """Summary model"""
    filename: str
    summary: str
    RAG: Optional[bool] = False


class UserInDB(BaseModel):
    """Extended user model with uploads and summaries"""
    name: Optional[str] = None
    email: str
    password: str
    uploads: Optional[List[UploadInfo]] = []
    summaries: Optional[List[Summary]] = []
