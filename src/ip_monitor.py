"""IP monitoring module.

This module handles external IP address monitoring and change detection.
Following PEP 257 for docstring conventions.
"""
import os
import json
import logging
import asyncio
import requests
from typing import Optional

class IPMonitor:
    """Monitor for external IP address changes."""
    
    def __init__(self, retry_seconds: int, previous_ip: Optional[str] = None):
        """Initialize IP monitor with configuration.
        
        Args:
            retry_seconds: Seconds to wait between IP checks
            previous_ip: Last known IP address
        """
        self.retry_seconds = retry_seconds
        self.previous_ip = previous_ip
    
    async def check_ip(self) -> Optional[str]:
        """Check current external IP address.
        
        Returns:
            Current IP address if successful, None otherwise
        """
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=10)
            return response.json()["ip"]
        except Exception as e:
            logging.error(f"Error checking IP: {e}")
            return None
    
    async def monitor(self, callback, stop_event: asyncio.Event) -> None:
        """Monitor IP address for changes and notify via callback.
        
        Args:
            callback: Async function to call with new IP
            stop_event: Event to signal monitoring should stop
        """
        servers_file = os.getenv("SERVERS_CONFIG", "servers.json")
        
        while not stop_event.is_set():
            current_ip = await self.check_ip()
            
            if current_ip and current_ip != self.previous_ip:
                self.previous_ip = current_ip
                
                # Update IP in the config file
                try:
                    with open(servers_file, 'r') as f:
                        config = json.load(f)
                    
                    if 'ip_monitor' not in config:
                        config['ip_monitor'] = {}
                    
                    config['ip_monitor']['last_known_ip'] = current_ip
                    
                    with open(servers_file, 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    await callback(current_ip)
                    logging.info(f"Updated last known IP in config file: {current_ip}")
                except Exception as e:
                    logging.error(f"Failed to update IP in config file: {e}")
                
            wait_task = asyncio.create_task(stop_event.wait())
            try:
                await asyncio.wait_for(wait_task, timeout=self.retry_seconds)
            except asyncio.TimeoutError:
                pass  # Expected timeout, continue monitoring
            finally:
                wait_task.cancel()
