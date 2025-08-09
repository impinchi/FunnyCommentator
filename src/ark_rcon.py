"""Alternative RCON implementation specifically for ARK servers."""

import socket
import struct
import logging
from typing import List, Optional

class ARKRconClient:
    """Custom RCON client specifically designed for ARK servers."""
    
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.socket = None
        self.request_id = 1
        
    def connect(self) -> bool:
        """Connect to the ARK RCON server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            
            # Send authentication
            if self._authenticate():
                logging.info(f"Successfully authenticated to ARK RCON at {self.host}:{self.port}")
                return True
            else:
                logging.error("RCON authentication failed")
                return False
                
        except Exception as e:
            logging.error(f"Failed to connect to ARK RCON: {e}")
            return False
    
    def _authenticate(self) -> bool:
        """Authenticate with the RCON server."""
        try:
            auth_packet = self._create_packet(3, self.password)  # SERVERDATA_AUTH = 3
            self.socket.send(auth_packet)
            
            # Read response
            response = self._read_packet()
            if response and response[0] == self.request_id:
                logging.debug("RCON authentication successful")
                self.request_id += 1
                return True
            else:
                logging.error("RCON authentication failed - invalid response")
                return False
                
        except Exception as e:
            logging.error(f"RCON authentication error: {e}")
            return False
    
    def _create_packet(self, packet_type: int, body: str) -> bytes:
        """Create an RCON packet."""
        body_bytes = body.encode('utf-8') + b'\x00'
        packet_size = len(body_bytes) + 10  # 4 bytes for ID + 4 bytes for type + 2 null terminators
        
        packet = struct.pack('<L', packet_size)  # Size (little endian)
        packet += struct.pack('<L', self.request_id)  # Request ID
        packet += struct.pack('<L', packet_type)  # Type
        packet += body_bytes  # Body with null terminator
        packet += b'\x00'  # Additional null terminator
        
        return packet
    
    def _read_packet(self) -> Optional[tuple]:
        """Read a packet from the socket."""
        try:
            # Read packet size
            size_data = self.socket.recv(4)
            if len(size_data) < 4:
                return None
            
            packet_size = struct.unpack('<L', size_data)[0]
            
            # Read the rest of the packet
            packet_data = b''
            while len(packet_data) < packet_size:
                chunk = self.socket.recv(packet_size - len(packet_data))
                if not chunk:
                    break
                packet_data += chunk
            
            if len(packet_data) < packet_size:
                return None
            
            # Parse packet
            request_id = struct.unpack('<L', packet_data[0:4])[0]
            packet_type = struct.unpack('<L', packet_data[4:8])[0]
            body = packet_data[8:-2].decode('utf-8')  # Remove null terminators
            
            return (request_id, packet_type, body)
            
        except Exception as e:
            logging.error(f"Error reading RCON packet: {e}")
            return None
    
    def send_command(self, command: str) -> Optional[str]:
        """Send a command to the RCON server."""
        try:
            command_packet = self._create_packet(2, command)  # SERVERDATA_EXECCOMMAND = 2
            self.socket.send(command_packet)
            
            # Read response
            response = self._read_packet()
            if response:
                self.request_id += 1
                return response[2]  # Return body
            else:
                return None
                
        except Exception as e:
            logging.error(f"Error sending RCON command '{command}': {e}")
            return None
    
    def close(self):
        """Close the RCON connection."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def fetch_logs(self) -> List[str]:
        """Fetch logs from ARK server using custom RCON implementation."""
        if not self.connect():
            return []
        
        try:
            # Try different ARK commands
            commands = [
                "GetGameLog",
                "getgamelog", 
                "getchat",
                "listplayers"  # This should work to test connectivity
            ]
            
            for cmd in commands:
                result = self.send_command(cmd)
                if result and len(result.strip()) > 10:  # Got meaningful response
                    logging.info(f"ARK RCON command '{cmd}' returned {len(result)} characters")
                    lines = result.splitlines()
                    return [line.strip() for line in lines if line.strip()]
            
            # If no commands worked, return empty list
            logging.warning("No ARK RCON commands returned useful data")
            return []
            
        finally:
            self.close()
