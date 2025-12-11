"""
Simple API test script
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"✓ Health check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_units():
    """Test units endpoint"""
    response = requests.get(f"{BASE_URL}/units")
    if response.status_code == 200:
        units = response.json()
        print(f"✓ Units: {response.status_code} - Found {len(units)} units")
        if units:
            print(f"  First unit: {units[0]}")
        return True
    else:
        print(f"✗ Units: {response.status_code} - {response.text}")
        return False

def test_cost_items():
    """Test cost items endpoint"""
    response = requests.get(f"{BASE_URL}/cost-items")
    if response.status_code == 200:
        items = response.json()
        print(f"✓ Cost Items: {response.status_code} - Found {len(items)} items")
        return True
    else:
        print(f"✗ Cost Items: {response.status_code} - {response.text}")
        return False

def test_materials():
    """Test materials endpoint"""
    response = requests.get(f"{BASE_URL}/materials")
    if response.status_code == 200:
        materials = response.json()
        print(f"✓ Materials: {response.status_code} - Found {len(materials)} materials")
        return True
    else:
        print(f"✗ Materials: {response.status_code} - {response.text}")
        return False

def test_work_composition():
    """Test work composition endpoint"""
    # Use a known work ID (6 exists in database)
    work_id = 6
    response = requests.get(f"{BASE_URL}/works/{work_id}/composition")
    if response.status_code == 200:
        comp = response.json()
        print(f"✓ Work Composition: {response.status_code}")
        print(f"  Work: {comp.get('work_name')}")
        print(f"  Cost Items: {len(comp.get('cost_items', []))}")
        print(f"  Materials: {len(comp.get('materials', []))}")
        print(f"  Total Cost: {comp.get('total_cost', 0)}")
        return True
    else:
        print(f"✗ Work Composition: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("API Test Suite")
    print("=" * 60)
    print("\nMake sure the server is running: python start_server.py\n")
    
    try:
        results = []
        results.append(("Health Check", test_health()))
        results.append(("Units", test_units()))
        results.append(("Cost Items", test_cost_items()))
        results.append(("Materials", test_materials()))
        results.append(("Work Composition", test_work_composition()))
        
        print("\n" + "=" * 60)
        print("Test Results:")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Please start the server first: python start_server.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
