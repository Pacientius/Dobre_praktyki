from sqlalchemy import Column, Integer, String
from database.database import Base
from pydantic import BaseModel

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    password = Column(String)

    
class UserCreate(BaseModel):
    name: str
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    password: str | None = None

class UserResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attribute = True