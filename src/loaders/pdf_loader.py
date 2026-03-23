import os
import tempfile
import re
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
import google.generativeai as genai

def clean_text(text):
    """Membersihkan teks dari enters berlebih dan format Daftar Isi."""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Hapus spasi liar di kiri-kanan setiap baris
        line = line.strip()
        
        # Buang baris jika isinya benar-benar kosong 
        # (ini yang sebelumnya lolos karena berisi spasi gaib)
        if not line:
            continue
            
        # Heuristik membuang baris daftar isi (misal: "Bab 1 ......... 12")
        if bool(re.search(r'\.{4,}\s*\d+', line)):
            continue 
            
        cleaned_lines.append(line)
        
    # Gabungkan kembali baris yang sudah bersih
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Hapus spasi ganda berturut-turut di tengah kalimat
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
    
    return cleaned_text

def extract_via_gemini_ocr(file_path, original_filename):
    """Menggunakan Gemini AI untuk membaca dokumen PDF bergambar/hasil scan (OCR)."""
    try:
        # Konfigurasi api key diambil otomatis dari environment variable (sudah di setup di app.py)
        gemini_api_key = os.environ.get("GOOGLE_API_KEY")
        if not gemini_api_key:
            return []
            
        genai.configure(api_key=gemini_api_key)
        
        # Upload ke storage temporer Gemini API
        sample_file = genai.upload_file(path=file_path, display_name="scan_upload")
        
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        
        # Prompt jitu untuk minta ekstrak teks
        prompt = (
            "Extract all the readable text from this document exactly as it is written. "
            "Ignore and DO NOT output any Table of Contents, Index pages, or page numbers. "
            "Return purely the educational content text. "
            "Do not include any chat formats like 'Here is the text:' etc."
        )
        
        response = model.generate_content([sample_file, prompt])
        
        # Kembalikan sebagai 1 Document langchain
        cleaned = clean_text(response.text)
        return [Document(page_content=cleaned, metadata={"source_file": original_filename, "is_ocr": True})]
        
    except Exception as e:
        st.warning(f"Gagal melakukan OCR di file {original_filename}: {str(e)}")
        return []

def load_pdfs(uploaded_files, progress_bar=None):
    """Mengekstrak teks mentah dengan PyPDFLoader, fallback ke Gemini OCR jika gambar/blank."""
    all_docs = []
    
    for i, file in enumerate(uploaded_files):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # 1. Coba baca secara standard (Teks murni)
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            
            # 2. Total Panjang Karakter
            total_chars = sum([len(doc.page_content) for doc in docs])
            
            # Jika karakter miskin (Kemungkinan besar ini PDF hasil Scan/Gambar)
            num_pages = len(docs)
            if total_chars < (num_pages * 50) or total_chars < 500:
                st.warning(f"⚠️ Dokumen '{file.name}' terdeteksi sebagai PDF hasil Scan/Gambar. Sistem sedang mencoba teknik OCR menggunakan Gemini AI...")
                docs = extract_via_gemini_ocr(tmp_path, file.name)
            else:
                # Bersihkan Teks Murni jika standard loader berhasil
                cleaned_docs = []
                for doc in docs:
                    doc.page_content = clean_text(doc.page_content)
                    
                    # Jangan masukkan metadata jika teksnya kurang dari 30 huruf (kadang cuma nomor halaman)
                    if len(doc.page_content.strip()) > 30:
                        doc.metadata["source_file"] = file.name
                        cleaned_docs.append(doc)
                docs = cleaned_docs

            all_docs.extend(docs)
            
        finally:
            os.unlink(tmp_path)
            
        if progress_bar:
            progress_bar.progress((i + 1) / len(uploaded_files), text=f"Selesai mengekstrak {file.name}")
            
    return all_docs
