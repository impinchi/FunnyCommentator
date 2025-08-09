"""Server configuration management."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerConfig:
    """Configuration for a single ARK server instance."""
    
    name: str  # Server identifier
    map_name: str  # Map name (e.g., "The Lost Island", "Ragnarok")
    rcon_host: str
    rcon_port: int
    rcon_password: str
    max_wild_dino_level: int
    tribe_name: str
    player_names: list[str]
    is_pve: bool
    database_table: str  # Each server gets its own table for summaries
    log_file_path: Optional[str] = None  # Path to ARK log file for fallback
    
    def get_context_prompt(self, ai_tone: str = None) -> str:
        """Generate the server-specific context for AI prompts."""
        game_type = "PvE" if self.is_pve else "PvP"
        default_tone = "You are expected to be sarcastic, hilarious and witty while being insulting and rude with mistakes."
        tone = ai_tone if ai_tone else default_tone
        
        return "\n".join([
            f"You are an advisor and commentator for an ARK: Survival Evolved server.",
            f"Server Name: {self.name}",
            f"Map: {self.map_name}",
            f"Max wild dino level is {self.max_wild_dino_level}.",
            f"Game Type: {game_type}",
            f"Active Tribe: {self.tribe_name}",
            f"Players: {', '.join(self.player_names)}",
            tone,
            "Sometimes players will use chat to ask you questions which you will receive in the logs. We will call you Ollama."
        ])
