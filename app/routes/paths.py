from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from app.models.path import (
    ManualPathCreate, PathInfoResponse, RouteResponse, RoutesSearchResponse,
    PathDetailResponse, SegmentResponse, ObstacleResponse
)
from app.utils.security import get_current_user, get_current_user_optional
from app.utils.geo_utils import calculate_segment_length, is_within_radius, calculate_path_score, find_nearest_segment
from app.config.database import get_db_connection, return_db_connection
from app.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/manual", response_model=PathInfoResponse, status_code=201)
async def create_manual_path(
    path_data: ManualPathCreate,
    user_id: str = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        path_info_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO PathInfo (path_info_id, user_id, name, description, data_source, publishable, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            path_info_id,
            user_id,
            path_data.name,
            path_data.description,
            'MANUAL',
            path_data.publishable,
            datetime.now()
        ))

        segment_id_map = {}
        segments_for_matching = []

        for idx, segment in enumerate(path_data.segments):
            segment_id = str(uuid.uuid4())
            segment_id_map[idx] = segment_id

            length_meters = calculate_segment_length(
                segment.startLatitude,
                segment.startLongitude,
                segment.endLatitude,
                segment.endLongitude
            )

            cursor.execute("""
                INSERT INTO Segments (
                    segment_id, path_info_id, street_name, status,
                    start_latitude, start_longitude, end_latitude, end_longitude,
                    segment_order, length_meters
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                segment_id,
                path_info_id,
                segment.streetName,
                segment.status.value,
                segment.startLatitude,
                segment.startLongitude,
                segment.endLatitude,
                segment.endLongitude,
                segment.order,
                length_meters
            ))

            segments_for_matching.append({
                'segment_id': segment_id,
                'start_latitude': segment.startLatitude,
                'start_longitude': segment.startLongitude,
                'end_latitude': segment.endLatitude,
                'end_longitude': segment.endLongitude,
                'route_geometry': segment.routeGeometry  # Include all route points for accurate matching
            })
            
            # Debug log
            logger.info(f"Segment {idx}: start=({segment.startLatitude}, {segment.startLongitude}), end=({segment.endLatitude}, {segment.endLongitude}), routeGeometry points: {len(segment.routeGeometry) if segment.routeGeometry else 0}")

        if path_data.obstacles:
            for obstacle in path_data.obstacles:
                logger.info(f"Processing obstacle at ({obstacle.latitude}, {obstacle.longitude})")
                target_segment_id = obstacle.segmentId

                if target_segment_id is None:
                    target_segment_id = find_nearest_segment(
                        obstacle.latitude,
                        obstacle.longitude,
                        segments_for_matching,
                        max_distance_meters=50.0
                    )

                    if target_segment_id is None:
                        logger.error(f"No segment found within 50m of obstacle at ({obstacle.latitude}, {obstacle.longitude}). Segments: {len(segments_for_matching)}")
                        conn.rollback()
                        raise HTTPException(
                            status_code=400,
                            detail=f"No segment found within 50m of obstacle at ({obstacle.latitude}, {obstacle.longitude})"
                        )

                    logger.info(f"Auto-associated obstacle at ({obstacle.latitude}, {obstacle.longitude}) to segment {target_segment_id}")
                else:
                    cursor.execute("""
                        SELECT segment_id FROM Segments WHERE segment_id = %s
                    """, (target_segment_id,))

                    if not cursor.fetchone():
                        conn.rollback()
                        raise HTTPException(status_code=400, detail=f"Segment {target_segment_id} not found")

                obstacle_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO Obstacles (
                        obstacle_id, segment_id, type, severity,
                        latitude, longitude, description, reported_date, confirmed
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    obstacle_id,
                    target_segment_id,
                    obstacle.type.value,
                    obstacle.severity.value,
                    obstacle.latitude,
                    obstacle.longitude,
                    obstacle.description,
                    datetime.now(),
                    True
                ))

        conn.commit()
        cursor.close()

        return PathInfoResponse(
            pathInfoId=path_info_id,
            message="Path information saved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating manual path: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            return_db_connection(conn)

@router.get("/search", response_model=RoutesSearchResponse)
async def search_routes(
    originLat: float = Query(...),
    originLon: float = Query(...),
    destLat: float = Query(...),
    destLon: float = Query(...),
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Search for routes between origin and destination.
    
    Visibility rules:
    - Public paths (publishable=TRUE) are visible to everyone
    - Private paths (publishable=FALSE) are visible ONLY to the user who created them
    - When a logged-in user searches, they see both public paths AND their own private paths
    """
    conn = None
    try:
        if originLat < -90 or originLat > 90 or destLat < -90 or destLat > 90:
            raise HTTPException(status_code=400, detail="Invalid latitude values")

        if originLon < -180 or originLon > 180 or destLon < -180 or destLon > 180:
            raise HTTPException(status_code=400, detail="Invalid longitude values")

        conn = get_db_connection()
        cursor = conn.cursor()

        tolerance = settings.TOLERANCE_RADIUS_METERS

        # Query paths based on visibility rules:
        # - All public paths (publishable = TRUE)
        # - Private paths (publishable = FALSE) ONLY if they belong to the current user
        if user_id:
            # Authenticated user: can see public paths + their own private paths
            logger.info(f"Search by authenticated user: {user_id}")
            cursor.execute("""
                SELECT DISTINCT pi.path_info_id
                FROM PathInfo pi
                JOIN Segments s ON pi.path_info_id = s.path_info_id
                WHERE pi.publishable = TRUE 
                   OR (pi.publishable = FALSE AND pi.user_id = %s)
            """, (user_id,))
        else:
            # Anonymous user: can only see public paths
            logger.info("Search by anonymous user: showing only public paths")
            cursor.execute("""
                SELECT DISTINCT pi.path_info_id
                FROM PathInfo pi
                JOIN Segments s ON pi.path_info_id = s.path_info_id
                WHERE pi.publishable = TRUE
            """)

        path_ids = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(path_ids)} paths matching visibility criteria")

        matching_paths = []

        for path_id in path_ids:
            cursor.execute("""
                SELECT segment_id, street_name, status,
                       start_latitude, start_longitude, end_latitude, end_longitude,
                       segment_order, length_meters
                FROM Segments
                WHERE path_info_id = %s
                ORDER BY segment_order
            """, (path_id,))

            segments = cursor.fetchall()

            if not segments:
                continue

            first_segment = segments[0]
            last_segment = segments[-1]

            start_within = is_within_radius(
                originLat, originLon,
                float(first_segment[3]), float(first_segment[4]),
                tolerance
            )

            end_within = is_within_radius(
                destLat, destLon,
                float(last_segment[5]), float(last_segment[6]),
                tolerance
            )

            if start_within and end_within:
                matching_paths.append({
                    "path_id": path_id,
                    "segments": segments
                })

        if not matching_paths:
            raise HTTPException(status_code=404, detail="No routes found between specified locations")

        routes = []

        for path in matching_paths[:3]:
            path_id = path["path_id"]
            segments_data = []
            total_distance = 0.0

            for seg in path["segments"]:
                segment_id = seg[0]

                cursor.execute("""
                    SELECT obstacle_id, type, severity, latitude, longitude, description
                    FROM Obstacles
                    WHERE segment_id = %s
                """, (segment_id,))

                obstacles_data = []
                for obs in cursor.fetchall():
                    obstacles_data.append({
                        "obstacleId": obs[0],
                        "type": obs[1],
                        "severity": obs[2],
                        "latitude": float(obs[3]),
                        "longitude": float(obs[4]),
                        "description": obs[5]
                    })

                segment_dict = {
                    "segmentId": seg[0],
                    "streetName": seg[1],
                    "status": seg[2],
                    "startLatitude": float(seg[3]),
                    "startLongitude": float(seg[4]),
                    "endLatitude": float(seg[5]),
                    "endLongitude": float(seg[6]),
                    "obstacles": obstacles_data
                }

                segments_data.append(segment_dict)
                total_distance += float(seg[8])

            all_obstacles = []
            for seg in segments_data:
                for obs in seg["obstacles"]:
                    all_obstacles.append({
                        "segment_id": seg["segmentId"],
                        "severity": obs["severity"]
                    })

            score = calculate_path_score(
                [{"length_meters": float(seg[8]), "status": seg[2], "segment_id": seg[0]} for seg in path["segments"]],
                all_obstacles
            )

            routes.append(RouteResponse(
                routeId=path_id,
                score=score,
                totalDistance=round(total_distance / 1000, 2),
                segments=[
                    SegmentResponse(
                        segmentId=s["segmentId"],
                        streetName=s["streetName"],
                        status=s["status"],
                        startLatitude=s["startLatitude"],
                        startLongitude=s["startLongitude"],
                        endLatitude=s["endLatitude"],
                        endLongitude=s["endLongitude"],
                        obstacles=[
                            ObstacleResponse(
                                obstacleId=o["obstacleId"],
                                type=o["type"],
                                severity=o["severity"],
                                latitude=o["latitude"],
                                longitude=o["longitude"],
                                description=o["description"]
                            ) for o in s["obstacles"]
                        ]
                    ) for s in segments_data
                ]
            ))

        routes.sort(key=lambda r: r.score)

        cursor.close()

        return RoutesSearchResponse(routes=routes)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching routes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            return_db_connection(conn)

