from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config.settings import DEFAULT_EMBEDDING_MODEL

def get_gemini_embeddings(model_name=DEFAULT_EMBEDDING_MODEL):
    """Mengembalikan class object dari AI model untuk meng-embed teks (Google Gemini)."""
    return GoogleGenerativeAIEmbeddings(model=model_name)
