# PERBEDAAN DENGAN REFERENSI

Instruksi dosen: **tiru lalu modifikasi** web referensi. Referensi kami: repo `saqialfaruq/telco-churn-app` (karya kelompok lain: prediksi churn pelanggan Telco, masalah **klasifikasi**).
Kami mempelajari POLA-nya lalu menulis ulang dengan struktur dan gaya sendiri untuk masalah yang berbeda: **regresi deret waktu PM2.5 Beijing**. Tidak ada kode yang disalin mentah.

Fakta tentang referensi di dokumen ini dibaca dari isi repo-nya (README, `app.py`, `train_all.py`, `utils.py`, folder `halaman/`, `artifacts/hasil.json`).
Fakta tentang proyek kami bisa dibuktikan lewat file atau halaman di kolom paling kanan.

---

## 1. Yang kami tiru idenya (pola)

| Pola di referensi | Kami terapkan sebagai |
|---|---|
| Multi-halaman dengan `st.navigation` dan `st.Page`, halaman di folder `halaman/` | `app.py` + `halaman/` (menu di atas, 5 grup) |
| Model dilatih sekali di skrip terpisah, disimpan ke `artifacts/*.joblib` dan `hasil.json`; app hanya membaca | `model/latih_semua_model.py` -> `artifacts/` |
| Preprocessing ikut tersimpan bersama model lewat `Pipeline` + `ColumnTransformer` | `preprocessing/fitur_waktu.py` (`buat_pipeline`) |
| Halaman prediksi memakai `st.form`; ada prediksi massal lewat unggah CSV | halaman 9 dan 10 |
| Halaman Dataset, EDA, Preprocessing, PCA, Modelling, Kesimpulan | halaman 2, 3, 4, 5, 6, 11 |

---

## 2. Tabel perbedaan

