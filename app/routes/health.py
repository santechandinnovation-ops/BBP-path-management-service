from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.config.database import get_db_connection, return_db_connection
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1")
        cursor.fetchone()

        cursor.close()

        return {
            "status": "healthy",
            "service": "path-management-service",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

    finally:
        if conn:
            return_db_connection(conn)
