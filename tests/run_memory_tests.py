"""
Test runner script for the AI Memory System comprehensive test suite.
This script runs all tests for Phase 1 (Vector Memory) and Phase 2 (Enhanced Context Manager).
"""

import unittest
import sys
import os
import tempfile
import shutil
from io import StringIO

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_all_tests():
    """Run all AI Memory System tests and generate a comprehensive report."""
    
    print("=" * 80)
    print("FunnyCommentator AI Memory System - Comprehensive Test Suite")
    print("=" * 80)
    print("Testing Phase 1: Vector Memory System")
    print("Testing Phase 2: Enhanced Context Manager")
    print("Testing Integration: Vector + Context Memory Coordination")
    print("=" * 80)
    
    # Discover and run all tests
    test_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()
    
    # Load test files that we can import
    suite = unittest.TestSuite()
    
    print("\n🔍 Discovering test modules...")
    
    # Try to load individual test modules
    test_modules = [
        'test_vector_memory',
        'test_recent_context', 
        'test_ai_memory_integration'
    ]
    
    imported_modules = []
    failed_imports = []
    
    for module_name in test_modules:
        try:
            # Import the test module
            test_module = __import__(module_name)
            imported_modules.append((module_name, test_module))
            print(f"✅ Successfully loaded {module_name}")
            
            # Add tests from this module
            module_tests = loader.loadTestsFromModule(test_module)
            suite.addTests(module_tests)
            
        except ImportError as e:
            failed_imports.append((module_name, str(e)))
            print(f"❌ Failed to load {module_name}: {e}")
        except Exception as e:
            failed_imports.append((module_name, f"Unexpected error: {e}"))
            print(f"❌ Error loading {module_name}: {e}")
    
    print(f"\n📊 Test Discovery Summary:")
    print(f"   Successfully loaded: {len(imported_modules)} modules")
    print(f"   Failed to load: {len(failed_imports)} modules")
    
    if failed_imports:
        print(f"\n⚠️  Import Failures:")
        for module, error in failed_imports:
            print(f"   {module}: {error}")
    
    # Run the tests
    print(f"\n🚀 Running tests from {len(imported_modules)} available modules...")
    print("=" * 80)
    
    # Capture test output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        descriptions=True,
        failfast=False
    )
    
    # Run tests and capture results
    result = runner.run(suite)
    
    # Get the test output
    test_output = stream.getvalue()
    
    # Print results
    print(test_output)
    
    print("=" * 80)
    print("📋 Test Results Summary")
    print("=" * 80)
    
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(getattr(result, 'skipped', []))}")
    
    # Calculate success rate
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Print detailed failure information
    if result.failures:
        print(f"\n❌ Test Failures ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See full traceback above'}")
    
    if result.errors:
        print(f"\n💥 Test Errors ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'See full traceback above'}")
    
    # Test categories status
    print(f"\n📈 Test Categories Status:")
    print(f"   Vector Memory Tests: {'✅ Available' if any('vector' in m[0] for m in imported_modules) else '❌ Not Available'}")
    print(f"   Context Manager Tests: {'✅ Available' if any('context' in m[0] for m in imported_modules) else '❌ Not Available'}")
    print(f"   Integration Tests: {'✅ Available' if any('integration' in m[0] for m in imported_modules) else '❌ Not Available'}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if failed_imports:
        print("   • Fix import issues by ensuring all source modules are properly implemented")
        print("   • Check that src/ directory contains all required files")
        print("   • Verify Python path configuration")
    
    if result.failures or result.errors:
        print("   • Review failed tests and fix implementation issues")
        print("   • Check mock configurations and test data setup")
        print("   • Ensure all dependencies are properly installed")
    
    if result.testsRun == 0:
        print("   • No tests were executed - check test discovery and imports")
    elif len(result.failures) + len(result.errors) == 0:
        print("   • All tests passed! AI Memory System is working correctly")
        print("   • Consider adding more edge case tests")
        print("   • Ready to proceed with Phase 3 implementation")
    
    print("=" * 80)
    
    return result.testsRun > 0 and len(result.failures) == 0 and len(result.errors) == 0


def run_simple_import_test():
    """Run a simple test to verify basic imports work."""
    print("\n🔧 Running Simple Import Test...")
    print("-" * 40)
    
    modules_to_test = [
        ('config', 'Config'),
        ('database', 'DatabaseManager'),
        ('vector_memory', 'VectorMemoryManager'),
        ('recent_context', 'RecentContextManager'),
        ('main', 'Application')
    ]
    
    success_count = 0
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name} - Import successful")
                success_count += 1
            else:
                print(f"❌ {module_name}.{class_name} - Class not found")
        except ImportError as e:
            print(f"❌ {module_name}.{class_name} - Import failed: {e}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name} - Error: {e}")
    
    print(f"\nImport Test Results: {success_count}/{len(modules_to_test)} successful")
    
    if success_count == len(modules_to_test):
        print("🎉 All core modules import successfully!")
        return True
    else:
        print("⚠️  Some modules failed to import. Check implementation.")
        return False


def main():
    """Main test runner function."""
    print("FunnyCommentator AI Memory System Test Suite")
    print("Testing Phase 1 (Vector Memory) and Phase 2 (Enhanced Context Manager)")
    
    # First, test basic imports
    imports_ok = run_simple_import_test()
    
    # Then run full test suite
    tests_ok = run_all_tests()
    
    # Final status
    print("\n" + "=" * 80)
    print("🏁 Final Status")
    print("=" * 80)
    
    if imports_ok and tests_ok:
        print("🎉 SUCCESS: AI Memory System is fully functional!")
        print("   • Phase 1 (Vector Memory): ✅ Working")
        print("   • Phase 2 (Enhanced Context): ✅ Working") 
        print("   • Integration: ✅ Working")
        print("\n🚀 Ready to proceed with Phase 3 (Player Profiles)!")
    elif imports_ok and not tests_ok:
        print("⚠️  PARTIAL SUCCESS: Modules import but some tests failed")
        print("   • Basic functionality: ✅ Available")
        print("   • Some test cases: ❌ Failed")
        print("\n🔧 Review test failures and fix issues before proceeding")
    elif not imports_ok:
        print("❌ FAILED: Core modules have import issues")
        print("   • Implementation: ❌ Incomplete")
        print("   • Dependencies: ❌ Missing")
        print("\n🛠️  Fix implementation issues before testing")
    
    print("=" * 80)


if __name__ == '__main__':
    main()
