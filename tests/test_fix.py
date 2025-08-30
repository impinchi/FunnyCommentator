#!/usr/bin/env python3
"""
Quick test to verify the player profiles fix for list/string input
"""

import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

def test_player_profiles_fix():
    """Test that player profiles can handle both string and list inputs."""
    print("🧪 Testing Player Profiles List/String Input Fix")
    print("=" * 50)
    
    try:
        from player_profiles import PlayerProfileManager
        
        # Mock database manager
        class MockDB:
            def __init__(self):
                self.db_path = ':memory:'
                self.server_tables = {'TestServer': 'test_summaries'}
        
        mock_db = MockDB()
        profile_manager = PlayerProfileManager(mock_db)
        
        print("✅ PlayerProfileManager created successfully")
        
        # Test data
        test_logs_string = '''
        2025-08-30 09:36:08: impinchi joined this ARK!
        2025-08-30 09:36:08: Tribe Tamed a Baby Tek Parasaur - Lvl 40!
        2025-08-30 09:36:08: Baby Tek Parasaur was killed by vim!
        '''
        
        test_logs_list = [
            '2025-08-30 09:36:08: impinchi joined this ARK!',
            '2025-08-30 09:36:08: Tribe Tamed a Baby Tek Parasaur - Lvl 40!',
            '2025-08-30 09:36:08: Baby Tek Parasaur was killed by vim!'
        ]
        
        # Test string input
        print("🧪 Testing string input...")
        players_from_string = profile_manager.extract_players_from_logs(test_logs_string)
        print(f"✅ String input worked: {players_from_string}")
        
        # Test list input  
        print("🧪 Testing list input...")
        players_from_list = profile_manager.extract_players_from_logs(test_logs_list)
        print(f"✅ List input worked: {players_from_list}")
        
        # Both should extract the same players
        if set(players_from_string) == set(players_from_list):
            print("✅ Both inputs produce the same results")
        else:
            print(f"❌ Results differ: string={players_from_string}, list={players_from_list}")
            return False
        
        # Test process_logs_for_profiles with list input
        print("🧪 Testing process_logs_for_profiles with list input...")
        profile_manager.process_logs_for_profiles(test_logs_list, 'TestServer')
        print("✅ process_logs_for_profiles works with list input")
        
        # Test process_logs_for_profiles with string input
        print("🧪 Testing process_logs_for_profiles with string input...")
        profile_manager.process_logs_for_profiles(test_logs_string, 'TestServer')
        print("✅ process_logs_for_profiles works with string input")
        
        print("=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Player Profiles can now handle both string and list inputs!")
        print("🚀 The TypeError should be fixed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_player_profiles_fix()
    exit(0 if success else 1)
