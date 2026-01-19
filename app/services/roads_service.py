import httpx
from typing import List, Dict, Optional
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class RoadsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://roads.googleapis.com/v1"
        self.timeout = 5.0

    async def snap_to_roads(self, coordinates: List[Dict[str, float]]) -> Optional[List[Dict[str, float]]]:
        if not self.api_key
            logger.warning("Google Maps API key not configured, skipping path refinement")
            return None

        if not coordinates or len(coordinates) < 2:
            logger.warning("Not enough coordinates for path refinement")
            return None

        try:
            points_param = "|".join([f"{coord['latitude']},{coord['longitude']}" for coord in coordinates])

            if len(points_param) > 2000:
                logger.warning("Too many points for single API call, using first 100 points")
                points_param = "|".join([f"{coord['latitude']},{coord['longitude']}" for coord in coordinates[:100]])

            url = f"{self.base_url}/snapToRoads"
            params = {
                "path": points_param,
                "interpolate": "true",
                "key": self.api_key
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    if "snappedPoints" in data:
                        snapped_coords = []
                        for point in data["snappedPoints"]:
                            location = point.get("location", {})
                            snapped_coords.append({
                                "latitude": location.get("latitude"),
                                "longitude": location.get("longitude")
                            })

                        logger.info(f"Successfully snapped {len(coordinates)} points to {len(snapped_coords)} road points")
                        return snapped_coords
                    else:
                        logger.warning("No snapped points in API response")
                        return None
                else:
                    logger.error(f"Google Maps Roads API error: {response.status_code} - {response.text}")
                    return None

        except httpx.TimeoutException:
            logger.error("Google Maps Roads API timeout")
            return None
        except Exception as e:
            logger.error(f"Error calling Google Maps Roads API: {e}")
            return None

roads_service = RoadsService()
