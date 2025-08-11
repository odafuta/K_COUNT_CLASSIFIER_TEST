#!/usr/bin/env python3
"""
Test script for previous simulated annealing versions
"""

import sys
import time

def test_previous_version(version_name, module_name):
    """Test a previous version of simulated annealing"""
    print(f"\n=== Testing {version_name} ===")
    
    try:
        # Import the module
        module = __import__(module_name)
        
        # Test with small parameters
        print("Running with n=10, tau=2, k=5...")
        start_time = time.time()
        
        result = module.lv_cit_sa(10, 2, 5, verbose=True)
        
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"Error in {version_name}: {e}")
        return False

def main():
    """Main test function"""
    print("Testing previous simulated annealing versions...")
    
    # Test v2
    success_v2 = test_previous_version("v2", "previous_simulated_annealing_v2")
    
    # Test v3
    success_v3 = test_previous_version("v3", "previous_simulated_annealing_v3")
    
    print(f"\n=== Summary ===")
    print(f"v2: {'SUCCESS' if success_v2 else 'FAILED'}")
    print(f"v3: {'SUCCESS' if success_v3 else 'FAILED'}")

if __name__ == "__main__":
    main() 