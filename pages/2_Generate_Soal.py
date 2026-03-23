import streamlit as st
import math
import io
from docx import Document
from src.config.settings import load_config, set_api_keys
from src.rag.retriever import get_context
from src.generator.qa_generator import generate_questions

st.set_page_config(page_title="Tahap 2: Generate Soal", page_icon="📝", layout="wide")
st.title("📝 Tahap 2: AI Soal & Kisi-kisi Generator")

st.markdown("""
Setelah semua materi terhimpun di Pinecone, rancang parameter ujian yang Anda kehendaki. AI akan membaca ratusan halaman dokumen Anda menggunakan metode MMR dan menuangkannya ke berbagai format tes spesifik (HOTS/LOTS)!
""")

# ---- KUNCI PENGAMANAN HALAMAN ----
if "processed_files" not in st.session_state or not st.session_state.processed_files:
    st.warning("🚫 Stop! Anda belum mengunggah Satupun Materi (PDF) ke Sistem.")
    st.info("Silakan kembali ke halaman **Tahap 1** di menu samping untuk melakukan Setup Knowledge Base terlebih dahulu.")
    st.stop() # Script akan berhenti disini dan tak menampilkan sisa UI bawahnya!

config = load_config()

# ---- 1. SETUP UI ---- #
with st.container(border=True):
    st.subheader("⚙️ Parameter Database (Konteks)")
    top_k_retrieve = st.number_input("Maksimal Penarikan Konteks (Jumlah Paragraf dari Pinecone)", 
                                     min_value=10, max_value=200, value=40,
                                     help="AI butuh bacaan dari PDF untuk membuat soal. Jika Anda mau mencetak 40 soal, angkanya usahakan besar (misal 50 - 80) agar AI punya banyak paragraf acak untuk dikembangkan!")
    topik_soal = st.text_input("Kata Kunci Pencarian Topik", placeholder="Biarkan kosong jika ingin mengambil materi acak dari seluruh PDF.")
    
st.subheader("Distribusi Jumlah Menu Soal")

# Tracker Variabel Global
total_soal = 0
total_hots = 0

cnt_pg, hots_pg_pct = 0, 0
cnt_pgk, hots_pgk_pct = 0, 0
cnt_bs, hots_bs_pct = 0, 0
cnt_jd, hots_jd_pct = 0, 0
cnt_us, hots_us_pct = 0, 0 # Uraian Singkat
pg_format = "A-E"

# A) PILIHAN GANDA BIASA
use_pg = st.checkbox("Pilihan Ganda (Biasa)")
if use_pg:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        cnt_pg = c1.number_input("Jumlah Soal", 1, 100, 5, key="cnt_pg")
        pg_start = c2.text_input("Opsi Awal", "A", key="pg_start")
        pg_end = c3.text_input("Opsi Akhir", "E", key="pg_end")
        hots_pg_pct = c4.slider("Target % HOTS", 0, 100, 10, step=5, key="hots_pg")
        
        pg_format = f"{pg_start.upper()}-{pg_end.upper()}"
        total_soal += cnt_pg
        total_hots += math.ceil(cnt_pg * (hots_pg_pct / 100.0))

# B) PILIHAN GANDA KOMPLEKS
use_pgk = st.checkbox("Pilihan Ganda Kompleks (Lebih dari 1 Jawaban)")
if use_pgk:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cnt_pgk = c1.number_input("Jumlah Soal", 1, 100, 5, key="cnt_pgk")
        hots_pgk_pct = c2.slider("Target % HOTS", 0, 100, 10, step=5, key="hots_pgk")
        
        total_soal += cnt_pgk
        total_hots += math.ceil(cnt_pgk * (hots_pgk_pct / 100.0))

# C) BENAR / SALAH
use_bs = st.checkbox("Benar / Salah")
if use_bs:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cnt_bs = c1.number_input("Jumlah Soal", 1, 100, 5, key="cnt_bs")
        hots_bs_pct = c2.slider("Target % HOTS", 0, 100, 10, step=5, key="hots_bs")
        
        total_soal += cnt_bs
        total_hots += math.ceil(cnt_bs * (hots_bs_pct / 100.0))

# D) MENJODOHKAN
use_jd = st.checkbox("Menjodohkan (Matching)")
if use_jd:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cnt_jd = c1.number_input("Jumlah Soal", 1, 50, 5, key="cnt_jd")
        hots_jd_pct = c2.slider("Target % HOTS", 0, 100, 10, step=5, key="hots_jd")
        
        total_soal += cnt_jd
        total_hots += math.ceil(cnt_jd * (hots_jd_pct / 100.0))

# E) URAIAN SINGKAT (Baru)
use_us = st.checkbox("Uraian Singkat / Hitungan Esai")
if use_us:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cnt_us = c1.number_input("Jumlah Soal", 1, 50, 5, key="cnt_us")
        hots_us_pct = c2.slider("Target % HOTS", 0, 100, 10, step=5, key="hots_us")
        
        total_soal += cnt_us
        total_hots += math.ceil(cnt_us * (hots_us_pct / 100.0))


total_lots = total_soal - total_hots

# Highlight Rekapitulasi
st.info(f"**REKAPITULASI APLIKASI:** \n\n"
        f"Total Rancangan Soal: **{total_soal} Butir**\n"
        f"🎯 Terakumulasi total **{total_hots} Soal HOTS** dan **{total_lots} Soal LOTS** secara keseluruhan.")

# Variabel State untuk Previewing
if "generated_results" not in st.session_state:
    st.session_state["generated_results"] = {}

