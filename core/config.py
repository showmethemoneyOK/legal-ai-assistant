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

# LLM Configuration
# Options: "openai", "local"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# Local LLM Configuration (e.g., Ollama, LM Studio, vLLM)
# Default points to Ollama running locally
LOCAL_LLM_API_BASE = os.getenv("LOCAL_LLM_API_BASE", "http://localhost:11434/v1")
LOCAL_LLM_API_KEY = os.getenv("LOCAL_LLM_API_KEY", "ollama") # Often not needed for local models
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "llama3")

