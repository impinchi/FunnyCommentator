from src.ollama_manager import OllamaManager
from src.config import Config

config = Config()

print("=== Testing Reasoning Modes ===")

# Test with reasoning OFF
om_off = OllamaManager(
    config.ollama_url, config.ollama_model, config.ollama_start_cmd, 
    config.ai_timeout_seconds, startup_timeout=config.ollama_startup_timeout,
    input_token_size=config.input_token_size, enable_reasoning=False,
    min_output_tokens=64, max_output_tokens=8096, safety_buffer=48,
    tokenizer_model='gpt-3.5-turbo'
)

result_off = om_off.get_funny_summary(['Player joined'], 'You are an ARK commentator. Be brief:')
print(f"Reasoning OFF - Length: {len(result_off)} chars")
print(f"Has thinking: {'<think>' in result_off}")
print(f"Preview: {result_off[:100]}...")

print("\n" + "="*50 + "\n")

# Test with reasoning ON  
om_on = OllamaManager(
    config.ollama_url, config.ollama_model, config.ollama_start_cmd,
    config.ai_timeout_seconds, startup_timeout=config.ollama_startup_timeout, 
    input_token_size=config.input_token_size, enable_reasoning=True,
    min_output_tokens=64, max_output_tokens=8096, safety_buffer=48,
    tokenizer_model='gpt-3.5-turbo'
)

result_on = om_on.get_funny_summary(['Player joined'], 'You are an ARK commentator. Be brief:')
print(f"Reasoning ON - Length: {len(result_on)} chars") 
print(f"Has thinking: {'<think>' in result_on}")
print(f"Preview: {result_on[:200]}...")
