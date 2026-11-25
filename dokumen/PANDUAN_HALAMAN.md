# PANDUAN HALAMAN

Panduan menjelaskan tiap halaman ke dosen: tujuan, data yang dipakai, fungsi Streamlit kunci, cara menjelaskan dalam
2-3 kalimat, dan tiga pertanyaan yang mungkin ditanya beserta jawabannya.

**Catatan penting: angka di dokumen ini diisi otomatis.** Angka yang dibungkus penanda `<!--ANGKA:...-->` dan blok
`<!--BLOK:...-->` ditulis ulang oleh `python -m alat.perbarui_panduan` dari `artifacts/hasil.json` dan CSV. Jalankan perintah itu
setiap selesai training ulang supaya dokumen selalu sama dengan hasil. Jangan edit angka di antara penanda secara manual.

Status: Halaman 1-11 dan 14 selesai. Halaman 12 dan 13 (tambahan) menyusul.

---

## Halaman 1. Beranda
**File:** `halaman/01_beranda.py`

**Tujuan.** Ringkasan satu layar: ukuran data, seberapa buruk polusinya, hasil model utama dibanding baseline, alur kerja, dan identitas kelompok.

**Data.** CSV (kartu KPI atas, dihitung langsung) dan `artifacts/hasil.json` (kartu KPI model dan ringkasan temuan).

**Fungsi Streamlit kunci.** `st.columns` untuk deretan kartu, `tema.kartu_kpi` (kartu HTML yang warnanya mengikuti kategori udara), `ua.kalimat_temuan` (kalimat dibuat dari hasil.json), `st.cache_data` pada pemuatan data dan hasil.

**Cara menjelaskan.** "Beranda merangkum proyek: datanya <!--ANGKA:n_baris-->43.824<!--/ANGKA--> jam pengamatan PM2.5 di Beijing, lalu hasil model utama dibandingkan dengan tebakan paling sederhana (baseline persistence). Semua angka model dibaca otomatis dari hasil training, bukan diketik."

**Pertanyaan yang mungkin ditanya**
1. *Kenapa header Beranda berwarna begitu?* Warna header mengikuti kategori kualitas udara dari rata-rata PM2.5 seluruh data (<!--ANGKA:mean-->98,6<!--/ANGKA--> ug/m3), yang jatuh di kategori <!--ANGKA:kategori_rata-->Tidak Sehat<!--/ANGKA-->. Itu sebabnya warnanya mengikuti palet AQI.
2. *Ringkasan temuan itu ditulis tangan?* Tidak. Kalimatnya dibangun oleh fungsi `kalimat_temuan` dari hasil.json, termasuk arah perbandingan (menang atau kalah dari baseline) yang ditentukan oleh angkanya. Kalau hasil training berubah, kalimatnya ikut berubah.
3. *Kenapa ada baseline persistence di Beranda?* Karena PM2.5 per jam sangat mirip dengan jam sebelumnya, tebakan "sama seperti jam lalu" sudah cukup kuat. Model baru dianggap berguna kalau mengalahkannya; itu diuji jujur di halaman Uji Kejujuran Model.

---

## Halaman 2. Tentang Dataset
**File:** `halaman/02_tentang_dataset.py`

**Tujuan.** Memperkenalkan 13 kolom, rentang waktu, kualitas data, data kosong, dan istilah penting (glosarium).

**Data.** CSV, lewat `utilitas_data.ringkasan_dataset`.

**Fungsi Streamlit kunci.** `st.tabs` (empat tab), `st.table` untuk kamus kolom, `st.altair_chart` untuk grafik data kosong. Altair memakai salinan kolom `pm25` karena nama `pm2.5` yang berisi titik dianggap properti bersarang oleh Vega-Lite (grafik jadi kosong).

**Cara menjelaskan.** "Datanya per jam dari <!--ANGKA:tahun_awal-->2010<!--/ANGKA--> sampai <!--ANGKA:tahun_akhir-->2014<!--/ANGKA--> di satu stasiun. Hanya kolom pm2.5 yang punya data kosong, sebanyak <!--ANGKA:n_kosong-->2.067<!--/ANGKA--> jam (<!--ANGKA:persen_kosong-->4,72<!--/ANGKA-->%), dan baris-baris itu tidak dipakai sebagai target."

**Pertanyaan yang mungkin ditanya**
1. *Kenapa jam yang kosong tidak diisi rata-rata saja?* Baris yang pm2.5-nya kosong tidak dipakai sebagai target supaya model tidak belajar dari angka karangan. Untuk fitur riwayat (lag) nilai kosong diisi nilai terakhir yang diketahui (forward fill) karena hanya memakai masa lalu. Pengisian memakai median dan interpolasi dibandingkan di halaman Preprocessing; interpolasi memakai masa depan sehingga dianggap bocor.
2. *Datanya satu stasiun, apakah mewakili seluruh Beijing?* Tidak, dan ini dicatat sebagai keterbatasan. Model hanya berlaku untuk titik pengukuran itu pada tahun <!--ANGKA:tahun_awal-->2010<!--/ANGKA-->-<!--ANGKA:tahun_akhir-->2014<!--/ANGKA-->. Koordinat yang ditampilkan perkiraan karena dataset tidak punya kolom koordinat.
3. *Apa arti nilai `cv` pada arah angin?* Di dokumentasi dataset asli kategori ini berarti angin tenang atau berubah-ubah. Cek ulang ke sumber dataset yang dipakai kelompok sebelum menyebutnya di presentasi.

---

