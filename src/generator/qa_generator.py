from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from src.config.settings import DEFAULT_GENERATOR_MODEL, DEFAULT_GENERATOR_TEMPERATURE

def generate_questions(topic, context_text, item_count, hots_count, lots_count, question_type, pg_options="A-E"):
    """Menggunakan LLM Gemini untuk meracik jenis soal tertentu secara spesifik (Batching)."""
    
    llm = ChatGoogleGenerativeAI(
        model=DEFAULT_GENERATOR_MODEL, 
        temperature=DEFAULT_GENERATOR_TEMPERATURE 
    )
    
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

   - [ ] [Statement/Pilihan 1]
   - [ ] [Statement/Pilihan 2]
   - [ ] [Statement/Pilihan 3]
   - ..."""
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
2. Filter & Format: ABAIKAN instruksi penggunaan modul. Demi menjaga agar layout tetap sempurna di Web dan Word, Anda WAJIB menggunakan karakter UNIVERSAL UNICODE Asli untuk mencetak angka rumus/kimia (Gunakan native subscript/superscript asli Contoh: `H₂O`, `x²`, `C₂H₆ → C₂H₅Cl`). PERINGATAN KERAS: DILARANG MENGGUNAKAN sintaks LaTeX (seperti `$`, `$$`, `\\rightarrow`) dan DILARANG MENGGUNAKAN karakter garis bawah `_` (seperti `H_2O`) karena akan menghancurkan kerangka Web Markdown!
3. Format Markdown UI: Agar opsi jawaban BISA DIBACA KE BAWAH bukan menyamping, WAJIB taruh ENTER KOSONG sebelum mulai Opsi A. Dan WAJIB gunakan bullet list (tanda strip `- `) pada AWAL setiap opsi jawaban, contoh: "- A. Jawaban". JANGAN PERNAH gunakan A. B. C. yang nyambung sebaris!
4. Keseimbangan Teori & Hitungan: JIKA teks referensi mengandung Rumus, Angka, atau Studi Kasus Perhitungan, Anda WAJIB membagi porsi agar soal yang dihasilkan TIDAK HANYA TEORI, tetapi juga memuat soal HITUNGAN KUANTITATIF / penerapan rumus numerik (Sangat diwajibkan untuk soal HOTS dan Uraian Singkat)!
5. Gaya Bahasa Ujian Independen: JANGAN PERNAH menyalin atau menggunakan frasa meta-referensi seperti "Menurut modul...", "Berdasarkan teks di atas...", "Di dalam dokumen disebutkan bahwa...", dsb. Susunlah narasi pertanyaan secara mandiri layaknya Soal Ujian Nasional yang berdiri sendiri tanpa menyinggung keberadaan 'modul' atau 'teks bacaan' di mata peserta ujian.

KONTEKS MATERI REFERENSI DATABASE KAMI:
{{context_text}}

OUTPUT WAJIB MENGANDUNG STRUKTUR INI SAJA (Tanpa basa-basi intro):

### 📋 KISI-KISI MATERI ({question_type})
(Tuangkan ringkasan indikator soal yang digunakan. WAJIB cantumkan Referensi Dokumen [Nama File PDF & Halaman] untuk masing-masing butir kisi-kisi sebagai Ground Truth!)

{type_instruction}

### 🎯 KUNCI JAWABAN & PEMBAHASAN DETAIL
(Wajib berisi daftar kunci jawaban setiap nomor dan lampirkan alasan argumentatif mengapa pilihan tersebut valid merujuk pada teks referensi).
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    # Execute AI Generation Process
    generated_result = chain.invoke({
        "context_text": context_text
    })
    
    return generated_result
