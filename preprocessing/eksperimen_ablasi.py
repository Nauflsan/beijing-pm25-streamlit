"""
eksperimen_ablasi.py - ablasi kelompok fitur (Ridge, Mode B): hasil jika satu kelompok fitur dibuang.

Hasilnya masuk hasil.json["eksperimen"]["ablasi"], dibaca halaman 13 (Feature Engineering).
"""
from preprocessing import fitur_waktu as fw
from preprocessing.eksperimen_umum import skor_ridge


def _eksp_ablasi(latih, uji):
    """Fungsi: Mode B tanpa satu kelompok fitur. Output: {nama_varian: metrik}."""
    penuh_num, kat = fw.FITUR_NUMERIK["B"], fw.FITUR_KATEGORIK
    varian = {
        "lengkap_mode_b": (penuh_num, kat),
        "tanpa_cuaca": ([f for f in penuh_num if f not in fw.FITUR_CUACA], kat),
        "tanpa_waktu_siklik": ([f for f in penuh_num if f not in fw.FITUR_SIKLIK], kat),
        "tanpa_arah_angin": (penuh_num, []),
        "tanpa_lag": ([f for f in penuh_num if f not in fw.FITUR_LAG], kat),
        "tanpa_rolling": ([f for f in penuh_num if f not in fw.FITUR_ROLLING], kat),
        "tanpa_lag_dan_rolling_(=mode_a)": (fw.FITUR_NUMERIK["A"], kat),
        "hanya_lag1": ([f for f in penuh_num if f == "pm25_lag1"], []),
    }
    return {nama: skor_ridge(latih, uji, num, k) for nama, (num, k) in varian.items() if num}