## Halaman 3. EDA Umum
**File:** `halaman/03_eda_umum.py`

**Tujuan.** Melihat sebaran PM2.5, nilai ekstrem, dan hubungan dengan variabel cuaca.

**Data.** CSV; semua angka dan kalimat interpretasi dihitung dari data.

**Fungsi Streamlit kunci.** `st.tabs`, `st.toggle` (skala log), `st.slider` (batas tampilan), `st.radio` (Pearson atau Spearman), `st.plotly_chart(..., width="stretch")`, `st.cache_data` untuk matriks korelasi.

**Cara menjelaskan.** "Sebaran PM2.5 miring ke kanan (skewness <!--ANGKA:skew-->1,80<!--/ANGKA-->): rata-rata <!--ANGKA:mean-->98,6<!--/ANGKA--> lebih besar dari median <!--ANGKA:median-->72,0<!--/ANGKA-->. Korelasi linear dengan cuaca lemah, jadi cuaca saja diperkirakan belum cukup; itu yang kami uji dengan dua mode fitur."

**Pertanyaan yang mungkin ditanya**
1. *Skewness <!--ANGKA:skew-->1,80<!--/ANGKA--> artinya apa dan kenapa penting?* Ekor sebaran panjang ke kanan: kebanyakan jam bernilai rendah-sedang, sedikit jam sangat tinggi. Metrik seperti RMSE sangat terpengaruh lonjakan, karena itu proyek juga memakai MAE, MedAE, dan evaluasi khusus saat polusi parah.
2. *Ada <!--ANGKA:n_outlier_iqr-->1.773<!--/ANGKA--> outlier menurut IQR, kenapa tidak dibuang?* Titik-titik itu ada di ekor kanan sebaran dan kemungkinan besar kejadian polusi nyata, bukan salah ukur (dugaan, belum diverifikasi ke sumber data). Membuangnya membuat model tidak pernah belajar polusi parah, padahal itu bagian paling penting.
3. *Korelasi cuaca lemah, apakah cuaca tidak berguna?* Korelasi Pearson hanya mengukur hubungan lurus. Hubungan non-linear dan interaksi antar variabel tidak terlihat di sana, dan model berbasis pohon bisa menangkapnya. Kegunaan cuaca diuji lewat Mode A dan permutation importance.

---

## Halaman 4. Preprocessing
**File:** `halaman/04_preprocessing.py`, **logika tabel kolom ke fitur:** `preprocessing/peta_fitur.py`, **peta kode:** `evaluasi/bukti_kode.py`

**Tujuan.** Menjelaskan bagaimana data mentah menjadi fitur model dan memberi bukti untuk tiap keputusan. Enam tab: Kolom ke fitur, Data kosong, Outlier, Log target, Split waktu dan scaling, Temuan EDA ke keputusan.

**Data.** `artifacts/hasil.json`: `data`, `fitur`, `model.*.n_fitur_setelah_enkode`, `model.*.cv`, `model.*.polusi_parah`, `eksperimen.isi_kosong`, `eksperimen.log_target`, `eksperimen.skala`. Angka data dari CSV.

**Fungsi Streamlit kunci.** `st.tabs`, `st.table` (tabel panjang yang membungkus teks), `st.plotly_chart`, `tampilkan_kode` (expander yang menampilkan KODE ASLI fungsi lewat modul `ast`, lengkap dengan nomor baris). Kalimat kesimpulan dibangun dari angka sehingga arahnya ditentukan data.

**Cara menjelaskan.** "Dari <!--ANGKA:n_kolom_csv-->13<!--/ANGKA--> kolom CSV, <!--ANGKA:n_dibuang-->3<!--/ANGKA--> tidak dipakai sebagai fitur, satu jadi target, sisanya jadi <!--ANGKA:n_fitur_a-->11<!--/ANGKA--> fitur di Mode A dan <!--ANGKA:n_fitur_b-->17<!--/ANGKA--> di Mode B; setelah arah angin di-one-hot menjadi <!--ANGKA:n_enkode_a-->14<!--/ANGKA--> dan <!--ANGKA:n_enkode_b-->20<!--/ANGKA--> kolom. Tiap keputusan (isi data kosong, outlier, log, split) kami uji dengan angka dan kodenya bisa dilihat di halaman."

