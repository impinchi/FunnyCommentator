#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.main import Application

async def test_immediate():
    app = Application()
    
    # Process clusters immediately
    await app.process_server_logs()
    
    # Cleanup
    await app.cleanup()

if __name__ == "__main__":
    asyncio.run(test_immediate())
