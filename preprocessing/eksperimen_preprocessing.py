"""
eksperimen_preprocessing.py - eksperimen preprocessing (Ridge): cara mengisi data kosong, scaling, dan log target.

Hasilnya masuk hasil.json["eksperimen"]["isi_kosong" | "skala" | "log_target"], dibaca halaman 4 (Preprocessing).
"""
import konfigurasi as cfg
from preprocessing import fitur_waktu as fw
from preprocessing.eksperimen_umum import skor_ridge

T = cfg.KOLOM_TARGET


def _eksp_skala_dan_log(latih, uji):
    out_skala, out_log = {}, {}
    for mode in ("A", "B"):
        num, kat = fw.FITUR_NUMERIK[mode], fw.FITUR_KATEGORIK
        out_skala[mode] = {"dengan_skala": skor_ridge(latih, uji, num, kat, skala=True),
                           "tanpa_skala": skor_ridge(latih, uji, num, kat, skala=False)}
        out_log[mode] = {"skala_asli": skor_ridge(latih, uji, num, kat, skala=True),
                         "target_log1p": skor_ridge(latih, uji, num, kat, skala=True, target_log=True)}
    return out_skala, out_log


def _eksp_isi_kosong(df_mentah, layak_acuan):
    """
    Fungsi: bandingkan cara mengisi PM2.5 kosong untuk fitur lag (Ridge Mode B). Dievaluasi pada baris yang SAMA
            (baris layak dari metode ffill) supaya adil. 'interpolasi' memakai masa depan = BOCOR, hanya pembanding.
    """
    out = {}
    num, kat = fw.FITUR_NUMERIK["B"], fw.FITUR_KATEGORIK
    for nama, metode in [("ffill", "ffill"), ("median_latih", "median_latih"), ("interpolasi_bocor", "interpolasi")]:
        d = fw.siapkan_data(df_mentah, metode_isi=metode)
        d = d[layak_acuan]
        latih, uji = d[d["year"] < cfg.TAHUN_UJI_MULAI], d[d["year"] >= cfg.TAHUN_UJI_MULAI]
        out[nama] = skor_ridge(latih, uji, num, kat)
    return out
