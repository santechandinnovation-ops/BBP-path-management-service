import math
from typing import List, Dict
import logging
from app.models.path import SegmentStatus, ObstacleSeverity

logger = logging.getLogger(__name__)

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000

    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return distance

def calculate_segment_length(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> float:
    return calculate_haversine_distance(start_lat, start_lon, end_lat, end_lon)

def is_within_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius_meters: float) -> bool:
    distance = calculate_haversine_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_meters

def find_nearest_segment(obstacle_lat: float, obstacle_lon: float, segments: List[Dict], max_distance_meters: float = 50.0) -> str:
    """
    finds the closest segment to an obstacal point
    if we have routeGeometry it uses all the points for beter matching
    otherwhise it just uses start and end points
    """
    obstacle_lat = float(obstacle_lat)
    obstacle_lon = float(obstacle_lon)

    min_distance = float('inf')
    nearest_segment_id = None

    logger.debug(f"Finding nearest segment for obstacle at ({obstacle_lat}, {obstacle_lon})")
    logger.debug(f"Number of segments to check: {len(segments)}")

    for segment in segments:
        segment_id = segment['segment_id']
        route_geometry = segment.get('route_geometry')
        
        logger.debug(f"Checking segment {segment_id}, route_geometry: {route_geometry is not None}, points: {len(route_geometry) if route_geometry else 0}")
        
        if route_geometry and len(route_geometry) >= 2:
            # use detailed route geomtry for more acurate matching
            for i in range(len(route_geometry) - 1):
                p1 = route_geometry[i]
                p2 = route_geometry[i + 1]
                
                # route_geometry format is like [[lat, lng], [lat, lng], ...]
                distance = point_to_segment_distance(
                    obstacle_lat, obstacle_lon,
                    float(p1[0]), float(p1[1]),
                    float(p2[0]), float(p2[1])
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_segment_id = segment_id
        else:
            # fallback - just use start and end points if no geometry
            start_lat = float(segment['start_latitude'])
            start_lon = float(segment['start_longitude'])
            end_lat = float(segment['end_latitude'])
            end_lon = float(segment['end_longitude'])

            distance = point_to_segment_distance(
                obstacle_lat, obstacle_lon,
                start_lat, start_lon,
                end_lat, end_lon
            )

            if distance < min_distance:
                min_distance = distance
                nearest_segment_id = segment_id

    logger.info(f"Nearest segment for obstacle at ({obstacle_lat}, {obstacle_lon}): {nearest_segment_id}, distance: {min_distance:.2f}m")

    if min_distance > max_distance_meters:
        logger.warning(f"Min distance {min_distance:.2f}m exceeds max {max_distance_meters}m")
        return None

    return nearest_segment_id


def point_to_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """
    calcualtes min distance from a point to a line segmnet
    coords are lat/lon and it returns meters
    """
    # vector from start to end of segment
    dx = x2 - x1
    dy = y2 - y1
    
    # if the segment is basicaly a point just return distnace to it
    if dx == 0 and dy == 0:
        return calculate_haversine_distance(px, py, x1, y1)
    
    # calculate projection paramater t
    # t=0 means closet point is at start, t=1 at end
    # t between 0-1 means its somwhere on the segment
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
    # clamp t to stay on the segment (cant be outside 0-1)
    t = max(0, min(1, t))
    
    # now we can get the closets point on segment
    closest_lat = x1 + t * dx
    closest_lon = y1 + t * dy
    
    # finaly return the distance to closet point
    return calculate_haversine_distance(px, py, closest_lat, closest_lon)

def calculate_path_score(segments: List[Dict], obstacles: List[Dict]) -> float:
    status_multipliers = {
        "OPTIMAL": 1.0,
        "MEDIUM": 1.2,
        "SUFFICIENT": 1.5,
        "REQUIRES_MAINTENANCE": 2.0
    }

    severity_penalties = {
        "MINOR": 50,
        "MODERATE": 150,
        "SEVERE": 400
    }

    total_score = 0.0

    for segment in segments:
        length = segment.get("length_meters", 0)
        status = segment.get("status", "OPTIMAL")
        multiplier = status_multipliers.get(status, 1.0)

        segment_score = length * multiplier
        total_score += segment_score

    obstacle_by_segment = {}
    for obstacle in obstacles:
        segment_id = obstacle.get("segment_id")
        if segment_id not in obstacle_by_segment:
            obstacle_by_segment[segment_id] = []
        obstacle_by_segment[segment_id].append(obstacle)

    for segment in segments:
        segment_id = segment.get("segment_id")
        if segment_id in obstacle_by_segment:
            for obstacle in obstacle_by_segment[segment_id]:
                severity = obstacle.get("severity", "MINOR")
                penalty = severity_penalties.get(severity, 0)
                total_score += penalty

    return round(total_score, 2)
