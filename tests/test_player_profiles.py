#!/usr/bin/env python3
"""
Comprehensive test suite for Player Profiles Manager (Phase 3)
Tests all player behavior tracking, profile generation, and context integration
"""

import unittest
import tempfile
import os
import json
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys

# Add src directory to path for imports
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from player_profiles import PlayerProfileManager
from database import DatabaseManager
from config import Config


class TestPlayerProfileManager(unittest.TestCase):
    """Test cases for Player Profile Manager functionality."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create mock config and database manager
        self.mock_config = Mock(spec=Config)
        self.mock_db = Mock(spec=DatabaseManager)
        self.mock_db.db_path = self.temp_db.name
        self.mock_db.server_tables = {'TestServer': 'test_server_summaries'}
        
        # Create real database connection for testing
        with sqlite3.connect(self.temp_db.name) as conn:
            conn.execute('''
                CREATE TABLE test_server_summaries (
                    id INTEGER PRIMARY KEY,
                    summary TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        
        # Initialize player profile manager
        self.profile_manager = PlayerProfileManager(self.mock_db)
    
    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_extract_players_from_logs(self):
        """Test player name extraction from log entries."""
        test_logs = '''
        2025-01-15 14:30:22: Sletty tamed a level 150 Tek Parasaur!
        2025-01-15 14:31:05: Impinchi died to a Giga
        2025-01-15 14:32:15: Bob joined the server
        2025-01-15 14:33:45: Alice said "Hello everyone!"
        2025-01-15 14:34:20: Charlie placed a Foundation
        '''
        
        players = self.profile_manager.extract_players_from_logs(test_logs)
        
        expected_players = ['Sletty', 'Impinchi', 'Bob', 'Alice', 'Charlie']
        self.assertEqual(set(players), set(expected_players))
    
    def test_analyze_event_type_taming(self):
        """Test event type analysis for taming events."""
        log_text = "Sletty tamed a level 150 Tek Parasaur!"
        
        event = self.profile_manager.analyze_event_type(log_text)
        
        self.assertEqual(event['type'], 'taming')
        self.assertEqual(event['details']['dino_type'], 'Tek')
        self.assertEqual(event['details']['level'], 150)
        self.assertEqual(event['details']['dino_category'], 'tek')
        self.assertEqual(event['raw_log'], log_text)
    
    def test_analyze_event_type_death(self):
        """Test event type analysis for death events."""
        log_text = "Impinchi was killed by a Giga"
        
        event = self.profile_manager.analyze_event_type(log_text)
        
        self.assertEqual(event['type'], 'death')
        self.assertEqual(event['details']['killed_by'], 'Giga')
        self.assertEqual(event['raw_log'], log_text)
    
    def test_analyze_event_type_building(self):
        """Test event type analysis for building events."""
        log_text = "Charlie placed a Stone Foundation"
        
        event = self.profile_manager.analyze_event_type(log_text)
        
        self.assertEqual(event['type'], 'building')
        self.assertEqual(event['details']['structure_type'], 'Stone')
        self.assertEqual(event['raw_log'], log_text)
    
    def test_create_empty_profile(self):
        """Test empty profile creation structure."""
        profile = self.profile_manager._create_empty_profile()
        
        expected_keys = [
            'favorite_dinos', 'dino_categories', 'death_count', 'taming_count',
            'building_count', 'pvp_encounters', 'session_count', 'preferred_playtimes',
            'personality_traits', 'notable_events', 'server_preferences', 'relationships'
        ]
        
        for key in expected_keys:
            self.assertIn(key, profile)
        
        # Test personality traits structure
        personality_traits = profile['personality_traits']
        expected_traits = ['aggressive', 'builder', 'tamer', 'explorer', 'social']
        for trait in expected_traits:
            self.assertIn(trait, personality_traits)
            self.assertEqual(personality_traits[trait], 0.0)
    
    def test_process_event_for_profile_taming(self):
        """Test profile processing for taming events."""
        profile_data = self.profile_manager._create_empty_profile()
        event = {
            'type': 'taming',
            'details': {
                'dino_type': 'Parasaur',
                'dino_category': 'utility',
                'level': 150
            }
        }
        
        self.profile_manager._process_event_for_profile(profile_data, event)
        
        self.assertEqual(profile_data['taming_count'], 1)
        self.assertEqual(profile_data['favorite_dinos']['Parasaur'], 1)
        self.assertEqual(profile_data['dino_categories']['utility'], 1)
        self.assertGreater(profile_data['personality_traits']['tamer'], 0.0)
    
    def test_process_event_for_profile_death(self):
        """Test profile processing for death events."""
        profile_data = self.profile_manager._create_empty_profile()
        event = {
            'type': 'death',
            'details': {
                'killed_by': 'player'
            }
        }
        
        self.profile_manager._process_event_for_profile(profile_data, event)
        
        self.assertEqual(profile_data['death_count'], 1)
        self.assertEqual(profile_data['pvp_encounters'], 1)
        self.assertGreater(profile_data['personality_traits']['aggressive'], 0.0)
    
    def test_process_event_for_profile_building(self):
        """Test profile processing for building events."""
        profile_data = self.profile_manager._create_empty_profile()
        event = {
            'type': 'building',
            'details': {
                'structure_type': 'Foundation'
            }
        }
        
        self.profile_manager._process_event_for_profile(profile_data, event)
        
        self.assertEqual(profile_data['building_count'], 1)
        self.assertGreater(profile_data['personality_traits']['builder'], 0.0)
    
    def test_determine_personality_type(self):
        """Test personality type determination."""
        # Test tamer personality
        tamer_profile = self.profile_manager._create_empty_profile()
        tamer_profile['personality_traits']['tamer'] = 0.8
        personality = self.profile_manager._determine_personality_type(tamer_profile)
        self.assertEqual(personality, "dinosaur enthusiast")
        
        # Test builder personality
        builder_profile = self.profile_manager._create_empty_profile()
        builder_profile['personality_traits']['builder'] = 0.7
        personality = self.profile_manager._determine_personality_type(builder_profile)
        self.assertEqual(personality, "master architect")
        
        # Test casual player (low values)
        casual_profile = self.profile_manager._create_empty_profile()
        casual_profile['personality_traits']['tamer'] = 0.1
        personality = self.profile_manager._determine_personality_type(casual_profile)
        self.assertEqual(personality, "casual player")
    
    def test_get_favorite_activities(self):
        """Test favorite activities extraction."""
        profile_data = self.profile_manager._create_empty_profile()
        profile_data['favorite_dinos'] = {'Parasaur': 5, 'Rex': 2}
        profile_data['dino_categories'] = {'utility': 8, 'combat': 2}
        profile_data['building_count'] = 15
        profile_data['pvp_encounters'] = 10
        
        activities = self.profile_manager._get_favorite_activities(profile_data)
        
        self.assertIn('taming Parasaurs', activities)
        self.assertIn('utility dinosaurs', activities)
        self.assertIn('building', activities)
    
    def test_get_notable_stats(self):
        """Test notable statistics extraction."""
        profile_data = self.profile_manager._create_empty_profile()
        profile_data['death_count'] = 25
        profile_data['taming_count'] = 20
        profile_data['building_count'] = 60
        
        stats = self.profile_manager._get_notable_stats(profile_data)
        
        self.assertIn('25 deaths', stats)
        self.assertIn('20 tames', stats)
    
    def test_update_player_profile(self):
        """Test complete player profile update process."""
        player_name = "TestPlayer"
        server_name = "TestServer"
        events = [
            {
                'type': 'taming',
                'details': {'dino_type': 'Rex', 'dino_category': 'combat', 'level': 150}
            },
            {
                'type': 'death',
                'details': {'killed_by': 'Giga'}
            },
            {
                'type': 'building',
                'details': {'structure_type': 'Foundation'}
            }
        ]
        
        # Call update method
        self.profile_manager.update_player_profile(player_name, server_name, events)
        
        # Verify database entries were created
        with sqlite3.connect(self.temp_db.name) as conn:
            # Check player profile exists
            cursor = conn.execute(
                'SELECT player_name, profile_data FROM player_profiles WHERE player_name = ?',
                (player_name,)
            )
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            
            # Check profile data
            profile_data = json.loads(result[1])
            self.assertEqual(profile_data['taming_count'], 1)
            self.assertEqual(profile_data['death_count'], 1)
            self.assertEqual(profile_data['building_count'], 1)
            self.assertEqual(profile_data['favorite_dinos']['Rex'], 1)
            
            # Check events were stored
            cursor = conn.execute(
                'SELECT COUNT(*) FROM player_events WHERE player_name = ?',
                (player_name,)
            )
            event_count = cursor.fetchone()[0]
            self.assertEqual(event_count, 3)
    
    def test_get_player_context_known_player(self):
        """Test context generation for known player."""
        # First create a player profile
        player_name = "TestPlayer"
        server_name = "TestServer"
        events = [
            {
                'type': 'taming',
                'details': {'dino_type': 'Parasaur', 'dino_category': 'utility', 'level': 150}
            }
        ]
        
        self.profile_manager.update_player_profile(player_name, server_name, events)
        
        # Get context
        context = self.profile_manager.get_player_context(player_name, server_name)
        
        self.assertTrue(context['is_known'])
        self.assertEqual(context['player_name'], player_name)
        self.assertIn('context_summary', context)
        self.assertIn('personality_type', context)
        self.assertIn('favorite_activities', context)
        self.assertIn('notable_stats', context)
    
    def test_get_player_context_unknown_player(self):
        """Test context generation for unknown player."""
        context = self.profile_manager.get_player_context("UnknownPlayer")
        
        self.assertFalse(context['is_known'])
        self.assertEqual(context['player_name'], "UnknownPlayer")
        self.assertIn("new or occasional player", context['context_summary'])
    
    def test_process_logs_for_profiles(self):
        """Test complete log processing workflow."""
        test_logs = '''
        2025-01-15 14:30:22: Sletty tamed a level 150 Tek Parasaur!
        2025-01-15 14:31:05: Impinchi died to a Giga
        2025-01-15 14:32:15: Bob placed a Foundation
        '''
        server_name = "TestServer"
        
        # Process logs
        self.profile_manager.process_logs_for_profiles(test_logs, server_name)
        
        # Verify players were processed
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM player_profiles')
            player_count = cursor.fetchone()[0]
            self.assertGreater(player_count, 0)
            
            cursor = conn.execute('SELECT COUNT(*) FROM player_events')
            event_count = cursor.fetchone()[0]
            self.assertGreater(event_count, 0)
    
    def test_get_contextual_player_summaries(self):
        """Test contextual player summaries generation."""
        # Create some test players
        players = ["TestPlayer1", "TestPlayer2"]
        
        for i, player in enumerate(players):
            events = [
                {
                    'type': 'taming',
                    'details': {'dino_type': f'Dino{i}', 'dino_category': 'utility'}
                }
            ]
            self.profile_manager.update_player_profile(player, "TestServer", events)
        
        # Get summaries
        summaries = self.profile_manager.get_contextual_player_summaries(players, max_length=200)
        
        self.assertIsInstance(summaries, str)
        self.assertGreater(len(summaries), 0)
        for player in players:
            self.assertIn(player, summaries)
    
    def test_get_server_player_summary(self):
        """Test server player summary generation."""
        # Create test players
        players = ["Player1", "Player2", "Player3"]
        server_name = "TestServer"
        
        for player in players:
            events = [
                {
                    'type': 'taming',
                    'details': {'dino_type': 'Rex', 'dino_category': 'combat'}
                }
            ]
            self.profile_manager.update_player_profile(player, server_name, events)
        
        # Get server summary
        summary = self.profile_manager.get_server_player_summary(server_name, limit=5)
        
        self.assertEqual(summary['server_name'], server_name)
        self.assertEqual(summary['total_tracked'], 3)
        self.assertEqual(len(summary['active_players']), 3)
        
        # Check player data structure
        for player_data in summary['active_players']:
            self.assertIn('name', player_data)
            self.assertIn('event_count', player_data)
            self.assertIn('personality_type', player_data)
            self.assertIn('context', player_data)
    
    def test_categorize_dino(self):
        """Test dinosaur categorization system."""
        test_cases = [
            ('Ankylo', 'utility'),
            ('Rex', 'combat'),
            ('Argentavis', 'transport'),
            ('Tek Parasaur', 'tek'),
            ('Wyvern', 'rare'),
            ('Unknown Dino', 'other')
        ]
        
        for dino_name, expected_category in test_cases:
            category = self.profile_manager._categorize_dino(dino_name)
            self.assertEqual(category, expected_category, 
                           f"Expected {dino_name} to be categorized as {expected_category}, got {category}")
    
    def test_cache_functionality(self):
        """Test profile caching mechanism."""
        player_name = "CacheTestPlayer"
        server_name = "TestServer"
        events = [
            {
                'type': 'taming',
                'details': {'dino_type': 'Rex', 'dino_category': 'combat'}
            }
        ]
        
        # Update profile (should cache it)
        self.profile_manager.update_player_profile(player_name, server_name, events)
        
        # Check cache
        with self.profile_manager.cache_lock:
            self.assertIn(player_name, self.profile_manager.profiles_cache)
            cached_data = self.profile_manager.profiles_cache[player_name]
            self.assertIn('data', cached_data)
            self.assertIn('cached_at', cached_data)
    
    def test_personality_trait_capping(self):
        """Test that personality traits are capped at 1.0."""
        profile_data = self.profile_manager._create_empty_profile()
        
        # Simulate many taming events
        taming_event = {
            'type': 'taming',
            'details': {'dino_type': 'Rex', 'dino_category': 'combat'}
        }
        
        # Process 20 taming events (should exceed 1.0 without capping)
        for _ in range(20):
            self.profile_manager._process_event_for_profile(profile_data, taming_event)
        
        # Check that tamer trait is capped at 1.0
        self.assertEqual(profile_data['personality_traits']['tamer'], 1.0)
    
    def test_database_table_creation(self):
        """Test that all required database tables are created."""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'player_profiles',
                'player_events',
                'player_relationships'
            ]
            
            for table in required_tables:
                self.assertIn(table, tables, f"Required table {table} not found")


class TestPlayerProfileIntegration(unittest.TestCase):
    """Integration tests for Player Profile Manager with other components."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create mock components
        self.mock_config = Mock(spec=Config)
        self.mock_db = Mock(spec=DatabaseManager)
        self.mock_db.db_path = self.temp_db.name
        
        self.profile_manager = PlayerProfileManager(self.mock_db)
    
    def tearDown(self):
        """Clean up integration test environment."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_realistic_log_processing(self):
        """Test processing of realistic ARK server logs."""
        realistic_logs = '''
        2025-01-15 14:30:22: Sletty tamed a Level 150 Tek Parasaur (Tek Parasaur)!
        2025-01-15 14:31:05: Impinchi was killed by a Giganotosaurus - Level 145!
        2025-01-15 14:32:15: Bob placed Stone Foundation
        2025-01-15 14:33:45: Alice said: "Anyone want to do boss fights?"
        2025-01-15 14:34:20: Charlie was killed by Impinchi!
        2025-01-15 14:35:10: Sletty tamed a Level 200 Argentavis (Argentavis)!
        2025-01-15 14:36:00: Bob destroyed Charlie's Wooden Wall
        '''
        
        server_name = "RealisticTestServer"
        
        # Process the logs
        self.profile_manager.process_logs_for_profiles(realistic_logs, server_name)
        
        # Verify Sletty's profile (should be a tamer)
        sletty_context = self.profile_manager.get_player_context("Sletty", server_name)
        if sletty_context['is_known']:
            self.assertIn("enthusiast", sletty_context['personality_type'])
        
        # Verify players were extracted correctly
        players = self.profile_manager.extract_players_from_logs(realistic_logs)
        expected_players = ['Sletty', 'Impinchi', 'Bob', 'Alice', 'Charlie']
        for player in expected_players:
            self.assertIn(player, players)
    
    def test_performance_with_large_logs(self):
        """Test performance with large log files."""
        import time
        
        # Generate large log content
        large_logs = []
        for i in range(1000):
            large_logs.append(f"Player{i % 10} tamed a Level {100 + i % 50} Rex!")
        
        large_log_content = "\n".join(large_logs)
        
        # Time the processing
        start_time = time.time()
        self.profile_manager.process_logs_for_profiles(large_log_content, "PerformanceTest")
        end_time = time.time()
        
        processing_time = end_time - start_time
        self.assertLess(processing_time, 5.0, "Processing took too long (> 5 seconds)")
        
        # Verify profiles were created
        summary = self.profile_manager.get_server_player_summary("PerformanceTest", limit=20)
        self.assertGreater(summary['total_tracked'], 0)


def run_tests():
    """Run all player profile tests."""
    print("=" * 80)
    print("FunnyCommentator Player Profiles - Comprehensive Test Suite")
    print("=" * 80)
    print("Testing Phase 3: Player Profiles Implementation")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.makeSuite(TestPlayerProfileManager))
    test_suite.addTest(unittest.makeSuite(TestPlayerProfileIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 Test Results Summary")
    print("=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print(f"\n🔥 ERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback.split('\n')[-2]}")
    
    if not result.failures and not result.errors:
        print("\n🎉 All tests passed! Player Profiles system is working correctly.")
        print("✅ Phase 3 implementation is ready for production use!")
    else:
        print(f"\n⚠️  Some tests failed. Please review and fix the issues.")
    
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
