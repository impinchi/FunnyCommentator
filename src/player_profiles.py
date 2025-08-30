#!/usr/bin/env python3
"""
Player Profile Manager for FunnyCommentator AI Memory System
Phase 3: Player Profiles - Tracks player behavior, preferences, and patterns
"""

import sqlite3
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import threading


class PlayerProfileManager:
    """
    Manages player profiles with behavior tracking, preference learning,
    and personality adaptation for the AI commentary system.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the Player Profile Manager.
        
        Args:
            database_manager: DatabaseManager instance for data persistence
        """
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        self.profiles_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_expiry = timedelta(hours=1)  # Cache profiles for 1 hour
        
        # Initialize database tables
        self._create_player_tables()
        
        # Player behavior patterns
        self.behavior_patterns = {
            'taming': ['tamed', 'tame completed', 'dinosaur tamed'],
            'death': ['died', 'was killed', 'death'],
            'building': ['placed', 'built', 'constructed', 'foundation'],
            'pvp': ['destroyed', 'killed', 'raided', 'attacked'],
            'joining': ['joined', 'connected'],
            'leaving': ['left', 'disconnected'],
            'tribe': ['tribe', 'invited', 'promoted', 'demoted'],
            'chat': ['said', 'chat', 'global']
        }
        
        # Dino categories for classification
        self.dino_categories = {
            'utility': ['ankylo', 'doedicurus', 'beaver', 'argentavis', 'quetzal'],
            'combat': ['rex', 'giga', 'spino', 'carno', 'therizino'],
            'transport': ['argentavis', 'quetzal', 'wyvern', 'griffin', 'phoenix'],
            'gathering': ['ankylo', 'doedicurus', 'mammoth', 'therizino'],
            'tek': ['tek parasaur', 'tek raptor', 'tek rex', 'tek stego'],
            'rare': ['wyvern', 'griffin', 'phoenix', 'reaper', 'rock drake']
        }
        
        self.logger.info("Player Profile Manager initialized")
    
    def _create_player_tables(self):
        """Create database tables for player profiles if they don't exist."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                # Player profiles table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS player_profiles (
                        player_name TEXT PRIMARY KEY,
                        first_seen TIMESTAMP,
                        last_seen TIMESTAMP,
                        total_sessions INTEGER DEFAULT 0,
                        total_playtime_hours REAL DEFAULT 0.0,
                        personality_type TEXT DEFAULT 'unknown',
                        profile_data TEXT,  -- JSON data
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Player events table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS player_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_name TEXT,
                        event_type TEXT,
                        event_details TEXT,  -- JSON data
                        server_name TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_name) REFERENCES player_profiles (player_name)
                    )
                ''')
                
                # Player relationships table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS player_relationships (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player1 TEXT,
                        player2 TEXT,
                        relationship_type TEXT,  -- tribe, ally, rival, friend
                        strength REAL DEFAULT 1.0,
                        last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(player1, player2, relationship_type)
                    )
                ''')
                
                conn.commit()
                self.logger.info("Player profile tables created/verified")
                
        except Exception as e:
            self.logger.error(f"Failed to create player tables: {e}")
            raise
    
    def extract_players_from_logs(self, logs) -> List[str]:
        """
        Extract player names from log entries.
        
        Args:
            logs: Raw log text to analyze (string or list of strings)
            
        Returns:
            List of player names found in logs
        """
        # Handle both string and list inputs
        if isinstance(logs, list):
            logs_text = '\n'.join(logs)
        elif isinstance(logs, str):
            logs_text = logs
        else:
            self.logger.warning(f"Unexpected logs type: {type(logs)}, converting to string")
            logs_text = str(logs)
        
        players = set()
        
        # Common ARK log patterns for player names
        patterns = [
            r'(\w+) tamed',
            r'(\w+) died',
            r'(\w+) was killed',
            r'(\w+) joined',
            r'(\w+) left',
            r'(\w+) said',
            r'(\w+) placed',
            r'(\w+) destroyed',
            r'Tribe (\w+)',
            r'Player (\w+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, logs_text, re.IGNORECASE)
            for match in matches:
                player_name = match.group(1).strip()
                # Filter out common false positives
                if (len(player_name) > 2 and 
                    not player_name.lower() in ['the', 'and', 'was', 'you', 'all', 'any']):
                    players.add(player_name)
        
        return list(players)
    
    def analyze_event_type(self, log_text: str) -> Dict[str, Any]:
        """
        Analyze log text to determine event type and extract details.
        
        Args:
            log_text: Single log entry to analyze
            
        Returns:
            Dictionary with event type and extracted details
        """
        log_lower = log_text.lower()
        
        for event_type, keywords in self.behavior_patterns.items():
            if any(keyword in log_lower for keyword in keywords):
                details = self._extract_event_details(log_text, event_type)
                return {
                    'type': event_type,
                    'details': details,
                    'raw_log': log_text
                }
        
        return {
            'type': 'unknown',
            'details': {},
            'raw_log': log_text
        }
    
    def _extract_event_details(self, log_text: str, event_type: str) -> Dict[str, Any]:
        """Extract specific details based on event type."""
        details = {}
        
        if event_type == 'taming':
            # Extract dino type and level
            dino_match = re.search(r'tamed a (\w+)', log_text, re.IGNORECASE)
            if dino_match:
                details['dino_type'] = dino_match.group(1)
                details['dino_category'] = self._categorize_dino(details['dino_type'])
            
            level_match = re.search(r'level (\d+)', log_text, re.IGNORECASE)
            if level_match:
                details['level'] = int(level_match.group(1))
        
        elif event_type == 'death':
            # Extract cause of death
            if 'killed by' in log_text.lower():
                killer_match = re.search(r'killed by (\w+)', log_text, re.IGNORECASE)
                if killer_match:
                    details['killed_by'] = killer_match.group(1)
            
        elif event_type == 'building':
            # Extract structure type
            structure_match = re.search(r'placed (\w+)', log_text, re.IGNORECASE)
            if structure_match:
                details['structure_type'] = structure_match.group(1)
        
        return details
    
    def _categorize_dino(self, dino_name: str) -> str:
        """Categorize a dinosaur based on its name."""
        dino_lower = dino_name.lower()
        
        for category, dinos in self.dino_categories.items():
            if any(dino in dino_lower for dino in dinos):
                return category
        
        return 'other'
    
    def update_player_profile(self, player_name: str, server_name: str, 
                            events: List[Dict[str, Any]]):
        """
        Update a player's profile based on new events.
        
        Args:
            player_name: Name of the player
            server_name: Server where events occurred  
            events: List of event dictionaries
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                # Get or create player profile
                cursor = conn.execute(
                    'SELECT profile_data, total_sessions FROM player_profiles WHERE player_name = ?',
                    (player_name,)
                )
                result = cursor.fetchone()
                
                if result:
                    profile_data = json.loads(result[0]) if result[0] else {}
                    total_sessions = result[1]
                else:
                    profile_data = self._create_empty_profile()
                    total_sessions = 0
                    
                    # Insert new player
                    conn.execute('''
                        INSERT INTO player_profiles 
                        (player_name, first_seen, last_seen, profile_data)
                        VALUES (?, ?, ?, ?)
                    ''', (player_name, datetime.now(), datetime.now(), json.dumps(profile_data)))
                
                # Process events
                for event in events:
                    self._process_event_for_profile(profile_data, event)
                    
                    # Store event in events table
                    conn.execute('''
                        INSERT INTO player_events 
                        (player_name, event_type, event_details, server_name)
                        VALUES (?, ?, ?, ?)
                    ''', (player_name, event['type'], json.dumps(event['details']), server_name))
                
                # Update player profile
                conn.execute('''
                    UPDATE player_profiles 
                    SET profile_data = ?, last_seen = ?, updated_at = ?
                    WHERE player_name = ?
                ''', (json.dumps(profile_data), datetime.now(), datetime.now(), player_name))
                
                conn.commit()
                
                # Update cache
                with self.cache_lock:
                    self.profiles_cache[player_name] = {
                        'data': profile_data,
                        'cached_at': datetime.now()
                    }
                
                self.logger.debug(f"Updated profile for {player_name} with {len(events)} events")
                
        except Exception as e:
            self.logger.error(f"Failed to update player profile for {player_name}: {e}")
    
    def _create_empty_profile(self) -> Dict[str, Any]:
        """Create an empty player profile structure."""
        return {
            'favorite_dinos': {},
            'dino_categories': {},
            'death_count': 0,
            'taming_count': 0,
            'building_count': 0,
            'pvp_encounters': 0,
            'session_count': 0,
            'preferred_playtimes': [],
            'personality_traits': {
                'aggressive': 0.0,
                'builder': 0.0,
                'tamer': 0.0,
                'explorer': 0.0,
                'social': 0.0
            },
            'notable_events': [],
            'server_preferences': {},
            'relationships': {}
        }
    
    def _process_event_for_profile(self, profile_data: Dict[str, Any], event: Dict[str, Any]):
        """Process a single event and update profile data."""
        event_type = event['type']
        details = event['details']
        
        if event_type == 'taming':
            profile_data['taming_count'] += 1
            
            if 'dino_type' in details:
                dino = details['dino_type']
                profile_data['favorite_dinos'][dino] = profile_data['favorite_dinos'].get(dino, 0) + 1
                
                category = details.get('dino_category', 'other')
                profile_data['dino_categories'][category] = profile_data['dino_categories'].get(category, 0) + 1
            
            # Increase tamer personality trait
            profile_data['personality_traits']['tamer'] += 0.1
            
        elif event_type == 'death':
            profile_data['death_count'] += 1
            
            if 'killed_by' in details:
                if details['killed_by'].lower() in ['player', 'tribe']:
                    profile_data['pvp_encounters'] += 1
                    profile_data['personality_traits']['aggressive'] += 0.05
            
        elif event_type == 'building':
            profile_data['building_count'] += 1
            profile_data['personality_traits']['builder'] += 0.1
            
        elif event_type == 'chat':
            profile_data['personality_traits']['social'] += 0.05
        
        # Cap personality traits at 1.0
        for trait in profile_data['personality_traits']:
            profile_data['personality_traits'][trait] = min(1.0, profile_data['personality_traits'][trait])
    
    def get_player_context(self, player_name: str, server_name: str = None) -> Dict[str, Any]:
        """
        Get contextual information about a player for AI response generation.
        
        Args:
            player_name: Name of the player
            server_name: Optional server name for server-specific context
            
        Returns:
            Dictionary with player context information
        """
        # Check cache first
        with self.cache_lock:
            if (player_name in self.profiles_cache and 
                datetime.now() - self.profiles_cache[player_name]['cached_at'] < self.cache_expiry):
                profile_data = self.profiles_cache[player_name]['data']
            else:
                profile_data = self._load_player_profile(player_name)
        
        if not profile_data:
            return {
                'player_name': player_name,
                'is_known': False,
                'context_summary': f"{player_name} is a new or occasional player"
            }
        
        # Generate context summary
        context = self._generate_context_summary(player_name, profile_data)
        
        return {
            'player_name': player_name,
            'is_known': True,
            'profile_data': profile_data,
            'context_summary': context,
            'personality_type': self._determine_personality_type(profile_data),
            'favorite_activities': self._get_favorite_activities(profile_data),
            'notable_stats': self._get_notable_stats(profile_data)
        }
    
    def _load_player_profile(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Load player profile from database."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute(
                    'SELECT profile_data FROM player_profiles WHERE player_name = ?',
                    (player_name,)
                )
                result = cursor.fetchone()
                
                if result and result[0]:
                    profile_data = json.loads(result[0])
                    
                    # Cache the profile
                    with self.cache_lock:
                        self.profiles_cache[player_name] = {
                            'data': profile_data,
                            'cached_at': datetime.now()
                        }
                    
                    return profile_data
                
        except Exception as e:
            self.logger.error(f"Failed to load profile for {player_name}: {e}")
        
        return None
    
    def _generate_context_summary(self, player_name: str, profile_data: Dict[str, Any]) -> str:
        """Generate a human-readable context summary for the player."""
        summary_parts = []
        
        # Personality type
        personality = self._determine_personality_type(profile_data)
        summary_parts.append(f"{player_name} is a {personality}")
        
        # Favorite activities
        activities = self._get_favorite_activities(profile_data)
        if activities:
            summary_parts.append(f"who loves {', '.join(activities)}")
        
        # Notable stats
        stats = self._get_notable_stats(profile_data)
        if stats:
            summary_parts.append(f"Notable: {', '.join(stats)}")
        
        return ". ".join(summary_parts)
    
    def _determine_personality_type(self, profile_data: Dict[str, Any]) -> str:
        """Determine player personality type based on their activities."""
        traits = profile_data.get('personality_traits', {})
        
        if not traits:
            return "newcomer"
        
        # Find dominant trait
        max_trait = max(traits, key=traits.get)
        max_value = traits[max_trait]
        
        if max_value < 0.3:
            return "casual player"
        
        personality_types = {
            'tamer': "dinosaur enthusiast",
            'builder': "master architect", 
            'aggressive': "PvP warrior",
            'social': "community leader",
            'explorer': "adventurous survivor"
        }
        
        return personality_types.get(max_trait, "active survivor")
    
    def _get_favorite_activities(self, profile_data: Dict[str, Any]) -> List[str]:
        """Get list of player's favorite activities."""
        activities = []
        
        # Check taming preferences
        favorite_dinos = profile_data.get('favorite_dinos', {})
        if favorite_dinos:
            top_dino = max(favorite_dinos, key=favorite_dinos.get)
            if favorite_dinos[top_dino] > 2:
                activities.append(f"taming {top_dino}s")
        
        # Check dino categories
        categories = profile_data.get('dino_categories', {})
        if categories:
            top_category = max(categories, key=categories.get)
            if categories[top_category] > 3:
                activities.append(f"{top_category} dinosaurs")
        
        # Check activity counts
        if profile_data.get('building_count', 0) > 10:
            activities.append("building")
        
        if profile_data.get('pvp_encounters', 0) > 5:
            activities.append("PvP combat")
        
        return activities[:3]  # Limit to top 3
    
    def _get_notable_stats(self, profile_data: Dict[str, Any]) -> List[str]:
        """Get notable statistics about the player."""
        stats = []
        
        death_count = profile_data.get('death_count', 0)
        if death_count > 20:
            stats.append(f"{death_count} deaths")
        
        taming_count = profile_data.get('taming_count', 0)
        if taming_count > 15:
            stats.append(f"{taming_count} tames")
        
        building_count = profile_data.get('building_count', 0)
        if building_count > 50:
            stats.append(f"{building_count} structures built")
        
        return stats[:2]  # Limit to top 2
    
    def get_player_relationships(self, player_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get player relationships (tribe mates, allies, rivals)."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute('''
                    SELECT player2, relationship_type, strength, last_interaction
                    FROM player_relationships 
                    WHERE player1 = ?
                    ORDER BY strength DESC
                ''', (player_name,))
                
                relationships = defaultdict(list)
                for row in cursor.fetchall():
                    relationships[row[1]].append({
                        'player': row[0],
                        'strength': row[2],
                        'last_interaction': row[3]
                    })
                
                return dict(relationships)
                
        except Exception as e:
            self.logger.error(f"Failed to get relationships for {player_name}: {e}")
            return {}
    
    def get_server_player_summary(self, server_name: str, limit: int = 10) -> Dict[str, Any]:
        """Get summary of most active players on a server."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute('''
                    SELECT p.player_name, p.profile_data, COUNT(e.id) as event_count
                    FROM player_profiles p
                    LEFT JOIN player_events e ON p.player_name = e.player_name
                    WHERE e.server_name = ? OR e.server_name IS NULL
                    GROUP BY p.player_name
                    ORDER BY event_count DESC, p.last_seen DESC
                    LIMIT ?
                ''', (server_name, limit))
                
                players = []
                for row in cursor.fetchall():
                    profile_data = json.loads(row[1]) if row[1] else {}
                    players.append({
                        'name': row[0],
                        'event_count': row[2],
                        'personality_type': self._determine_personality_type(profile_data),
                        'context': self._generate_context_summary(row[0], profile_data)
                    })
                
                return {
                    'server_name': server_name,
                    'active_players': players,
                    'total_tracked': len(players)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get server player summary for {server_name}: {e}")
            return {'server_name': server_name, 'active_players': [], 'total_tracked': 0}
    
    def process_logs_for_profiles(self, logs, server_name: str):
        """
        Process raw logs to extract player events and update profiles.
        
        Args:
            logs: Raw log text to process (string or list of strings)
            server_name: Name of the server
        """
        try:
            # Handle both string and list inputs
            if isinstance(logs, list):
                logs_text = '\n'.join(logs)
                log_lines = [line.strip() for line in logs if line.strip()]
            elif isinstance(logs, str):
                logs_text = logs
                log_lines = [line.strip() for line in logs.split('\n') if line.strip()]
            else:
                self.logger.warning(f"Unexpected logs type: {type(logs)}, converting to string")
                logs_text = str(logs)
                log_lines = [line.strip() for line in logs_text.split('\n') if line.strip()]
            
            # Extract players from logs
            players = self.extract_players_from_logs(logs_text)
            
            if not players:
                return
            
            # Process each player
            for player_name in players:
                player_events = []
                
                # Find log entries mentioning this player
                for log_line in log_lines:
                    if player_name.lower() in log_line.lower():
                        event = self.analyze_event_type(log_line)
                        if event['type'] != 'unknown':
                            player_events.append(event)
                
                # Update player profile if we found events
                if player_events:
                    self.update_player_profile(player_name, server_name, player_events)
            
            self.logger.debug(f"Processed logs for {len(players)} players on {server_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to process logs for profiles: {e}")
    
    def get_contextual_player_summaries(self, players: List[str], max_length: int = 500) -> str:
        """
        Get contextual summaries for multiple players, optimized for AI context.
        
        Args:
            players: List of player names
            max_length: Maximum length of returned text
            
        Returns:
            Formatted string with player contexts
        """
        if not players:
            return ""
        
        summaries = []
        for player_name in players[:5]:  # Limit to 5 players
            context = self.get_player_context(player_name)
            if context['is_known']:
                summaries.append(context['context_summary'])
            else:
                summaries.append(f"{player_name} (new player)")
        
        full_summary = "\n".join(summaries)
        
        # Truncate if too long
        if len(full_summary) > max_length:
            full_summary = full_summary[:max_length-3] + "..."
        
        return full_summary
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old player events to prevent database bloat."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute(
                    'DELETE FROM player_events WHERE timestamp < ?',
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old player events")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
