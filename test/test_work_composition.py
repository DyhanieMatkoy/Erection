"""Test work composition functionality"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_work_composition():
    """Test complete work composition workflow"""
    print("=" * 60)
    print("Work Composition Test")
    print("=" * 60)
    
    # 1. Get a work
    print("\n1. Getting works...")
    response = requests.get(f"{BASE_URL}/references/works")
    if response.status_code != 200:
        print(f"✗ Failed to get works: {response.status_code}")
        return False
    
    data = response.json()
    works = data.get('data', [])
    if not works:
        print("✗ No works found in database")
        return False
    
    work = works[0]
    work_id = work['id']
    print(f"✓ Found work: {work['name']} (ID: {work_id})")
    
    # 2. Get cost items
    print("\n2. Getting cost items...")
    response = requests.get(f"{BASE_URL}/cost-items")
    if response.status_code != 200:
        print(f"✗ Failed to get cost items: {response.status_code}")
        return False
    
    cost_items = response.json()
    if not cost_items:
        print("✗ No cost items found")
        return False
    
    # Find a non-folder cost item
    cost_item = next((ci for ci in cost_items if not ci.get('is_folder', False)), None)
    if not cost_item:
        print("✗ No non-folder cost items found")
        return False
    
    cost_item_id = cost_item['id']
    print(f"✓ Found cost item: {cost_item['description'][:50]} (ID: {cost_item_id})")
    
    # 3. Get materials
    print("\n3. Getting materials...")
    response = requests.get(f"{BASE_URL}/materials")
    if response.status_code != 200:
        print(f"✗ Failed to get materials: {response.status_code}")
        return False
    
    materials = response.json()
    if not materials:
        print("✗ No materials found")
        return False
    
    material = materials[0]
    material_id = material['id']
    print(f"✓ Found material: {material['description'][:50]} (ID: {material_id})")
    
    # 4. Get current composition
    print(f"\n4. Getting current composition for work {work_id}...")
    response = requests.get(f"{BASE_URL}/works/{work_id}/composition")
    if response.status_code != 200:
        print(f"✗ Failed to get composition: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    comp = response.json()
    print(f"✓ Current composition:")
    print(f"   Work: {comp.get('work_name')}")
    print(f"   Cost Items: {len(comp.get('cost_items', []))}")
    print(f"   Materials: {len(comp.get('materials', []))}")
    print(f"   Total Cost: {comp.get('total_cost', 0):.2f}")
    
    # 5. Add cost item to work (if not already there)
    print(f"\n5. Adding cost item {cost_item_id} to work {work_id}...")
    response = requests.post(f"{BASE_URL}/works/{work_id}/cost-items?cost_item_id={cost_item_id}")
    if response.status_code in [200, 201]:
        print(f"✓ Cost item added successfully")
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print(f"✓ Cost item already exists in work")
    else:
        print(f"⚠ Unexpected response: {response.status_code} - {response.text}")
    
    # 6. Add material to work
    print(f"\n6. Adding material {material_id} to work {work_id}...")
    material_data = {
        "work_id": work_id,
        "cost_item_id": cost_item_id,
        "material_id": material_id,
        "quantity_per_unit": 0.5
    }
    response = requests.post(
        f"{BASE_URL}/works/{work_id}/materials",
        json=material_data
    )
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✓ Material added successfully (Association ID: {result.get('id')})")
        association_id = result.get('id')
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print(f"✓ Material already exists in work")
        # Get the association ID from composition
        response = requests.get(f"{BASE_URL}/works/{work_id}/composition")
        comp = response.json()
        materials = comp.get('materials', [])
        matching = [m for m in materials if m.get('material_id') == material_id]
        association_id = matching[0]['association_id'] if matching else None
    else:
        print(f"⚠ Unexpected response: {response.status_code} - {response.text}")
        association_id = None
    
    # 7. Update material quantity
    if association_id:
        print(f"\n7. Updating material quantity (Association ID: {association_id})...")
        update_data = {"quantity_per_unit": 0.75}
        response = requests.put(
            f"{BASE_URL}/works/{work_id}/materials/{association_id}",
            json=update_data
        )
        if response.status_code == 200:
            print(f"✓ Material quantity updated successfully")
        else:
            print(f"⚠ Failed to update: {response.status_code} - {response.text}")
    
    # 8. Get final composition
    print(f"\n8. Getting final composition...")
    response = requests.get(f"{BASE_URL}/works/{work_id}/composition")
    if response.status_code == 200:
        comp = response.json()
        print(f"✓ Final composition:")
        print(f"   Work: {comp.get('work_name')}")
        print(f"   Cost Items: {len(comp.get('cost_items', []))}")
        print(f"   Materials: {len(comp.get('materials', []))}")
        print(f"   Total Cost: {comp.get('total_cost', 0):.2f}")
        
        # Show first few items
        if comp.get('cost_items'):
            print(f"\n   First cost item:")
            ci = comp['cost_items'][0]
            print(f"     - {ci.get('description', 'N/A')[:50]}")
            print(f"     - Price: {ci.get('price', 0):.2f}")
        
        if comp.get('materials'):
            print(f"\n   First material:")
            m = comp['materials'][0]
            print(f"     - {m.get('description', 'N/A')[:50]}")
            print(f"     - Quantity: {m.get('quantity_per_unit', 0):.3f}")
            print(f"     - Price: {m.get('price', 0):.2f}")
            print(f"     - Total: {m.get('total_cost', 0):.2f}")
    else:
        print(f"✗ Failed to get final composition: {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All work composition tests completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_work_composition()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Please start the server first: python start_server.py")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
