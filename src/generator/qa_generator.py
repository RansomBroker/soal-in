from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
import os
import time
from src.config.settings import DEFAULT_GENERATOR_MODEL, DEFAULT_GENERATOR_TEMPERATURE, get_all_google_keys

def generate_questions(topic, context_text, item_count, hots_count, lots_count, question_type, pg_options="A-E", images_b64=None):
    """Menggunakan LLM Gemini untuk meracik jenis soal tertentu secara spesifik (Batching)."""
    if images_b64 is None:
        images_b64 = []
    
    # Meracik format instruksi sesuai Jenis Soal yang direquest
    type_instruction = ""
    if question_type == "Pilihan Ganda":
        type_instruction = f"""Format: Pilihan ganda dengan opsi {pg_options}. Hanya 1 opsi yang menjadi jawaban benar.
### 📝 SOAL {question_type.upper()}
1. [Teks Pertanyaan]
  
   - A. [Pilihan A]
   - B. [Pilihan B]
   - ... (Sesuaikan hingga {pg_options.split('-')[1]})"""
    elif question_type == "Pilihan Ganda Kompleks":
        type_instruction = f"""Format: Pilihan ganda kompleks di mana JAWABAN BENAR DAPAT LEBIH DARI SATU opsi.
### 📝 SOAL {question_type.upper()}
1. [Teks Pertanyaan]

   - A. [ ] [Statement/Pilihan 1]
   - B. [ ] [Statement/Pilihan 2]
   - C. [ ] [Statement/Pilihan 3]
   - ... (WAJIB awali opsi dengan abjad A, B, C.. lalu spasi dan tanda kurung siku siku `[ ]` seperti contoh! JANGAN HANYA MENULIS `- [ ]` SAJA!)"""
    elif question_type == "Benar/Salah":
        type_instruction = f"""Format: Pernyataan faktual berupa benar atau salah.
### 📝 SOAL {question_type.upper()}
1. [Klaim/Pernyataan dari topik]

   - A. Benar
   - B. Salah"""
    elif question_type == "Menjodohkan":
        type_instruction = f"""Format: Soal tipe menjodohkan. Sajikan {item_count} premis (soal) bernomor 1, 2, 3.. di kiri, dan sekumpulan pilihan jawaban berhuruf A, B, C.. di kanan. Sediakan LEBIH BANYAK opsi jawaban daripada premis sebagai pengecoh.
### 📝 SOAL {question_type.upper()}
**Premis/Pernyataan Kiri:**
1. [Pernyataan 1]
2. [Pernyataan 2]
...

**Pilihan Respon/Jawaban Kanan:**
- A. [Jawaban Pengecoh]
- B. [Jawaban Valid]
- C. [Jawaban Valid]
..."""
    elif question_type == "Uraian Singkat":
        type_instruction = f"""Format: Soal esai uraian singkat yang mengutarakan pertanyaan pemahaman mendalam, penyelesaian masalah, atau kasus hitungan angka (jika data referensinya mendukung). Tanpa satupun opsi pilihan!
### 📝 SOAL {question_type.upper()}
1. [Teks Pertanyaan Kritis/Kasus Singkat]
2. [Teks Pertanyaan Kritis/Kasus Singkat]
..."""

    template = f"""Anda adalah seorang pakar kurikulum dan dosen evaluasi pendidikan tingkat lanjut.
Tugas Anda mendesain BANK SOAL murni mengenai topik "{topic}".

BUATLAH {item_count} SOAL BERTIPE '{question_type}', terdiri dari:
- **{hots_count} Soal HOTS** (High Order Thinking Skills - Mensyaratkan penalaran analitis/pemecahan masalah konseptual dari teks).
- **{lots_count} Soal LOTS** (Lower Order Thinking Skills - Mensyaratkan ingatan/pemahaman dari teks).

PERATURAN MUTLAK KETAT: 
1. Fakta Teks: Semua bahan/fakta WAJIB DITARIK 100% dari KONTEKS REFERENSI di bawah. BILA topik yang ditarik sama sekali TIDAK MEMILIKI kaitan/informasi apapun di teks referensi, WAJIB tuliskan: "ERROR_404: Materi X tidak diajarkan di modul/PDF ini" dan hentikan penulisan.
2. Filter & Format: ABAIKAN instruksi penggunaan modul. Demi menjaga agar layout tetap sempurna di Web dan Word, Anda WAJIB menggunakan karakter UNIVERSAL UNICODE Asli untuk mencetak angka rumus/kimia (Gunakan native subscript/superscript asli Contoh: `H₂O`, `x²`, `C₂H₆ → C₂H₅Cl`). PERINGATAN KERAS: DILARANG MENGGUNAKAN sintaks LaTeX (seperti `$`, `$$`, `\rightarrow`) dan DILARANG MENGGUNAKAN karakter garis bawah `_` (seperti `H_2O`) karena akan menghancurkan kerangka Web Markdown!
3. Format Markdown UI: Agar opsi jawaban BISA DIBACA KE BAWAH bukan menyamping, WAJIB taruh ENTER KOSONG sebelum mulai Opsi A. Dan WAJIB gunakan bullet list (tanda strip `- `) pada AWAL setiap opsi jawaban, contoh: "- A. Jawaban". JANGAN PERNAH gunakan A. B. C. yang nyambung sebaris!
4. Keseimbangan Teori & Hitungan: JIKA teks referensi mengandung Rumus, Angka, atau Studi Kasus Perhitungan, Anda WAJIB membagi porsi agar soal menghasilkan HITUNGAN KUANTITATIF!
5. Gaya Bahasa Ujian Independen: Susunlah narasi pertanyaan secara mandiri layaknya Soal Ujian Nasional yang berdiri sendiri tanpa menyinggung keberadaan 'modul' atau 'teks bacaan' di peserta ujian.

KONTEKS MATERI REFERENSI DATABASE KAMI:
{{context_text}}

OUTPUT WAJIB MENGANDUNG 4 STRUKTUR INI SECARA BERURUTAN (Tanpa basa-basi intro):

{type_instruction}

### 🔑 KUNCI JAWABAN ({question_type})
(WAJIB susun dalam blok Tabel Markdown persis seperti format ini)
| No | Jawaban |
|---|---|
| 1 | A. Jawaban |
...

### 💡 PEMBAHASAN SOAL ({question_type})
(WAJIB susun dalam blok Tabel Markdown persis seperti format ini)
| No | Pembahasan Detail |
|---|---|
| 1 | (Tuliskan penjelasan argumentatif/perhitungan langkah demi langkah mengapa jawaban tersebut benar) |
...

### 📋 KISI-KISI SOAL ({question_type})
(WAJIB susun dalam blok Tabel Markdown persis seperti format ini)
| Bagian | No | Materi | Indikator | Level |
|---|---|---|---|---|
| {question_type} | 1 | (Nama Topik) | (Fungsi/Deskripsi Soal) | (Mudah/Sedang/HOTS) |
...
"""
    prompt = PromptTemplate.from_template(template)
    filled_prompt = prompt.format(context_text=context_text)
    
    # ---------------------------------------------
    # MULTIMODAL INSTRUCTION BLOCK (VISION SUPPORT)
    # ---------------------------------------------
    content_blocks = [{"type": "text", "text": filled_prompt}]
    
    # Attach actual image files to the LLM context if available
    for b64 in images_b64:
        content_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"}
        })
        
    human_msg = HumanMessage(content=content_blocks)
    
    # Ambil seluruh API Key Cadangan
    keys = get_all_google_keys()
    if not keys:
         raise Exception("❌ GOOGLE_API_KEY tidak ditemukan di .env!")
    
    last_err = None
    for idx, g_key in enumerate(keys):
        try:
            # Re-initiate LLM untuk API Key saat ini (Multi-Key Rotator)
            os.environ["GOOGLE_API_KEY"] = g_key
            
            llm = ChatGoogleGenerativeAI(
                model=DEFAULT_GENERATOR_MODEL, 
                temperature=DEFAULT_GENERATOR_TEMPERATURE,
                google_api_key=g_key
            )
            
            # Execute AI Generation Process
            response = llm.invoke([human_msg])
            
            # Parse object respons to String
            parser = StrOutputParser()
            generated_result = parser.invoke(response)
            
            return generated_result
            
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "exhausted" in err_msg or "quota" in err_msg:
                last_err = e
                print(f"⚠️ [WARNING] Quota limit tercapai pada Key Engine ke-{idx + 1}. Mencoba failover ke Key berikutnya...")
                time.sleep(1) # Jeda bernafas aman
                continue
            else:
                raise e # Lemparkan error ke UI jika bukan masalah Quota Limit!
                
    # Jika loop berakhir tapi tidak pernah ter-RETURN, artinya seluruh key habis!
    raise Exception(f"🚨 SELURUH ({len(keys)}) GOOGLE API KEY TELAH MENCAPAI BATAS LIMIT HARIAN. Silakan istirahatkan server, atau tambahkan GOOGLE_API_KEY_5 dst di file .env. Error Terakhir: {str(last_err)}")
