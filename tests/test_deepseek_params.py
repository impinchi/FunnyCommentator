#!/usr/bin/env python3
"""
Test DeepSeek-R1 with corrected parameters
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ollama_manager import OllamaManager

def test_deepseek_params():
    print("Testing DeepSeek-R1 with corrected parameters...")
    
    # Initialize with small context for quick test
    manager = OllamaManager(
        url="http://localhost:11434/api/generate",
        model="deepseek-r1:8b",
        start_cmd="ollama serve",
        timeout=300,              # 5 minute timeout
        input_token_size=2048,    # Smaller for quick test
        min_output_tokens=64,
        max_output_tokens=128,    # Much smaller for testing
        safety_buffer=48,
        enable_reasoning=False    # Reasoning disabled
    )
    
    # Simple test prompt
    test_prompt = """Write a short funny comment about ARK players who keep dying to raptors. 
    Keep it under 100 words and be sarcastic."""
    
    print(f"Prompt: {test_prompt}")
    print(f"Prompt length: {len(test_prompt)} chars")
    
    # Generate response
    print("\nTesting actual request...")
    result = manager.get_funny_summary(["Test log line"], test_prompt)
    
    print(f"\nResult length: {len(result)}")
    print(f"Response: {repr(result)}")
    
    return result

if __name__ == "__main__":
    result = test_deepseek_params()
