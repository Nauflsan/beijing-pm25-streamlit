# LATIHAN TANYA-JAWAB

30 pertanyaan yang paling mungkin ditanya dosen, dengan jawaban singkat (2-3 kalimat) dan tempat membuktikannya di aplikasi atau kode.
Angka diisi otomatis dari `artifacts/hasil.json` oleh `python -m alat.perbarui_panduan`.

## Cara berlatih (20 menit)

1. Tutup dokumen ini, baca satu pertanyaan dari daftar, jawab dengan suara keras tanpa melihat jawaban (target 30 detik).
2. Buka jawabannya, cocokkan inti jawabanmu (yang penting intinya, bukan kata per kata).
3. Tandai yang meleset, ulang hanya yang meleset. Lakukan berpasangan dengan anggota kelompok: satu bertanya, satu menjawab, lalu bergantian.
4. Untuk setiap pertanyaan, latih juga **menunjukkan buktinya** di halaman atau kode yang tertulis di kolom "Buktikan di".
5. Kalau tidak tahu jawabannya di depan dosen: katakan apa yang kamu tahu, lalu "itu kami catat sebagai keterbatasan", jangan mengarang angka.

---

## A. Konsep dasar

1. **Apa beda MAE dan RMSE, dan kenapa dua-duanya?** MAE = rata-rata meleset dalam ug/m3; RMSE mengkuadratkan selisih sehingga lebih menghukum kesalahan besar. Dua-duanya dipakai karena lonjakan polusi (kesalahan besar) penting. Contoh Random Forest Mode B: MAE <!--ANGKA:m_rf_B_mae-->11,38<!--/ANGKA-->, RMSE <!--ANGKA:m_rf_B_rmse-->20,52<!--/ANGKA-->. *Buktikan di:* Evaluasi tab Metrik.
2. **Apa itu R2 dan kapan ia menipu?** R2 = bagian variasi yang dijelaskan dibanding tebakan "selalu rata-rata". Pada data yang sangat mirip dari jam ke jam, tebakan nilai jam lalu saja sudah R2 <!--ANGKA:b_persistence_1jam_r2-->0,944<!--/ANGKA-->. *Buktikan di:* Uji Kejujuran tab R2 vs MAE vs RMSE.
3. **Apa itu overfitting dan bagaimana kalian mencegahnya?** Model terlalu hafal data latih sehingga buruk di data baru. Kami membatasi kedalaman pohon dan jumlah sampel daun, memakai regularisasi pada Ridge, memakai validasi silang berurutan waktu, dan menguji di tahun yang tidak pernah dilihat saat latih. *Buktikan di:* Modelling tab Lima model dan Validasi silang.
4. **Kenapa validasi silang biasa tidak dipakai?** K-fold biasa mengacak urutan sehingga masa depan bisa ikut melatih model untuk memprediksi masa lalu. `TimeSeriesSplit` selalu melatih di masa lalu dan menguji di masa sesudahnya. *Buktikan di:* Preprocessing tab Split waktu (gambar lipatan), `evaluasi/evaluasi_regresi.py` fungsi `cv_regresi`.
5. **Apa itu one-hot dan kenapa arah angin memakainya?** Arah angin kategori tanpa urutan; one-hot memecahnya jadi kolom 0/1 per kategori supaya model tidak menganggap NE < NW < SE < cv. Satu fitur jadi 4 kolom, itu sebabnya <!--ANGKA:n_fitur_a-->11<!--/ANGKA--> fitur menjadi <!--ANGKA:n_enkode_a-->14<!--/ANGKA--> kolom. *Buktikan di:* Preprocessing tab Kolom ke fitur.
6. **Kenapa jam dan bulan diubah ke sin dan cos?** Jam 23 dan jam 0 bertetangga; angka biasa membuat model mengira keduanya jauh. Satu sudut butuh dua koordinat, jadi sin dan cos. *Buktikan di:* Feature Engineering tab Fitur waktu siklik.
7. **Apa itu PSO dan bagaimana dipakai di sini?** Sekawanan "partikel" mencari kombinasi hyperparameter terbaik dengan saling meniru posisi terbaik. Di sini PSO mencari jumlah pohon, kedalaman, dan sampel daun Random Forest, dengan fitness dari validasi silang berurutan pada data latih saja. *Buktikan di:* Modelling tab RF vs RF + PSO, `model/pso_random_forest.py`.
8. **Apa itu baseline persistence dan kenapa penting?** Menebak nilai jam lalu sebagai prediksi. Model baru berguna kalau mengalahkannya; di data ini ia sangat kuat. *Buktikan di:* Uji Kejujuran tab Baseline persistence.

