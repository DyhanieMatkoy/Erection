#!/usr/bin/env python3
"""
Test script to verify hierarchy navigation works correctly
"""

import sys
import os

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager
from src.data.repositories.work_repository import WorkRepository

def test_hierarchy_navigation():
    """Test hierarchy navigation functionality"""
    print("=== Testing Hierarchy Navigation ===")
    
    db_manager = DatabaseManager()
    db_manager.initialize()
    work_repo = WorkRepository(db_manager)
    
    # Test 1: Get root level works (parent_id is None or 0)
    print("\n1. Root level works:")
    root_works = work_repo.find_children(None)
    print(f"   Found {len(root_works)} root level works")
    
    # Show first few root works
    for i, work in enumerate(root_works[:5]):
        icon = "📁" if work['is_group'] else "📄"
        print(f"   {icon} ID: {work['id']}, Name: {work['name']}")
    
    # Test 2: Find "БЛАГОУСТРОЙСТВО И МАЛЫЕ ФОРМЫ" and its children
    print("\n2. Testing 'БЛАГОУСТРОЙСТВО И МАЛЫЕ ФОРМЫ':")
    target_work = None
    for work in root_works:
        if "Благоустройство" in work['name']:
            target_work = work
            break
    
    if target_work:
        print(f"   Found: ID {target_work['id']}, Name: {target_work['name']}")
        print(f"   Is group: {target_work['is_group']}")
        
        # Get its children
        children = work_repo.find_children(target_work['id'])
        print(f"   Children count: {len(children)}")
        
        # Show first few children
        for i, child in enumerate(children[:5]):
            icon = "📁" if child['is_group'] else "📄"
            print(f"     {icon} ID: {child['id']}, Name: {child['name']}")
    else:
        print("   Not found in root level!")
    
    # Test 3: Test navigation simulation
    print("\n3. Navigation simulation:")
    current_parent_id = None
    print(f"   Current level: Root (parent_id = {current_parent_id})")
    
    # Simulate Ctrl+Down on first group
    current_works = work_repo.find_children(current_parent_id)
    first_group = None
    for work in current_works:
        if work['is_group']:
            first_group = work
            break
    
    if first_group:
        print(f"   Ctrl+Down on: {first_group['name']}")
        current_parent_id = first_group['id']
        
        # Get children
        children = work_repo.find_children(current_parent_id)
        print(f"   New level: {first_group['name']} (parent_id = {current_parent_id})")
        print(f"   Children count: {len(children)}")
        
        # Show first few children
        for i, child in enumerate(children[:3]):
            icon = "📁" if child['is_group'] else "📄"
            print(f"     {icon} {child['name']}")
        
        # Simulate Ctrl+Up
        print(f"   Ctrl+Up from: {first_group['name']}")
        parent_work = work_repo.find_by_id(current_parent_id)
        if parent_work:
            current_parent_id = parent_work['parent_id']
            print(f"   Back to: Root (parent_id = {current_parent_id})")
        else:
            print("   Error: Could not find parent work!")
    else:
        print("   No groups found at root level!")

if __name__ == "__main__":
    test_hierarchy_navigation()