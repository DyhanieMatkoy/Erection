#!/usr/bin/env python3

# Simple test to check if we can import the production config test runner

try:
    print("Attempting to import production_config_test_runner module...")
    import production_config_test_runner
    print("✓ Module imported successfully")
    
    print("Available attributes in module:")
    attrs = [attr for attr in dir(production_config_test_runner) if not attr.startswith('_')]
    for attr in attrs:
        print(f"  - {attr}")
    
    print("\nTrying to import ProductionConfigTestRunner class...")
    from production_config_test_runner import ProductionConfigTestRunner
    print("✓ ProductionConfigTestRunner imported successfully")
    
    print("\nTrying to create instance...")
    runner = ProductionConfigTestRunner()
    print("✓ Instance created successfully")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Other error: {e}")
    import traceback
    traceback.print_exc()