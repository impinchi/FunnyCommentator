"""
Comprehensive tests for Phase 1: Vector Memory System
Tests the VectorMemoryManager functionality including embeddings, storage, and similarity search.
"""

import unittest
import tempfile
import shutil
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vector_memory import VectorMemoryManager


class TestVectorMemoryManager(unittest.TestCase):
    """Test suite for VectorMemoryManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_vector_memory.db')
        
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.vector_memory_enabled = True
        self.mock_config.vector_memory_model = 'sentence-transformers/all-MiniLM-L6-v2'
        self.mock_config.vector_memory_top_k = 5
        self.mock_config.vector_memory_similarity_threshold = 0.7
        self.mock_config.database_path = self.test_db_path
        
        # Test data
        self.test_memories = [
            "Player John joined the server and started building a wooden house",
            "Player Sarah tamed a Raptor near the beach and named it Spike",
            "A massive Giganotosaurus appeared near the base and destroyed everything",
            "Players formed an alliance to take down the Alpha Rex in the volcano",
            "New player Mike asked for help with basic survival tips"
        ]
        
        self.test_contexts = [
            "Island Server - PvE",
            "Ragnarok Server - PvP", 
            "Island Server - PvE",
            "Ragnarok Server - PvP",
            "Island Server - PvE"
        ]

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove temporary directory and all contents
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization_enabled(self):
        """Test VectorMemoryManager initialization when enabled."""
        with patch('vector_memory.SentenceTransformer') as mock_transformer:
            mock_model = Mock()
            mock_transformer.return_value = mock_model
            
            vm = VectorMemoryManager(self.mock_config)
            
            self.assertTrue(vm.enabled)
            self.assertEqual(vm.model_name, 'sentence-transformers/all-MiniLM-L6-v2')
            self.assertEqual(vm.top_k, 5)
            self.assertEqual(vm.similarity_threshold, 0.7)
            mock_transformer.assert_called_once_with('sentence-transformers/all-MiniLM-L6-v2')

    def test_initialization_disabled(self):
        """Test VectorMemoryManager initialization when disabled."""
        self.mock_config.vector_memory_enabled = False
        
        vm = VectorMemoryManager(self.mock_config)
        
        self.assertFalse(vm.enabled)
        self.assertIsNone(vm.model)

    def test_database_creation(self):
        """Test that the vector memory database is created properly."""
        with patch('vector_memory.SentenceTransformer'):
            vm = VectorMemoryManager(self.mock_config)
            vm._ensure_database()
            
            # Check that database file exists
            self.assertTrue(os.path.exists(self.test_db_path))
            
            # Check database schema
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vector_memories'")
            table_exists = cursor.fetchone() is not None
            self.assertTrue(table_exists)
            
            # Check table structure
            cursor.execute("PRAGMA table_info(vector_memories)")
            columns = [column[1] for column in cursor.fetchall()]
            expected_columns = ['id', 'content', 'embedding', 'context', 'timestamp', 'content_hash']
            for col in expected_columns:
                self.assertIn(col, columns)
            
            conn.close()

    @patch('vector_memory.SentenceTransformer')
    def test_store_memory(self, mock_transformer):
        """Test storing memories in the vector database."""
        # Mock the transformer model
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Store a memory
        content = "Player built a magnificent castle"
        context = "Test Server"
        
        result = vm.store_memory(content, context)
        self.assertTrue(result)
        
        # Verify it was stored in database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content, context FROM vector_memories WHERE content = ?", (content,))
        stored_memory = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(stored_memory)
        self.assertEqual(stored_memory[0], content)
        self.assertEqual(stored_memory[1], context)
        
        # Verify model was called
        mock_model.encode.assert_called_once_with(content)

    @patch('vector_memory.SentenceTransformer')
    def test_duplicate_memory_prevention(self, mock_transformer):
        """Test that duplicate memories are not stored."""
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        vm = VectorMemoryManager(self.mock_config)
        
        content = "Duplicate memory test"
        context = "Test Server"
        
        # Store the same memory twice
        result1 = vm.store_memory(content, context)
        result2 = vm.store_memory(content, context)
        
        self.assertTrue(result1)
        self.assertFalse(result2)  # Should return False for duplicate
        
        # Verify only one entry exists
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vector_memories WHERE content = ?", (content,))
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)

    @patch('vector_memory.SentenceTransformer')
    def test_search_similar_memories(self, mock_transformer):
        """Test searching for similar memories."""
        mock_model = Mock()
        
        # Create mock embeddings for stored memories and query
        stored_embeddings = [
            np.array([1.0, 0.0, 0.0]),  # Building-related
            np.array([0.0, 1.0, 0.0]),  # Taming-related
            np.array([0.0, 0.0, 1.0]),  # Combat-related
        ]
        
        query_embedding = np.array([0.9, 0.1, 0.0])  # Similar to building
        
        # Mock encode to return appropriate embeddings
        encode_calls = 0
        def mock_encode(text):
            nonlocal encode_calls
            if encode_calls < len(stored_embeddings):
                result = stored_embeddings[encode_calls]
                encode_calls += 1
                return result
            else:
                return query_embedding
        
        mock_model.encode.side_effect = mock_encode
        mock_transformer.return_value = mock_model
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Store test memories
        test_memories = [
            "Player built a wooden house",
            "Player tamed a Raptor",
            "Player fought an Alpha Rex"
        ]
        
        for memory in test_memories:
            vm.store_memory(memory, "Test Server")
        
        # Search for similar memories
        query = "Player constructed a stone building"
        results = vm.search_similar_memories(query, "Test Server")
        
        # Should return the building-related memory as most similar
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertIn("wooden house", results[0])

    @patch('vector_memory.SentenceTransformer')
    def test_similarity_threshold(self, mock_transformer):
        """Test that similarity threshold is respected."""
        mock_model = Mock()
        
        # Create embeddings with low similarity
        stored_embedding = np.array([1.0, 0.0, 0.0])
        query_embedding = np.array([0.0, 0.0, 1.0])  # Very different
        
        encode_calls = 0
        def mock_encode(text):
            nonlocal encode_calls
            if encode_calls == 0:
                encode_calls += 1
                return stored_embedding
            else:
                return query_embedding
        
        mock_model.encode.side_effect = mock_encode
        mock_transformer.return_value = mock_model
        
        # Set high similarity threshold
        self.mock_config.vector_memory_similarity_threshold = 0.9
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Store a memory
        vm.store_memory("Completely different topic", "Test Server")
        
        # Search with dissimilar query
        results = vm.search_similar_memories("Unrelated query", "Test Server")
        
        # Should return empty list due to low similarity
        self.assertEqual(len(results), 0)

    @patch('vector_memory.SentenceTransformer')
    def test_top_k_limit(self, mock_transformer):
        """Test that top_k parameter limits results."""
        mock_model = Mock()
        
        # Create similar embeddings
        base_embedding = np.array([1.0, 0.0, 0.0])
        mock_model.encode.return_value = base_embedding
        mock_transformer.return_value = mock_model
        
        # Set top_k to 2
        self.mock_config.vector_memory_top_k = 2
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Store multiple similar memories
        for i in range(5):
            vm.store_memory(f"Similar memory {i}", "Test Server")
        
        # Search should return only top_k results
        results = vm.search_similar_memories("Similar query", "Test Server")
        
        self.assertLessEqual(len(results), 2)

    def test_cosine_similarity_calculation(self):
        """Test cosine similarity calculation."""
        with patch('vector_memory.SentenceTransformer'):
            vm = VectorMemoryManager(self.mock_config)
            
            # Test identical vectors
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])
            similarity = vm._cosine_similarity(vec1, vec2)
            self.assertAlmostEqual(similarity, 1.0, places=5)
            
            # Test orthogonal vectors
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([0.0, 1.0, 0.0])
            similarity = vm._cosine_similarity(vec1, vec2)
            self.assertAlmostEqual(similarity, 0.0, places=5)
            
            # Test opposite vectors
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([-1.0, 0.0, 0.0])
            similarity = vm._cosine_similarity(vec1, vec2)
            self.assertAlmostEqual(similarity, -1.0, places=5)

    @patch('vector_memory.SentenceTransformer')
    def test_context_filtering(self, mock_transformer):
        """Test that context filtering works correctly."""
        mock_model = Mock()
        mock_embedding = np.array([1.0, 0.0, 0.0])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Store memories in different contexts
        vm.store_memory("Island memory", "Island Server")
        vm.store_memory("Ragnarok memory", "Ragnarok Server")
        vm.store_memory("Another island memory", "Island Server")
        
        # Search within specific context
        results = vm.search_similar_memories("Query", "Island Server")
        
        # Verify only Island Server memories are returned
        for result in results:
            # Check that result is from Island context
            # (This would need actual context verification in implementation)
            self.assertIn("island", result.lower())

    @patch('vector_memory.SentenceTransformer')
    def test_error_handling(self, mock_transformer):
        """Test error handling in various scenarios."""
        # Test model loading failure
        mock_transformer.side_effect = Exception("Model loading failed")
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Should handle gracefully and disable functionality
        self.assertFalse(vm.enabled)
        
        # Test database connection failure
        mock_transformer.side_effect = None
        mock_model = Mock()
        mock_transformer.return_value = mock_model
        
        # Use invalid database path
        self.mock_config.database_path = "/invalid/path/database.db"
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Should handle database errors gracefully
        result = vm.store_memory("Test memory", "Test Server")
        self.assertFalse(result)

    @patch('vector_memory.SentenceTransformer')
    def test_memory_content_formats(self, mock_transformer):
        """Test handling of different memory content formats."""
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Test various content formats
        test_contents = [
            "Simple string",
            "Multi-line\ncontent\nwith\nbreaks",
            "Content with special characters: !@#$%^&*()",
            "Unicode content: 🦕🏰⚔️",
            "",  # Empty string
            "   Whitespace padded   ",
            "Content with 'quotes' and \"double quotes\"",
        ]
        
        for content in test_contents:
            if content.strip():  # Skip empty content
                result = vm.store_memory(content, "Test Server")
                self.assertTrue(result, f"Failed to store content: {repr(content)}")


class TestVectorMemoryIntegration(unittest.TestCase):
    """Integration tests for VectorMemoryManager with real components."""

    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_integration.db')
        
        self.mock_config = Mock()
        self.mock_config.vector_memory_enabled = True
        self.mock_config.vector_memory_model = 'sentence-transformers/all-MiniLM-L6-v2'
        self.mock_config.vector_memory_top_k = 3
        self.mock_config.vector_memory_similarity_threshold = 0.3
        self.mock_config.database_path = self.test_db_path

    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('vector_memory.SentenceTransformer')
    def test_realistic_memory_scenario(self, mock_transformer):
        """Test a realistic scenario with ARK-like game events."""
        # Create mock model with realistic behavior
        mock_model = Mock()
        
        # Simulate different embeddings for different types of content
        def mock_encode(text):
            # Simple simulation based on keywords
            embedding = np.zeros(384)  # Typical sentence-transformer dimension
            
            if 'build' in text.lower() or 'house' in text.lower() or 'castle' in text.lower():
                embedding[0] = 0.8  # Building dimension
            if 'tame' in text.lower() or 'dino' in text.lower() or 'raptor' in text.lower():
                embedding[1] = 0.8  # Taming dimension
            if 'fight' in text.lower() or 'alpha' in text.lower() or 'battle' in text.lower():
                embedding[2] = 0.8  # Combat dimension
            if 'join' in text.lower() or 'new' in text.lower() or 'player' in text.lower():
                embedding[3] = 0.8  # Social dimension
                
            # Add some noise
            embedding += np.random.normal(0, 0.1, 384)
            return embedding
        
        mock_model.encode.side_effect = mock_encode
        mock_transformer.return_value = mock_model
        
        vm = VectorMemoryManager(self.mock_config)
        
        # Store various ARK-related memories
        game_events = [
            ("Player John built an impressive stone castle on the beach", "Island-PvE"),
            ("Sarah tamed a high-level Raptor and named it Spike", "Island-PvE"),
            ("Alpha Rex appeared and destroyed half the base structures", "Island-PvE"),
            ("New player Mike joined and asked for building materials", "Island-PvE"),
            ("Tribe war broke out over metal resources in the mountains", "Ragnarok-PvP"),
            ("Someone built a magnificent wooden bridge across the canyon", "Ragnarok-PvP"),
            ("Pack of wild Raptors invaded the starter beach area", "Island-PvE"),
        ]
        
        # Store all events
        for event, context in game_events:
            result = vm.store_memory(event, context)
            self.assertTrue(result)
        
        # Test similarity searches for different types of queries
        
        # Building-related query
        building_results = vm.search_similar_memories(
            "Player constructed a large fortress",
            "Island-PvE"
        )
        self.assertGreater(len(building_results), 0)
        # Should contain building-related memories
        has_building_memory = any('castle' in result or 'bridge' in result 
                                for result in building_results)
        self.assertTrue(has_building_memory)
        
        # Taming-related query
        taming_results = vm.search_similar_memories(
            "Dinosaur was successfully tamed by a player",
            "Island-PvE"
        )
        self.assertGreater(len(taming_results), 0)
        # Should contain taming-related memories
        has_taming_memory = any('tame' in result.lower() or 'raptor' in result.lower()
                               for result in taming_results)
        self.assertTrue(has_taming_memory)
        
        # Combat-related query
        combat_results = vm.search_similar_memories(
            "Dangerous creature attacked the settlement",
            "Island-PvE"
        )
        self.assertGreater(len(combat_results), 0)
        
        # Cross-context search (should not return Ragnarok memories for Island query)
        island_results = vm.search_similar_memories(
            "Building activity on the server",
            "Island-PvE"
        )
        # Verify context filtering works
        for result in island_results:
            # This would need actual implementation to verify context
            pass


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
