"""
latih_semua_model.py - melatih 5 model regresi PM2.5 sekali jalan, lalu menyimpan hasilnya.

CARA PAKAI (dari folder proyek, env aktif):
  python latih_semua_model.py --cepat      # uji alur, model kecil, hasilnya BUKAN untuk laporan
  python latih_semua_model.py --penuh      # hasil final (jalankan di laptop, biarkan sampai selesai)
  python latih_semua_model.py --penuh --ulang    # paksa latih ulang semua model dari nol
  python latih_semua_model.py --cepat --sampel 2000   # tes kode di data kecil -> artifacts_dummy/ (DUMMY)

Perilaku penting:
  - Tiap model disimpan begitu selesai. Kalau terhenti (laptop mati, Ctrl+C), jalankan lagi perintah yang sama:
    model yang sudah selesai dengan profil yang sama DILEWATI.
  - Keluaran: artifacts/models/*.joblib, artifacts/hasil.json, artifacts/prediksi_uji.csv, logs/latih_*.log
  - Semua angka di halaman web dibaca dari hasil.json. Jangan mengedit hasil.json manual.
"""
import argparse
import logging
import os
import platform
import sys
import time
import warnings
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor

import eksperimen_ringan
import evaluasi_regresi as ev
import fitur_waktu as fw
import konfigurasi as cfg
import utilitas_data as ud
from pso_random_forest import jalankan_pso

warnings.filterwarnings("ignore", category=FutureWarning)
T = cfg.KOLOM_TARGET
BATAS_UKURAN_MB = 50   # [UBAH] peringatan kalau satu file model lebih besar dari ini (batas GitHub 100 MB)


# ----------------------------------------------------------------------------- util
def siapkan_log(folder_log, nama_awal="latih"):
    """Fungsi: logger ke layar + file logs/latih_<waktu>.log. Output: (logger, path_file_log)."""
    folder_log.mkdir(parents=True, exist_ok=True)
    path = folder_log / f"{nama_awal}_{datetime.now():%Y%m%d_%H%M%S}.log"
    logger = logging.getLogger("latih")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S")
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(path, encoding="utf-8")):
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger, path


def fmt_waktu(detik):
    """Fungsi: detik -> teks ramah ('45 detik' / '3.2 menit'). Output: str."""
    return f"{detik:.0f} detik" if detik < 90 else f"{detik / 60:.1f} menit"


def info_versi():
    """Fungsi: versi Python/library saat training (untuk mendeteksi ketidakcocokan saat app dijalankan)."""
    return {"python": platform.python_version(), "scikit_learn": sklearn.__version__, "pandas": pd.__version__,
            "numpy": np.__version__, "joblib": joblib.__version__}


def buat_estimator(kode, profil, params_pso=None):
    """
    Fungsi: membuat estimator sklearn (belum di-fit).
    Input : kode ('ridge','dt','rf','hgb','rf_pso'), profil (dict dari cfg.PROFIL_LATIH), params_pso (untuk 'rf_pso').
    Output: estimator.
    """
    if kode == "ridge":
        return Ridge(alpha=cfg.RIDGE_ALPHA)
    if kode == "dt":
        return DecisionTreeRegressor(max_depth=cfg.DT_MAX_DEPTH, min_samples_leaf=cfg.DT_MIN_SAMPLES_LEAF,
                                     random_state=cfg.SEED)
    if kode in ("rf", "rf_pso"):
        p = dict(n_estimators=profil["rf_n_estimators"], max_depth=profil["rf_max_depth"],
                 min_samples_leaf=profil["rf_min_samples_leaf"])
        if kode == "rf_pso":
            p.update(params_pso)
        return RandomForestRegressor(max_features=profil["rf_max_features"], n_jobs=cfg.N_JOBS,
                                     random_state=cfg.SEED, **p)
    if kode == "hgb":
        return HistGradientBoostingRegressor(max_iter=profil["hgb_max_iter"], learning_rate=cfg.HGB_LEARNING_RATE,
                                             max_leaf_nodes=cfg.HGB_MAX_LEAF_NODES,
                                             min_samples_leaf=cfg.HGB_MIN_SAMPLES_LEAF,
                                             l2_regularization=cfg.HGB_L2, early_stopping=False,
                                             random_state=cfg.SEED)
    raise ValueError(kode)


