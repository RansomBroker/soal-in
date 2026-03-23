from langchain_pinecone import PineconeVectorStore
from src.embeddings.gemini_embedding import get_gemini_embeddings
from src.config.settings import DEFAULT_RETRIEVER_TOP_K, DEFAULT_RETRIEVER_FETCH_K

def get_context(query, index_name, top_k=DEFAULT_RETRIEVER_TOP_K):
    """Mencari referensi teratas dari Pinecone menggunakan Maximum Marginal Relevance (MMR)."""
    # Siapkan alat embed agar query teks pengguna dipahami ke dalam vector
    embeddings = get_gemini_embeddings()
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    
    # Setup alat Retriever menggunakan algoritma `mmr`
    # fetch_k = Ambil 20 kandidat tertinggi dulu
    # k = Lalu saring dan buang opsi yang isinya menduplikat satu sama lain, dan sisakan final top_k
    retriever = vectorstore.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": top_k, "fetch_k": DEFAULT_RETRIEVER_FETCH_K}
    )
    
    # Dapatkan dokumennya (chunk list)
    docs = retriever.invoke(query)
    
    # Rangkai / Gabungkan semua dokumen teks menjadi satu kesatuan string beserta metadata Halamannya!
    context_text_list = []
    for doc in docs:
        filename = doc.metadata.get('source_file', 'unknown')
        page_num = doc.metadata.get('page')
        page_str = f"Halaman {page_num + 1}" if isinstance(page_num, int) else "Halaman (OCR/Gambar)"
        
        context_text_list.append(f"---\nSumber Referensi: [{filename}] | {page_str}\n{doc.page_content}")
        
    context_text = "\n\n".join(context_text_list)
    return context_text
