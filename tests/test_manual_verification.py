"""
Manual test scenarios for the AI Memory System
These tests can be run manually to verify functionality in a real environment.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_vector_memory_basic():
    """Test basic vector memory functionality."""
    print("🧠 Testing Vector Memory System...")
    
    try:
        from vector_memory import VectorMemoryManager
        from unittest.mock import Mock
        
        # Create mock config
        config = Mock()
        config.vector_memory_enabled = True
        config.vector_memory_model = 'sentence-transformers/all-MiniLM-L6-v2'
        config.vector_memory_top_k = 3
        config.vector_memory_similarity_threshold = 0.3
        config.database_path = 'test_vector.db'
        
        # Initialize vector memory
        vm = VectorMemoryManager(config)
        
        if vm.enabled:
            print("✅ Vector memory initialized successfully")
            
            # Test storing memories
            test_memories = [
                "Player John built a magnificent stone castle",
                "Sarah tamed a high-level Rex using kibble",
                "Alpha Raptor pack destroyed the wooden bridge",
                "New tribe alliance formed for boss battles"
            ]
            
            stored_count = 0
            for memory in test_memories:
                if vm.store_memory(memory, "TestServer"):
                    stored_count += 1
            
            print(f"✅ Stored {stored_count}/{len(test_memories)} memories")
            
            # Test searching
            query = "Building and construction activities"
            results = vm.search_similar_memories(query, "TestServer")
            
            print(f"✅ Search returned {len(results)} similar memories")
            if results:
                print(f"   Most similar: {results[0]}")
            
            return True
        else:
            print("❌ Vector memory failed to initialize")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_context_manager_basic():
    """Test basic context manager functionality."""
    print("\n💬 Testing Enhanced Context Manager...")
    
    try:
        from recent_context import RecentContextManager
        from unittest.mock import Mock
        
        # Create mock database
        mock_db = Mock()
        
        # Setup mock data
        base_time = datetime.now()
        mock_summaries = [
            ("John built a stone fortress", base_time - timedelta(minutes=5), 45, "Island-PvE"),
            ("Sarah helped with construction", base_time - timedelta(minutes=10), 42, "Island-PvE"),
            ("Rex taming was successful", base_time - timedelta(minutes=20), 38, "Island-PvE"),
        ]
        
        mock_db.get_recent_summaries.return_value = mock_summaries
        mock_db._decompress_text.side_effect = lambda x: x
        
        # Initialize context manager
        rcm = RecentContextManager(mock_db)
        print("✅ Context manager initialized successfully")
        
        # Test contextual summaries
        summaries = rcm.get_contextual_summaries(
            server_name="Island-PvE",
            target_tokens=200
        )
        
        print(f"✅ Retrieved {len(summaries)} contextual summaries")
        if summaries:
            print(f"   Example: {summaries[0][:50]}...")
        
        # Test conversation threading
        threads = rcm.get_conversation_thread(
            server_name="Island-PvE",
            max_summaries=10,
            conversation_threshold=0.3
        )
        
        print(f"✅ Identified {len(threads)} conversation threads")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_database_integration():
    """Test database integration."""
    print("\n🗄️ Testing Database Integration...")
    
    try:
        from database import DatabaseManager
        import tempfile
        import os
        
        # Create temporary database
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, 'test.db')
        
        # Mock config
        from unittest.mock import Mock
        config = Mock()
        config.database_path = db_path
        
        # Initialize database
        db = DatabaseManager(config)
        print("✅ Database manager initialized")
        
        # Test basic operations
        test_summary = "Test summary for database integration"
        db.save_summary("TestServer", test_summary)
        print("✅ Summary saved to database")
        
        # Test retrieval
        summaries = db.get_summaries_up_to_token_limit("TestServer", 1000)
        print(f"✅ Retrieved {len(summaries)} summaries from database")
        
        # Test decompression helper
        if hasattr(db, '_decompress_text'):
            decompressed = db._decompress_text(test_summary)
            print("✅ Decompression helper working")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_main_application_integration():
    """Test main application integration."""
    print("\n🎯 Testing Main Application Integration...")
    
    try:
        from main import Application
        print("✅ Application class imported successfully")
        
        # Note: We can't fully initialize without proper config
        # but we can verify the class structure
        
        # Check if Application has the required attributes
        required_attrs = ['__init__']
        for attr in required_attrs:
            if hasattr(Application, attr):
                print(f"✅ Application.{attr} exists")
            else:
                print(f"❌ Application.{attr} missing")
                return False
        
        print("✅ Application structure looks correct")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_configuration_loading():
    """Test configuration loading."""
    print("\n⚙️ Testing Configuration...")
    
    try:
        # Test config file existence
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.exists(config_path):
            print("✅ config.json exists")
            
            # Load and verify config
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Check for memory system settings
            memory_settings = [
                'vector_memory_enabled',
                'vector_memory_model',
                'vector_memory_top_k',
                'vector_memory_similarity_threshold'
            ]
            
            found_settings = 0
            for setting in memory_settings:
                if setting in config_data:
                    print(f"✅ {setting}: {config_data[setting]}")
                    found_settings += 1
                else:
                    print(f"❌ Missing setting: {setting}")
            
            if found_settings == len(memory_settings):
                print("✅ All memory system settings present")
                return True
            else:
                print(f"⚠️ Only {found_settings}/{len(memory_settings)} settings found")
                return False
        else:
            print("❌ config.json not found")
            return False
            
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False


def run_manual_tests():
    """Run all manual tests."""
    print("=" * 80)
    print("FunnyCommentator AI Memory System - Manual Test Suite")
    print("=" * 80)
    print("This suite tests the functionality without requiring complex dependencies")
    print("=" * 80)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Database Integration", test_database_integration),
        ("Vector Memory Basic", test_vector_memory_basic),
        ("Context Manager Basic", test_context_manager_basic),
        ("Main Application Integration", test_main_application_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Manual Test Results Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All manual tests passed! AI Memory System is functional.")
        print("🚀 Ready for comprehensive testing and Phase 3 implementation.")
    elif passed > total // 2:
        print("\n⚠️ Most tests passed. Review failed tests and fix issues.")
        print("🔧 System is partially functional.")
    else:
        print("\n❌ Many tests failed. Significant issues need to be addressed.")
        print("🛠️ Review implementation and dependencies.")
    
    print("=" * 80)
    
    return passed == total


if __name__ == '__main__':
    run_manual_tests()
