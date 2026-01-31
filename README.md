# BBP Path Management Service

Microservice for managing bike paths, route search, and obstacle reporting.

## Overview

Handles all path-related operations including route search using OSRM, manual path creation, segment management, and obstacle reporting. Uses PostgreSQL for data persistence.

## Features

- **Route Search**: Find optimal bike routes using OSRM
- **Manual Path Creation**: Create paths with custom segments
- **Obstacle Reporting**: Report and track road obstacles
- **Segment Scoring**: Rate path segments (optimal/medium/difficult)
- **Geocoding**: Address lookup via Nominatim API

## Tech Stack

- FastAPI
- PostgreSQL (psycopg2)
- OSRM (routing)
- Nominatim (geocoding)
- Python-Jose (JWT)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/routes/search` | Search routes between points |
| POST | `/paths/manual` | Create manual path |
| GET | `/paths/{id}` | Get path details |
| POST | `/paths/obstacles` | Report obstacle |
| GET | `/paths/obstacles/{segment_id}` | Get segment obstacles |

## Database Tables

- `path_info` - Path metadata
- `segments` - Path segments with coordinates
- `obstacles` - Reported obstacles

## Environment Variables

```
DATABASE_URL=<postgresql-url>
JWT_SECRET_KEY=<secret-key>
```

## Running Locally

```bash
pip install -r requirements.txt
python database/setup_db.py  # Initialize tables
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Deployment

Deployed on Railway. See `Procfile` for startup command.
