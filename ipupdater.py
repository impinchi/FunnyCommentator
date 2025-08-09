import os
import socket
import sqlite3
import zlib
import discord
import asyncio
import logging
import subprocess
import requests
import time
import re
import tiktoken
from rcon.source import Client
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
# --- Environment Setup ---
load_dotenv()
# --- Logging Setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("aiLogsResponder.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# --- Configuration Setup ---
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_GLOBAL = int(os.getenv("DISCORD_CHANNEL_ID"))
CHANNEL_ID_SERVER_STATUS = int(os.getenv("DISCORD_CHANNEL_ID_SERVER_STATUS"))
CHANNEL_ID_AI = int(os.getenv("DISCORD_CHANNEL_ID_AI"))
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
IP_RETRY_SECONDS = int(os.getenv("IP_RETRY_SECONDS"))
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS"))
PREVIOUS_IP = os.getenv("PREVIOUS_IP")
OLLAMA_START_CMD = os.getenv("OLLAMA_START_CMD")  
DB_PATH = os.getenv("DB_PATH")
INPUT_TOKEN_SIZE = int(os.getenv("INPUT_TOKEN_SIZE", 16000))
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# --- Functions ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                summary BLOB
            )
        """)

def save_summary(summary: str):
    compressed = zlib.compress(summary.encode("utf-8"))
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO summaries (summary) VALUES (?)", (compressed,))

def count_tokens(text, model="gpt-3.5-turbo"):
    # Use a tokenizer compatible with your model; adjust as needed for DeepSeek
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))
    
def get_summaries_up_to_token_limit(token_limit=INPUT_TOKEN_SIZE):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT summary FROM summaries ORDER BY id DESC")
        summaries = []
        total_tokens = 0
        for row in rows:
            summary = zlib.decompress(row[0]).decode("utf-8")
            tokens = count_tokens(summary) 
            if total_tokens + tokens > token_limit:
                break
            summaries.insert(0, summary)  # Keep chronological order
            total_tokens += tokens
        return summaries

def stop_ollama():
    """Stop Ollama server to free memory."""
    try:
        # This works if Ollama is running as a service or in the background
        subprocess.run("ollama stop", shell=True, check=True)
        logging.info("Ollama AI server stopped successfully.")
    except Exception as e:
        logging.error(f"Failed to stop Ollama AI server: {e}")

def ensure_ollama_running():
    """Ensure Ollama AI server is running, start if not and send history of summaries"""
    prompt_parts = [
        "".join(get_summaries_up_to_token_limit(INPUT_TOKEN_SIZE)),
        "above are previous prompt responses you've given me"
    ]
    prompt = "\n".join(prompt_parts)
    try:
        # Try to connect to Ollama API
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=AI_TIMEOUT_SECONDS 
        )
        if resp.status_code == 200:
            logging.info("Ollama AI server is already running.")
            return
    except Exception as e:
        logging.info(f"Ollama AI server not running or not responding: {e}")
        # Start Ollama as a subprocess
        try:
            subprocess.Popen(OLLAMA_START_CMD, shell=True)
            # Wait for Ollama to start
            for _ in range(AI_TIMEOUT_SECONDS):
                try:
                    resp = requests.post(
                        OLLAMA_URL,
                        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                        timeout=AI_TIMEOUT_SECONDS
                    )
                    if resp.status_code == 200:
                        logging.info("Ollama AI server started successfully.")
                        return
                except Exception:
                    time.sleep(2)
            logging.error("Failed to start Ollama AI server.")
        except Exception as e2:
            logging.error(f"Failed to start Ollama AI server: {e2}")

async def rcon_summary_job():
    """Fetch logs, summarize, and send to Discord at 4am daily."""
    try:
        logging.info("Fetching logs from ARK RCON (scheduled job)...")
        lines = await asyncio.to_thread(fetch_rcon_logs)

        if len(lines) <= 2:
            logging.info("Not enough log lines to summarize. Skipping.")
            return

        summary = await asyncio.to_thread(get_funny_summary, lines)
        logging.debug(f"Summary: {summary}")
        await send_to_discord(summary, CHANNEL_ID_AI)
        logging.info("Sent daily summary to Discord.")
    except Exception as e:
        logging.error(f"RCON summary job error: {e}", exc_info=True)

def sanitize_log_line(line: str) -> str:
    # Remove control characters except newlines and tabs
    line = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]', '', line)
    # Optionally, strip excessive whitespace
    line = line.strip()
    # Optionally, limit length per line
    return line[:500]

def fetch_rcon_logs() -> List[str]:
    """Fetch logs from ARK RCON server and sanitize them."""
    logging.debug("Setting socket timeout for RCON connection.")
    socket.setdefaulttimeout(10)
    try:
        with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASSWORD) as rcon_client:
            logging.info("Connected to ARK RCON.")
            logs = rcon_client.run("GetGameLog")
            logging.info("Closing connection to ARK RCON.")
    finally:
        socket.setdefaulttimeout(None)
    lines = logs.splitlines()
    # Sanitize each line
    lines = [sanitize_log_line(line) for line in lines]
    logging.debug(f"Fetched {len(lines)} lines from ARK log.")
    return lines

def get_funny_summary(log_lines: List[str]) -> str:
    """
    Generates a humorous and sarcastic summary of ARK: Survival Evolved game log events using the Ollama API.
    Args:
        log_lines (List[str]): A list of game log lines to be summarized.
    Returns:
        str: A witty, sarcastic summary of the provided log events, or a message indicating no new events.
    """
    """Get a funny summary from Ollama API."""
    if not log_lines:
        logging.info("No new events in the last day.")
        return "No new events in the last day!"

    prompt_parts = [
        "Here are Gamelog events from RCON:",
        "\n".join(log_lines),
        "You are an advisor and commentator in the game ARK: Survival Evolved.",
        "You are expected to be sarcastic, hilarious and witty while being insulting and rude with mistakes.",
        "Here is context for you to understand better:",
        "Max wild dinos level is 350.",
        "Map is The Lost Island.",
        "We are the only tribe, playing a private PvE server.",
        "Players are OpenTangent, K4321f/Sletty, The Boogeyman and impnchi/impo; Yes somehow some have multiple names.",
        "Sometimes we will use that chat to ask you questions which you will receive in the logs. We will call you Ollama.",
        "End of context",
        "Summarize these events for us"
    ]
    prompt = "\n".join(prompt_parts)

    try:
        logging.debug(f"Sending {len(log_lines)} lines to Ollama for summary.")
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=AI_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        summary = response.json()["response"].strip()
        save_summary(summary)
        logging.info("Received summary from Ollama.")
        return summary
    except Exception as e:
        logging.error(f"Ollama API error: {e}")
        return f"[AI Error: {e}]"
    finally:
        stop_ollama()
    
def split_text_on_word_boundaries(text, max_length=2000):
    """Split text into chunks <= max_length, breaking only at spaces."""
    chunks = []
    while len(text) > max_length:
        # Find the last space within the limit
        split_at = text.rfind(' ', 0, max_length)
        if split_at == -1:
            # No space found, force split at max_length
            split_at = max_length
        chunks.append(text[:split_at])
        # Remove only a single leading space if present
        if text[split_at:split_at+1] == ' ':
            text = text[split_at+1:]
        else:
            text = text[split_at:]
    if text:
        chunks.append(text)
    return chunks

async def send_to_discord(summary: str, channel_id: int) -> None:
    """Send summary to specified Discord channel in 2000-character, word-safe chunks."""
    try:
        channel = await client.fetch_channel(channel_id)
        for chunk in split_text_on_word_boundaries(summary, 2000):
            await channel.send(chunk)
        logging.info(f"Sent summary to Discord channel {channel_id}.")
    except Exception as e:
        logging.error(f"Discord send error: {e}")

async def periodic_ip_task(stop_event: asyncio.Event) -> None:
    """Periodically check external IP and notify Discord if it changes."""
    global PREVIOUS_IP
    await client.wait_until_ready()
    while not client.is_closed() and not stop_event.is_set():
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=10)
            current_ip = response.json()["ip"]
            if current_ip != PREVIOUS_IP:
                PREVIOUS_IP = current_ip
                msg = f"External IP Address has changed: {current_ip}"
                await send_to_discord(msg, CHANNEL_ID_SERVER_STATUS)
                logging.info(f"Sent IP change notification: {current_ip}")
        except Exception as e:
            logging.error(f"Error checking IP: {e}")
        wait_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait([wait_task], timeout=IP_RETRY_SECONDS)
        for task in pending:
            task.cancel()

async def main():
    stop_event = asyncio.Event()

    def handle_sigint():
        logging.info("Keyboard interrupt received. Shutting down gracefully...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(getattr(__import__('signal'), sig), handle_sigint)
        except (AttributeError, NotImplementedError):
            pass

    # Schedule the daily job 
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ensure_ollama_running, CronTrigger(hour=2, minute=0))
    scheduler.add_job(rcon_summary_job, CronTrigger(hour=4, minute=0))
    scheduler.start()

    ip_task = asyncio.create_task(periodic_ip_task(stop_event))
    try:
        await client.start(TOKEN)
    except KeyboardInterrupt:
        handle_sigint()
    finally:
        stop_event.set()
        await ip_task
        await client.close()
        logging.info("Bot shutdown complete.")

if __name__ == "__main__":
    init_db()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Exited by user.")