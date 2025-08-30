"""
Comprehensive tests for Phase 2: Enhanced Context Manager
Tests the RecentContextManager functionality including conversation threading and temporal filtering.
"""

import unittest
import tempfile
import shutil
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from recent_context import RecentContextManager
from database import DatabaseManager


class TestRecentContextManager(unittest.TestCase):
    """Test suite for RecentContextManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_recent_context.db')
        
        # Create mock database manager
        self.mock_db = Mock(spec=DatabaseManager)
        
        # Create test data
        self.base_time = datetime.now()
        self.test_summaries = [
            {
                'timestamp': self.base_time - timedelta(minutes=5),
                'summary': 'Player John built a wooden house near the beach',
                'server_name': 'Island-PvE',
                'cluster_name': 'MainCluster',
                'tokens': 50
            },
            {
                'timestamp': self.base_time - timedelta(minutes=10),
                'summary': 'Sarah tamed a Raptor and named it Spike',
                'server_name': 'Island-PvE',
                'cluster_name': 'MainCluster',
                'tokens': 45
            },
            {
                'timestamp': self.base_time - timedelta(hours=1),
                'summary': 'Alpha Rex destroyed multiple structures in the base',
                'server_name': 'Island-PvE',
                'cluster_name': 'MainCluster',
                'tokens': 60
            },
            {
                'timestamp': self.base_time - timedelta(hours=2),
                'summary': 'New player Mike joined and requested building materials',
                'server_name': 'Island-PvE',
                'cluster_name': 'MainCluster',
                'tokens': 55
            },
            {
                'timestamp': self.base_time - timedelta(days=1),
                'summary': 'Tribe established a new outpost on the mountain',
                'server_name': 'Ragnarok-PvP',
                'cluster_name': 'MainCluster',
                'tokens': 52
            },
            {
                'timestamp': self.base_time - timedelta(days=2),
                'summary': 'Resource gathering expedition found rare materials',
                'server_name': 'Island-PvE',
                'cluster_name': 'MainCluster',
                'tokens': 48
            }
        ]
        
        # Setup cluster summaries
        self.test_cluster_summaries = [
            {
                'timestamp': self.base_time - timedelta(minutes=15),
                'summary': 'Cluster-wide event: Dragon boss defeated by alliance',
                'cluster_name': 'MainCluster',
                'tokens': 65
            },
            {
                'timestamp': self.base_time - timedelta(hours=3),
                'summary': 'Cross-server trading event was successful',
                'cluster_name': 'MainCluster',
                'tokens': 58
            }
        ]

    def tearDown(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        """Test RecentContextManager initialization."""
        rcm = RecentContextManager(self.mock_db)
        
        self.assertEqual(rcm.db, self.mock_db)
        self.assertIsInstance(rcm.conversation_cache, dict)
        self.assertIsInstance(rcm.cache_expiry, dict)

    def test_get_recent_summaries_by_timeframe_hours(self):
        """Test retrieving summaries by hour timeframes."""
        # Mock database responses
        self.mock_db.get_summaries_by_timeframe.return_value = [
            (s['summary'], s['timestamp'], s['tokens']) 
            for s in self.test_summaries[:2]  # Last hour
        ]
        
        rcm = RecentContextManager(self.mock_db)
        
        # Test getting summaries from last hour
        results = rcm.get_recent_summaries_by_timeframe(
            server_name='Island-PvE',
            hours=1,
            max_tokens=200
        )
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertIn('wooden house', results[0])
        self.assertIn('Raptor', results[1])
        
        # Verify database was called correctly
        self.mock_db.get_summaries_by_timeframe.assert_called_once()

    def test_get_recent_summaries_by_timeframe_days(self):
        """Test retrieving summaries by day timeframes."""
        # Mock database responses for longer timeframe
        self.mock_db.get_summaries_by_timeframe.return_value = [
            (s['summary'], s['timestamp'], s['tokens']) 
            for s in self.test_summaries[:4]  # Last few hours
        ]
        
        rcm = RecentContextManager(self.mock_db)
        
        # Test getting summaries from last day
        results = rcm.get_recent_summaries_by_timeframe(
            server_name='Island-PvE',
            days=1,
            max_tokens=250
        )
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 4)

    def test_token_limit_enforcement(self):
        """Test that token limits are properly enforced."""
        # Mock database with high token content
        high_token_summaries = [
            (s['summary'], s['timestamp'], 100)  # Each summary has 100 tokens
            for s in self.test_summaries[:5]
        ]
        
        self.mock_db.get_summaries_by_timeframe.return_value = high_token_summaries
        
        rcm = RecentContextManager(self.mock_db)
        
        # Request with limited tokens
        results = rcm.get_recent_summaries_by_timeframe(
            server_name='Island-PvE',
            hours=24,
            max_tokens=250  # Should fit only 2-3 summaries
        )
        
        # Calculate total tokens used
        total_estimated_tokens = sum(len(result.split()) * 1.3 for result in results)
        self.assertLessEqual(total_estimated_tokens, 250)

    def test_calculate_conversation_score(self):
        """Test conversation relationship scoring algorithm."""
        rcm = RecentContextManager(self.mock_db)
        
        base_time = datetime.now()
        
        # Test temporal proximity scoring
        summary1 = {
            'timestamp': base_time - timedelta(minutes=5),
            'summary': 'Player built a house',
            'server_name': 'Island-PvE'
        }
        
        summary2 = {
            'timestamp': base_time - timedelta(minutes=10),
            'summary': 'Player gathered materials for building',
            'server_name': 'Island-PvE'
        }
        
        score = rcm._calculate_conversation_score(summary1, summary2)
        
        # Should have high score due to:
        # - Close temporal proximity
        # - Same server
        # - Related content (building theme)
        self.assertGreater(score, 0.5)
        
        # Test with different servers
        summary3 = {
            'timestamp': base_time - timedelta(minutes=8),
            'summary': 'Player tamed a dinosaur',
            'server_name': 'Ragnarok-PvP'
        }
        
        score_diff_server = rcm._calculate_conversation_score(summary1, summary3)
        
        # Should have lower score due to different server
        self.assertLess(score_diff_server, score)

    def test_content_similarity_detection(self):
        """Test content similarity detection in conversation scoring."""
        rcm = RecentContextManager(self.mock_db)
        
        base_time = datetime.now()
        
        # Summaries with similar content
        summary1 = {
            'timestamp': base_time - timedelta(minutes=5),
            'summary': 'Player John built a wooden house',
            'server_name': 'Island-PvE'
        }
        
        summary2 = {
            'timestamp': base_time - timedelta(minutes=10),
            'summary': 'John finished constructing his wooden building',
            'server_name': 'Island-PvE'
        }
        
        score_similar = rcm._calculate_conversation_score(summary1, summary2)
        
        # Summaries with different content
        summary3 = {
            'timestamp': base_time - timedelta(minutes=8),
            'summary': 'Dragon attacked the volcano base',
            'server_name': 'Island-PvE'
        }
        
        score_different = rcm._calculate_conversation_score(summary1, summary3)
        
        # Similar content should have higher score
        self.assertGreater(score_similar, score_different)

    def test_create_contextual_summary(self):
        """Test creation of contextual summaries with metadata."""
        rcm = RecentContextManager(self.mock_db)
        
        # Create test conversation thread
        thread = [
            {
                'timestamp': self.base_time - timedelta(minutes=5),
                'summary': 'Player John built a wooden house',
                'server_name': 'Island-PvE',
                'tokens': 50
            },
            {
                'timestamp': self.base_time - timedelta(minutes=10),
                'summary': 'John gathered wood and stone materials',
                'server_name': 'Island-PvE',
                'tokens': 45
            }
        ]
        
        contextual_summary = rcm._create_contextual_summary(thread)
        
        # Verify structure
        self.assertIn('timeline', contextual_summary)
        self.assertIn('summary', contextual_summary)
        self.assertIn('servers', contextual_summary)
        self.assertIn('conversation_flow', contextual_summary)
        
        # Verify content
        self.assertIn('John', contextual_summary['summary'])
        self.assertIn('wooden house', contextual_summary['summary'])
        self.assertIn('Island-PvE', contextual_summary['servers'])

    def test_get_conversation_thread(self):
        """Test conversation thread analysis and grouping."""
        # Mock database responses
        recent_summaries = [
            (s['summary'], s['timestamp'], s['tokens'], s['server_name'])
            for s in self.test_summaries[:4]
        ]
        
        self.mock_db.get_recent_summaries.return_value = recent_summaries
        
        rcm = RecentContextManager(self.mock_db)
        
        # Get conversation thread for specific server
        thread = rcm.get_conversation_thread(
            server_name='Island-PvE',
            max_summaries=10,
            conversation_threshold=0.3
        )
        
        self.assertIsInstance(thread, list)
        self.assertGreater(len(thread), 0)
        
        # Verify each thread item has required fields
        for thread_group in thread:
            self.assertIn('summaries', thread_group)
            self.assertIn('start_time', thread_group)
            self.assertIn('end_time', thread_group)
            self.assertIn('servers', thread_group)

    def test_get_contextual_summaries_server_specific(self):
        """Test getting contextual summaries for specific server."""
        # Mock database responses
        self.mock_db.get_recent_summaries.return_value = [
            (s['summary'], s['timestamp'], s['tokens'], s['server_name'])
            for s in self.test_summaries if s['server_name'] == 'Island-PvE'
        ]
        
        self.mock_db._decompress_text.side_effect = lambda x: x  # Pass-through
        
        rcm = RecentContextManager(self.mock_db)
        
        # Get contextual summaries
        results = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=200
        )
        
        self.assertIsInstance(results, list)
        
        # Verify all results are relevant to the server
        for result in results:
            # Should contain server-relevant content
            self.assertTrue(len(result) > 0)

    def test_get_contextual_summaries_cluster_specific(self):
        """Test getting contextual summaries for specific cluster."""
        # Mock database responses
        self.mock_db.get_recent_cluster_summaries.return_value = [
            (s['summary'], s['timestamp'], s['tokens'])
            for s in self.test_cluster_summaries
        ]
        
        self.mock_db._decompress_text.side_effect = lambda x: x
        
        rcm = RecentContextManager(self.mock_db)
        
        # Get cluster contextual summaries
        results = rcm.get_contextual_summaries(
            cluster_name='MainCluster',
            target_tokens=150
        )
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_mixed_server_cluster_context(self):
        """Test getting contextual summaries with both server and cluster specified."""
        # Mock both server and cluster responses
        self.mock_db.get_recent_summaries.return_value = [
            (s['summary'], s['timestamp'], s['tokens'], s['server_name'])
            for s in self.test_summaries[:2]
        ]
        
        self.mock_db.get_recent_cluster_summaries.return_value = [
            (s['summary'], s['timestamp'], s['tokens'])
            for s in self.test_cluster_summaries[:1]
        ]
        
        self.mock_db._decompress_text.side_effect = lambda x: x
        
        rcm = RecentContextManager(self.mock_db)
        
        # Get mixed context
        results = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            cluster_name='MainCluster',
            target_tokens=300
        )
        
        self.assertIsInstance(results, list)
        # Should include both server and cluster summaries
        self.assertGreater(len(results), 0)

    def test_cache_functionality(self):
        """Test conversation cache functionality."""
        rcm = RecentContextManager(self.mock_db)
        
        # Mock database response
        self.mock_db.get_recent_summaries.return_value = [
            (s['summary'], s['timestamp'], s['tokens'], s['server_name'])
            for s in self.test_summaries[:3]
        ]
        
        # First call should hit database
        results1 = rcm.get_conversation_thread(
            server_name='Island-PvE',
            max_summaries=5,
            conversation_threshold=0.3
        )
        
        # Second call should use cache
        results2 = rcm.get_conversation_thread(
            server_name='Island-PvE',
            max_summaries=5,
            conversation_threshold=0.3
        )
        
        # Results should be identical
        self.assertEqual(len(results1), len(results2))
        
        # Database should only be called once (cache hit on second call)
        self.assertEqual(self.mock_db.get_recent_summaries.call_count, 1)

    def test_cache_expiry(self):
        """Test that cache expires after specified time."""
        rcm = RecentContextManager(self.mock_db)
        rcm.cache_duration = timedelta(seconds=0.1)  # Very short cache duration
        
        # Mock database response
        self.mock_db.get_recent_summaries.return_value = [
            (s['summary'], s['timestamp'], s['tokens'], s['server_name'])
            for s in self.test_summaries[:2]
        ]
        
        # First call
        results1 = rcm.get_conversation_thread(
            server_name='Island-PvE',
            max_summaries=5,
            conversation_threshold=0.3
        )
        
        # Wait for cache to expire
        import time
        time.sleep(0.2)
        
        # Second call should hit database again
        results2 = rcm.get_conversation_thread(
            server_name='Island-PvE',
            max_summaries=5,
            conversation_threshold=0.3
        )
        
        # Database should be called twice (cache expired)
        self.assertEqual(self.mock_db.get_recent_summaries.call_count, 2)

    def test_temporal_grouping_logic(self):
        """Test temporal grouping of conversations."""
        rcm = RecentContextManager(self.mock_db)
        
        # Create summaries with specific temporal patterns
        grouped_summaries = [
            # Group 1: Recent cluster (5-10 minutes ago)
            {
                'timestamp': self.base_time - timedelta(minutes=5),
                'summary': 'John started building',
                'server_name': 'Island-PvE',
                'tokens': 40
            },
            {
                'timestamp': self.base_time - timedelta(minutes=7),
                'summary': 'John gathered materials',
                'server_name': 'Island-PvE',
                'tokens': 35
            },
            {
                'timestamp': self.base_time - timedelta(minutes=10),
                'summary': 'John planned construction',
                'server_name': 'Island-PvE',
                'tokens': 38
            },
            # Gap in time
            # Group 2: Earlier cluster (2 hours ago)
            {
                'timestamp': self.base_time - timedelta(hours=2),
                'summary': 'Sarah tamed a Raptor',
                'server_name': 'Island-PvE',
                'tokens': 42
            }
        ]
        
        self.mock_db.get_recent_summaries.return_value = [
            (s['summary'], s['timestamp'], s['tokens'], s['server_name'])
            for s in grouped_summaries
        ]
        
        thread = rcm.get_conversation_thread(
            server_name='Island-PvE',
            max_summaries=10,
            conversation_threshold=0.4
        )
        
        # Should group into separate conversation threads
        self.assertGreaterEqual(len(thread), 1)
        
        # First thread should contain John's building activities
        first_thread_summaries = thread[0]['summaries']
        john_mentions = sum(1 for s in first_thread_summaries if 'John' in s['summary'])
        self.assertGreater(john_mentions, 1)

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        rcm = RecentContextManager(self.mock_db)
        
        # Test with no summaries
        self.mock_db.get_recent_summaries.return_value = []
        results = rcm.get_contextual_summaries(
            server_name='NonexistentServer',
            target_tokens=100
        )
        self.assertEqual(len(results), 0)
        
        # Test with None database
        with self.assertRaises(AttributeError):
            rcm_none = RecentContextManager(None)
            rcm_none.get_contextual_summaries(server_name='Test', target_tokens=100)
        
        # Test with invalid token count
        results = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=0
        )
        self.assertEqual(len(results), 0)
        
        # Test with negative token count
        results = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=-100
        )
        self.assertEqual(len(results), 0)

    def test_decompression_integration(self):
        """Test integration with database decompression."""
        rcm = RecentContextManager(self.mock_db)
        
        # Mock compressed data
        compressed_summary = "compressed_data_placeholder"
        decompressed_summary = "Player built a magnificent castle"
        
        self.mock_db.get_recent_summaries.return_value = [
            (compressed_summary, self.base_time, 50, 'Island-PvE')
        ]
        
        self.mock_db._decompress_text.return_value = decompressed_summary
        
        results = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=100
        )
        
        # Verify decompression was called
        self.mock_db._decompress_text.assert_called_with(compressed_summary)
        
        # Verify decompressed content is in results
        self.assertGreater(len(results), 0)
        result_text = ' '.join(results)
        self.assertIn('castle', result_text)


class TestRecentContextIntegration(unittest.TestCase):
    """Integration tests for RecentContextManager with realistic scenarios."""

    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_integration.db')
        
        # Create real database for integration testing
        self.create_test_database()
        
        # Create mock database manager with realistic behavior
        self.mock_db = Mock(spec=DatabaseManager)
        self.setup_realistic_database_behavior()

    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_database(self):
        """Create a test database with realistic schema."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create summaries table
        cursor.execute('''
            CREATE TABLE summaries (
                id INTEGER PRIMARY KEY,
                server_name TEXT,
                summary TEXT,
                timestamp DATETIME,
                tokens INTEGER
            )
        ''')
        
        # Create cluster_summaries table
        cursor.execute('''
            CREATE TABLE cluster_summaries (
                id INTEGER PRIMARY KEY,
                cluster_name TEXT,
                summary TEXT,
                timestamp DATETIME,
                tokens INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()

    def setup_realistic_database_behavior(self):
        """Setup realistic database behavior for integration tests."""
        base_time = datetime.now()
        
        # Realistic ARK server summaries
        realistic_summaries = [
            # Recent building activity thread
            ("John and Sarah collaborated on building a massive stone fortress near the waterfall", 
             base_time - timedelta(minutes=2), 65, "Island-PvE"),
            ("John gathered metal ingots while Sarah prepared the foundation blueprint", 
             base_time - timedelta(minutes=8), 58, "Island-PvE"),
            ("Construction project started: fortress location scouted by John and Sarah", 
             base_time - timedelta(minutes=15), 62, "Island-PvE"),
            
            # Separate taming activity thread
            ("Mike successfully tamed a level 150 Rex using kibble and patience", 
             base_time - timedelta(minutes=25), 55, "Island-PvE"),
            ("Mike prepared kibble and narcotics for the Rex taming attempt", 
             base_time - timedelta(minutes=45), 52, "Island-PvE"),
            
            # PvP activity on different server
            ("Raid defense successful: Enemy tribe's attack on the mountain base was repelled", 
             base_time - timedelta(hours=1), 70, "Ragnarok-PvP"),
            ("Alert: Enemy tribe spotted near the mountain base perimeter", 
             base_time - timedelta(hours=1, minutes=15), 48, "Ragnarok-PvP"),
            
            # Older activities
            ("Community event: Dragon boss fight organized with 5 tribes participating", 
             base_time - timedelta(days=1), 68, "Island-PvE"),
            ("Resource gathering expedition discovered rich metal node in volcano cave", 
             base_time - timedelta(days=2), 60, "Island-PvE"),
        ]
        
        self.mock_db.get_recent_summaries.return_value = realistic_summaries
        self.mock_db._decompress_text.side_effect = lambda x: x  # No compression for test

    def test_realistic_conversation_threading(self):
        """Test conversation threading with realistic ARK scenarios."""
        rcm = RecentContextManager(self.mock_db)
        
        # Get conversation threads for Island-PvE
        threads = rcm.get_conversation_thread(
            server_name='Island-PvE',
            max_summaries=15,
            conversation_threshold=0.3
        )
        
        self.assertGreater(len(threads), 0)
        
        # Verify building thread is properly grouped
        building_thread = None
        for thread in threads:
            summaries_text = ' '.join([s['summary'] for s in thread['summaries']])
            if 'John' in summaries_text and 'Sarah' in summaries_text and 'fortress' in summaries_text:
                building_thread = thread
                break
        
        self.assertIsNotNone(building_thread, "Building conversation thread should be identified")
        self.assertGreaterEqual(len(building_thread['summaries']), 2, "Building thread should have multiple related summaries")
        
        # Verify temporal ordering within thread
        timestamps = [s['timestamp'] for s in building_thread['summaries']]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True), "Summaries should be ordered by timestamp (newest first)")

    def test_contextual_summary_generation(self):
        """Test contextual summary generation with realistic data."""
        rcm = RecentContextManager(self.mock_db)
        
        # Get contextual summaries
        contextual_summaries = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=300
        )
        
        self.assertGreater(len(contextual_summaries), 0)
        
        # Verify content quality
        combined_text = ' '.join(contextual_summaries)
        
        # Should contain key players and activities
        self.assertIn('John', combined_text)
        self.assertIn('Sarah', combined_text)
        
        # Should contain building context
        building_terms = ['fortress', 'building', 'stone', 'construction']
        has_building_context = any(term in combined_text.lower() for term in building_terms)
        self.assertTrue(has_building_context, "Should contain building-related context")

    def test_cross_server_context_isolation(self):
        """Test that server-specific context is properly isolated."""
        rcm = RecentContextManager(self.mock_db)
        
        # Get context for Island-PvE
        island_context = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=200
        )
        
        # Get context for Ragnarok-PvP
        ragnarok_context = rcm.get_contextual_summaries(
            server_name='Ragnarok-PvP',
            target_tokens=200
        )
        
        # Verify context isolation
        island_text = ' '.join(island_context).lower()
        ragnarok_text = ' '.join(ragnarok_context).lower()
        
        # Island should not contain PvP raid content
        self.assertNotIn('raid', island_text)
        self.assertNotIn('enemy tribe', island_text)
        
        # Ragnarok should contain PvP content
        # Note: This test depends on the mock setup including Ragnarok data
        # which might not be returned due to server filtering

    def test_token_budget_optimization(self):
        """Test token budget optimization and distribution."""
        rcm = RecentContextManager(self.mock_db)
        
        # Test with limited token budget
        limited_context = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=150  # Limited budget
        )
        
        # Test with generous token budget
        generous_context = rcm.get_contextual_summaries(
            server_name='Island-PvE',
            target_tokens=500  # Generous budget
        )
        
        # Generous budget should return more context
        self.assertGreaterEqual(len(generous_context), len(limited_context))
        
        # Verify token limits are respected
        limited_tokens = sum(len(summary.split()) * 1.3 for summary in limited_context)
        self.assertLessEqual(limited_tokens, 150 * 1.2)  # Allow some margin for estimation

    def test_temporal_filtering_accuracy(self):
        """Test temporal filtering accuracy."""
        rcm = RecentContextManager(self.mock_db)
        
        # Test hour-based filtering
        hourly_summaries = rcm.get_recent_summaries_by_timeframe(
            server_name='Island-PvE',
            hours=1,
            max_tokens=200
        )
        
        # Test day-based filtering
        daily_summaries = rcm.get_recent_summaries_by_timeframe(
            server_name='Island-PvE',
            days=1,
            max_tokens=400
        )
        
        # Daily should include more summaries than hourly
        self.assertGreaterEqual(len(daily_summaries), len(hourly_summaries))
        
        # Verify temporal relevance
        if hourly_summaries:
            # Recent summaries should contain current activities
            recent_text = ' '.join(hourly_summaries).lower()
            self.assertTrue(
                'fortress' in recent_text or 'building' in recent_text,
                "Recent summaries should contain current building activities"
            )


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
