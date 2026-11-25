# STATUS PROYEK: Langit Beijing (Prediksi PM2.5)

Terakhir diperbarui: Minggu, 22 Nov 2026 (Tahap 5: Prediksi, Kesimpulan, What-if, dokumentasi). Deadline: Rabu, 25 Nov 2026.

## Tahap
- [x] Tahap 0-1: brief, verifikasi, kode training (training penuh sudah jalan di laptop, 156 detik)
- [x] Tahap 2: app, tema terang kalem, Beranda, Tentang Dataset, EDA Umum
- [x] Tahap 3: Preprocessing (6 tab) dan PCA (3 tab) lengkap, dengan bukti dan kode. Belum: Feature Engineering dan Pola Waktu (halaman tambahan, menyusul bila sempat)
- [x] Tahap 4: halaman 6 Modelling & Tuning, 7 Evaluasi & Interpretasi, 8 Uji Kejujuran Model (dengan hasil.json asli)
- [x] Tahap 5: halaman 9 Prediksi Satu Input, 10 Prediksi Massal, 11 Kesimpulan, 14 What-if; README, CARA_MENJALANKAN, PRESENTASI, KAMUS_FUNGSI
- [ ] Tahap 6: deploy, PERBEDAAN_DENGAN_REFERENSI.md, latihan tanya-jawab

## File baru/berubah di Tahap 3
evaluasi/bukti_kode.py, evaluasi/bukti_eksperimen.py, PANDUAN_KODE.md (baru); halaman/04_preprocessing.py (ditulis ulang), halaman/05_pca.py (baru);
tampilan/grafik.py, tampilan/utilitas_app.py, alat/perbarui_panduan.py, PANDUAN_HALAMAN.md, alat/uji_cepat.py (diperluas).

## Struktur folder (dirapikan 22 Nov 2026)
preprocessing/ (data, fitur, tabel fitur, eksperimen), model/ (latih, PSO), evaluasi/ (metrik, kategori udara, bukti), tampilan/ (tema, grafik),
alat/ (tes dan pembaruan dokumen), dokumen/, halaman/. Perintah sekarang `python -m nama_folder.nama_file`. Detail: dokumen/PANDUAN_KODE.md.
eksperimen_ringan.py dipecah per topik (preprocessing, pca, ablasi). hasil.json dan .joblib TIDAK berubah (tidak perlu training ulang).

## Temuan hasil.json ASLI (21 Nov 2026) yang harus dijelaskan jujur di Tahap 4
- Mode B hanya menang tipis dari persistence 1 jam. RMSE uji: RF 20,52; HGB 20,92; RF+PSO 20,77; Ridge 21,30; DT 22,45; persistence 22,14.
- Di validasi silang, HGB_B (24,31) dan DT_B (25,70) lebih buruk dari persistence (24,20). Pemenang CV Mode B = Ridge (23,05), bukan RF.
- PSO tidak memperbaiki di data uji (RF+PSO 20,77 vs RF default 20,52); perbaikan hanya di sampel fitness PSO (25,32 vs 25,60).
- Mode A lemah (R2 0,42-0,46) dan sangat meremehkan polusi parah (bias sekitar -74 sampai -96 ug/m3).
- Uji Kejujuran: Mode A split acak R2 0,596 > split waktu 0,462 (bocor), TETAPI Mode B split acak 0,936 < split waktu 0,950. Jangan mengklaim "split acak selalu lebih tinggi".
- PCA mengurangi kolom tetapi menaikkan RMSE (Mode B 21,30 -> 29,19 pada 95% varians); log target memperburuk (Mode B 21,30 -> 174,66).
- Lag 1 jam hampir semua kekuatan Mode B (ablasi: hanya_lag1 RMSE 22,00 vs lengkap 21,30).

## Catatan Tahap 4
- Halaman 7 (grafik aktual vs prediksi dan residual) membaca artifacts/prediksi_uji.csv. File itu dibuat skrip latih di laptop kalian; di sandbox
  hanya diuji dengan versi dummy, jadi tampilannya dengan data asli belum pernah kulihat.
- Ringkasan di halaman 8 dan semua kalimat kesimpulan dihitung dari hasil.json; angka di dokumen/PANDUAN_HALAMAN.md diisi `python -m alat.perbarui_panduan`.

## Catatan Tahap 5
- Halaman 9, 10, 14 memuat model dari artifacts/models/*.joblib. Di sandbox hanya diuji dengan model DUMMY (data kecil); dengan model asli di laptop belum pernah kulihat.
- Daftar pustaka halaman 11: hanya sumber EPA yang diverifikasi; sisanya dari pengetahuan umum, cek ulang sebelum masuk laporan.
- Halaman tambahan 12 (Pola Waktu dan Cuaca) dan 13 (Feature Engineering) BELUM dibuat; menu otomatis memunculkannya begitu filenya ada.
- Dokumen otomatis: python -m alat.perbarui_panduan (angka di PANDUAN_HALAMAN, PANDUAN_KODE, PRESENTASI + KAMUS_FUNGSI).

## Diuji di sandbox (Python 3.12, pandas 3.0.6, Streamlit 1.67.0)
alat/uji_cepat.py, alat/uji_halaman.py (dengan hasil.json asli), evaluasi/bukti_eksperimen.py --dummy, screenshot halaman. Belum diuji di laptop (Python 3.14.2).
evaluasi/bukti_eksperimen.py TANPA --dummy belum pernah dijalankan terhadap hasil.json asli: jalankan di laptop dan laporkan hasilnya.

## Masalah terbuka
- Nama anggota, NIM, dosen, halaman wajib dosen, SUMBER_DATASET masih [ISI] di konfigurasi.py.
- Saran kesehatan di evaluasi/kategori_udara.py perlu dicocokkan dengan airnow.gov.
- Ukuran model asli kecil (maks sekitar 5,7 MB per file), aman untuk GitHub.
