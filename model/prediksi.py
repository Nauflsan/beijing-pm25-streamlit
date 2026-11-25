"""
prediksi.py - logika prediksi untuk halaman Prediksi Satu Input, Prediksi Massal, dan What-if (tanpa Streamlit).

  muat_paket          : baca satu model terlatih (.joblib) dari artifacts/models/
  prediksi_satu       : satu baris input -> satu angka pm2.5 (rumus fitur SAMA dengan training lewat fitur_waktu.buat_baris_fitur)
  interval_prediksi   : rentang ketidakpastian dari kuantil residual data uji (perkiraan kasar, dijelaskan jujur di halaman)
  validasi_unggahan   : cek CSV unggahan (kolom, arah angin, urutan jam) dengan pesan yang ramah
  prediksi_massal     : banyak baris sekaligus; Mode B memakai riwayat dari baris-baris sebelumnya di file yang sama
  contoh_dari_data    : ambil satu jam dari data asli (input + riwayat 24 jam + nilai aktual) untuk demo
"""
import io

import joblib
import numpy as np
import pandas as pd

import konfigurasi as cfg
from evaluasi import kategori_udara as ku
from evaluasi.evaluasi_regresi import prediksi_aman
from preprocessing import fitur_waktu as fw

MAKS_BARIS_MASSAL = 20000   # [UBAH] batas baris unggahan agar web tetap ringan
KOLOM_UNGGAHAN_WAJIB = ["year", "month", "day", "hour", *cfg.KOLOM_CUACA_NUMERIK, cfg.KOLOM_ARAH_ANGIN]


def muat_paket(kunci, folder=None):
    """
    Fungsi: baca model terlatih. Input: kunci (mis. 'ridge_B'), folder artefak (default cfg.FOLDER_ARTEFAK_AKTIF).
    Output: dict {pipeline, mode, kode, nama, fitur, profil, dummy, versi} atau None kalau file tidak ada.
    """
    folder = folder or cfg.FOLDER_ARTEFAK_AKTIF
    path = folder / cfg.SUBFOLDER_MODEL / f"{kunci}.joblib"
    return joblib.load(path) if path.exists() else None


def versi_tidak_cocok(paket):
    """Fungsi: beda versi scikit-learn antara saat training dan sekarang. Output: (versi_latih, versi_sekarang) atau None kalau sama."""
    import sklearn
    v_latih = paket.get("versi", {}).get("scikit_learn")
    return (v_latih, sklearn.__version__) if v_latih and v_latih != sklearn.__version__ else None


def prediksi_satu(paket, waktu, cuaca, riwayat=None):
    """
    Fungsi: prediksi pm2.5 untuk SATU jam. Input: paket model, waktu (Timestamp), cuaca (dict DEWP,TEMP,PRES,Iws,Is,Ir,cbwd),
            riwayat (list pm2.5 per jam, lama -> baru, minimal 24 nilai; wajib untuk Mode B). Output: float (ug/m3, >= 0).
    """
    x = fw.buat_baris_fitur(waktu, cuaca, riwayat, paket["mode"])
    return float(prediksi_aman(paket["pipeline"], x)[0])


def interval_prediksi(hasil, kunci, nilai):
    """
    Fungsi: rentang ketidakpastian 90% dari kuantil residual data uji, dikelompokkan menurut kategori PREDIKSI
            (pakai kuantil global kalau kategori itu punya terlalu sedikit sampel). INI PERKIRAAN KASAR dari satu tahun uji.
    Input : dict hasil.json, kunci model, nilai prediksi. Output: dict {bawah, atas, dasar, n}.
    """
    kq = hasil["model"][kunci]["kuantil_residual"]
    nama = cfg.NAMA_KATEGORI_PENDEK[ku.indeks_kategori(nilai)]
    e = kq["per_kategori_prediksi"].get(nama)
    if e and e.get("kuantil"):
        q, dasar, n = e["kuantil"], f"kuantil residual data uji untuk prediksi kategori {nama}", e["n"]
    else:
        q, dasar, n = kq["global"], "kuantil residual data uji (semua kategori)", None
    return {"bawah": max(0.0, nilai + q["0.05"]), "atas": nilai + q["0.95"], "dasar": dasar, "n": n}


def contoh_dari_data(d_siap, waktu):
    """
    Fungsi: ambil satu jam dari data asli sebagai contoh. Input: d_siap (hasil fitur_waktu.siapkan_data), waktu (Timestamp).
    Output: (waktu, cuaca dict, riwayat 24 jam lama->baru, aktual atau None) atau None kalau tidak tersedia/riwayat tidak lengkap.
    """
    idx = d_siap.index[d_siap["waktu"] == pd.Timestamp(waktu)]
    if len(idx) == 0:
        return None
    i = d_siap.index.get_loc(idx[0])
    if i < fw.RIWAYAT_MINIMAL:
        return None
    riwayat = d_siap["pm_diisi"].iloc[i - fw.RIWAYAT_MINIMAL: i].tolist()
    if any(pd.isna(v) for v in riwayat):
        return None
    baris = d_siap.iloc[i]
    cuaca = {k: float(baris[k]) for k in cfg.KOLOM_CUACA_NUMERIK}
    cuaca[cfg.KOLOM_ARAH_ANGIN] = str(baris[cfg.KOLOM_ARAH_ANGIN])
    aktual = None if pd.isna(baris[cfg.KOLOM_TARGET]) else float(baris[cfg.KOLOM_TARGET])
    return pd.Timestamp(waktu), cuaca, [float(v) for v in riwayat], aktual


