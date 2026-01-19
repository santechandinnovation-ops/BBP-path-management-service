from fastapi import APIRouter, Depends, HTTPException
import uuid
from datetime import datetime
import logging

from app.models.path import ObstacleCreateRequest, ObstacleCreateResponse
from app.utils.security import get_current_user
from app.config.database import get_db_connection, return_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=ObstacleCreateResponse, status_code=201)
async def add_obstacle(
    obstacle_data: ObstacleCreateRequest,
    user_id: str = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT segment_id FROM Segments WHERE segment_id = %s
        """, (obstacle_data.segmentId,))

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Segment not found")

        obstacle_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO Obstacles (
                obstacle_id, segment_id, type, severity,
                latitude, longitude, description, reported_date, confirmed
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            obstacle_id,
            obstacle_data.segmentId,
            obstacle_data.type.value,
            obstacle_data.severity.value,
            obstacle_data.latitude,
            obstacle_data.longitude,
            obstacle_data.description,
            datetime.now(),
            True
        ))

        conn.commit()
        cursor.close()

        return ObstacleCreateResponse(
            obstacleId=obstacle_id,
            message="Obstacle added successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error adding obstacle: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            return_db_connection(conn)
