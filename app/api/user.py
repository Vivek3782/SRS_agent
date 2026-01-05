from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserRegister, UserDelete
from app.services.user_service import user_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(request: UserRegister, db: Session = Depends(get_db)):
    try:
        db_user = user_service.get_user_by_email(db, email=request.email)
        if db_user:
            raise HTTPException(
                status_code=400, detail="Email already registered")
        return user_service.create_user(db=db, user=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        users = user_service.get_users(db, skip=skip, limit=limit)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        db_user = user_service.get_user(db, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/", response_model=UserResponse)
def update_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_user = user_service.update_user(
            db, user_id=user_update.user_id, user_update=user_update)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/", response_model=bool)
def delete_user(user_delete: UserDelete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        success = user_service.delete_user(db, user_id=user_delete.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
