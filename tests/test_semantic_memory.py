"""Test semantic memory functionality."""
import logging
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.config import Config
from src.vector_memory import VectorMemoryManager

def test_semantic_memory():
    """Test the semantic memory system."""
    print("=== Testing Semantic Memory System ===\n")
    
    # Set up logging for test
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Load config
    config = Config()
    print(f"Semantic memory enabled in config: {config.semantic_memory_enabled}")
    print(f"Embedding model: {config.embedding_model}")
    print(f"Max memories per search: {config.max_memories_per_search}")
    print(f"Relevance threshold: {config.memory_relevance_threshold}")
    print()
    
    # Test VectorMemoryManager
    memory_manager = VectorMemoryManager(config)
    print(f"Memory manager initialized: {memory_manager.enabled}")
    
    if not memory_manager.enabled:
        print("\n❌ Semantic memory is disabled - check config and dependencies")
        
        # Check if dependencies are available
        try:
            import sentence_transformers
            print("✅ sentence-transformers is available")
        except ImportError:
            print("❌ sentence-transformers not installed")
            print("   Install with: pip install sentence-transformers")
        
        try:
            import numpy
            print("✅ numpy is available")
        except ImportError:
            print("❌ numpy not installed")
            print("   Install with: pip install numpy")
        
        return
    
    print("\n=== Testing Memory Storage ===")
    
    # Test storing memories
    test_logs = [
        "Player Bob joined the game",
        "Player Alice built a house",
        "Wild Rex attacked the base"
    ]
    
    test_response = "Welcome Bob! Alice is busy building while a Rex is causing trouble near the base."
    
    success = memory_manager.store_memory(
        "TestServer",
        test_response,
        test_logs,
        {"test": True}
    )
    
    print(f"Memory storage test: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n=== Testing Memory Search ===")
    
    # Test searching for similar memories
    search_logs = [
        "Player Charlie joined the game", 
        "New player entered the server"
    ]
    
    similar_memories = memory_manager.search_similar_memories(search_logs, "TestServer")
    
    print(f"Found {len(similar_memories)} similar memories")
    for i, memory in enumerate(similar_memories):
        print(f"  {i+1}. {memory[:100]}...")
    
    print("\n=== Memory Statistics ===")
    
    stats = memory_manager.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_semantic_memory()
