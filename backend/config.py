"""Application settings loaded from environment variables and defaults."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "knowledge.db"

# API keys and secrets (set in .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "knowledge-assistant-index")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")

# Model settings
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"
VISION_MODEL = "gpt-4.1-mini"
EMBEDDING_DIMENSION = 1536

# RAG settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5
MAX_HISTORY_MESSAGES = 12

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx",
    "txt",
    "md",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "gif",
    "bmp",
    "tiff",
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
