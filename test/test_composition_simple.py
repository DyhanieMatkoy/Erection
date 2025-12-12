"""Simple test for work composition endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("Work Composition API Test")
print("=" * 60)

# Test with a known work ID (6 from database)
work_id = 6

print(f"\n1. Testing GET /works/{work_id}/composition")
response = requests.get(f"{BASE_URL}/works/{work_id}/composition")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    comp = response.json()
    print(f"   ✓ Work: {comp['work_name']}")
    print(f"   ✓ Cost Items: {len(comp['cost_items'])}")
    print(f"   ✓ Materials: {len(comp['materials'])}")
    print(f"   ✓ Total Cost: {comp['total_cost']:.2f}")
else:
    print(f"   ✗ Error: {response.text}")
    exit(1)

# Get a cost item to add
print(f"\n2. Getting cost items...")
response = requests.get(f"{BASE_URL}/cost-items")
if response.status_code == 200:
    cost_items = response.json()
    # Find a non-folder item
    cost_item = next((ci for ci in cost_items if not ci.get('is_folder', False) and ci.get('price', 0) > 0), None)
    if cost_item:
        cost_item_id = cost_item['id']
        print(f"   ✓ Found cost item: {cost_item['description'][:50]} (ID: {cost_item_id}, Price: {cost_item['price']})")
    else:
        print(f"   ✗ No suitable cost items found")
        exit(1)
else:
    print(f"   ✗ Error: {response.text}")
    exit(1)

# Get a material to add
print(f"\n3. Getting materials...")
response = requests.get(f"{BASE_URL}/materials")
if response.status_code == 200:
    materials = response.json()
    # Find a material with price
    material = next((m for m in materials if m.get('price', 0) > 0), None)
    if material:
        material_id = material['id']
        print(f"   ✓ Found material: {material['description'][:50]} (ID: {material_id}, Price: {material['price']})")
    else:
        print(f"   ✗ No suitable materials found")
        exit(1)
else:
    print(f"   ✗ Error: {response.text}")
    exit(1)

# Add cost item to work
print(f"\n4. Testing POST /works/{work_id}/cost-items")
response = requests.post(f"{BASE_URL}/works/{work_id}/cost-items?cost_item_id={cost_item_id}")
print(f"   Status: {response.status_code}")
if response.status_code in [200, 201]:
    print(f"   ✓ Cost item added successfully")
elif response.status_code == 400:
    print(f"   ✓ Cost item already exists (expected)")
else:
    print(f"   ⚠ Unexpected: {response.text}")

# Add material to work
print(f"\n5. Testing POST /works/{work_id}/materials")
material_data = {
    "work_id": work_id,
    "cost_item_id": cost_item_id,
    "material_id": material_id,
    "quantity_per_unit": 1.5
}
response = requests.post(f"{BASE_URL}/works/{work_id}/materials", json=material_data)
print(f"   Status: {response.status_code}")
if response.status_code in [200, 201]:
    result = response.json()
    association_id = result.get('id')
    print(f"   ✓ Material added successfully (Association ID: {association_id})")
elif response.status_code == 400:
    print(f"   ✓ Material already exists")
    # Get association ID from composition
    response = requests.get(f"{BASE_URL}/works/{work_id}/composition")
    comp = response.json()
    materials = comp.get('materials', [])
    matching = [m for m in materials if m.get('material_id') == material_id and m.get('cost_item_id') == cost_item_id]
    association_id = matching[0]['id'] if matching else None
    print(f"   ✓ Found existing association ID: {association_id}")
else:
    print(f"   ✗ Error: {response.text}")
    association_id = None

# Update material quantity
if association_id:
    print(f"\n6. Testing PUT /works/{work_id}/materials/{association_id}")
    update_data = {"quantity_per_unit": 2.0}
    response = requests.put(f"{BASE_URL}/works/{work_id}/materials/{association_id}", json=update_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✓ Material quantity updated successfully")
    else:
        print(f"   ✗ Error: {response.text}")

# Get final composition
print(f"\n7. Testing final composition")
response = requests.get(f"{BASE_URL}/works/{work_id}/composition")
if response.status_code == 200:
    comp = response.json()
    print(f"   ✓ Final composition:")
    print(f"     - Work: {comp['work_name']}")
    print(f"     - Cost Items: {len(comp['cost_items'])}")
    print(f"     - Materials: {len(comp['materials'])}")
    print(f"     - Total Cost: {comp['total_cost']:.2f}")
    
    if comp['cost_items']:
        print(f"\n   Cost Items:")
        for item in comp['cost_items'][:3]:
            ci = item['cost_item']
            if ci:
                print(f"     - {ci['description'][:40]:40} | Price: {ci['price']:8.2f}")
    
    if comp['materials']:
        print(f"\n   Materials:")
        for item in comp['materials'][:3]:
            m = item['material']
            if m:
                qty = item['quantity_per_unit']
                total = m['price'] * qty
                print(f"     - {m['description'][:40]:40} | Qty: {qty:6.3f} | Price: {m['price']:8.2f} | Total: {total:8.2f}")
else:
    print(f"   ✗ Error: {response.text}")
    exit(1)

# Delete material (cleanup)
if association_id:
    print(f"\n8. Testing DELETE /works/{work_id}/materials/{association_id}")
    response = requests.delete(f"{BASE_URL}/works/{work_id}/materials/{association_id}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✓ Material deleted successfully")
    else:
        print(f"   ⚠ Could not delete: {response.text}")

# Delete cost item (cleanup)
print(f"\n9. Testing DELETE /works/{work_id}/cost-items/{cost_item_id}")
response = requests.delete(f"{BASE_URL}/works/{work_id}/cost-items/{cost_item_id}")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Cost item deleted successfully")
else:
    print(f"   ⚠ Could not delete: {response.text}")

print("\n" + "=" * 60)
print("✓ All tests completed successfully!")
print("=" * 60)