# ---- 2. GENERATION ACTION ---- #
if st.button("🚀 Mulai Generate Bank Soal", type="primary", use_container_width=True):
    if total_soal == 0:
        st.warning("Peringatan: Anda belum menceklis satupun bentuk soal. Silakan pilih jenis soal yang dimau.")
    elif not config["google_api_key"] or not config["pinecone_api_key"]:
        st.error("🔑 API Key belum tersedia. Pastikan konfigurasi aman.")
    else:
        set_api_keys(config["google_api_key"], config["pinecone_api_key"])
        st.session_state["generated_results"] = {} # Kosongkan preview lama
        
        with st.status("Mesin AI Sedang Bekerja Membongkar File Database...", expanded=True) as status_box:
            try:
                st.write("🔍 Merangkum literatur referensi dengan algoritma pencarian MMR-Pinecone...")
                
                # Biarkan kalau user ga ketik topik, dia nyari string kosong (ambil random)
                query_topik = topik_soal if topik_soal.strip() else "Materi penting"
                konteks_kasar = get_context(query_topik, config["pinecone_index_name"], top_k=top_k_retrieve)
                
                # Fungsi Helper untuk mengeksekusi AI per Tipe
                def trigger_ai(tipe_soal, jumlah, param_hots_pct, op_length="A-E"):
                    if jumlah <= 0: return
                    
                    st.write(f"💭 Mencetak {jumlah} Soal tipe {tipe_soal}...")
                    
                    jml_hots = math.ceil(jumlah * (param_hots_pct / 100.0))
                    jml_lots = jumlah - jml_hots
                    
                    hasil = generate_questions(
                        topic=query_topik,
                        context_text=konteks_kasar,
                        item_count=jumlah,
                        hots_count=jml_hots,
                        lots_count=jml_lots,
                        question_type=tipe_soal,
                        pg_options=op_length
                    )
                    st.session_state["generated_results"][tipe_soal] = hasil
                
                # Jalankan Siklus Sesuai Ceklis User
                if use_pg:
                    trigger_ai("Pilihan Ganda", cnt_pg, hots_pg_pct, pg_format)
                if use_pgk:
                    trigger_ai("Pilihan Ganda Kompleks", cnt_pgk, hots_pgk_pct)
                if use_bs:
                    trigger_ai("Benar/Salah", cnt_bs, hots_bs_pct)
                if use_jd:
                    trigger_ai("Menjodohkan", cnt_jd, hots_jd_pct)
                if use_us:
                    trigger_ai("Uraian Singkat", cnt_us, hots_us_pct)
                
                status_box.update(label="Seluruh Soal Telah Berhasil Dicetak ke Layar Anda!", state="complete", expanded=False)
                
            except Exception as e:
                status_box.update(label="Terjadi Gangguan pada Koneksi/Batas Quota!", state="error")
                st.error(str(e))

# ---- 3. WEB PREVIEW SECTION ---- #
if len(st.session_state["generated_results"]) > 0:
    st.divider()
    st.header("📖 Preview & Export Hasil")
    
    import re
    
    # Fungsi Helper Export ke Word (DOCX) + Parser LaTeX Sederhana
    def create_docx(text_content):
        doc = Document()
        for line in text_content.split('\n'):
            line = line.strip()
            if not line:
                doc.add_paragraph()
                continue
            
            if line.startswith('### '):
                doc.add_heading(line.replace('### ', ''), level=3)
            else:
                p = doc.add_paragraph()
                
                # Memecah kalimat berdasarkan pola Bold (**) dan Latex Math ($)
                tokens = re.split(r'(\*\*.*?\*\*|\$.*?\$)', line)
                
                for token in tokens:
                    if not token:
                        continue
                    if token.startswith('**') and token.endswith('**'):
                        p.add_run(token[2:-2]).bold = True
                    elif token.startswith('$') and token.endswith('$'):
                        # Ini adalah balok Rumus Latex!
                        math_text = token[1:-1]
                        math_text = math_text.replace('\\rightarrow', ' → ')
                        
                        # Parsing Subscript (_) dan Superscript (^) dasar Regex
                        sub_tokens = re.split(r'(_[a-zA-Z0-9]|\^[a-zA-Z0-9]|_{[^}]+}|\^{[^{]+})', math_text)
                        for sub in sub_tokens:
                            if sub.startswith('_'):
                                val = sub[1:]
                                if val.startswith('{') and val.endswith('}'): val = val[1:-1]
                                p.add_run(val).font.subscript = True
                            elif sub.startswith('^'):
                                val = sub[1:]
                                if val.startswith('{') and val.endswith('}'): val = val[1:-1]
                                p.add_run(val).font.superscript = True
                            else:
                                p.add_run(sub)
                    else:
                        p.add_run(token) # Teks biasa
        
        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue()
    
    # Bundling semua teks untuk fitur Download Master
    master_text = "\n\n========================================\n\n".join(
        [f"--- BAGIAN: {k.upper()} ---\n{v}" for k, v in st.session_state["generated_results"].items()]
    )
    
    st.download_button(
        label="📥 Download Semua Soal & Kisi-Kisi (.DOCX)",
        data=create_docx(master_text),
        file_name="Bank_Soal_Generated.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary"
    )
    
    # Gunakan Tabs agar preview sangat rapi per Jenis Soal
    tabs = st.tabs(list(st.session_state["generated_results"].keys()))
    
    for tab, (tipe_soal, teks_hasil) in zip(tabs, st.session_state["generated_results"].items()):
        with tab:
            st.download_button(
                label=f"📥 Download Spesifik: {tipe_soal} (.DOCX)",
                data=create_docx(teks_hasil),
                file_name=f"Soal_{tipe_soal.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_btn_{tipe_soal}"
            )
            st.markdown(teks_hasil)
            st.caption(f"*Soal, Kisi-kisi, dan Kemenjodohan di atas diproduksi secara eksklusif menggunakan sistem AI berdasarkan dokumen milik Anda pribadi.*")
