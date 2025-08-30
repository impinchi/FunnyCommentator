#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ollama_manager import OllamaManager
import logging

# Set up logging to see the debug output
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_ollama_manager():
    """Test our ollama_manager with reasoning disabled to see if it handles thinking tokens correctly"""
    
    # Create manager with reasoning disabled (like in the real config)
    manager = OllamaManager(
        model="deepseek-r1:8b",
        input_token_size=4096,
        max_output_tokens=200,
        min_output_tokens=64,
        safety_buffer=48,
        tokenizer_model="gpt-3.5-turbo",
        enable_reasoning=False,  # This should extract from thinking tokens
        timeout_seconds=60,
        startup_timeout_seconds=120,
        ollama_url="http://localhost:11434/api/generate"
    )
    
    # Simple test data
    log_lines = [
        "2025.08.27_10.05.14: impinchi joined this ARK!",
        "2025.08.27_10.05.46: impinchi left this ARK!",
        "2025.08.27_10.18.23: impinchi joined this ARK!",
        "2025.08.27_10.18.44: impinchi left this ARK!"
    ]
    
    context = """You are a witty, sarcastic commentator for ARK Survival Evolved. 
Make funny comments about player activities. Be entertaining and roast players for silly behavior.

Recent activity:
"""
    
    print("Testing ollama_manager with reasoning=False...")
    print(f"Input log lines: {len(log_lines)}")
    
    try:
        result = manager.get_funny_summary(log_lines, context)
        print(f"Result length: {len(result)}")
        print(f"Result: {repr(result)}")
        
        if result and len(result) > 0:
            print("SUCCESS: Got a non-empty response!")
            print(f"Response: {result}")
        else:
            print("FAILED: Still getting empty responses")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_ollama_manager()
