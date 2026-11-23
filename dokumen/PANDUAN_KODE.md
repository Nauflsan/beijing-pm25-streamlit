# PANDUAN KODE

Peta seluruh kode proyek: file apa melakukan apa, alur datanya, dan kalau ingin mengubah sesuatu, file mana yang diubah.
Dibuat supaya bisa menjawab pertanyaan "angka ini dari mana dan kodenya mana?".

Tabel peta hasil.json di bagian 5 diisi otomatis oleh `python -m alat.perbarui_panduan` (nomor baris dihitung langsung dari file).

**Semua perintah dijalankan dari folder proyek** (`web_pm25_beijing`) dengan env aktif. Skrip di dalam paket dijalankan dengan
`python -m nama_folder.nama_file`, bukan `python nama_folder/nama_file.py`, supaya impor antar-folder bekerja.

---

## 1. Struktur folder

```
web_pm25_beijing/
├── app.py                  pintu masuk web (menu navigasi di atas)
├── konfigurasi.py          SEMUA konstanta proyek (tetap di root, dibaca semua folder)
├── requirements.txt, .gitignore, .streamlit/config.toml
├── data/                   CSV dataset
├── artifacts/              HASIL training: models/*.joblib, hasil.json, prediksi_uji.csv (ikut di-commit)
├── halaman/                halaman web (01 sampai 11, tambahan/ untuk 12 sampai 14)
├── preprocessing/          persiapan data
│     utilitas_data.py          muat CSV, ringkasan dataset, format angka
│     fitur_waktu.py            isi kosong, sin-cos, lag, rolling, split waktu, Pipeline, buat_baris_fitur
│     peta_fitur.py             tabel "Dari 13 kolom CSV ke fitur model" + tanya-jawab jumlah fitur
│     eksperimen_ringan.py      pintu masuk eksperimen (Ridge): memanggil tiga file di bawah
│     eksperimen_preprocessing.py   isi data kosong, skala, log target
│     eksperimen_pca.py             PCA dan SelectKBest
│     eksperimen_ablasi.py          ablasi kelompok fitur
│     eksperimen_umum.py            pembantu bersama (skor_ridge)
├── model/                  pelatihan
│     latih_semua_model.py      skrip latih utama (resume, log, ukuran file)
│     pso_random_forest.py      PSO untuk hyperparameter Random Forest
├── evaluasi/               penilaian dan pembuktian
│     evaluasi_regresi.py       metrik, error per bulan/kategori/polusi parah, CV, permutation, partial dependence
│     kategori_udara.py         PM2.5 menjadi kategori AQI, warna, saran kesehatan
│     bukti_kode.py             peta hasil.json ke kode + pengambil kode asli fungsi
│     bukti_eksperimen.py       hitung ulang eksperimen dan bandingkan dengan hasil.json
├── tampilan/               tema_langit_beijing.py, grafik.py, utilitas_app.py
├── alat/                   uji_cepat.py, uji_halaman.py, perbarui_panduan.py
└── dokumen/                PANDUAN_KODE.md (ini), PANDUAN_HALAMAN.md, STATUS_PROYEK.md (+ README, CARA_MENJALANKAN, PERBEDAAN_DENGAN_REFERENSI menyusul)
```

## 2. Alur data (dari CSV sampai tampil di halaman)

```
data/PRSA_Beijing_PM25_2010_2014_clean.csv
        |  preprocessing/utilitas_data.muat_data_mentah        (baca CSV, buat kolom waktu, urutkan)
        v
preprocessing/fitur_waktu.siapkan_data          (isi kosong ffill, sin-cos, lag, rolling, kolom layak_model)
        |  fitur_waktu.bagi_waktu               (latih: tahun < 2014, uji: tahun >= 2014)
        v
model/latih_semua_model.py   (dijalankan di LAPTOP, bukan di web)
   |-- hitung_baseline            -> hasil.json["baseline"]
   |-- latih_dan_simpan x 9       -> artifacts/models/*.joblib + hasil.json["model"]
   |      (CV: evaluasi/evaluasi_regresi.cv_regresi; metrik: evaluasi_regresi.evaluasi_lengkap)
   |-- model/pso_random_forest.jalankan_pso   -> hasil.json["pso"]
   |-- uji_kejujuran              -> hasil.json["uji_kejujuran"]
   |-- preprocessing/eksperimen_ringan.jalankan_eksperimen -> hasil.json["eksperimen"]  (Ridge saja)
   |-- hitung_interpretasi        -> hasil.json["interpretasi"]
   `-- simpan_prediksi_uji        -> artifacts/prediksi_uji.csv
        |
        v
