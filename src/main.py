"""Main application module.

This module coordinates all components and runs the main application loop.
Following PEP 257 for docstring conventions.
"""
import asyncio
import json
import logging
import time
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import Config
from src.database import DatabaseManager
from src.rcon_client import RconClient
from src.discord_manager import DiscordManager
from src.ollama_manager import OllamaManager
from src.ip_monitor_manager import IPMonitorManager

class Application:
    """Main application class coordinating all components."""
    
    def __init__(self):
        """Initialize application and its components."""
        self.config = Config()
        self.setup_logging()
        
        # Create database manager with tables for each server
        server_tables = {name: config.database_table 
                        for name, config in self.config.servers.items()}
        self.db = DatabaseManager(self.config.db_path, server_tables)
        
        # Create RCON clients for each server
        self.rcon_clients = {
            name: RconClient(
                config.rcon_host,
                config.rcon_port,
                config.rcon_password
            )
            for name, config in self.config.servers.items()
        }
        
        # Create shared components
        self.discord = DiscordManager(self.config.discord_token, use_client=False)
        self.ollama = OllamaManager(
            self.config.ollama_url,
            self.config.ollama_model,
            self.config.ollama_start_cmd,
            self.config.ai_timeout_seconds,
            startup_timeout=self.config.ollama_startup_timeout,
            input_token_size=self.config.input_token_size
        )
        
        # Create IP monitor (shared across all servers since they're on the same machine)
        self.ip_monitor = IPMonitorManager(
            self.config,
            self.db,
            self.discord
        )
        
        self.stop_event = asyncio.Event()
        self.scheduler = AsyncIOScheduler()
    
    def setup_logging(self):
        """Set up application logging."""
        # Ensure logs directory exists
        import os
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        logging.basicConfig(
            level=self.config.log_level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, "application.log"), encoding="utf-8"),
                logging.StreamHandler()
            ]
        )
    
    async def ip_change_callback(self, new_ip: str):
        """Handle IP address changes.
        
        Args:
            new_ip: The new IP address
        """
        # IPMonitorManager already handles Discord notifications internally
        # Just log the change here
        logging.info(f"IP Address changed to: {new_ip}")
    
    async def _monitor_ip_changes(self):
        """Monitor IP address changes using IPMonitorManager."""
        try:
            # Get check interval from config
            monitor_config = self.ip_monitor.get_monitor_config()
            check_interval = monitor_config.get('check_interval_seconds', 3600)
            
            logging.info(f"Starting IP monitoring with {check_interval}s interval")
            
            while not self.stop_event.is_set():
                try:
                    result = await self.ip_monitor.perform_ip_check_and_notify()
                    
                    if result.get('success'):
                        if result.get('changed'):
                            await self.ip_change_callback(result['current_ip'])
                    else:
                        logging.error(f"IP check failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logging.error(f"Error during IP monitoring: {e}")
                
                # Wait for the next check or stop event
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=check_interval)
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    continue  # Timeout reached, continue monitoring
                    
        except Exception as e:
            logging.error(f"IP monitoring task failed: {e}")
    
    async def process_cluster_logs(self, cluster_name: str):
        """Process logs for all servers in a cluster.
        
        Args:
            cluster_name: Name of the cluster to process
        """
        cluster_info = self.config.clusters[cluster_name]
        server_names = cluster_info["servers"]
        
        try:
            # Collect logs from all servers in cluster
            all_lines = []
            cluster_context = []
            
            for server_name in server_names:
                server_config = self.config.servers[server_name]
                rcon_client = self.rcon_clients[server_name]
                
                logging.info(f"Fetching logs from {server_name} for cluster {cluster_name}...")
                lines = await asyncio.to_thread(rcon_client.fetch_logs)
                
                if lines:
                    all_lines.extend([f"[{server_name}] {line}" for line in lines])
                    cluster_context.append(server_config.get_context_prompt(self.config.ai_tone))

            if not all_lines:
                logging.info(f"No logs to summarize for cluster {cluster_name}")
                return

            # Get previous cluster summaries
            cluster_summaries = self.db.get_cluster_summaries_up_to_token_limit(
                cluster_name, 
                self.config.input_token_size
            )
            history_context = "\n".join(cluster_summaries + ["\nAbove are my previous responses for this cluster."])
            
            # Create cluster context
            combined_context = (
                f"This is a summary for the cluster '{cluster_name}' which includes the following servers:\n"
                + "\n".join(cluster_context)
                + f"\n{history_context}"
            )
            
            # Generate cluster summary
            cluster_summary = await asyncio.to_thread(
                self.ollama.get_funny_summary,
                all_lines,
                combined_context
            )
            
            # Save and send cluster summary
            self.db.save_cluster_summary(cluster_name, cluster_summary)
            cluster_header = f"=== {cluster_name} Cluster Summary ===\n"
            await self.discord.send_message(
                cluster_header + cluster_summary,
                self.config.channel_id_ai
            )
            logging.info(f"Sent cluster summary for {cluster_name} to Discord.")
            
        except Exception as e:
            logging.error(f"Cluster summary job error for {cluster_name}: {e}", exc_info=True)

    async def process_server_logs(self, server_name: str):
        """Process logs for a single server.
        
        Args:
            server_name: Name of the server to process
        """
        server_config = self.config.servers[server_name]
        rcon_client = self.rcon_clients[server_name]
        
        try:
            logging.info(f"Fetching logs from {server_name} (scheduled job)...")
            lines = await asyncio.to_thread(rcon_client.fetch_logs)

            if len(lines) <= 2:
                logging.info(f"Not enough log lines to summarize for {server_name}. Skipping.")
                return

            # Prepend server context to the logs
            context = server_config.get_context_prompt(self.config.ai_tone)
            
            # Get previous summaries for this server
            summaries = self.db.get_summaries_up_to_token_limit(
                server_name, 
                self.config.input_token_size
            )
            history_context = "\n".join(summaries + ["\nAbove are my previous responses for this server."])
            
            # Generate summary with server-specific context
            summary = await asyncio.to_thread(
                self.ollama.get_funny_summary,
                lines,
                f"{context}\n{history_context}"
            )
            
            # Save and send the summary
            self.db.save_summary(server_name, summary)
            server_header = f"=== {server_name} ({server_config.map_name}) Summary ===\n"
            await self.discord.send_message(
                server_header + summary,
                self.config.channel_id_ai
            )
            logging.info(f"Sent daily summary for {server_name} to Discord.")
            
        except Exception as e:
            logging.error(f"RCON summary job error for {server_name}: {e}", exc_info=True)
    
    async def rcon_summary_job(self):
        """Fetch and summarize RCON logs for all servers and clusters sequentially."""
        # Check if we're already running an Ollama job
        if getattr(self, '_ollama_running', False):
            logging.warning("Another Ollama job is still running, skipping this one")
            return
            
        self._ollama_running = True
        try:
            # Ensure Ollama is running before processing
            # Run this in a thread since it involves network and process operations
            is_running = await asyncio.to_thread(self.ollama.ensure_server_running, "Hi")
            if not is_running:
                logging.error("Skipping RCON summary job - Ollama server not available")
                return
                
            try:
                # First, identify which servers are in clusters to avoid duplication
                servers_in_clusters = set()
                for cluster_name in self.config.clusters:
                    cluster_info = self.config.clusters[cluster_name]
                    if "servers" in cluster_info:
                        servers_in_clusters.update(cluster_info["servers"])
                
                # Process only standalone servers (not in any cluster)
                standalone_servers = set(self.config.servers.keys()) - servers_in_clusters
                
                if standalone_servers:
                    logging.info(f"Processing {len(standalone_servers)} standalone servers: {list(standalone_servers)}")
                    for server_name in standalone_servers:
                        try:
                            await self.process_server_logs(server_name)
                        except asyncio.CancelledError:
                            logging.info("Job cancelled during server processing - shutting down gracefully")
                            return
                else:
                    logging.info("No standalone servers to process (all servers are in clusters)")
                    
                # Then process all clusters
                if self.config.clusters:
                    logging.info(f"Processing {len(self.config.clusters)} clusters: {list(self.config.clusters.keys())}")
                    for cluster_name in self.config.clusters:
                        try:
                            await self.process_cluster_logs(cluster_name)
                        except asyncio.CancelledError:
                            logging.info("Job cancelled during cluster processing - shutting down gracefully")
                            return
                else:
                    logging.info("No clusters configured to process")
                    
            finally:
                # Stop Ollama after processing all servers and clusters
                try:
                    self.ollama.stop_server()
                except Exception as e:
                    logging.error(f"Error stopping Ollama server: {e}")
            
        except asyncio.CancelledError:
            logging.info("RCON summary job cancelled - shutting down gracefully")
            try:
                self.ollama.stop_server()
            except Exception as e:
                logging.error(f"Error stopping Ollama server during cancellation: {e}")
        except Exception as e:
            logging.error(f"RCON summary job error: {e}", exc_info=True)
            try:
                self.ollama.stop_server()  # Ensure Ollama is stopped even on error
            except Exception as stop_error:
                logging.error(f"Error stopping Ollama server after error: {stop_error}")
        finally:
            self._ollama_running = False  # Reset the running flag
    
    def setup_scheduler(self):
        """Set up scheduled jobs."""
        # Schedule the RCON summary job for all servers
        self.scheduler.add_job(
            self.rcon_summary_job,
            CronTrigger(
                hour=self.config.scheduler_logs_hour,
                minute=self.config.scheduler_logs_minute
            ),
            id='rcon_summary_job'  # Give it a unique ID for management
        )
        self.scheduler.start()
    
    def reload_scheduler(self):
        """Reload scheduler configuration without restarting the application."""
        try:
            # Remove existing job if it exists
            if self.scheduler.get_job('rcon_summary_job'):
                self.scheduler.remove_job('rcon_summary_job')
                logging.info("Removed existing scheduled job")
            
            # Reload configuration
            self.config.reload()
            logging.info("Reloaded configuration from file")
            
            # Add the job with new schedule
            self.scheduler.add_job(
                self.rcon_summary_job,
                CronTrigger(
                    hour=self.config.scheduler_logs_hour,
                    minute=self.config.scheduler_logs_minute
                ),
                id='rcon_summary_job'
            )
            
            logging.info(f"Scheduler reloaded successfully - new schedule: {self.config.scheduler_logs_hour:02d}:{self.config.scheduler_logs_minute:02d}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to reload scheduler: {e}", exc_info=True)
            return False
    
    def check_reload_signal(self):
        """Check for scheduler reload signal file and process if found."""
        signal_file = Path("scheduler_reload.signal")
        if signal_file.exists():
            try:
                logging.info("Scheduler reload signal detected")
                success = self.reload_scheduler()
                
                # Remove the signal file
                signal_file.unlink()
                
                # Create response file
                response_file = Path("scheduler_reload.response")
                with response_file.open('w') as f:
                    json.dump({
                        'success': success,
                        'timestamp': time.time(),
                        'schedule': f"{self.config.scheduler_logs_hour:02d}:{self.config.scheduler_logs_minute:02d}"
                    }, f)
                    
                logging.info(f"Scheduler reload signal processed - success: {success}")
                
            except Exception as e:
                logging.error(f"Error processing scheduler reload signal: {e}")
                # Still remove the signal file to prevent repeated attempts
                if signal_file.exists():
                    signal_file.unlink()
    
    def handle_shutdown(self):
        """Handle graceful shutdown of the application."""
        logging.info("Keyboard interrupt received. Shutting down gracefully...")
        self.stop_event.set()
    
    async def cleanup(self):
        """Clean up resources before shutdown."""
        try:
            # Set stop event first to prevent new tasks
            self.stop_event.set()
            
            # Stop the scheduler first to prevent new jobs
            if hasattr(self, 'scheduler') and self.scheduler and self.scheduler.running:
                try:
                    self.scheduler.shutdown(wait=True)  # Wait for jobs to complete
                except Exception as e:
                    logging.error(f"Error shutting down scheduler: {e}")
            
            # Cancel all tasks except the current one
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                if not task.done():
                    task.cancel()
                    
            # Give tasks a chance to handle cancellation
            if tasks:
                try:
                    # Wait for all tasks to complete or be cancelled
                    done, pending = await asyncio.wait(tasks, timeout=5.0)
                    # Cancel any remaining tasks
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                except Exception as e:
                    logging.error(f"Error during task cleanup: {e}", exc_info=True)

            # Stop Ollama if running
            if hasattr(self, 'ollama') and self.ollama:
                try:
                    self.ollama.stop_server()
                except Exception as e:
                    logging.error(f"Error stopping Ollama: {e}")

            # Close RCON connections
            if hasattr(self, 'rcon_clients'):
                for name, client in self.rcon_clients.items():
                    try:
                        if hasattr(client, 'close'):
                            await client.close()
                    except Exception as e:
                        logging.error(f"Error closing RCON client {name}: {e}")

            # Note: No Discord client cleanup needed in HTTP-only mode

            # Close database connections
            if hasattr(self, 'db') and self.db:
                try:
                    await asyncio.to_thread(self.db.close)
                except Exception as e:
                    logging.error(f"Error closing database: {e}")

            logging.info("All resources cleaned up successfully")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}", exc_info=True)
            raise  # Re-raise to ensure the error is properly handled

    async def run(self):
        """Run the main application loop."""
        try:
            # Signal handling is now managed by run.py
            # Set up scheduler and start it
            self.setup_scheduler()
            
            # Start IP monitoring (single monitor for all servers)
            ip_monitor_task = asyncio.create_task(
                self._monitor_ip_changes()
            )
            
            # Start scheduler reload signal monitoring
            reload_monitor_task = asyncio.create_task(self._monitor_reload_signals())
            
            # Since we're using HTTP-only Discord mode, just wait for shutdown signal
            logging.info("Application started with HTTP-only Discord mode")
            try:
                await self.stop_event.wait()
            finally:
                # Cancel and wait for all background tasks
                for task in [ip_monitor_task, reload_monitor_task]:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                
                logging.info("Application shutdown complete.")
                
        except KeyboardInterrupt:
            self.handle_shutdown()
    
    async def _monitor_reload_signals(self):
        """Monitor for scheduler reload signals in the background."""
        try:
            while not self.stop_event.is_set():
                try:
                    # Check for reload signal every 5 seconds
                    await asyncio.wait_for(self.stop_event.wait(), timeout=5.0)
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    # Timeout is expected - check for reload signal
                    await asyncio.to_thread(self.check_reload_signal)
        except asyncio.CancelledError:
            logging.debug("Reload signal monitor cancelled")
        except Exception as e:
            logging.error(f"Error in reload signal monitor: {e}")

def main():
    """Application entry point."""
    app = Application()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logging.info("Exited by user.")
