"""
eksperimen_ringan.py - eksperimen kecil memakai Ridge SAJA (hitungan detik), dipanggil dari latih_semua_model.py.

Hasilnya masuk hasil.json["eksperimen"] dan dibaca halaman:
  Preprocessing : skala, log target, cara isi data kosong
  PCA           : scree plot, dengan vs tanpa PCA, SelectKBest
  Feature Eng.  : ablasi kelompok fitur
Catatan: Ridge model linear, jadi kesimpulan ablasi/PCA belum tentu sama untuk model berbasis pohon.
Semua eksperimen dievaluasi di data uji 2014; imputer/scaler/PCA hanya belajar dari data latih (di dalam Pipeline).
"""
import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import evaluasi_regresi as ev
import fitur_waktu as fw
import konfigurasi as cfg

T = cfg.KOLOM_TARGET


def _skor(latih, uji, kolom_num, kolom_kat, skala=True, tengah=None, target_log=False):
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


def _eksp_skala_dan_log(latih, uji):
    out_skala, out_log = {}, {}
    for mode in ("A", "B"):
        num, kat = fw.FITUR_NUMERIK[mode], fw.FITUR_KATEGORIK
        out_skala[mode] = {"dengan_skala": _skor(latih, uji, num, kat, skala=True),
                           "tanpa_skala": _skor(latih, uji, num, kat, skala=False)}
        out_log[mode] = {"skala_asli": _skor(latih, uji, num, kat, skala=True),
                         "target_log1p": _skor(latih, uji, num, kat, skala=True, target_log=True)}
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
        out[nama] = _skor(latih, uji, num, kat)
    return out


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
                 "tanpa_pca": _skor(latih, uji, num, kat), "varian": {}, "select_k_best": {}}
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
                hasil["select_k_best"][str(k)] = _skor(latih, uji, num, kat, tengah=tengah)
        out[mode] = hasil
    return out


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
    return {nama: _skor(latih, uji, num, k) for nama, (num, k) in varian.items() if num}


def jalankan_eksperimen(df_mentah, d_siap, latih, uji, log=print):
    """
    Fungsi: jalankan semua eksperimen ringan.
    Input : df_mentah (hasil muat_data_mentah), d_siap (hasil siapkan_data), latih, uji (hasil bagi_waktu), log.
    Output: dict {skala, log_target, isi_kosong, pca, ablasi, catatan}.
    """
    log("Eksperimen ringan (Ridge): skala dan log target ...")
    skala, log_t = _eksp_skala_dan_log(latih, uji)
    log("Eksperimen ringan: cara isi data kosong ...")
    isi = _eksp_isi_kosong(df_mentah, d_siap["layak_model"].to_numpy())
    log("Eksperimen ringan: PCA dan SelectKBest ...")
    pca = _eksp_pca(latih, uji)
    log("Eksperimen ringan: ablasi kelompok fitur ...")
    ablasi = _eksp_ablasi(latih, uji)
    return {"skala": skala, "log_target": log_t, "isi_kosong": isi, "pca": pca, "ablasi": ablasi,
            "catatan": "Semua eksperimen memakai Ridge (model linear) dan dievaluasi di data uji; "
                       "hasilnya belum tentu sama untuk model berbasis pohon."}
