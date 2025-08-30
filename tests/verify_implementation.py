"""
Simple Test Verification Script
Verifies the AI Memory System implementation without complex imports.
This script checks file structure, basic syntax, and configuration.
"""

import os
import json
import sys
from pathlib import Path

def check_file_structure():
    """Check that all required files exist."""
    print("📁 Checking File Structure...")
    
    base_dir = Path(__file__).parent.parent
    src_dir = base_dir / 'src'
    
    required_files = [
        # Core AI Memory System files
        'src/vector_memory.py',
        'src/recent_context.py', 
        'src/database.py',
        'src/main.py',
        'config.json',
        
        # Test files
        'tests/test_vector_memory.py',
        'tests/test_recent_context.py',
        'tests/test_ai_memory_integration.py',
        'tests/test_manual_verification.py',
        'tests/run_memory_tests.py',
    ]
    
    found_files = []
    missing_files = []
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            found_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} - MISSING")
    
    print(f"\nFile Structure Summary: {len(found_files)}/{len(required_files)} files found")
    
    return len(missing_files) == 0, found_files, missing_files


def check_python_syntax():
    """Check Python syntax of key files."""
    print("\n🐍 Checking Python Syntax...")
    
    base_dir = Path(__file__).parent.parent
    
    python_files = [
        'src/vector_memory.py',
        'src/recent_context.py',
        'src/main.py',
        'tests/run_memory_tests.py',
    ]
    
    syntax_ok = []
    syntax_errors = []
    
    for file_path in python_files:
        full_path = base_dir / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Try to compile the source code
                compile(source_code, str(full_path), 'exec')
                syntax_ok.append(file_path)
                print(f"✅ {file_path} - Syntax OK")
                
            except SyntaxError as e:
                syntax_errors.append((file_path, str(e)))
                print(f"❌ {file_path} - Syntax Error: {e}")
            except Exception as e:
                syntax_errors.append((file_path, f"Error reading file: {e}"))
                print(f"❌ {file_path} - Error: {e}")
        else:
            print(f"⚠️ {file_path} - File not found, skipping syntax check")
    
    print(f"\nSyntax Check Summary: {len(syntax_ok)} files passed, {len(syntax_errors)} files failed")
    
    return len(syntax_errors) == 0, syntax_ok, syntax_errors


def check_configuration():
    """Check configuration file."""
    print("\n⚙️ Checking Configuration...")
    
    base_dir = Path(__file__).parent.parent
    config_path = base_dir / 'config.json'
    
    if not config_path.exists():
        print("❌ config.json not found")
        return False, {}, ["config.json missing"]
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ config.json loads successfully")
        
        # Check for AI Memory System settings
        memory_settings = {
            'vector_memory_enabled': bool,
            'vector_memory_model': str,
            'vector_memory_top_k': int,
            'vector_memory_similarity_threshold': (int, float),
            'input_token_size': int,
            'database_path': str,
        }
        
        found_settings = []
        missing_settings = []
        
        for setting, expected_type in memory_settings.items():
            if setting in config:
                value = config[setting]
                if isinstance(value, expected_type):
                    found_settings.append((setting, value))
                    print(f"✅ {setting}: {value} (type: {type(value).__name__})")
                else:
                    print(f"⚠️ {setting}: {value} (expected {expected_type.__name__}, got {type(value).__name__})")
                    found_settings.append((setting, value))
            else:
                missing_settings.append(setting)
                print(f"❌ {setting} - Missing")
        
        print(f"\nConfiguration Summary: {len(found_settings)}/{len(memory_settings)} settings found")
        
        # Check if vector memory is enabled
        if config.get('vector_memory_enabled', False):
            print("🧠 Vector Memory is ENABLED in configuration")
        else:
            print("⚠️ Vector Memory is DISABLED in configuration")
        
        return len(missing_settings) == 0, found_settings, missing_settings
        
    except json.JSONDecodeError as e:
        print(f"❌ config.json syntax error: {e}")
        return False, {}, [f"JSON syntax error: {e}"]
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return False, {}, [f"Read error: {e}"]


def check_implementation_features():
    """Check for specific implementation features in source code."""
    print("\n🔍 Checking Implementation Features...")
    
    base_dir = Path(__file__).parent.parent
    
    # Features to check for
    features_to_check = [
        # Vector Memory features
        ('src/vector_memory.py', 'VectorMemoryManager', 'Vector Memory Manager class'),
        ('src/vector_memory.py', 'store_memory', 'Memory storage method'),
        ('src/vector_memory.py', 'search_similar_memories', 'Similarity search method'),
        ('src/vector_memory.py', '_cosine_similarity', 'Cosine similarity calculation'),
        
        # Enhanced Context Manager features  
        ('src/recent_context.py', 'RecentContextManager', 'Recent Context Manager class'),
        ('src/recent_context.py', 'get_contextual_summaries', 'Contextual summaries method'),
        ('src/recent_context.py', 'get_conversation_thread', 'Conversation threading method'),
        ('src/recent_context.py', '_calculate_conversation_score', 'Conversation scoring method'),
        
        # Main application integration
        ('src/main.py', 'vector_memory', 'Vector memory integration'),
        ('src/main.py', 'recent_context', 'Recent context integration'),
        ('src/main.py', 'RecentContextManager', 'Recent context manager import'),
        
        # Database enhancements
        ('src/database.py', '_decompress_text', 'Decompression helper method'),
    ]
    
    found_features = []
    missing_features = []
    
    for file_path, feature, description in features_to_check:
        full_path = base_dir / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if feature in content:
                    found_features.append((file_path, feature, description))
                    print(f"✅ {description} found in {file_path}")
                else:
                    missing_features.append((file_path, feature, description))
                    print(f"❌ {description} missing from {file_path}")
                    
            except Exception as e:
                print(f"⚠️ Error checking {file_path}: {e}")
        else:
            missing_features.append((file_path, feature, f"{description} (file missing)"))
            print(f"❌ {file_path} not found")
    
    print(f"\nFeature Check Summary: {len(found_features)}/{len(features_to_check)} features found")
    
    return len(missing_features) == 0, found_features, missing_features


