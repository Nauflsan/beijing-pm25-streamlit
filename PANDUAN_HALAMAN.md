# PANDUAN HALAMAN

Panduan menjelaskan tiap halaman ke dosen: tujuan, data yang dipakai, fungsi Streamlit kunci, cara menjelaskan dalam
2-3 kalimat, dan tiga pertanyaan yang mungkin ditanya beserta jawabannya.

**Catatan penting: angka di dokumen ini diisi otomatis.** Angka yang dibungkus penanda `<!--ANGKA:...-->` dan blok
`<!--BLOK:...-->` ditulis ulang oleh `python perbarui_panduan.py` dari `artifacts/hasil.json` dan CSV. Jalankan perintah itu
setiap selesai training ulang supaya dokumen selalu sama dengan hasil. Jangan edit angka di antara penanda secara manual.

Status: Halaman 1-4 (4 = sebagian). Halaman 5-14 menyusul di tahap berikutnya.

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

## Halaman 4. Preprocessing (sebagian)
**File:** `halaman/04_preprocessing.py`, **logika tabel:** `peta_fitur.py`

**Tujuan.** Menjelaskan bagaimana data mentah menjadi fitur model. Bagian yang sudah ada: tabel kolom CSV ke fitur dan pertanyaan antisipasi tentang jumlah fitur. Menyusul: isi data kosong, outlier, log target, split waktu, scaling.

**Data.** `artifacts/hasil.json`, kunci `data.n_kolom_asli`, `fitur` (daftar fitur Mode A dan B), dan `model.<kunci>.n_fitur_setelah_enkode`.

**Fungsi Streamlit kunci.** `st.table` (tabel panjang dengan teks yang membungkus), `tema.kartu_kpi`, `st.expander`. Jumlah-jumlah dihitung oleh `peta_fitur.ringkasan_jumlah`, bukan ditulis tangan; kalau ada fitur yang tidak terpetakan ke kolom asal, halaman menampilkan peringatan.

**Cara menjelaskan.** "Dari <!--ANGKA:n_kolom_csv-->13<!--/ANGKA--> kolom CSV, <!--ANGKA:n_dibuang-->3<!--/ANGKA--> tidak dipakai sebagai fitur, satu jadi target, sisanya jadi <!--ANGKA:n_fitur_a-->11<!--/ANGKA--> fitur di Mode A dan <!--ANGKA:n_fitur_b-->17<!--/ANGKA--> di Mode B. Setelah arah angin di-one-hot, masing-masing menjadi <!--ANGKA:n_enkode_a-->14<!--/ANGKA--> dan <!--ANGKA:n_enkode_b-->20<!--/ANGKA--> kolom."

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

Untuk data sekecil ini jumlahnya cukup banyak (data kecil seperti ini biasanya hanya hasil uji dummy): ada 955 baris latih untuk 20 kolom, sekitar 48 baris per kolom. Risiko overfitting dikendalikan dengan validasi silang berurutan waktu dan evaluasi di tahun yang tidak pernah dilihat saat latih; model pohon juga dibatasi kedalaman dan jumlah sampel daun. Fitur lag saling berkorelasi tinggi, itu wajar dan tidak merusak model pohon. Di eksperimen Ridge Mode B, PCA yang mempertahankan 95% varians memakai 10 dari 20 komponen dengan RMSE 40,67, dibanding 29,51 tanpa PCA (data uji). Perbandingan lengkap dengan dan tanpa PCA ada di halaman PCA.
<!--/BLOK-->
