from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from app.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


class AuthService:
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        exp_timestamp = int(expire.timestamp())
        to_encode.update({"exp": exp_timestamp, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        exp_timestamp = int(expire.timestamp())
        to_encode.update({"exp": exp_timestamp, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str, credentials_exception=None):
        try:
            now = datetime.now(timezone.utc)
            # Add a small leeway (10 seconds) to account for clock skew
            payload = jwt.decode(token, SECRET_KEY, algorithms=[
                                 ALGORITHM], options={"leeway": 10})
            username: str = payload.get("sub")
            token_type: str = payload.get("type")
            if username is None:
                if credentials_exception:
                    raise credentials_exception
                raise Exception("Token missing 'sub' claim")
            if token_type is None:
                if credentials_exception:
                    raise credentials_exception
                raise Exception("Token missing 'type' claim")
            return payload
        except JWTError as e:
            now = datetime.now(timezone.utc)
            print(f"DEBUG: Verification failed at {now}: {str(e)}")
            if credentials_exception:
                raise credentials_exception
            raise Exception(f"JWT Decode Error: {str(e)}")


auth_service = AuthService()
