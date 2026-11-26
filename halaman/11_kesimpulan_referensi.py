"""
halaman/11_kesimpulan_referensi.py - Kesimpulan & Referensi: temuan (dihitung dari hasil.json), keterbatasan, saran, daftar pustaka.

Temuan dibangun dari angka sehingga arah kesimpulan (menang/kalah, membantu/merugikan) mengikuti data.
Keterbatasan dan saran adalah penilaian penulis; daftar pustaka ditulis di PUSTAKA di bawah.
"""
import streamlit as st

import konfigurasi as cfg
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("Kesimpulan dan Referensi", "Apa yang kami temukan, apa batasnya, dan ke mana selanjutnya.")
hasil = ua.hasil_atau_berhenti()
base1 = hasil["baseline"]["persistence_1jam"]["uji"]
pem = hasil["pemenang"]
mA, mB = hasil["model"][pem["A"]], hasil["model"][pem["B"]]
modelB = [m for m in hasil["model"].values() if m["mode"] == "B"]
terbaikB = min(modelB, key=lambda m: m["uji"]["rmse"])
eks = hasil.get("eksperimen", {})

st.subheader("Temuan utama")
temuan = []
temuan.append(f"**Dua mode, dua peran.** Mode B (dengan riwayat PM2.5) adalah model utama; Mode A (cuaca dan waktu saja) menjadi pembanding. "
              f"Menurut validasi silang model terbaik Mode B adalah {mB['nama']} dan Mode A adalah {mA['nama']}.")
sk = ua.skill_persentase(terbaikB["uji"]["rmse"], base1["rmse"])
menang_cv = sum(1 for m in modelB if m["cv"]["rmse_rata"] < hasil["baseline"]["persistence_1jam"]["cv"]["rmse_rata"])
temuan.append(f"**Mode B hanya sedikit lebih baik dari baseline.** RMSE terbaik di data uji {fmt(terbaikB['uji']['rmse'])} ({terbaikB['nama']}) berbanding "
              f"{fmt(base1['rmse'])} untuk persistence 1 jam ({fmt(sk, 1)}% lebih rendah); di validasi silang hanya {menang_cv} dari {len(modelB)} model yang mengalahkannya.")
temuan.append(f"**Mode A lemah.** R2 {fmt(mA['uji']['r2'], 3)} dan RMSE {fmt(mA['uji']['rmse'])}. Cuaca dan waktu saja belum cukup; "
              f"bias saat polusi parah {fmt(mA['polusi_parah']['parah']['bias'], 1)} ug/m3 ({'meremehkan' if mA['polusi_parah']['parah']['bias'] < 0 else 'melebihkan'}).")
if "pso" in hasil:
    rf, rp = hasil["model"]["rf_B"]["uji"]["rmse"], hasil["model"]["rf_pso_B"]["uji"]["rmse"]
    temuan.append(f"**Tuning PSO {'membantu' if rp < rf else 'tidak membantu'} di data uji.** RF default {fmt(rf)} berbanding RF + PSO {fmt(rp)}.")
if eks.get("pca"):
    p = eks["pca"]["B"]
    v = p["varian"]["0.95"]["metrik"]["rmse"]
    temuan.append(f"**PCA {'membantu' if v <= p['tanpa_pca']['rmse'] else 'merugikan'}.** Mengurangi kolom Mode B dari {p['n_fitur_setelah_enkode']} menjadi "
                  f"{p['varian']['0.95']['n_komponen']} (95% varians) mengubah RMSE dari {fmt(p['tanpa_pca']['rmse'])} menjadi {fmt(v)}; karena itu model final tidak memakai PCA.")
uk = hasil["uji_kejujuran"]
temuan.append(f"**Split acak tidak selalu tampak lebih bagus.** Mode A: R2 {fmt(uk['A']['split_acak']['uji']['r2'], 3)} (acak) vs {fmt(uk['A']['split_waktu']['uji']['r2'], 3)} (waktu); "
              f"Mode B: {fmt(uk['B']['split_acak']['uji']['r2'], 3)} vs {fmt(uk['B']['split_waktu']['uji']['r2'], 3)}.")
