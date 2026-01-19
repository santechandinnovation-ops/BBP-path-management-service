# BBP Path Management Microservice

Microservice for managing bike paths, route search, and obstacle reporting.

## Features

- **Manual Path Entry**: Users can manually create bike paths with segments and obstacles
- **Route Search**: Public endpoint to search for routes between origin and destination coordinates
- **Path Refinement**: Integration with Google Maps Roads API to validate and refine paths on real roads
- **Obstacle Reporting**: Users can report obstacles on path segments
- **Path Scoring**: Automatic scoring based on segment status and obstacles

## Requirements

- Python 3.11+
- PostgreSQL database (Supabase)
- Google Maps API key (for path refinement)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET_KEY=your-secret-key-here
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
TOLERANCE_RADIUS_METERS=100
PORT=8001
```

3. Initialize database tables:
```bash
python database/setup_db.py
```

4. Run the service:
```bash
uvicorn app.main:app --reload --port 8001
```

## API Endpoints

### Public Endpoints (No Authentication Required)

#### `GET /routes/search`
Search for bike routes between origin and destination.

**Query Parameters:**
- `originLat` (float): Origin latitude
- `originLon` (float): Origin longitude
- `destLat` (float): Destination latitude
- `destLon` (float): Destination longitude

**Example:**
```bash
curl "http://localhost:8001/routes/search?originLat=45.4642&originLon=9.1900&destLat=45.4700&destLon=9.1950"
```

#### `GET /paths/{path_id}`
Get detailed information about a specific path.

**Example:**
```bash
curl "http://localhost:8001/paths/{path_id}"
```

### Authenticated Endpoints (Require JWT Token)

#### `POST /paths/manual`
Create a new manual path entry.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "My Bike Path",
  "description": "A scenic route",
  "segments": [
    {
      "streetName": "Main Street",
      "status": "OPTIMAL",
      "startLatitude": 45.4642,
      "startLongitude": 9.1900,
      "endLatitude": 45.4650,
      "endLongitude": 9.1910,
      "order": 0
    }
  ],
  "obstacles": [],
  "publishable": true
}
```

#### `POST /paths/obstacles`
Add an obstacle to a path segment.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "segmentId": "uuid",
  "type": "POTHOLE",
  "severity": "MODERATE",
  "latitude": 45.4645,
  "longitude": 9.1905,
  "description": "Large pothole on right side"
}
```

### Health Check

#### `GET /health`
Check service health and database connectivity.

## Path Scoring Algorithm

Routes are scored based on:
- **Segment Status Multipliers:**
  - OPTIMAL: 1.0
  - MEDIUM: 1.2
  - SUFFICIENT: 1.5
  - REQUIRES_MAINTENANCE: 2.0

- **Obstacle Penalties:**
  - MINOR: +50 meters
  - MODERATE: +150 meters
  - SEVERE: +400 meters

Lower scores indicate better routes.

## Route Search Logic

The search finds paths where:
1. The first segment starts within `TOLERANCE_RADIUS_METERS` (default 100m) of the origin
2. The last segment ends within `TOLERANCE_RADIUS_METERS` of the destination
3. The path is marked as `publishable = true`

Up to 3 routes are returned, sorted by score (best first).

## Google Maps Integration

The service can optionally use Google Maps Roads API to refine manually drawn paths:
- Validates that paths follow real roads/bike lanes
- Snaps coordinates to actual road network
- Provides interpolation between points

If the API key is not configured or the service fails, paths are stored with the original coordinates provided by the user.

## Database Schema

### PathInfo Table
Stores metadata about bike paths.

### Segments Table
Stores individual segments of each path with coordinates and status.

### Obstacles Table
Stores obstacles reported on segments with type, severity, and location.

## Development

Run tests:
```bash
python test_path_service.py
```

Interactive API documentation available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Deployment

The service is configured for deployment on Railway:

1. Create new project on Railway
2. Connect repository
3. Set environment variables in Railway dashboard
4. Deploy automatically via Procfile

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT validation (shared with user service) | Yes |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key for path refinement | Optional |
| `TOLERANCE_RADIUS_METERS` | Search tolerance radius in meters | No (default: 100) |
| `PORT` | Service port | No (default: 8001) |

## Notes

- All endpoints return JSON responses
- Coordinates must be valid (latitude: -90 to 90, longitude: -180 to 180)
- Authenticated endpoints require valid JWT token from User Management Service
- Database is shared with other BBP microservices