## B. Data dan preprocessing

9. **Kenapa 13 kolom tapi fitur hanya 11 (Mode A) dan 17 (Mode B)?** Satu kolom jadi target (pm2.5), tiga tidak dipakai sebagai fitur (No, year, day), sisanya jadi fitur; Mode B menambah <!--ANGKA:n_lag_roll-->6<!--/ANGKA--> fitur riwayat. *Buktikan di:* Preprocessing tab Kolom ke fitur.
10. **Bagaimana menangani data kosong?** Baris dengan pm2.5 kosong tidak jadi target; untuk fitur lag nilai kosong diisi nilai terakhir yang diketahui (forward fill), yang hanya memakai masa lalu. Interpolasi lebih kecil errornya (<!--ANGKA:isi_interp-->21,17<!--/ANGKA--> vs <!--ANGKA:isi_ffill-->21,30<!--/ANGKA-->) tetapi mengintip masa depan sehingga tidak dipakai. *Buktikan di:* Preprocessing tab Data kosong.
11. **Kenapa outlier tidak dibuang?** Itu kejadian polusi parah, bagian yang paling penting dinilai; dibuang berarti kita tidak tahu kinerja di jam paling berbahaya. Dampaknya dinilai terpisah lewat metrik polusi parah. *Buktikan di:* Preprocessing tab Outlier.
12. **Kenapa tidak memakai log pada target?** Dicoba dan dievaluasi di skala asli: Mode B RMSE jadi <!--ANGKA:log_b_log-->174,66<!--/ANGKA--> vs <!--ANGKA:log_b_asli-->21,30<!--/ANGKA-->. Jadi memburuk dan tidak dipakai. *Buktikan di:* Preprocessing tab Log target.
13. **Kenapa split berdasarkan waktu?** Data berurutan dan PM2.5 mirip dari jam ke jam; split acak membuat jam bertetangga ada di latih dan uji sekaligus. Kami latih 2010-2013 (<!--ANGKA:n_latih-->33.072<!--/ANGKA--> baris) dan uji 2014 (<!--ANGKA:n_uji-->8.661<!--/ANGKA--> baris). *Buktikan di:* Preprocessing tab Split waktu.
14. **Bagaimana kalian mencegah data bocor?** Split waktu; imputer dan scaler di dalam Pipeline (hanya belajar dari data latih); lag dan rata-rata hanya memakai jam sebelumnya (digeser dulu); tes otomatis yang mengubah masa depan dan memastikan fitur tidak berubah. *Buktikan di:* `python -m alat.uji_cepat`, Feature Engineering tab Lag.

## C. Hasil

