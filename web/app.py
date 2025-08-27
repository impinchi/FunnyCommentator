"""Flask web application for FunnyCommentator configuration.

This module provides a web-based interface for configuring the FunnyCommentator
system, including server settings, AI configuration, and credential management.
Following PEP 257 for docstring conventions.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.credential_manager import CredentialManager
from src.server_config import ServerConfig


class ConfigWebApp:
    """Flask web application for system configuration."""
    
    def __init__(self):
        """Initialize the Flask web application."""
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')
        self.config_manager = None
        self._setup_routes()
        
        # Add custom Jinja2 filter for cluster assignment
        @self.app.template_filter('get_server_cluster')
        def get_server_cluster(server_name, clusters_dict):
            """Get the cluster assignment for a server."""
            for cluster_name, cluster in clusters_dict.items():
                if cluster.get('servers') and server_name in cluster.get('servers', []):
                    return cluster_name
            return None
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging for the web application using config.json settings."""
        # Load config to get logging level
        log_level = logging.INFO  # Default fallback
        try:
            # Try to load the logging level from config.json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    if 'logging' in config_data and 'level' in config_data['logging']:
                        level_str = config_data['logging']['level'].upper()
                        log_level = getattr(logging, level_str, logging.INFO)
                        print(f"Setting log level to {level_str} from config.json")
        except Exception as e:
            print(f"Could not load logging config, using INFO: {e}")
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        # Only reduce Flask's verbose logging if not in DEBUG mode
        if log_level != logging.DEBUG:
            logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    def _load_config_safe(self) -> Optional[Config]:
        """Safely load configuration, handling errors gracefully.
        
        Returns:
            Config object or None if loading fails
        """
        try:
            # Force reload configuration to pick up external changes
            logging.info(f"Loading configuration... Working directory: {os.getcwd()}")
            
            # If we don't have a config instance yet, create one first
            if not hasattr(self, 'config_manager') or self.config_manager is None:
                logging.info("Creating new Config instance")
                self.config_manager = Config()
            else:
                # Reload existing instance
                logging.info("Reloading existing Config instance")
                self.config_manager = Config.reload()
                # If reload returns None, create a new instance
                if self.config_manager is None:
                    logging.info("Reload returned None, creating new instance")
                    self.config_manager = Config()
            
            config = self.config_manager
            
            # Safely check servers count
            servers_count = 0
            if config and hasattr(config, 'servers') and config.servers:
                servers_count = len(config.servers)
            
            logging.info(f"Configuration loaded successfully. Servers: {servers_count}")
            return config
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            logging.error(f"Exception type: {type(e).__name__}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            
            # Reset the singleton instance so next attempt can start fresh
            Config.reset()
            self.config_manager = None
            
            return None
    
    def _setup_routes(self) -> None:
        """Set up Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            config = self._load_config_safe()
            if not config:
                flash('Configuration could not be loaded. Please check your setup.', 'error')
                return render_template('error.html', 
                                     error="Configuration Error",
                                     message="Could not load system configuration.")
            
            # Get system status
            status = self._get_system_status(config)
            return render_template('dashboard.html', config=config, status=status)
        
        @self.app.route('/servers')
        def servers():
            """Server configuration page."""
            config = self._load_config_safe()
            if not config:
                return redirect(url_for('index'))
            
            return render_template('servers.html', config=config)
        
        @self.app.route('/servers/add', methods=['GET', 'POST'])
        def add_server():
            """Add new server configuration."""
            if request.method == 'POST':
                try:
                    server_data = self._extract_server_data(request.form)
                    self._add_server_to_config(server_data)
                    flash('Server added successfully!', 'success')
                    return redirect(url_for('servers'))
                except Exception as e:
                    flash(f'Error adding server: {str(e)}', 'error')
            
            # Load clusters for the form
            config_data = self._load_raw_config()
            clusters_data = config_data.get('clusters', {})
            
            return render_template('add_server.html', clusters=clusters_data)
        
        @self.app.route('/servers/edit/<server_name>', methods=['GET', 'POST'])
        def edit_server(server_name: str):
            """Edit existing server configuration."""
            config = self._load_config_safe()
            if not config or server_name not in config.servers:
                flash('Server not found.', 'error')
                return redirect(url_for('servers'))
            
            if request.method == 'POST':
                try:
                    server_data = self._extract_server_data(request.form)
                    self._update_server_in_config(server_name, server_data)
                    flash('Server updated successfully!', 'success')
                    return redirect(url_for('servers'))
                except Exception as e:
                    flash(f'Error updating server: {str(e)}', 'error')
            
            server = config.servers[server_name]
            return render_template('edit_server.html', server=server)
        
        @self.app.route('/servers/delete/<server_name>', methods=['POST'])
        def delete_server(server_name: str):
            """Delete server configuration."""
            try:
                self._delete_server_from_config(server_name)
                flash('Server deleted successfully!', 'success')
            except Exception as e:
                flash(f'Error deleting server: {str(e)}', 'error')
            
            return redirect(url_for('servers'))
        
        @self.app.route('/clusters')
        def clusters():
            """Cluster management page."""
            config = self._load_config_safe()
            if not config:
                return redirect(url_for('index'))
            
            # For cluster management, use raw config to show ALL clusters
            # (including empty ones that need to be managed)
            raw_config = self._load_raw_config()
            clusters_data = raw_config.get('clusters', {})
            logging.debug(f"Raw clusters data being passed to template: {clusters_data}")
            
            return render_template('clusters.html', 
                                 config=config, 
                                 clusters=clusters_data)
        
        @self.app.route('/clusters/add', methods=['GET', 'POST'])
        def add_cluster():
            """Add new cluster."""
            if request.method == 'POST':
                try:
                    cluster_data = self._extract_cluster_data(request.form)
                    self._add_cluster_to_config(cluster_data)
                    flash('Cluster added successfully!', 'success')
                    return redirect(url_for('clusters'))
                except Exception as e:
                    flash(f'Error adding cluster: {str(e)}', 'error')
            
            config = self._load_config_safe()
            return render_template('add_cluster.html', config=config)
        
        @self.app.route('/clusters/edit/<cluster_name>', methods=['GET', 'POST'])
        def edit_cluster(cluster_name: str):
            """Edit cluster configuration."""
            config_data = self._load_raw_config()
            clusters = config_data.get('clusters', {})
            
            if cluster_name not in clusters:
                flash('Cluster not found!', 'error')
                return redirect(url_for('clusters'))
            
            if request.method == 'POST':
                try:
                    cluster_data = self._extract_cluster_data(request.form)
                    self._update_cluster_in_config(cluster_name, cluster_data)
                    flash('Cluster updated successfully!', 'success')
                    return redirect(url_for('clusters'))
                except Exception as e:
                    flash(f'Error updating cluster: {str(e)}', 'error')
            
            config = self._load_config_safe()
            return render_template('edit_cluster.html', 
                                 config=config, 
                                 cluster_name=cluster_name,
                                 cluster=clusters[cluster_name])
        
        @self.app.route('/clusters/delete/<cluster_name>', methods=['POST'])
        def delete_cluster(cluster_name: str):
            """Delete cluster configuration."""
            try:
                self._delete_cluster_from_config(cluster_name)
                flash('Cluster deleted successfully!', 'success')
            except Exception as e:
                flash(f'Error deleting cluster: {str(e)}', 'error')
            
            return redirect(url_for('clusters'))
        
        @self.app.route('/servers/assign', methods=['POST'])
        def assign_server():
            """Assign server to cluster."""
            try:
                server_name = request.form.get('server_name')
                cluster_name = request.form.get('cluster_name')
                
                if not server_name or not cluster_name:
                    flash('Server name and cluster name are required.', 'error')
                    return redirect(url_for('clusters'))
                
                self._assign_server_to_cluster(server_name, cluster_name)
                flash(f'Server "{server_name}" assigned to cluster "{cluster_name}" successfully!', 'success')
            except Exception as e:
                flash(f'Error assigning server: {str(e)}', 'error')
            
            return redirect(url_for('clusters'))
        
        @self.app.route('/ai')
        def ai_config():
            """AI configuration page."""
            config = self._load_config_safe()
            if not config:
                return redirect(url_for('index'))
            
            return render_template('ai_config.html', config=config)
        
        @self.app.route('/ai/update', methods=['POST'])
        def update_ai_config():
            """Update AI configuration."""
            try:
                ai_data = self._extract_ai_data(request.form)
                self._update_ai_config(ai_data)
                flash('AI configuration updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating AI configuration: {str(e)}', 'error')
            
            return redirect(url_for('ai_config'))
        
        @self.app.route('/credentials')
        def credentials():
            """Enhanced enterprise-grade credential management page."""
            try:
                # Get all configured servers from raw config (includes missing credential servers)
                raw_config = self._load_raw_config()
                all_servers_config = raw_config.get('servers', [])
                
                # Get loaded config (only servers with valid credentials)
                loaded_config = self._load_config_safe()
                loaded_servers = loaded_config.servers if loaded_config and hasattr(loaded_config, 'servers') else {}
                
                # Comprehensive credential analysis
                credential_analysis = {
                    'discord_token': {
                        'configured': bool(CredentialManager.get_discord_token()),
                        'required': True,
                        'status': 'valid' if CredentialManager.get_discord_token() else 'missing'
                    },
                    'servers': {},
                    'missing_servers': [],
                    'health_check': {
                        'total_servers_configured': len(all_servers_config),
                        'total_servers_loaded': len(loaded_servers),
                        'servers_with_missing_credentials': 0,
                        'overall_health': 'healthy'
                    }
                }
                
                # Analyze each server from config
                for server_config in all_servers_config:
                    server_name = server_config.get('name', 'Unknown Server')
                    rcon_password = CredentialManager.get_rcon_password(server_name)
                    is_configured = bool(rcon_password)
                    is_loaded = server_name in loaded_servers
                    
                    # Determine server status
                    if is_configured and is_loaded:
                        status = 'valid'
                    elif not is_configured:
                        status = 'missing_credential'
                        credential_analysis['missing_servers'].append({
                            'name': server_name,
                            'map_name': server_config.get('map_name', 'Unknown'),
                            'rcon_host': server_config.get('rcon_host', 'Unknown'),
                            'rcon_port': server_config.get('rcon_port', 'Unknown'),
                            'issue': 'RCON password not found in credential store'
                        })
                        credential_analysis['health_check']['servers_with_missing_credentials'] += 1
                    else:
                        status = 'error'  # Configured but not loaded (other issues)
                    
                    credential_analysis['servers'][server_name] = {
                        'configured': is_configured,
                        'loaded': is_loaded,
                        'status': status,
                        'server_config': server_config
                    }
                
                # Calculate overall health
                missing_count = credential_analysis['health_check']['servers_with_missing_credentials']
                total_count = credential_analysis['health_check']['total_servers_configured']
                
                if missing_count == 0 and credential_analysis['discord_token']['configured']:
                    credential_analysis['health_check']['overall_health'] = 'healthy'
                elif missing_count == total_count or not credential_analysis['discord_token']['configured']:
                    credential_analysis['health_check']['overall_health'] = 'critical'
                else:
                    credential_analysis['health_check']['overall_health'] = 'warning'
                
                return render_template('credentials.html', credential_analysis=credential_analysis)
                
            except Exception as e:
                logging.error(f"Error in credentials page: {e}")
                # Fallback to basic mode
                credentials_status = {
                    'discord_token': bool(CredentialManager.get_discord_token()),
                    'servers': {}
                }
                config = self._load_config_safe()
                if config and hasattr(config, 'servers') and config.servers:
                    for server_name in config.servers:
                        credentials_status['servers'][server_name] = bool(
                            CredentialManager.get_rcon_password(server_name)
                        )
                
                return render_template('credentials.html', 
                                     credentials_status=credentials_status,
                                     error_mode=True,
                                     error_message=str(e))
        
        @self.app.route('/credentials/update', methods=['POST'])
        def update_credentials():
            """Enhanced enterprise-grade credential update with batch operations."""
            success_count = 0
            error_count = 0
            operations_log = []
            
            try:
                # Update Discord token if provided
                discord_token = request.form.get('discord_token', '').strip()
                if discord_token:
                    try:
                        # Validate token format (basic check)
                        if len(discord_token) < 50:
                            raise ValueError("Discord token appears to be too short")
                        
                        CredentialManager.store_discord_token(discord_token)
                        flash('Discord token updated successfully!', 'success')
                        operations_log.append(f"✓ Discord token updated")
                        success_count += 1
                    except Exception as e:
                        flash(f'Error updating Discord token: {str(e)}', 'error')
                        operations_log.append(f"✗ Discord token failed: {str(e)}")
                        error_count += 1
                
                # Get all servers from raw config for comprehensive update
                try:
                    raw_config = self._load_raw_config()
                    all_servers = raw_config.get('servers', [])
                except Exception:
                    # Fallback to loaded config if raw config fails
                    config = self._load_config_safe()
                    all_servers = []
                    if config and hasattr(config, 'servers'):
                        for server_name in config.servers:
                            all_servers.append({'name': server_name})
                
                # Update RCON passwords for all configured servers
                for server_info in all_servers:
                    server_name = server_info.get('name')
                    if not server_name:
                        continue
                        
                    password_field = f'rcon_password_{server_name.lower().replace(" ", "_")}'
                    password = request.form.get(password_field, '').strip()
                    
                    if password:
                        try:
                            # Validate password (basic check)
                            if len(password) < 4:
                                raise ValueError("Password appears to be too short")
                            
                            CredentialManager.store_rcon_password(server_name, password)
                            flash(f'RCON password for {server_name} updated successfully!', 'success')
                            operations_log.append(f"✓ {server_name} RCON password updated")
                            success_count += 1
                        except Exception as e:
                            flash(f'Error updating RCON password for {server_name}: {str(e)}', 'error')
                            operations_log.append(f"✗ {server_name} RCON password failed: {str(e)}")
                            error_count += 1
                
                # Batch operation summary
                if success_count > 0 or error_count > 0:
                    if error_count == 0:
                        flash(f'✓ All {success_count} credential operations completed successfully!', 'success')
                    elif success_count == 0:
                        flash(f'✗ All {error_count} credential operations failed!', 'error')
                    else:
                        flash(f'⚠ Mixed results: {success_count} successful, {error_count} failed', 'warning')
                
                # Log operations for audit trail
                if operations_log:
                    logging.info(f"Credential update operations: {'; '.join(operations_log)}")
                
                # Force config reload to pick up new credentials
                try:
                    config = self._load_config_safe()
                    if config:
                        flash('Configuration reloaded with new credentials', 'info')
                        logging.info("Successfully reloaded configuration after credential update")
                except Exception as e:
                    flash(f'Warning: Could not reload configuration: {str(e)}', 'warning')
                    logging.warning(f"Failed to reload configuration after credential update: {e}")
                
            except Exception as e:
                flash(f'Critical error during credential update: {str(e)}', 'error')
                logging.error(f"Critical error in credential update: {e}")
            
            return redirect(url_for('credentials'))

        @self.app.route('/credentials/test', methods=['POST'])
        def test_credentials():
            """Test credential connectivity and validation."""
            test_results = {
                'discord_token': {'status': 'unknown', 'message': ''},
                'servers': {},
                'overall_status': 'unknown'
            }
            
            try:
                # Test Discord token
                discord_token = CredentialManager.get_discord_token()
                if discord_token:
                    try:
                        # Basic token format validation
                        if len(discord_token) >= 50 and '.' in discord_token:
                            test_results['discord_token'] = {
                                'status': 'valid', 
                                'message': 'Token format appears valid (full connectivity test requires Discord API)'
                            }
                        else:
                            test_results['discord_token'] = {
                                'status': 'warning', 
                                'message': 'Token format may be invalid'
                            }
                    except Exception as e:
                        test_results['discord_token'] = {
                            'status': 'error', 
                            'message': f'Error validating token: {str(e)}'
                        }
                else:
                    test_results['discord_token'] = {
                        'status': 'missing', 
                        'message': 'Discord token not found in credential store'
                    }
                
                # Test RCON credentials
                raw_config = self._load_raw_config()
                all_servers = raw_config.get('servers', [])
                
                for server_config in all_servers:
                    server_name = server_config.get('name', 'Unknown')
                    try:
                        password = CredentialManager.get_rcon_password(server_name)
                        if password:
                            # Basic validation - could be enhanced with actual RCON connection test
                            test_results['servers'][server_name] = {
                                'status': 'valid',
                                'message': f'Credential found (length: {len(password)} chars)',
                                'host': server_config.get('rcon_host', 'Unknown'),
                                'port': server_config.get('rcon_port', 'Unknown')
                            }
                        else:
                            test_results['servers'][server_name] = {
                                'status': 'missing',
                                'message': 'RCON password not found in credential store',
                                'host': server_config.get('rcon_host', 'Unknown'),
                                'port': server_config.get('rcon_port', 'Unknown')
                            }
                    except Exception as e:
                        test_results['servers'][server_name] = {
                            'status': 'error',
                            'message': f'Error testing credential: {str(e)}',
                            'host': server_config.get('rcon_host', 'Unknown'),
                            'port': server_config.get('rcon_port', 'Unknown')
                        }
                
                # Calculate overall status
                all_valid = True
                any_missing = False
                
                if test_results['discord_token']['status'] in ['missing', 'error']:
                    all_valid = False
                    any_missing = True
                
                for server_test in test_results['servers'].values():
                    if server_test['status'] in ['missing', 'error']:
                        all_valid = False
                        if server_test['status'] == 'missing':
                            any_missing = True
                
                if all_valid:
                    test_results['overall_status'] = 'healthy'
                elif any_missing:
                    test_results['overall_status'] = 'missing_credentials'
                else:
                    test_results['overall_status'] = 'error'
                
                return jsonify(test_results)
                
            except Exception as e:
                logging.error(f"Error testing credentials: {e}")
                return jsonify({
                    'error': str(e),
                    'overall_status': 'error'
                }), 500

        @self.app.route('/credentials/export', methods=['POST'])
        def export_credentials():
            """Export credential configuration template for enterprise deployment."""
            try:
                raw_config = self._load_raw_config()
                all_servers = raw_config.get('servers', [])
                
                export_data = {
                    'credential_template': {
                        'discord_token': {
                            'required': True,
                            'description': 'Discord bot token for sending notifications',
                            'current_status': 'configured' if CredentialManager.get_discord_token() else 'missing'
                        },
                        'rcon_passwords': {}
                    },
                    'deployment_info': {
                        'total_servers': len(all_servers),
                        'missing_credentials': 0,
                        'export_timestamp': datetime.now().isoformat()
                    }
                }
                
                for server_config in all_servers:
                    server_name = server_config.get('name', 'Unknown')
                    has_credential = bool(CredentialManager.get_rcon_password(server_name))
                    
                    export_data['credential_template']['rcon_passwords'][server_name] = {
                        'required': True,
                        'description': f'RCON password for {server_name} server',
                        'host': server_config.get('rcon_host', 'Unknown'),
                        'port': server_config.get('rcon_port', 'Unknown'),
                        'current_status': 'configured' if has_credential else 'missing'
                    }
                    
                    if not has_credential:
                        export_data['deployment_info']['missing_credentials'] += 1
                
                return jsonify(export_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/scheduler')
        def scheduler_config():
            """Scheduler configuration page."""
            config = self._load_config_safe()
            if not config:
                return redirect(url_for('index'))
            
            return render_template('scheduler.html', config=config)
        
        @self.app.route('/scheduler/update', methods=['POST'])
        def update_scheduler():
            """Update scheduler configuration."""
            try:
                scheduler_data = self._extract_scheduler_data(request.form)
                self._update_scheduler_config(scheduler_data)
                
                # Try to reload the scheduler in the running application
                try:
                    import requests
                    reload_response = requests.post('http://127.0.0.1:5000/api/scheduler/reload', timeout=10)
                    if reload_response.status_code == 200:
                        reload_data = reload_response.json()
                        if reload_data.get('success'):
                            flash(f'Scheduler configuration updated and reloaded successfully! New schedule: {reload_data.get("schedule", "unknown")}', 'success')
                        else:
                            flash(f'Configuration updated but reload failed: {reload_data.get("message", "unknown error")}', 'warning')
                    else:
                        flash('Configuration updated but could not reload scheduler. Please restart the application to apply changes.', 'warning')
                except requests.exceptions.ConnectionError:
                    flash('Configuration updated but main application is not running. Changes will apply on next startup.', 'info')
                except Exception as e:
                    flash(f'Configuration updated but reload encountered an error: {str(e)}', 'warning')
                
            except Exception as e:
                flash(f'Error updating scheduler: {str(e)}', 'error')
            
            return redirect(url_for('scheduler_config'))
        
        @self.app.route('/api/scheduler/reload', methods=['POST'])
        def reload_scheduler():
            """Reload scheduler configuration in the running application."""
            try:
                import os
                import time
                from pathlib import Path
                
                # Create signal file to request scheduler reload
                signal_file = Path("scheduler_reload.signal")
                signal_file.write_text(str(time.time()))
                
                # Wait for response file (with timeout)
                response_file = Path("scheduler_reload.response")
                start_time = time.time()
                timeout = 10  # 10 second timeout
                
                while time.time() - start_time < timeout:
                    if response_file.exists():
                        try:
                            import json
                            with response_file.open('r') as f:
                                response_data = json.load(f)
                            
                            # Clean up response file
                            response_file.unlink()
                            
                            return jsonify({
                                'success': response_data.get('success', False),
                                'message': f"Scheduler reloaded successfully. New schedule: {response_data.get('schedule', 'unknown')}" if response_data.get('success') else 'Failed to reload scheduler',
                                'schedule': response_data.get('schedule')
                            })
                        except Exception as e:
                            return jsonify({
                                'success': False,
                                'message': f'Error reading reload response: {str(e)}'
                            }), 500
                    
                    time.sleep(0.5)  # Check every 500ms
                
                # Timeout - clean up signal file if it still exists
                if signal_file.exists():
                    signal_file.unlink()
                    
                return jsonify({
                    'success': False,
                    'message': 'Timeout waiting for application response. Is the main application running?'
                }), 408
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error reloading scheduler: {str(e)}'
                }), 500
        
        @self.app.route('/scheduler/test', methods=['POST'])
        def test_scheduler():
            """Manually trigger the scheduler job for testing."""
            try:
                import asyncio
                import threading
                import time
                
                result = {'success': False, 'message': 'Test started'}
                
                def run_async_job():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self.main_app.rcon_summary_job())
                            result['success'] = True
                            result['message'] = 'Summary job completed successfully'
                        finally:
                            loop.close()
                    except Exception as e:
                        logging.error(f"Manual scheduler test failed: {e}")
                        result['success'] = False
                        result['error'] = str(e)
                
                # Run in background thread to avoid blocking
                thread = threading.Thread(target=run_async_job)
                thread.daemon = True
                thread.start()
                
                # Give it a moment to start, then return
                time.sleep(0.5)
                return jsonify({'success': True, 'message': 'Summary job started in background. Check logs and Discord for results.'})
                
            except Exception as e:
                logging.error(f"Failed to start manual scheduler test: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for system status."""
            config = self._load_config_safe()
            if not config:
                return jsonify({'error': 'Configuration not available'}), 500
            
            status = self._get_system_status(config)
            return jsonify(status)
        
        @self.app.route('/system')
        def system_info():
            """Enterprise system information page."""
            config = self._load_config_safe()
            if not config:
                return redirect(url_for('index'))
            
            # Get comprehensive system status
            status = self._get_system_status(config)
            return render_template('system_info.html', config=config, status=status)
        
        @self.app.route('/api/system/validate')
        def api_system_validate():
            """API endpoint for backend validation."""
            try:
                credential_manager = CredentialManager.create_manager(enterprise_mode=False)
                validation_results = credential_manager.validate_credential_access()
                return jsonify({
                    'success': True,
                    'validation': validation_results,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/process/status')
        def api_process_status():
            """API endpoint for process status."""
            try:
                from src.process_manager import ProcessManager
                process_manager = ProcessManager()
                status = process_manager.get_process_status()
                
                return jsonify({
                    'success': True,
                    'process': {
                        'is_running': status.is_running,
                        'pid': status.pid,
                        'cpu_percent': status.cpu_percent,
                        'memory_percent': status.memory_percent,
                        'uptime_seconds': status.uptime_seconds,
                        'uptime_formatted': process_manager.format_uptime(status.uptime_seconds) if status.uptime_seconds else None,
                        'status': status.status
                    },
                    'system': {
                        'cpu_percent': status.system_cpu_percent,
                        'memory_percent': status.system_memory_percent
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/process/start', methods=['POST'])
        def api_process_start():
            """API endpoint to start the main application."""
            try:
                from src.process_manager import ProcessManager
                process_manager = ProcessManager()
                result = process_manager.start_application()
                
                return jsonify({
                    'success': result['success'],
                    'message': result['message'],
                    'process': {
                        'is_running': result['status'].is_running,
                        'pid': result['status'].pid,
                        'status': result['status'].status
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/process/stop', methods=['POST'])
        def api_process_stop():
            """API endpoint to stop the main application."""
            try:
                from src.process_manager import ProcessManager
                process_manager = ProcessManager()
                result = process_manager.stop_application()
                
                return jsonify({
                    'success': result['success'],
                    'message': result['message'],
                    'process': {
                        'is_running': result['status'].is_running,
                        'pid': result['status'].pid,
                        'status': result['status'].status
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/process/restart', methods=['POST'])
        def api_process_restart():
            """API endpoint to restart the main application."""
            try:
                from src.process_manager import ProcessManager
                process_manager = ProcessManager()
                result = process_manager.restart_application()
                
                return jsonify({
                    'success': result['success'],
                    'message': result['message'],
                    'process': {
                        'is_running': result['status'].is_running,
                        'pid': result['status'].pid,
                        'status': result['status'].status
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/process/logs')
        def api_process_logs():
            """API endpoint for process logs."""
            try:
                from src.process_manager import ProcessManager
                process_manager = ProcessManager()
                lines = request.args.get('lines', 50, type=int)
                logs = process_manager.get_application_logs(lines)
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'lines': lines,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # Log Management routes
        @self.app.route('/logs')
        def log_management():
            """Log management page."""
            config = self._load_config_safe()
            if not config:
                return redirect(url_for('index'))
            
            try:
                # Import here to avoid circular imports
                from src.log_manager import LogManager
                log_manager = LogManager(
                    retention_days=getattr(config, 'log_retention_days', 30),
                    max_size_mb=getattr(config, 'log_max_size_mb', 100)
                )
                
                log_status = {
                    "sizes": log_manager.get_log_sizes(),
                    "files_needing_rotation": log_manager.check_log_rotation_needed(),
                    "retention_days": log_manager.retention_days,
                    "max_size_mb": log_manager.max_size_mb
                }
                
                return render_template('log_management.html', config=config, log_status=log_status)
            except Exception as e:
                flash(f'Error loading log management: {e}', 'error')
                return redirect(url_for('dashboard'))
        
        @self.app.route('/api/logs/status')
        def api_logs_status():
            """API endpoint for log status."""
            try:
                from src.log_manager import LogManager
                config = self._load_config_safe()
                
                log_manager = LogManager(
                    retention_days=getattr(config, 'log_retention_days', 30),
                    max_size_mb=getattr(config, 'log_max_size_mb', 100)
                )
                
                return jsonify({
                    'success': True,
                    'status': {
                        "sizes": log_manager.get_log_sizes(),
                        "files_needing_rotation": log_manager.check_log_rotation_needed(),
                        "retention_days": log_manager.retention_days,
                        "max_size_mb": log_manager.max_size_mb
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/logs/cleanup', methods=['POST'])
        def api_logs_cleanup():
            """API endpoint for manual log cleanup."""
            try:
                from src.log_manager import LogManager
                config = self._load_config_safe()
                
                force_clear = request.json.get('force_clear', False) if request.json else False
                
                log_manager = LogManager(
                    retention_days=getattr(config, 'log_retention_days', 30),
                    max_size_mb=getattr(config, 'log_max_size_mb', 100)
                )
                
                results = log_manager.manual_cleanup(force_clear)
                
                return jsonify({
                    'success': True,
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # IP Monitor routes
        @self.app.route('/ip_monitor')
        def ip_monitor():
            """IP Monitor configuration and status page."""
            config = self._load_config_safe()
            if not config:
                return redirect(url_for('index'))
            
            # Get IP monitor status
            ip_status = self._get_ip_monitor_status()
            return render_template('ip_monitor.html', config=config, ip_status=ip_status)
        
        @self.app.route('/api/ip/status')
        def api_ip_status():
            """API endpoint for IP monitor status."""
            try:
                status = self._get_ip_monitor_status()
                return jsonify({
                    'success': True,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/ip/config', methods=['GET', 'POST'])
        def api_ip_config():
            """API endpoint for IP monitor configuration."""
            if request.method == 'GET':
                try:
                    config = self._load_config_safe()
                    if not config:
                        return jsonify({'error': 'Configuration not available'}), 500
                    
                    # Get IP monitor config from the Config object attributes
                    ip_config = {
                        'check_interval_seconds': getattr(config, 'ip_retry_seconds', 1800),
                        'last_known_ip': getattr(config, 'previous_ip', None),
                        'discord_notifications': True,  # Default value 
                        'auto_monitoring': True  # Default value
                    }
                    return jsonify({
                        'success': True,
                        'config': ip_config,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': str(e)
                    }), 500
            
            elif request.method == 'POST':
                try:
                    data = request.get_json()
                    if not data:
                        return jsonify({'error': 'No data provided'}), 400
                    
                    # Update IP monitor configuration
                    self._update_ip_monitor_config(data)
                    
                    return jsonify({
                        'success': True,
                        'message': 'IP monitor configuration updated successfully',
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }), 500
        
        @self.app.route('/api/ip/check', methods=['POST'])
        def api_ip_check():
            """API endpoint for manual IP check."""
            try:
                from src.ip_monitor_manager import IPMonitorManager
                from src.database import DatabaseManager
                
                # Get dependencies
                config = self._load_config_safe()
                if not config:
                    return jsonify({'error': 'Configuration not available'}), 500
                
                # Create managers
                database_manager = DatabaseManager(
                    config.db_path,
                    {}  # server_tables - not needed for IP operations
                )
                
                # Create IP monitor (Discord handled via HTTP API)
                ip_manager = IPMonitorManager(self, database_manager, None)
                
                # Perform IP check
                import asyncio
                result = asyncio.run(ip_manager.perform_ip_check_and_notify())
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/ip/history')
        def api_ip_history():
            """API endpoint for IP change history."""
            try:
                from src.database import DatabaseManager
                
                config = self._load_config_safe()
                if not config:
                    return jsonify({'error': 'Configuration not available'}), 500
                
                database_manager = DatabaseManager(
                    config.db_path,
                    {}  # server_tables - not needed for IP operations
                )
                
                limit = request.args.get('limit', 50, type=int)
                history = database_manager.get_ip_history(limit)
                
                return jsonify({
                    'success': True,
                    'history': history,
                    'count': len(history),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/ip/update', methods=['POST'])
        def api_ip_update():
            """API endpoint for manual IP update."""
            try:
                data = request.get_json()
                if not data or 'ip_address' not in data:
                    return jsonify({'error': 'IP address is required'}), 400
                
                from src.ip_monitor_manager import IPMonitorManager
                from src.database import DatabaseManager
                
                # Get dependencies
                config = self._load_config_safe()
                if not config:
                    return jsonify({'error': 'Configuration not available'}), 500
                
                # Create managers
                database_manager = DatabaseManager(
                    config.db_path,
                    {}
                )
                
                # Create IP monitor (Discord handled via HTTP API)  
                ip_manager = IPMonitorManager(self, database_manager, None)
                
                # Update IP manually
                success = ip_manager.update_last_known_ip(data['ip_address'], 'manual')
                
                return jsonify({
                    'success': success,
                    'message': 'IP address updated successfully' if success else 'No change detected',
                    'new_ip': data['ip_address'],
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors."""
            return render_template('error.html', 
                                 error="Page Not Found",
                                 message="The requested page could not be found."), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            return render_template('error.html',
                                 error="Internal Server Error", 
                                 message="An internal error occurred."), 500
    
    def _get_system_status(self, config: Config) -> Dict[str, Any]:
        """Get comprehensive system status including enterprise credential info.
        
        Args:
            config: Configuration object
            
        Returns:
            Dictionary containing system status information with enterprise features
        """
        try:
            # Create credential manager (use standard mode for compatibility)
            credential_manager = CredentialManager.create_manager(enterprise_mode=False)
            
            # Get system information
            system_info = credential_manager.get_system_info()
            
            # Validate credential backends
            backend_validation = credential_manager.validate_credential_access()
            
            # Check credential status
            discord_token_status = bool(credential_manager.get_credential(CredentialManager.DISCORD_TOKEN))
            
            # Get stored credentials count
            # Get stored credentials count
            try:
                credentials_count = credential_manager.count_stored_credentials()
            except Exception:
                credentials_count = 0
            
            return {
                'servers_count': len(config.servers) if hasattr(config, 'servers') and config.servers else 0,
                'clusters_count': len(config.clusters) if hasattr(config, 'clusters') and config.clusters else 0,
                'discord_configured': discord_token_status,
                'ai_model': config.ollama_model,
                'scheduler_time': f"{config.scheduler_logs_hour:02d}:{config.scheduler_logs_minute:02d}",
                'database_path': config.db_path,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                # Enterprise credential features
                'system_info': system_info,
                'backend_validation': backend_validation,
                'stored_credentials_count': credentials_count,
                'platform_support': {
                    'platform': system_info.get('platform', 'unknown'),
                    'keyring_backend': system_info.get('keyring_backend', 'unknown'),
                    'keyring_available': backend_validation.get('keyring_available', False),
                    'fallback_available': backend_validation.get('fallback_available', False),
                    'enterprise_features': system_info.get('enterprise_mode', False)
                }
            }
        except Exception as e:
            logging.error(f"Error getting system status: {e}")
            return {
                'servers_count': len(config.servers) if hasattr(config, 'servers') and config.servers else 0,
                'clusters_count': len(config.clusters) if hasattr(config, 'clusters') and config.clusters else 0,
                'discord_configured': False,
                'ai_model': config.ollama_model if hasattr(config, 'ollama_model') else 'Error loading',
                'scheduler_time': 'Error loading',
                'database_path': 'Error loading',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
                'platform_support': {
                    'platform': 'unknown',
                    'keyring_backend': 'error',
                    'keyring_available': False,
                    'fallback_available': False,
                    'enterprise_features': False
                }
            }
    
    def _extract_server_data(self, form_data) -> Dict[str, Any]:
        """Extract server data from form submission.
        
        Args:
            form_data: Flask request form data
            
        Returns:
            Dictionary containing server configuration data
        """
        # Extract player names from comma-separated string
        player_names_str = form_data.get('player_names', '')
        player_names = [name.strip() for name in player_names_str.split(',') if name.strip()]
        
        return {
            'name': form_data.get('name', '').strip(),
            'map_name': form_data.get('map_name', '').strip(),
            'rcon_host': form_data.get('rcon_host', '127.0.0.1').strip(),
            'rcon_port': int(form_data.get('rcon_port', 27015)),
            'max_wild_dino_level': int(form_data.get('max_wild_dino_level', 150)),
            'tribe_name': form_data.get('tribe_name', '').strip(),
            'player_names': player_names,
            'is_pve': form_data.get('is_pve') == 'on',
            'cluster': form_data.get('cluster', '').strip(),
            'log_file_path': form_data.get('log_file_path', '').strip() or None
        }
    
    def _extract_ai_data(self, form_data) -> Dict[str, Any]:
        """Extract AI configuration data from form submission."""
        return {
            'ollama_url': form_data.get('ollama_url', '').strip(),
            'ollama_model': form_data.get('ollama_model', '').strip(),
            'ollama_start_cmd': form_data.get('ollama_start_cmd', '').strip(),
            'timeout_seconds': int(form_data.get('timeout_seconds', 300)),
            'startup_timeout_seconds': int(form_data.get('startup_timeout_seconds', 300)),
            'input_token_size': int(form_data.get('input_token_size', 16000)),
            'min_output_tokens': int(form_data.get('min_output_tokens', 64)),
            'max_output_tokens': int(form_data.get('max_output_tokens', 512)),
            'safety_buffer': int(form_data.get('safety_buffer', 48)),
            'tokenizer_model': form_data.get('tokenizer_model', 'gpt-3.5-turbo').strip(),
            'enable_reasoning': form_data.get('enable_reasoning', 'false').lower() == 'true',
            'ai_tone': form_data.get('ai_tone', '').strip() or "You are expected to be sarcastic, hilarious and witty while being insulting and rude with mistakes."
        }
    
    def _extract_scheduler_data(self, form_data) -> Dict[str, Any]:
        """Extract scheduler configuration data from form submission."""
        return {
            'logs_summary_hour': int(form_data.get('logs_summary_hour', 8)),
            'logs_summary_minute': int(form_data.get('logs_summary_minute', 0))
        }
    
    def _add_server_to_config(self, server_data: Dict[str, Any]) -> None:
        """Add a new server to the configuration."""
        # Load current config
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add new server
        new_server = {
            'name': server_data['name'],
            'map_name': server_data['map_name'],
            'rcon_host': server_data['rcon_host'],
            'rcon_port': server_data['rcon_port'],
            'rcon_password': 'STORED_IN_KEYRING',
            'max_wild_dino_level': server_data['max_wild_dino_level'],
            'tribe_name': server_data['tribe_name'],
            'player_names': server_data['player_names'],
            'is_pve': server_data['is_pve']
        }
        
        # Add log_file_path if provided
        if server_data.get('log_file_path'):
            new_server['log_file_path'] = server_data['log_file_path']
        
        config['servers'].append(new_server)
        
        # Handle cluster assignment
        if 'cluster' in server_data and server_data['cluster']:
            cluster_name = server_data['cluster']
            if 'clusters' not in config:
                config['clusters'] = {}
            
            if cluster_name in config['clusters']:
                if 'servers' not in config['clusters'][cluster_name]:
                    config['clusters'][cluster_name]['servers'] = []
                
                if server_data['name'] not in config['clusters'][cluster_name]['servers']:
                    config['clusters'][cluster_name]['servers'].append(server_data['name'])
        
        # Save config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _update_server_in_config(self, server_name: str, server_data: Dict[str, Any]) -> None:
        """Update an existing server in the configuration."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Find and update server
        for i, server in enumerate(config['servers']):
            if server['name'] == server_name:
                config['servers'][i].update({
                    'name': server_data['name'],
                    'map_name': server_data['map_name'],
                    'rcon_host': server_data['rcon_host'],
                    'rcon_port': server_data['rcon_port'],
                    'max_wild_dino_level': server_data['max_wild_dino_level'],
                    'tribe_name': server_data['tribe_name'],
                    'player_names': server_data['player_names'],
                    'is_pve': server_data['is_pve']
                })
                
                # Handle log_file_path - add if provided, remove if empty
                if server_data.get('log_file_path'):
                    config['servers'][i]['log_file_path'] = server_data['log_file_path']
                elif 'log_file_path' in config['servers'][i]:
                    del config['servers'][i]['log_file_path']
                    
                break
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _delete_server_from_config(self, server_name: str) -> None:
        """Delete a server from the configuration."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Remove server
        config['servers'] = [s for s in config['servers'] if s['name'] != server_name]
        
        # Also remove from clusters
        if 'clusters' in config:
            for cluster_name, cluster_data in config['clusters'].items():
                if 'servers' in cluster_data and server_name in cluster_data['servers']:
                    cluster_data['servers'].remove(server_name)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _extract_cluster_data(self, form_data) -> Dict[str, Any]:
        """Extract cluster data from form submission."""
        return {
            'name': form_data['name'].strip(),
            'description': form_data.get('description', '').strip(),
            'host': form_data['host'].strip(),
            'servers': []  # Start with empty server list
        }
    
    def _add_cluster_to_config(self, cluster_data: Dict[str, Any]) -> None:
        """Add a new cluster to the configuration."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Initialize clusters section if it doesn't exist
        if 'clusters' not in config:
            config['clusters'] = {}
        
        # Add new cluster
        config['clusters'][cluster_data['name']] = {
            'description': cluster_data['description'],
            'host': cluster_data['host'],
            'servers': cluster_data['servers']
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _update_cluster_in_config(self, cluster_name: str, cluster_data: Dict[str, Any]) -> None:
        """Update cluster configuration."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'clusters' not in config:
            config['clusters'] = {}
        
        # Update cluster (preserve existing servers if not specified)
        if cluster_name in config['clusters']:
            existing_servers = config['clusters'][cluster_name].get('servers', [])
        else:
            existing_servers = []
        
        config['clusters'][cluster_data['name']] = {
            'description': cluster_data['description'],
            'host': cluster_data['host'],
            'servers': cluster_data.get('servers', existing_servers)
        }
        
        # If cluster name changed, remove old entry
        if cluster_name != cluster_data['name'] and cluster_name in config['clusters']:
            del config['clusters'][cluster_name]
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _delete_cluster_from_config(self, cluster_name: str) -> None:
        """Delete a cluster from the configuration."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'clusters' in config and cluster_name in config['clusters']:
            del config['clusters'][cluster_name]
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _assign_server_to_cluster(self, server_name: str, cluster_name: str) -> None:
        """Assign a server to a cluster, removing it from any previous cluster."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Ensure clusters section exists
        if 'clusters' not in config:
            config['clusters'] = {}
        
        # Remove server from all clusters first
        for cluster in config['clusters'].values():
            if 'servers' in cluster and server_name in cluster['servers']:
                cluster['servers'].remove(server_name)
        
        # Ensure target cluster exists and has servers list
        if cluster_name not in config['clusters']:
            config['clusters'][cluster_name] = {
                'description': f'Cluster {cluster_name}',
                'servers': []
            }
        elif 'servers' not in config['clusters'][cluster_name]:
            config['clusters'][cluster_name]['servers'] = []
        
        # Add server to target cluster
        if server_name not in config['clusters'][cluster_name]['servers']:
            config['clusters'][cluster_name]['servers'].append(server_name)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _load_raw_config(self) -> Dict[str, Any]:
        """Load raw configuration from JSON file."""
        try:
            config_path = self._get_config_path()
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load raw config: {e}")
            return {}
    
    def _update_ai_config(self, ai_data: Dict[str, Any]) -> None:
        """Update AI configuration."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        config['ai'].update(ai_data)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _get_config_path(self) -> str:
        """Get the correct path to config.json file."""
        from pathlib import Path
        config_paths = [
            'config.json',
            '../config.json',
            Path(__file__).parent.parent / 'config.json'
        ]
        
        for config_path in config_paths:
            if Path(config_path).exists():
                return str(config_path)
        
        raise FileNotFoundError(f"Config file not found in any of: {config_paths}")
    
    def _update_scheduler_config(self, scheduler_data: Dict[str, Any]) -> None:
        """Update scheduler configuration."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        config['scheduler'].update(scheduler_data)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _get_ip_monitor_status(self) -> Dict:
        """Get current IP monitor status and configuration."""
        try:
            from src.ip_monitor_manager import IPMonitorManager
            from src.database import DatabaseManager
            
            config = self._load_config_safe()
            if not config:
                return {'error': 'Configuration not available'}
            
            # Create managers
            database_manager = DatabaseManager(
                config.db_path,
                {}
            )
            
            # Create IP monitor (Discord handled via HTTP API)
            ip_manager = IPMonitorManager(self, database_manager, None)
            
            # Get current status
            import asyncio
            current_ip = asyncio.run(ip_manager.check_current_ip())
            last_known = ip_manager.get_last_known_ip()
            monitor_config = ip_manager.get_monitor_config()
            recent_history = ip_manager.get_ip_history(5)
            
            return {
                'current_ip': current_ip,
                'last_known_ip': last_known,
                'config': monitor_config,
                'recent_history': recent_history,
                'is_changed': current_ip != last_known if current_ip else False,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting IP monitor status: {e}")
            return {'error': str(e)}
    
    def _update_ip_monitor_config(self, config_data: Dict) -> None:
        """Update IP monitor configuration in config file."""
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Initialize ip_monitor section if it doesn't exist
        if 'ip_monitor' not in config:
            config['ip_monitor'] = {}
        
        # Update allowed fields
        allowed_fields = [
            'check_interval_seconds',
            'discord_notifications', 
            'auto_monitoring'
        ]
        
        for field in allowed_fields:
            if field in config_data:
                config['ip_monitor'][field] = config_data[field]
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def run(self, host: str = '127.0.0.1', port: int = 5000, debug: bool = False) -> None:
        """Run the Flask web application.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        logging.info(f"Starting FunnyCommentator web interface on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_app() -> Flask:
    """Flask application factory.
    
    Returns:
        Configured Flask application
    """
    web_app = ConfigWebApp()
    return web_app.app


if __name__ == '__main__':
    app = ConfigWebApp()
    app.run(debug=True)
