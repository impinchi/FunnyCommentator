#!/usr/bin/env python3

import requests
import json
import sys

def test_ollama_direct():
    """Test Ollama directly with a simple prompt"""
    
    url = "http://localhost:11434/api/generate"
    
    # Simple test prompt that encourages a final answer
    test_prompt = """You are a witty, sarcastic commentator for ARK Survival Evolved server events. 

Recent events: impinchi joined and left the server multiple times today.

Please provide a funny, sarcastic comment about this behavior. Make it entertaining and roast the player for their indecisiveness. End with a clear final comment."""
    
    payload = {
        "model": "deepseek-r1:8b",
        "prompt": test_prompt,
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "num_predict": 200,
            "temperature": 0.8
        }
    }
    
    print(f"Testing Ollama with prompt: {test_prompt}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Raw response: {repr(data.get('response', 'MISSING'))}")
            print(f"Response length: {len(data.get('response', ''))}")
            print(f"Done: {data.get('done', 'MISSING')}")
            print(f"Done reason: {data.get('done_reason', 'MISSING')}")
            
            if data.get('response'):
                print(f"Actual response text: {data['response']}")
            else:
                print("WARNING: Empty response from model!")
                
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ollama_direct()
