# PANDUAN DEPLOY (Streamlit Community Cloud)

Deploy itu **bonus, bukan syarat presentasi**. Kalau deploy bermasalah, presentasi tetap bisa dari laptop dengan `streamlit run app.py`.
Siapkan keduanya: tautan deploy sebagai tambahan, dan versi lokal sebagai cadangan.

## 1. Cek sebelum deploy

- [ ] `python -m alat.uji_halaman` lulus di laptop.
- [ ] `artifacts/` (isinya `models/*.joblib`, `hasil.json`, `prediksi_uji.csv`) dan `data/` ikut ter-commit. Cek `git status` bersih dan ukuran file model di bawah 100 MB (modelmu kecil, total sekitar 13 MB).
- [ ] `requirements.txt` ada di root repo dan berisi versi yang sama dengan env lokal yang terbukti jalan.
- [ ] `konfigurasi.py` sudah diisi (anggota, dosen, sumber dataset).
- [ ] Repo di GitHub (publik, atau privat yang diberi akses ke Streamlit).

## 2. Langkah

1. Buka https://share.streamlit.io lalu masuk dengan akun GitHub.
2. **Create app** -> pilih repo, branch `main`, file utama `app.py`.
3. Buka **Advanced settings** dan pilih **Python version**. Pilih yang sama dengan lokal (3.14) kalau ada di daftar; kalau tidak ada, pilih yang terdekat (lihat bagian 3).
4. **Deploy**, lalu tunggu proses build. Kalau gagal, buka **Manage app** -> log untuk melihat pesan error.
5. Setelah jalan, uji lima halaman: Beranda, Modelling dan Tuning, Uji Kejujuran Model, Prediksi Satu Input (tombol contoh), dan Prediksi Massal (unggah template).
6. Salin tautan aplikasi ke README.md dan simpan di bahan laporan.

## 3. requirements.txt dan versi Python

`requirements.txt` di proyek ini berisi **semua paket dengan versi persis** dari env lokal yang terbukti jalan (Python 3.14.2). Itu pilihan paling aman
kalau Cloud memakai Python yang sama. Kalau build gagal karena ada versi yang tidak tersedia untuk Python yang dipilih di Cloud:

1. Ganti nama `requirements.txt` menjadi `requirements-lengkap.txt`, lalu ganti nama `requirements-longgar.txt` menjadi `requirements.txt`
   (isinya hanya paket utama dengan versi persis; paket pendukung dibiarkan dipilih otomatis).
2. Commit dan push, lalu deploy ulang.
3. Kalau muncul peringatan "model dilatih dengan scikit-learn versi X" di halaman Prediksi, itu hanya peringatan: pastikan versi scikit-learn
   di requirements sama dengan yang tercatat di `artifacts/hasil.json` (bagian meta).

Yang dikonfirmasi dari dokumentasi Streamlit saat dokumen ini ditulis: versi Python dipilih lewat **Advanced settings** saat deploy dan dependensi dibaca dari `requirements.txt`
di repo (https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
Yang berasal dari **laporan pengguna di forum komunitas** (belum tentu masih berlaku, cek ulang): ada pengguna yang melaporkan Cloud memakai Python 3.14 walau memilih versi lain,
dan ada kegagalan start karena ketidakcocokan versi Starlette dengan Streamlit saat versi Streamlit tidak dikunci
(https://discuss.streamlit.io/t/streamlit-cloud-forcing-python-3-14-before-tensorflow-supports-it/121567,
https://discuss.streamlit.io/t/community-cloud-installs-incompatible-streamlit-starlette-versions-causing-gzipresponder-typeerror-on-startup/122128).
Karena itu `requirements.txt` kami mengunci Streamlit dan paket pendukungnya.

## 4. Masalah umum

| Gejala | Penyebab dan solusi |
|---|---|
| Build gagal: "No matching distribution found for ..." | paket itu tidak tersedia untuk Python yang dipilih. Pakai `requirements-longgar.txt` (bagian 3) atau pilih Python lain |
| App error saat start tapi lokal jalan | bandingkan versi paket di log Cloud dengan `pip list` lokal; kunci versi yang berbeda di requirements |
| "Hasil training belum ada" | folder `artifacts/` belum ter-commit (periksa `.gitignore`, `git status`, lalu push) |
| Halaman Prediksi: file model tidak ditemukan | `artifacts/models/*.joblib` belum ter-commit |
| Peringatan versi scikit-learn berbeda | samakan versi di requirements atau latih ulang dengan versi yang dipakai Cloud |
| Font judul tampak berbeda | Google Fonts butuh internet di perangkat penonton; ada font cadangan, aman diabaikan |

## 5. Setelah deploy

- Tulis tautan aplikasi di `README.md`.
- Jangan commit apa pun yang berisi kata sandi atau token (proyek ini tidak membutuhkannya).
- Setiap `git push` ke `main` otomatis memperbarui aplikasi di Cloud.
