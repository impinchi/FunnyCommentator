"""Database operations module.

This module handles all database-related operations including initialization,
saving and retrieving summaries. Following PEP 257 for docstring conventions.
"""
import sqlite3
import zlib
from typing import List, Dict
import tiktoken

class DatabaseManager:
    """Database manager class for handling all database operations."""
    
    def __init__(self, db_path: str, server_tables: Dict[str, str]):
        """Initialize database manager with path to database file.
        
        Args:
            db_path: Path to the SQLite database file
            server_tables: Dictionary mapping server names to their table names
        """
        self.db_path = db_path
        self.server_tables = server_tables
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database with required tables for each server and clusters."""
        with sqlite3.connect(self.db_path) as conn:
            # Create tables for individual servers
            for table_name in self.server_tables.values():
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        summary BLOB
                    )
                """)
            
            # Create table for cluster summaries
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cluster_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cluster_name TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    summary BLOB
                )
            """)
    
    def save_summary(self, server_name: str, summary: str) -> None:
        """Save a compressed summary to the server's table.
        
        Args:
            server_name: Name of the server this summary is for
            summary: The summary text to save
        """
        table_name = self.server_tables[server_name]
        compressed = zlib.compress(summary.encode("utf-8"))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"INSERT INTO {table_name} (summary) VALUES (?)", (compressed,))
    
    @staticmethod
    def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            model: The model to use for tokenization
        
        Returns:
            Number of tokens in the text
        """
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    
    def get_summaries_up_to_token_limit(self, server_name: str, token_limit: int) -> List[str]:
        """Retrieve summaries from the server's table up to the token limit.
        
        Args:
            server_name: Name of the server to get summaries for
            token_limit: Maximum number of tokens to retrieve
        
        Returns:
            List of summaries within the token limit
        """
        table_name = self.server_tables[server_name]
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(f"SELECT summary FROM {table_name} ORDER BY id DESC")
            summaries = []
            total_tokens = 0
            
            for row in rows:
                summary = zlib.decompress(row[0]).decode("utf-8")
                tokens = self.count_tokens(summary)
                
                if total_tokens + tokens > token_limit:
                    break
                    
                summaries.insert(0, summary)  # Keep chronological order
                total_tokens += tokens
                
            return summaries
    
    def save_cluster_summary(self, cluster_name: str, summary: str) -> None:
        """Save a compressed summary for a cluster.
        
        Args:
            cluster_name: Name of the cluster this summary is for
            summary: The summary text to save
        """
        compressed = zlib.compress(summary.encode("utf-8"))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO cluster_summaries (cluster_name, summary) VALUES (?, ?)",
                (cluster_name, compressed)
            )

    def get_cluster_summaries_up_to_token_limit(self, cluster_name: str, token_limit: int) -> List[str]:
        """Retrieve cluster summaries up to the token limit.
        
        Args:
            cluster_name: Name of the cluster to get summaries for
            token_limit: Maximum number of tokens to retrieve
        
        Returns:
            List of cluster summaries within the token limit
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT summary FROM cluster_summaries WHERE cluster_name = ? ORDER BY id DESC",
                (cluster_name,)
            )
            summaries = []
            total_tokens = 0
            
            for row in rows:
                summary = zlib.decompress(row[0]).decode("utf-8")
                tokens = self.count_tokens(summary)
                
                if total_tokens + tokens > token_limit:
                    break
                    
                summaries.insert(0, summary)  # Keep chronological order
                total_tokens += tokens
                
            return summaries
            
    def close(self) -> None:
        """Close any open database connections.
        
        Note: SQLite connections are closed automatically after each transaction,
        but this method exists for consistency with other database interfaces.
        """
        pass  # Connections are managed by context managers
