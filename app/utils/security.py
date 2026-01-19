from jose import jwt, JWTError
from fastapi import HTTPException, Depends, Header
from typing import Optional
from app.config.settings import settings

def get_user_id_from_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: user_id not found")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    return get_user_id_from_token(token)

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    try:
        return get_user_id_from_token(token)
    except HTTPException:
        return None
