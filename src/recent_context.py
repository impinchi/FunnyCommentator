"""Enhanced context management for FunnyCommentator.

This module provides improved recent context handling with conversation threading,
metadata filtering, and temporal awareness for better AI response context.
Following PEP 257 for docstring conventions.
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path


class RecentContextManager:
    """Manages recent context with conversation threading and metadata filtering.
    
    This class provides enhanced context management beyond simple token limits,
    including conversation flow awareness and temporal context windows.
    """
    
    def __init__(self, database_manager):
        """Initialize the recent context manager.
        
        Args:
            database_manager: The main database manager instance
        """
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        
    def get_conversation_thread(self, server_name: str, max_responses: int = 3) -> List[Dict[str, Any]]:
        """Get the most recent responses to maintain conversation flow.
        
        Args:
            server_name: Name of the server to get conversation for
            max_responses: Maximum number of recent responses to include
            
        Returns:
            List of dictionaries with response data and metadata
        """
        if server_name not in self.db.server_tables:
            return []
            
        table_name = self.db.server_tables[server_name]
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                # Get recent responses with timestamps if available
                cursor = conn.execute(f"""
                    SELECT id, summary, created_at 
                    FROM {table_name} 
                    ORDER BY id DESC 
                    LIMIT ?
                """, (max_responses,))
                
                results = []
                for row in cursor.fetchall():
                    summary = self.db._decompress_text(row[1])
                    results.append({
                        "id": row[0],
                        "response": summary,
                        "timestamp": row[2],
                        "type": "server_response"
                    })
                
                # Reverse to get chronological order (oldest first)
                results.reverse()
                
                logging.debug(f"Retrieved {len(results)} conversation thread items for {server_name}")
                return results
                
        except Exception as e:
            self.logger.warning(f"Failed to get conversation thread for {server_name}: {e}")
            return []
    
    def get_cluster_conversation_thread(self, cluster_name: str, max_responses: int = 3) -> List[Dict[str, Any]]:
        """Get recent cluster responses for conversation flow.
        
        Args:
            cluster_name: Name of the cluster to get conversation for
            max_responses: Maximum number of recent responses to include
            
        Returns:
            List of dictionaries with response data and metadata
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, summary, timestamp 
                    FROM cluster_summaries 
                    WHERE cluster_name = ?
                    ORDER BY id DESC 
                    LIMIT ?
                """, (cluster_name, max_responses))
                
                results = []
                for row in cursor.fetchall():
                    summary = self.db._decompress_text(row[1])
                    results.append({
                        "id": row[0],
                        "response": summary,
                        "timestamp": row[2],
                        "type": "cluster_response"
                    })
                
                # Reverse to get chronological order (oldest first)
                results.reverse()
                
                logging.debug(f"Retrieved {len(results)} cluster conversation thread items for {cluster_name}")
                return results
                
        except Exception as e:
            self.logger.warning(f"Failed to get cluster conversation thread for {cluster_name}: {e}")
            return []
    
    def get_recent_summaries_by_timeframe(self, server_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get summaries from a specific time window.
        
        Args:
            server_name: Name of the server to get summaries for
            days: Number of days back to look for summaries
            
        Returns:
            List of summaries with metadata from the timeframe
        """
        if server_name not in self.db.server_tables:
            return []
            
        table_name = self.db.server_tables[server_name]
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff_date.isoformat()
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute(f"""
                    SELECT id, summary, created_at 
                    FROM {table_name} 
                    WHERE created_at >= ?
                    ORDER BY created_at ASC
                """, (cutoff_timestamp,))
                
                results = []
                for row in cursor.fetchall():
                    summary = self.db._decompress_text(row[1])
                    results.append({
                        "id": row[0],
                        "response": summary,
                        "timestamp": row[2],
                        "age_days": (datetime.now() - datetime.fromisoformat(row[2])).days,
                        "type": "server_response"
                    })
                
                logging.debug(f"Retrieved {len(results)} summaries from last {days} days for {server_name}")
                return results
                
        except Exception as e:
            logging.error(f"Failed to get recent summaries by timeframe for {server_name}: {e}")
            return []
    
    def get_contextual_summaries(self, server_name: str = None, cluster_name: str = None, 
                                target_tokens: int = None, token_limit: int = None,
                                include_conversation_flow: bool = True,
                                conversation_weight: float = 0.3) -> List[str]:
        """Get contextually aware summaries with conversation flow consideration.
        
        Args:
            server_name: Name of the server to get summaries for (optional)
            cluster_name: Name of the cluster to get summaries for (optional)
            target_tokens: Target token count for summaries (alias for token_limit)
            token_limit: Maximum tokens available for context
            include_conversation_flow: Whether to prioritize recent conversation
            conversation_weight: Fraction of tokens to reserve for conversation flow (0.0-1.0)
            
        Returns:
            List of contextual summary strings
        """
        # Handle parameter aliases and defaults
        effective_token_limit = target_tokens or token_limit or 4000
        target_identifier = server_name or cluster_name
        is_cluster = cluster_name is not None
        
        if not target_identifier:
            self.logger.warning("No server_name or cluster_name provided for contextual summaries")
            return []
            
        if not include_conversation_flow:
            # Fall back to standard token-limited summaries
            if is_cluster:
                summaries = self.db.get_cluster_summaries_up_to_token_limit(target_identifier, effective_token_limit)
            else:
                summaries = self.db.get_summaries_up_to_token_limit(target_identifier, effective_token_limit)
            return summaries
        
        # Split token budget between conversation flow and historical context
        conversation_tokens = int(effective_token_limit * conversation_weight)
        historical_tokens = effective_token_limit - conversation_tokens
        
        # Get conversation thread (recent responses) - use appropriate method for server/cluster
        if is_cluster:
            conversation_thread = self.get_cluster_conversation_thread(target_identifier, max_responses=5)
        else:
            conversation_thread = self.get_conversation_thread(target_identifier, max_responses=5)
        
        conversation_summaries = []
        conversation_token_count = 0
        
        for item in reversed(conversation_thread):  # Most recent first for token counting
            response = item["response"]
            tokens = self.db.count_tokens(response)
            
            if conversation_token_count + tokens <= conversation_tokens:
                conversation_summaries.insert(0, response)  # Keep chronological order
                conversation_token_count += tokens
            else:
                break
        
        # Get additional historical context with remaining tokens - use appropriate method
        if is_cluster:
            historical_summaries = self.db.get_cluster_summaries_up_to_token_limit(target_identifier, historical_tokens)
        else:
            historical_summaries = self.db.get_summaries_up_to_token_limit(target_identifier, historical_tokens)
        
        # Remove any overlap between conversation and historical summaries
        historical_summaries = [s for s in historical_summaries if s not in conversation_summaries]
        
        # Combine: historical context first, then conversation flow
        all_summaries = historical_summaries + conversation_summaries
        
        return all_summaries
    
    def get_context_statistics(self, server_name: str) -> Dict[str, Any]:
        """Get statistics about available context for a server.
        
        Args:
            server_name: Name of the server to analyze
            
        Returns:
            Dictionary with context statistics
        """
        if server_name not in self.db.server_tables:
            return {"error": "Server not found"}
        
        table_name = self.db.server_tables[server_name]
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                # Total summaries
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_summaries = cursor.fetchone()[0]
                
                # Recent summaries (last 7 days)
                cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
                cursor = conn.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE created_at >= ?
                """, (cutoff_date,))
                recent_summaries = cursor.fetchone()[0]
                
                # Get date range
                cursor = conn.execute(f"""
                    SELECT MIN(created_at), MAX(created_at) FROM {table_name}
                """)
                date_range = cursor.fetchone()
                
                return {
                    "server_name": server_name,
                    "total_summaries": total_summaries,
                    "recent_summaries_7d": recent_summaries,
                    "earliest_summary": date_range[0],
                    "latest_summary": date_range[1],
                    "coverage_days": (datetime.now() - datetime.fromisoformat(date_range[0])).days if date_range[0] else 0
                }
                
        except Exception as e:
            logging.error(f"Failed to get context statistics for {server_name}: {e}")
            return {"error": str(e)}
    
    def _calculate_conversation_score(self, summary1: Dict[str, Any], summary2: Dict[str, Any]) -> float:
        """Calculate the conversation relationship score between two summaries.
        
        Args:
            summary1: First summary with timestamp, summary, server_name
            summary2: Second summary with timestamp, summary, server_name
            
        Returns:
            Float score between 0.0 and 1.0 indicating conversation relationship strength
        """
        try:
            # Base score starts at 0
            score = 0.0
            
            # Temporal proximity scoring (closer in time = higher score)
            time1 = summary1.get('timestamp', summary1.get('created_at'))
            time2 = summary2.get('timestamp', summary2.get('created_at'))
            
            if time1 and time2:
                # Parse timestamps if they're strings
                if isinstance(time1, str):
                    time1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
                if isinstance(time2, str):
                    time2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
                
                # Calculate time difference in minutes
                time_diff = abs((time1 - time2).total_seconds() / 60)
                
                # Temporal score: higher for closer times (exponential decay)
                if time_diff <= 5:  # Within 5 minutes
                    temporal_score = 1.0
                elif time_diff <= 15:  # Within 15 minutes
                    temporal_score = 0.8
                elif time_diff <= 60:  # Within 1 hour
                    temporal_score = 0.6
                elif time_diff <= 240:  # Within 4 hours
                    temporal_score = 0.3
                else:  # Older than 4 hours
                    temporal_score = 0.1
                
                score += temporal_score * 0.4  # 40% weight for temporal proximity
            
            # Server relationship scoring
            server1 = summary1.get('server_name', '')
            server2 = summary2.get('server_name', '')
            
            if server1 and server2:
                if server1 == server2:
                    score += 0.3  # 30% boost for same server
                else:
                    score += 0.1  # 10% boost for different servers (still related)
            
            # Content similarity scoring (basic keyword matching)
            text1 = summary1.get('summary', '').lower()
            text2 = summary2.get('summary', '').lower()
            
            if text1 and text2:
                # Extract keywords (simple approach)
                words1 = set(text1.split())
                words2 = set(text2.split())
                
                # Remove common words
                common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did'}
                words1 = words1 - common_words
                words2 = words2 - common_words
                
                # Calculate intersection
                if words1 and words2:
                    intersection = len(words1.intersection(words2))
                    union = len(words1.union(words2))
                    
                    if union > 0:
                        jaccard_similarity = intersection / union
                        score += jaccard_similarity * 0.3  # 30% weight for content similarity
                
                # Player name matching (indicates related activity)
                # Simple check for player names (capitalized words that might be names)
                potential_names1 = [word for word in text1.split() if word.isalpha() and word[0].isupper() and len(word) > 2]
                potential_names2 = [word for word in text2.split() if word.isalpha() and word[0].isupper() and len(word) > 2]
                
                common_names = set(potential_names1).intersection(set(potential_names2))
                if common_names:
                    score += len(common_names) * 0.1  # Boost for each common player name
            
            # Ensure score is between 0 and 1
            return min(max(score, 0.0), 1.0)
            
        except Exception as e:
            logging.warning(f"Error calculating conversation score: {e}")
            return 0.0