| Aspek | Referensi | Punya kita | Di file atau halaman mana |
|---|---|---|---|
| Masalah | Klasifikasi biner (churn pelanggan) | **Regresi deret waktu**: memprediksi angka PM2.5 per jam | seluruh proyek |
| Data | Tabular pelanggan (`Telco_customer_churn.csv`) | Deret waktu per jam, 43.824 baris, 2010-2014, satu stasiun | `data/`, halaman 2 |
| Model | Logistic Regression, KNN, Decision Tree, Random Forest, Gradient Boosting; tuning GridSearchCV | Ridge, Decision Tree, Random Forest, HistGradientBoosting, **Random Forest + PSO** | `model/latih_semua_model.py`, `model/pso_random_forest.py`, halaman 6 |
| Cara membagi data | `train_test_split` 80/20 acak berstrata | **Split berdasarkan waktu** (latih 2010-2013, uji 2014) + `TimeSeriesSplit` pada data latih | `preprocessing/fitur_waktu.py` (`bagi_waktu`), `evaluasi/evaluasi_regresi.py` (`cv_regresi`), halaman 4 dan 6 |
| Fitur | Kolom tabular, one-hot, scaler | **Sin-cos jam dan bulan, lag, rata-rata bergulir**, dua mode (A tanpa riwayat, B dengan riwayat) | `preprocessing/fitur_waktu.py`, halaman 4 dan 13 |
| Pencegahan kebocoran waktu | Tidak relevan (data bukan deret waktu) | Shift sebelum rolling, forward fill, imputer/scaler di dalam Pipeline, **tes otomatis kebocoran** | `alat/uji_cepat.py`, halaman 4 dan 13 |
| Metrik | Metrik klasifikasi (tuning memakai f1 dan roc_auc) | MAE, RMSE, R2, MedAE, bias; error per bulan, per kategori udara, dan saat polusi parah | `evaluasi/evaluasi_regresi.py`, halaman 7 |
| Pembanding | `baseline_tuning` (sebelum dan sesudah tuning) | **Baseline persistence** (1 jam, 24 jam) dan rata-rata data latih, selain sebelum/sesudah tuning PSO | `model/latih_semua_model.py` (`hitung_baseline`), halaman 6 dan 8 |
| Uji kejujuran | Tidak ada halaman khusus | **Halaman Uji Kejujuran Model**: split acak vs waktu, baseline, R2 yang menipu, polusi parah | halaman 8 |
| Interpretasi | Tab Fitur Penting | Permutation importance **dan** partial dependence untuk model terbaik tiap mode | halaman 7 |
| Eksperimen preprocessing | PCA | PCA + SelectKBest, cara isi data kosong (termasuk yang bocor sebagai pembanding), skala, log target, ablasi fitur | `preprocessing/eksperimen_*.py`, halaman 4, 5, 13 |
| Prediksi satu input | Form + ambang (threshold) + indikator risiko + rekomendasi retensi | Demo dari data asli atau form manual, **gauge Plotly**, kategori udara berwarna, saran kesehatan, **rentang ketidakpastian**, bandingkan semua model | halaman 9, `model/prediksi.py` |
| Prediksi massal | Unggah CSV dan unduh | + template unduhan, **validasi dengan pesan ramah** (kolom, arah angin, jam bolong), error vs aktual, grafik, ringkasan kategori | halaman 10 |
| Halaman tambahan | Tidak ada | What-if Simulator, Pola Waktu dan Cuaca, Feature Engineering (bisa dimatikan lewat saklar) | halaman 12, 13, 14, `konfigurasi.py` |
| Navigasi | 9 halaman, 3 grup, menu samping | **14 halaman**, 5 grup, menu di atas, halaman yang belum ada otomatis tersembunyi | `app.py` |
| Tampilan | Biru muda polos | Tema **Langit Beijing**: biru langit kalem, aksen warna kategori udara, terang saja | `tampilan/tema_langit_beijing.py` |
| Skrip training | Satu skrip, berjalan sekali | Profil `--cepat` dan `--penuh`, **resume** model yang sudah selesai, log ke file, perkiraan sisa waktu, peringatan ukuran file | `model/latih_semua_model.py` |
| Struktur kode | Datar (`app.py`, `charts.py`, `utils.py`, `train_all.py`) | Dikelompokkan: `preprocessing/`, `model/`, `evaluasi/`, `tampilan/`, `alat/`, `dokumen/` | `dokumen/PANDUAN_KODE.md` |
| Konstanta | Tersebar di beberapa file | Semua di satu `konfigurasi.py` dengan tag [UBAH], [TERKAIT], [JANGAN UBAH] | `konfigurasi.py` |
| Bukti hasil | Angka dibaca dari `hasil.json` | Sama, **ditambah** expander yang menampilkan kode asli (file dan baris), dan skrip yang menghitung ulang eksperimen lalu mencocokkannya | `evaluasi/bukti_kode.py`, `evaluasi/bukti_eksperimen.py` |
| Pengujian | Tidak ditemukan skrip tes di repo | `uji_cepat` (kebocoran, konsistensi fitur, alur latih), `uji_halaman` (semua halaman) | `alat/` |
| Dokumentasi | Satu README | README, CARA_MENJALANKAN, PANDUAN_KODE, PANDUAN_HALAMAN, PRESENTASI, KAMUS_FUNGSI (otomatis dari kode), PANDUAN_DEPLOY, LATIHAN_TANYA_JAWAB | `dokumen/` |

---

## 3. Bahan bicara (30 detik)

"Kami meniru pola referensi: multi-halaman, training terpisah yang disimpan ke artefak, Pipeline, form prediksi, dan unggah massal.
Perbedaannya mendasar karena masalahnya berbeda: referensi klasifikasi tabular, kami regresi deret waktu. Karena itu kami menambahkan hal-hal yang tidak ada di
klasifikasi biasa: split berdasarkan waktu, fitur lag tanpa kebocoran, baseline persistence, dan halaman Uji Kejujuran yang menguji apakah hasilnya benar-benar bagus.
Tampilannya juga kami rancang ulang dengan tema Langit Beijing dan menu di atas."

## 4. Jangan salah bicara

- Jangan bilang referensi "tidak punya interpretasi fitur": mereka punya tab Fitur Penting. Perbedaan kami ada pada permutation importance dan partial dependence.
- Jangan bilang kami "menemukan" PCA, form, atau unggah massal: itu pola yang kami tiru idenya; yang kami tambah adalah validasi, template, dan konteks deret waktu.
- Jangan membandingkan kualitas hasil model (referensi: klasifikasi; kami: regresi); angkanya tidak sebanding.
