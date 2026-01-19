import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_route_search():
    print("\n=== Testing Route Search (Public) ===")

    params = {
        "originLat": 45.4642,
        "originLon": 9.1900,
        "destLat": 45.4700,
        "destLon": 9.1950
    }

    response = requests.get(f"{BASE_URL}/routes/search", params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_create_manual_path(token):
    print("\n=== Testing Create Manual Path ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "name": "Test Bike Path",
        "description": "A test path for development",
        "segments": [
            {
                "streetName": "Via Roma",
                "status": "OPTIMAL",
                "startLatitude": 45.4642,
                "startLongitude": 9.1900,
                "endLatitude": 45.4650,
                "endLongitude": 9.1910,
                "order": 0
            },
            {
                "streetName": "Via Milano",
                "status": "MEDIUM",
                "startLatitude": 45.4650,
                "startLongitude": 9.1910,
                "endLatitude": 45.4700,
                "endLongitude": 9.1950,
                "order": 1
            }
        ],
        "obstacles": [],
        "publishable": True
    }

    response = requests.post(f"{BASE_URL}/paths/manual", headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        return response.json()["pathInfoId"]
    return None

def test_add_obstacle(token, segment_id):
    print("\n=== Testing Add Obstacle ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "segmentId": segment_id,
        "type": "POTHOLE",
        "severity": "MODERATE",
        "latitude": 45.4645,
        "longitude": 9.1905,
        "description": "Large pothole on the right side"
    }

    response = requests.post(f"{BASE_URL}/paths/obstacles", headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_path_details(path_id):
    print("\n=== Testing Get Path Details (Public) ===")

    response = requests.get(f"{BASE_URL}/paths/{path_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("BBP Path Management Service - Manual Tests")
    print("=" * 50)

    try:
        test_health()
    except Exception as e:
        print(f"Health check failed: {e}")

    try:
        test_route_search()
    except Exception as e:
        print(f"Route search test error: {e}")

    token = input("\nEnter JWT token for authenticated tests (or press Enter to skip): ").strip()

    if token:
        try:
            path_id = test_create_manual_path(token)

            if path_id:
                print(f"\nCreated path ID: {path_id}")
                test_get_path_details(path_id)
        except Exception as e:
            print(f"Create manual path test error: {e}")
    else:
        print("\nSkipping authenticated tests")

    print("\n" + "=" * 50)
    print("Tests completed!")
