"""
uji_cepat.py - jalankan SEBELUM training penuh:  python -m alat.uji_cepat
Memeriksa: (1) data terbaca, (2) batas kategori udara, (3) tidak ada kebocoran masa depan di fitur lag/rolling,
(4) buat_baris_fitur (dipakai halaman Prediksi) sama persis dengan fitur untuk training, (5) alur latih
lengkap di data kecil (2.000 baris) -> artifacts_dummy/ (DUMMY, bukan hasil asli).
Kalau semua lolos, tercetak: UJI CEPAT LULUS.
"""
import sys

import numpy as np
import pandas as pd

from preprocessing import fitur_waktu as fw
from evaluasi import kategori_udara as ku
import konfigurasi as cfg
from preprocessing import utilitas_data as ud

T = cfg.KOLOM_TARGET
GAGAL = []


def cek(nama, kondisi, rinci=""):
    """Fungsi: catat hasil satu pengecekan. Input: nama, kondisi (bool), rinci (teks)."""
    print(("  OK    " if kondisi else "  GAGAL ") + nama + (f"  [{rinci}]" if rinci and not kondisi else ""))
    if not kondisi:
        GAGAL.append(nama)


def uji_data():
    """Fungsi: cek dataset. Output: DataFrame mentah."""
    print("1) Data")
    df = ud.muat_data_mentah()
    cek("jumlah baris 43.824", len(df) == 43824, str(len(df)))
    cek("waktu terurut dan selisih 1 jam", df["waktu"].is_monotonic_increasing and
        (df["waktu"].diff().dropna() == pd.Timedelta(hours=1)).all())
    cek("target kosong 2.067 baris", int(df[T].isna().sum()) == 2067, str(int(df[T].isna().sum())))
    return df


def uji_kategori():
    """Fungsi: cek batas kategori AQI 2024 (nilai batas, antar batas, dan pemotongan 1 desimal)."""
    print("2) Kategori udara (ambang 2024)")
    kasus = [(0, 0), (9.0, 0), (9.05, 0), (9.1, 1), (35.4, 1), (35.5, 2), (55.4, 2), (55.5, 3), (125.4, 3),
             (125.5, 4), (225.4, 4), (225.5, 5), (994, 5)]
    for nilai, harap in kasus:
        cek(f"PM2.5 {nilai} -> kategori {harap}", ku.indeks_kategori(nilai, "2024") == harap,
            f"dapat {ku.indeks_kategori(nilai, '2024')}")
    arr = ku.indeks_kategori(np.array([5, 20, 40, 100, 200, 300]), "2024")
    cek("input array", list(arr) == [0, 1, 2, 3, 4, 5], str(list(arr)))


def uji_kebocoran(df):
    """Fungsi: pastikan fitur di jam t TIDAK berubah kalau nilai PM2.5 jam >= t diubah (tidak mengintip masa depan)."""
    print("3) Kebocoran masa depan")
    d = fw.siapkan_data(df)
    rng = np.random.RandomState(0)
    layak = np.flatnonzero(d["layak_model"].to_numpy())
    fitur_pm = fw.FITUR_LAG + fw.FITUR_ROLLING
    for t in rng.choice(layak, 5, replace=False):
        cek(f"lag1 baris {t} = PM2.5 terisi jam sebelumnya",
            np.isclose(d["pm25_lag1"].iloc[t], d["pm_diisi"].iloc[t - 1]))
        df2 = df.copy()
        df2.loc[t:, T] = 999.0          # ubah jam t dan semua masa depan
        d2 = fw.siapkan_data(df2)
        sama = np.allclose(d[fitur_pm].iloc[: t + 1].to_numpy(dtype=float), d2[fitur_pm].iloc[: t + 1].to_numpy(dtype=float),
                           equal_nan=True)
        cek(f"fitur lag/rolling sampai baris {t} tidak berubah saat PM2.5 jam t dst diubah", sama)
    cek("tidak ada bfill: 24 jam pertama tidak dipakai", not d["layak_model"].iloc[:24].any())


def uji_baris_fitur(df):
    """Fungsi: buat_baris_fitur (halaman Prediksi) harus sama dengan fitur vektor untuk training."""
    print("4) buat_baris_fitur sama dengan fitur training")
    d = fw.siapkan_data(df)
    rng = np.random.RandomState(1)
    layak = np.flatnonzero(d["layak_model"].to_numpy())
    semua_sama = True
    for t in rng.choice(layak, 30, replace=False):
        baris = d.iloc[t]
        cuaca = {k: baris[k] for k in fw.FITUR_CUACA}
        cuaca[cfg.KOLOM_ARAH_ANGIN] = baris[cfg.KOLOM_ARAH_ANGIN]
        riwayat = d["pm_diisi"].iloc[t - fw.RIWAYAT_MINIMAL: t].tolist()
        for mode in ("A", "B"):
            x = fw.buat_baris_fitur(baris["waktu"], cuaca, riwayat, mode)
            ref = d[fw.daftar_fitur(mode)].iloc[[t]].reset_index(drop=True)
            num = fw.FITUR_NUMERIK[mode]
            ok = np.allclose(x[num].to_numpy(float), ref[num].to_numpy(float)) and x[cfg.KOLOM_ARAH_ANGIN].iloc[0] == ref[cfg.KOLOM_ARAH_ANGIN].iloc[0]
            semua_sama &= ok
    cek("30 baris acak x 2 mode identik", semua_sama)


