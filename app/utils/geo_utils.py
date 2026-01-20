import math
from typing import List, Dict
from app.models.path import SegmentStatus, ObstacleSeverity

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
    obstacle_lat = float(obstacle_lat)
    obstacle_lon = float(obstacle_lon)

    min_distance = float('inf')
    nearest_segment_id = None

    for segment in segments:
        segment_id = segment['segment_id']
        start_lat = float(segment['start_latitude'])
        start_lon = float(segment['start_longitude'])
        end_lat = float(segment['end_latitude'])
        end_lon = float(segment['end_longitude'])

        # Calculate distance to the closest point on the line segment
        distance = point_to_segment_distance(
            obstacle_lat, obstacle_lon,
            start_lat, start_lon,
            end_lat, end_lon
        )

        if distance < min_distance:
            min_distance = distance
            nearest_segment_id = segment_id

    if min_distance > max_distance_meters:
        return None

    return nearest_segment_id


def point_to_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate the minimum distance from point (px, py) to a line segment defined by (x1, y1) and (x2, y2).
    All coordinates are in latitude/longitude.
    Returns distance in meters.
    """
    # Vector from segment start to end
    dx = x2 - x1
    dy = y2 - y1
    
    # If segment is a point, return distance to that point
    if dx == 0 and dy == 0:
        return calculate_haversine_distance(px, py, x1, y1)
    
    # Calculate the projection parameter t
    # t = 0 means closest point is at segment start
    # t = 1 means closest point is at segment end
    # t between 0-1 means closest point is on the segment
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
    # Clamp t to [0, 1] to stay on the segment
    t = max(0, min(1, t))
    
    # Calculate the closest point on the segment
    closest_lat = x1 + t * dx
    closest_lon = y1 + t * dy
    
    # Return the distance from the obstacle to the closest point
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
