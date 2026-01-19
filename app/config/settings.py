from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    TOLERANCE_RADIUS_METERS: float = 100.0

    PORT: int = 8001

    class Config:
        case_sensitive = True

def get_settings() -> Settings:
    return Settings(
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", ""),
        JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
        TOLERANCE_RADIUS_METERS=float(os.getenv("TOLERANCE_RADIUS_METERS", "100.0")),
        PORT=int(os.getenv("PORT", "8001"))
    )

settings = get_settings()
