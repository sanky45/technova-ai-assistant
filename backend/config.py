
import os
from dotenv import load_dotenv

load_dotenv()

# Application
APP_NAME = os.getenv("APP_NAME", "TechNova AI Assistant")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Authentication
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
)

# Document processing
TESSERACT_PATH = os.getenv("TESSERACT_PATH")
POPPLER_PATH = os.getenv("POPPLER_PATH")
OCR_TEXT_THRESHOLD = int(
    os.getenv("OCR_TEXT_THRESHOLD", 20)
)

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# New standard Pinecone index for OpenRouter embeddings
PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "technova-openrouter"
)

PINECONE_HYBRID_INDEX_NAME = os.getenv(
    "PINECONE_HYBRID_INDEX_NAME",
    "kstore-ai-hybrid"
)

# OpenRouter - Embeddings and LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1"
)

# Embedding configuration
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "openai/text-embedding-3-small"
)

EMBEDDING_DIMENSION = int(
    os.getenv("EMBEDDING_DIMENSION", "384")
)

# LLM configuration
OPENROUTER_LLM_MODEL = os.getenv(
    "OPENROUTER_LLM_MODEL",
    "google/gemini-2.5-flash"
)

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
