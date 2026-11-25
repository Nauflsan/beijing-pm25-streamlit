"""
utilitas_app.py - bantuan khusus app Streamlit: memuat data/hasil dengan cache, pesan ramah kalau artefak belum ada,
format angka gaya Indonesia, dan kalimat temuan yang dibangun dari hasil.json (bukan ditulis tangan).

File ini mengimpor streamlit (berbeda dengan utilitas_data.py yang bebas streamlit).
"""
import streamlit as st

import konfigurasi as cfg
from evaluasi import kategori_udara as ku
from evaluasi import bukti_kode as bk
from model import prediksi as pr
from preprocessing import fitur_waktu as fw
from preprocessing import utilitas_data as ud

PESAN_ARTEFAK_KOSONG = ("Hasil training belum ada. Jalankan `python -m model.latih_semua_model --penuh` dulu "
                        "(lihat CARA_MENJALANKAN.md), lalu muat ulang halaman ini.")


def fmt(angka, desimal=2):
    """Fungsi: format angka gaya Indonesia. Input: angka (atau None), desimal. Output: str. (lihat utilitas_data.fmt_id)"""
    return ud.fmt_id(angka, desimal)


@st.cache_data(show_spinner="Memuat data ...")
def muat_data():
    """Fungsi: data mentah (cache). Output: DataFrame dari utilitas_data.muat_data_mentah."""
    return ud.muat_data_mentah()


def _mtime(path):
    """Fungsi: waktu ubah terakhir file (0 kalau tidak ada), dipakai sebagai kunci cache. Input: Path. Output: float."""
    return path.stat().st_mtime if path.exists() else 0


@st.cache_data(show_spinner=False)
def _baca_hasil(path_str, mtime):
    """Fungsi: baca hasil.json dengan cache. Input: path (str), mtime. Output: dict."""
    return ud.muat_json(path_str)   # mtime ikut jadi kunci cache supaya hasil.json baru otomatis terbaca


def muat_hasil():
    """Fungsi: baca artifacts/hasil.json (cache, otomatis segar kalau file berubah). Output: dict ({} kalau belum ada)."""
    path = cfg.FOLDER_ARTEFAK_AKTIF / cfg.NAMA_FILE_HASIL
    return _baca_hasil(str(path), _mtime(path))


def hasil_atau_berhenti():
    """
    Fungsi: ambil hasil.json; kalau belum ada tampilkan pesan ramah lalu hentikan halaman (st.stop).
            Kalau hasilnya DUMMY, tampilkan banner peringatan. Output: dict hasil.
    """
    hasil = muat_hasil()
    if not hasil or "model" not in hasil:
        st.info(PESAN_ARTEFAK_KOSONG)
        st.stop()
    if hasil.get("meta", {}).get("dummy"):
        st.warning("Ini hasil DUMMY (data kecil, hanya untuk menguji tampilan). Angka model di halaman ini BUKAN hasil asli.")
    elif hasil.get("meta", {}).get("profil_terakhir") == "cepat":
        st.warning("Hasil ini dari profil --cepat (model kecil untuk uji alur). Untuk laporan jalankan --penuh.")
    return hasil


def sebut_model(kunci, hasil):
    """Fungsi: 'ridge_B' -> 'Ridge Regression (Mode B)'. Input: kunci, hasil. Output: str."""
    m = hasil["model"][kunci]
    return f"{m['nama']} (Mode {m['mode']})"


def kalimat_temuan(hasil):
    """
    Fungsi: kalimat ringkasan temuan untuk Beranda, dihitung dari hasil.json. Semua angka dan arah perbandingan
            (menang/kalah dari baseline) ditentukan oleh data, jadi kalau hasilnya berubah kalimatnya ikut berubah.
    Input : dict hasil.json. Output: list[str].
    """
    out = []
    pem = hasil.get("pemenang", {})
    base = hasil["baseline"]["persistence_1jam"]["uji"]
    for mode in ("A", "B"):
        kunci = pem.get(mode)
        if not kunci:
            continue
        m = hasil["model"][kunci]
        u = m["uji"]
        out.append(f"Mode {mode}: model terbaik menurut validasi silang adalah {m['nama']}. Di data uji "
                   f"{hasil['data']['tahun_uji_mulai']} hasilnya RMSE {fmt(u['rmse'])}, MAE {fmt(u['mae'])}, R2 {fmt(u['r2'], 3)}.")
    kb = pem.get("B")
    if kb:
        u = hasil["model"][kb]["uji"]
        lebih_baik_rmse = u["rmse"] < base["rmse"]
        lebih_baik_mae = u["mae"] < base["mae"]
        if lebih_baik_rmse and lebih_baik_mae:
            arah = "sedikit lebih baik dari" if (base["rmse"] - u["rmse"]) / base["rmse"] < 0.05 else "lebih baik dari"
        elif not lebih_baik_rmse and not lebih_baik_mae:
            arah = "TIDAK mengalahkan"
        else:
            arah = "campuran (menang di satu metrik, kalah di metrik lain) dibanding"
        out.append(f"Mode B {arah} baseline persistence 1 jam (RMSE {fmt(base['rmse'])}, MAE {fmt(base['mae'])}, "
                   f"R2 {fmt(base['r2'], 3)}). Rinciannya ada di halaman Uji Kejujuran Model.")
    ka = pem.get("A")
    if ka:
        ua = hasil["model"][ka]["uji"]
        if kb:
            ub = hasil["model"][kb]["uji"]
            out.append(f"Selisih Mode A dan Mode B: R2 {fmt(ua['r2'], 3)} tanpa riwayat PM2.5 (cuaca dan waktu saja) "
                       f"berbanding {fmt(ub['r2'], 3)} dengan riwayat PM2.5.")
    return out


