"""
bukti_kode.py - menjawab "angka ini dari mana dan kodenya mana?".

Dua hal:
  1. PETA: tiap bagian hasil.json -> fungsi yang menghasilkannya -> halaman yang membacanya.
  2. kode_fungsi / lokasi_kode: mengambil KODE ASLI fungsi dari file .py (lewat modul ast, tanpa mengimpor/menjalankan
     file itu), jadi yang tampil di halaman selalu sama dengan kode yang benar-benar dijalankan, termasuk nomor barisnya.

File ini tidak mengimpor streamlit. Dipakai halaman Preprocessing, PCA, dst. dan perbarui_panduan.py (PANDUAN_KODE.md).
"""
import ast

import konfigurasi as cfg

# [TERKAIT] kalau nama fungsi diganti di file aslinya, ganti juga di sini (uji_cepat.py mengecek semua entri masih ada).
# (kunci di hasil.json, isinya, file, fungsi/kelas, halaman yang membaca)
PETA = [
    ("data", "ringkasan data (jumlah baris, rentang latih/uji)", "latih_semua_model.py", "Data", "2, 3, 4"),
    ("fitur", "daftar nama fitur Mode A dan B", "fitur_waktu.py", "daftar_fitur", "4"),
    ("baseline", "persistence 1 jam, 24 jam, rata-rata latih", "latih_semua_model.py", "hitung_baseline", "1, 6, 7, 8"),
    ("model.<kode>_<mode> (parameter, ukuran, waktu)", "9 model terlatih dan metadatanya", "latih_semua_model.py", "latih_dan_simpan", "6, 7"),
    ("model.*.cv", "validasi silang TimeSeriesSplit", "evaluasi_regresi.py", "cv_regresi", "6"),
    ("model.*.uji, per_bulan, per_kategori, polusi_parah, kuantil_residual", "metrik di data uji", "evaluasi_regresi.py", "evaluasi_lengkap", "7, 8, 9"),
    ("pso", "riwayat dan hasil pencarian PSO", "pso_random_forest.py", "jalankan_pso", "6"),
    ("pemenang", "model terbaik tiap mode (menurut CV)", "latih_semua_model.py", "pilih_pemenang", "1, 7"),
    ("uji_kejujuran", "split acak vs split waktu (HGB)", "latih_semua_model.py", "uji_kejujuran", "8"),
    ("eksperimen.isi_kosong", "cara isi data kosong (Ridge Mode B)", "eksperimen_preprocessing.py", "_eksp_isi_kosong", "4"),
    ("eksperimen.skala, eksperimen.log_target", "skala dan log target (Ridge)", "eksperimen_preprocessing.py", "_eksp_skala_dan_log", "4"),
    ("eksperimen.pca", "scree, dengan vs tanpa PCA, SelectKBest", "eksperimen_pca.py", "_eksp_pca", "5"),
    ("eksperimen.ablasi", "Mode B tanpa satu kelompok fitur", "eksperimen_ablasi.py", "_eksp_ablasi", "13"),
    ("interpretasi", "permutation importance dan partial dependence", "latih_semua_model.py", "hitung_interpretasi", "7"),
    ("prediksi_uji.csv", "prediksi semua model di data uji", "latih_semua_model.py", "simpan_prediksi_uji", "7"),
]


def _cari(tree, nama):
    """Fungsi: cari node fungsi/kelas (boleh 'Kelas.metode') di pohon ast. Input: ast.Module, nama. Output: node atau None."""
    bagian = nama.split(".")
    isi = tree.body
    node = None
    for b in bagian:
        node = next((n for n in isi if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == b), None)
        if node is None:
            return None
        isi = getattr(node, "body", [])
    return node


# Folder tempat kode proyek berada. [TERKAIT] kalau menambah folder kode baru, tambahkan di sini.
FOLDER_KODE = ("", "preprocessing", "model", "evaluasi", "tampilan", "alat", "halaman", "halaman/tambahan")


def _path(berkas):
    """Fungsi: cari file kode di folder-folder proyek (cukup nama file, mis. 'fitur_waktu.py'). Output: Path atau OSError."""
    for folder in FOLDER_KODE:
        p = cfg.FOLDER_PROYEK / folder / berkas
        if p.exists():
            return p
    raise OSError(berkas)


def _muat(berkas):
    p = _path(berkas)
    teks = p.read_text(encoding="utf-8")
    return p, teks, ast.parse(teks)


def kode_fungsi(berkas, nama):
    """
    Fungsi: kode asli satu fungsi/kelas dari file proyek (tanpa menjalankan file). Input: nama file (mis. 'fitur_waktu.py'),
            nama fungsi/kelas. Output: str kode, atau pesan kalau tidak ditemukan.
    """
    try:
        _, teks, tree = _muat(berkas)
    except OSError:
        return f"# file {berkas} tidak ditemukan"
    node = _cari(tree, nama)
    if node is None:
        return f"# {nama} tidak ditemukan di {berkas}"
    return ast.get_source_segment(teks, node)


def lokasi_kode(berkas, nama):
    """Fungsi: teks 'file baris N' untuk fungsi/kelas. Input: file, nama. Output: str ('file (tidak ditemukan)' kalau gagal)."""
    try:
        p, _, tree = _muat(berkas)
    except OSError:
        return f"{berkas} (file tidak ditemukan)"
    rel = p.relative_to(cfg.FOLDER_PROYEK).as_posix()
    node = _cari(tree, nama)
    return f"{rel} baris {node.lineno}" if node else f"{rel} ({nama} tidak ditemukan)"


def tabel_peta():
    """
    Fungsi: tabel peta hasil.json -> kode. Output: list of dict {'Bagian hasil.json', 'Isi', 'Dihasilkan oleh (file baris)',
            'Fungsi', 'Dibaca halaman'}. Nomor baris dihitung langsung dari file, jadi selalu akurat.
    """
    return [{"Bagian hasil.json": k, "Isi": isi, "Dihasilkan oleh": lokasi_kode(f, fn), "Fungsi": fn, "Dibaca halaman": h}
            for k, isi, f, fn, h in PETA]


def semua_entri_ada():
    """Fungsi: cek semua fungsi di PETA masih ada di file asalnya. Output: list entri yang hilang (kosong = aman)."""
    return [f"{f}:{fn}" for _, _, f, fn, _ in PETA if "tidak ditemukan" in lokasi_kode(f, fn)]
