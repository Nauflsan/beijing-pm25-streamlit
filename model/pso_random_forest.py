"""
pso_random_forest.py - Particle Swarm Optimization (PSO) untuk mencari hyperparameter Random Forest.

Logika dasar sama dengan notebook P5 (posisi, kecepatan, pbest, gbest; w=0,6; c1=c2=1,5). Bedanya:
  - fitness = RMSE rata-rata TimeSeriesSplit pada DATA LATIH saja (data uji 2014 tidak pernah dilihat PSO),
  - fitness dihitung pada sampel data latih yang tetap berurutan waktu (agar cepat),
  - kombinasi parameter yang sama tidak dihitung dua kali (cache).

Satu partikel = satu kombinasi (n_estimators, max_depth, min_samples_leaf), semuanya dibulatkan ke bilangan bulat.
"""
import time

import numpy as np
from sklearn.model_selection import TimeSeriesSplit

import konfigurasi as cfg


def ambil_sampel_berurutan(X, y, maks):
    """
    Fungsi: ambil paling banyak 'maks' baris secara merata (urutan waktu tetap terjaga, TIDAK diacak).
    Input : X, y (terurut waktu), maks. Output: (X_sampel, y_sampel).
    """
    if len(X) <= maks:
        return X, y
    idx = np.unique(np.linspace(0, len(X) - 1, maks).astype(int))
    return X.iloc[idx], y.iloc[idx]


def _menit(detik):
    """Fungsi: format detik menjadi teks ramah ('45 detik' atau '3.2 menit'). Input: detik. Output: str."""
    return f"{detik / 60:.1f} menit" if detik >= 90 else f"{detik:.0f} detik"


