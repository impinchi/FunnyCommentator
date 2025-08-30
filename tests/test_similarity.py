"""Test semantic memory similarity search."""
import logging
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.config import Config
from src.vector_memory import VectorMemoryManager

def test_similarity_search():
    """Test semantic memory similarity search with similar content."""
    print("=== Testing Semantic Memory Similarity Search ===\n")
    
    # Set up logging for test
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Load config and initialize memory manager
    config = Config()
    memory_manager = VectorMemoryManager(config)
    
    if not memory_manager.enabled:
        print("❌ Semantic memory is disabled")
        return
    
    print("=== Storing Test Memories ===")
    
    # Store several memories with different scenarios
    memories = [
        {
            "logs": ["Player Alice joined the server", "Welcome Alice to the island!"],
            "response": "A warm welcome to Alice who just arrived on our island adventure!"
        },
        {
            "logs": ["Player Bob disconnected", "Bob left the game"],  
            "response": "Farewell Bob! Hope to see you back on the island soon."
        },
        {
            "logs": ["Wild Triceratops destroyed wooden wall", "Base under attack!"],
            "response": "A massive Triceratops just demolished part of the base defenses!"
        },
        {
            "logs": ["Player Charlie tamed a Rex", "Congratulations on the new dino!"],
            "response": "Charlie has successfully tamed a fearsome Rex - what a beast!"
        }
    ]
    
    for i, memory in enumerate(memories):
        success = memory_manager.store_memory(
            "TestServer",
            memory["response"], 
            memory["logs"],
            {"scenario": f"test_{i+1}"}
        )
        print(f"Stored memory {i+1}: {'✅' if success else '❌'}")
    
    print(f"\n=== Testing Similarity Searches ===")
    
    # Test searches for similar scenarios
    test_searches = [
        {
            "name": "New Player Joining",
            "logs": ["Player David joined", "New player connected"]
        },
        {
            "name": "Player Leaving", 
            "logs": ["Player Sarah left the server", "Player disconnected"]
        },
        {
            "name": "Dino Attack",
            "logs": ["Wild Carnotaurus attacking base", "Carnivore spotted near walls"] 
        },
        {
            "name": "Taming Success",
            "logs": ["Player Mike tamed Spino", "New dinosaur tamed successfully"]
        }
    ]
    
    for search in test_searches:
        print(f"\n--- {search['name']} ---")
        similar_memories = memory_manager.search_similar_memories(search["logs"], "TestServer")
        
        print(f"Query: {' | '.join(search['logs'])}")
        print(f"Found {len(similar_memories)} similar memories:")
        
        for j, memory in enumerate(similar_memories):
            print(f"  {j+1}. {memory}")
    
    # Show final stats
    print(f"\n=== Final Statistics ===")
    stats = memory_manager.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_similarity_search()
