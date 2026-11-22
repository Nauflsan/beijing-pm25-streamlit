"""
utilitas_app.py - bantuan khusus app Streamlit: memuat data/hasil dengan cache, pesan ramah kalau artefak belum ada,
format angka gaya Indonesia, dan kalimat temuan yang dibangun dari hasil.json (bukan ditulis tangan).

File ini mengimpor streamlit (berbeda dengan utilitas_data.py yang bebas streamlit).
"""
import streamlit as st

import konfigurasi as cfg
import kategori_udara as ku
import utilitas_data as ud

PESAN_ARTEFAK_KOSONG = ("Hasil training belum ada. Jalankan `python latih_semua_model.py --penuh` dulu "
                        "(lihat CARA_MENJALANKAN.md), lalu muat ulang halaman ini.")


def fmt(angka, desimal=2):
    """Fungsi: format angka gaya Indonesia. Input: angka (atau None), desimal. Output: str. (lihat utilitas_data.fmt_id)"""
    return ud.fmt_id(angka, desimal)


@st.cache_data(show_spinner="Memuat data ...")
def muat_data():
    """Fungsi: data mentah (cache). Output: DataFrame dari utilitas_data.muat_data_mentah."""
    return ud.muat_data_mentah()


def _mtime(path):
    return path.stat().st_mtime if path.exists() else 0


@st.cache_data(show_spinner=False)
def _baca_hasil(path_str, mtime):
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
