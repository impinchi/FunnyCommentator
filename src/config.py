"""Configuration management module.

This module handles all configuration settings for the application using JSON.
Following PEP 257 for docstring conventions.
"""
import json
import logging
from typing import Dict
from pathlib import Path
from .server_config import ServerConfig
from .credential_manager import CredentialManager

class Config:
    """Configuration class following singleton pattern for application settings."""
    
    _instance = None
    _config_file = "config.json"
    
    def __new__(cls):
        """Ensure only one instance of Config exists."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    @classmethod
    def reload(cls):
        """Force reload the configuration from file."""
        if cls._instance is not None:
            cls._instance._load_config()
        return cls._instance
    
    @classmethod 
    def reset(cls):
        """Clear the singleton instance (useful for testing)."""
        cls._instance = None
    
    def _load_servers(self, servers_data: list) -> Dict[str, ServerConfig]:
        """Load server configurations from config data."""
        try:
            servers = {}
            logging.info(f"Loading {len(servers_data)} servers from config")
            for server_data in servers_data:
                server_name = server_data["name"]
                logging.info(f"Loading server: {server_name}")
                
                try:
                    # Get RCON password from keyring if it's a placeholder
                    rcon_password = server_data["rcon_password"]
                    if rcon_password == "STORED_IN_KEYRING":
                        logging.info(f"Retrieving RCON password for {server_name} from keyring")
                        rcon_password = CredentialManager.get_rcon_password(server_name)
                        if not rcon_password:
                            logging.warning(f"RCON password for server '{server_name}' not found in keyring. Skipping server.")
                            continue
                        else:
                            logging.info(f"RCON password found for {server_name}")
                    
                    servers[server_name] = ServerConfig(
                        name=server_name,
                        map_name=server_data["map_name"],
                        rcon_host=server_data["rcon_host"],
                        rcon_port=int(server_data["rcon_port"]),
                        rcon_password=rcon_password,
                        max_wild_dino_level=int(server_data["max_wild_dino_level"]),
                        tribe_name=server_data["tribe_name"],
                        player_names=server_data["player_names"],
                        is_pve=bool(server_data["is_pve"]),
                        database_table=f"summaries_{server_data['name'].lower().replace(' ', '_')}",
                        log_file_path=server_data.get("log_file_path", None)
                    )
                    logging.info(f"Successfully loaded server: {server_name}")
                    
                except Exception as e:
                    logging.warning(f"Failed to load server '{server_name}': {e}. Skipping.")
                    continue
            
            logging.info(f"Successfully loaded {len(servers)} out of {len(servers_data)} servers")
            return servers
        except KeyError as e:
            error_msg = f"Missing required server configuration field: {e}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            logging.error(f"Error loading servers: {e}")
            raise
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            # Try current directory first, then parent directory
            config_paths = [
                self._config_file,
                Path("..") / self._config_file,
                Path(__file__).parent.parent / self._config_file
            ]
            
            config_file_used = None
            for config_path in config_paths:
                if Path(config_path).exists():
                    config_file_used = config_path
                    break
            
            if config_file_used is None:
                raise FileNotFoundError(f"Config file not found in any of: {config_paths}")
            
            with open(config_file_used, 'r') as f:
                config = json.load(f)
            
            logging.info(f"Successfully loaded config from: {config_file_used}")
            logging.debug(f"Config clusters section: {config.get('clusters', {})}")
            
            # Store the path for future writes
            self._config_file = str(config_file_used)
            
            # Discord Configuration
            discord = config.get("discord", {})
            discord_token = discord["token"]
            if discord_token == "STORED_IN_KEYRING":
                discord_token = CredentialManager.get_discord_token()
                if not discord_token:
                    raise RuntimeError("Discord token not found in keyring. Run credential setup first.")
            self.discord_token = discord_token
            self.channel_id_global = int(discord["channel_id_global"])
            self.channel_id_server_status = int(discord["channel_id_server_status"])
            self.channel_id_ai = int(discord["channel_id_ai"])
            
            # AI Configuration
            ai = config.get("ai", {})
            self.ollama_url = ai["ollama_url"]
            self.ollama_model = ai["ollama_model"]
            self.ollama_start_cmd = ai["ollama_start_cmd"]
            self.ai_timeout_seconds = int(ai["timeout_seconds"])
            self.input_token_size = int(ai.get("input_token_size", 4096))
            self.min_output_tokens = int(ai.get("min_output_tokens", 64))
            self.max_output_tokens = int(ai.get("max_output_tokens", 512))
            self.safety_buffer = int(ai.get("safety_buffer", 48))
            self.tokenizer_model = ai.get("tokenizer_model", "gpt-3.5-turbo")
            self.ollama_startup_timeout = int(ai.get("startup_timeout_seconds", 300))  # 5 minutes default
            self.ai_tone = ai.get("ai_tone", "You are expected to be sarcastic, hilarious and witty while being insulting and rude with mistakes.")
            
            # Server Configurations
            servers_data = config.get("servers", [])
            try:
                self.servers = self._load_servers(servers_data)
            except Exception as e:
                logging.warning(f"Error loading servers, continuing with empty server list: {e}")
                self.servers = {}
            
            # Cluster Configurations
            clusters_data = config.get("clusters", {})
            logging.debug(f"Loaded clusters data: {clusters_data}")
            self.clusters = {}
            for cluster_name, cluster_info in clusters_data.items():
                try:
                    logging.debug(f"Processing cluster '{cluster_name}': {cluster_info}")
                    # Verify all servers in cluster exist
                    valid_servers = []
                    for server_name in cluster_info.get("servers", []):
                        logging.debug(f"Checking server '{server_name}' for cluster '{cluster_name}'")
                        if server_name in self.servers:
                            valid_servers.append(server_name)
                        else:
                            logging.warning(f"Cluster '{cluster_name}' references non-existent server '{server_name}'. Skipping server.")
                    
                    # Only add cluster if it has at least one valid server
                    if valid_servers:
                        self.clusters[cluster_name] = {
                            "name": cluster_name,
                            "servers": valid_servers,
                            "description": cluster_info.get("description", "")
                        }
                        logging.info(f"Successfully loaded cluster '{cluster_name}' with {len(valid_servers)} servers")
                    else:
                        logging.warning(f"Cluster '{cluster_name}' has no valid servers. Skipping cluster.")
                except Exception as e:
                    logging.warning(f"Failed to load cluster '{cluster_name}': {e}. Skipping.")
                    continue
            
            # Build reverse lookup for server to cluster
            self.server_to_cluster = {}
            for cluster_name, cluster_info in self.clusters.items():
                for server_name in cluster_info["servers"]:
                    self.server_to_cluster[server_name] = cluster_name
            
            # IP Monitor Configuration
            ip_monitor = config.get("ip_monitor", {})
            self.ip_retry_seconds = int(ip_monitor.get("check_interval_seconds", 1800))
            self.previous_ip = ip_monitor.get("last_known_ip")
            
            # Scheduler Configuration
            scheduler = config.get("scheduler", {})
            self.scheduler_logs_hour = int(scheduler.get("logs_summary_hour", 4))
            self.scheduler_logs_minute = int(scheduler.get("logs_summary_minute", 0))
            
            # Database Configuration
            database = config.get("database", {})
            self.db_path = database["path"]
            
            # Logging Configuration
            logging_config = config.get("logging", {})
            self.log_level = logging_config.get("level", "DEBUG").upper()
            
        except FileNotFoundError:
            raise RuntimeError(f"Configuration file {self._config_file} not found")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in configuration file: {e}")
        except (KeyError, ValueError) as e:
            raise RuntimeError(f"Invalid configuration value: {e}")
    
    def save_config(self):
        """Save current configuration to JSON file."""
        config = {
            "discord": {
                "token": self.discord_token,
                "channel_id_global": self.channel_id_global,
                "channel_id_server_status": self.channel_id_server_status,
                "channel_id_ai": self.channel_id_ai
            },
            "ai": {
                "ollama_url": self.ollama_url,
                "ollama_model": self.ollama_model,
                "ollama_start_cmd": self.ollama_start_cmd,
                "timeout_seconds": self.ai_timeout_seconds,
                "input_token_size": self.input_token_size,
                "min_output_tokens": self.min_output_tokens,
                "max_output_tokens": self.max_output_tokens,
                "safety_buffer": self.safety_buffer,
                "tokenizer_model": self.tokenizer_model,
                "startup_timeout_seconds": self.ollama_startup_timeout,
                "ai_tone": self.ai_tone
            },
            "servers": [
                {
                    "name": server.name,
                    "map_name": server.map_name,
                    "rcon_host": server.rcon_host,
                    "rcon_port": server.rcon_port,
                    "rcon_password": server.rcon_password,
                    "max_wild_dino_level": server.max_wild_dino_level,
                    "tribe_name": server.tribe_name,
                    "player_names": server.player_names,
                    "is_pve": server.is_pve
                }
                for server in self.servers.values()
            ],
            "clusters": {
                name: {
                    "servers": info["servers"]
                }
                for name, info in self.clusters.items()
            },
            "ip_monitor": {
                "check_interval_seconds": self.ip_retry_seconds,
                "last_known_ip": self.previous_ip
            },
            "scheduler": {
                "logs_summary_hour": self.scheduler_logs_hour,
                "logs_summary_minute": self.scheduler_logs_minute
            },
            "database": {
                "path": self.db_path
            },
            "logging": {
                "level": self.log_level
            }
        }
        
        try:
            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            raise RuntimeError(f"Failed to save configuration: {e}")
