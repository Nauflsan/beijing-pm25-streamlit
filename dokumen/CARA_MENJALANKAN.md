# CARA MENJALANKAN

Semua perintah dijalankan di PowerShell, di folder `web_pm25_beijing`, dengan environment aktif.

## 1. Persiapan (sekali)

```
cd E:\Program_Semester_5\Machine_Learning\web_pm25_beijing
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Kalau muncul "running scripts is disabled", jalankan dulu `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`.
Taruh dataset di `data\PRSA_Beijing_PM25_2010_2014_clean.csv`.

## 2. Tes sebelum training

```
python -m alat.uji_cepat
```

Harus berakhir dengan `UJI CEPAT LULUS`. Tes ini hanya menulis ke `artifacts_dummy\` (artefak dummy dari data kecil, bukan hasil asli).

## 3. Training (di laptop, sekali)

```
python -m model.latih_semua_model --penuh
```

- Tiap model disimpan begitu selesai. Kalau terhenti, jalankan perintah yang sama; model yang sudah selesai dilewati.
- `--ulang` memaksa latih dari nol. `--cepat` hanya untuk uji alur (hasilnya bukan untuk laporan).
- Keluaran: `artifacts\models\*.joblib`, `artifacts\hasil.json`, `artifacts\prediksi_uji.csv`, log di `logs\`.
- Kalau laptop jadi lemot, ubah `N_JOBS = 2` di `konfigurasi.py`.

## 4. Menjalankan web

```
streamlit run app.py
```

Buka alamat yang tertera (biasanya http://localhost:8501). Tes semua halaman tanpa browser: `python -m alat.uji_halaman`.

## 5. Memperbarui dokumen

```
python -m alat.perbarui_panduan
```

Mengisi ulang angka di PANDUAN_HALAMAN, PANDUAN_KODE, PRESENTASI dari `hasil.json`, dan membuat ulang KAMUS_FUNGSI. Jalankan setiap selesai training ulang.

## 6. Membuktikan angka eksperimen

```
python -m evaluasi.bukti_eksperimen
```

Menghitung ulang eksperimen (isi kosong, skala, log, PCA, ablasi) dari data dan membandingkannya dengan `hasil.json`. Hasil yang diharapkan: COCOK.

## 7. Git dan deploy (Streamlit Community Cloud)

```
git status
git add -A
git commit -m "pesan commit"
git push
```

Folder `artifacts\` sengaja ikut di-commit (web membaca model dari repo). Cek ukuran file model sebelum commit; batas GitHub 100 MB per file.
`env\`, `logs\`, `artifacts_dummy\`, `bahan_laporan\` sudah dikecualikan di `.gitignore`.

Deploy (garis besar, detail dan pengecekan versi menyusul di Tahap 6):
1. Buat aplikasi baru di Streamlit Community Cloud dari repo GitHub ini, file utama `app.py`.
2. Pada pengaturan lanjutan, pilih versi Python yang sama dengan lokal kalau tersedia; kalau tidak, pilih yang terdekat dan pastikan
   versi paket di `requirements.txt` cocok (model dilatih dengan scikit-learn tertentu; web memperingatkan kalau versinya berbeda).
3. Tunggu build selesai lalu buka tautan aplikasi.

## 8. Masalah umum

| Gejala | Penyebab dan solusi |
|---|---|
| `ModuleNotFoundError: No module named 'model'` | skrip dijalankan dengan cara lama. Pakai `python -m nama_folder.nama_file` dari folder proyek |
| Halaman menampilkan "Hasil training belum ada" | `artifacts\hasil.json` belum ada. Jalankan langkah 3 |
| Halaman Evaluasi tanpa grafik aktual vs prediksi | `artifacts\prediksi_uji.csv` belum ada. Jalankan training lagi (`--ulang` bila perlu) |
| Peringatan versi scikit-learn berbeda | samakan versi di `requirements.txt` dengan yang tercatat di `hasil.json` (bagian meta), atau latih ulang |
| `FileNotFoundError` data | CSV belum ada di `data\` atau namanya berbeda dari `konfigurasi.FILE_CSV` |
| Grafik Altair kosong | gunakan kolom `pm25` (salinan dari `pm2.5`), bukan `pm2.5`; titik dianggap properti bersarang oleh Vega-Lite |
