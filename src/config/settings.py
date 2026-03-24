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


def get_all_google_keys():
    """Retrieve all Google API Keys starting with GOOGLE_API_KEY inside the environment."""
    load_dotenv()
    keys = []
    
    # Utama
    main_key = os.getenv("GOOGLE_API_KEY")
    if main_key:
        keys.append(main_key)
        
    # Cadangan (1, 2, 3...)
    for i in range(1, 20):
        bk_key = os.getenv(f"GOOGLE_API_KEY_{i}")
        if bk_key and bk_key not in keys:
            keys.append(bk_key)
            
    return keys

def load_config():
    """Load dan validasi environment variables."""
    load_dotenv()
    
    google_keys = get_all_google_keys()
    
    config = {
        "google_api_keys": google_keys,
        "google_api_key": google_keys[0] if google_keys else None,
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
