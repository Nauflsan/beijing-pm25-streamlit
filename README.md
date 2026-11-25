# Langit Beijing: Prediksi PM2.5 (Machine Learning, Streamlit)

Aplikasi web untuk memprediksi **PM2.5 per jam di Beijing (2010-2014)** dengan lima model regresi, dibuat untuk tugas kelompok mata kuliah
Machine Learning. Fokus proyek: hasil yang **diuji jujur** (baseline persistence, split berdasarkan waktu, validasi silang berurutan waktu),
bukan sekadar angka yang terlihat bagus.

## Ringkas

- **Data:** 43.824 jam, 13 kolom, satu stasiun (`data/PRSA_Beijing_PM25_2010_2014_clean.csv`).
- **Model:** Ridge, Decision Tree, Random Forest, HistGradientBoosting, Random Forest + PSO.
- **Dua mode fitur:** Mode A (cuaca + waktu) dan Mode B (ditambah lag dan rata-rata bergulir PM2.5).
- **Evaluasi:** latih 2010-2013, uji 2014; MAE, RMSE, R2, MedAE; error per bulan, per kategori udara, dan saat polusi parah.
- **Halaman** (menu navigasi di atas): Beranda, Tentang Dataset, EDA, Preprocessing, PCA, Modelling dan Tuning, Evaluasi dan Interpretasi,
  Uji Kejujuran Model, Prediksi Satu Input, Prediksi Massal, Kesimpulan, dan What-if Simulator (tambahan). Dua halaman tambahan lain
  (Pola Waktu dan Cuaca, Feature Engineering) menyusul; menunya otomatis muncul begitu filenya ada.
- Training dilakukan **di laptop**, hasilnya disimpan di `artifacts/` (`hasil.json` + `models/*.joblib`); web hanya membaca hasil, tidak melatih.

## Cara cepat

```
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alat.uji_cepat                       # tes sebelum training
python -m model.latih_semua_model --penuh      # training (sekali)
streamlit run app.py
```

Detail langkah, tes, dan deploy: `dokumen/CARA_MENJALANKAN.md`.

## Struktur folder

```
app.py, konfigurasi.py        pintu masuk web dan semua konstanta
data/  artifacts/             dataset dan hasil training
halaman/                      halaman web
preprocessing/  model/  evaluasi/  tampilan/  alat/   kode, dikelompokkan menurut fungsinya
dokumen/                      panduan (kode, halaman, presentasi, kamus fungsi, status)
```

## Dokumentasi

| File | Isi |
|---|---|
| `dokumen/CARA_MENJALANKAN.md` | menjalankan, tes, deploy, masalah umum |
| `dokumen/PANDUAN_KODE.md` | peta file, alur data, "kalau mau ganti X ubah Y" |
| `dokumen/PANDUAN_HALAMAN.md` | tiap halaman: tujuan, cara menjelaskan, pertanyaan dosen |
| `dokumen/PRESENTASI.md` | naskah presentasi, cara baca grafik, pertanyaan sulit |
| `dokumen/KAMUS_FUNGSI.md` | semua fungsi dan penjelasannya (dibuat otomatis dari kode) |
| `dokumen/STATUS_PROYEK.md` | status tahap dan temuan |

## Catatan jujur tentang hasil

Persistence (menebak nilai jam lalu) sudah sangat kuat karena PM2.5 per jam sangat mirip dengan jam sebelumnya. Model Mode B hanya
sedikit lebih baik darinya; Mode A jauh lebih lemah. Angka lengkap ada di halaman Uji Kejujuran Model dan dihitung dari `artifacts/hasil.json`.
Aplikasi ini bahan belajar, bukan alat keputusan kesehatan. Keterbatasan: satu stasiun, 2010-2014, bukan real-time.

## Kelompok

Isi nama kelompok, anggota, NIM, dan dosen di `konfigurasi.py` (bagian 7).
