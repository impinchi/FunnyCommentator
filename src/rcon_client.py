"""RCON client module.

This module handles all RCON-related operations including fetching game logs
and sanitizing them. Following PEP 257 for docstring conventions.
"""
import socket
import logging
import re
from typing import List
from rcon.source import Client
from contextlib import contextmanager

class RconClient:
    """RCON client for interacting with game servers."""
    
    def __init__(self, host: str, port: int, password: str, log_file_path: str = None):
        """Initialize RCON client with connection details.
        
        Args:
            host: The RCON server host
            port: The RCON server port
            password: The RCON server password
            log_file_path: Optional path to ARK log file for fallback
        """
        self.host = host
        self.port = port
        self.password = password
        self.log_file_path = log_file_path
    
    @contextmanager
    def _connect(self):
        """Context manager for RCON connection handling.
        
        Yields:
            An RCON client connection
        """
        # Use socket timeout like in the working old script
        socket.setdefaulttimeout(10)
        try:
            # Use the same pattern as the working old script - let the context manager handle connection
            with Client(self.host, self.port, passwd=self.password) as client:
                logging.debug(f"RCON connected to {self.host}:{self.port}")
                yield client
        except Exception as e:
            logging.error(f"RCON connection failed to {self.host}:{self.port}: {e}")
            raise
        finally:
            socket.setdefaulttimeout(None)
    
    @staticmethod
    def sanitize_log_line(line: str) -> str:
        """Sanitize a log line by removing control characters and limiting length.
        
        Args:
            line: The log line to sanitize
        
        Returns:
            Sanitized log line
        """
        # Remove control characters except newlines and tabs
        line = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]', '', line)
        # Strip excessive whitespace
        line = line.strip()
        # Limit length per line
        return line[:500]
    
    def fetch_logs(self) -> List[str]:
        """Fetch and sanitize logs from the RCON server or log file.
        
        Returns:
            List of sanitized log lines
        """
        # First try RCON
        rcon_logs = self._try_rcon_logs()
        if rcon_logs:
            return rcon_logs
        
        # Fallback to file-based log reading
        return self._try_file_logs()
    
    def _try_rcon_logs(self) -> List[str]:
        """Try to fetch logs via RCON using the same approach as the working old script."""
        logging.debug("Attempting RCON log fetch...")
        
        try:
            with self._connect() as rcon_client:
                logging.info("Connected to ARK RCON.")
                # Use the exact same command as the working old script
                logs = rcon_client.run("GetGameLog")
                logging.info("Closing connection to ARK RCON.")
                
                if not logs:
                    raise Exception("No data returned from GetGameLog command")
                
                lines = logs.splitlines()
                # Sanitize each line
                lines = [self.sanitize_log_line(line) for line in lines if line.strip()]
                logging.info(f"Successfully fetched {len(lines)} lines via RCON.")
                return lines
                
        except Exception as e:
            logging.warning(f"RCON log fetching failed: {e}")
            return []
    
    def _try_file_logs(self) -> List[str]:
        """Try to fetch logs from ARK log files."""
        # Try to get log file path from server config
        log_file_path = getattr(self, 'log_file_path', None)
        if not log_file_path:
            logging.warning("No log file path configured for file-based log reading")
            return []
        
        try:
            import os
            from datetime import datetime, timedelta
            
            if not os.path.exists(log_file_path):
                logging.warning(f"Log file not found: {log_file_path}")
                return []
            
            # Read the last part of the log file (last 1000 lines)
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Get recent lines (last 2 hours worth)
            recent_lines = []
            now = datetime.now()
            cutoff_time = now - timedelta(hours=2)
            
            # Take last 1000 lines and filter by time if possible
            for line in lines[-1000:]:
                sanitized = self.sanitize_log_line(line)
                if sanitized:
                    recent_lines.append(sanitized)
            
            logging.info(f"Successfully fetched {len(recent_lines)} lines from log file: {log_file_path}")
            return recent_lines
            
        except Exception as e:
            logging.error(f"File-based log reading failed: {e}")
            return []
