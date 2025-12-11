"""Test API login endpoint with SHA256"""
import requests
import json

# API endpoint
url = "http://localhost:8000/api/auth/login"

# Login credentials
payload = {
    "username": "admin",
    "password": "admin"
}

print("Testing API login endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✓ Login successful!")
        data = response.json()
        print(f"  Token: {data.get('access_token', 'N/A')[:50]}...")
        print(f"  User: {data.get('user', {}).get('username', 'N/A')}")
        print(f"  Role: {data.get('user', {}).get('role', 'N/A')}")
    else:
        print("\n✗ Login failed!")
        
except requests.exceptions.ConnectionError:
    print("✗ Could not connect to API server")
    print("  Make sure the server is running on http://localhost:8000")
except Exception as e:
    print(f"✗ Error: {e}")
