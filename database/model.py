from sqlalchemy import Column, Integer, String, JSON
from database.database import Base
from pydantic import BaseModel
from typing import List, Optional

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    roles = Column(JSON, default=[])

    
class UserCreate(BaseModel):
    name: str
    password: str
    roles: List[str] = ["USER"]

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None

class UserResponse(BaseModel):
    id: int
    name: str
    roles: List[str]

    class Config:
        from_attribute = True