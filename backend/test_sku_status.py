#!/usr/bin/env python3
"""
Test script to verify SKU status functionality
"""

import os
import sys

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from sku_tracker import load_status, save_status, mark_completed, is_completed

def test_sku_status():
    """Test the SKU status functionality"""
    print("🧪 Testing SKU status functionality...")
    
    # Test 1: Load initial status
    print("\n1. Loading initial status...")
    status = load_status()
    print(f"   Initial status: {status}")
    
    # Test 2: Create a test SKU entry
    print("\n2. Creating test SKU entry...")
    test_sku = "TEST_SKU_001"
    status[test_sku] = {"myntra": False, "meesho": False, "flipkart": False}
    save_status(status)
    print(f"   Created test SKU: {test_sku}")
    
    # Test 3: Mark as completed
    print("\n3. Marking test SKU as completed for Flipkart...")
    mark_completed(test_sku, "flipkart")
    
    # Test 4: Check completion status
    print("\n4. Checking completion status...")
    is_flipkart_completed = is_completed(test_sku, "flipkart")
    print(f"   Flipkart completed: {is_flipkart_completed}")
    
    # Test 5: Load final status
    print("\n5. Loading final status...")
    final_status = load_status()
    print(f"   Final status: {final_status}")
    
    # Test 6: Clean up test data
    print("\n6. Cleaning up test data...")
    if test_sku in final_status:
        del final_status[test_sku]
        save_status(final_status)
        print(f"   Removed test SKU: {test_sku}")
    
    print("\n✅ SKU status test completed successfully!")

if __name__ == "__main__":
    test_sku_status() 