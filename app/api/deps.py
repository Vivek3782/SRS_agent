from fastapi import Depends, HTTPException, status, Header
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.schemas.token import TokenData
from app.models.user import User


def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract Bearer token from Authorization header.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


async def get_current_user(token: str = Depends(get_token_from_header), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = auth_service.verify_token(token, credentials_exception)
    username: str = payload.get("sub")

    if username is None:
        raise credentials_exception

    token_data = TokenData(username=username)

    user = user_service.get_user_by_email(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    return user
