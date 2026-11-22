"""
evaluasi_regresi.py - metrik regresi, error per bulan / kategori udara / polusi parah, kuantil residual
(untuk interval prediksi), validasi silang berurutan waktu, permutation importance, dan partial dependence.

Residual didefinisikan: aktual - prediksi. Prediksi selalu dipotong >= 0 (PM2.5 tidak mungkin negatif).
"""
import numpy as np
from sklearn.metrics import (mean_absolute_error, mean_squared_error, median_absolute_error, r2_score)
from sklearn.model_selection import TimeSeriesSplit

import konfigurasi as cfg
import kategori_udara as ku

KUANTIL = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]   # [TERKAIT] halaman Prediksi memakai 0.05 dan 0.95
MIN_SAMPEL_KUANTIL = 30                                 # kategori dengan sampel lebih sedikit -> pakai kuantil global


def prediksi_aman(model, X):
    """Fungsi: model.predict lalu dipotong >= 0. Input: model, X. Output: array float."""
    return np.clip(np.asarray(model.predict(X), dtype=float), 0, None)


def hitung_metrik(y, p):
    """
    Fungsi: MAE, RMSE, R2, MedAE, bias (rata-rata prediksi - aktual), n.
    Input : y aktual, p prediksi. Output: dict (satuan ug/m3 kecuali r2).
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(np.sqrt(mean_squared_error(y, p))),
        "r2": float(r2_score(y, p)) if len(y) > 1 else None,
        "medae": float(median_absolute_error(y, p)),
        "bias": float(np.mean(p - y)),
        "n": int(len(y)),
    }


def _metrik_ringkas(y, p):
    m = hitung_metrik(y, p)
    return {"n": m["n"], "mae": m["mae"], "rmse": m["rmse"], "bias": m["bias"]}


def metrik_per_bulan(bulan, y, p):
    """Fungsi: error per bulan kalender. Input: array bulan (1-12), y, p. Output: {bulan: {n, mae, rmse, bias}}."""
    bulan, y, p = np.asarray(bulan), np.asarray(y, float), np.asarray(p, float)
    return {int(b): _metrik_ringkas(y[bulan == b], p[bulan == b]) for b in sorted(set(bulan.tolist()))}


def metrik_per_kategori(y, p):
    """Fungsi: error per kategori udara AKTUAL. Output: {nama_pendek: {n, mae, rmse, bias}}."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    idx = ku.indeks_kategori(y)
    out = {}
    for i, nama in enumerate(cfg.NAMA_KATEGORI_PENDEK):
        m = idx == i
        if m.any():
            out[nama] = _metrik_ringkas(y[m], p[m])
    return out


def metrik_polusi_parah(y, p, ambang=None):
    """
    Fungsi: bandingkan error saat polusi normal vs parah (aktual > ambang).
    Output: {ambang, normal:{...}, parah:{...}, rasio_mae_parah_per_normal}.
    """
    ambang = cfg.AMBANG_POLUSI_PARAH if ambang is None else ambang
    y, p = np.asarray(y, float), np.asarray(p, float)
    parah = y > ambang
    out = {"ambang": float(ambang)}
    out["normal"] = _metrik_ringkas(y[~parah], p[~parah]) if (~parah).any() else None
    out["parah"] = _metrik_ringkas(y[parah], p[parah]) if parah.any() else None
    if out["normal"] and out["parah"] and out["normal"]["mae"] > 0:
        out["rasio_mae_parah_per_normal"] = out["parah"]["mae"] / out["normal"]["mae"]
    return out


def kuantil_residual(y, p):
    """
    Fungsi: kuantil residual (aktual - prediksi) untuk interval ketidakpastian. Ini PERKIRAAN kasar:
            dihitung dari data uji 2014, mengasumsikan sebaran galat mirip di masa depan.
    Output: {'global': {kuantil: nilai}, 'per_kategori_prediksi': {nama_pendek: {n, kuantil | None}}}
            Per kategori dikelompokkan menurut PREDIKSI (itu yang diketahui saat pengguna memprediksi).
    """
    y, p = np.asarray(y, float), np.asarray(p, float)
    res = y - p
    out = {"global": {str(q): float(np.quantile(res, q)) for q in KUANTIL}, "per_kategori_prediksi": {}}
    idx = ku.indeks_kategori(p)
    for i, nama in enumerate(cfg.NAMA_KATEGORI_PENDEK):
        m = idx == i
        n = int(m.sum())
        if n >= MIN_SAMPEL_KUANTIL:
            out["per_kategori_prediksi"][nama] = {"n": n, "kuantil": {str(q): float(np.quantile(res[m], q)) for q in KUANTIL}}
        else:
            out["per_kategori_prediksi"][nama] = {"n": n, "kuantil": None}
    return out