@router.get("/{path_id}", response_model=PathDetailResponse)
async def get_path_details(
    path_id: str,
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Get path details by ID.
    
    Visibility rules:
    - Public paths are visible to everyone
    - Private paths are visible ONLY to the user who created them
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # First, get the path info without filtering by publishable
        cursor.execute("""
            SELECT path_info_id, user_id, name, description, data_source, publishable, created_date
            FROM PathInfo
            WHERE path_info_id = %s
        """, (path_id,))

        path_info = cursor.fetchone()

        if not path_info:
            raise HTTPException(status_code=404, detail="Path not found")
        
        # Check visibility: public paths are visible to all, private paths only to owner
        path_owner_id = path_info[1]
        is_publishable = path_info[5]
        
        if not is_publishable:
            # Private path - only the owner can see it
            if user_id != path_owner_id:
                logger.warning(f"User {user_id} attempted to access private path {path_id} owned by {path_owner_id}")
                raise HTTPException(status_code=404, detail="Path not found")

        cursor.execute("""
            SELECT segment_id, street_name, status,
                   start_latitude, start_longitude, end_latitude, end_longitude,
                   segment_order, length_meters
            FROM Segments
            WHERE path_info_id = %s
            ORDER BY segment_order
        """, (path_id,))

        segments = cursor.fetchall()

        total_distance = 0.0
        segments_data = []

        for seg in segments:
            segment_id = seg[0]

            cursor.execute("""
                SELECT obstacle_id, type, severity, latitude, longitude, description
                FROM Obstacles
                WHERE segment_id = %s
            """, (segment_id,))

            obstacles_data = []
            for obs in cursor.fetchall():
                obstacles_data.append({
                    "obstacleId": obs[0],
                    "type": obs[1],
                    "severity": obs[2],
                    "latitude": float(obs[3]),
                    "longitude": float(obs[4]),
                    "description": obs[5]
                })

            segment_dict = {
                "segmentId": seg[0],
                "streetName": seg[1],
                "status": seg[2],
                "startLatitude": float(seg[3]),
                "startLongitude": float(seg[4]),
                "endLatitude": float(seg[5]),
                "endLongitude": float(seg[6]),
                "obstacles": obstacles_data
            }

            segments_data.append(segment_dict)
            total_distance += float(seg[8])

        all_obstacles = []
        for seg in segments_data:
            for obs in seg["obstacles"]:
                all_obstacles.append({
                    "segment_id": seg["segmentId"],
                    "severity": obs["severity"]
                })

        score = calculate_path_score(
            [{"length_meters": float(seg[8]), "status": seg[2], "segment_id": seg[0]} for seg in segments],
            all_obstacles
        )

        cursor.close()

        return PathDetailResponse(
            pathInfoId=path_info[0],
            name=path_info[2],
            description=path_info[3],
            dataSource=path_info[4],
            createdDate=path_info[6],
            totalDistance=round(total_distance / 1000, 2),
            score=score,
            segments=[
                SegmentResponse(
                    segmentId=s["segmentId"],
                    streetName=s["streetName"],
                    status=s["status"],
                    startLatitude=s["startLatitude"],
                    startLongitude=s["startLongitude"],
                    endLatitude=s["endLatitude"],
                    endLongitude=s["endLongitude"],
                    obstacles=[
                        ObstacleResponse(
                            obstacleId=o["obstacleId"],
                            type=o["type"],
                            severity=o["severity"],
                            latitude=o["latitude"],
                            longitude=o["longitude"],
                            description=o["description"]
                        ) for o in s["obstacles"]
                    ]
                ) for s in segments_data
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting path details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            return_db_connection(conn)
