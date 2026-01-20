from pydantic import BaseModel, field_validator
from typing import List, Optional
from enum import Enum
from datetime import datetime


class DataSource(str, Enum):
    MANUAL = "MANUAL"
    AUTOMATED = "AUTOMATED"

class SegmentStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    MEDIUM = "MEDIUM"
    SUFFICIENT = "SUFFICIENT"
    REQUIRES_MAINTENANCE = "REQUIRES_MAINTENANCE"

class ObstacleType(str, Enum):
    POTHOLE = "POTHOLE"
    ROUGH_SURFACE = "ROUGH_SURFACE"
    DEBRIS = "DEBRIS"
    CONSTRUCTION = "CONSTRUCTION"
    OTHER = "OTHER"

class ObstacleSeverity(str, Enum):
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"

class CoordinateInput(BaseModel):
    latitude: float
    longitude: float

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class SegmentInput(BaseModel):
    streetName: Optional[str] = None
    status: SegmentStatus
    startLatitude: float
    startLongitude: float
    endLatitude: float
    endLongitude: float
    order: int

    @field_validator('startLatitude', 'endLatitude')
    @classmethod
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('startLongitude', 'endLongitude')
    @classmethod
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class ObstacleInput(BaseModel):
    segmentId: Optional[str] = None
    type: ObstacleType
    severity: ObstacleSeverity
    latitude: float
    longitude: float
    description: Optional[str] = None

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class ManualPathCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    roughPath: Optional[List[CoordinateInput]] = None
    segments: List[SegmentInput]
    obstacles: Optional[List[ObstacleInput]] = []
    publishable: bool

class PathInfoResponse(BaseModel):
    pathInfoId: str
    message: str

class ObstacleResponse(BaseModel):
    obstacleId: str
    type: str
    severity: str
    latitude: float
    longitude: float
    description: Optional[str]

class SegmentResponse(BaseModel):
    segmentId: str
    streetName: Optional[str]
    status: str
    startLatitude: float
    startLongitude: float
    endLatitude: float
    endLongitude: float
    obstacles: List[ObstacleResponse]

class RouteResponse(BaseModel):
    routeId: str
    score: float
    totalDistance: float
    segments: List[SegmentResponse]

class RoutesSearchResponse(BaseModel):
    routes: List[RouteResponse]

class PathDetailResponse(BaseModel):
    pathInfoId: str
    name: Optional[str]
    description: Optional[str]
    dataSource: str
    createdDate: datetime
    totalDistance: float
    score: float
    segments: List[SegmentResponse]