artifacts/hasil.json + artifacts/models/*.joblib      (di-commit ke GitHub)
        |
        v
app.py -> halaman/*.py   (HANYA membaca hasil.json / .joblib / CSV, tidak melatih apa pun)
```

Prinsip: web tidak pernah melatih model. Semua angka model dibaca dari `hasil.json`; angka dataset dihitung dari CSV.

## 3. Kalau mau ganti X, ubah file Y

| Mau mengubah | Ubah di | Lalu |
|---|---|---|
| Tahun pemisah latih/uji | `konfigurasi.py` `TAHUN_UJI_MULAI` | latih ulang (`python -m model.latih_semua_model --penuh --ulang`) |
| Lag atau jendela rata-rata | `konfigurasi.py` `LAG_JAM`, `JENDELA_ROLLING_JAM` | latih ulang; cek `preprocessing/peta_fitur.py` dan halaman Prediksi |
| Parameter model (Ridge, DT, HGB) | `konfigurasi.py` bagian 4 | latih ulang |
| Parameter Random Forest | `konfigurasi.py` `PROFIL_LATIH` | latih ulang |
| Ruang cari PSO | `konfigurasi.py` `PSO_BATAS`, `PSO_W/C1/C2`; partikel/iterasi di `PROFIL_LATIH` | latih ulang |
| Ambang kategori udara atau versinya | `konfigurasi.py` `AMBANG_BATAS_ATAS`, `VERSI_AMBANG_AKTIF` | tidak perlu latih ulang |
| Warna/tema tampilan | `konfigurasi.py` bagian 9 dan `.streamlit/config.toml` | muat ulang web |
| Nama anggota, dosen, kelompok | `konfigurasi.py` bagian 7 | muat ulang web |
| Cara isi data kosong | `preprocessing/fitur_waktu.py` `isi_pm` | latih ulang |
| Menambah fitur baru | `preprocessing/fitur_waktu.py` (`siapkan_data`, `FITUR_NUMERIK`), `preprocessing/peta_fitur.py` (`ATURAN`) | latih ulang |
| Menambah eksperimen baru | file baru di `preprocessing/`, daftarkan di `eksperimen_ringan.jalankan_eksperimen` dan `evaluasi/bukti_kode.py` (`PETA`) | latih ulang (--ulang) |
| Menambah model baru | `konfigurasi.py` `NAMA_MODEL`, `model/latih_semua_model.py` (`buat_estimator` dan daftar di `main`) | latih ulang |
| Menyembunyikan halaman tambahan | `konfigurasi.py` `SAKLAR_HALAMAN_TAMBAHAN` | muat ulang web |
| Urutan/judul menu | `app.py` `DAFTAR_HALAMAN` | muat ulang web |
| Memindah file kode ke folder lain | pindahkan file lalu perbaiki `from ... import`; `evaluasi/bukti_kode.py` mencari file otomatis di folder yang terdaftar di `FOLDER_KODE` | `python -m alat.uji_cepat` |

## 4. Cara menjalankan (ringkas)

| Tujuan | Perintah |
|---|---|
| Tes sebelum training | `python -m alat.uji_cepat` |
| Training penuh | `python -m model.latih_semua_model --penuh` (tambah `--ulang` untuk paksa ulang) |
| Tes semua halaman | `python -m alat.uji_halaman` |
| Jalankan web | `streamlit run app.py` |
| Isi ulang angka di dokumen panduan | `python -m alat.perbarui_panduan` |
| Buktikan angka eksperimen | `python -m evaluasi.bukti_eksperimen` (atau `--bagian pca`) |

## 5. Peta: bagian hasil.json dihasilkan kode yang mana

<!--BLOK:peta_hasil-->
| Bagian hasil.json | Isi | Dihasilkan oleh | Fungsi | Dibaca halaman |
|---|---|---|---|---|
| data | ringkasan data (jumlah baris, rentang latih/uji) | model/latih_semua_model.py baris 113 | Data | 2, 3, 4 |
| fitur | daftar nama fitur Mode A dan B | preprocessing/fitur_waktu.py baris 35 | daftar_fitur | 4 |
| baseline | persistence 1 jam, 24 jam, rata-rata latih | model/latih_semua_model.py baris 140 | hitung_baseline | 1, 6, 7, 8 |
| model.<kode>_<mode> (parameter, ukuran, waktu) | 9 model terlatih dan metadatanya | model/latih_semua_model.py baris 171 | latih_dan_simpan | 6, 7 |
| model.*.cv | validasi silang TimeSeriesSplit | evaluasi/evaluasi_regresi.py baris 124 | cv_regresi | 6 |
| model.*.uji, per_bulan, per_kategori, polusi_parah, kuantil_residual | metrik di data uji | evaluasi/evaluasi_regresi.py baris 100 | evaluasi_lengkap | 7, 8, 9 |
| pso | riwayat dan hasil pencarian PSO | model/pso_random_forest.py baris 34 | jalankan_pso | 6 |
| pemenang | model terbaik tiap mode (menurut CV) | model/latih_semua_model.py baris 254 | pilih_pemenang | 1, 7 |
| uji_kejujuran | split acak vs split waktu (HGB) | model/latih_semua_model.py baris 222 | uji_kejujuran | 8 |
| eksperimen.isi_kosong | cara isi data kosong (Ridge Mode B) | preprocessing/eksperimen_preprocessing.py baris 24 | _eksp_isi_kosong | 4 |
| eksperimen.skala, eksperimen.log_target | skala dan log target (Ridge) | preprocessing/eksperimen_preprocessing.py baris 13 | _eksp_skala_dan_log | 4 |
| eksperimen.pca | scree, dengan vs tanpa PCA, SelectKBest | preprocessing/eksperimen_pca.py baris 22 | _eksp_pca | 5 |
| eksperimen.ablasi | Mode B tanpa satu kelompok fitur | preprocessing/eksperimen_ablasi.py baris 10 | _eksp_ablasi | 13 |
| interpretasi | permutation importance dan partial dependence | model/latih_semua_model.py baris 264 | hitung_interpretasi | 7 |
| prediksi_uji.csv | prediksi semua model di data uji | model/latih_semua_model.py baris 283 | simpan_prediksi_uji | 7 |
<!--/BLOK-->

## 6. Cara membuktikan angka (untuk menjawab dosen)

| Pertanyaan | Jalankan | Hasil yang diharapkan |
|---|---|---|
| Apakah eksperimen (PCA, log, isi kosong, skala, ablasi) benar-benar menghasilkan angka di hasil.json? | `python -m evaluasi.bukti_eksperimen` (atau `--bagian pca`) | tiap bagian tertulis COCOK |
| Apakah fitur lag/rolling bebas kebocoran masa depan? | `python -m alat.uji_cepat` | pengecekan "fitur lag/rolling ... tidak berubah" semuanya OK |
| Kapan dan dengan versi library apa model dilatih? | buka `artifacts/hasil.json` bagian `meta` | tanggal, profil, versi Python dan scikit-learn |
| Log proses training | folder `logs/latih_*.log` | progres tiap model dan ringkasan akhir |
| Semua halaman berjalan tanpa error? | `python -m alat.uji_halaman` | SEMUA HALAMAN LULUS |
| Melatih ulang seluruhnya | `python -m model.latih_semua_model --penuh --ulang` | hasil.json baru; lalu `python -m alat.perbarui_panduan` |

Catatan: `bukti_eksperimen` memakai fungsi yang sama dengan saat training (di folder `preprocessing/`), bukan salinan, jadi COCOK berarti
angka di hasil.json memang berasal dari kode itu pada data itu. Kalau BEDA, periksa dulu apakah versi library sama dengan yang tercatat di `meta`.
