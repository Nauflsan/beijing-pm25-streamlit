"""
konfigurasi.py - SATU-SATUNYA tempat semua konstanta proyek.

Tag komentar yang dipakai di seluruh proyek:
  # [UBAH]         aman diubah (tertulis apa lagi yang ikut harus diubah)
  # [TERKAIT]      kalau ini diubah, ubah juga bagian lain yang disebut
  # [JANGAN UBAH]  diubah = proyek rusak / hasil tidak konsisten

Setelah mengubah parameter MODEL atau FITUR, jalankan ulang:
  python -m model.latih_semua_model --penuh --ulang
"""
import os
from pathlib import Path

# =============================================================================
# 1. PATH
# =============================================================================
FOLDER_PROYEK = Path(__file__).resolve().parent                     # [JANGAN UBAH]
FOLDER_DATA = FOLDER_PROYEK / "data"                                # [JANGAN UBAH]
FILE_CSV = FOLDER_DATA / "PRSA_Beijing_PM25_2010_2014_clean.csv"    # [UBAH] kalau nama file CSV berbeda
FOLDER_ARTEFAK = FOLDER_PROYEK / "artifacts"                        # [TERKAIT] .gitignore & halaman membaca dari sini
FOLDER_ARTEFAK_DUMMY = FOLDER_PROYEK / "artifacts_dummy"           # hasil uji cepat (BUKAN hasil asli)
FOLDER_LOG = FOLDER_PROYEK / "logs"
# Hanya untuk menguji TAMPILAN dengan artefak dummy: set variabel lingkungan PM25_DUMMY=1 sebelum streamlit run.
PAKAI_ARTEFAK_DUMMY = os.environ.get("PM25_DUMMY") == "1"                          # [JANGAN UBAH]
FOLDER_ARTEFAK_AKTIF = FOLDER_ARTEFAK_DUMMY if PAKAI_ARTEFAK_DUMMY else FOLDER_ARTEFAK   # [TERKAIT] semua halaman membaca dari sini
SUBFOLDER_MODEL = "models"                                          # artifacts/models/*.joblib
NAMA_FILE_HASIL = "hasil.json"
NAMA_FILE_PREDIKSI_UJI = "prediksi_uji.csv"

# =============================================================================
# 2. KOLOM DATASET
# =============================================================================
KOLOM_TARGET = "pm2.5"            # [JANGAN UBAH] ada titik -> Altair butuh salinan bernama pm25
KOLOM_TARGET_ALTAIR = "pm25"      # [TERKAIT] utilitas_data.tambah_kolom_altair, grafik.py
KOLOM_ID = "No"                   # tidak dipakai sebagai fitur
KOLOM_CUACA_NUMERIK = ["DEWP", "TEMP", "PRES", "Iws", "Is", "Ir"]   # [TERKAIT] fitur_waktu.py
KOLOM_ARAH_ANGIN = "cbwd"
KELAS_ARAH_ANGIN = ["NE", "NW", "SE", "cv"]    # [TERKAIT] OneHotEncoder + form prediksi

# =============================================================================
# 3. SPLIT WAKTU, SEED, FITUR
# =============================================================================
TAHUN_UJI_MULAI = 2014   # [UBAH] latih = tahun < ini, uji = tahun >= ini. Latih ulang semua model kalau diubah
SEED = 42                # [UBAH] random_state semua model; latih ulang kalau diubah

LAG_JAM = [1, 2, 3, 24]              # [UBAH] [TERKAIT] fitur_waktu.py, halaman Prediksi (butuh riwayat >= max(LAG_JAM) jam)
JENDELA_ROLLING_JAM = [3, 24]        # [UBAH] rata-rata bergulir (dihitung dari jam-jam SEBELUM jam target)
AMBANG_POLUSI_PARAH = 150.0          # [UBAH] ug/m3, dipakai "performa saat polusi parah" (sama dengan notebook P5)

# =============================================================================
# 4. PARAMETER MODEL (selain Random Forest, yang ada di PROFIL_LATIH)
# =============================================================================
RIDGE_ALPHA = 10.0
DT_MAX_DEPTH = 10
DT_MIN_SAMPLES_LEAF = 20
HGB_LEARNING_RATE = 0.08
HGB_MAX_LEAF_NODES = 31
HGB_MIN_SAMPLES_LEAF = 40
HGB_L2 = 1.0
N_JOBS = -1   # [UBAH] jumlah thread RF. Kalau laptop jadi lemot waktu training, ganti 2