def evaluasi_lengkap(y, p, bulan):
    """
    Fungsi: semua evaluasi data uji sekaligus (disimpan ke hasil.json).
    Input : y aktual, p prediksi (sudah dipotong >= 0), bulan (array bulan tiap baris).
    Output: dict {uji, per_bulan, per_kategori, polusi_parah, kuantil_residual}.
    """
    return {
        "uji": hitung_metrik(y, p),
        "per_bulan": metrik_per_bulan(bulan, y, p),
        "per_kategori": metrik_per_kategori(y, p),
        "polusi_parah": metrik_polusi_parah(y, p),
        "kuantil_residual": kuantil_residual(y, p),
    }


def _ringkas_cv(per_fold):
    out = {"per_fold": per_fold}
    for k in ("rmse", "mae", "r2"):
        nilai = [f[k] for f in per_fold if f[k] is not None]
        out[f"{k}_rata"] = float(np.mean(nilai)) if nilai else None
        out[f"{k}_std"] = float(np.std(nilai)) if nilai else None
    return out


def cv_regresi(buat_model, X, y, n_fold):
    """
    Fungsi: TimeSeriesSplit pada DATA LATIH (lipatan selalu: latih di masa lalu, validasi di masa depan).
    Input : buat_model() -> model/pipeline baru, X, y (terurut waktu), n_fold.
    Output: dict {per_fold:[{n_latih,n_valid,mae,rmse,r2}], rmse_rata, rmse_std, mae_rata, ...}
    """
    per_fold = []
    for tr, va in TimeSeriesSplit(n_splits=n_fold).split(X):
        m = buat_model()   # model baru tiap lipatan (tidak ada yang bocor antar lipatan)
        m.fit(X.iloc[tr], y.iloc[tr])
        met = hitung_metrik(y.iloc[va], prediksi_aman(m, X.iloc[va]))
        per_fold.append({"n_latih": int(len(tr)), "n_valid": int(len(va)),
                         "mae": met["mae"], "rmse": met["rmse"], "r2": met["r2"]})
    return _ringkas_cv(per_fold)


def cv_baseline(fungsi_prediksi, X, y, n_fold):
    """
    Fungsi: CV untuk baseline tanpa training, pada lipatan yang SAMA dengan cv_regresi.
    Input : fungsi_prediksi(idx_latih, idx_valid) -> array prediksi untuk idx_valid.
    """
    per_fold = []
    for tr, va in TimeSeriesSplit(n_splits=n_fold).split(X):
        met = hitung_metrik(y.iloc[va], np.clip(fungsi_prediksi(tr, va), 0, None))
        per_fold.append({"n_latih": int(len(tr)), "n_valid": int(len(va)),
                         "mae": met["mae"], "rmse": met["rmse"], "r2": met["r2"]})
    return _ringkas_cv(per_fold)


def importance_permutasi(model, X, y, n_repeat, sampel, seed=None):
    """
    Fungsi: permutation importance = seberapa naik RMSE kalau satu kolom diacak. Input: model (Pipeline),
            X, y (data uji), n_repeat, sampel (jumlah baris yang dipakai), seed.
    Output: list [{fitur, naik_rmse, std}] urut dari terpenting.
    """
    from sklearn.inspection import permutation_importance
    seed = cfg.SEED if seed is None else seed
    rng = np.random.RandomState(seed)
    idx = np.sort(rng.choice(len(X), size=min(sampel, len(X)), replace=False))
    r = permutation_importance(model, X.iloc[idx], y.iloc[idx], scoring="neg_root_mean_squared_error",
                               n_repeats=n_repeat, random_state=seed, n_jobs=1)
    tabel = [{"fitur": f, "naik_rmse": float(m), "std": float(s)}
             for f, m, s in zip(X.columns, r.importances_mean, r.importances_std)]
    return sorted(tabel, key=lambda t: t["naik_rmse"], reverse=True)


def kurva_parsial(model, X, daftar_fitur_pd, sampel, resolusi=20, seed=None):
    """
    Fungsi: partial dependence (rata-rata prediksi saat satu fitur digeser, fitur lain apa adanya).
    Input : model, X (data uji), daftar fitur numerik, sampel (jumlah baris), resolusi (titik grid).
    Output: {fitur: {'grid': [...], 'rata_prediksi': [...]}}
    """
    from sklearn.inspection import partial_dependence
    seed = cfg.SEED if seed is None else seed
    rng = np.random.RandomState(seed)
    idx = np.sort(rng.choice(len(X), size=min(sampel, len(X)), replace=False))
    Xs = X.iloc[idx].copy()
    # partial_dependence menolak kolom bertipe integer (DEWP, TEMP, dst. di CSV bertipe int) -> ubah ke float
    Xs = Xs.astype({c: float for c in Xs.select_dtypes("number").columns})
    out = {}
    for f in daftar_fitur_pd:
        r = partial_dependence(model, Xs, [f], kind="average", grid_resolution=resolusi)
        out[f] = {"grid": [float(v) for v in r["grid_values"][0]],
                  "rata_prediksi": [float(v) for v in r["average"][0]]}
    return out