**Pertanyaan yang mungkin ditanya**
1. *Kenapa tidak memakai interpolasi padahal RMSE-nya paling kecil?* Interpolasi memberi RMSE <!--ANGKA:isi_interp-->21,17<!--/ANGKA--> berbanding <!--ANGKA:isi_ffill-->21,30<!--/ANGKA--> untuk forward fill, tetapi interpolasi menghitung nilai kosong dari titik sebelum dan SESUDAH jam itu, jadi model ikut mengintip masa depan. Di dunia nyata nilai masa depan tidak tersedia, jadi yang adil adalah forward fill. Median data latih memberi <!--ANGKA:isi_median-->21,89<!--/ANGKA-->.
2. *Kenapa outlier tidak dibuang?* Karena polusi parah adalah bagian yang paling penting dan paling sulit: saat polusi parah error model terbaik Mode B sekitar <!--ANGKA:parah_b_kali-->2,2<!--/ANGKA--> kali error saat normal, dan Mode A sekitar <!--ANGKA:parah_a_kali-->2,7<!--/ANGKA--> kali. Kalau dibuang, kita tidak bisa lagi menilai model pada kejadian yang paling berbahaya bagi kesehatan.
3. *Kenapa tidak memakai log pada target?* Dicoba dan dievaluasi di skala asli: RMSE Mode B menjadi <!--ANGKA:log_b_log-->174,66<!--/ANGKA--> berbanding <!--ANGKA:log_b_asli-->21,30<!--/ANGKA--> tanpa log, dan Mode A <!--ANGKA:log_a_log-->75,79<!--/ANGKA--> berbanding <!--ANGKA:log_a_asli-->71,11<!--/ANGKA-->. Jadi log memperburuk dan tidak dipakai. Dugaan penyebabnya pengembalian ke skala asli (expm1) membesarkan selisih; ini belum diuji lebih lanjut.
4. *Kenapa split berdasarkan waktu, bukan acak?* Data berurutan waktu dan PM2.5 sangat mirip dari jam ke jam. Split waktu melatih di masa lalu (<!--ANGKA:n_latih-->33.072<!--/ANGKA--> baris) dan menguji di tahun yang tidak pernah dilihat (<!--ANGKA:n_uji-->8.661<!--/ANGKA--> baris), seperti kondisi pemakaian nyata. Perbandingan dengan split acak ada di halaman Uji Kejujuran Model.
5. *Apakah scaling berpengaruh?* Untuk Ridge, RMSE dengan skala <!--ANGKA:skala_b_dengan-->21,298<!--/ANGKA--> dan tanpa skala <!--ANGKA:skala_b_tanpa-->21,307<!--/ANGKA--> (Mode B): hampir sama. Scaler tetap dipasang di dalam Pipeline agar hanya belajar dari data latih; model pohon tidak memakainya karena tidak peka skala.

### Tabel: Dari <!--ANGKA:n_kolom_csv-->13<!--/ANGKA--> kolom CSV ke fitur model

<!--BLOK:tabel_kolom_ke_fitur-->
| Kolom asal | Diapakan | Alasan | Mode A | Mode B |
|---|---|---|---|---|
| No | Dibuang | Nomor urut baris. Tidak membawa informasi cuaca atau waktu; kalau dipakai, model hanya menghafal urutan. | tidak | tidak |
| year | Dibuang dari fitur (dipakai untuk membentuk waktu dan membagi data) | Data uji (tahun >= 2014) berada di luar rentang tahun data latih, jadi angka tahun tidak bisa dipelajari dengan benar. Tahun dipakai untuk split waktu. | tidak | tidak |
| month | Diubah sin-cos (bulan_sin, bulan_cos) | Bulan 12 dan bulan 1 sebenarnya bertetangga. Angka biasa 1-12 membuat model mengira keduanya jauh; pasangan sin-cos membentuk 'lingkaran' bulan. | 2 fitur: bulan_sin, bulan_cos | 2 fitur: bulan_sin, bulan_cos |
| day | Dibuang dari fitur (dipakai untuk membentuk waktu) | Tanggal dalam bulan tidak punya pola yang masuk akal terhadap polusi; pola musim sudah dibawa bulan dan pola harian dibawa jam. Pengaruhnya belum diuji ablasi. | tidak | tidak |
| hour | Diubah sin-cos (jam_sin, jam_cos) | Jam 23 dan jam 0 bertetangga. Sin-cos membuat jam berputar seperti jam dinding. | 2 fitur: jam_sin, jam_cos | 2 fitur: jam_sin, jam_cos |
| pm2.5 | Target (Y). Mode B: dibuat lag 1, 2, 3, 24 jam dan rata-rata bergulir 3, 24 jam | Mode A tidak boleh memakai PM2.5 sebagai input. Mode B memakai masa lalunya, digeser 1 jam dulu sebelum dirata-rata supaya jam yang diprediksi tidak ikut mengintip. | tidak | 6 fitur: pm25_lag1, pm25_lag2, pm25_lag3, pm25_lag24, pm25_rata3, pm25_rata24 |
| DEWP | Dipakai langsung | Titik embun (kelembapan udara). Sudah numerik; Ridge distandarkan, model pohon tidak butuh. | 1 fitur: DEWP | 1 fitur: DEWP |
| TEMP | Dipakai langsung | Suhu. Sudah numerik dan bermakna. | 1 fitur: TEMP | 1 fitur: TEMP |
| PRES | Dipakai langsung | Tekanan udara. Sudah numerik dan bermakna. | 1 fitur: PRES | 1 fitur: PRES |
| cbwd | One-hot (NE, NW, SE, cv) | Arah angin adalah kategori tanpa urutan. One-hot mencegah model menganggap NE < NW < SE < cv. | 1 fitur: cbwd | 1 fitur: cbwd |
| Iws | Dipakai langsung | Kecepatan angin kumulatif. Sebaran miring ke kanan, tetapi tidak ditransformasi: model pohon tidak terpengaruh dan Ridge distandarkan. | 1 fitur: Iws | 1 fitur: Iws |
| Is | Dipakai langsung | Akumulasi jam salju. Hampir selalu 0, tetap dipakai karena nilai tidak nolnya mungkin bermakna (lihat ablasi 'tanpa cuaca' di halaman Feature Engineering). | 1 fitur: Is | 1 fitur: Is |
| Ir | Dipakai langsung | Akumulasi jam hujan. Hampir selalu 0, tetap dipakai dengan alasan yang sama dengan Is. | 1 fitur: Ir | 1 fitur: Ir |
| TOTAL (13 kolom CSV) | - | Jumlah fitur sebelum one-hot lalu sesudah one-hot (arah angin menjadi beberapa kolom). | 11 fitur, jadi 14 kolom setelah one-hot | 17 fitur, jadi 20 kolom setelah one-hot |
<!--/BLOK-->

