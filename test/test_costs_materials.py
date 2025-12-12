#!/usr/bin/env python3
"""Test script for Cost Items and Materials repositories"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.repositories.cost_item_repository import CostItemRepository
from src.data.repositories.material_repository import MaterialRepository
from src.data.database_manager import DatabaseManager

# Initialize database
db_manager = DatabaseManager()
db_manager.initialize()

def test_cost_items():
    """Test CostItemRepository"""
    print("Testing CostItemRepository...")
    repo = CostItemRepository()
    
    # Test find_all
    cost_items = repo.find_all()
    print(f"Found {len(cost_items)} cost items")
    
    if cost_items:
        print("First cost item:")
        print(f"  ID: {cost_items[0]['id']}")
        print(f"  Code: {cost_items[0]['code']}")
        print(f"  Description: {cost_items[0]['description']}")
        print(f"  Is Folder: {cost_items[0]['is_folder']}")
        print(f"  Price: {cost_items[0]['price']}")
        print(f"  Unit: {cost_items[0]['unit']}")
    
    print("CostItemRepository test completed successfully!\n")

def test_materials():
    """Test MaterialRepository"""
    print("Testing MaterialRepository...")
    repo = MaterialRepository()
    
    # Test find_all
    materials = repo.find_all()
    print(f"Found {len(materials)} materials")
    
    if materials:
        print("First material:")
        print(f"  ID: {materials[0]['id']}")
        print(f"  Code: {materials[0]['code']}")
        print(f"  Description: {materials[0]['description']}")
        print(f"  Price: {materials[0]['price']}")
        print(f"  Unit: {materials[0]['unit']}")
    
    # Test search_by_description
    if materials:
        search_term = materials[0]['description'][:5] if materials[0]['description'] else "test"
        search_results = repo.search_by_description(search_term)
        print(f"Search for '{search_term}' returned {len(search_results)} results")
    
    print("MaterialRepository test completed successfully!\n")

if __name__ == "__main__":
    try:
        test_cost_items()
        test_materials()
        print("All tests passed successfully!")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)