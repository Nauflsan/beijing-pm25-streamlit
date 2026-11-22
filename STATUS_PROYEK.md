# STATUS PROYEK: Langit Beijing (Prediksi PM2.5)

Terakhir diperbarui: Minggu, 22 Nov 2026 (Tahap 2 + perapian tampilan). Deadline: Rabu, 25 Nov 2026.

## Tahap
- [x] Tahap 0: baca brief, verifikasi dataset, usulan struktur
- [x] Tahap 1: konfigurasi, utilitas data, fitur, evaluasi, PSO, skrip latih, uji cepat (training penuh sudah dijalankan di laptop)
- [x] Tahap 2: app.py, tema Langit Beijing, Beranda, Tentang Dataset, EDA Umum, Preprocessing (SEBAGIAN: tabel kolom ke fitur)
- [ ] Tahap 3: sisa Preprocessing (isi kosong, outlier, log target, split, scaling), PCA (+ Feature Engineering, Pola Waktu kalau sempat)
- [ ] Tahap 4: Modelling & Tuning, Evaluasi & Interpretasi, Uji Kejujuran (butuh hasil.json asli)
- [ ] Tahap 5: Prediksi Satu Input, Prediksi Massal, Kesimpulan, What-if, dokumentasi lengkap
- [ ] Tahap 6: deploy, PERBEDAAN_DENGAN_REFERENSI.md, latihan tanya-jawab

## File
| File | Status | Catatan |
|---|---|---|
| konfigurasi.py | diubah di Tahap 2 | tambah PAKAI_ARTEFAK_DUMMY/FOLDER_ARTEFAK_AKTIF dan bagian 9 (tampilan, SUMBER_DATASET, STASIUN_CATATAN) |
| utilitas_data.py | diubah di Tahap 2 | tambah fmt_id (format angka Indonesia) |
| uji_cepat.py | diubah di Tahap 2 | tambah cek peta_fitur |
| utilitas_app.py, grafik.py, tema_langit_beijing.py, app.py | selesai | kerangka, tema, grafik |
| peta_fitur.py | selesai | tabel 13 kolom ke fitur + 5 tanya-jawab dosen, semua angka dari hasil.json |
| halaman/01_beranda.py, 02_tentang_dataset.py, 03_eda_umum.py | selesai | |
| halaman/04_preprocessing.py | SEBAGIAN | baru bagian tabel kolom ke fitur |
| perbarui_panduan.py, PANDUAN_HALAMAN.md | selesai untuk halaman 1-4 | angka diisi otomatis dari hasil.json |
| uji_halaman.py | selesai | uji asap semua halaman (AppTest) |
| .streamlit/config.toml | selesai | |

## Diuji di sandbox (Python 3.12, pandas 3.0.6, streamlit 1.67.0, artefak DUMMY)
- uji_cepat.py lulus; uji_halaman.py lulus; tampilan terang dicek lewat screenshot (juga saat browser disetel mode gelap: tetap terang).
- Belum diuji: di laptop (Python 3.14.2, pandas 3.1.1), dengan hasil.json ASLI, dan dengan font Google (sandbox tanpa internet ke fonts).

## Keputusan tampilan (22 Nov 2026)
- Hanya mode TERANG (config.toml base=light, menu pengaturan disembunyikan lewat CSS). Mode gelap sengaja tidak didukung.
- Header biru langit kalem; warna kategori udara hanya jadi aksen kecil (titik + label di kartu KPI), tidak lagi mewarnai header/kartu.
- Palet tema ada di konfigurasi.py bagian 9 dan .streamlit/config.toml (harus sama).

## Masalah terbuka
- Nama anggota, NIM, dosen, halaman wajib dosen masih [ISI] di konfigurasi.py; SUMBER_DATASET juga [ISI].
- Saran kesehatan di kategori_udara.py perlu dicocokkan dengan airnow.gov sebelum dikutip di laporan.
- Ukuran file model asli: cek sebelum commit/push (batas GitHub 100 MB per file).

## Tahap berikutnya
Tahap 3: lengkapi Preprocessing dan PCA.
