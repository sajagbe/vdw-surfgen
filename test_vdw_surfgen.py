#!/usr/bin/env python3
"""
Simple test for vdw-surfgen deployment automation.
This file will be automatically discovered and run by auto_deploy.py
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that the package can be imported."""
    try:
        import vdw_surfgen
        print("✅ vdw_surfgen package imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import vdw_surfgen: {e}")
        return False

def test_cli_module():
    """Test that CLI module exists and has required functions."""
    try:
        from vdw_surfgen import cli
        required_functions = ['main', 'read_xyz_file', 'generate_surface']
        
        for func_name in required_functions:
            if not hasattr(cli, func_name):
                print(f"❌ Missing function: {func_name}")
                return False
                
        print("✅ CLI module has all required functions")
        return True
    except ImportError as e:
        print(f"❌ Failed to import CLI module: {e}")
        return False

def test_vdw_radii():
    """Test that VDW radii data is available."""
    try:
        from vdw_surfgen.cli import VDW_RADII
        
        # Check for common elements
        common_elements = ['H', 'C', 'N', 'O']
        for element in common_elements:
            if element not in VDW_RADII:
                print(f"❌ Missing VDW radius for element: {element}")
                return False
                
        print(f"✅ VDW radii data available for {len(VDW_RADII)} elements")
        return True
    except ImportError as e:
        print(f"❌ Failed to access VDW_RADII: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running vdw-surfgen tests...")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_cli_module,
        test_vdw_radii,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
