"""
app.py - pintu masuk web (jalankan: streamlit run app.py).

Tugasnya: pengaturan halaman, pasang tema, dan menyusun menu navigasi di ATAS (bukan sidebar).
Halaman yang filenya belum ada otomatis tidak muncul di menu (supaya app bisa jalan selama dibangun bertahap).
Halaman tambahan (12-14) bisa dimatikan lewat konfigurasi.SAKLAR_HALAMAN_TAMBAHAN.
"""
from pathlib import Path

import streamlit as st

import konfigurasi as cfg
from tampilan import tema_langit_beijing as tema

st.set_page_config(page_title=cfg.NAMA_PROYEK, page_icon=":material/cloud:", layout="wide")
tema.pasang_tema()

FOLDER_HALAMAN = Path(__file__).resolve().parent / "halaman"

# (grup menu, file relatif ke halaman/, judul, ikon Material, url_path, kunci saklar atau None)
# [UBAH] urutan/judul/grup bebas diubah. [TERKAIT] PANDUAN_HALAMAN.md memakai nomor & judul yang sama.
DAFTAR_HALAMAN = [
    ("Mulai", "01_beranda.py", "Beranda", ":material/home:", "beranda", None),
    ("Mulai", "02_tentang_dataset.py", "Tentang Dataset", ":material/database:", "dataset", None),
    ("Mulai", "03_eda_umum.py", "EDA Umum", ":material/bar_chart:", "eda", None),
    ("Persiapan", "04_preprocessing.py", "Preprocessing", ":material/tune:", "preprocessing", None),
    ("Persiapan", "05_pca.py", "PCA", ":material/scatter_plot:", "pca", None),
    ("Persiapan", "tambahan/12_pola_waktu_cuaca.py", "Pola Waktu & Cuaca", ":material/calendar_month:", "pola-waktu", "pola_waktu_cuaca"),
    ("Persiapan", "tambahan/13_feature_engineering.py", "Feature Engineering", ":material/build:", "feature-engineering", "feature_engineering"),
    ("Model", "06_modelling_tuning.py", "Modelling & Tuning", ":material/model_training:", "modelling", None),
    ("Model", "07_evaluasi_interpretasi.py", "Evaluasi & Interpretasi", ":material/fact_check:", "evaluasi", None),
    ("Model", "08_uji_kejujuran.py", "Uji Kejujuran Model", ":material/verified:", "uji-kejujuran", None),
    ("Prediksi", "09_prediksi_satu_input.py", "Prediksi Satu Input", ":material/bolt:", "prediksi", None),
    ("Prediksi", "10_prediksi_massal.py", "Prediksi Massal", ":material/upload_file:", "prediksi-massal", None),
    ("Prediksi", "tambahan/14_whatif_simulator.py", "What-if Simulator", ":material/science:", "whatif", "whatif_simulator"),
    ("Penutup", "11_kesimpulan_referensi.py", "Kesimpulan & Referensi", ":material/flag:", "kesimpulan", None),
]


def susun_menu():
    """Fungsi: kumpulkan halaman yang ada + aktif jadi dict {grup: [st.Page]}. Output: dict untuk st.navigation."""
    menu, pertama = {}, True
    for grup, berkas, judul, ikon, url, saklar in DAFTAR_HALAMAN:
        if saklar and not cfg.SAKLAR_HALAMAN_TAMBAHAN.get(saklar, False):
            continue
        path = FOLDER_HALAMAN / berkas
        if not path.exists():
            continue
        menu.setdefault(grup, []).append(st.Page(path, title=judul, icon=ikon, url_path=url, default=pertama))
        pertama = False
    return menu


halaman = st.navigation(susun_menu(), position="top")
halaman.run()
