import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError

from passlib.context import CryptContext

from src.config import SecurityConfig
from src.usecases.schemas.auth_schemas import TokenData

_log = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    _log.info(f"Starting to create access token. Source data: {data}")
    to_encode = data.copy()
    to_encode.update({"id": data.get('user_id')})
    expire = datetime.now(timezone.utc) + SecurityConfig().access_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SecurityConfig().SECRET_KEY, algorithm=SecurityConfig().ALGORITHM)
    _log.info("Access token successfully created.")
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    _log.info(f"Starting to create refresh token. Source data: {data}")
    to_encode = data.copy()
    to_encode.update({"id": data.get('user_id')})
    expire = datetime.now(timezone.utc) + SecurityConfig().refresh_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SecurityConfig().SECRET_KEY, algorithm=SecurityConfig().ALGORITHM)
    _log.info("Refresh token successfully created.")
    return encoded_jwt


def verify_token_and_get_data(token: str) -> TokenData:
    try:
        _log.info("Starting token verification.")
        payload = jwt.decode(token, SecurityConfig().SECRET_KEY, algorithms=[SecurityConfig().ALGORITHM])
        _log.info(f"Token successfully decoded. Payload: {payload}")
        username: str = payload.get("sub")
        role: Optional[str] = payload.get("role")
        user_id: Optional[int] = payload.get("id")

        if username is None:
            _log.error("Token has no 'sub' claim.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(id=user_id, username=username, role=role)
    except ExpiredSignatureError:
        _log.error("Token has expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        _log.error("Invalid token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
