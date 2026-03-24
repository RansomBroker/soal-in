import time
import hashlib
import streamlit as st
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from src.config.settings import DEFAULT_DIMENSION, DEFAULT_BATCH_SIZE, DEFAULT_SLEEP_TIME, get_all_google_keys
from src.embeddings.gemini_embedding import get_gemini_embeddings
import os

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
    # Koneksi awal object store ke DB Index
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
            
        # Limit Tracker untuk Multi-Key Rotate Embeddings
        keys = get_all_google_keys()
        if not keys: raise Exception("Tidak ada GOOGLE_API_KEY satupun di lingkungan Anda!")
        
        last_err = None
        success_batch = False
        
        for idx_k, g_key in enumerate(keys):
            try:
                # Re-Initialize Embedding Model untuk mem-bypass limit dengan api_key baru
                os.environ["GOOGLE_API_KEY"] = g_key
                fresh_embed = get_gemini_embeddings()
                vs = PineconeVectorStore(
                    index_name=index_name,
                    embedding=fresh_embed
                )
                
                # Simpan menggunakan ID yang sudah dipatenkan
                vs.add_documents(batch_splits, ids=batch_ids)
                success_batch = True
                break
                
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "exhausted" in err_msg or "quota" in err_msg:
                    last_err = e
                    embed_progress.progress(current_progress if 'current_progress' in locals() else 0, text=f"⚠️ Mengganti token (Embedding Limit). Mencoba engine-{idx_k+2}...")
                    time.sleep(1)
                    continue
                else:
                    raise e
                    
        if not success_batch:
            raise Exception(f"Gagal memproses batch! Seluruh ({len(keys)}) API Key Anda telah kandas menembus limit Embeddings. Tunggu beberapa saat. Error: {str(last_err)}")
        
        # Hitung progress normal
        current_progress = min((j + batch_size) / len(splits), 1.0)
        embed_progress.progress(current_progress, text=f"Menyimpan batch {(j//batch_size)+1} ke VectorDB...")
        
        if j + batch_size < len(splits):
            time.sleep(sleep_time)
            
    return vectorstore