15. **Apakah modelnya bagus?** Sederhana: Mode B hanya <!--ANGKA:terbaik_uji_b_skill-->7,3<!--/ANGKA-->% lebih baik RMSE-nya dari persistence (<!--ANGKA:terbaik_uji_b_rmse-->20,52<!--/ANGKA--> vs <!--ANGKA:b_persistence_1jam_rmse-->22,14<!--/ANGKA-->); Mode A lemah (R2 <!--ANGKA:pem_a_r2-->0,462<!--/ANGKA-->). Itu hasil jujur karena baseline kuat. *Buktikan di:* Uji Kejujuran, kotak ringkasan.
16. **Kenapa Mode A jauh dari data aktual?** Mode A sengaja tanpa riwayat PM2.5; ia mengukur seberapa jauh cuaca dan waktu saja menjelaskan polusi, dan cenderung meremehkan lonjakan (bias <!--ANGKA:pem_a_parah_bias-->-74,2<!--/ANGKA--> ug/m3 saat polusi parah). *Buktikan di:* Evaluasi (Mode A, tab Aktual vs prediksi).
17. **Model mana yang kalian pakai?** Mode B sebagai model utama, Mode A sebagai pembanding dan cadangan. Model terbaik dipilih lewat validasi silang: <!--ANGKA:pem_b_nama-->Ridge Regression<!--/ANGKA--> (Mode B) dan <!--ANGKA:pem_a_nama-->HistGradientBoosting<!--/ANGKA--> (Mode A). *Buktikan di:* Modelling tab Lima model.
18. **Kenapa dipilih lewat validasi silang, padahal di data uji Random Forest lebih baik?** Supaya pemilihan tidak mengintip data uji. Selisih antar model dekat sehingga urutannya mudah bergeser; kami menampilkan keduanya. *Buktikan di:* Modelling tab Lima model (kalimat di bawah tabel).
19. **Apakah PSO berguna?** Di sampel pencarian ya (<!--ANGKA:pso_fit_pembanding-->25,60<!--/ANGKA--> ke <!--ANGKA:pso_fit_terbaik-->25,32<!--/ANGKA-->), di data uji tidak (<!--ANGKA:m_rf_B_rmse-->20,52<!--/ANGKA--> vs <!--ANGKA:m_rf_pso_B_rmse-->20,77<!--/ANGKA-->). Dugaan: sedikit menyesuaikan diri dengan sampel; belum diuji lebih jauh. *Buktikan di:* Modelling tab RF vs RF + PSO.
20. **Kenapa PCA tidak dipakai?** Dicoba (Ridge): Mode B turun dari <!--ANGKA:pca_awal_b-->20<!--/ANGKA--> ke <!--ANGKA:pca_k95_b-->12<!--/ANGKA--> kolom tetapi RMSE naik dari <!--ANGKA:pca_rmse_tanpa_b-->21,30<!--/ANGKA--> ke <!--ANGKA:pca_rmse95_b-->29,19<!--/ANGKA-->. *Buktikan di:* halaman PCA tab Bukti dan kode, `python -m evaluasi.bukti_eksperimen --bagian pca`.
21. **Fitur apa yang paling penting?** Di Mode B `<!--ANGKA:imp_top_b-->pm25_lag1<!--/ANGKA-->`: kalau diacak RMSE naik <!--ANGKA:imp_top_b_nilai-->119,4<!--/ANGKA--> ug/m3. Cuaca dan waktu hampir tidak mengubah hasil di Mode B (ablasi). *Buktikan di:* Evaluasi tab Interpretasi, Feature Engineering tab Ablasi.
22. **Apakah split acak selalu terlihat lebih bagus?** Tidak. Mode A: R2 acak <!--ANGKA:uj_acak_r2_a-->0,596<!--/ANGKA--> vs waktu <!--ANGKA:uj_waktu_r2_a-->0,462<!--/ANGKA--> (tampak lebih bagus); Mode B: <!--ANGKA:uj_acak_r2_b-->0,936<!--/ANGKA--> vs <!--ANGKA:uj_waktu_r2_b-->0,950<!--/ANGKA--> (tidak). Uji acak mencakup 2010-2014, uji waktu hanya 2014, jadi ini menunjukkan arah, bukan ukuran persis. *Buktikan di:* Uji Kejujuran tab Split acak vs waktu.

## D. Kode dan implementasi