temuan.append(f"**R2 tinggi tidak cukup.** Persistence tanpa belajar sudah R2 {fmt(base1['r2'], 3)}; karena itu kami melaporkan MAE, RMSE, MedAE, "
              "selisih terhadap baseline, dan performa saat polusi parah.")
for t in temuan:
    st.markdown(f"- {t}")

st.subheader("Keterbatasan")
st.markdown(
    "- **Satu stasiun** (US Embassy Beijing). Hasil tidak otomatis berlaku untuk lokasi lain.\n"
    f"- **Periode 2010-2014** dan evaluasi di **satu tahun uji** ({hasil['data']['tahun_uji_mulai']}). Hasil di tahun lain bisa berbeda.\n"
    "- **Bukan real-time.** Aplikasi tidak mengambil data terbaru; semua prediksi dari input yang diberikan pengguna.\n"
    f"- **Hanya {len(cfg.KOLOM_CUACA_NUMERIK)} variabel cuaca** dan tidak ada data sumber emisi, sehingga Mode A terbatas.\n"
    "- **Prediksi satu jam ke depan** dari riwayat yang lengkap. Kualitas Mode B bergantung pada kebenaran riwayat PM2.5 yang dimasukkan; "
    "nilai kosong diisi nilai terakhir yang diketahui (bisa usang kalau kosongnya panjang).\n"
    f"- **Kategori udara per jam** memakai ambang AQI yang aslinya untuk rata-rata 24 jam (pendekatan). {cfg.CATATAN_AMBANG}\n"
    "- **Interval ketidakpastian hanya perkiraan kasar** dari kuantil residual satu tahun uji.\n"
    "- **Pencarian hyperparameter dibuat kecil** (PSO diperkecil agar muat di laptop i3), jadi belum tentu menemukan konfigurasi terbaik.")

st.subheader("Saran pengembangan")
st.markdown(
    "- Menguji **horizon lebih panjang** (misalnya 6 atau 24 jam ke depan), tempat baseline persistence diperkirakan melemah (belum diuji).\n"
    "- Menambah **stasiun dan tahun**, serta validasi berjalan (walk-forward) di beberapa tahun uji.\n"
    "- Menambah **fitur** seperti data sumber emisi atau kalender musim pemanas (belum diuji).\n"
    "- Mencoba **prediksi kategori** (klasifikasi) bila tujuan akhirnya peringatan kesehatan, bukan angka pasti.")

st.subheader("Daftar pustaka")
PUSTAKA = [
    "U.S. Environmental Protection Agency. (2024). Final Updates to the Air Quality Index (AQI) for Particulate Matter [fact sheet]. "
    "https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf",
    "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825-2830.",
    "Hoerl, A. E., & Kennard, R. W. (1970). Ridge regression: Biased estimation for nonorthogonal problems. Technometrics, 12(1), 55-67.",
    "Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5-32.",
    "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. The Annals of Statistics, 29(5), 1189-1232.",
    "Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization. Proceedings of ICNN'95 - International Conference on Neural Networks, 4, 1942-1948.",
    "Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. Philosophical Magazine, 2(11), 559-572.",
    "Bergmeir, C., & Benitez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. Information Sciences, 191, 192-213.",
    "Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts. https://otexts.com/fpp3/",
    "Chapman, P., et al. (2000). CRISP-DM 1.0: Step-by-step data mining guide. SPSS Inc.",
]
for i, p in enumerate(PUSTAKA, 1):
    st.markdown(f"{i}. {p}")
st.caption("Referensi nomor 3 sampai 11 ditulis dari pengetahuan umum penulis dan belum dicek ulang satu per satu ke sumbernya; cocokkan tahun, "
           "halaman, dan DOI sebelum dimasukkan ke daftar pustaka laporan. Nomor 1 dibaca langsung dari dokumen EPA. Nomor 2 harus diisi kelompok (SUMBER_DATASET di konfigurasi.py).")
