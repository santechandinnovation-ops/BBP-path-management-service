import math
from typing import List, Dict
from app.models.path import SegmentStatus, ObstacleSeverity

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000

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
