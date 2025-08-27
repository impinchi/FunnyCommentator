"""Log management module for FunnyCommentator.

This module handles log file cleanup, rotation, and retention policies.
Following PEP 257 for docstring conventions.
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List


class LogManager:
    """Manages log files including cleanup, rotation, and retention."""
    
    def __init__(self, logs_directory: str = "logs", retention_days: int = 30, max_size_mb: int = 100):
        """Initialize the log manager.
        
        Args:
            logs_directory: Directory containing log files
            retention_days: Number of days to keep old log files
            max_size_mb: Maximum size in MB before rotating logs
        """
        self.logs_dir = Path(logs_directory)
        self.retention_days = retention_days
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
        
        # Define log files managed by this system
        self.managed_log_files = [
            "application.log"
        ]
    
    def clear_logs_on_startup(self) -> None:
        """Clear or rotate log files on application startup.
        
        This method will:
        1. Rotate large log files to .old files
        2. Clear existing log files for a fresh start
        3. Clean up old rotated files based on retention policy
        """
        try:
            logging.info("Starting log cleanup on application startup...")
            
            for log_file in self.managed_log_files:
                log_path = self.logs_dir / log_file
                
                if log_path.exists():
                    file_size = log_path.stat().st_size
                    
                    # If file is larger than max size, rotate it
                    if file_size > self.max_size_bytes:
                        self._rotate_log_file(log_path)
                    else:
                        # For smaller files, just clear them
                        self._clear_log_file(log_path)
            
            # Clean up old rotated files
            self._cleanup_old_logs()
            
            logging.info("Log cleanup completed successfully")
            
        except Exception as e:
            logging.error(f"Error during log cleanup: {e}")
    
    def _rotate_log_file(self, log_path: Path) -> None:
        """Rotate a log file to preserve large logs.
        
        Args:
            log_path: Path to the log file to rotate
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_name = f"{log_path.stem}_{timestamp}.old"
            rotated_path = log_path.parent / rotated_name
            
            # Move current log to rotated file
            log_path.rename(rotated_path)
            
            # Create new empty log file
            log_path.touch()
            
            file_size_mb = rotated_path.stat().st_size / (1024 * 1024)
            logging.info(f"Rotated large log file {log_path.name} ({file_size_mb:.1f}MB) to {rotated_name}")
            
        except Exception as e:
            logging.error(f"Error rotating log file {log_path}: {e}")
    
    def _clear_log_file(self, log_path: Path) -> None:
        """Clear a log file.
        
        Args:
            log_path: Path to the log file to clear
        """
        try:
            file_size_mb = log_path.stat().st_size / (1024 * 1024)
            
            # Clear the file by opening in write mode
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("")
            
            logging.info(f"Cleared log file {log_path.name} ({file_size_mb:.1f}MB)")
            
        except Exception as e:
            logging.error(f"Error clearing log file {log_path}: {e}")
    
    def _cleanup_old_logs(self) -> None:
        """Clean up old rotated log files based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cutoff_timestamp = cutoff_date.timestamp()
            
            deleted_count = 0
            total_size_mb = 0
            
            # Find all .old files in logs directory
            for old_file in self.logs_dir.glob("*.old"):
                try:
                    file_mtime = old_file.stat().st_mtime
                    
                    if file_mtime < cutoff_timestamp:
                        file_size = old_file.stat().st_size
                        total_size_mb += file_size / (1024 * 1024)
                        
                        old_file.unlink()
                        deleted_count += 1
                        
                except Exception as e:
                    logging.warning(f"Error processing old log file {old_file}: {e}")
            
            if deleted_count > 0:
                logging.info(f"Cleaned up {deleted_count} old log files ({total_size_mb:.1f}MB total)")
            
        except Exception as e:
            logging.error(f"Error during old log cleanup: {e}")
    
    def get_log_sizes(self) -> dict:
        """Get current sizes of managed log files.
        
        Returns:
            Dictionary mapping log file names to their sizes in MB
        """
        sizes = {}
        
        for log_file in self.managed_log_files:
            log_path = self.logs_dir / log_file
            
            if log_path.exists():
                size_mb = log_path.stat().st_size / (1024 * 1024)
                sizes[log_file] = round(size_mb, 2)
            else:
                sizes[log_file] = 0.0
        
        return sizes
    
    def check_log_rotation_needed(self) -> List[str]:
        """Check which log files need rotation.
        
        Returns:
            List of log file names that exceed the maximum size
        """
        files_needing_rotation = []
        
        for log_file in self.managed_log_files:
            log_path = self.logs_dir / log_file
            
            if log_path.exists():
                file_size = log_path.stat().st_size
                if file_size > self.max_size_bytes:
                    files_needing_rotation.append(log_file)
        
        return files_needing_rotation
    
    def manual_cleanup(self, force_clear: bool = False) -> dict:
        """Manually trigger log cleanup.
        
        Args:
            force_clear: If True, clear all logs regardless of size
            
        Returns:
            Dictionary with cleanup results
        """
        results = {
            "cleared_files": [],
            "rotated_files": [],
            "errors": []
        }
        
        try:
            for log_file in self.managed_log_files:
                log_path = self.logs_dir / log_file
                
                if log_path.exists():
                    try:
                        file_size = log_path.stat().st_size
                        
                        if force_clear or file_size < self.max_size_bytes:
                            self._clear_log_file(log_path)
                            results["cleared_files"].append(log_file)
                        else:
                            self._rotate_log_file(log_path)
                            results["rotated_files"].append(log_file)
                            
                    except Exception as e:
                        error_msg = f"Error processing {log_file}: {e}"
                        results["errors"].append(error_msg)
                        logging.error(error_msg)
            
            # Clean up old files
            self._cleanup_old_logs()
            
        except Exception as e:
            error_msg = f"Error during manual cleanup: {e}"
            results["errors"].append(error_msg)
            logging.error(error_msg)
        
        return results