### Pertanyaan antisipasi dosen tentang jumlah fitur

<!--BLOK:tanya_jawab_fitur-->
**1. Datanya 13 kolom, kok fitur Mode A cuma 11? Ke mana sisanya?**

13 kolom itu dibagi tiga peran. (1) Target: pm2.5, ini yang diprediksi sehingga tidak boleh jadi input di Mode A. (2) Tidak dipakai sebagai fitur (3 kolom): No, year, day. No hanya nomor urut, year hanya dipakai membagi data latih dan uji (tahun uji di luar rentang latih), day hanya dipakai membentuk waktu. (3) Sisanya jadi fitur: 6 kolom cuaca dipakai langsung, month dan hour masing-masing jadi sin dan cos (4 fitur), dan arah angin (1 fitur). Totalnya 6 + 4 + 1 = 11 fitur.

**2. Kenapa Mode B punya 17 fitur dan dari mana tambahan 6 fitur itu?**

Mode B = Mode A ditambah riwayat PM2.5: 4 fitur lag (pm25_lag1, pm25_lag2, pm25_lag3, pm25_lag24) dan 2 fitur rata-rata bergulir (pm25_rata3, pm25_rata24). 11 + 4 + 2 = 17. Riwayat ini hanya memakai jam-jam SEBELUM jam yang diprediksi (digeser 1 jam dulu), jadi tidak mengintip masa depan. Mode A sengaja dipertahankan sebagai versi tanpa riwayat supaya terlihat seberapa besar bantuan riwayat PM2.5.

**3. Kenapa 11 fitur menjadi 14 kolom dan 17 menjadi 20? Bukankah fiturnya sama?**

Bedanya karena one-hot encoding arah angin. Arah angin satu fitur dengan 4 kategori (NE, NW, SE, cv), model butuh angka, jadi satu kolom itu dipecah menjadi 4 kolom 0/1. Satu fitur menjadi 4 kolom, bertambah 3: 11 + 3 = 14 (Mode A) dan 17 + 3 = 20 (Mode B). Jumlah 'fitur' dihitung sebelum one-hot, jumlah 'kolom' sesudahnya.

**4. Kenapa jam dan bulan dibuat dua kolom (sin dan cos), bukan satu angka saja?**

Jam dan bulan itu melingkar: jam 23 bertetangga dengan jam 0, bulan 12 dengan bulan 1. Kalau dipakai sebagai angka biasa, model mengira 23 dan 0 berjauhan. Satu sudut di lingkaran butuh dua koordinat; kalau cuma sin, dua waktu berbeda bisa punya nilai sama (misalnya jam 3 dan jam 9), jadi cos diperlukan untuk membedakannya. Itu sebabnya month dan hour masing-masing menghasilkan dua fitur.

**5. Apakah 20 kolom tidak terlalu banyak? Perlu PCA atau pengurangan fitur?**

Relatif terhadap data, tidak banyak: ada 33.072 baris latih untuk 20 kolom, sekitar 1.654 baris per kolom. Risiko overfitting dikendalikan dengan validasi silang berurutan waktu dan evaluasi di tahun yang tidak pernah dilihat saat latih; model pohon juga dibatasi kedalaman dan jumlah sampel daun. Fitur lag saling berkorelasi tinggi, itu wajar dan tidak merusak model pohon. Di eksperimen Ridge Mode B, PCA yang mempertahankan 95% varians memakai 12 dari 20 komponen dengan RMSE 29,19, dibanding 21,30 tanpa PCA (data uji). Perbandingan lengkap dengan dan tanpa PCA ada di halaman PCA.
<!--/BLOK-->

---

## Halaman 5. PCA
**File:** `halaman/05_pca.py`

**Tujuan.** Menguji apakah mengurangi jumlah kolom lewat PCA membantu model, dengan SelectKBest sebagai pembanding. PCA hanya EKSPERIMEN (Ridge), bukan bagian model final.

**Data.** `artifacts/hasil.json` -> `eksperimen` -> `pca` -> `A`/`B` (kolom awal, scree, kumulatif, varian 80/90/95/99%, SelectKBest, tanpa PCA).

**Fungsi Streamlit kunci.** `st.radio` (pilih mode), `st.tabs` (Scree plot, Dengan vs tanpa PCA, Bukti dan kode), `grafik.scree_plot`, `tampilkan_kode` (menampilkan kode asli `_eksp_pca`).

**Cara menjelaskan.** "PCA berhasil mengurangi kolom Mode B dari <!--ANGKA:pca_awal_b-->20<!--/ANGKA--> menjadi <!--ANGKA:pca_k95_b-->12<!--/ANGKA--> pada 95% varians, tetapi RMSE naik dari <!--ANGKA:pca_rmse_tanpa_b-->21,30<!--/ANGKA--> menjadi <!--ANGKA:pca_rmse95_b-->29,19<!--/ANGKA-->. Karena merugikan, model final tidak memakai PCA."