23. **Kenapa web tidak melatih model?** Training berat dan tidak perlu diulang tiap pengguna membuka halaman. Skrip latih dijalankan sekali di laptop, hasilnya disimpan di `artifacts/` dan web hanya membaca, sehingga cepat dan konsisten. *Buktikan di:* `dokumen/PANDUAN_KODE.md` bagian alur data.
24. **Kenapa memakai Pipeline?** Preprocessing (imputer, scaler, one-hot) ikut tersimpan bersama model, jadi prediksi di web memakai langkah yang sama persis dengan training dan tidak ada ketidakcocokan. *Buktikan di:* `preprocessing/fitur_waktu.py` fungsi `buat_pipeline`.
25. **Bagaimana prediksi satu input dibuat?** Input diubah ke baris fitur dengan fungsi `buat_baris_fitur` (rumus sama dengan training, diuji kecocokannya), lalu dimasukkan ke Pipeline model. *Buktikan di:* Prediksi Satu Input, expander Kode; `alat/uji_cepat.py`.
26. **Bagaimana kalian memastikan angka di web bukan karangan?** Semua angka model dibaca dari `artifacts/hasil.json`; eksperimen bisa dihitung ulang dengan `python -m evaluasi.bukti_eksperimen` (harus COCOK); kode asli tiap hasil ditampilkan di halaman. *Buktikan di:* halaman PCA tab Bukti dan kode.
27. **Dari mana rentang ketidakpastian di halaman Prediksi?** Dari kuantil residual model di data uji, dikelompokkan menurut kategori prediksi (rentang 90%). Itu perkiraan kasar dari satu tahun data, bukan jaminan. *Buktikan di:* Evaluasi tab Residual, `model/prediksi.py` fungsi `interval_prediksi`.

## E. Keterbatasan, deploy, dan pengembangan

28. **Apa keterbatasan proyek ini?** Satu stasiun, 2010-2014, evaluasi di satu tahun uji, bukan real-time, hanya enam variabel cuaca, kategori udara per jam adalah pendekatan, dan pencarian PSO dibuat kecil. *Buktikan di:* halaman Kesimpulan.
29. **Kenapa tidak memakai deep learning (LSTM)?** Dibatasi laptop CPU i3 dan waktu; model klasik lebih mudah dijelaskan dan dilatih dalam sekitar <!--ANGKA:total_waktu_detik-->59<!--/ANGKA--> detik ditambah PSO <!--ANGKA:pso_detik-->73<!--/ANGKA--> detik. Deep learning masuk saran pengembangan dan belum dicoba.
30. **Apa yang akan kalian perbaiki kalau ada waktu?** Horizon prediksi lebih panjang (misalnya 6 atau 24 jam, belum diuji), lebih banyak stasiun dan tahun, validasi berjalan di beberapa tahun uji, dan fitur sumber emisi. *Buktikan di:* halaman Kesimpulan, bagian Saran.

---

## Pertanyaan jebakan (jawab jujur, jangan membela diri)

- **"Kalau cuma 7% lebih baik, apa gunanya?"** Gunanya menunjukkan dengan angka bahwa riwayat PM2.5 yang menentukan; model lebih rumit belum tentu jauh lebih baik. Kontribusinya pengujian yang jujur, bukan hasil yang spektakuler.
- **"Kalian yakin tidak ada kebocoran?"** Kami uji langsung: tes otomatis mengubah semua nilai masa depan dan memastikan fitur tidak berubah (`python -m alat.uji_cepat`). Yang tidak kami klaim: bahwa tidak ada kebocoran yang tidak terpikir oleh kami.
- **"Ini kode kalian sendiri?"** Pola ide dari referensi sesuai instruksi "tiru lalu modifikasi"; kodenya ditulis ulang untuk masalah yang berbeda (lihat `dokumen/PERBEDAAN_DENGAN_REFERENSI.md`). Bagian yang kami jelaskan di atas bisa kami tunjukkan barisnya di kode.
