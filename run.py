"""Entry point for the application package."""
import sys
import signal
import logging
import asyncio
import os
import platform
import json
from enum import Enum, auto
from typing import Optional, Dict, List
from contextlib import contextmanager

class Platform(Enum):
    """Supported platforms enumeration."""
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()

    @staticmethod
    def detect() -> 'Platform':
        """Detect the current platform."""
        system = platform.system().lower()
        if system == 'windows':
            return Platform.WINDOWS
        elif system == 'linux':
            return Platform.LINUX
        elif system == 'darwin':
            return Platform.MACOS
        return Platform.UNKNOWN

# Current platform
CURRENT_PLATFORM = Platform.detect()

# Exit codes
EXIT_SUCCESS = 0
EXIT_KEYBOARD_INTERRUPT = 1
EXIT_EXCEPTION = 2
EXIT_SIGNAL = 3

class ApplicationExit(SystemExit):
    """Custom exit exception for graceful shutdown."""
    pass

@contextmanager
def setup_logging():
    """Set up logging configuration as a context manager."""
    try:
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # Set up rotating file handler
        from logging.handlers import RotatingFileHandler
        log_file = os.path.join(log_dir, "application.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        
        # Set up formatting
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Load config to get logging level
        try:
            with open("config.json", 'r') as f:
                config = json.load(f)
            log_level = getattr(logging, config["logging"]["level"].upper())
        except (FileNotFoundError, KeyError, ValueError, AttributeError):
            log_level = logging.INFO  # Fallback if config is missing or invalid
            print("Warning: Could not load logging level from config, using INFO", file=sys.stderr)
            
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Adjust levels for noisy libraries
        logging.getLogger('discord').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('apscheduler').setLevel(logging.WARNING)
        
        yield
        
        # Clean up handlers
        root_logger.removeHandler(file_handler)
        root_logger.removeHandler(console_handler)
        file_handler.close()
        console_handler.close()
        
    except Exception as e:
        print(f"Failed to initialize logging: {e}", file=sys.stderr)
        sys.exit(EXIT_EXCEPTION)

class SignalHandler:
    """Handle system signals and graceful shutdown."""
    
    # Platform-specific signal mappings
    @staticmethod
    def _get_platform_signals():
        """Get platform-specific signal mappings."""
        def is_valid_signal(sig):
            """Check if a signal is valid on the current platform."""
            try:
                signal.Signals(sig)  # Validate the signal
                signal.getsignal(sig)  # Check if we can get its current handler
                return True
            except (ValueError, OSError, AttributeError):
                return False

        base_signals = {
            'terminate': [],
            'interrupt': [],
            'reload': []
        }
        
        # Always try to add SIGTERM and SIGINT if available
        if is_valid_signal(signal.SIGTERM):
            base_signals['terminate'].append(signal.SIGTERM)
        if is_valid_signal(signal.SIGINT):
            base_signals['interrupt'].append(signal.SIGINT)
        
        if Platform.detect() == Platform.WINDOWS:
            # Windows-specific signals
            for sig in [signal.SIGBREAK, signal.CTRL_C_EVENT, signal.CTRL_BREAK_EVENT]:
                if is_valid_signal(sig):
                    base_signals['terminate'].append(sig)
        else:
            # Unix-like systems (Linux, macOS)
            try:
                if hasattr(signal, 'SIGHUP') and is_valid_signal(signal.SIGHUP):
                    base_signals['reload'].append(signal.SIGHUP)
            except AttributeError:
                pass  # SIGHUP not available
                
        # Use the same validated signals for all platforms
        return {
            Platform.WINDOWS: base_signals,
            Platform.LINUX: base_signals,
            Platform.MACOS: base_signals,
            Platform.UNKNOWN: base_signals
        }
    
    # Initialize signals based on current platform
    SIGNALS = _get_platform_signals()
    
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._original_handlers: Dict[int, Optional[signal.Handlers]] = {}
        self._app = None
        self._platform = CURRENT_PLATFORM
    
    def attach_application(self, app):
        """Attach the main application instance for cleanup."""
        self._app = app
    
    async def shutdown(self, signame: str):
        """Handle graceful shutdown.
        
        Args:
            signame: Name of the signal triggering shutdown
        """
        if self._shutdown_event.is_set():
            return  # Already shutting down
            
        self._shutdown_event.set()
        logging.info(f"Initiating graceful shutdown due to {signame}")
        
        try:
            # If we have an application instance, try to clean it up
            if self._app and hasattr(self._app, 'cleanup'):
                await asyncio.wait_for(self._app.cleanup(), timeout=10.0)
        except asyncio.TimeoutError:
            logging.error("Cleanup timed out after 10 seconds")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}", exc_info=True)
        
        # Restore original signal handlers
        for sig, handler in self._original_handlers.items():
            try:
                if handler is not None:  # Only restore if we had a previous handler
                    signal.signal(sig, handler)
            except ValueError as e:
                logging.warning(f"Could not restore signal {sig}: {e}")
        
        raise ApplicationExit(EXIT_SIGNAL)
    
    def handle_signal(self, signum: int, frame) -> None:
        """Synchronous signal handler that schedules async shutdown.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signame = signal.Signals(signum).name
        
        if asyncio.get_event_loop().is_running():
            # Schedule the shutdown coroutine
            asyncio.create_task(self.shutdown(signame))
        else:
            # If not in event loop, exit immediately
            logging.warning(f"Received {signame} outside event loop, exiting immediately")
            sys.exit(EXIT_SIGNAL)
    
    def _setup_platform_specific(self):
        """Set up platform-specific configurations."""
        if self._platform == Platform.WINDOWS:
            # Windows-specific setup
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                
        elif self._platform == Platform.MACOS:
            # macOS-specific setup
            try:
                import fcntl
                # Prevent Terminal.app from sending SIGTERM on window close
                fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            except (ImportError, AttributeError, OSError) as e:
                logging.warning(f"Failed to set macOS terminal handling: {e}")
                
        elif self._platform == Platform.LINUX:
            # Linux-specific setup
            try:
                # Ignore SIGPIPE (broken pipe)
                signal.signal(signal.SIGPIPE, signal.SIG_IGN)
            except (AttributeError, ValueError) as e:
                logging.warning(f"Failed to set Linux signal handling: {e}")

    def setup(self):
        """Set up signal handlers for the current platform."""
        self._setup_platform_specific()
        
        # Get signals for current platform
        platform_signals = self.SIGNALS.get(self._platform, self.SIGNALS[Platform.UNKNOWN])
        active_signals = []
        
        # Collect all signals for the platform
        for signal_type, sigs in platform_signals.items():
            active_signals.extend(sigs)
        
        # Set up handlers for all collected signals
        for sig in active_signals:
            try:
                # Only set up handlers for signals that have been pre-validated
                self._original_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, self.handle_signal)
                logging.debug(f"Registered handler for signal {signal.Signals(sig).name}")
            except Exception as e:
                # This shouldn't happen since signals are pre-validated, but log just in case
                logging.debug(f"Skipping signal {sig}: {e}")

async def async_main() -> int:
    """Async main function that sets up and runs the application."""
    from src.main import Application
    
    signal_handler = SignalHandler()
    signal_handler.setup()
    
    try:
        app = Application()
        signal_handler.attach_application(app)
        await app.run()
        return EXIT_SUCCESS
        
    except KeyboardInterrupt:
        logging.info("Application terminated by user (CTRL+C)")
        if app:
            try:
                await app.cleanup()
            except Exception as e:
                logging.error(f"Error during cleanup: {e}", exc_info=True)
        return EXIT_KEYBOARD_INTERRUPT
    except ApplicationExit as e:
        if app:
            try:
                await app.cleanup()
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {cleanup_error}", exc_info=True)
        return e.code
    except asyncio.CancelledError:
        logging.info("Application tasks cancelled during shutdown")
        if app:
            try:
                await app.cleanup()
            except Exception as e:
                logging.error(f"Error during cleanup: {e}", exc_info=True)
        return EXIT_SUCCESS
    except Exception as e:
        logging.error(f"Application failed with error: {str(e)}", exc_info=True)
        return EXIT_EXCEPTION

def platform_checks() -> None:
    """Perform platform-specific checks and setup."""
    if CURRENT_PLATFORM == Platform.WINDOWS:
        # Check Windows version
        if sys.getwindowsversion().major < 10:
            logging.warning("Windows version < 10 detected. Some features may not work correctly.")
    
    elif CURRENT_PLATFORM == Platform.MACOS:
        # Check macOS version
        mac_ver = tuple(map(int, platform.mac_ver()[0].split('.')))
        if mac_ver < (10, 15):  # Catalina
            logging.warning("macOS version < 10.15 detected. Some features may not work correctly.")
    
    elif CURRENT_PLATFORM == Platform.LINUX:
        # Check for systemd
        if not os.path.exists('/run/systemd/system'):
            logging.info("Non-systemd Linux detected, using alternative service management.")
    
    # Check Python version
    if sys.version_info < (3, 7):
        logging.error("Python 3.7 or higher is required.")
        sys.exit(EXIT_EXCEPTION)

def main() -> int:
    """Main entry point with proper setup and error handling."""
    with setup_logging():
        try:
            # Write PID file
            pid_file = os.path.join(os.path.dirname(__file__), "app.pid")
            try:
                with open(pid_file, 'w') as f:
                    f.write(str(os.getpid()))
                logging.info(f"PID file written: {pid_file}")
            except Exception as e:
                logging.warning(f"Could not write PID file: {e}")
            
            # Perform platform-specific checks
            platform_checks()
            
            # Set default event loop policy based on platform
            if CURRENT_PLATFORM == Platform.WINDOWS:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            else:
                # Use uvloop on Unix-like systems if available
                try:
                    import uvloop
                    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                    logging.info("Using uvloop event loop")
                except ImportError:
                    logging.debug("uvloop not available, using default event loop")
                    
            # Run the application
            result = asyncio.run(async_main())
            
            # Clean up PID file on normal exit
            try:
                if os.path.exists(pid_file):
                    os.unlink(pid_file)
                    logging.info("PID file cleaned up")
            except Exception as e:
                logging.warning(f"Could not clean up PID file: {e}")
            
            return result
            
        except KeyboardInterrupt:
            # Clean up PID file on interrupt
            try:
                pid_file = os.path.join(os.path.dirname(__file__), "app.pid")
                if os.path.exists(pid_file):
                    os.unlink(pid_file)
            except Exception:
                pass
            return EXIT_KEYBOARD_INTERRUPT
        except Exception as e:
            logging.error(f"Startup error: {e}", exc_info=True)
            return EXIT_EXCEPTION

if __name__ == "__main__":
    sys.exit(main())