**Pertanyaan yang mungkin ditanya**
1. *Mana buktinya PCA mengurangi kolom, dan memang sudah di-train?* Datanya di `artifacts/hasil.json` -> `eksperimen` -> `pca`: Mode B dari <!--ANGKA:pca_awal_b-->20<!--/ANGKA--> kolom jadi <!--ANGKA:pca_k95_b-->12<!--/ANGKA--> komponen (95% varians), Mode A dari <!--ANGKA:pca_awal_a-->14<!--/ANGKA--> jadi <!--ANGKA:pca_k95_a-->10<!--/ANGKA-->. Kodenya `preprocessing/eksperimen_ringan.py` fungsi `_eksp_pca` (tampil di tab Bukti dan kode, lengkap dengan nomor baris), dipanggil dari `model/latih_semua_model.py`. Untuk membuktikan, jalankan `python -m evaluasi.bukti_eksperimen --bagian pca`: skrip menghitung ulang dari data dan membandingkannya dengan hasil.json angka demi angka (harus COCOK).
2. *Kenapa PCA tidak dipakai di model final padahal mengurangi kolom?* Karena akurasinya turun: Mode B RMSE <!--ANGKA:pca_rmse95_b-->29,19<!--/ANGKA--> dengan PCA 95% berbanding <!--ANGKA:pca_rmse_tanpa_b-->21,30<!--/ANGKA--> tanpa PCA (naik <!--ANGKA:pca_naik_b-->37,1<!--/ANGKA-->%); Mode A <!--ANGKA:pca_rmse95_a-->88,47<!--/ANGKA--> berbanding <!--ANGKA:pca_rmse_tanpa_a-->71,11<!--/ANGKA-->. Jumlah kolom hanya <!--ANGKA:pca_awal_b-->20<!--/ANGKA-->, jadi penghematan komputasinya kecil dibanding kerugian akurasinya.
3. *PCA dilatih untuk kelima model?* Tidak. PCA hanya dicoba dengan Ridge sebagai eksperimen pembanding. Kelima model final dilatih tanpa PCA (lihat `buat_pipeline` di `preprocessing/fitur_waktu.py`: hanya preprocessor dan estimator).
4. *Kenapa SelectKBest hampir tidak merugikan padahal PCA merugikan?* Di Mode B, memilih 15 dari 20 kolom memberi RMSE <!--ANGKA:kbest15_rmse_b-->21,41<!--/ANGKA-->, hampir sama dengan tanpa seleksi. Dugaan (belum diuji): PCA mengurutkan berdasarkan varians dan mencampur kolom, sehingga fitur terpenting (riwayat PM2.5) ikut tercampur; SelectKBest memilih kolom asli berdasarkan hubungannya dengan target.

---

## Halaman 6. Modelling dan Tuning
**File:** `halaman/06_modelling_tuning.py`

**Tujuan.** Memperkenalkan lima model dan alasan memilihnya, membandingkan Random Forest biasa dengan Random Forest + PSO (sebelum dan sesudah tuning), menunjukkan validasi silang berurutan waktu, serta waktu dan ukuran file.

**Data.** `artifacts/hasil.json`: `model.*` (parameter, cv, uji, waktu, ukuran), `baseline`, `pso`, `pemenang`.

**Fungsi Streamlit kunci.** `st.radio` (mode), `st.tabs`, `st.container(border=True)` (kartu model), `st.plotly_chart`, `tampilkan_kode` (kode asli `buat_estimator`, `latih_dan_simpan`, `jalankan_pso`, `cv_regresi`). Kesimpulan PSO dibangun dari angka di tiga tingkat (sampel PSO, validasi silang, data uji).

**Cara menjelaskan.** "Kami melatih lima model regresi dengan dan tanpa riwayat PM2.5. Di Mode B semua model hanya sedikit lebih baik dari baseline persistence (RMSE terbaik <!--ANGKA:m_rf_B_rmse-->20,52<!--/ANGKA--> berbanding <!--ANGKA:b_persistence_1jam_rmse-->22,14<!--/ANGKA-->). Tuning PSO menurunkan error di sampel tempat ia mencari, tetapi tidak membaik di data uji."

**Pertanyaan yang mungkin ditanya**
1. *Kenapa lima model ini?* Semuanya regresi (memprediksi angka), mewakili keluarga berbeda: linear (Ridge), satu pohon (Decision Tree), kumpulan pohon (Random Forest), boosting (HistGradientBoosting), dan Random Forest yang dituning PSO. Semuanya ringan untuk CPU laptop: seluruh training selesai dalam sekitar <!--ANGKA:total_waktu_detik-->59<!--/ANGKA--> detik ditambah PSO <!--ANGKA:pso_detik-->73<!--/ANGKA--> detik, total ukuran model <!--ANGKA:total_mb-->13,0<!--/ANGKA--> MB.
2. *Kenapa PSO tidak lebih baik dari Random Forest biasa?* Di sampel fitness PSO, RMSE turun dari <!--ANGKA:pso_fit_pembanding-->25,60<!--/ANGKA--> ke <!--ANGKA:pso_fit_terbaik-->25,32<!--/ANGKA-->. Tetapi di data uji RF biasa <!--ANGKA:m_rf_B_rmse-->20,52<!--/ANGKA--> dan RF + PSO <!--ANGKA:m_rf_pso_B_rmse-->20,77<!--/ANGKA-->; di validasi silang penuh juga tidak membaik. Selisihnya kecil dan kemungkinan masuk wilayah derau; dugaan, PSO sedikit menyesuaikan diri dengan sampel fitness (belum diuji lebih jauh). PSO sengaja diperkecil (<!--ANGKA:pso_partikel-->6<!--/ANGKA--> partikel x <!--ANGKA:pso_iterasi-->5<!--/ANGKA--> iterasi) agar muat di laptop i3.
3. *Kenapa model terbaik dipilih lewat validasi silang, bukan data uji?* Supaya pemilihan tidak mengintip data uji. Menurut validasi silang model terbaik Mode B adalah <!--ANGKA:pem_b_nama-->Ridge Regression<!--/ANGKA--> (RMSE <!--ANGKA:pem_b_cv-->23,05<!--/ANGKA-->), sedangkan di data uji Random Forest sedikit lebih baik. Selisih antar model dekat sehingga urutannya mudah bergeser, dan itu kami tampilkan apa adanya.
4. *Kenapa tidak ada model yang jauh lebih baik dari persistence?* Karena PM2.5 per jam sangat mirip dengan jam sebelumnya, sehingga tebakan sederhana sudah kuat; riwayat 1 jam lalu hampir semua informasi yang dibutuhkan (lihat permutation importance di halaman Evaluasi).

