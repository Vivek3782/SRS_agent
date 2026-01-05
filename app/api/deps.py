from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.schemas.token import TokenData
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
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