def template_csv(df_data, tahun=None, n_baris=72):
    """
    Fungsi: contoh file unggahan (format sama dengan CSV dataset): n_baris jam berurutan dari data asli. Input: df data mentah,
            tahun (default tahun uji), n_baris. Output: str CSV (bisa diunduh).
    """
    tahun = tahun or cfg.TAHUN_UJI_MULAI
    sub = df_data[(df_data["year"] == tahun)].head(n_baris)
    kolom = ["year", "month", "day", "hour", cfg.KOLOM_TARGET, *cfg.KOLOM_CUACA_NUMERIK, cfg.KOLOM_ARAH_ANGIN]
    buf = io.StringIO()
    sub[kolom].to_csv(buf, index=False)
    return buf.getvalue()


def validasi_unggahan(df, mode):
    """
    Fungsi: periksa CSV unggahan sebelum diprediksi. Input: DataFrame hasil pd.read_csv, mode 'A'/'B'.
    Output: (ok: bool, pesan: list[str], df_bersih atau None). Pesan berisi alasan yang bisa langsung diperbaiki pengguna.
    """
    pesan = []
    hilang = [k for k in KOLOM_UNGGAHAN_WAJIB if k not in df.columns]
    if hilang:
        return False, [f"Kolom wajib belum ada: {', '.join(hilang)}. Unduh template dan samakan nama kolomnya."], None
    if len(df) == 0:
        return False, ["File kosong."], None
    if len(df) > MAKS_BARIS_MASSAL:
        return False, [f"Terlalu banyak baris ({len(df):,}). Maksimal {MAKS_BARIS_MASSAL:,} baris per unggahan.".replace(",", ".")], None
    d = df.copy()
    if cfg.KOLOM_TARGET not in d.columns:
        d[cfg.KOLOM_TARGET] = np.nan
    for k in ["year", "month", "day", "hour", *cfg.KOLOM_CUACA_NUMERIK, cfg.KOLOM_TARGET]:
        d[k] = pd.to_numeric(d[k], errors="coerce")
    d[cfg.KOLOM_ARAH_ANGIN] = d[cfg.KOLOM_ARAH_ANGIN].astype(str).str.strip().astype(object)
    salah = sorted(set(d[cfg.KOLOM_ARAH_ANGIN]) - set(cfg.KELAS_ARAH_ANGIN))
    if salah:
        return False, [f"Nilai arah angin tidak dikenal: {salah}. Yang valid: {', '.join(cfg.KELAS_ARAH_ANGIN)}."], None
    if d[["year", "month", "day", "hour"]].isna().any().any():
        return False, ["Kolom year, month, day, hour harus berisi angka di semua baris."], None
    d["waktu"] = pd.to_datetime(d[["year", "month", "day", "hour"]], errors="coerce")
    if d["waktu"].isna().any():
        return False, ["Ada tanggal/jam yang tidak valid (mis. bulan 13 atau jam 25)."], None
    if not d["waktu"].is_monotonic_increasing:
        return False, ["Baris harus terurut dari jam paling lama ke paling baru."], None
    if mode == "B":
        if d[cfg.KOLOM_TARGET].notna().sum() < fw.RIWAYAT_MINIMAL + 1:
            return False, [f"Mode B butuh kolom pm2.5 terisi (riwayat) minimal {fw.RIWAYAT_MINIMAL + 1} baris."], None
        if not (d["waktu"].diff().dropna() == pd.Timedelta(hours=1)).all():
            return False, ["Mode B menghitung lag dari baris-baris sebelumnya, jadi jam harus berurutan satu per satu tanpa jam yang hilang."], None
    if d[cfg.KOLOM_CUACA_NUMERIK].isna().any().any():
        pesan.append("Ada nilai cuaca kosong; nilainya diisi median saat prediksi (hasil kurang andal untuk baris itu).")
    return True, pesan, d.reset_index(drop=True)


def prediksi_massal(paket, d_valid):
    """
    Fungsi: prediksi banyak baris. Input: paket model, d_valid (hasil validasi_unggahan). Output: DataFrame
            {waktu, prediksi, kategori, aktual (bisa kosong), galat = aktual - prediksi}. Mode B hanya mengeluarkan baris yang
            riwayat 24 jam-nya lengkap (baris awal file tidak bisa diprediksi).
    """
    d = fw.siapkan_data(d_valid)
    mode = paket["mode"]
    mask = d[fw.FITUR_NUMERIK["B"]].notna().all(axis=1) if mode == "B" else pd.Series(True, index=d.index)
    x = d.loc[mask, fw.daftar_fitur(mode)]
    pred = prediksi_aman(paket["pipeline"], x)
    out = pd.DataFrame({"waktu": d.loc[mask, "waktu"].to_numpy(), "prediksi": np.round(pred, 2),
                        "kategori": [cfg.NAMA_KATEGORI[i] for i in ku.indeks_kategori(pred)],
                        "aktual": d.loc[mask, cfg.KOLOM_TARGET].to_numpy()})
    out["galat"] = np.round(out["aktual"] - out["prediksi"], 2)
    return out.reset_index(drop=True)