---

## Halaman 7. Evaluasi dan Interpretasi
**File:** `halaman/07_evaluasi_interpretasi.py`

**Tujuan.** Menilai satu model terpilih: metrik, aktual vs prediksi, residual, error per bulan dan kategori udara, serta fitur apa yang paling dipakai.

**Data.** `artifacts/hasil.json` (`model.*.uji`, `per_bulan`, `per_kategori`, `kuantil_residual`, `interpretasi`) dan `artifacts/prediksi_uji.csv` untuk grafik aktual vs prediksi dan residual.

**Fungsi Streamlit kunci.** `st.selectbox` (pilih model, bawaan = terbaik menurut CV), `st.select_slider` (bulan), `st.tabs`, `st.plotly_chart`, `tampilkan_kode`. Kalimat tentang bias dan lebar rentang dibangun dari angka.

**Cara menjelaskan.** "Di Mode B model kami meleset rata-rata sekitar <!--ANGKA:m_ridge_B_mae-->11,80<!--/ANGKA--> ug/m3 (MAE Ridge) dan paling bergantung pada kolom <!--ANGKA:imp_top_b-->pm25_lag1<!--/ANGKA-->: kalau kolom itu diacak, RMSE naik <!--ANGKA:imp_top_b_nilai-->119,4<!--/ANGKA--> ug/m3. Tanpa riwayat PM2.5 (Mode A) modelnya jauh lebih lemah (R2 <!--ANGKA:m_hgb_A_r2-->0,462<!--/ANGKA-->)."

**Pertanyaan yang mungkin ditanya**
1. *Apa arti MAE dan RMSE di sini?* MAE adalah rata-rata meleset dalam ug/m3; RMSE serupa tetapi lebih menghukum kesalahan besar. Contoh Random Forest Mode B: MAE <!--ANGKA:m_rf_B_mae-->11,38<!--/ANGKA--> dan RMSE <!--ANGKA:m_rf_B_rmse-->20,52<!--/ANGKA-->, artinya sebagian besar meleset kecil tetapi ada lonjakan yang meleset besar.
2. *Dari mana rentang ketidakpastian di halaman Prediksi?* Dari kuantil residual (aktual dikurangi prediksi) di data uji. Untuk Ridge Mode B, 90% residual ada di antara <!--ANGKA:kq05_b-->-24,3<!--/ANGKA--> dan <!--ANGKA:kq95_b-->26,9<!--/ANGKA--> ug/m3. Ini perkiraan kasar dari satu tahun uji, bukan jaminan statistik.
3. *Fitur apa yang paling penting dan bagaimana tahu?* Dengan permutation importance: satu kolom diacak lalu dilihat seberapa naik RMSE. Di Mode B kolom teratas <!--ANGKA:imp_top_b-->pm25_lag1<!--/ANGKA-->. Itu menunjukkan ketergantungan model, bukan sebab-akibat di atmosfer.
4. *Kenapa interpretasi memakai Ridge di Mode B?* Karena interpretasi dihitung untuk model terbaik menurut validasi silang, yaitu <!--ANGKA:pem_b_nama-->Ridge Regression<!--/ANGKA--> di Mode B dan <!--ANGKA:pem_a_nama-->HistGradientBoosting<!--/ANGKA--> di Mode A. Karena Ridge linear, kurva partial dependence-nya berupa garis lurus.

---

## Halaman 8. Uji Kejujuran Model
**File:** `halaman/08_uji_kejujuran.py` (ciri khas proyek)

**Tujuan.** Menguji apakah model benar-benar bagus atau hanya terlihat bagus: split acak vs split waktu, baseline persistence, kenapa R2 tinggi bisa menipu, dan performa saat polusi parah.

**Data.** `artifacts/hasil.json`: `uji_kejujuran`, `baseline`, `model.*`, `pemenang`. Ringkasan di bagian atas halaman dihitung otomatis.

**Fungsi Streamlit kunci.** `st.container(border=True)` (ringkasan), `st.tabs` (4 tab), `grafik.bar_berkelompok`, `grafik.bar_metode`, `tampilkan_kode` (kode asli `uji_kejujuran`, `hitung_baseline`, `metrik_polusi_parah`). Arah setiap kesimpulan (menang atau kalah, lebih tinggi atau lebih rendah) ditentukan angka, termasuk saat hasilnya tidak sesuai harapan.

**Cara menjelaskan.** "Kami tidak hanya melaporkan R2 yang tinggi. Menebak nilai jam lalu saja sudah R2 <!--ANGKA:b_persistence_1jam_r2-->0,944<!--/ANGKA-->, jadi yang kami laporkan adalah seberapa jauh model mengalahkan tebakan itu: RMSE terbaik hanya <!--ANGKA:skill_rf_B-->7,3<!--/ANGKA-->% lebih rendah. Di split acak Mode A hasilnya tampak lebih bagus (R2 <!--ANGKA:uj_acak_r2_a-->0,596<!--/ANGKA--> vs <!--ANGKA:uj_waktu_r2_a-->0,462<!--/ANGKA-->), tetapi di Mode B tidak, jadi kami tidak mengklaim split acak selalu lebih tinggi."

