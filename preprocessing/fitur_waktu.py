"""
fitur_waktu.py - pembuatan fitur (siklik jam/bulan, lag, rolling), split waktu, dan Pipeline preprocessing.

Dua set fitur:
  Mode A : cuaca + waktu siklik + arah angin (TANPA riwayat PM2.5)
  Mode B : Mode A + lag PM2.5 + rata-rata bergulir PM2.5

Aturan anti-kebocoran (data bocor = model "mengintip" masa depan):
  1. Nilai PM2.5 kosong diisi ffill (hanya memakai masa lalu), HANYA untuk membentuk fitur lag/rolling.
  2. Baris yang target aslinya kosong TIDAK dipakai sebagai target latih maupun uji.
  3. Rolling dihitung dari seri yang sudah digeser 1 jam (shift dulu, baru rolling), jadi jam target tidak ikut.
  4. Imputer dan scaler ada DI DALAM Pipeline, sehingga hanya belajar dari data latih.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import konfigurasi as cfg

FITUR_CUACA = list(cfg.KOLOM_CUACA_NUMERIK)
FITUR_SIKLIK = ["jam_sin", "jam_cos", "bulan_sin", "bulan_cos"]
FITUR_LAG = [f"pm25_lag{k}" for k in cfg.LAG_JAM]                  # [TERKAIT] konfigurasi.LAG_JAM
FITUR_ROLLING = [f"pm25_rata{w}" for w in cfg.JENDELA_ROLLING_JAM]  # [TERKAIT] konfigurasi.JENDELA_ROLLING_JAM
FITUR_NUMERIK = {                                                   # [JANGAN UBAH] urutan = urutan kolom model
    "A": FITUR_CUACA + FITUR_SIKLIK,
    "B": FITUR_CUACA + FITUR_SIKLIK + FITUR_LAG + FITUR_ROLLING,
}
FITUR_KATEGORIK = [cfg.KOLOM_ARAH_ANGIN]
RIWAYAT_MINIMAL = max(max(cfg.LAG_JAM), max(cfg.JENDELA_ROLLING_JAM))   # jam riwayat yang dibutuhkan Mode B


def daftar_fitur(mode):
    """Fungsi: nama kolom input model. Input: 'A' atau 'B'. Output: list (numerik dulu, lalu arah angin)."""
    return FITUR_NUMERIK[mode] + FITUR_KATEGORIK


def hitung_fitur_pm(pm_diisi):
    """
    Fungsi: fitur lag dan rata-rata bergulir dari seri PM2.5 (yang sudah diisi).
    Input : Series PM2.5 terurut waktu per jam. Output: DataFrame (kolom FITUR_LAG + FITUR_ROLLING).
    """
    keluar = pd.DataFrame(index=pm_diisi.index)
    for k in cfg.LAG_JAM:
        keluar[f"pm25_lag{k}"] = pm_diisi.shift(k)
    geser = pm_diisi.shift(1)   # shift DULU supaya jam target tidak ikut rata-rata
    for w in cfg.JENDELA_ROLLING_JAM:
        keluar[f"pm25_rata{w}"] = geser.rolling(w, min_periods=w).mean()
    return keluar


def isi_pm(pm, tahun, metode="ffill"):
    """
    Fungsi: mengisi PM2.5 kosong untuk membentuk fitur lag.
    Input : pm (Series), tahun (Series), metode:
            'ffill'        -> teruskan nilai terakhir (hanya masa lalu)  [DIPAKAI]
            'median_latih' -> median data latih (pembanding)
            'interpolasi'  -> interpolasi linear, MEMAKAI MASA DEPAN = BOCOR (hanya pembanding di halaman Preprocessing)
    Output: Series terisi.
    """
    if metode == "ffill":
        return pm.ffill()
    if metode == "median_latih":
        return pm.fillna(pm[tahun < cfg.TAHUN_UJI_MULAI].median())
    if metode == "interpolasi":
        return pm.interpolate(limit_direction="both")
    raise ValueError(f"metode isi tidak dikenal: {metode}")


def siapkan_data(df_mentah, metode_isi="ffill"):
    """
    Fungsi: tambah semua fitur turunan ke data mentah.
    Input : DataFrame dari utilitas_data.muat_data_mentah (terurut waktu), metode_isi (lihat isi_pm).
    Output: DataFrame dengan kolom tambahan: ada_target, pm_diisi, fitur siklik, lag, rolling, layak_model.
            'layak_model' = target asli ada DAN semua fitur Mode B lengkap (dipakai kedua mode agar adil).
    """
    d = df_mentah.copy()
    d["ada_target"] = d[cfg.KOLOM_TARGET].notna()
    d["pm_diisi"] = isi_pm(d[cfg.KOLOM_TARGET], d["year"], metode_isi)
    d["jam_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
    d["jam_cos"] = np.cos(2 * np.pi * d["hour"] / 24)
    d["bulan_sin"] = np.sin(2 * np.pi * d["month"] / 12)
    d["bulan_cos"] = np.cos(2 * np.pi * d["month"] / 12)
    fitur_pm = hitung_fitur_pm(d["pm_diisi"])
    for kolom in fitur_pm.columns:
        d[kolom] = fitur_pm[kolom]
    d["layak_model"] = d["ada_target"] & d[FITUR_NUMERIK["B"]].notna().all(axis=1)
    return d


def bagi_waktu(d, tahun_uji=None):
    """
    Fungsi: split berdasarkan waktu. Input: DataFrame dari siapkan_data. Output: (latih, uji) hanya baris layak.
            latih = tahun < tahun_uji, uji = tahun >= tahun_uji. [TERKAIT] konfigurasi.TAHUN_UJI_MULAI
    """
    tahun_uji = tahun_uji or cfg.TAHUN_UJI_MULAI
    layak = d[d["layak_model"]]
    return layak[layak["year"] < tahun_uji].copy(), layak[layak["year"] >= tahun_uji].copy()


def buat_preprocessor_umum(kolom_num, kolom_kat, skala=False):
    """
    Fungsi: ColumnTransformer: numerik -> imputer median (+ StandardScaler bila skala), arah angin -> one-hot.
    Input : daftar kolom numerik, daftar kolom kategorik, skala (bool). Output: ColumnTransformer (belum di-fit).
    """
    langkah_num = [("imputer", SimpleImputer(strategy="median"))]
    if skala:
        langkah_num.append(("scaler", StandardScaler()))
    bagian = []
    if kolom_num:
        bagian.append(("num", Pipeline(langkah_num), list(kolom_num)))
    if kolom_kat:
        bagian.append(("kat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(categories=[cfg.KELAS_ARAH_ANGIN] * len(kolom_kat),
                                  handle_unknown="ignore", sparse_output=False)),
        ]), list(kolom_kat)))
    return ColumnTransformer(bagian)


def buat_preprocessor(mode, skala=False):
    """Fungsi: preprocessor standar untuk Mode A/B. Input: mode, skala. Output: ColumnTransformer."""
    return buat_preprocessor_umum(FITUR_NUMERIK[mode], FITUR_KATEGORIK, skala)


def buat_pipeline(estimator, mode, skala=False):
    """
    Fungsi: Pipeline (preprocessing + model) yang disimpan utuh ke .joblib, jadi app tidak perlu
            menulis ulang preprocessing. Input: estimator sklearn, mode, skala (True untuk Ridge).
    Output: Pipeline [('prep', ...), ('model', estimator)].
    """
    return Pipeline([("prep", buat_preprocessor(mode, skala)), ("model", estimator)])


def buat_baris_fitur(waktu, cuaca, riwayat_pm25=None, mode="A"):
    """
    Fungsi: membentuk SATU baris fitur dari input pengguna (dipakai halaman Prediksi), dengan rumus yang
            sama persis seperti siapkan_data (sudah diuji di uji_cepat.py).
    Input : waktu (pd.Timestamp jam yang diprediksi);
            cuaca (dict: DEWP, TEMP, PRES, Iws, Is, Ir, cbwd);
            riwayat_pm25 (list PM2.5 per jam, urut LAMA -> BARU, nilai terakhir = 1 jam sebelum 'waktu';
            minimal RIWAYAT_MINIMAL nilai; hanya untuk Mode B);
            mode 'A'/'B'.
    Output: DataFrame 1 baris dengan kolom = daftar_fitur(mode).
    """
    waktu = pd.Timestamp(waktu)
    if cuaca[cfg.KOLOM_ARAH_ANGIN] not in cfg.KELAS_ARAH_ANGIN:
        raise ValueError(f"cbwd harus salah satu dari {cfg.KELAS_ARAH_ANGIN}")
    baris = {k: float(cuaca[k]) for k in FITUR_CUACA}
    baris["jam_sin"] = np.sin(2 * np.pi * waktu.hour / 24)
    baris["jam_cos"] = np.cos(2 * np.pi * waktu.hour / 24)
    baris["bulan_sin"] = np.sin(2 * np.pi * waktu.month / 12)
    baris["bulan_cos"] = np.cos(2 * np.pi * waktu.month / 12)
    if mode == "B":
        if riwayat_pm25 is None or len(riwayat_pm25) < RIWAYAT_MINIMAL:
            raise ValueError(f"Mode B butuh riwayat PM2.5 minimal {RIWAYAT_MINIMAL} jam terakhir.")
        h = [float(v) for v in riwayat_pm25]
        for k in cfg.LAG_JAM:
            baris[f"pm25_lag{k}"] = h[-k]
        for w in cfg.JENDELA_ROLLING_JAM:
            baris[f"pm25_rata{w}"] = float(np.mean(h[-w:]))
    baris[cfg.KOLOM_ARAH_ANGIN] = cuaca[cfg.KOLOM_ARAH_ANGIN]
    return pd.DataFrame([baris])[daftar_fitur(mode)]
