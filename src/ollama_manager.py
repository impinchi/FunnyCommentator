"""Ollama AI integration module.

This module handles all AI-related operations including starting/stopping the Ollama
server and generating summaries. Uses configurable context window size (num_ctx) to
limit memory usage while allowing large models to run on constrained hardware.
Following PEP 257 for docstring conventions.
"""
import logging
import subprocess
import requests
from typing import List
import time
import tiktoken

class OllamaManager:
    def __init__(self, url: str, model: str, start_cmd: str, timeout: int, 
                 startup_timeout: int = 300, input_token_size: int = 4096,
                 min_output_tokens: int = 64, max_output_tokens: int = 512,
                 safety_buffer: int = 48, tokenizer_model: str = "gpt-3.5-turbo",
                 enable_reasoning: bool = False):
        self.url = url
        self.model = model
        self.start_cmd = start_cmd
        self.timeout = timeout
        self.startup_timeout = startup_timeout
        self.input_token_size = input_token_size 
        self.min_output_tokens = min_output_tokens
        self.max_output_tokens = max_output_tokens
        self.safety_buffer = safety_buffer
        self.tokenizer_model = tokenizer_model
        self.enable_reasoning = enable_reasoning
        self._shutdown_requested = False
        
        # Initialize tiktoken encoder
        try:
            self.tokenizer = tiktoken.encoding_for_model(tokenizer_model)
            logging.info(f"Using tiktoken with model '{tokenizer_model}' for token counting")
        except Exception as e:
            logging.warning(f"Failed to load tiktoken for model '{tokenizer_model}': {e}")
            logging.info("Falling back to character-based token estimation")
            self.tokenizer = None
        
        logging.info(f"OllamaManager initialized model='{model}' ctx={input_token_size} "
                     f"out∈[{min_output_tokens},{max_output_tokens}] buffer={safety_buffer}")
        
        # Create persistent session for connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1,
            pool_maxsize=1,
            pool_block=False,
            max_retries=0
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def _estimate_prompt_tokens(self, text: str) -> int:
        """Accurate token count using tiktoken or fallback to character estimation.
        
        Uses tiktoken encoder for precise token counting when available,
        falls back to simple heuristic if tiktoken fails to load.
        
        Args:
            text: The prompt text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        if not text:
            return 0
            
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logging.warning(f"Tiktoken encoding failed: {e}, falling back to character estimation")
                
        # Fallback: conservative estimate of ~4 characters per token
        return max(1, len(text) // 4)

    def _compute_num_predict(self, prompt: str) -> int:
        """Calculate optimal num_predict based on available context space.
        
        Uses dynamic leftover approach: allocate remaining context window space
        to output generation while respecting min/max bounds and safety buffer.
        
        Args:
            prompt: The full prompt text that will be sent
            
        Returns:
            Number of tokens to allocate for generation (num_predict)
        """
        prompt_tokens = self._estimate_prompt_tokens(prompt)
        
        # Calculate remaining capacity after prompt and safety buffer
        remaining = self.input_token_size - prompt_tokens - self.safety_buffer
        
        if remaining < self.min_output_tokens:
            # Fallback: use minimum but never exceed a reasonable fraction of context
            candidate = max(8, min(self.min_output_tokens, self.input_token_size // 8))
            logging.warning(f"Limited context space: prompt={prompt_tokens}, "
                          f"remaining={remaining}, using fallback={candidate}")
        else:
            # Normal case: use remaining space up to max_output_tokens
            candidate = min(remaining, self.max_output_tokens)
            
        # Ensure we never go below absolute minimum
        result = max(self.min_output_tokens, candidate)
        
        logging.debug(f"Token allocation: prompt={prompt_tokens}, "
                     f"ctx={self.input_token_size}, buffer={self.safety_buffer}, "
                     f"num_predict={result}")
        
        return result

    def ensure_server_running(self, initial_prompt: str) -> bool:
        """Ensure Ollama server is running and start if needed."""
        self._shutdown_requested = False
        
        try:
            # First try to connect to existing server
            resp = self.session.post(
                self.url,
                json={
                    "model": self.model, 
                    "prompt": initial_prompt, 
                    "stream": False,
                    "options": {
                        "num_ctx": self.input_token_size,
                        "num_predict": self._compute_num_predict(initial_prompt)
                    }
                },
                timeout=self.startup_timeout
            )
            if resp.status_code == 200:
                logging.info("Ollama AI server is already running.")
                return True
            else:
                logging.warning(f"Ollama server responded with status {resp.status_code}: {resp.text}")
        except Exception as e:
            logging.info(f"Ollama AI server not running or not responding: {e}")

        # Start Ollama as a subprocess if not running
        try:
            logging.info("Starting Ollama AI server...")
            subprocess.Popen(
                self.start_cmd, 
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Wait for server to become available
            start_time = time.time()
            while time.time() - start_time < self.startup_timeout:
                if self._shutdown_requested:
                    logging.info("Startup cancelled - shutdown requested")
                    return False
                    
                try:
                    resp = self.session.post(
                        self.url,
                        json={
                            "model": self.model, 
                            "prompt": initial_prompt, 
                            "stream": False,
                            "options": {
                                "num_ctx": self.input_token_size,
                                "num_predict": self._compute_num_predict(initial_prompt)
                            }
                        },
                        timeout=self.startup_timeout/2
                    )
                    if resp.status_code == 200:
                        logging.info("Ollama AI server started successfully.")
                        return True
                    else:
                        logging.warning(f"Ollama startup check failed - HTTP {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    logging.warning(f"Ollama startup check error: {e}")
                    time.sleep(2)
                    continue
                    
            logging.error("Failed to start Ollama AI server within timeout.")
            return False
            
        except Exception as e:
            logging.error(f"Failed to start Ollama AI server: {e}")
            return False

    def stop_server(self):
        """Stop the Ollama server."""
        self._shutdown_requested = True
        
        try:
            # First try to stop the model gracefully
            subprocess.run(
                f'ollama stop {self.model}',
                shell=True,
                check=False,
                capture_output=True,
                text=True
            )
            logging.info(f"Ollama model {self.model} stopped successfully.")
            
            # Then forcefully terminate the process on Windows
            result = subprocess.run(
                'taskkill /F /IM ollama.exe',
                shell=True,
                check=False,
                capture_output=True,
                text=True
            )
            # Only log if there were actual processes to terminate
            if result.returncode == 0:
                logging.info("Ollama server terminated.")
            else:
                logging.debug("No Ollama processes found to terminate.")
            
        except Exception as e:
            logging.error(f"Error stopping Ollama: {e}")

    def get_funny_summary(self, log_lines: List[str], context: str) -> str:
        """Get a funny summary from Ollama API."""
        if not log_lines:
            return "No new events in the last day!"

        try:
            logging.debug(f"Using Ollama with context window limited to {self.input_token_size} tokens")
            full_prompt = context + "\n".join(log_lines)
            num_predict = self._compute_num_predict(full_prompt)
            
            # Enable thinking mode for supported models (like DeepSeek-R1)
            # This will be ignored by models that don't support it
            options = {
                "num_ctx": self.input_token_size,
                "num_predict": num_predict,
                "use_mmap": True,  # Memory optimization
                "num_thread": -1,  # Use all available threads
                "temperature": 0.8,        # Good creativity
                "tfs_z": 0.95,            # Remove unlikely tokens
                "repeat_penalty": 1.15,    # Avoid repetitive jokes
            }
            
            # Add thinking mode if enabled in config
            if self.enable_reasoning:
                options["reasoning"] = True
                logging.debug(f"Enabled reasoning mode for model: {self.model}")
            else:
                logging.debug(f"Reasoning mode disabled for model: {self.model}")
            
            response = self.session.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": options
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["response"].strip()
            
        except Exception as e:
            logging.error(f"Ollama API error: {e}")
            return f"[AI Error: {e}]"