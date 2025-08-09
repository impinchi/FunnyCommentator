"""Test database module."""
import pytest
import sqlite3
import zlib
from src.database import DatabaseManager

@pytest.fixture
def db_manager(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.sqlite"
    return DatabaseManager(str(db_path))

def test_init_db(db_manager):
    """Test database initialization."""
    # Connect to the database and check if the table exists
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='summaries'
        """)
        assert cursor.fetchone() is not None

def test_save_and_retrieve_summary(db_manager):
    """Test saving and retrieving summaries."""
    test_summary = "Test summary"
    db_manager.save_summary(test_summary)
    
    summaries = db_manager.get_summaries_up_to_token_limit(1000)
    assert len(summaries) == 1
    assert summaries[0] == test_summary

def test_token_count():
    """Test token counting functionality."""
    text = "Hello, world!"
    token_count = DatabaseManager.count_tokens(text)
    assert token_count > 0

def test_token_limit_enforcement(db_manager):
    """Test that token limits are enforced when retrieving summaries."""
    summaries = [
        "First summary with some tokens",
        "Second summary with more tokens",
        "Third summary with even more tokens"
    ]
    
    for summary in summaries:
        db_manager.save_summary(summary)
    
    # Set a very low token limit to test enforcement
    retrieved = db_manager.get_summaries_up_to_token_limit(10)
    assert len(retrieved) < len(summaries)
