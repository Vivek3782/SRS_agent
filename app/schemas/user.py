from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    user_id: UUID
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_superuser: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=6)


class UserDelete(BaseModel):
    user_id: UUID


class UserLogin(BaseModel):
    email: EmailStr
    password: str