NAMA_MODEL = {
    "ridge": "Ridge Regression",
    "dt": "Decision Tree",
    "rf": "Random Forest",
    "hgb": "HistGradientBoosting",
    "rf_pso": "Random Forest + PSO",
}   # [TERKAIT] semua halaman membaca nama dari sini
URUTAN_MODEL = ["ridge", "dt", "rf", "hgb", "rf_pso"]
MODE_FITUR = {"A": "Mode A: cuaca + waktu (tanpa riwayat PM2.5)",
              "B": "Mode B: Mode A + lag & rata-rata bergulir PM2.5"}

# Profil latih. --cepat = uji alur (hasil TIDAK dipakai untuk laporan), --penuh = hasil final.
PROFIL_LATIH = {
    "penuh": dict(                      # [UBAH]
        rf_n_estimators=100, rf_max_depth=14, rf_min_samples_leaf=10, rf_max_features=0.6,
        hgb_max_iter=200, cv_fold=3,
        pso_partikel=6, pso_iterasi=5, pso_sampel_maks=8000, pso_fold=3,
        perm_repeat=3, perm_sampel=3000, pd_sampel=1000,
    ),
    "cepat": dict(
        rf_n_estimators=40, rf_max_depth=12, rf_min_samples_leaf=15, rf_max_features=0.6,
        hgb_max_iter=80, cv_fold=2,
        pso_partikel=3, pso_iterasi=2, pso_sampel_maks=3000, pso_fold=2,
        perm_repeat=2, perm_sampel=1500, pd_sampel=500,
    ),
}
# [TERKAIT] Ukuran file RF ~ n_estimators x (2^max_depth atau N/min_samples_leaf). Kalau ada file > 50 MB,
#           turunkan rf_max_depth / naikkan rf_min_samples_leaf, lalu latih ulang (--ulang).

# =============================================================================
# 5. PSO (Random Forest + PSO, hanya Mode B)
# =============================================================================
PSO_BATAS = {                 # [UBAH] (batas bawah, batas atas); semua bilangan bulat
    "n_estimators": (50, 120),
    "max_depth": (6, 16),
    "min_samples_leaf": (5, 40),
}   # [TERKAIT] batas ini juga menentukan ukuran file model rf_pso_B
PSO_W = 0.6     # [UBAH] inersia (nilai dari notebook P5)
PSO_C1 = 1.5    # [UBAH] tarikan ke posisi terbaik partikel sendiri
PSO_C2 = 1.5    # [UBAH] tarikan ke posisi terbaik kawanan
# Jumlah partikel, iterasi, sampel, fold ada di PROFIL_LATIH (pso_*).

# Bobot relatif HANYA untuk perkiraan sisa waktu di log (perkiraan kasar, bukan hasil ukur)
BOBOT_ETA = {"ridge": 1, "dt": 2, "rf": 40, "hgb": 15, "rf_pso": 40}   # [UBAH] bebas, tidak mempengaruhi hasil

# =============================================================================
# 6. KATEGORI KUALITAS UDARA (AQI PM2.5, US EPA)
# =============================================================================
VERSI_AMBANG_AKTIF = "2024"   # [UBAH] "2024" (revisi EPA, efektif 6 Mei 2024) atau "2012" (ambang lama)
NAMA_KATEGORI = ["Baik", "Sedang", "Tidak Sehat bagi Kelompok Sensitif", "Tidak Sehat",
                 "Sangat Tidak Sehat", "Berbahaya"]
