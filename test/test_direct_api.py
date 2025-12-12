"""Direct API test using TestClient"""
from fastapi.testclient import TestClient
from start_server import app

client = TestClient(app)

print("Testing POST /works/6/cost-items...")
response = client.post("/api/works/6/cost-items?cost_item_id=120")
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code not in [200, 201, 400]:
    print("\nTrying with a different cost item...")
    response = client.post("/api/works/6/cost-items?cost_item_id=121")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
