"""
Test web authentication flow
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_login():
    """Test login endpoint"""
    print("Testing login...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"\nToken: {token[:50]}...")
        return token
    
    return None


def test_estimates_list(token):
    """Test estimates list with token"""
    print("\n\nTesting estimates list...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/documents/estimates",
        headers=headers,
        params={"page": 1, "page_size": 50}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Items count: {len(data.get('data', []))}")
    else:
        print(f"Error: {response.text}")


def test_estimates_list_without_token():
    """Test estimates list without token"""
    print("\n\nTesting estimates list WITHOUT token...")
    
    response = requests.get(
        f"{BASE_URL}/documents/estimates",
        params={"page": 1, "page_size": 50}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


if __name__ == "__main__":
    # Test without token first
    test_estimates_list_without_token()
    
    # Test login
    token = test_login()
    
    if token:
        # Test with token
        test_estimates_list(token)
