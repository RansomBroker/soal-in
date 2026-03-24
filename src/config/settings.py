import os
from dotenv import load_dotenv

# ==========================================
# CENTRALIZED SETTINGS & MAGIC NUMBERS
# ==========================================

# Vector Store (Pinecone) Parameters
DEFAULT_DIMENSION = 3072
DEFAULT_BATCH_SIZE = 20
DEFAULT_SLEEP_TIME = 5

# Text Splitting Parameters
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 400

# Retrieval (RAG) Parameters
DEFAULT_RETRIEVER_TOP_K = 5
DEFAULT_RETRIEVER_FETCH_K = 20

# AI Generator & Embedding Parameters
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_GENERATOR_MODEL = "gemini-2.5-flash"
DEFAULT_GENERATOR_ITEM_COUNT = 5
DEFAULT_GENERATOR_DIFFICULTY = "Menengah"
DEFAULT_GENERATOR_TEMPERATURE = 0.5


def load_config():
    """Load dan validasi environment variables."""
    load_dotenv()
    
    config = {
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "pinecone_api_key": os.getenv("PINECONE_API_KEY"),
        "pinecone_environment": os.getenv("PINECONE_ENV", "us-east-1"),
        "pinecone_index_name": os.getenv("PINECONE_INDEX_NAME", "buat-soalan-3072"),
        "batch_size": DEFAULT_BATCH_SIZE,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "google_search_api_key": os.getenv("GOOGLE_SEARCH_API_KEY"),
        "google_cx": os.getenv("GOOGLE_CX")
    }
    
    return config

def set_api_keys(google_key, pinecone_key):
    """Fungsi manual untuk mengamankan api key di runtime jika diperlukan by system."""
    if google_key:
        os.environ["GOOGLE_API_KEY"] = google_key
    if pinecone_key:
        os.environ["PINECONE_API_KEY"] = pinecone_key