def uji_alur_latih():
    """Fungsi: jalankan latih_semua_model --cepat --sampel 2000 --ulang dan cek keluarannya (artifacts_dummy/)."""
    print("5) Alur latih lengkap di data kecil (DUMMY)")
    from model import latih_semua_model as lt
    path = lt.main(["--cepat", "--sampel", "2000", "--ulang"])
    hasil = ud.muat_json(path)
    for kunci in ["ridge_A", "dt_A", "rf_A", "hgb_A", "ridge_B", "dt_B", "rf_B", "hgb_B", "rf_pso_B"]:
        cek(f"model {kunci} tercatat dan filenya ada", kunci in hasil.get("model", {}) and
            (path.parent / cfg.SUBFOLDER_MODEL / f"{kunci}.joblib").exists())
    for bagian in ["meta", "data", "fitur", "baseline", "pso", "uji_kejujuran", "eksperimen", "interpretasi", "pemenang"]:
        cek(f"hasil.json punya bagian '{bagian}'", bagian in hasil)
    cek("hasil.json ditandai dummy", hasil["meta"]["dummy"] is True)
    cek("prediksi_uji.csv ada", (path.parent / cfg.NAMA_FILE_PREDIKSI_UJI).exists())
    # peta kolom -> fitur (halaman Preprocessing & PANDUAN_HALAMAN.md) konsisten dengan hasil.json
    from preprocessing import peta_fitur as pf
    tabel, peringatan = pf.bangun_tabel(hasil)
    r = pf.ringkasan_jumlah(hasil)
    cek("peta_fitur: semua fitur terpetakan ke kolom asal (tanpa peringatan)", not peringatan, str(peringatan))
    cek("peta_fitur: jumlah baris aturan sama dengan jumlah kolom CSV", len(pf.ATURAN) == r["n_kolom_csv"])
    cek("peta_fitur: fitur setelah one-hot = fitur + (jumlah kelas arah angin - 1)",
        r["n_enkode_a"] == r["n_fitur_a"] + len(cfg.KELAS_ARAH_ANGIN) - 1 and
        r["n_enkode_b"] == r["n_fitur_b"] + len(cfg.KELAS_ARAH_ANGIN) - 1,
        f"{r}")
    cek("peta_fitur: 5 pertanyaan dosen terbentuk", len(pf.pertanyaan_dosen(hasil)) == 5)
    # peta hasil.json -> kode (halaman Preprocessing/PCA dan PANDUAN_KODE.md) masih menunjuk fungsi yang ada
    from evaluasi import bukti_kode as bk
    hilang = bk.semua_entri_ada()
    cek("bukti_kode: semua fungsi di peta masih ada di file asalnya", not hilang, str(hilang))
    # prediksi massal = prediksi satu input (rumus fitur sama), dan validasi menolak file yang salah
    from model import prediksi as pr
    import io as _io
    import pandas as _pd
    paket = pr.muat_paket("rf_B", path.parent)
    df_up = _pd.read_csv(_io.StringIO(pr.template_csv(ud.muat_data_mentah())))
    ok, _, d_valid = pr.validasi_unggahan(df_up, "B")
    massal = pr.prediksi_massal(paket, d_valid)
    dsiap = fw.siapkan_data(d_valid)
    selisih = []
    for i in range(0, len(massal), 9):
        w = massal.loc[i, "waktu"]
        p_ = dsiap.index.get_loc(dsiap.index[dsiap["waktu"] == w][0])
        cuaca = {k: float(dsiap.iloc[p_][k]) for k in cfg.KOLOM_CUACA_NUMERIK}
        cuaca[cfg.KOLOM_ARAH_ANGIN] = str(dsiap.iloc[p_][cfg.KOLOM_ARAH_ANGIN])
        selisih.append(abs(pr.prediksi_satu(paket, w, cuaca, dsiap["pm_diisi"].iloc[p_ - 24:p_].tolist()) - massal.loc[i, "prediksi"]))
    cek("prediksi massal sama dengan prediksi satu input (selisih < 0,006)", ok and max(selisih) < 0.006, str(max(selisih)))
    salah = df_up.copy()
    salah.loc[2, cfg.KOLOM_ARAH_ANGIN] = "XX"
    cek("validasi_unggahan menolak arah angin yang salah", not pr.validasi_unggahan(salah, "B")[0])
    cek("validasi_unggahan menolak jam bolong di Mode B", not pr.validasi_unggahan(df_up.drop(index=[10]), "B")[0])
    from alat import buat_kamus_fungsi as bkf
    _, n_file, _ = bkf.tulis()
    cek("kamus fungsi berhasil dibuat dari kode", n_file > 20)
    # eksperimen di hasil.json bisa dihitung ulang dan cocok (dummy)
    from evaluasi import bukti_eksperimen as be
    cek("bukti_eksperimen: hitung ulang cocok dengan hasil.json (dummy)", be.main(["--dummy"]) == 0)


if __name__ == "__main__":
    df_mentah = uji_data()
    uji_kategori()
    uji_kebocoran(df_mentah)
    uji_baris_fitur(df_mentah)
    uji_alur_latih()
    print()
    if GAGAL:
        print(f"UJI CEPAT GAGAL ({len(GAGAL)} pengecekan): {GAGAL}")
        sys.exit(1)
    print("UJI CEPAT LULUS")
