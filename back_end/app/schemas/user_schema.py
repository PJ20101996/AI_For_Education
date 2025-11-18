from pydantic import BaseModel

class User(BaseModel):
    name: str | None = None
    email: str
    password: str
