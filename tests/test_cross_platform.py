"""Cross-platform compatibility test for ProcessManager.

This script tests the process manager on different platforms to ensure
proper functionality across Windows, macOS, and Linux.
"""
import sys
import time
import platform
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.process_manager import ProcessManager

def test_process_manager():
    """Test the process manager functionality."""
    print(f"Testing ProcessManager on {platform.system()} {platform.release()}")
    print("-" * 60)
    
    manager = ProcessManager()
    
    # Test 1: Initial status check
    print("1. Checking initial process status...")
    status = manager.get_process_status()
    print(f"   Status: {status.status}")
    print(f"   Running: {status.is_running}")
    if status.pid:
        print(f"   PID: {status.pid}")
    
    # Test 2: Find any running processes
    print("\n2. Searching for running FunnyCommentator processes...")
    running_processes = manager.find_running_processes()
    print(f"   Found {len(running_processes)} running process(es)")
    for i, proc in enumerate(running_processes):
        try:
            print(f"   Process {i+1}: PID {proc.pid}, Command: {' '.join(proc.cmdline()[:3])}")
        except Exception as e:
            print(f"   Process {i+1}: PID {proc.pid}, Error reading command: {e}")
    
    # Test 3: Platform detection
    print(f"\n3. Platform detection:")
    print(f"   Detected platform: {platform.system()}")
    print(f"   Is Windows: {manager.is_windows}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Script path: {manager.script_path}")
    print(f"   PID file: {manager.pid_file}")
    print(f"   Log file: {manager.log_file}")
    
    # Test 4: Process detection logic
    print(f"\n4. Testing process detection...")
    try:
        import psutil
        current_process = psutil.Process()
        is_our_process = manager._is_our_process(current_process)
        print(f"   Current process is detected as ours: {is_our_process}")
        print(f"   Current process command line: {current_process.cmdline()}")
    except Exception as e:
        print(f"   Error testing process detection: {e}")
    
    print("\n" + "=" * 60)
    print("Cross-platform compatibility test completed!")
    print("If you see no errors above, the ProcessManager should work")
    print("correctly on your platform.")

if __name__ == "__main__":
    test_process_manager()
