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
                 startup_timeout: int = 300, input_token_size: int = 64000,
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
        """Calculate num_predict based on available context space.
        
        Uses the available space after prompt and safety buffer, capped by max_output_tokens.
        This ensures we never request more tokens than the context window can handle.
        
        Args:
            prompt: The full prompt text that will be sent
            
        Returns:
            Number of tokens to allocate for generation (num_predict)
        """
        prompt_tokens = self._estimate_prompt_tokens(prompt)
        
        # Calculate available space: total context - prompt - safety buffer
        available_space = self.input_token_size - prompt_tokens - self.safety_buffer
        
        # Use available space but cap at max_output_tokens
        result = min(available_space, self.max_output_tokens)
        
        # Ensure we have at least some reasonable minimum
        if result < self.min_output_tokens:
            logging.warning(f"Very limited output space: {result} tokens available, "
                          f"prompt={prompt_tokens}, ctx={self.input_token_size}")
            result = max(result, 100)  # At least 100 tokens or available space
        
        logging.debug(f"Token allocation: prompt={prompt_tokens}, "
                     f"ctx={self.input_token_size}, buffer={self.safety_buffer}, "
                     f"available={available_space}, num_predict={result}")
        
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
                    "options": {}  # Minimal options for startup check
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
                            "options": {}  # Minimal options for startup check
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
            logging.debug("No log lines provided to get_funny_summary")
            return "No new events in the last day!"

        try:
            logging.info(f"Starting AI summary generation for {len(log_lines)} log lines")
            logging.debug(f"Using Ollama model: {self.model} with context window limited to {self.input_token_size} tokens")
            
            # Create final prompt with events at the end for optimal ordering
            if log_lines:
                events_section = (
                    "\n=== CURRENT EVENTS TO SUMMARIZE ===\n" + 
                    "\n".join(log_lines) + 
                    "\n=== END OF CURRENT EVENTS ===\n" + 
                    "\nIMPORTANT: Focus your commentary on the CURRENT EVENTS above. Use any historical context only to avoid repetition, not as the main topic. And stop repeating the phrase 'but hey'."
                )
                full_prompt = context + events_section
            else:
                full_prompt = context
                
            prompt_tokens = self._estimate_prompt_tokens(full_prompt)
            num_predict = self._compute_num_predict(full_prompt)
            
            logging.debug(f"Prompt tokens: {prompt_tokens}, Max output tokens: {num_predict}")
            
            # Minimal options - let the model manage its own token allocation
            options = {
                # Only set essential parameters for DeepSeek-R1
                "temperature": 0.6,        # DeepSeek-R1 default
                "top_p": 0.95,            # DeepSeek-R1 default (instead of tfs_z)
                "repeat_penalty": 1.1,     # Gentler penalty for DeepSeek-R1
            }
            
            # Add thinking mode if enabled in config
            if self.enable_reasoning:
                options["reasoning"] = True
                logging.debug(f"Enabled reasoning mode for model: {self.model}")
            else:
                logging.debug(f"Reasoning mode disabled for model: {self.model}")
            
            logging.info(f"Sending request to Ollama API at {self.url}")
            logging.debug(f"Request options: {options}")
            
            # Prepare the request payload
            request_payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": options
            }
            
            # Log the full request details for debugging
            logging.debug(f"Full request payload: model={request_payload['model']}, "
                         f"stream={request_payload['stream']}, "
                         f"prompt_length={len(request_payload['prompt'])} chars")
            # logging.debug(f"Prompt preview (first 200 chars): {repr(full_prompt[:200])}")
            logging.debug(f"Prompt : {repr(full_prompt)}")
            logging.debug(f"Request payload options: {request_payload['options']}")
            
            response = self.session.post(
                self.url,
                json=request_payload,
                timeout=self.timeout
            )
            
            logging.debug(f"Ollama API response status: {response.status_code}")
            response.raise_for_status()
            raw_json = response.json()
            logging.debug(f"Full Ollama response JSON keys: {list(raw_json.keys())}")
            logging.debug(f"Raw response field: {repr(raw_json.get('response', 'MISSING'))}")
            
            # Critical diagnostic information
            logging.debug(f"Response done: {raw_json.get('done', 'MISSING')}")
            logging.debug(f"Response done_reason: {repr(raw_json.get('done_reason', 'MISSING'))}")
            logging.debug(f"Prompt eval count: {raw_json.get('prompt_eval_count', 'MISSING')}")
            logging.debug(f"Eval count (output tokens): {raw_json.get('eval_count', 'MISSING')}")
            logging.debug(f"Total duration: {raw_json.get('total_duration', 'MISSING')} ns")
            
            raw_response = raw_json["response"].strip()
            
            # # Handle DeepSeek-R1 thinking tokens - extract content after </think>
            # if "<think>" in raw_response and "</think>" in raw_response:
            #     logging.debug("Detected thinking tokens in response, extracting final answer")
            #     # Find the end of the thinking section
            #     think_end = raw_response.find("</think>")
            #     if think_end != -1:
            #         # Extract everything after </think>
            #         final_response = raw_response[think_end + len("</think>"):].strip()
            #         logging.debug(f"Extracted final response after thinking: {repr(final_response[:100])}")
            #         raw_response = final_response
            
            logging.info(f"Successfully generated AI summary - Response length: {len(raw_response)} chars")
            logging.debug(f"AI Response preview: {raw_response[:200]}{'...' if len(raw_response) > 200 else ''}")
            
            return raw_response
            
        except Exception as e:
            logging.error(f"Ollama API error during summary generation: {e}")
            logging.debug(f"Failed prompt preview: {full_prompt[:500] if 'full_prompt' in locals() else 'N/A'}")
            return f"[AI Error: {e}]"