"""
kategori_udara.py - mengubah nilai PM2.5 menjadi kategori kualitas udara (AQI PM2.5 US EPA).

Ambang, warna, sumber, dan tanggal akses ada di konfigurasi.py. Versi ambang bisa diganti lewat
konfigurasi.VERSI_AMBANG_AKTIF ("2024" atau "2012").
"""
import numpy as np

import konfigurasi as cfg

# Ringkasan umum untuk tampilan. BUKAN saran medis.
# [UBAH] Sebelum dikutip di laporan, cocokkan kata-katanya dengan https://www.airnow.gov/aqi/aqi-basics/
SARAN_KESEHATAN = [
    "Kualitas udara baik. Aktivitas di luar ruangan aman dilakukan seperti biasa.",
    "Kualitas udara dapat diterima. Orang yang sangat sensitif terhadap polusi sebaiknya mempertimbangkan "
    "mengurangi aktivitas berat yang lama di luar ruangan.",
    "Kelompok sensitif (anak-anak, lansia, penderita asma, penyakit jantung atau paru) sebaiknya mengurangi "
    "aktivitas berat di luar ruangan. Masyarakat umum umumnya masih aman.",
    "Semua orang sebaiknya mengurangi aktivitas berat di luar ruangan; kelompok sensitif lebih baik menghindarinya. "
    "Kalau harus keluar, pertimbangkan masker yang cocok untuk partikel halus (N95/KN95).",
    "Hindari aktivitas fisik di luar ruangan. Kelompok sensitif sebaiknya tetap di dalam ruangan. "
    "Kurangi masuknya udara luar ke dalam rumah.",
    "Kondisi darurat kesehatan. Tetap di dalam ruangan dengan jendela tertutup, gunakan pembersih udara kalau ada, "
    "dan hubungi tenaga kesehatan kalau muncul gejala seperti sesak napas atau batuk berat.",
]


def _batas_atas(versi=None):
    """Fungsi: batas atas tiap kategori udara untuk satu versi ambang. Input: versi ('2024'/'2012') atau None (pakai versi aktif). Output: array float."""
    return np.asarray(cfg.AMBANG_BATAS_ATAS[versi or cfg.VERSI_AMBANG_AKTIF], dtype=float)


def indeks_kategori(nilai, versi=None):
    """
    Fungsi: nilai PM2.5 -> indeks kategori 0..5 (0 = Baik, 5 = Berbahaya).
    Input : angka atau array (ug/m3). Nilai dipotong (bukan dibulatkan) ke 1 desimal, seperti aturan AQI EPA.
    Output: int, atau array int kalau input array.
    """
    arr = np.asarray(nilai, dtype=float)
    dipotong = np.floor(arr * 10 + 1e-9) / 10
    idx = np.searchsorted(_batas_atas(versi), dipotong, side="left")
    return int(idx) if np.ndim(arr) == 0 else idx


def info_kategori(idx, versi=None):
    """
    Fungsi: detail satu kategori. Input: indeks 0..5. Output: dict(indeks, nama, nama_pendek, warna,
            batas_bawah, batas_atas (None untuk kategori terakhir), saran).
    """
    idx = int(idx)
    batas = _batas_atas(versi)
    bawah = 0.0 if idx == 0 else float(batas[idx - 1]) + 0.1
    atas = float(batas[idx]) if idx < len(batas) else None
    return {"indeks": idx, "nama": cfg.NAMA_KATEGORI[idx], "nama_pendek": cfg.NAMA_KATEGORI_PENDEK[idx],
            "warna": cfg.WARNA_KATEGORI[idx], "batas_bawah": round(bawah, 1), "batas_atas": atas,
            "saran": SARAN_KESEHATAN[idx]}


def kategori_dari_nilai(nilai, versi=None):
    """Fungsi: gabungan indeks_kategori + info_kategori untuk SATU nilai. Output: dict info kategori."""
    return info_kategori(indeks_kategori(float(nilai), versi), versi)


def tabel_ambang(versi=None):
    """Fungsi: daftar semua kategori (untuk tabel di halaman). Output: list of dict info_kategori."""
    return [info_kategori(i, versi) for i in range(len(cfg.NAMA_KATEGORI))]