def jalankan_pso(X, y, buat_model, batas=None, partikel=6, iterasi=5, w=None, c1=None, c2=None,
                 n_fold=3, sampel_maks=8000, seed=None, params_pembanding=None, log=print):
    """
    Fungsi: jalankan PSO.
    Input : X, y data LATIH (terurut waktu);
            buat_model(n_estimators, max_depth, min_samples_leaf) -> pipeline/model baru;
            batas {nama: (bawah, atas)} (default cfg.PSO_BATAS); partikel, iterasi, w, c1, c2, n_fold, sampel_maks, seed;
            params_pembanding (dict parameter RF default, untuk perbandingan sebelum/sesudah tuning);
            log (fungsi cetak, mis. logger.info).
    Output: dict {parameter_terbaik, rmse_cv_terbaik, rmse_cv_pembanding, riwayat_gbest (per iterasi, termasuk
            iterasi 0 = inisialisasi), evaluasi [{params, rmse}], n_evaluasi, n_cache_hit, waktu_detik, pengaturan}
    """
    batas = batas or cfg.PSO_BATAS
    w = cfg.PSO_W if w is None else w
    c1 = cfg.PSO_C1 if c1 is None else c1
    c2 = cfg.PSO_C2 if c2 is None else c2
    seed = cfg.SEED if seed is None else seed

    nama = list(batas.keys())
    lb = np.array([batas[k][0] for k in nama], dtype=float)
    ub = np.array([batas[k][1] for k in nama], dtype=float)
    dim = len(nama)

    Xs, ys = ambil_sampel_berurutan(X, y, sampel_maks)
    log(f"PSO: sampel fitness {len(Xs)} baris dari {len(X)} (terurut waktu), {n_fold} fold, "
        f"{partikel} partikel x {iterasi} iterasi, ruang cari {batas}")
    tscv = TimeSeriesSplit(n_splits=n_fold)

    cache, evaluasi = {}, []
    total_eval = partikel * (iterasi + 1)
    hitung = {"eval": 0, "hit": 0}
    t_mulai = time.time()

    def ke_params(vektor):
        """Fungsi: ubah vektor posisi partikel menjadi dict parameter bilangan bulat yang dipotong ke batas. Input: vektor. Output: dict."""
        return {k: int(round(float(np.clip(v, lb[i], ub[i])))) for i, (k, v) in enumerate(zip(nama, vektor))}

    def fitness(params, tampil=True):
        """Fungsi: RMSE rata-rata TimeSeriesSplit pada sampel data latih untuk satu kombinasi parameter (dengan cache). Input: dict params, tampil (bool). Output: float."""
        kunci = tuple(params[k] for k in nama)
        if kunci in cache:
            hitung["hit"] += 1
            return cache[kunci]
        skor = []
        for tr, va in tscv.split(Xs):
            m = buat_model(**params)
            m.fit(Xs.iloc[tr], ys.iloc[tr])
            p = np.clip(m.predict(Xs.iloc[va]), 0, None)
            skor.append(float(np.sqrt(np.mean((ys.iloc[va].to_numpy() - p) ** 2))))
        rmse = float(np.mean(skor))
        cache[kunci] = rmse
        hitung["eval"] += 1
        evaluasi.append({"params": dict(params), "rmse": rmse})
        if tampil:
            lewat = time.time() - t_mulai
            sisa = lewat / hitung["eval"] * max(total_eval - hitung["eval"] - hitung["hit"], 0)
            log(f"  PSO eval {hitung['eval']}: {params} -> RMSE CV {rmse:.3f} | sisa sekitar {_menit(sisa)}")
        return rmse

    rng = np.random.RandomState(seed)
    pos = rng.uniform(lb, ub, size=(partikel, dim))
    vel = np.zeros((partikel, dim))
    pbest_pos = pos.copy()
    pbest_val = np.array([fitness(ke_params(p)) for p in pos])
    g = int(np.argmin(pbest_val))
    gbest_pos, gbest_val = pbest_pos[g].copy(), float(pbest_val[g])
    riwayat = [gbest_val]
    log(f"PSO iterasi 0 (inisialisasi): RMSE terbaik {gbest_val:.3f} | {ke_params(gbest_pos)}")

    for it in range(iterasi):
        for i in range(partikel):
            r1, r2 = rng.rand(dim), rng.rand(dim)
            vel[i] = w * vel[i] + c1 * r1 * (pbest_pos[i] - pos[i]) + c2 * r2 * (gbest_pos - pos[i])
            pos[i] = np.clip(pos[i] + vel[i], lb, ub)
            nilai = fitness(ke_params(pos[i]))
            if nilai < pbest_val[i]:
                pbest_val[i], pbest_pos[i] = nilai, pos[i].copy()
            if nilai < gbest_val:
                gbest_val, gbest_pos = float(nilai), pos[i].copy()
        riwayat.append(gbest_val)
        log(f"PSO iterasi {it + 1}/{iterasi}: RMSE terbaik {gbest_val:.3f} | {ke_params(gbest_pos)}")

    terbaik = ke_params(gbest_pos)
    rmse_pembanding = None
    if params_pembanding:
        rmse_pembanding = fitness({k: int(params_pembanding[k]) for k in nama}, tampil=False)
        log(f"PSO: RMSE CV pada sampel yang sama untuk parameter default {params_pembanding} = {rmse_pembanding:.3f} "
            f"(terbaik PSO {gbest_val:.3f})")

    return {
        "parameter_terbaik": terbaik,
        "rmse_cv_terbaik": gbest_val,
        "rmse_cv_pembanding": rmse_pembanding,
        "parameter_pembanding": dict(params_pembanding) if params_pembanding else None,
        "riwayat_gbest": riwayat,
        "evaluasi": evaluasi,
        "n_evaluasi": hitung["eval"],
        "n_cache_hit": hitung["hit"],
        "waktu_detik": time.time() - t_mulai,
        "pengaturan": {"partikel": partikel, "iterasi": iterasi, "w": w, "c1": c1, "c2": c2, "n_fold": n_fold,
                       "sampel": int(len(Xs)), "batas": {k: list(v) for k, v in batas.items()}, "seed": seed},
    }
