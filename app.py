import streamlit as st

# Menerima module-module external (Modular)
from src.config.settings import load_config, set_api_keys
from src.loaders.pdf_loader import load_pdfs
from src.splitter.text_splitter import split_documents
from src.embeddings.gemini_embedding import get_gemini_embeddings
from src.vectorestore.pinecone_db import init_pinecone_index, store_to_pinecone

# Konfigurasi setup
st.set_page_config(page_title="Generator Soal V1.0", page_icon="📚", layout="wide")

# Konfigurasi Load
config = load_config()

# Cek History List dan Memory
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

# ==================== MAIN UI ====================== #

st.title("📚 Generator Soal AI V1.0 - Setup Knowledge Base")
st.markdown("""
**Tahap 1: Upload dan Proses Materi (Refactored to Source Folder)**
Seluruh pemrosesan Document, Splitting, Embedding, Vector Database sudah berjalan melalui Module terpisah!
""")

# Setup Variabel API (Untuk Pengecekan)
google_key = config["google_api_key"]
pinecone_key = config["pinecone_api_key"]
pinecone_env = config["pinecone_environment"]
pinecone_idx = config["pinecone_index_name"]

if not google_key or not pinecone_key or not pinecone_env or not pinecone_idx:
    st.error("❌ Oops: Sistem tidak dapat menemukan nilai setup di `.env`. Harap perhatikan file env Anda.")

uploaded_files = st.file_uploader("Upload Rekap Materi (Beberapa PDF diizinkan)", type="pdf", accept_multiple_files=True)

if st.button("Proses dan Simpan ke Vector DB", type="primary"):
    if not uploaded_files:
        st.warning("⚠️ Masukkan berkas dokumen yang hendak di unggah terlebih dahulu.")
    elif google_key and pinecone_key:
        
        # Override nilai runtime
        set_api_keys(google_key, pinecone_key)
        
        with st.spinner("Menjalankan pipeline pemrosesan PDF secara modular..."):
            try:
                # 1. Pendaftaran Target Index di Pinecone
                init_pinecone_index(pinecone_key, pinecone_env, pinecone_idx, dimension=3072)
                
                # 2. Extract Document (Memanggil Pdf Loader)
                st_progress = st.progress(0, text="Mengumpulkan Teks dari Dokumen Fisik...")
                docs = load_pdfs(uploaded_files, st_progress)
                
                # 3. Potong Document (Memanggil Splitter)
                text_splits = split_documents(docs, chunk_size=1000, chunk_overlap=200)
                st.info(f"✅ Text Pipeline berhasil dengan menghasilkan {len(text_splits)} chunk!")

                # 4. Ambil object Model AI (Memanggil Embeddings)
                embed_model = get_gemini_embeddings(config["embedding_model"])
                
                # 5. Injection (Menyimpan vector ke Pinecone_store Database)
                store_to_pinecone(text_splits, embed_model, pinecone_idx, batch_size=config["batch_size"])
                
                # Selesai!
                st.success("🎉 Berhasil! Peta Pengetahuan Anda kini bersemayam dengan aman di server Database Cloud.")
                
                # Tambah Status history
                for docs_file in uploaded_files:
                    if docs_file.name not in st.session_state.processed_files:
                        st.session_state.processed_files.append(docs_file.name)
                        
            except Exception as e:
                st.error(f"Pecah belah error: {str(e)}")


# History Section UI
if st.session_state.processed_files:
    st.markdown("### 📋 History File yang Telah Mengisi Memory:")
    for file_name in st.session_state.processed_files:
        st.markdown(f"- ✅ **{file_name}**")
