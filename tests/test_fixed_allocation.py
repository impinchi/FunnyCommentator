#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ollama_manager import OllamaManager
import logging

# Set up logging to see the debug output
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_fixed_token_allocation():
    """Test the fixed token allocation logic"""
    
    # Create manager with the fixed config
    manager = OllamaManager(
        url="http://localhost:11434/api/generate",
        model="deepseek-r1:8b",
        start_cmd="ollama serve",
        timeout=60,
        startup_timeout=120,
        input_token_size=32000,  # Large context
        max_output_tokens=8000,  # Reasonable output
        min_output_tokens=64,
        safety_buffer=48,
        tokenizer_model="gpt-3.5-turbo",
        enable_reasoning=False   # Reasoning disabled for testing
    )
    
    # Test with a very large prompt that would previously trigger the fallback
    large_context = "This is a test context. " * 1000  # ~5000 characters
    test_prompt = f"""You are a witty commentator. {large_context}
    
Recent events:
2025.08.27_10.05.14: impinchi joined this ARK!
2025.08.27_10.05.46: impinchi left this ARK!

Please make a funny comment about this."""
    
    print(f"Testing token allocation with large prompt ({len(test_prompt)} chars)")
    
    # Test the _compute_num_predict method directly
    num_predict = manager._compute_num_predict(test_prompt)
    print(f"Computed num_predict: {num_predict}")
    
    if num_predict == 8000:  # Should be max_output_tokens
        print("SUCCESS: Fixed logic returns max_output_tokens instead of tiny fallback!")
    else:
        print(f"ISSUE: Expected 8000, got {num_predict}")
    
    # Test actual request (if ollama is running)
    try:
        print("\nTesting actual request...")
        log_lines = [
            "2025.08.27_10.05.14: impinchi joined this ARK!",
            "2025.08.27_10.05.46: impinchi left this ARK!"
        ]
        
        context = f"You are a witty commentator. {large_context}"
        
        result = manager.get_funny_summary(log_lines, context)
        print(f"Result length: {len(result)}")
        if result and len(result) > 100:  # Reasonable response length
            print("SUCCESS: Got a proper response!")
            print(f"Response preview: {result[:200]}...")
        else:
            print(f"Response: {repr(result)}")
            
    except Exception as e:
        print(f"Request failed (expected if ollama not running): {e}")

if __name__ == "__main__":
    test_fixed_token_allocation()
