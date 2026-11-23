"""
eksperimen_umum.py - pembantu bersama semua eksperimen ringan: melatih Ridge lalu menilainya di data uji.

Dipakai oleh eksperimen_preprocessing.py, eksperimen_pca.py, eksperimen_ablasi.py.
Semua eksperimen memakai Ridge (hitungan detik); imputer/scaler/PCA hanya belajar dari data latih (di dalam Pipeline).
"""
import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline

import konfigurasi as cfg
from evaluasi import evaluasi_regresi as ev
from preprocessing import fitur_waktu as fw

T = cfg.KOLOM_TARGET


def skor_ridge(latih, uji, kolom_num, kolom_kat, skala=True, tengah=None, target_log=False):
    """Fungsi: latih Ridge (preprocessor + langkah 'tengah' opsional) lalu nilai di data uji. Output: dict metrik."""
    langkah = [("prep", fw.buat_preprocessor_umum(kolom_num, kolom_kat, skala))]
    langkah += tengah or []
    langkah += [("model", Ridge(alpha=cfg.RIDGE_ALPHA))]
    model = Pipeline(langkah)
    if target_log:
        model = TransformedTargetRegressor(regressor=model, func=np.log1p, inverse_func=np.expm1)
    kolom = list(kolom_num) + list(kolom_kat)
    model.fit(latih[kolom], latih[T])
    return ev.hitung_metrik(uji[T], ev.prediksi_aman(model, uji[kolom]))
