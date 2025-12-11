"""
Test references API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# Login first
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "admin"}
)

if response.status_code != 200:
    print("Login failed!")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test each reference endpoint
endpoints = [
    "counterparties",
    "objects",
    "works",
    "persons",
    "organizations"
]

for endpoint in endpoints:
    print(f"\nTesting {endpoint}...")
    response = requests.get(
        f"{BASE_URL}/references/{endpoint}",
        headers=headers,
        params={"page": 1, "page_size": 1000}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Items count: {len(data.get('data', []))}")
        if len(data.get('data', [])) > 0:
            print(f"First item: {data['data'][0]}")
    else:
        print(f"Error: {response.text}")
