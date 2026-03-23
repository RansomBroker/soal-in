import time
import hashlib
import streamlit as st
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from src.config.settings import DEFAULT_DIMENSION, DEFAULT_BATCH_SIZE, DEFAULT_SLEEP_TIME

def init_pinecone_index(api_key, environment, index_name, dimension=DEFAULT_DIMENSION):
    """Mengecek apakah index DB sudah ada. JIka belum otomatis mendirikan yang baru."""
    pc = Pinecone(api_key=api_key)
    
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    if index_name not in existing_indexes:
        st.info(f"🔹 Menginisiasi index DB Server : `{index_name}`. Tunggu sebentar...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=environment
            )
        )
    return pc

def store_to_pinecone(splits, embeddings, index_name, batch_size=DEFAULT_BATCH_SIZE, sleep_time=DEFAULT_SLEEP_TIME):
    """Store batch ke vectorstore dengan delay limit-rate safeguard dan ID Unik Anti-Duplikat."""
    # Koneksi object store kosongan ke DB Index
    vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )
    
    # Progress text
    embed_progress = st.progress(0, text="Mengantrikan penyimpanan ke Pinecone (Mencegah Limit Error & Duplikasi)...")
    
    # Batch looping
    for j in range(0, len(splits), batch_size):
        batch_splits = splits[j : j + batch_size]
        
        # --- MITIGASI DUPLIKASI (Ingestion Deduplication) ---
        # Membuat Sidik Jari / ID unik berdasarkan Gabungan isi teks dan nama file 
        # (MD5 Hash) sehingga jika teks sama persis diupload ulang, ID-nya akan kembar 
        # dan Pinecone hanya sekadar me-replace tanpa membuat data numpuk.
        batch_ids = []
        for doc in batch_splits:
            fingerprint = f"{doc.metadata.get('source_file', 'unknown')}_{doc.page_content}"
            doc_id = hashlib.md5(fingerprint.encode('utf-8')).hexdigest()
            batch_ids.append(doc_id)
            
        # Simpan menggunakan ID yang sudah dipatenkan
        vectorstore.add_documents(batch_splits, ids=batch_ids)
        
        current_progress = min((j + batch_size) / len(splits), 1.0)
        embed_progress.progress(current_progress, text=f"Menyimpan batch {(j//batch_size)+1} ke VectorDB...")
        
        if j + batch_size < len(splits):
            time.sleep(sleep_time)
            
    return vectorstore
