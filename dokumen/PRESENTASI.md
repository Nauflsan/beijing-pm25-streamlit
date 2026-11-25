# PRESENTASI: cara menjelaskan proyek di depan kelas

Dokumen ini panduan bicara: urutan halaman yang dibuka, apa yang diucapkan, cara membaca grafik, dan jawaban pertanyaan sulit.
Angka di dalamnya diisi otomatis dari `artifacts/hasil.json` oleh `python -m alat.perbarui_panduan`. Nama model di kalimat naskah
juga ikut otomatis, tetapi **baca ulang naskah setelah training ulang** karena urutan model bisa berubah.

---

## 0. Pesan utama (hafalkan tiga ini)

1. **Kami memprediksi PM2.5 per jam di Beijing** dengan lima model regresi, dalam dua mode: Mode B (memakai riwayat PM2.5 jam-jam sebelumnya) dan Mode A (hanya cuaca dan waktu).
2. **Kami menguji dengan jujur.** Tebakan "sama seperti jam lalu" (persistence) sudah R2 <!--ANGKA:b_persistence_1jam_r2-->0,944<!--/ANGKA-->, jadi yang kami laporkan adalah seberapa jauh model mengalahkannya: RMSE terbaik hanya <!--ANGKA:terbaik_uji_b_skill-->7,3<!--/ANGKA-->% lebih rendah.
3. **Hasilnya sederhana tapi bisa dipertanggungjawabkan.** Mode B bisa dipakai sebagai model utama; Mode A menunjukkan batas apa yang bisa dijelaskan cuaca saja.

**Peran dua mode.** Mode B = model utama kalau ada riwayat 24 jam terakhir. Mode A = pembanding dan cadangan kalau riwayat tidak ada.

---

## 1. Sebelum maju (checklist)

