import os
from pathlib import Path
from dotenv import load_dotenv

# Load env file from the same directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")
# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://n8n_user:n8n_secure_pass_2026@localhost:5435/my_office_db")

# Agent Configuration (Allows multi-agent support)
AGENT_ID = os.getenv("AGENT_ID", "Agent-001")

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"


# Verify critical configs are loaded
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is not configured in .env file.")