def indeks_kategori_rata(nilai):
    """Fungsi: indeks kategori untuk satu nilai PM2.5 (dipakai untuk mewarnai KPI/header). Output: int 0-5."""
    return ku.indeks_kategori(float(nilai))


def persen_selisih(nilai, acuan):
    """Fungsi: selisih relatif nilai terhadap acuan dalam persen ((nilai-acuan)/acuan*100). Output: float, None kalau acuan 0/None."""
    if acuan in (None, 0) or nilai is None:
        return None
    return (nilai - acuan) / acuan * 100


def tampilkan_kode(berkas, nama, judul=None):
    """
    Fungsi: expander berisi KODE ASLI satu fungsi/kelas (diambil dari file proyek lewat bukti_kode, bukan salinan teks)
            beserta nama file dan nomor barisnya. Input: nama file, nama fungsi/kelas, judul (opsional). Output: -
    Catatan: jangan dipanggil di dalam st.expander lain (Streamlit tidak mengizinkan expander bersarang).
    """
    with st.expander(judul or f"Kode: {nama}  ({bk.lokasi_kode(berkas, nama)})"):
        st.caption(f"Sumber: {bk.lokasi_kode(berkas, nama)}. Ini kode yang benar-benar dijalankan, bukan salinan.")
        st.code(bk.kode_fungsi(berkas, nama), language="python")


def skill_persentase(rmse_model, rmse_acuan):
    """
    Fungsi: skill score terhadap acuan dalam persen = (1 - RMSE_model / RMSE_acuan) x 100.
            Positif = model lebih baik dari acuan; 0 = sama; negatif = lebih buruk. Output: float atau None.
    """
    if not rmse_acuan or rmse_model is None:
        return None
    return (1 - rmse_model / rmse_acuan) * 100


def tabel_semua_model(hasil):
    """
    Fungsi: satu tabel datar berisi semua model dan baseline (dibaca dari hasil.json) untuk dipakai berbagai halaman.
    Input : dict hasil.json. Output: list of dict dengan kunci:
            kunci, nama, mode ('A'/'B'/'-'), jenis ('Model'/'Baseline'), rmse, mae, medae, r2, cv_rmse, cv_std,
            ukuran_mb, waktu_latih, waktu_cv (None untuk baseline).
    """
    baris = []
    for kunci, m in hasil["model"].items():
        u = m["uji"]
        baris.append({"kunci": kunci, "nama": m["nama"], "mode": m["mode"], "jenis": "Model", "rmse": u["rmse"], "mae": u["mae"],
                      "medae": u["medae"], "r2": u["r2"], "cv_rmse": m["cv"]["rmse_rata"], "cv_std": m["cv"]["rmse_std"],
                      "ukuran_mb": m["ukuran_file_mb"], "waktu_latih": m["waktu_latih_detik"], "waktu_cv": m["waktu_cv_detik"]})
    for kunci, b in hasil["baseline"].items():
        u = b["uji"]
        baris.append({"kunci": kunci, "nama": b["nama"], "mode": "-" if kunci == "rata_rata_latih" else "B", "jenis": "Baseline",
                      "rmse": u["rmse"], "mae": u["mae"], "medae": u["medae"], "r2": u["r2"], "cv_rmse": b["cv"]["rmse_rata"],
                      "cv_std": b["cv"]["rmse_std"], "ukuran_mb": None, "waktu_latih": None, "waktu_cv": None})
    return baris


@st.cache_data(show_spinner=False)
def _baca_prediksi(path_str, mtime):
    """Fungsi: baca prediksi_uji.csv dengan cache. Input: path (str), mtime. Output: DataFrame."""
    import pandas as pd
    return pd.read_csv(path_str, parse_dates=["waktu"])


def muat_prediksi_uji():
    """
    Fungsi: baca artifacts/prediksi_uji.csv (prediksi semua model dan baseline di data uji; cache, segar kalau file berubah).
    Output: DataFrame, atau None kalau file belum ada.
    """
    path = cfg.FOLDER_ARTEFAK_AKTIF / cfg.NAMA_FILE_PREDIKSI_UJI
    return _baca_prediksi(str(path), _mtime(path)) if path.exists() else None


@st.cache_resource(show_spinner="Memuat model ...")
def _paket_cache(kunci, mtime):
    """Fungsi: muat satu model dengan st.cache_resource (kunci cache memuat mtime). Input: kunci model, mtime. Output: dict paket atau None."""
    return pr.muat_paket(kunci)


def muat_paket(kunci):
    """
    Fungsi: baca satu model terlatih dengan cache (st.cache_resource; segar kalau file berubah). Input: kunci model.
    Output: dict paket model, atau None kalau file .joblib belum ada. Juga menampilkan peringatan kalau versi scikit-learn berbeda.
    """
    path = cfg.FOLDER_ARTEFAK_AKTIF / cfg.SUBFOLDER_MODEL / f"{kunci}.joblib"
    paket = _paket_cache(kunci, _mtime(path))
    if paket is not None:
        beda = pr.versi_tidak_cocok(paket)
        if beda:
            st.warning(f"Model dilatih dengan scikit-learn {beda[0]}, sedangkan yang terpasang sekarang {beda[1]}. "
                       "Hasil prediksi bisa berbeda atau gagal; samakan versi di requirements.txt.")
    return paket


@st.cache_data(show_spinner="Menyiapkan data ...")
def data_siap():
    """Fungsi: data mentah + semua fitur (fitur_waktu.siapkan_data), cache. Output: DataFrame."""
    return fw.siapkan_data(muat_data())
