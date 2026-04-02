import os
from dotenv import load_dotenv

load_dotenv(override=True)

PERSONA_NAME = os.getenv("PERSONA_NAME", "Saketh")
PERSONA_TITLE = os.getenv("PERSONA_TITLE", "AI Engineer")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))
TOP_K = int(os.getenv("TOP_K", "5"))

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

DB_PATH = os.getenv("DB_PATH", "data/knowledge.db")
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma_store")

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN", "")
PUSHOVER_USER = os.getenv("PUSHOVER_USER", "")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "7860"))