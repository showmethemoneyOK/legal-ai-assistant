import os
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
PUBLIC_LAW_DIR = DATA_DIR / "public_law"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
DB_DIR = BASE_DIR / "db"

# Ensure directories exist
for d in [DATA_DIR, PUBLIC_LAW_DIR, VECTOR_DB_DIR, DB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database configuration
DATABASE_URL = f"sqlite:///{DB_DIR}/app.db"

# ChromaDB configuration
CHROMA_PERSIST_DIRECTORY = str(VECTOR_DB_DIR / "chroma_db")

# Security configuration (Change this in production!)
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# LLM Proxy Configuration (LiteLLM)
# Default values for the local LiteLLM Proxy. These can be overridden in the database.
LLM_PROXY_BASE = os.getenv("LLM_PROXY_BASE", "http://localhost:4000/v1")
LLM_MASTER_KEY = os.getenv("LLM_MASTER_KEY", "sk-legalai-master-2026")
DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "ollama/qwen2.5:7b") # Example default

# Global execution mode for LLMs
ASYNC_MODEL_EXECUTION = os.getenv("ASYNC_MODEL_EXECUTION", "false").lower() == "true"



