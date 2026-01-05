from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_superuser: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True