NAMA_KATEGORI_PENDEK = ["Baik", "Sedang", "TSK", "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]
# Warna resmi AQI EPA (hijau, kuning, oranye, merah, ungu, marun). [UBAH] boleh disesuaikan agar nyaman
# di mode gelap; [TERKAIT] tema_langit_beijing.py memakai daftar ini.
WARNA_KATEGORI = ["#00E400", "#FFFF00", "#FF7E00", "#FF0000", "#8F3F97", "#7E0023"]
# Batas ATAS tiap kategori (ug/m3, rata-rata 24 jam). Kategori terakhir tidak punya batas atas.
AMBANG_BATAS_ATAS = {
    "2024": [9.0, 35.4, 55.4, 125.4, 225.4],
    "2012": [12.0, 35.4, 55.4, 150.4, 250.4],
}   # [JANGAN UBAH] angka mengikuti sumber di bawah
SUMBER_AMBANG = ("US EPA, 'Final Updates to the Air Quality Index (AQI) for Particulate Matter' (fact sheet, 7 Feb 2024): "
                 "https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf")
TANGGAL_AKSES_SUMBER = "21 November 2026"
CATATAN_AMBANG = ("Ambang AQI didefinisikan untuk rata-rata 24 jam. Di proyek ini ambang dipakai pada nilai PM2.5 "
                  "per jam sebagai pendekatan untuk pengelompokan, bukan sebagai AQI resmi.")

# =============================================================================
# 7. IDENTITAS PROYEK (tampil di Beranda)
# =============================================================================
NAMA_PROYEK = "Langit Beijing: Prediksi PM2.5"
MATA_KULIAH = "Machine Learning"
KAMPUS = "Universitas Pamulang"
NAMA_KELOMPOK = "Kelompok 1"                                  # [UBAH]
ANGGOTA = [{"nama": "Naufal Sausan Su'daa", "nim": "241011403033"}, {"nama": "Mohammad Arief Ardiansyah", "nim": "241011202280"}, {"nama": "Ibnu Ramadhan", "nim": "241011400490"}]            # [UBAH] tambah dict per anggota
DOSEN = "Farizi Ilham"                                          # [UBAH]
                           # [UBAH] catatan halaman wajib dari dosen (kalau ada)

# =============================================================================
# 8. SAKLAR HALAMAN TAMBAHAN
# =============================================================================
SAKLAR_HALAMAN_TAMBAHAN = {   # [UBAH] False = halaman tidak muncul di menu
    "pola_waktu_cuaca": True,
    "feature_engineering": True,
    "whatif_simulator": True,
}   # [TERKAIT] app.py membaca saklar ini

# =============================================================================
# 9. TAMPILAN (tema "Langit Beijing") DAN SUMBER DATA
# =============================================================================
# Tema TERANG saja (mode gelap dimatikan). [TERKAIT] .streamlit/config.toml memakai warna yang sama untuk latar/teks/aksen.
WARNA_AKSEN = "#2F6FAE"         # [UBAH] biru utama (tombol, garis aksen kartu)
WARNA_NETRAL = WARNA_AKSEN      # alias lama; dipakai grafik untuk deret tunggal
WARNA_LATAR = "#F5F8FC"         # [UBAH] latar halaman [TERKAIT] config.toml backgroundColor
WARNA_KARTU = "#FFFFFF"         # [UBAH] latar kartu/KPI
WARNA_TEKS = "#1F2D3D"          # [UBAH] teks utama [TERKAIT] config.toml textColor
WARNA_TEKS_PUDAR = "#5B6B7C"    # [UBAH] teks kecil/keterangan
WARNA_GARIS = "#DCE5EF"         # [UBAH] garis tepi kartu
GRADIEN_HEADER = ("#E6F1FC", "#C9E0F6", "#A9CCEF")   # [UBAH] biru langit untuk header halaman
WARNA_SERI = ["#2F6FAE", "#F28E2B", "#8E5BB5", "#2BA58F", "#D6453D", "#7F8C99"]   # [UBAH] warna deret grafik
FONT_JUDUL = "Sora"             # [UBAH] font Google Fonts untuk judul [TERKAIT] tema_langit_beijing.py
FONT_ISI = "Nunito Sans"        # [UBAH] font Google Fonts untuk isi
SUMBER_DATASET = "[ISI] tulis sumber dataset yang dipakai kelompok (nama, penulis, tahun, tautan)"   # [UBAH]
STASIUN_CATATAN = ("Satu stasiun pemantauan (US Embassy Beijing, kira-kira 39,9489 LU 116,4691 BT). "
                   "Koordinat ini perkiraan; dataset tidak punya kolom koordinat.")   # [UBAH]
