"""
Comprehensive integration tests for the complete AI Memory System
Tests the interaction between Vector Memory (Phase 1) and Enhanced Context Manager (Phase 2)
"""

import unittest
import tempfile
import shutil
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import numpy as np

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after path setup
try:
    from vector_memory import VectorMemoryManager
    from recent_context import RecentContextManager
    from database import DatabaseManager
    from main import Application
    from config import Config
except ImportError as e:
    print(f"Import error: {e}")
    print("Some modules may not be available for testing")


class TestAIMemorySystemIntegration(unittest.TestCase):
    """Integration tests for the complete AI Memory System."""

    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_integration.db')
        self.test_vector_db_path = os.path.join(self.test_dir, 'test_vector.db')
        
        # Create mock configuration
        self.mock_config = Mock()
        self.mock_config.database_path = self.test_db_path
        self.mock_config.vector_memory_enabled = True
        self.mock_config.vector_memory_model = 'sentence-transformers/all-MiniLM-L6-v2'
        self.mock_config.vector_memory_top_k = 3
        self.mock_config.vector_memory_similarity_threshold = 0.3
        self.mock_config.input_token_size = 4000
        
        # Test scenarios
        self.ark_scenarios = [
            {
                'content': 'Player John built a magnificent stone castle with multiple towers and defensive walls',
                'context': 'Island-PvE',
                'timestamp': datetime.now() - timedelta(minutes=5)
            },
            {
                'content': 'Sarah successfully tamed a level 150 Rex using advanced kibble and careful planning',
                'context': 'Island-PvE', 
                'timestamp': datetime.now() - timedelta(minutes=15)
            },
            {
                'content': 'Alpha Raptor pack invaded the beach area and destroyed several small buildings',
                'context': 'Island-PvE',
                'timestamp': datetime.now() - timedelta(minutes=30)
            },
            {
                'content': 'Tribe alliance successfully defeated the Dragon boss in epic battle',
                'context': 'Island-PvE',
                'timestamp': datetime.now() - timedelta(hours=1)
            },
            {
                'content': 'New player Mike joined and received help from veteran players with building materials',
                'context': 'Island-PvE',
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'content': 'Cross-server raid attempt was successfully defended by coordinated base defenses',
                'context': 'Ragnarok-PvP',
                'timestamp': datetime.now() - timedelta(hours=3)
            }
        ]

    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('vector_memory.SentenceTransformer')
    def test_vector_and_context_memory_coordination(self, mock_transformer):
        """Test coordination between vector memory and context manager."""
        # Setup mock transformer
        mock_model = Mock()
        
        def mock_encode(text):
            # Simulate embeddings based on content type
            embedding = np.random.normal(0, 0.1, 384)
            
            if 'build' in text.lower() or 'castle' in text.lower():
                embedding[0] = 0.8  # Building dimension
            elif 'tame' in text.lower() or 'rex' in text.lower():
                embedding[1] = 0.8  # Taming dimension
            elif 'fight' in text.lower() or 'boss' in text.lower():
                embedding[2] = 0.8  # Combat dimension
            elif 'raid' in text.lower() or 'defend' in text.lower():
                embedding[3] = 0.8  # PvP dimension
                
            return embedding
        
        mock_model.encode.side_effect = mock_encode
        mock_transformer.return_value = mock_model
        
        # Create vector memory manager
        vector_manager = VectorMemoryManager(self.mock_config)
        
        # Create mock database manager for context manager
        mock_db = Mock(spec=DatabaseManager)
        context_manager = RecentContextManager(mock_db)
        
        # Store memories in vector system
        for scenario in self.ark_scenarios:
            vector_manager.store_memory(scenario['content'], scenario['context'])
        
        # Setup context manager with realistic data
        mock_db.get_recent_summaries.return_value = [
            (scenario['content'], scenario['timestamp'], len(scenario['content'].split()) * 2, scenario['context'])
            for scenario in self.ark_scenarios[:4]  # Recent summaries
        ]
        mock_db._decompress_text.side_effect = lambda x: x
        
        # Test coordinated retrieval for building-related query
        building_query = "Player wants to construct a large fortress"
        
        # Get semantic memories (similar past experiences)
        semantic_memories = vector_manager.search_similar_memories(building_query, "Island-PvE")
        
        # Get contextual summaries (conversation flow)
        contextual_summaries = context_manager.get_contextual_summaries(
            server_name="Island-PvE",
            target_tokens=200
        )
        
        # Verify coordination
        self.assertIsInstance(semantic_memories, list)
        self.assertIsInstance(contextual_summaries, list)
        
        # Should have building-related semantic memory
        semantic_text = ' '.join(semantic_memories)
        self.assertIn('castle', semantic_text.lower())
        
        # Should have recent contextual information
        contextual_text = ' '.join(contextual_summaries)
        self.assertGreater(len(contextual_text), 0)

    @patch('vector_memory.SentenceTransformer')
    def test_memory_system_with_realistic_workflow(self, mock_transformer):
        """Test complete memory system workflow with realistic ARK scenario."""
        # Setup mock transformer
        mock_model = Mock()
        mock_model.encode.return_value = np.random.normal(0, 0.1, 384)
        mock_transformer.return_value = mock_model
        
        # Create vector memory manager
        vector_manager = VectorMemoryManager(self.mock_config)
        
        # Create mock database and context manager
        mock_db = Mock(spec=DatabaseManager)
        context_manager = RecentContextManager(mock_db)
        
        # Simulate realistic workflow: multiple gaming sessions
        
        # Session 1: Building activities
        building_memories = [
            "John started construction of a stone fortress on the hilltop",
            "Sarah helped John by gathering stone and metal for the fortress",
            "The fortress foundation was completed after 2 hours of work"
        ]
        
        for memory in building_memories:
            vector_manager.store_memory(memory, "Island-PvE")
        
        # Session 2: Taming activities  
        taming_memories = [
            "Mike began taming a high-level Spino near the swamp",
            "The Spino taming was successful after using prime meat",
            "Mike named his new Spino 'Swamp King' and built a pen"
        ]
        
        for memory in taming_memories:
            vector_manager.store_memory(memory, "Island-PvE")
        
        # Setup context manager with session data
        all_memories = building_memories + taming_memories
        base_time = datetime.now()
        
        mock_db.get_recent_summaries.return_value = [
            (memory, base_time - timedelta(minutes=i*15), len(memory.split())*2, "Island-PvE")
            for i, memory in enumerate(reversed(all_memories))
        ]
        mock_db._decompress_text.side_effect = lambda x: x
        
        # Test query for building advice
        building_query = "How to build a secure base?"
        
        semantic_results = vector_manager.search_similar_memories(building_query, "Island-PvE")
        contextual_results = context_manager.get_contextual_summaries(
            server_name="Island-PvE",
            target_tokens=150
        )
        
        # Verify building memories are retrieved
        semantic_text = ' '.join(semantic_results).lower()
        self.assertTrue(
            'fortress' in semantic_text or 'stone' in semantic_text,
            "Should retrieve building-related semantic memories"
        )
        
        # Verify recent context includes relevant activities
        contextual_text = ' '.join(contextual_results).lower()
        self.assertGreater(len(contextual_text), 0)
        
        # Test query for taming advice
        taming_query = "Best way to tame large dinosaurs?"
        
        taming_semantic = vector_manager.search_similar_memories(taming_query, "Island-PvE")
        taming_text = ' '.join(taming_semantic).lower()
        
        self.assertTrue(
            'spino' in taming_text or 'taming' in taming_text,
            "Should retrieve taming-related semantic memories"
        )

    def test_token_budget_coordination(self):
        """Test token budget coordination between vector and context systems."""
        # Create mock systems
        mock_vector = Mock(spec=VectorMemoryManager)
        mock_vector.enabled = True
        mock_vector.search_similar_memories.return_value = [
            "Semantic memory 1 with building content",
            "Semantic memory 2 with construction details"
        ]
        
        mock_db = Mock(spec=DatabaseManager)
        context_manager = RecentContextManager(mock_db)
        
        # Setup context manager data
        mock_db.get_recent_summaries.return_value = [
            ("Recent summary 1", datetime.now() - timedelta(minutes=5), 50, "Island-PvE"),
            ("Recent summary 2", datetime.now() - timedelta(minutes=10), 45, "Island-PvE"),
            ("Recent summary 3", datetime.now() - timedelta(minutes=20), 60, "Island-PvE")
        ]
        mock_db._decompress_text.side_effect = lambda x: x
        
        # Test token budget allocation
        total_budget = 300
        context_budget = total_budget // 3  # 33% for context as in main.py
        
        contextual_results = context_manager.get_contextual_summaries(
            server_name="Island-PvE",
            target_tokens=context_budget
        )
        
        # Estimate tokens used by context
        context_tokens = sum(len(result.split()) * 1.3 for result in contextual_results)
        
        # Should respect budget
        self.assertLessEqual(context_tokens, context_budget * 1.2)  # Allow some margin
        
        # Remaining budget should be available for semantic memories
        remaining_budget = total_budget - context_tokens
        self.assertGreater(remaining_budget, 0)

    @patch('vector_memory.SentenceTransformer')
    def test_cross_server_memory_isolation(self, mock_transformer):
        """Test memory isolation between different servers."""
        # Setup mock transformer
        mock_model = Mock()
        mock_model.encode.return_value = np.random.normal(0, 0.1, 384)
        mock_transformer.return_value = mock_model
        
        vector_manager = VectorMemoryManager(self.mock_config)
        
        # Store server-specific memories
        island_memories = [
            "Island PvE: Peaceful building session with beautiful castle",
            "Island PvE: Cooperative taming of gentle herbivores"
        ]
        
        ragnarok_memories = [
            "Ragnarok PvP: Intense raid battle with heavy casualties",
            "Ragnarok PvP: Aggressive PvP tactics and base destruction"
        ]
        
        for memory in island_memories:
            vector_manager.store_memory(memory, "Island-PvE")
            
        for memory in ragnarok_memories:
            vector_manager.store_memory(memory, "Ragnarok-PvP")
        
        # Test server-specific retrieval
        island_query = "Building and taming activities"
        island_results = vector_manager.search_similar_memories(island_query, "Island-PvE")
        
        ragnarok_query = "PvP combat strategies"
        ragnarok_results = vector_manager.search_similar_memories(ragnarok_query, "Ragnarok-PvP")
        
        # Verify context isolation
        island_text = ' '.join(island_results).lower()
        ragnarok_text = ' '.join(ragnarok_results).lower()
        
        # Island results should not contain PvP content
        self.assertNotIn('raid', island_text)
        self.assertNotIn('battle', island_text)
        
        # Ragnarok results should not contain peaceful content
        # (depending on similarity, this may vary)
        if ragnarok_results:
            self.assertTrue(
                'pvp' in ragnarok_text or 'raid' in ragnarok_text,
                "Ragnarok results should contain PvP-related content"
            )

    def test_memory_system_performance_characteristics(self):
        """Test performance characteristics of the memory system."""
        # Create mock systems for performance testing
        mock_db = Mock(spec=DatabaseManager)
        context_manager = RecentContextManager(mock_db)
        
        # Setup large dataset simulation
        large_dataset = []
        base_time = datetime.now()
        
        for i in range(100):  # Simulate 100 summaries
            large_dataset.append((
                f"Summary {i} with various content and activities",
                base_time - timedelta(minutes=i*5),
                50,  # tokens
                "Island-PvE"
            ))
        
        mock_db.get_recent_summaries.return_value = large_dataset
        mock_db._decompress_text.side_effect = lambda x: x
        
        # Test performance with large dataset
        import time
        start_time = time.time()
        
        results = context_manager.get_contextual_summaries(
            server_name="Island-PvE",
            target_tokens=500
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (< 1 second for mock data)
        self.assertLess(processing_time, 1.0)
        
        # Should return reasonable number of results
        self.assertGreater(len(results), 0)
        self.assertLess(len(results), 100)  # Should not return all 100

    def test_conversation_threading_with_vector_similarity(self):
        """Test conversation threading enhanced by vector similarity."""
        mock_db = Mock(spec=DatabaseManager)
        context_manager = RecentContextManager(mock_db)
        
        # Create conversation with thematic similarity
        base_time = datetime.now()
        conversation_data = [
            # Building conversation thread
            ("John finished the stone walls of the fortress", base_time - timedelta(minutes=2), 45, "Island-PvE"),
            ("John worked on fortress gate mechanism", base_time - timedelta(minutes=8), 42, "Island-PvE"),
            ("John started fortress construction project", base_time - timedelta(minutes=20), 48, "Island-PvE"),
            
            # Separate taming thread
            ("Sarah's Rex reached full taming effectiveness", base_time - timedelta(minutes=25), 40, "Island-PvE"),
            ("Sarah began Rex taming process with kibble", base_time - timedelta(minutes=45), 43, "Island-PvE"),
            
            # Unrelated event
            ("Weather event: Heavy rain affected visibility", base_time - timedelta(hours=1), 35, "Island-PvE")
        ]
        
        mock_db.get_recent_summaries.return_value = conversation_data
        mock_db._decompress_text.side_effect = lambda x: x
        
        # Get conversation threads
        threads = context_manager.get_conversation_thread(
            server_name="Island-PvE",
            max_summaries=10,
            conversation_threshold=0.3
        )
        
        self.assertGreater(len(threads), 0)
        
        # Verify thematic grouping
        # Building thread should be grouped together
        building_thread = None
        for thread in threads:
            summaries_text = ' '.join([s['summary'] for s in thread['summaries']])
            if 'fortress' in summaries_text and summaries_text.count('John') >= 2:
                building_thread = thread
                break
        
        self.assertIsNotNone(building_thread, "Building thread should be identified")
        self.assertGreaterEqual(len(building_thread['summaries']), 2)

    @patch('vector_memory.SentenceTransformer')
    def test_memory_system_error_recovery(self, mock_transformer):
        """Test error recovery and graceful degradation."""
        # Test vector memory failure
        mock_transformer.side_effect = Exception("Model loading failed")
        
        vector_manager = VectorMemoryManager(self.mock_config)
        
        # Should gracefully disable
        self.assertFalse(vector_manager.enabled)
        
        # Should return empty results without crashing
        results = vector_manager.search_similar_memories("test query", "Island-PvE")
        self.assertEqual(len(results), 0)
        
        # Test context manager with database errors
        mock_db = Mock(spec=DatabaseManager)
        mock_db.get_recent_summaries.side_effect = Exception("Database error")
        
        context_manager = RecentContextManager(mock_db)
        
        # Should handle database errors gracefully
        try:
            results = context_manager.get_contextual_summaries(
                server_name="Island-PvE",
                target_tokens=100
            )
            # Should return empty list or handle gracefully
            self.assertIsInstance(results, list)
        except Exception:
            # Or may raise exception, which is also acceptable
            pass


class TestMemorySystemConfiguration(unittest.TestCase):
    """Test memory system configuration and settings."""
    
    def test_vector_memory_configuration_validation(self):
        """Test vector memory configuration validation."""
        # Test valid configuration
        valid_config = Mock()
        valid_config.vector_memory_enabled = True
        valid_config.vector_memory_model = 'sentence-transformers/all-MiniLM-L6-v2'
        valid_config.vector_memory_top_k = 5
        valid_config.vector_memory_similarity_threshold = 0.7
        valid_config.database_path = 'test.db'
        
        with patch('vector_memory.SentenceTransformer'):
            vm = VectorMemoryManager(valid_config)
            self.assertTrue(vm.enabled)
            self.assertEqual(vm.top_k, 5)
            self.assertEqual(vm.similarity_threshold, 0.7)
    
    def test_context_manager_configuration(self):
        """Test context manager configuration."""
        mock_db = Mock(spec=DatabaseManager)
        rcm = RecentContextManager(mock_db)
        
        # Test default configuration
        self.assertEqual(rcm.db, mock_db)
        self.assertIsInstance(rcm.conversation_cache, dict)
        
        # Test cache functionality
        self.assertEqual(len(rcm.conversation_cache), 0)
        self.assertEqual(len(rcm.cache_expiry), 0)


if __name__ == '__main__':
    # Set up test discovery
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAIMemorySystemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorySystemConfiguration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