- [ ] Aplikasi sudah terbuka (lokal `streamlit run app.py` atau tautan deploy) dan sudah dicoba satu kali.
- [ ] Halaman yang akan dibuka sudah ditandai urutannya (lihat bagian 2). Siapkan cadangan: screenshot semua halaman di `bahan_laporan\`.
- [ ] `artifacts/hasil.json` dan `artifacts/models/` ada (kalau tidak, halaman menampilkan pesan "jalankan latih_semua_model.py dulu").
- [ ] Siapkan PANDUAN_HALAMAN.md dan KAMUS_FUNGSI.md di tab terpisah untuk menjawab "kodenya mana?".
- [ ] Latih kalimat 2 detik untuk tiap bagian di bawah, tidak perlu menghafal angka (semuanya tertulis di layar).

---

## 2. Urutan presentasi (sekitar 10 menit)

### Bagian 1. Masalah dan data (1,5 menit): halaman Beranda, Tentang Dataset
**Ucapkan:** "Kami memprediksi PM2.5 per jam di Beijing. Datanya <!--ANGKA:n_baris-->43.824<!--/ANGKA--> jam dari 2010 sampai 2014 di satu stasiun, 13 kolom. Hanya pm2.5 yang punya data kosong, <!--ANGKA:persen_kosong-->4,72<!--/ANGKA-->%."
**Tunjukkan:** kartu KPI Beranda; tab Kamus 13 kolom.
**Cara baca:** kartu dengan label berwarna kecil (titik dan nama kategori) = kategori kualitas udara dari rata-rata nilai.

### Bagian 2. Dari EDA ke keputusan (2 menit): EDA Umum, Preprocessing tab "Temuan EDA ke keputusan"
**Ucapkan:** "Sebaran PM2.5 miring ke kanan (skewness <!--ANGKA:skew-->1,80<!--/ANGKA-->), korelasi dengan cuaca lemah, tetapi sangat mirip dengan jam sebelumnya. Dari tiga temuan ini kami mengambil keputusan: dua mode fitur, baseline persistence, dan split berdasarkan waktu."
**Tunjukkan:** histogram (toggle skala log), heatmap korelasi, lalu tabel Temuan EDA ke keputusan (ada kolom kode file dan barisnya).
**Cara baca histogram:** batang tinggi di kiri = kebanyakan jam bernilai rendah-sedang; ekor panjang di kanan = sedikit jam sangat tinggi yang menarik rata-rata naik.
**Cara baca heatmap:** warna biru/merah = arah hubungan, makin pekat makin kuat; angka dekat 0 = lemah.

### Bagian 3. Fitur dan split waktu (1,5 menit): Preprocessing tab "Kolom ke fitur" dan "Split waktu"
**Ucapkan:** "Dari <!--ANGKA:n_kolom_csv-->13<!--/ANGKA--> kolom jadi <!--ANGKA:n_fitur_a-->11<!--/ANGKA--> fitur di Mode A dan <!--ANGKA:n_fitur_b-->17<!--/ANGKA--> di Mode B; setelah one-hot menjadi <!--ANGKA:n_enkode_a-->14<!--/ANGKA--> dan <!--ANGKA:n_enkode_b-->20<!--/ANGKA--> kolom. Kami membagi data berdasarkan waktu: latih 2010-2013, uji 2014, supaya model diuji pada masa depan yang belum pernah dilihat."
**Tunjukkan:** tabel kolom ke fitur, lalu gambar lipatan validasi silang.
**Cara baca gambar lipatan:** biru = data latih (selalu di masa lalu), oranye = validasi, hijau = uji akhir.

### Bagian 4. Lima model dan PSO (1,5 menit): Modelling dan Tuning
**Ucapkan:** "Kami melatih lima model: Ridge, Decision Tree, Random Forest, HistGradientBoosting, dan Random Forest yang dituning PSO. Menariknya, tuning PSO menurunkan error di sampel tempat ia mencari (<!--ANGKA:pso_fit_pembanding-->25,60<!--/ANGKA--> ke <!--ANGKA:pso_fit_terbaik-->25,32<!--/ANGKA-->), tetapi di data uji tidak membaik (<!--ANGKA:m_rf_B_rmse-->20,52<!--/ANGKA--> vs <!--ANGKA:m_rf_pso_B_rmse-->20,77<!--/ANGKA-->). Kami melaporkannya apa adanya."
**Tunjukkan:** tab "RF vs RF + PSO": kurva konvergensi dan tabel tiga tingkat.
**Cara baca kurva konvergensi:** turun lalu mendatar = pencarian sudah berhenti membaik.

### Bagian 5. Evaluasi (1 menit): Evaluasi dan Interpretasi
**Ucapkan:** "Di Mode B model terbaik menurut data uji adalah <!--ANGKA:terbaik_uji_b_nama-->Random Forest<!--/ANGKA--> (RMSE <!--ANGKA:terbaik_uji_b_rmse-->20,52<!--/ANGKA-->, MAE <!--ANGKA:terbaik_uji_b_mae-->11,38<!--/ANGKA-->). Menurut validasi silang yang terbaik <!--ANGKA:pem_b_nama-->Ridge Regression<!--/ANGKA-->; kami memilih lewat validasi silang supaya tidak mengintip data uji. Kolom paling berpengaruh <!--ANGKA:imp_top_b-->pm25_lag1<!--/ANGKA-->."
**Tunjukkan:** Mode A dan Mode B bergantian; tab Aktual vs prediksi; tab Interpretasi.
**Cara baca aktual vs prediksi:** titik dekat garis putus = prediksi mendekati kenyataan; titik jauh di bawah garis = model meremehkan.

### Bagian 6. Uji Kejujuran (2 menit, bagian paling penting): Uji Kejujuran Model
**Ucapkan:** "Di sini kami menguji apakah modelnya benar-benar bagus. Pertama, persistence tanpa belajar sudah R2 <!--ANGKA:b_persistence_1jam_r2-->0,944<!--/ANGKA--> dan model hanya <!--ANGKA:terbaik_uji_b_skill-->7,3<!--/ANGKA-->% lebih baik; di validasi silang hanya <!--ANGKA:n_menang_cv_b-->3<!--/ANGKA--> dari <!--ANGKA:n_model_b-->5<!--/ANGKA--> model yang mengalahkannya. Kedua, R2 semua model hampir sama jadi tidak membedakan. Ketiga, di split acak Mode A hasilnya tampak lebih bagus (R2 <!--ANGKA:uj_acak_r2_a-->0,596<!--/ANGKA--> vs <!--ANGKA:uj_waktu_r2_a-->0,462<!--/ANGKA-->), tetapi di Mode B tidak, jadi kami tidak mengklaim split acak selalu lebih tinggi."
**Tunjukkan:** kotak ringkasan di atas, tab R2 vs MAE vs RMSE (batang R2 hampir sama panjang), tab Saat polusi parah.
**Cara baca batang R2 vs RMSE:** di R2 semua batang hampir sama panjang (tidak membedakan); di RMSE batang model terlihat lebih pendek dari persistence (itu keunggulan sebenarnya).
**Cara baca polusi parah:** batang oranye (parah) lebih tinggi dari biru (normal) = model lebih sering meleset saat polusi tinggi; bias negatif = meremehkan.

### Bagian 7. Demo prediksi dan penutup (1,5 menit): Prediksi Satu Input, Kesimpulan
**Ucapkan:** "Ini contoh prediksi satu jam dari data asli saat polusi paling parah; gauge menunjukkan nilai dan kategori, ada saran kesehatan dan rentang ketidakpastian yang kami hitung dari kuantil residual."
**Tunjukkan:** halaman Prediksi Satu Input, tombol "Contoh: polusi paling parah", lalu bandingkan semua model. Tutup dengan halaman Kesimpulan (keterbatasan dan saran).
**Cara baca gauge:** pita warna latar = kategori udara; bar yang berwarna = kategori hasil prediksi; angka di tengah = prediksi dalam ug/m3.
**Cara baca rentang 90%:** perkiraan kasar dari galat model di data uji; bukan jaminan.

---

## 3. Cara baca grafik dan tabel (contekan cepat)

| Grafik | Cara baca | Apa yang ditunjukkan di sini |
|---|---|---|
| Histogram pm2.5 | tinggi batang = jumlah jam | sebaran miring kanan |
| Heatmap korelasi | merah/biru = arah, pekat = kuat | cuaca lemah terhadap pm2.5 |
| Scree plot PCA | batang = varians tiap komponen, garis = kumulatif | kolom berkurang tetapi akurasi turun |
| Bar RMSE + garis putus | makin pendek makin baik; garis = persistence | model hanya sedikit di bawah garis |
| CV per lipatan | tiap kelompok batang = satu lipatan waktu | hasil antar lipatan berbeda cukup jauh |
| Aktual vs prediksi | dekat garis putus = tepat | model menarik prediksi ke tengah saat ekstrem |
| Residual | simetris di sekitar 0 = baik; melebar ke kanan = galat besar saat prediksi tinggi | dasar interval ketidakpastian |
| Error per bulan/kategori | tinggi batang = error | polusi tinggi lebih sulit |
| Permutation importance | panjang batang = seberapa naik RMSE saat kolom diacak | riwayat 1 jam lalu paling dominan |
| Partial dependence | kurva = prediksi saat satu fitur digeser | Ridge: garis lurus |
| Gauge | pita = kategori, bar = prediksi | kategori dan nilai prediksi |
| What-if | kurva respons model, diamond = skenario awal | pengaruh satu variabel pada prediksi |

---

## 4. Pertanyaan sulit dan jawaban singkat

1. **"Jadi modelnya jelek?"** Tidak jelek, tetapi keunggulannya tipis, dan kami menunjukkannya. Mode B RMSE <!--ANGKA:terbaik_uji_b_rmse-->20,52<!--/ANGKA--> vs persistence <!--ANGKA:b_persistence_1jam_rmse-->22,14<!--/ANGKA-->. Sebabnya PM2.5 per jam sangat mirip dengan jam lalu sehingga tebakan sederhana sudah kuat.
2. **"Kenapa Mode A jauh dari data aktual?"** Mode A sengaja tidak boleh melihat riwayat PM2.5; ia mengukur seberapa jauh cuaca dan waktu saja menjelaskan polusi (R2 <!--ANGKA:pem_a_r2-->0,462<!--/ANGKA-->). Ia cenderung meremehkan lonjakan (bias <!--ANGKA:pem_a_parah_bias-->-74,2<!--/ANGKA--> ug/m3 saat polusi parah).
3. **"Kenapa R2 0,95 tapi katanya tidak bagus?"** Persistence tanpa belajar sudah R2 <!--ANGKA:b_persistence_1jam_r2-->0,944<!--/ANGKA-->; R2 tidak membedakan. Yang dilaporkan: MAE, RMSE, selisih terhadap baseline, dan performa saat polusi parah.
4. **"Kenapa model terbaik dipilih lewat validasi silang, bukan data uji?"** Supaya pemilihan tidak mengintip data uji. Menurut validasi silang yang terbaik Mode B <!--ANGKA:pem_b_nama-->Ridge Regression<!--/ANGKA-->, sedangkan di data uji <!--ANGKA:terbaik_uji_b_nama-->Random Forest<!--/ANGKA--> sedikit lebih baik; selisihnya dekat sehingga urutan mudah bergeser.
5. **"PSO-nya berguna?"** Di sampel pencarian ya (<!--ANGKA:pso_fit_pembanding-->25,60<!--/ANGKA--> ke <!--ANGKA:pso_fit_terbaik-->25,32<!--/ANGKA-->), di data uji tidak. Dugaan: sedikit menyesuaikan diri dengan sampel (belum diuji). PSO sengaja diperkecil (<!--ANGKA:pso_partikel-->6<!--/ANGKA--> partikel x <!--ANGKA:pso_iterasi-->5<!--/ANGKA--> iterasi) agar muat di laptop i3.
6. **"Bagaimana mencegah data bocor?"** Split berdasarkan waktu; imputer/scaler ada di dalam Pipeline (hanya belajar dari data latih); lag dan rata-rata bergulir hanya memakai jam sebelumnya (digeser dulu); pengisian data kosong memakai forward fill (bukan interpolasi yang mengintip masa depan). Ada tes otomatis di `alat/uji_cepat.py` yang mengubah nilai masa depan dan memastikan fitur tidak berubah.
7. **"Kenapa tidak pakai deep learning (LSTM)?"** Dibatasi laptop CPU i3 dan waktu; lima model klasik lebih mudah dijelaskan dan dilatih dalam sekitar <!--ANGKA:total_waktu_detik-->59<!--/ANGKA--> detik ditambah PSO <!--ANGKA:pso_detik-->73<!--/ANGKA--> detik. Deep learning masuk saran pengembangan, belum dicoba.
8. **"Apakah bisa dipakai real-time?"** Belum. Aplikasi tidak mengambil data terbaru; pengguna memasukkan cuaca dan riwayatnya sendiri. Ini tercantum di keterbatasan.
9. **"Kenapa PCA tidak dipakai?"** Dicoba dengan Ridge: mengurangi kolom Mode B dari <!--ANGKA:pca_awal_b-->20<!--/ANGKA--> ke <!--ANGKA:pca_k95_b-->12<!--/ANGKA--> tetapi RMSE naik dari <!--ANGKA:pca_rmse_tanpa_b-->21,30<!--/ANGKA--> ke <!--ANGKA:pca_rmse95_b-->29,19<!--/ANGKA-->.
10. **"Buktinya angka-angka ini nyata?"** Semua angka dibaca dari `artifacts/hasil.json` yang dibuat skrip latih; eksperimen bisa dihitung ulang dengan `python -m evaluasi.bukti_eksperimen` (hasilnya harus COCOK), dan kode tiap hasil bisa dibuka lewat expander "Kode" di halaman.
11. **"Kenapa ambang kategori udara memakai versi 2024?"** Karena itu revisi EPA yang berlaku sejak 6 Mei 2024 (sumber tercantum di Tentang Dataset dan Kesimpulan). Ambang aslinya untuk rata-rata 24 jam, dipakai di sini pada nilai per jam sebagai pendekatan; versi 2012 bisa dipilih di `konfigurasi.py`.

---

## 5. Kalau ditanya "kodenya mana?"

| Pertanyaan | Buka | File |
|---|---|---|
| Bagaimana isi data kosong? | Preprocessing tab Data kosong, expander Kode | `preprocessing/fitur_waktu.py` fungsi `isi_pm` |
| Bagaimana lag/rolling dihitung tanpa bocor? | Preprocessing tab Kolom ke fitur | `preprocessing/fitur_waktu.py` fungsi `hitung_fitur_pm`, `siapkan_data` |
| Bagaimana model dilatih? | Modelling tab Lima model | `model/latih_semua_model.py` fungsi `latih_dan_simpan` |
| Bagaimana PSO bekerja? | Modelling tab RF vs RF + PSO | `model/pso_random_forest.py` fungsi `jalankan_pso` |
| Bagaimana PCA dijalankan? | PCA tab Bukti dan kode | `preprocessing/eksperimen_pca.py` fungsi `_eksp_pca` |
| Bagaimana metrik dihitung? | Evaluasi tab Metrik | `evaluasi/evaluasi_regresi.py` fungsi `hitung_metrik` |
| Bagaimana uji kejujuran dilakukan? | Uji Kejujuran tab Split acak vs waktu | `model/latih_semua_model.py` fungsi `uji_kejujuran` |
| Bagaimana satu prediksi dibuat? | Prediksi Satu Input, bagian bawah | `model/prediksi.py` fungsi `prediksi_satu` |
| Daftar semua fungsi? | file `dokumen/KAMUS_FUNGSI.md` | dibuat otomatis dari kode |

---

## 6. Jangan sampai terucap

- "Modelnya akurat karena R2 0,95." (persistence juga <!--ANGKA:b_persistence_1jam_r2-->0,944<!--/ANGKA-->)
- "PSO meningkatkan hasil." (di data uji tidak)
- "Split acak selalu lebih bagus." (di Mode B tidak)
- "Model ini bisa dipakai memutuskan kesehatan." (hanya bahan belajar)
- Angka yang tidak ada di layar atau di `hasil.json`.
