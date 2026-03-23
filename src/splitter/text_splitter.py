from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config.settings import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

def split_documents(docs, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
    """Memotong dokumen raw hasil loader menjadi potongan kecil referensi (chunks)."""
    # Gunakan chunk_size lebih besar (2000) agar konteks utuh 
    # dan tidak terpotong-potong maknanya di tengah kalimat.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    splits = text_splitter.split_documents(docs)
    return splits
