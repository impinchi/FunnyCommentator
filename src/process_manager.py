"""Process management for FunnyCommentator application.

This module provides functionality to manage the main application process,
including starting, stopping, and monitoring status.
"""
import os
import sys
import time
import signal
import psutil
import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ProcessStatus:
    """Process status information."""
    is_running: bool
    pid: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    start_time: Optional[float] = None
    uptime_seconds: Optional[int] = None
    status: str = "unknown"
    system_cpu_percent: Optional[float] = None
    system_memory_percent: Optional[float] = None

class ProcessManager:
    """Manages the FunnyCommentator main application process."""
    
    def __init__(self):
        """Initialize the process manager."""
        self.app_name = "FunnyCommentator"
        self.script_path = Path(__file__).parent.parent / "run.py"
        self.pid_file = Path(__file__).parent.parent / "app.pid"
        self.log_file = Path(__file__).parent.parent / "logs" / "process.log"
        self.is_windows = platform.system().lower() == 'windows'
        
    def _is_our_process(self, process: psutil.Process) -> bool:
        """Check if a process is our FunnyCommentator application."""
        try:
            cmdline = process.cmdline()
            
            # Check for our script in command line
            for arg in cmdline:
                if 'run.py' in arg or 'FunnyCommentator' in arg:
                    return True
                    
            # Alternative check: look for python process with our script
            if len(cmdline) >= 2:
                python_executables = ['python', 'python.exe', 'python3', 'python3.exe']
                if any(exe in cmdline[0].lower() for exe in python_executables):
                    if len(cmdline) > 1 and 'run.py' in cmdline[1]:
                        return True
                        
            return False
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return False
    
    def find_running_processes(self) -> list:
        """Find all running FunnyCommentator processes."""
        running_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    if self._is_our_process(proc):
                        running_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logging.error(f"Error finding running processes: {e}")
        return running_processes
        
    def _get_system_metrics(self) -> tuple:
        """Get system-wide CPU and memory usage."""
        try:
            system_cpu = psutil.cpu_percent(interval=0.1)
            system_memory = psutil.virtual_memory().percent
            return system_cpu, system_memory
        except Exception:
            return None, None

    def get_process_status(self) -> ProcessStatus:
        """Get the current status of the main application process."""
        try:
            # Check if PID file exists
            if not self.pid_file.exists():
                # No PID file, but check for orphaned processes
                running_processes = self.find_running_processes()
                if running_processes:
                    # Found orphaned process(es), use the first one
                    process = running_processes[0]
                    try:
                        # Write PID file for the orphaned process
                        with open(self.pid_file, 'w') as f:
                            f.write(str(process.pid))
                        logging.info(f"Found orphaned process {process.pid}, created PID file")
                        
                        # Get process information
                        # Note: cpu_percent() with interval gives more accurate reading
                        try:
                            cpu_percent = process.cpu_percent(interval=0.1)
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            cpu_percent = 0.0
                        
                        try:
                            memory_percent = process.memory_percent()
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            memory_percent = 0.0
                        
                        start_time = process.create_time()
                        uptime_seconds = int(time.time() - start_time)
                        
                        # Get system-wide metrics
                        system_cpu, system_memory = self._get_system_metrics()
                        
                        return ProcessStatus(
                            is_running=True,
                            pid=process.pid,
                            cpu_percent=cpu_percent,
                            memory_percent=memory_percent,
                            start_time=start_time,
                            uptime_seconds=uptime_seconds,
                            status="running_orphaned",
                            system_cpu_percent=system_cpu,
                            system_memory_percent=system_memory
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                return ProcessStatus(is_running=False, status="not_started", 
                                    system_cpu_percent=self._get_system_metrics()[0], 
                                    system_memory_percent=self._get_system_metrics()[1])
            
            # Read PID from file
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
            except (ValueError, FileNotFoundError):
                return ProcessStatus(is_running=False, status="pid_file_invalid",
                                    system_cpu_percent=self._get_system_metrics()[0], 
                                    system_memory_percent=self._get_system_metrics()[1])
            
            # Check if process is actually running
            try:
                process = psutil.Process(pid)
                
                # Verify it's our process by checking command line
                if not self._is_our_process(process):
                    return ProcessStatus(is_running=False, status="different_process",
                                        system_cpu_percent=self._get_system_metrics()[0], 
                                        system_memory_percent=self._get_system_metrics()[1])
                
                # Get process information
                # Note: cpu_percent() with interval gives more accurate reading
                try:
                    cpu_percent = process.cpu_percent(interval=0.1)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cpu_percent = 0.0
                
                try:
                    memory_percent = process.memory_percent()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    memory_percent = 0.0
                start_time = process.create_time()
                uptime_seconds = int(time.time() - start_time)
                
                # Get system-wide metrics
                system_cpu, system_memory = self._get_system_metrics()
                
                return ProcessStatus(
                    is_running=True,
                    pid=pid,
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    start_time=start_time,
                    uptime_seconds=uptime_seconds,
                    status="running",
                    system_cpu_percent=system_cpu,
                    system_memory_percent=system_memory
                )
                
            except psutil.NoSuchProcess:
                # Process doesn't exist, clean up PID file
                try:
                    self.pid_file.unlink()
                except FileNotFoundError:
                    pass
                return ProcessStatus(is_running=False, status="process_not_found",
                                    system_cpu_percent=self._get_system_metrics()[0], 
                                    system_memory_percent=self._get_system_metrics()[1])
            
        except Exception as e:
            logging.error(f"Error checking process status: {e}")
            return ProcessStatus(is_running=False, status="error",
                                system_cpu_percent=self._get_system_metrics()[0], 
                                system_memory_percent=self._get_system_metrics()[1])
    
    def start_application(self) -> Dict[str, Any]:
        """Start the main application."""
        try:
            # Check if already running
            status = self.get_process_status()
            if status.is_running:
                return {
                    'success': False,
                    'message': f'Application is already running (PID: {status.pid})',
                    'status': status
                }
            
            # Ensure logs directory exists
            self.log_file.parent.mkdir(exist_ok=True)
            
            # Start the process with platform-specific parameters
            log_file_handle = open(self.log_file, 'a')
            startup_kwargs = {
                'stdout': log_file_handle,
                'stderr': subprocess.STDOUT,
                'cwd': str(self.script_path.parent)
            }
            
            if self.is_windows:
                # Windows-specific: Use CREATE_NEW_PROCESS_GROUP
                startup_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                # Unix-specific: Use start_new_session
                startup_kwargs['start_new_session'] = True
            
            try:
                process = subprocess.Popen(
                    [sys.executable, str(self.script_path)],
                    **startup_kwargs
                )
            finally:
                # Close the log file handle after starting
                log_file_handle.close()
            
            # Write PID to file
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment and verify it started
            time.sleep(2)
            new_status = self.get_process_status()
            
            if new_status.is_running:
                return {
                    'success': True,
                    'message': f'Application started successfully (PID: {new_status.pid})',
                    'status': new_status
                }
            else:
                return {
                    'success': False,
                    'message': 'Application failed to start - check logs for details',
                    'status': new_status
                }
                
        except Exception as e:
            logging.error(f"Error starting application: {e}")
            return {
                'success': False,
                'message': f'Failed to start application: {str(e)}',
                'status': ProcessStatus(is_running=False, status="start_error")
            }
    
    def stop_application(self) -> Dict[str, Any]:
        """Stop the main application."""
        try:
            status = self.get_process_status()
            
            if not status.is_running:
                return {
                    'success': True,
                    'message': 'Application is not running',
                    'status': status
                }
            
            # Send termination signal (graceful shutdown)
            try:
                process = psutil.Process(status.pid)
                
                if self.is_windows:
                    # Windows: Use terminate() which sends SIGTERM equivalent
                    process.terminate()
                else:
                    # Unix: Send SIGTERM signal
                    process.send_signal(signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    if self.is_windows:
                        # Windows: Use kill() for force termination
                        process.kill()
                    else:
                        # Unix: Send SIGKILL
                        process.send_signal(signal.SIGKILL)
                    process.wait(timeout=5)
                
            except psutil.NoSuchProcess:
                pass  # Process already terminated
            
            # Clean up PID file
            try:
                self.pid_file.unlink()
            except FileNotFoundError:
                pass
            
            # Verify it stopped
            final_status = self.get_process_status()
            
            return {
                'success': True,
                'message': 'Application stopped successfully',
                'status': final_status
            }
            
        except Exception as e:
            logging.error(f"Error stopping application: {e}")
            return {
                'success': False,
                'message': f'Failed to stop application: {str(e)}',
                'status': self.get_process_status()
            }
    
    def restart_application(self) -> Dict[str, Any]:
        """Restart the main application."""
        try:
            # Stop first
            stop_result = self.stop_application()
            if not stop_result['success']:
                return stop_result
            
            # Wait a moment before starting
            time.sleep(1)
            
            # Start again
            start_result = self.start_application()
            
            return {
                'success': start_result['success'],
                'message': f"Restart {'completed' if start_result['success'] else 'failed'}: {start_result['message']}",
                'status': start_result['status']
            }
            
        except Exception as e:
            logging.error(f"Error restarting application: {e}")
            return {
                'success': False,
                'message': f'Failed to restart application: {str(e)}',
                'status': self.get_process_status()
            }
    
    def get_application_logs(self, lines: int = 50) -> str:
        """Get recent application logs."""
        try:
            if not self.log_file.exists():
                return "No logs available"
            
            with open(self.log_file, 'r') as f:
                log_lines = f.readlines()
                
            # Return last N lines
            recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
            return ''.join(recent_lines)
            
        except Exception as e:
            return f"Error reading logs: {str(e)}"
    
    def format_uptime(self, uptime_seconds: int) -> str:
        """Format uptime in human readable format."""
        if uptime_seconds < 60:
            return f"{uptime_seconds}s"
        elif uptime_seconds < 3600:
            minutes = uptime_seconds // 60
            seconds = uptime_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
