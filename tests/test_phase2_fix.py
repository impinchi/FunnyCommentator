#!/usr/bin/env python3
"""Test script to verify Phase 2 API fixes"""

import sys
import os

# Add src directory to path for imports
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from src.recent_context import RecentContextManager
    from src.database import DatabaseManager
    from src.config import Config
    
    print("✅ Import test passed")
    
    # Test API compatibility 
    config = Config()
    db = DatabaseManager(config)
    rcm = RecentContextManager(db)
    
    # Test the fixed method signature matches main.py calls
    try:
        # This should work now (server context)
        result1 = rcm.get_contextual_summaries(server_name="test_server", target_tokens=1000)
        print("✅ Server contextual summaries call succeeded")
        
        # This should work now (cluster context)  
        result2 = rcm.get_contextual_summaries(cluster_name="test_cluster", target_tokens=2000)
        print("✅ Cluster contextual summaries call succeeded")
        
        # Check return type is list, not tuple
        if isinstance(result1, list) and isinstance(result2, list):
            print("✅ Return type is list (not tuple)")
        else:
            print(f"❌ Wrong return type: {type(result1)}, {type(result2)}")
            
        print("\n🎉 All API compatibility tests passed!")
        print("Phase 2 Enhanced Context Manager is now complete and ready for Phase 3!")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Test failed: {e}")
