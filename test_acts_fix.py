#!/usr/bin/env python3
"""
ACTS修正のテストスクリプト
"""

from acts_runner import run_acts_covering_array

def test_acts_fix():
    """ACTS修正のテスト"""
    print("Testing ACTS fix...")
    
    # 小さなテストケース
    n, tau, k = 5, 2, 2
    
    result = run_acts_covering_array(n=n, tau=tau, k=k, verbose=True)
    
    print(f"Result: {result}")
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS: Generated {result['num_rows']} rows")
        return True

if __name__ == "__main__":
    success = test_acts_fix()
    if success:
        print("ACTS test passed!")
    else:
        print("ACTS test failed!") 