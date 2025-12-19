#!/usr/bin/env python3
"""Test API endpoints after migration

This script tests that API endpoints work correctly with the new unit structure.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from api.main import app

def test_works_endpoints():
    """Test works-related endpoints"""
    client = TestClient(app)
    
    print("Testing API endpoints...")
    print("=" * 80)
    
    # Test 1: List works
    print("\n1. Testing GET /api/references/works")
    response = client.get("/api/references/works", params={"page": 1, "page_size": 10})
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total items: {data.get('total', 0)}")
        print(f"   Items returned: {len(data.get('items', []))}")
        
        # Check if unit information is included
        if data.get('items'):
            first_item = data['items'][0]
            has_unit_id = 'unit_id' in first_item
            has_unit_name = 'unit_name' in first_item
            print(f"   Has unit_id field: {has_unit_id}")
            print(f"   Has unit_name field: {has_unit_name}")
            
            if has_unit_id and first_item['unit_id']:
                print(f"   Sample unit_id: {first_item['unit_id']}")
            if has_unit_name and first_item['unit_name']:
                print(f"   Sample unit_name: {first_item['unit_name']}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 2: List works with explicit unit info
    print("\n2. Testing GET /api/references/works with include_unit_info=true")
    response = client.get("/api/references/works", params={
        "page": 1,
        "page_size": 10,
        "include_unit_info": True
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Items returned: {len(data.get('items', []))}")
        
        # Check unit information
        items_with_units = sum(1 for item in data.get('items', []) if item.get('unit_id'))
        print(f"   Items with unit_id: {items_with_units}/{len(data.get('items', []))}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 3: Get specific work
    print("\n3. Testing GET /api/references/works/{id}")
    # First get a work ID
    response = client.get("/api/references/works", params={"page": 1, "page_size": 1})
    if response.status_code == 200 and response.json().get('items'):
        work_id = response.json()['items'][0]['id']
        
        response = client.get(f"/api/references/works/{work_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            work = response.json()
            print(f"   Work ID: {work.get('id')}")
            print(f"   Work name: {work.get('name', '')[:50]}")
            print(f"   Unit ID: {work.get('unit_id')}")
            print(f"   Unit name: {work.get('unit_name')}")
        else:
            print(f"   Error: {response.text}")
    
    # Test 4: List units
    print("\n4. Testing GET /api/references/units")
    response = client.get("/api/references/units", params={"page": 1, "page_size": 10})
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total units: {data.get('total', 0)}")
        print(f"   Items returned: {len(data.get('items', []))}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 5: Search works
    print("\n5. Testing GET /api/references/works with search")
    response = client.get("/api/references/works", params={
        "page": 1,
        "page_size": 10,
        "search": "демонтаж"
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Search results: {len(data.get('items', []))}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 6: Filter works by unit
    print("\n6. Testing GET /api/references/works filtered by unit_id")
    # Get a unit ID first
    response = client.get("/api/references/units", params={"page": 1, "page_size": 1})
    if response.status_code == 200 and response.json().get('items'):
        unit_id = response.json()['items'][0]['id']
        
        response = client.get("/api/references/works", params={
            "page": 1,
            "page_size": 10,
            "unit_id": unit_id
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Works with unit_id {unit_id}: {len(data.get('items', []))}")
        else:
            print(f"   Error: {response.text}")
    
    print("\n" + "=" * 80)
    print("API endpoint testing completed!")


if __name__ == '__main__':
    try:
        test_works_endpoints()
    except Exception as e:
        print(f"Error during API testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)