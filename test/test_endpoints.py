"""Test individual endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("Testing Units endpoint...")
response = requests.get(f"{BASE_URL}/units")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

print("\nTesting Cost Items endpoint...")
response = requests.get(f"{BASE_URL}/cost-items")
print(f"Status: {response.status_code}")
try:
    data = response.json()
    if isinstance(data, list):
        print(f"Found {len(data)} items")
        if data:
            print(f"First item: {data[0]}")
    else:
        print(f"Response: {data}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Raw response: {response.text}")

print("\nTesting Materials endpoint...")
response = requests.get(f"{BASE_URL}/materials")
print(f"Status: {response.status_code}")
try:
    data = response.json()
    if isinstance(data, list):
        print(f"Found {len(data)} materials")
        if data:
            print(f"First material: {data[0]}")
    else:
        print(f"Response: {data}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Raw response: {response.text}")