**Pertanyaan yang mungkin ditanya**
1. *Apakah model benar-benar lebih baik dari tebakan sederhana?* Sedikit. Di data uji Mode B, RMSE Random Forest <!--ANGKA:m_rf_B_rmse-->20,52<!--/ANGKA--> berbanding <!--ANGKA:b_persistence_1jam_rmse-->22,14<!--/ANGKA--> untuk persistence (lebih baik <!--ANGKA:skill_rf_B-->7,3<!--/ANGKA-->%). Di validasi silang hanya <!--ANGKA:n_menang_cv_b-->3<!--/ANGKA--> dari <!--ANGKA:n_model_b-->5<!--/ANGKA--> model Mode B yang mengalahkan persistence. Itu temuan jujur kami, bukan kegagalan: kami menunjukkannya, bukan menyembunyikannya.
2. *Apakah split acak selalu terlihat lebih bagus?* Tidak selalu. Mode A: R2 acak <!--ANGKA:uj_acak_r2_a-->0,596<!--/ANGKA--> vs waktu <!--ANGKA:uj_waktu_r2_a-->0,462<!--/ANGKA--> (tampak lebih bagus, kemungkinan karena jam bertetangga bocor ke data uji). Mode B: acak <!--ANGKA:uj_acak_r2_b-->0,936<!--/ANGKA--> vs waktu <!--ANGKA:uj_waktu_r2_b-->0,950<!--/ANGKA--> (tidak lebih bagus). Perlu diingat uji acak mencakup 2010-2014 sedangkan uji waktu hanya 2014, jadi perbandingan ini menunjukkan arah, bukan ukuran persis efek kebocoran.
3. *Kenapa R2 tinggi bisa menipu?* R2 membandingkan dengan tebakan "selalu rata-rata". Karena PM2.5 sangat mirip dari jam ke jam, persistence tanpa belajar sudah R2 <!--ANGKA:b_persistence_1jam_r2-->0,944<!--/ANGKA-->, sedangkan model terbaik <!--ANGKA:m_rf_B_r2-->0,952<!--/ANGKA-->: R2 nyaris tidak membedakan. Karena itu kami melaporkan MAE, RMSE, MedAE, dan selisih terhadap baseline.
4. *Bagaimana performa saat polusi parah?* Ada <!--ANGKA:parah_n-->1.737<!--/ANGKA--> jam di atas ambang di data uji. Model terbaik Mode B menurut CV punya MAE <!--ANGKA:pem_b_parah_mae-->20,7<!--/ANGKA--> saat parah (<!--ANGKA:parah_b_kali-->2,2<!--/ANGKA--> kali saat normal; persistence <!--ANGKA:b_persist_parah_mae-->21,0<!--/ANGKA-->). Mode A bias <!--ANGKA:pem_a_parah_bias-->-74,2<!--/ANGKA--> ug/m3: sangat meremehkan polusi parah karena tidak punya riwayat PM2.5.

---

## Halaman 9. Prediksi Satu Input
**File:** `halaman/09_prediksi_satu_input.py`, **logika:** `model/prediksi.py`

**Tujuan.** Memprediksi PM2.5 satu jam dari input pengguna, menampilkan gauge, kategori udara berwarna, saran kesehatan, rentang ketidakpastian, dan perbandingan semua model.

**Data.** Model dari `artifacts/models/*.joblib`; rentang ketidakpastian dari `hasil.json` (`model.*.kuantil_residual`); mode demo memakai CSV (cuaca, riwayat 24 jam, dan nilai aktual).

**Fungsi Streamlit kunci.** `st.form` + `st.form_submit_button` (input manual), `st.data_editor` (riwayat 24 jam Mode B), `st.session_state` (tombol contoh), `st.cache_resource` (muat model), `st.plotly_chart` (gauge Plotly), `tampilkan_kode`. Rumus fitur sama persis dengan training karena memakai `fitur_waktu.buat_baris_fitur` (diuji di `alat/uji_cepat.py`).

**Cara menjelaskan.** "Pengguna memilih satu jam (atau mengisi manual); model Mode B memakai cuaca dan riwayat 24 jam terakhir. Hasilnya dalam gauge dengan kategori udara, saran kesehatan, dan rentang 90% yang dihitung dari galat model di data uji. Di bawahnya semua model dibandingkan untuk input yang sama."

**Pertanyaan yang mungkin ditanya**
1. *Dari mana rentang ketidakpastian itu?* Dari kuantil residual (aktual dikurangi prediksi) model terpilih di data uji, dikelompokkan menurut kategori prediksi. Perkiraan kasar dari satu tahun data, bukan jaminan statistik; halaman menyebutnya begitu.
2. *Kenapa ada Mode A dan Mode B di prediksi?* Mode B butuh riwayat PM2.5 24 jam terakhir dan jauh lebih akurat; Mode A cadangan kalau riwayat tidak ada (RMSE <!--ANGKA:pem_a_rmse-->68,60<!--/ANGKA--> vs <!--ANGKA:pem_b_rmse-->21,30<!--/ANGKA--> untuk model terbaik menurut CV).
3. *Apakah prediksi di halaman ini sama dengan di training?* Ya. Fungsi pembentuk fitur satu baris dipakai bersama dengan pipeline training dan diuji kecocokannya (30 baris acak, dua mode) di `alat/uji_cepat.py`; Pipeline preprocessing ikut tersimpan di file model.
4. *Kenapa saran kesehatan hanya ringkasan?* Itu ringkasan umum per kategori AQI, bukan saran medis; aplikasi ini bahan belajar.