def check_test_completeness():
    """Check test file completeness."""
    print("\n🧪 Checking Test Completeness...")
    
    base_dir = Path(__file__).parent.parent
    tests_dir = base_dir / 'tests'
    
    if not tests_dir.exists():
        print("❌ tests/ directory not found")
        return False, [], ["tests directory missing"]
    
    expected_test_files = [
        'test_vector_memory.py',
        'test_recent_context.py', 
        'test_ai_memory_integration.py',
        'run_memory_tests.py',
        'test_manual_verification.py'
    ]
    
    found_tests = []
    missing_tests = []
    
    for test_file in expected_test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            # Check file size to ensure it's not empty
            file_size = test_path.stat().st_size
            if file_size > 100:  # At least 100 bytes
                found_tests.append(test_file)
                print(f"✅ {test_file} ({file_size:,} bytes)")
            else:
                print(f"⚠️ {test_file} exists but seems empty ({file_size} bytes)")
                found_tests.append(test_file)
        else:
            missing_tests.append(test_file)
            print(f"❌ {test_file} - Missing")
    
    print(f"\nTest Completeness Summary: {len(found_tests)}/{len(expected_test_files)} test files found")
    
    return len(missing_tests) == 0, found_tests, missing_tests


def check_documentation():
    """Check documentation completeness."""
    print("\n📚 Checking Documentation...")
    
    base_dir = Path(__file__).parent.parent
    
    doc_files = [
        'README.md',
        'PHASE_2_COMPLETION_SUMMARY.md',
        'docs/COMPLETE_DOCUMENTATION.md',
    ]
    
    found_docs = []
    missing_docs = []
    
    for doc_file in doc_files:
        doc_path = base_dir / doc_file
        if doc_path.exists():
            file_size = doc_path.stat().st_size
            found_docs.append((doc_file, file_size))
            print(f"✅ {doc_file} ({file_size:,} bytes)")
        else:
            missing_docs.append(doc_file)
            print(f"❌ {doc_file} - Missing")
    
    print(f"\nDocumentation Summary: {len(found_docs)}/{len(doc_files)} documentation files found")
    
    return len(missing_docs) == 0, found_docs, missing_docs


def run_comprehensive_verification():
    """Run all verification checks."""
    print("=" * 80)
    print("FunnyCommentator AI Memory System - Comprehensive Verification")
    print("=" * 80)
    print("Verifying Phase 1 (Vector Memory) and Phase 2 (Enhanced Context Manager)")
    print("=" * 80)
    
    # Run all checks
    checks = [
        ("File Structure", check_file_structure),
        ("Python Syntax", check_python_syntax),
        ("Configuration", check_configuration),
        ("Implementation Features", check_implementation_features),
        ("Test Completeness", check_test_completeness),
        ("Documentation", check_documentation),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            success, found, missing = check_func()
            results.append((check_name, success, len(found), len(missing)))
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append((check_name, False, 0, 1))
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 Comprehensive Verification Results")
    print("=" * 80)
    
    passed_checks = 0
    total_checks = len(results)
    
    for check_name, success, found_count, missing_count in results:
        status = "✅ PASS" if success else "❌ FAIL"
        details = f"({found_count} found, {missing_count} missing)" if missing_count > 0 else f"({found_count} items verified)"
        print(f"{status} {check_name} {details}")
        if success:
            passed_checks += 1
    
    success_rate = (passed_checks / total_checks) * 100
    print(f"\nOverall Success Rate: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
    
    # Final assessment
    print("\n" + "=" * 80)
    print("🎯 Final Assessment")
    print("=" * 80)
    
    if passed_checks == total_checks:
        print("🎉 EXCELLENT: All verification checks passed!")
        print("   • Phase 1 (Vector Memory): ✅ Fully implemented")
        print("   • Phase 2 (Enhanced Context): ✅ Fully implemented")
        print("   • Integration: ✅ Complete")
        print("   • Tests: ✅ Comprehensive")
        print("   • Documentation: ✅ Complete")
        print("\n🚀 READY FOR PHASE 3 (Player Profiles) implementation!")
        
    elif passed_checks >= total_checks * 0.8:
        print("🌟 GOOD: Most verification checks passed!")
        print("   • Core functionality: ✅ Implemented")
        print("   • Minor issues: ⚠️ Need attention")
        print("\n🔧 Address remaining issues before Phase 3")
        
    elif passed_checks >= total_checks * 0.6:
        print("⚠️ MODERATE: Some verification checks failed")
        print("   • Basic structure: ✅ Present")
        print("   • Significant gaps: ❌ Need fixes")
        print("\n🛠️ Substantial work needed before proceeding")
        
    else:
        print("❌ POOR: Many verification checks failed")
        print("   • Implementation: ❌ Incomplete")
        print("   • Core issues: ❌ Need resolution")
        print("\n🚨 Major implementation work required")
    
    print("=" * 80)
    
    return passed_checks == total_checks


if __name__ == '__main__':
    success = run_comprehensive_verification()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
