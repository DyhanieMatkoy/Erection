#!/usr/bin/env python3

# Debug script to find the issue with production_config_test_runner

import sys
import traceback

print("Python version:", sys.version)
print("Current working directory:", sys.path[0])

try:
    print("\n=== Attempting to import production_config_test_runner ===")
    
    # Try to execute the file directly to see any runtime errors
    with open('production_config_test_runner.py', 'r') as f:
        code = f.read()
    
    print("File read successfully, attempting to compile...")
    compiled = compile(code, 'production_config_test_runner.py', 'exec')
    print("✓ Code compiled successfully")
    
    print("Attempting to execute...")
    namespace = {}
    exec(compiled, namespace)
    print("✓ Code executed successfully")
    
    print("Available names in namespace:")
    for name in sorted(namespace.keys()):
        if not name.startswith('_'):
            print(f"  - {name}: {type(namespace[name])}")
    
    if 'ProductionConfigTestRunner' in namespace:
        print("✓ ProductionConfigTestRunner found in namespace")
    else:
        print("✗ ProductionConfigTestRunner NOT found in namespace")
        
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()