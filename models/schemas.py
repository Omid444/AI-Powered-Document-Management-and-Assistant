from pydantic import BaseModel

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str