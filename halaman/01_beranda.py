"""
halaman/01_beranda.py - Beranda: KPI, alur kerja, ringkasan temuan (dari hasil.json), identitas kelompok.

Data CSV -> KPI atas (dihitung langsung). hasil.json -> KPI model dan ringkasan temuan (tidak ada angka model yang ditulis tangan).
Kalau hasil.json belum ada, halaman tetap tampil dan memberi pesan ramah.
"""
import pandas as pd
import streamlit as st

import grafik
import konfigurasi as cfg
import kategori_udara as ku
import tema_langit_beijing as tema
import utilitas_app as ua

T = cfg.KOLOM_TARGET
df = ua.muat_data()
valid = df[T].dropna()
idx_rata = ku.indeks_kategori(valid.mean())

tema.header_halaman(cfg.NAMA_PROYEK, "Prediksi PM2.5 per jam di Beijing (2010-2014) dengan regresi time series, "
                                     "dibuat untuk diuji jujur, bukan sekadar terlihat bagus.")

# --- KPI data -----------------------------------------------------------------------------
jumlah = grafik.jumlah_per_kategori(valid)
persen_tidak_sehat = 100 * sum(jumlah[3:]) / sum(jumlah)
k1, k2, k3, k4 = st.columns(4)
with k1:
    tema.kartu_kpi("Jumlah pengamatan", ua.fmt(len(df), 0), f"{ua.fmt(df[T].isna().sum(), 0)} jam tanpa nilai pm2.5")
with k2:
    tema.kartu_kpi("Rentang data", f"{df['waktu'].dt.year.min()} - {df['waktu'].dt.year.max()}", "per jam, satu stasiun")
with k3:
    tema.kartu_kpi("Rata-rata pm2.5", f"{ua.fmt(valid.mean(), 1)} ug/m3", "rata-rata seluruh jam bernilai", idx_rata)
with k4:
    tema.kartu_kpi("Jam kategori Tidak Sehat atau lebih buruk", f"{ua.fmt(persen_tidak_sehat, 1)}%",
                   f"ambang AQI versi {cfg.VERSI_AMBANG_AKTIF}")

# --- KPI model (hasil.json) -----------------------------------------------------------------
hasil = ua.muat_hasil()
st.write("")
if hasil and "model" in hasil:
    if hasil.get("meta", {}).get("dummy"):
        st.warning("Ini hasil DUMMY (hanya untuk menguji tampilan). Angka model di bawah BUKAN hasil asli.")
    pem = hasil.get("pemenang", {})
    base = hasil["baseline"]["persistence_1jam"]["uji"]
    tahun = hasil["data"]["tahun_uji_mulai"]
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        if "B" in pem:
            mb = hasil["model"][pem["B"]]
            tema.kartu_kpi(f"RMSE model terbaik, Mode B", f"{ua.fmt(mb['uji']['rmse'])} ug/m3", f"{mb['nama']}, uji {tahun}")
    with m2:
        tema.kartu_kpi("RMSE baseline persistence 1 jam", f"{ua.fmt(base['rmse'])} ug/m3", "nilai jam lalu dipakai sebagai tebakan")
    with m3:
        if "A" in pem:
            ma = hasil["model"][pem["A"]]
            tema.kartu_kpi("R2 model terbaik, Mode A (tanpa riwayat)", ua.fmt(ma["uji"]["r2"], 3), f"{ma['nama']}, uji {tahun}")
    with m4:
        n_lat = hasil["data"]["n_latih"]
        tema.kartu_kpi("Baris latih / uji", f"{ua.fmt(n_lat, 0)} / {ua.fmt(hasil['data']['n_uji'], 0)}",
                       f"split waktu: uji = tahun {tahun} dan sesudahnya")
else:
    st.info(ua.PESAN_ARTEFAK_KOSONG)

# --- alur kerja -------------------------------------------------------------------------------
st.subheader("Alur kerja")
langkah = [
    ("Memahami data", "Kamus kolom, rentang waktu, data kosong. Halaman Tentang Dataset dan EDA Umum."),
    ("Menyiapkan data", "Isi data kosong tanpa mengintip masa depan, fitur waktu siklik, split berdasarkan waktu. Halaman Preprocessing dan PCA."),
    ("Melatih 5 model", "Ridge, Decision Tree, Random Forest, HistGradientBoosting, Random Forest + PSO, masing-masing dengan dan tanpa riwayat PM2.5."),
    ("Mengevaluasi", "MAE, RMSE, R2, error per bulan dan per kategori udara, fitur terpenting."),
    ("Menguji kejujuran", "Split acak vs split waktu, dibandingkan dengan baseline persistence, termasuk saat polusi parah."),
    ("Memprediksi", "Satu input dengan gauge dan saran kesehatan, atau banyak baris lewat unggah CSV."),
]
kolom = st.columns(3)
for i, (judul, isi) in enumerate(langkah):
    with kolom[i % 3]:
        tema.langkah_alur(i + 1, judul, isi)
        st.write("")

# --- ringkasan temuan -------------------------------------------------------------------------
st.subheader("Ringkasan temuan")
if hasil and "model" in hasil:
    for kalimat in ua.kalimat_temuan(hasil):
        st.markdown(f"- {kalimat}")
    st.caption("Kalimat di atas dibangun otomatis dari artifacts/hasil.json, jadi selalu sama dengan hasil training terakhir.")
else:
    st.write("Ringkasan temuan muncul setelah training selesai.")

# --- identitas ----------------------------------------------------------------------------------
st.subheader("Tentang proyek")
c1, c2 = st.columns([3, 2])
with c1:
    st.markdown(f"**Mata kuliah:** {cfg.MATA_KULIAH}  \n**Kampus:** {cfg.KAMPUS}  \n**Kelompok:** {cfg.NAMA_KELOMPOK}  \n"
                f"**Dosen pengampu:** {cfg.DOSEN}")
    if cfg.HALAMAN_WAJIB_DOSEN and cfg.HALAMAN_WAJIB_DOSEN != "[ISI]":
        st.markdown(f"**Halaman wajib dari dosen:** {cfg.HALAMAN_WAJIB_DOSEN}")
with c2:
    st.dataframe(pd.DataFrame(cfg.ANGGOTA).rename(columns={"nama": "Nama anggota", "nim": "NIM"}), hide_index=True, width="stretch")
st.caption("Cakupan: satu stasiun, 2010-2014, bukan prediksi real-time. Aplikasi ini bahan belajar, bukan alat keputusan kesehatan.")
