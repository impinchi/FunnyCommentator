#!/usr/bin/env python3
"""
Simple verification test for Phase 3 Player Profiles
Tests core functionality without complex imports
"""

import tempfile
import os
import json
import sqlite3
import sys

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

def test_player_profiles():
    """Simple test of player profiles functionality."""
    print("🧪 Testing Phase 3: Player Profiles Implementation")
    print("=" * 60)
    
    try:
        # Import with direct path manipulation
        from player_profiles import PlayerProfileManager
        print("✅ Successfully imported PlayerProfileManager")
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # Mock database manager
        class MockDB:
            def __init__(self, db_path):
                self.db_path = db_path
                self.server_tables = {'TestServer': 'test_summaries'}
        
        mock_db = MockDB(temp_db.name)
        
        # Initialize player profiles manager
        profile_manager = PlayerProfileManager(mock_db)
        print("✅ Successfully created PlayerProfileManager instance")
        
        # Test player extraction
        test_logs = '''
        2025-01-15 14:30:22: Sletty tamed a level 150 Tek Parasaur!
        2025-01-15 14:31:05: Impinchi died to a Giga
        2025-01-15 14:32:15: Bob placed a Foundation
        '''
        
        players = profile_manager.extract_players_from_logs(test_logs)
        expected_players = ['Sletty', 'Impinchi', 'Bob']
        
        if set(players) == set(expected_players):
            print("✅ Player extraction working correctly")
        else:
            print(f"❌ Player extraction failed. Got {players}, expected {expected_players}")
            return False
        
        # Test event analysis
        event = profile_manager.analyze_event_type("Sletty tamed a level 150 Tek Parasaur!")
        if event['type'] == 'taming' and 'dino_type' in event['details']:
            print("✅ Event analysis working correctly")
        else:
            print(f"❌ Event analysis failed. Got {event}")
            return False
        
        # Test profile creation
        profile = profile_manager._create_empty_profile()
        required_keys = ['favorite_dinos', 'personality_traits', 'taming_count', 'death_count']
        
        if all(key in profile for key in required_keys):
            print("✅ Profile structure created correctly")
        else:
            print(f"❌ Profile structure missing keys. Got {list(profile.keys())}")
            return False
        
        # Test database table creation
        with sqlite3.connect(temp_db.name) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['player_profiles', 'player_events', 'player_relationships']
            if all(table in tables for table in required_tables):
                print("✅ Database tables created correctly")
            else:
                print(f"❌ Missing database tables. Got {tables}")
                return False
        
        # Test log processing
        profile_manager.process_logs_for_profiles(test_logs, 'TestServer')
        print("✅ Log processing completed without errors")
        
        # Test player context
        context = profile_manager.get_player_context('Sletty', 'TestServer')
        if 'player_name' in context and 'is_known' in context:
            print("✅ Player context generation working")
        else:
            print(f"❌ Player context generation failed. Got {context}")
            return False
        
        # Test personality determination
        test_profile = profile_manager._create_empty_profile()
        test_profile['personality_traits']['tamer'] = 0.8
        personality = profile_manager._determine_personality_type(test_profile)
        
        if 'enthusiast' in personality:
            print("✅ Personality determination working")
        else:
            print(f"❌ Personality determination failed. Got {personality}")
            return False
        
        # Clean up
        try:
            os.unlink(temp_db.name)
        except PermissionError:
            # Windows file lock issue - not critical for test success
            pass
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Phase 3 Player Profiles implementation is working correctly!")
        print("🚀 Ready for integration with main application!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_check():
    """Test integration points with main application."""
    print("\n🔗 Testing Integration Points")
    print("=" * 60)
    
    try:
        # Test main.py can import player profiles
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        # Check if main.py has the import
        main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'main.py')
        with open(main_path, 'r') as f:
            main_content = f.read()
            
        if 'from src.player_profiles import PlayerProfileManager' in main_content:
            print("✅ main.py has correct PlayerProfileManager import")
        else:
            print("❌ main.py missing PlayerProfileManager import")
            return False
        
        if 'self.player_profiles = PlayerProfileManager(self.db)' in main_content:
            print("✅ main.py initializes PlayerProfileManager")
        else:
            print("❌ main.py doesn't initialize PlayerProfileManager")
            return False
        
        if 'process_logs_for_profiles' in main_content:
            print("✅ main.py calls player profile processing")
        else:
            print("❌ main.py doesn't call player profile processing")
            return False
        
        if 'get_contextual_player_summaries' in main_content:
            print("✅ main.py uses player context in AI generation")
        else:
            print("❌ main.py doesn't use player context")
            return False
        
        print("=" * 60)
        print("🎉 INTEGRATION CHECKS PASSED!")
        print("✅ Player Profiles are properly integrated with main application!")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration check failed: {e}")
        return False

if __name__ == "__main__":
    print("Phase 3: Player Profiles - Quick Verification Test")
    print("=" * 60)
    
    success1 = test_player_profiles()
    success2 = test_integration_check()
    
    if success1 and success2:
        print("\n🎯 PHASE 3 VERIFICATION COMPLETE!")
        print("✅ Player Profiles system is fully implemented and integrated!")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
        exit(1)
