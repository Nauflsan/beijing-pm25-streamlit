"""
utilitas_data.py - memuat dan memeriksa dataset, ringkasan dataset, penyimpan JSON aman.

File ini sengaja TIDAK mengimpor streamlit supaya bisa dipakai skrip latih.
Caching untuk app (st.cache_data) dipasang di halaman/app, bukan di sini.
"""
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

import konfigurasi as cfg

KOLOM_WAJIB = ["year", "month", "day", "hour", cfg.KOLOM_TARGET, *cfg.KOLOM_CUACA_NUMERIK, cfg.KOLOM_ARAH_ANGIN]


def validasi_kolom(df):
    """Fungsi: cek semua kolom wajib ada. Input: DataFrame. Output: (ok: bool, kolom_hilang: list)."""
    hilang = [k for k in KOLOM_WAJIB if k not in df.columns]
    return (len(hilang) == 0, hilang)


def muat_data_mentah(path=None):
    """
    Fungsi: baca CSV, buat kolom 'waktu', urutkan kronologis.
    Input : path CSV (default cfg.FILE_CSV).
    Output: DataFrame mentah (13 kolom asli + 'waktu'); arah angin bertipe object (aman untuk pandas 3).
    """
    path = Path(path) if path else cfg.FILE_CSV
    if not path.exists():
        raise FileNotFoundError(f"File data tidak ditemukan: {path}\nTaruh CSV di folder data/ (lihat konfigurasi.FILE_CSV).")
    df = pd.read_csv(path)
    ok, hilang = validasi_kolom(df)
    if not ok:
        raise ValueError(f"Kolom wajib tidak ada di CSV: {hilang}")
    df["waktu"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
    df = df.sort_values("waktu").reset_index(drop=True)
    df[cfg.KOLOM_ARAH_ANGIN] = df[cfg.KOLOM_ARAH_ANGIN].astype(object)
    return df


def tambah_kolom_altair(df):
    """
    Fungsi: salin kolom 'pm2.5' ke 'pm25'. Altair/Vega-Lite menganggap titik sebagai properti bersarang
            sehingga grafik kosong. Judul sumbu tetap ditulis "pm2.5" di grafik.
    Input : DataFrame. Output: salinan DataFrame dengan kolom tambahan 'pm25'.
    """
    d = df.copy()
    d[cfg.KOLOM_TARGET_ALTAIR] = d[cfg.KOLOM_TARGET]
    return d


def panjang_kosong_terpanjang(seri):
    """Fungsi: panjang deretan nilai kosong berurutan terpanjang. Input: Series. Output: int (jam)."""
    kosong = seri.isna().to_numpy()
    terpanjang = saat_ini = 0
    for v in kosong:
        saat_ini = saat_ini + 1 if v else 0
        terpanjang = max(terpanjang, saat_ini)
    return int(terpanjang)


def ringkasan_dataset(df):
    """
    Fungsi: angka-angka ringkas dataset (dihitung dari CSV, bukan di-hardcode).
    Input : DataFrame hasil muat_data_mentah. Output: dict.
    """
    p = df[cfg.KOLOM_TARGET]
    q1, q3 = p.quantile([0.25, 0.75])
    batas_iqr = q3 + 1.5 * (q3 - q1)
    return {
        "n_baris": int(len(df)),
        "n_kolom_asli": int(df.shape[1] - 1),   # tanpa kolom 'waktu' buatan
        "waktu_awal": str(df["waktu"].min()),
        "waktu_akhir": str(df["waktu"].max()),
        "n_kosong_target": int(p.isna().sum()),
        "persen_kosong_target": float(p.isna().mean() * 100),
        "panjang_kosong_terpanjang_jam": panjang_kosong_terpanjang(p),
        "kosong_kolom_lain": int(df.drop(columns=[cfg.KOLOM_TARGET]).isna().sum().sum()),
        "pm25_mean": float(p.mean()), "pm25_median": float(p.median()),
        "pm25_skew": float(p.skew()), "pm25_max": float(p.max()),
        "batas_outlier_iqr": float(batas_iqr), "n_outlier_iqr": int((p > batas_iqr).sum()),
    }


def fmt_id(angka, desimal=2):
    """
    Fungsi: format angka gaya Indonesia (titik ribuan, koma desimal). Input: angka (atau None), desimal. Output: str.
    Contoh: fmt_id(1234.567, 1) -> '1.234,6'.
    """
    if angka is None:
        return "-"
    teks = f"{angka:,.{desimal}f}"
    return teks.replace(",", "#").replace(".", ",").replace("#", ".")


def _bersih(x):
    """Ubah tipe numpy/NaN jadi tipe JSON biasa (NaN/inf -> None)."""
    if isinstance(x, dict):
        return {str(k): _bersih(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_bersih(v) for v in x]
    if isinstance(x, np.ndarray):
        return [_bersih(v) for v in x.tolist()]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (pd.Timestamp,)):
        return str(x)
    return x


def simpan_json_aman(path, data):
    """
    Fungsi: tulis JSON secara atomik (tulis ke file sementara lalu ganti) supaya hasil.json tidak rusak
            kalau skrip terhenti di tengah jalan.
    Input : path, dict. Output: -
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sementara = path.with_suffix(path.suffix + ".tmp")
    with open(sementara, "w", encoding="utf-8") as f:
        json.dump(_bersih(data), f, ensure_ascii=False, indent=1)
    os.replace(sementara, path)


def muat_json(path):
    """Fungsi: baca JSON. Input: path. Output: dict ({} kalau file belum ada)."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)
