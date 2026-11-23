"""
eksperimen_pca.py - eksperimen PCA dan SelectKBest (Ridge): scree, dengan vs tanpa PCA, seleksi kolom pembanding.

PCA di proyek ini hanya EKSPERIMEN pembanding; kelima model final dilatih tanpa PCA.
Hasilnya masuk hasil.json["eksperimen"]["pca"], dibaca halaman 5 (PCA).
"""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import konfigurasi as cfg
from evaluasi import evaluasi_regresi as ev
from preprocessing import fitur_waktu as fw
from preprocessing.eksperimen_umum import skor_ridge

T = cfg.KOLOM_TARGET


def _eksp_pca(latih, uji):
    out = {}
    for mode in ("A", "B"):
        num, kat = fw.FITUR_NUMERIK[mode], fw.FITUR_KATEGORIK
        kolom = num + kat
        # PCA pada semua fitur setelah one-hot, distandarkan (PCA peka skala)
        siap = Pipeline([("prep", fw.buat_preprocessor_umum(num, kat, skala=False)), ("skala_semua", StandardScaler())])
        Z = siap.fit_transform(latih[kolom])
        evr = PCA().fit(Z).explained_variance_ratio_
        n_fitur = Z.shape[1]
        hasil = {"n_fitur_setelah_enkode": int(n_fitur), "scree": [float(v) for v in evr],
                 "kumulatif": [float(v) for v in np.cumsum(evr)],
                 "tanpa_pca": skor_ridge(latih, uji, num, kat), "varian": {}, "select_k_best": {}}
        for target in (0.80, 0.90, 0.95, 0.99):
            tengah = [("skala_semua", StandardScaler()), ("pca", PCA(n_components=target, svd_solver="full"))]
            langkah = [("prep", fw.buat_preprocessor_umum(num, kat, skala=False))] + tengah + [("model", Ridge(alpha=cfg.RIDGE_ALPHA))]
            m = Pipeline(langkah).fit(latih[kolom], latih[T])
            hasil["varian"][f"{target:.2f}"] = {
                "n_komponen": int(m.named_steps["pca"].n_components_),
                "metrik": ev.hitung_metrik(uji[T], ev.prediksi_aman(m, uji[kolom]))}
        for k in (5, 10, 15):
            if k < n_fitur:
                tengah = [("pilih", SelectKBest(f_regression, k=k))]
                hasil["select_k_best"][str(k)] = skor_ridge(latih, uji, num, kat, tengah=tengah)
        out[mode] = hasil
    return out
