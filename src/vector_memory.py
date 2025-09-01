"""Vector-based semantic memory system for FunnyCommentator.

This module provides semantic memory capabilities using vector embeddings
to store and retrieve contextually relevant past AI responses.
Following PEP 257 for docstring conventions.
"""
import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import sqlite3


class VectorMemoryManager:
    """Manages semantic memory using vector embeddings and similarity search.
    
    This class provides an optional advanced memory system that can understand
    contextual relationships between events across time.
    """
    
    def __init__(self, config):
        """Initialize the vector memory manager.
        
        Args:
            config: Configuration object with semantic memory settings
        """
        self.config = config
        self.enabled = config.semantic_memory_enabled
        
        # Initialize storage path - use database path from config with V_ prefix
        config_db_path = Path(config.db_path)
        memory_db_name = f"V_{config_db_path.name}"
        self.memory_db_path = config_db_path.parent / memory_db_name
        
        if not self.enabled:
            logging.info("Semantic memory is disabled - using simple context mode")
            return
            
        self.embedding_model = config.embedding_model
        self.max_memories = config.max_memories_per_search
        self.relevance_threshold = config.memory_relevance_threshold
        
        self._init_database()
        
        # Initialize embedding system
        self.embedding_function = None
        self._init_embeddings()
        
        logging.info(f"Semantic memory initialized - Model: {self.embedding_model}")
    
    def _init_database(self):
        """Initialize the semantic memory database."""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            # Create memories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    server_name TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    original_logs TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            ''')
            
            # Create index for faster searches
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_server_timestamp 
                ON memories(server_name, timestamp)
            ''')
            
            conn.commit()
            conn.close()
            
            logging.debug("Semantic memory database initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize semantic memory database: {e}")
            self.enabled = False
    
    def _init_embeddings(self):
        """Initialize the embedding system."""
        if not self.enabled:
            return
            
        try:
            if self.config.embedding_provider == "local":
                # Use sentence-transformers for local embeddings
                from sentence_transformers import SentenceTransformer
                self.embedding_function = SentenceTransformer(self.embedding_model)
                logging.info(f"Loaded local embedding model: {self.embedding_model}")
                
            elif self.config.embedding_provider == "openai":
                # Future: OpenAI embeddings support
                logging.warning("OpenAI embeddings not yet implemented, falling back to local")
                self.enabled = False
                
            else:
                logging.error(f"Unknown embedding provider: {self.config.embedding_provider}")
                self.enabled = False
                
        except ImportError as e:
            logging.warning(f"sentence-transformers not available: {e}")
            logging.info("To enable semantic memory, install: pip install sentence-transformers")
            self.enabled = False
        except Exception as e:
            logging.error(f"Failed to initialize embedding system: {e}")
            self.enabled = False
    
    def _create_embedding(self, text: str) -> Optional[List[float]]:
        """Create an embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not self.enabled or not self.embedding_function:
            logging.debug("Embedding creation skipped - system disabled or not initialized")
            return None
            
        try:
            # Log the text being embedded (truncated for readability)
            text_preview = text[:200] + "..." if len(text) > 200 else text
            logging.debug(f"Creating embedding for text ({len(text)} chars): {text_preview}")
            
            # Create the embedding using the sentence transformer model
            embedding = self.embedding_function.encode(text)
            embedding_list = embedding.tolist()
            
            # Log embedding statistics
            import numpy as np
            embedding_array = np.array(embedding_list)
            logging.debug(f"Embedding created successfully:")
            logging.debug(f"  Dimensions: {len(embedding_list)}")
            logging.debug(f"  Mean value: {np.mean(embedding_array):.6f}")
            logging.debug(f"  Std deviation: {np.std(embedding_array):.6f}")
            logging.debug(f"  Min value: {np.min(embedding_array):.6f}")
            logging.debug(f"  Max value: {np.max(embedding_array):.6f}")
            logging.debug(f"  Vector magnitude: {np.linalg.norm(embedding_array):.6f}")
            
            return embedding_list
            
        except Exception as e:
            logging.error(f"Failed to create embedding: {e}")
            return None
    
    def store_memory(self, server_name: str, response_text: str, original_logs: List[str], 
                    metadata: Optional[Dict] = None) -> bool:
        """Store a new memory in the vector database.
        
        Args:
            server_name: Name of the server
            response_text: The AI's response text
            original_logs: The original log lines that prompted the response
            metadata: Additional metadata about the response
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            # Create combined text for embedding (response + context)
            logs_text = "\n".join(original_logs)
            combined_text = f"Response: {response_text}\n\nContext: {logs_text}"
            
            # Generate embedding
            embedding = self._create_embedding(combined_text)
            if embedding is None:
                return False
            
            # Create unique ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.md5(combined_text.encode()).hexdigest()[:8]
            memory_id = f"{server_name}_{timestamp}_{content_hash}"
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata.update({
                "server": server_name,
                "timestamp": timestamp,
                "log_count": len(original_logs)
            })
            
            # Store in database
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO memories 
                (id, server_name, response_text, original_logs, embedding, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id,
                server_name,
                response_text,
                logs_text,
                json.dumps(embedding),  # Store as JSON string
                timestamp,
                json.dumps(metadata)
            ))
            
            conn.commit()
            conn.close()
            
            logging.debug(f"Stored semantic memory for {server_name}: {memory_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store semantic memory: {e}")
            return False
    
    def search_similar_memories(self, current_logs: List[str], server_name: str) -> List[str]:
        """Search for semantically similar past memories.
        
        Args:
            current_logs: Current log lines to find similar memories for
            server_name: Name of the server to search within
            
        Returns:
            List of relevant past response texts
        """
        if not self.enabled:
            logging.debug(f"Vector memory disabled - no search performed for {server_name}")
            return []
            
        try:
            # Create embedding for current logs
            current_text = "\n".join(current_logs)
            logging.debug(f"Creating embedding for {len(current_text)} chars of current log text for {server_name}")
            current_embedding = self._create_embedding(current_text)
            if current_embedding is None:
                logging.warning(f"Failed to create embedding for current logs for {server_name}")
                return []
            
            logging.debug(f"Successfully created embedding with {len(current_embedding)} dimensions for {server_name}")
            
            # Get all memories for this server
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT response_text, embedding, timestamp 
                FROM memories 
                WHERE server_name = ? 
                ORDER BY timestamp DESC
            ''', (server_name,))
            
            memories = cursor.fetchall()
            conn.close()
            
            if not memories:
                logging.debug(f"No memories found in database for server {server_name}")
                return []
            
            logging.debug(f"Retrieved {len(memories)} stored memories from database for {server_name}")
            
            # Calculate similarities
            similar_memories = []
            processed_count = 0
            similarity_scores = []
            
            for response_text, embedding_json, timestamp in memories:
                try:
                    stored_embedding = json.loads(embedding_json)
                    similarity = self._cosine_similarity(current_embedding, stored_embedding)
                    similarity_scores.append(similarity)
                    processed_count += 1
                    
                    logging.debug(f"Memory {processed_count}: similarity={similarity:.4f}, threshold={self.relevance_threshold}")
                    
                    if similarity >= self.relevance_threshold:
                        similar_memories.append({
                            "response": response_text,
                            "similarity": similarity,
                            "timestamp": timestamp
                        })
                        logging.debug(f"Memory {processed_count} ACCEPTED (similarity {similarity:.4f} >= threshold {self.relevance_threshold})")
                        logging.debug(f"Memory content preview: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
                    else:
                        logging.debug(f"Memory {processed_count} rejected (similarity {similarity:.4f} < threshold {self.relevance_threshold})")
                        
                except Exception as e:
                    logging.warning(f"Failed to process memory embedding {processed_count}: {e}")
                    continue
            
            # Log similarity statistics
            if similarity_scores:
                avg_similarity = sum(similarity_scores) / len(similarity_scores)
                max_similarity = max(similarity_scores)
                min_similarity = min(similarity_scores)
                logging.debug(f"Similarity stats for {server_name}: avg={avg_similarity:.4f}, max={max_similarity:.4f}, min={min_similarity:.4f}")
            
            # Sort by similarity and return top results
            similar_memories.sort(key=lambda x: x["similarity"], reverse=True)
            top_memories = similar_memories[:self.max_memories]
            
            result = [memory["response"] for memory in top_memories]
            
            logging.info(f"Vector search for {server_name}: {len(result)} similar memories found from {len(memories)} total memories (threshold: {self.relevance_threshold})")
            if result:
                for i, memory in enumerate(top_memories, 1):
                    logging.debug(f"Selected memory {i}: similarity={memory['similarity']:.4f}, timestamp={memory['timestamp']}")
                    logging.debug(f"Memory {i} content: {memory['response'][:150]}{'...' if len(memory['response']) > 150 else ''}")
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to search semantic memories for {server_name}: {e}")
            return []
    
    def explain_similarity_calculation(self, text1: str, text2: str) -> Dict[str, Any]:
        """Explain how similarity is calculated between two texts (for debugging).
        
        Args:
            text1: First text to compare
            text2: Second text to compare
            
        Returns:
            Dictionary with detailed similarity calculation explanation
        """
        if not self.enabled:
            return {"error": "Vector memory system is disabled"}
            
        try:
            # Create embeddings for both texts
            embedding1 = self._create_embedding(text1)
            embedding2 = self._create_embedding(text2)
            
            if embedding1 is None or embedding2 is None:
                return {"error": "Failed to create embeddings"}
            
            import numpy as np
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate similarity components
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            similarity = dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
            
            return {
                "text1_preview": text1[:100] + "..." if len(text1) > 100 else text1,
                "text2_preview": text2[:100] + "..." if len(text2) > 100 else text2,
                "embedding_dimensions": len(embedding1),
                "vector1_magnitude": float(norm1),
                "vector2_magnitude": float(norm2),
                "dot_product": float(dot_product),
                "cosine_similarity": float(similarity),
                "similarity_interpretation": self._interpret_similarity(similarity),
                "passes_threshold": similarity >= self.relevance_threshold,
                "current_threshold": self.relevance_threshold
            }
            
        except Exception as e:
            return {"error": f"Similarity calculation failed: {e}"}
    
    def _interpret_similarity(self, similarity: float) -> str:
        """Interpret what a similarity score means.
        
        Args:
            similarity: Cosine similarity score
            
        Returns:
            Human-readable interpretation
        """
        if similarity >= 0.9:
            return "Nearly identical semantic meaning"
        elif similarity >= 0.8:
            return "Very high semantic similarity"
        elif similarity >= 0.7:
            return "High semantic similarity"
        elif similarity >= 0.6:
            return "Moderate semantic similarity"
        elif similarity >= 0.5:
            return "Some semantic similarity"
        elif similarity >= 0.3:
            return "Low semantic similarity"
        else:
            return "Very low or no semantic similarity"
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector (current log embedding)
            vec2: Second vector (stored memory embedding)
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        try:
            import numpy as np
            
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # Calculate dot product (measures how much the vectors point in the same direction)
            dot_product = np.dot(vec1, vec2)
            
            # Calculate norms (magnitudes) of each vector
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            # Log detailed similarity calculation for debugging
            logging.debug(f"Vector similarity calculation:")
            logging.debug(f"  Vector 1 dimensions: {len(vec1)}, magnitude: {norm1:.6f}")
            logging.debug(f"  Vector 2 dimensions: {len(vec2)}, magnitude: {norm2:.6f}")
            logging.debug(f"  Dot product: {dot_product:.6f}")
            
            if norm1 == 0 or norm2 == 0:
                logging.debug(f"  Zero vector detected - similarity: 0.0")
                return 0.0
            
            # Cosine similarity = dot_product / (norm1 * norm2)
            # This normalizes the similarity to be between -1 and 1
            # Since we're using text embeddings, we expect values between 0 and 1
            similarity = dot_product / (norm1 * norm2)
            
            logging.debug(f"  Final cosine similarity: {similarity:.6f}")
                
            return float(similarity)
            
        except ImportError:
            logging.warning("NumPy not available for similarity calculation")
            return 0.0
        except Exception as e:
            logging.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self.enabled:
            return {"enabled": False, "total_memories": 0}
            
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            # Total memories
            cursor.execute("SELECT COUNT(*) FROM memories")
            total_count = cursor.fetchone()[0]
            
            # Memories per server
            cursor.execute('''
                SELECT server_name, COUNT(*) 
                FROM memories 
                GROUP BY server_name
            ''')
            server_counts = dict(cursor.fetchall())
            
            # Database size
            db_size_mb = self.memory_db_path.stat().st_size / (1024 * 1024)
            
            conn.close()
            
            return {
                "enabled": True,
                "total_memories": total_count,
                "server_counts": server_counts,
                "database_size_mb": round(db_size_mb, 2),
                "embedding_model": self.embedding_model
            }
            
        except Exception as e:
            logging.error(f"Failed to get memory stats: {e}")
            return {"enabled": False, "error": str(e)}
    
    def cleanup_old_memories(self, days_to_keep: int = 90) -> int:
        """Clean up old memories to save space.
        
        Args:
            days_to_keep: Number of days of memories to keep
            
        Returns:
            Number of memories deleted
        """
        if not self.enabled:
            return 0
            
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_iso = cutoff_date.isoformat()
            
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM memories WHERE timestamp < ?", (cutoff_iso,))
            count_to_delete = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM memories WHERE timestamp < ?", (cutoff_iso,))
            conn.commit()
            conn.close()
            
            logging.info(f"Cleaned up {count_to_delete} old semantic memories")
            return count_to_delete
            
        except Exception as e:
            logging.error(f"Failed to cleanup old memories: {e}")
            return 0
