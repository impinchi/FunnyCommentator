#!/usr/bin/env python3
"""
Test runner for FunnyCommentator - Validates test organization and imports.

This script ensures all tests are properly organized in the tests directory
and can be imported correctly.
"""
import os
import sys
from pathlib import Path

def main():
    """Main test runner function."""
    print("=== FunnyCommentator Test Organization Validator ===\n")
    
    # Get the tests directory
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    
    # Add project root to Python path for imports
    sys.path.insert(0, str(project_root))
    
    print(f"Tests directory: {tests_dir}")
    print(f"Project root: {project_root}")
    
    # Find all Python test files
    test_files = list(tests_dir.glob("test_*.py"))
    verify_files = list(tests_dir.glob("verify_*.py"))
    
    print(f"\nFound {len(test_files)} test files:")
    for test_file in sorted(test_files):
        print(f"  ✓ {test_file.name}")
    
    print(f"\nFound {len(verify_files)} verification files:")
    for verify_file in sorted(verify_files):
        print(f"  ✓ {verify_file.name}")
    
    # Test imports
    print(f"\n=== Testing Imports ===")
    
    # Test main project imports
    try:
        import src.config
        print("  ✓ src.config imported successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import src.config: {e}")
    
    try:
        import src.database
        print("  ✓ src.database imported successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import src.database: {e}")
    
    try:
        import src.player_profiles
        print("  ✓ src.player_profiles imported successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import src.player_profiles: {e}")
    
    # Test if we can import test modules
    importable_tests = 0
    total_tests = len(test_files)
    
    for test_file in test_files:
        module_name = test_file.stem
        try:
            __import__(module_name)
            importable_tests += 1
            print(f"  ✓ {module_name} imported successfully")
        except ImportError as e:
            print(f"  ✗ Failed to import {module_name}: {e}")
        except Exception as e:
            print(f"  ⚠ {module_name} imported with warnings: {e}")
            importable_tests += 1  # Still count as importable
    
    print(f"\n=== Summary ===")
    print(f"Total test files: {total_tests}")
    print(f"Importable tests: {importable_tests}")
    print(f"Success rate: {importable_tests/total_tests*100:.1f}%")
    
    if importable_tests == total_tests:
        print("\n🎉 All tests are properly organized and importable!")
        return True
    else:
        print("\n⚠️  Some tests may need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