def buat_pipeline_model(kode, mode, profil, params_pso=None):
    """Fungsi: Pipeline lengkap (preprocessing + estimator). Ridge memakai StandardScaler, model pohon tidak perlu."""
    return fw.buat_pipeline(buat_estimator(kode, profil, params_pso), mode, skala=(kode == "ridge"))


def parameter_ringkas(kode, est):
    """Fungsi: parameter penting model untuk dicatat di hasil.json. Output: dict."""
    kunci = {"ridge": ["alpha"], "dt": ["max_depth", "min_samples_leaf"],
             "rf": ["n_estimators", "max_depth", "min_samples_leaf", "max_features"],
             "rf_pso": ["n_estimators", "max_depth", "min_samples_leaf", "max_features"],
             "hgb": ["max_iter", "learning_rate", "max_leaf_nodes", "min_samples_leaf", "l2_regularization"]}[kode]
    p = est.get_params()
    return {k: p[k] for k in kunci}


class Data:
    """Wadah data latih/uji yang sudah disiapkan. Atribut: df_mentah, d (semua fitur), latih, uji, info."""

    def __init__(self, sampel=None):
        df = ud.muat_data_mentah()
        if sampel:   # hanya untuk uji cepat: jendela berurutan di sekitar batas latih/uji (lag tetap valid)
            titik = int((df["year"] >= cfg.TAHUN_UJI_MULAI).idxmax())
            df = df.iloc[max(titik - sampel // 2, 0): titik + sampel // 2].reset_index(drop=True)
        self.df_mentah = df
        self.d = fw.siapkan_data(df)
        self.latih, self.uji = fw.bagi_waktu(self.d)
        if len(self.latih) < 50 or len(self.uji) < 50:
            raise ValueError("Data latih/uji terlalu sedikit. Cek TAHUN_UJI_MULAI atau ukuran --sampel.")
        self.info = {**ud.ringkasan_dataset(df),
                     "n_baris_layak_model": int(self.d["layak_model"].sum()),
                     "n_latih": int(len(self.latih)), "n_uji": int(len(self.uji)),
                     "rentang_latih": [str(self.latih["waktu"].min()), str(self.latih["waktu"].max())],
                     "rentang_uji": [str(self.uji["waktu"].min()), str(self.uji["waktu"].max())],
                     "tahun_uji_mulai": cfg.TAHUN_UJI_MULAI, "n_baris_dibuang_fitur_tidak_lengkap":
                         int((self.d["ada_target"] & ~self.d["layak_model"]).sum())}

    def xy(self, bagian, mode):
        d = self.latih if bagian == "latih" else self.uji
        return d[fw.daftar_fitur(mode)], d[T]


# ----------------------------------------------------------------------------- baseline
def hitung_baseline(data, profil):
    """
    Fungsi: baseline tanpa training sebagai pembanding: persistence 1 jam, persistence 24 jam, rata-rata data latih.
    Output: (dict untuk hasil.json, dict prediksi uji {nama: array}).
    """
    Xl, yl = data.xy("latih", "B")
    Xu, yu = data.xy("uji", "B")
    bulan = data.uji["month"].to_numpy()
    n_fold = profil["cv_fold"]
    rata = float(yl.mean())
    preds = {"persistence_1jam": Xu["pm25_lag1"].to_numpy(), "persistence_24jam": Xu["pm25_lag24"].to_numpy(),
             "rata_rata_latih": np.full(len(Xu), rata)}
    cv_fn = {"persistence_1jam": lambda tr, va: Xl["pm25_lag1"].iloc[va].to_numpy(),
             "persistence_24jam": lambda tr, va: Xl["pm25_lag24"].iloc[va].to_numpy(),
             "rata_rata_latih": lambda tr, va: np.full(len(va), yl.iloc[tr].mean())}
    nama = {"persistence_1jam": "Persistence 1 jam (nilai jam lalu)", "persistence_24jam": "Persistence 24 jam (nilai kemarin)",
            "rata_rata_latih": "Rata-rata data latih"}
    out = {}
    for k, p in preds.items():
        out[k] = {"nama": nama[k], **ev.evaluasi_lengkap(yu, p, bulan), "cv": ev.cv_baseline(cv_fn[k], Xl, yl, n_fold),
                  "nilai_konstan": rata if k == "rata_rata_latih" else None}
    return out, preds


# ----------------------------------------------------------------------------- latih satu model
def sudah_selesai(hasil, kunci, profil_nama, dummy, file_model, ulang):
    """Fungsi: apakah model ini boleh dilewati (resume). Syarat: bukan --ulang, profil sama, dummy sama, file ada."""
    m = hasil.get("model", {}).get(kunci)
    return bool(m and not ulang and m.get("profil") == profil_nama and m.get("dummy") == dummy and file_model.exists())


def latih_dan_simpan(kode, mode, data, profil, profil_nama, dummy, folder_model, hasil, path_hasil, ulang, log,
                     params_pso=None):
    """
    Fungsi: CV berurutan waktu -> fit pada seluruh data latih -> evaluasi di data uji -> simpan .joblib -> catat hasil.json.
    Input : kode model, mode 'A'/'B', objek Data, profil, nama profil, dummy (bool), folder_model, hasil (dict, diubah di
            tempat), path_hasil, ulang (bool), log, params_pso (khusus rf_pso).
    Output: entri hasil model (dict) atau None kalau dilewati.
    """
    kunci = f"{kode}_{mode}"
    file_model = folder_model / f"{kunci}.joblib"
    if sudah_selesai(hasil, kunci, profil_nama, dummy, file_model, ulang):
        log.info(f"LEWATI {cfg.NAMA_MODEL[kode]} Mode {mode}: sudah ada (profil {profil_nama})")
        return None
    Xl, yl = data.xy("latih", mode)
    Xu, yu = data.xy("uji", mode)
    buat = lambda: buat_pipeline_model(kode, mode, profil, params_pso)

    t0 = time.time()
    log.info(f"  validasi silang berurutan ({profil['cv_fold']} fold) ...")
    cv = ev.cv_regresi(buat, Xl, yl, profil["cv_fold"])
    t_cv = time.time() - t0
    log.info(f"  CV selesai {fmt_waktu(t_cv)}: RMSE rata-rata {cv['rmse_rata']:.3f}, R2 {cv['r2_rata']:.3f}")

    t1 = time.time()
    model = buat()
    model.fit(Xl, yl)
    t_fit = time.time() - t1
    pred = ev.prediksi_aman(model, Xu)
    hasil_uji = ev.evaluasi_lengkap(yu, pred, data.uji["month"].to_numpy())

    paket = {"pipeline": model, "mode": mode, "kode": kode, "nama": cfg.NAMA_MODEL[kode], "fitur": fw.daftar_fitur(mode),
             "profil": profil_nama, "dummy": dummy, "versi": info_versi()}
    joblib.dump(paket, file_model, compress=3)
    ukuran = os.path.getsize(file_model) / 1e6
    if ukuran > BATAS_UKURAN_MB:
        log.info(f"  PERINGATAN: {file_model.name} {ukuran:.1f} MB > {BATAS_UKURAN_MB} MB. Batas GitHub 100 MB. "
                 f"Kecilkan rf_max_depth / naikkan rf_min_samples_leaf di konfigurasi.py lalu latih ulang.")
    entri = {"kode": kode, "nama": cfg.NAMA_MODEL[kode], "mode": mode, "profil": profil_nama, "dummy": dummy,
             "parameter": parameter_ringkas(kode, model.named_steps["model"]),
             "n_fitur_setelah_enkode": int(len(model.named_steps["prep"].get_feature_names_out())),
             "waktu_cv_detik": t_cv, "waktu_latih_detik": t_fit, "ukuran_file_mb": ukuran, "file": file_model.name,
             "cv": cv, **hasil_uji}
    hasil.setdefault("model", {})[kunci] = entri
    ud.simpan_json_aman(path_hasil, hasil)
    u = hasil_uji["uji"]
    log.info(f"  SELESAI {cfg.NAMA_MODEL[kode]} Mode {mode}: uji 2014 RMSE {u['rmse']:.2f} | MAE {u['mae']:.2f} | "
             f"R2 {u['r2']:.3f} | latih {fmt_waktu(t_fit)} | file {ukuran:.1f} MB")
    return entri


# ----------------------------------------------------------------------------- tahap tambahan
def uji_kejujuran(data, profil, hasil, baseline_preds, log):
    """
    Fungsi: model HGB yang SAMA dilatih ulang dengan split ACAK (jumlah baris uji sama dengan split waktu) untuk
            dibandingkan dengan split waktu. Hanya fit kecil (HGB), untuk halaman Uji Kejujuran Model.
    Output: dict {A:{split_waktu, split_acak, persistence_1jam_pada_uji_acak, ...}, B:{...}, catatan}.
    """
    semua = pd.concat([data.latih, data.uji]).sort_values("waktu")
    n_uji = len(data.uji)
    rng = np.random.RandomState(cfg.SEED)
    pos_uji = np.sort(rng.choice(len(semua), size=n_uji, replace=False))
    mask = np.zeros(len(semua), dtype=bool)
    mask[pos_uji] = True
    acak_latih, acak_uji = semua[~mask], semua[mask]
    out = {"n_latih_acak": int(len(acak_latih)), "n_uji_acak": int(len(acak_uji)), "model": "hgb"}
    for mode in ("A", "B"):
        cols = fw.daftar_fitur(mode)
        m = buat_pipeline_model("hgb", mode, profil)
        t0 = time.time()
        m.fit(acak_latih[cols], acak_latih[T])
        pred = ev.prediksi_aman(m, acak_uji[cols])
        res = ev.evaluasi_lengkap(acak_uji[T], pred, acak_uji["month"].to_numpy())
        out[mode] = {"split_acak": res,
                     "split_waktu": {k: hasil["model"][f"hgb_{mode}"][k] for k in ("uji", "polusi_parah")},
                     "persistence_1jam_pada_uji_acak": ev.hitung_metrik(
                         acak_uji[T], np.clip(acak_uji["pm25_lag1"].to_numpy(), 0, None))}
        log.info(f"  Uji kejujuran Mode {mode}: R2 split acak {res['uji']['r2']:.3f} vs split waktu "
                 f"{hasil['model'][f'hgb_{mode}']['uji']['r2']:.3f} ({fmt_waktu(time.time() - t0)})")
    out["catatan"] = ("Split acak menaruh jam-jam bertetangga di data latih DAN uji, padahal PM2.5 sangat mirip dari jam ke jam. "
                      "Hasilnya terlihat lebih bagus tetapi tidak menggambarkan prediksi masa depan.")
    return out


def pilih_pemenang(hasil):
    """Fungsi: model terbaik per mode menurut RMSE rata-rata CV (BUKAN data uji). Output: {'A': kunci, 'B': kunci}."""
    out = {}
    for mode in ("A", "B"):
        kandidat = {k: m["cv"]["rmse_rata"] for k, m in hasil.get("model", {}).items() if m["mode"] == mode}
        if kandidat:
            out[mode] = min(kandidat, key=kandidat.get)
    return out


def hitung_interpretasi(data, profil, hasil, folder_model, log):
    """
    Fungsi: permutation importance dan partial dependence untuk model terbaik tiap mode (berdasarkan CV).
    Output: {mode: {model, permutation, parsial}}.
    """
    out = {}
    for mode, kunci in pilih_pemenang(hasil).items():
        paket = joblib.load(folder_model / f"{kunci}.joblib")
        Xu, yu = data.xy("uji", mode)
        t0 = time.time()
        perm = ev.importance_permutasi(paket["pipeline"], Xu, yu, profil["perm_repeat"], profil["perm_sampel"])
        numerik = [t["fitur"] for t in perm if t["fitur"] in fw.FITUR_NUMERIK[mode]][:4]
        pd_ = ev.kurva_parsial(paket["pipeline"], Xu, numerik, profil["pd_sampel"])
        out[mode] = {"model": kunci, "permutation": perm, "parsial": pd_}
        log.info(f"  Interpretasi Mode {mode} ({cfg.NAMA_MODEL[paket['kode']]}): fitur terpenting {perm[0]['fitur']} "
                 f"({fmt_waktu(time.time() - t0)})")
    return out


def simpan_prediksi_uji(data, hasil, baseline_preds, folder_model, path_csv, log):
    """
    Fungsi: simpan prediksi semua model + baseline pada data uji ke CSV (untuk grafik aktual vs prediksi).
    Kolom: waktu, bulan, aktual, lalu satu kolom per model ('<kode>_<mode>') dan per baseline.
    """
    df = pd.DataFrame({"waktu": data.uji["waktu"].to_numpy(), "bulan": data.uji["month"].to_numpy(),
                       "aktual": data.uji[T].to_numpy()})
    for kunci in sorted(hasil.get("model", {})):
        paket = joblib.load(folder_model / f"{kunci}.joblib")
        Xu = data.uji[fw.daftar_fitur(paket["mode"])]
        df[kunci] = ev.prediksi_aman(paket["pipeline"], Xu)
    for k, p in baseline_preds.items():
        df[k] = np.clip(p, 0, None)
    df.to_csv(path_csv, index=False, float_format="%.2f")
    log.info(f"Prediksi data uji disimpan: {path_csv.name} ({len(df)} baris, {df.shape[1]} kolom)")


def cetak_ringkasan(hasil, log):
    """Fungsi: tabel ringkas hasil di akhir (dari hasil.json) + peringatan ukuran file."""
    log.info("=" * 78)
    log.info("RINGKASAN (data uji 2014; urut kolom: RMSE, MAE, R2, CV-RMSE, ukuran file)")
    for mode in ("A", "B"):
        log.info(f"-- Mode {mode} --")
        base = [("persistence_1jam", "Persistence 1 jam"), ("persistence_24jam", "Persistence 24 jam"),
                ("rata_rata_latih", "Rata-rata latih")]
        for k, nama in base:
            if mode == "B" or k == "rata_rata_latih":
                u = hasil["baseline"][k]["uji"]
                log.info(f"   {nama:<24} RMSE {u['rmse']:7.2f} | MAE {u['mae']:7.2f} | R2 {u['r2']:7.3f}  (baseline)")
        for kode in cfg.URUTAN_MODEL:
            m = hasil["model"].get(f"{kode}_{mode}")
            if m:
                u = m["uji"]
                log.info(f"   {m['nama']:<24} RMSE {u['rmse']:7.2f} | MAE {u['mae']:7.2f} | R2 {u['r2']:7.3f} | "
                         f"CV-RMSE {m['cv']['rmse_rata']:7.2f} | {m['ukuran_file_mb']:6.1f} MB")
    besar = [m["file"] for m in hasil["model"].values() if m["ukuran_file_mb"] > BATAS_UKURAN_MB]
    if besar:
        log.info(f"PERINGATAN: file model > {BATAS_UKURAN_MB} MB: {besar}")
    total = sum(m["ukuran_file_mb"] for m in hasil["model"].values())
    log.info(f"Total ukuran semua model: {total:.1f} MB. Pemenang (CV): {hasil.get('pemenang')}")


# ----------------------------------------------------------------------------- main
def baca_argumen(argv=None):
    p = argparse.ArgumentParser(description="Latih semua model regresi PM2.5 (lihat docstring file).")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--cepat", action="store_true", help="profil kecil untuk uji alur (bukan hasil final)")
    g.add_argument("--penuh", action="store_true", help="profil final")
    p.add_argument("--ulang", action="store_true", help="latih ulang semua, abaikan model yang sudah ada")
    p.add_argument("--sampel", type=int, default=None,
                   help="pakai jendela data kecil (mis. 2000 baris) untuk tes kode; hasil ke artifacts_dummy/ (DUMMY)")
    return p.parse_args(argv)


def main(argv=None):
    """Fungsi: alur utama pelatihan. Input: argumen CLI (list) atau None. Output: path hasil.json."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = baca_argumen(argv)
    profil_nama = "cepat" if args.cepat else "penuh"
    profil = cfg.PROFIL_LATIH[profil_nama]
    dummy = args.sampel is not None
    folder_artefak = cfg.FOLDER_ARTEFAK_DUMMY if dummy else cfg.FOLDER_ARTEFAK
    folder_model = folder_artefak / cfg.SUBFOLDER_MODEL
    folder_model.mkdir(parents=True, exist_ok=True)
    path_hasil = folder_artefak / cfg.NAMA_FILE_HASIL
    log, path_log = siapkan_log(cfg.FOLDER_LOG, "latih_dummy" if dummy else "latih")

    log.info(f"Mulai | profil {profil_nama} | ulang={args.ulang} | {'DUMMY (sampel %d baris)' % args.sampel if dummy else 'HASIL ASLI'}")
    log.info(f"Folder keluaran: {folder_artefak} | log: {path_log.name} | N_JOBS={cfg.N_JOBS}")
    if dummy:
        log.info("PERINGATAN: ini artefak DUMMY hanya untuk menguji kode. JANGAN dipakai untuk laporan.")
    t_awal = time.time()

    data = Data(sampel=args.sampel)
    log.info(f"Data: {data.info['n_baris']} baris mentah -> latih {data.info['n_latih']} | uji {data.info['n_uji']} "
             f"(split waktu: uji = tahun >= {cfg.TAHUN_UJI_MULAI})")

    hasil = ud.muat_json(path_hasil)
    if hasil and (hasil.get("meta", {}).get("dummy") != dummy):
        hasil = {}   # jangan mencampur dummy dengan asli
    hasil.setdefault("meta", {})
    hasil["meta"].update({"dummy": dummy, "profil_terakhir": profil_nama, "seed": cfg.SEED,
                          "versi": info_versi(), "diperbarui": datetime.now().isoformat(timespec="seconds"),
                          "tahun_uji_mulai": cfg.TAHUN_UJI_MULAI, "ambang_aqi_versi": cfg.VERSI_AMBANG_AKTIF,
                          "sumber_ambang": cfg.SUMBER_AMBANG, "tanggal_akses_sumber": cfg.TANGGAL_AKSES_SUMBER,
                          "catatan_ambang": cfg.CATATAN_AMBANG})
    hasil["data"] = data.info
    hasil["fitur"] = {m: fw.daftar_fitur(m) for m in ("A", "B")}
    hasil["baseline"], baseline_preds = hitung_baseline(data, profil)
    ud.simpan_json_aman(path_hasil, hasil)
    u1 = hasil["baseline"]["persistence_1jam"]["uji"]
    log.info(f"Baseline persistence 1 jam di data uji: RMSE {u1['rmse']:.2f}, MAE {u1['mae']:.2f}, R2 {u1['r2']:.3f}")

    daftar = [(k, m) for m in ("A", "B") for k in ("ridge", "dt", "rf", "hgb")] + [("rf_pso", "B")]
    total_bobot = sum(cfg.BOBOT_ETA[k] for k, _ in daftar)
    selesai_bobot, t_model0 = 0.0, time.time()
    params_pso = None
    for i, (kode, mode) in enumerate(daftar, 1):
        log.info(f"[{i}/{len(daftar)}] {cfg.NAMA_MODEL[kode]} | Mode {mode}")
        if kode == "rf_pso":
            lama = hasil.get("pso")
            if lama and not args.ulang and lama.get("profil") == profil_nama and lama.get("dummy") == dummy:
                params_pso = lama["parameter_terbaik"]
                log.info(f"  PSO sudah ada, memakai parameter {params_pso}")
            else:
                Xl, yl = data.xy("latih", "B")
                pembanding = {k: profil[f"rf_{k}"] for k in ("n_estimators", "max_depth", "min_samples_leaf")}
                def buat(n_estimators, max_depth, min_samples_leaf):
                    """Pembuat model untuk fitness PSO: RF Mode B dengan 3 parameter yang dicari."""
                    return buat_pipeline_model("rf_pso", "B", profil, {
                        "n_estimators": n_estimators, "max_depth": max_depth, "min_samples_leaf": min_samples_leaf})
                pso = jalankan_pso(Xl, yl, buat, partikel=profil["pso_partikel"], iterasi=profil["pso_iterasi"],
                                   n_fold=profil["pso_fold"], sampel_maks=profil["pso_sampel_maks"],
                                   params_pembanding=pembanding, log=lambda s: log.info("  " + s))
                pso.update({"profil": profil_nama, "dummy": dummy})
                hasil["pso"] = pso
                ud.simpan_json_aman(path_hasil, hasil)
                params_pso = pso["parameter_terbaik"]
                log.info(f"  PSO selesai {fmt_waktu(pso['waktu_detik'])}: parameter terbaik {params_pso}")
        latih_dan_simpan(kode, mode, data, profil, profil_nama, dummy, folder_model, hasil, path_hasil,
                         args.ulang, log, params_pso if kode == "rf_pso" else None)
        selesai_bobot += cfg.BOBOT_ETA[kode]
        lewat = time.time() - t_model0
        sisa = lewat * (total_bobot - selesai_bobot) / selesai_bobot if selesai_bobot else 0
        log.info(f"  progres {selesai_bobot / total_bobot * 100:.0f}% | berjalan {fmt_waktu(lewat)} | "
                 f"perkiraan sisa kasar {fmt_waktu(sisa)} (hanya perkiraan)")

    hasil["pemenang"] = pilih_pemenang(hasil)
    if "uji_kejujuran" not in hasil or args.ulang or hasil["uji_kejujuran"].get("profil") != profil_nama \
            or hasil["uji_kejujuran"].get("dummy") != dummy:
        log.info("Uji kejujuran (HGB, split acak vs split waktu) ...")
        hasil["uji_kejujuran"] = {**uji_kejujuran(data, profil, hasil, baseline_preds, log),
                                  "profil": profil_nama, "dummy": dummy}
        ud.simpan_json_aman(path_hasil, hasil)
    if "eksperimen" not in hasil or args.ulang or hasil["eksperimen"].get("profil") != profil_nama \
            or hasil["eksperimen"].get("dummy") != dummy:
        t0 = time.time()
        hasil["eksperimen"] = {**eksperimen_ringan.jalankan_eksperimen(data.df_mentah, data.d, data.latih, data.uji,
                                                                       log=lambda s: log.info(s)),
                               "profil": profil_nama, "dummy": dummy}
        ud.simpan_json_aman(path_hasil, hasil)
        log.info(f"Eksperimen ringan selesai {fmt_waktu(time.time() - t0)}")
    log.info("Interpretasi (permutation importance, partial dependence) ...")
    hasil["interpretasi"] = hitung_interpretasi(data, profil, hasil, folder_model, log)
    simpan_prediksi_uji(data, hasil, baseline_preds, folder_model, folder_artefak / cfg.NAMA_FILE_PREDIKSI_UJI, log)

    hasil["meta"]["durasi_sesi_terakhir_detik"] = time.time() - t_awal
    ud.simpan_json_aman(path_hasil, hasil)
    cetak_ringkasan(hasil, log)
    log.info(f"SELESAI dalam {fmt_waktu(time.time() - t_awal)}. hasil.json: {path_hasil}")
    if dummy:
        log.info("Ingat: ini DUMMY (artifacts_dummy/). Hasil asli: python latih_semua_model.py --penuh")
    return path_hasil


if __name__ == "__main__":
    main()
