"""
Test script to verify Google Maps Roads API integration for path refinement.

This script demonstrates:
1. Creating a path without API key (uses original coordinates)
2. Creating a path with valid API key (coordinates get refined/snapped to roads)
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8001"
# Replace with a valid JWT token from the user-management-service
AUTH_TOKEN = "your-jwt-token-here"

def test_manual_path_creation():
    """Test creating a manual path - coordinates should be refined by Google Maps Roads API"""

    url = f"{BASE_URL}/paths/manual"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    # Test path in Milano, Italy
    payload = {
        "name": "Test Path Refinement - Milano",
        "description": "Path to test Google Maps Roads API integration",
        "segments": [
            {
                "streetName": None,
                "status": "OPTIMAL",
                "startLatitude": 45.4520,
                "startLongitude": 9.1700,
                "endLatitude": 45.4700,
                "endLongitude": 9.1750,
                "order": 1
            },
            {
                "streetName": None,
                "status": "OPTIMAL",
                "startLatitude": 45.4700,
                "startLongitude": 9.1750,
                "endLatitude": 45.4800,
                "endLongitude": 9.2000,
                "order": 2
            },
            {
                "streetName": None,
                "status": "OPTIMAL",
                "startLatitude": 45.4800,
                "startLongitude": 9.2000,
                "endLatitude": 45.4780,
                "endLongitude": 9.1950,
                "order": 3
            }
        ],
        "obstacles": [],
        "publishable": True
    }

    print("=" * 80)
    print("Testing Path Creation with Google Maps Roads API Refinement")
    print("=" * 80)
    print(f"\nSending request to: {url}")
    print(f"Original segments: {len(payload['segments'])}")
    print("\nOriginal coordinates:")
    for seg in payload["segments"]:
        print(f"  Segment {seg['order']}: ({seg['startLatitude']}, {seg['startLongitude']}) -> ({seg['endLatitude']}, {seg['endLongitude']})")

    response = requests.post(url, json=payload, headers=headers)

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        path_id = response.json().get("pathInfoId")
        print(f"\n✅ Path created successfully with ID: {path_id}")

        # Retrieve the created path to see refined segments
        get_url = f"{BASE_URL}/paths/{path_id}"
        get_response = requests.get(get_url)

        if get_response.status_code == 200:
            path_data = get_response.json()
            refined_segments = path_data.get("segments", [])

            print(f"\n📊 Path Details:")
            print(f"   Total segments after refinement: {len(refined_segments)}")
            print(f"   Total distance: {path_data.get('totalDistance')} km")
            print(f"   Score: {path_data.get('score')}")

            if len(refined_segments) > len(payload['segments']):
                print(f"\n✅ Path was refined! Google Maps added {len(refined_segments) - len(payload['segments'])} intermediate points")
                print("\nRefined segments (first 5):")
                for seg in refined_segments[:5]:
                    print(f"  ({seg['startLatitude']:.6f}, {seg['startLongitude']:.6f}) -> ({seg['endLatitude']:.6f}, {seg['endLongitude']:.6f})")
                if len(refined_segments) > 5:
                    print(f"  ... and {len(refined_segments) - 5} more segments")
            else:
                print(f"\n⚠️  Path was NOT refined (using original coordinates)")
                print("   Possible reasons:")
                print("   - Google Maps API key not configured")
                print("   - API key invalid or expired")
                print("   - API request failed or timed out")
                print("   - Coordinates are not near roads")

        return path_id
    else:
        print(f"\n❌ Failed to create path: {response.text}")
        return None

def check_service_health():
    """Check if the service is running"""
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Service is healthy: {response.json()}")
            return True
        else:
            print(f"⚠️  Service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Service is not reachable: {e}")
        return False

if __name__ == "__main__":
    print("\n🚴 BBP Path Management - Google Maps Roads API Test\n")

    # Check service health
    if not check_service_health():
        print("\n❌ Please start the path-management-service first:")
        print("   cd path-management-service")
        print("   uvicorn app.main:app --reload --port 8001")
        exit(1)

    print("\n")

    # Test path creation
    if AUTH_TOKEN == "your-jwt-token-here":
        print("⚠️  Please set a valid AUTH_TOKEN in the script")
        print("   You can get a token by logging in via the user-management-service")
        exit(1)

    path_id = test_manual_path_creation()

    if path_id:
        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        print("=" * 80)
        print(f"\nYou can view the path details at: {BASE_URL}/paths/{path_id}")
        print("\nTo verify Google Maps API is being called:")
        print("1. Check the service logs for 'Path refined' or 'Path refinement' messages")
        print("2. Check your Google Cloud Console API dashboard for Roads API requests")
    else:
        print("\n" + "=" * 80)
        print("❌ Test failed")
        print("=" * 80)