---

## Halaman 10. Prediksi Massal
**File:** `halaman/10_prediksi_massal.py`, **validasi dan prediksi:** `model/prediksi.py`

**Tujuan.** Memprediksi banyak jam sekaligus dari CSV unggahan dan mengunduh hasilnya.

**Data.** CSV unggahan (format sama dengan CSV dataset), template contoh dari data asli, model dari `artifacts/models`.

**Fungsi Streamlit kunci.** `st.download_button` (template dan hasil), `st.file_uploader`, `st.dataframe`, `validasi_unggahan` (pesan error ramah), `prediksi_massal`.

**Cara menjelaskan.** "Pengguna mengunduh template, mengisinya, lalu mengunggah. Kami memvalidasi kolom, arah angin, dan urutan jam dengan pesan yang jelas, lalu setiap jam diprediksi; kalau ada nilai aktual, error dihitung dan hasil bisa diunduh."

**Pertanyaan yang mungkin ditanya**
1. *Kenapa Mode B butuh jam berurutan tanpa celah?* Karena lag dan rata-rata bergulir dihitung dari baris-baris sebelumnya; jam yang hilang membuat lag salah. Validasi menolak file seperti itu dengan pesan yang jelas.
2. *Kenapa 24 baris pertama tidak diprediksi (Mode B)?* Butuh riwayat 24 jam sebelumnya; baris awal tidak punya riwayat itu.
3. *Bagaimana memastikan hasil massal sama dengan prediksi satu input?* Rumus fitur dan model sama; selisih hanya pembulatan 2 desimal pada tabel hasil (diuji manual: selisih maksimum di bawah 0,005 ug/m3).

---

## Halaman 11. Kesimpulan dan Referensi
**File:** `halaman/11_kesimpulan_referensi.py`

**Tujuan.** Merangkum temuan (dihitung dari hasil.json), keterbatasan, saran, dan daftar pustaka.

**Data.** `artifacts/hasil.json`; daftar pustaka ditulis di kode halaman.

**Fungsi Streamlit kunci.** `st.markdown`, kalimat temuan dibangun dari angka sehingga arah (membantu atau merugikan) mengikuti data.

**Cara menjelaskan.** "Kesimpulan kami: Mode B sedikit lebih baik dari baseline persistence (<!--ANGKA:terbaik_uji_b_skill-->7,3<!--/ANGKA-->% lebih rendah RMSE), Mode A lemah, PSO dan PCA tidak membantu. Keterbatasan utama: satu stasiun, 2010-2014, bukan real-time."

**Pertanyaan yang mungkin ditanya**
1. *Apa kontribusi proyek ini kalau hasilnya hanya sedikit lebih baik dari baseline?* Pengujian yang jujur: baseline persistence, split berdasarkan waktu, uji R2 vs error, split acak vs waktu, dan evaluasi saat polusi parah; semuanya tersedia dan bisa dibuktikan ulang.
2. *Apa saran perbaikan?* Horizon prediksi lebih panjang, lebih banyak stasiun dan tahun, fitur tambahan, dan validasi berjalan di beberapa tahun uji (belum diuji).
3. *Apakah daftar pustaka sudah diverifikasi?* Hanya sumber EPA yang dibaca langsung dari dokumennya; yang lain dari pengetahuan umum dan harus dicek ulang (tahun, halaman, DOI) sebelum masuk laporan. Halaman menyebutkan itu.

---

## Halaman 14. What-if Simulator (tambahan)
**File:** `halaman/tambahan/14_whatif_simulator.py`

**Tujuan.** Menggeser satu variabel (suhu, titik embun, tekanan, angin, arah angin, jam, bulan, atau riwayat PM2.5) dan melihat kurva prediksi model.

**Data.** Rentang slider dari CSV (persentil 1 sampai 99); model dari `artifacts/models`.

**Fungsi Streamlit kunci.** `st.slider`, `st.selectbox`, `grafik.kurva_whatif` (pita warna kategori udara di latar), `model/prediksi.py:prediksi_satu`.

**Cara menjelaskan.** "Ini menunjukkan bagaimana MODEL merespons perubahan satu variabel dengan variabel lain tetap. Di Mode B riwayat PM2.5 sangat dominan sehingga cuaca hanya sedikit mengubah prediksi; di Mode A pengaruh cuaca lebih terlihat."

**Pertanyaan yang mungkin ditanya**
1. *Apakah kurva ini hubungan sebab-akibat?* Tidak. Ini respons model, dengan variabel lain dianggap tetap padahal di dunia nyata saling terkait.
2. *Kenapa di Mode B menggeser suhu hampir tidak mengubah prediksi?* Karena kolom yang paling diandalkan model adalah riwayat PM2.5 (<!--ANGKA:imp_top_b-->pm25_lag1<!--/ANGKA-->; RMSE naik <!--ANGKA:imp_top_b_nilai-->119,4<!--/ANGKA--> ug/m3 saat diacak).
3. *Kenapa Is dan Ir dibuat 0?* Hampir selalu 0 di data, jadi skenario dasar dibuat 0.
