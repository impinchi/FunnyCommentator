"""Ollama AI integration module.

This module handles all AI-related operations including starting/stopping the Ollama
server and generating summaries. Uses configurable context window size (num_ctx) to
limit memory usage while allowing large models to run on constrained hardware.
Following PEP 257 for docstring conventions.
"""
import logging
import subprocess
import requests
import sys
from typing import List
import time

class OllamaManager:
    def __init__(self, url: str, model: str, start_cmd: str, timeout: int, startup_timeout: int = 300, input_token_size: int = 4096):
        self.url = url
        self.model = model
        self.start_cmd = start_cmd
        self.timeout = timeout
        self.startup_timeout = startup_timeout
        self.input_token_size = input_token_size  # Store the token size limit
        self._shutdown_requested = False
        
        logging.info(f"OllamaManager initialized with model '{model}' and context window limited to {input_token_size} tokens")
        
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
                        "num_ctx": self.input_token_size
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
                                "num_ctx": self.input_token_size
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
            response = self.session.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": context + "\n".join(log_lines),
                    "stream": False,
                    "options": {
                        "num_ctx": self.input_token_size  # Use configured token size to limit memory
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["response"].strip()
            
        except Exception as e:
            logging.error(f"Ollama API error: {e}")
            return f"[AI Error: {e}]"