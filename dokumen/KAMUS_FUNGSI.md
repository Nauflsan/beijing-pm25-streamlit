# KAMUS FUNGSI

Dibuat OTOMATIS dari kode dan docstring oleh `python -m alat.buat_kamus_fungsi`. Jangan diedit manual; ubah docstring di kodenya.
Kolom: nama fungsi, nomor baris di file, fungsinya apa, input, output.


## Root

### `app.py`

app.py - pintu masuk web (jalankan: streamlit run app.py).

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `susun_menu` | 40 | kumpulkan halaman yang ada + aktif jadi dict {grup: [st.Page]}. | - | dict untuk st.navigation. |

### `konfigurasi.py`

konfigurasi.py - SATU-SATUNYA tempat semua konstanta proyek.


## preprocessing/ : persiapan data

### `preprocessing/eksperimen_ablasi.py`

eksperimen_ablasi.py - ablasi kelompok fitur (Ridge, Mode B): hasil jika satu kelompok fitur dibuang.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `_eksp_ablasi` | 10 | Mode B tanpa satu kelompok fitur. | - | {nama_varian: metrik}. |

### `preprocessing/eksperimen_pca.py`

eksperimen_pca.py - eksperimen PCA dan SelectKBest (Ridge): scree, dengan vs tanpa PCA, seleksi kolom pembanding.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `_eksp_pca` | 22 | eksperimen PCA dan SelectKBest dengan Ridge untuk Mode A dan B. | latih, uji (hasil bagi_waktu). | dict {A/B: scree, kumulatif, tanpa_pca, varian, select_k_best}. |

### `preprocessing/eksperimen_preprocessing.py`

eksperimen_preprocessing.py - eksperimen preprocessing (Ridge): cara mengisi data kosong, scaling, dan log target.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `_eksp_skala_dan_log` | 13 | Ridge dengan vs tanpa scaler, dan target asli vs log1p (dievaluasi di skala asli). | latih, uji. | (hasil skala, hasil log_target). |
| `_eksp_isi_kosong` | 25 | bandingkan cara mengisi PM2.5 kosong untuk fitur lag (Ridge Mode B). Dievaluasi pada baris yang SAMA (baris layak dari metode ffill) supaya adil. 'interpolasi' memakai masa depan = BOCOR, hanya pembanding. | - | - |

### `preprocessing/eksperimen_ringan.py`

eksperimen_ringan.py - pintu masuk eksperimen ringan (Ridge saja, hitungan detik). Dipanggil dari model/latih_semua_model.py.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `jalankan_eksperimen` | 17 | jalankan semua eksperimen ringan. | df_mentah (hasil muat_data_mentah), d_siap (hasil siapkan_data), latih, uji (hasil bagi_waktu), log. | dict {skala, log_target, isi_kosong, pca, ablasi, catatan}. |

### `preprocessing/eksperimen_umum.py`

eksperimen_umum.py - pembantu bersama semua eksperimen ringan: melatih Ridge lalu menilainya di data uji.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `skor_ridge` | 19 | latih Ridge (preprocessor + langkah 'tengah' opsional) lalu nilai di data uji. | - | dict metrik. |

### `preprocessing/fitur_waktu.py`

fitur_waktu.py - pembuatan fitur (siklik jam/bulan, lag, rolling), split waktu, dan Pipeline preprocessing.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `daftar_fitur` | 35 | nama kolom input model. | 'A' atau 'B'. | list (numerik dulu, lalu arah angin). |
| `hitung_fitur_pm` | 40 | fitur lag dan rata-rata bergulir dari seri PM2.5 (yang sudah diisi). | Series PM2.5 terurut waktu per jam. | DataFrame (kolom FITUR_LAG + FITUR_ROLLING). |
| `isi_pm` | 54 | mengisi PM2.5 kosong untuk membentuk fitur lag. | pm (Series), tahun (Series), metode: 'ffill' -> teruskan nilai terakhir (hanya masa lalu) [DIPAKAI] 'median_latih' -> median data latih (pembanding) 'interpo... | Series terisi. |
| `siapkan_data` | 72 | tambah semua fitur turunan ke data mentah. | DataFrame dari utilitas_data.muat_data_mentah (terurut waktu), metode_isi (lihat isi_pm). | DataFrame dengan kolom tambahan: ada_target, pm_diisi, fitur siklik, lag, rolling, layak_model. 'layak_model' = target asli ada DAN semua fitur Mode B lengka... |
| `bagi_waktu` | 93 | split berdasarkan waktu. | DataFrame dari siapkan_data. | (latih, uji) hanya baris layak. latih = tahun < tahun_uji, uji = tahun >= tahun_uji. [TERKAIT] konfigurasi.TAHUN_UJI_MULAI |
| `buat_preprocessor_umum` | 103 | ColumnTransformer: numerik -> imputer median (+ StandardScaler bila skala), arah angin -> one-hot. | daftar kolom numerik, daftar kolom kategorik, skala (bool). | ColumnTransformer (belum di-fit). |
| `buat_preprocessor` | 123 | preprocessor standar untuk Mode A/B. | mode, skala. | ColumnTransformer. |
| `buat_pipeline` | 128 | Pipeline (preprocessing + model) yang disimpan utuh ke .joblib, jadi app tidak perlu menulis ulang preprocessing. | estimator sklearn, mode, skala (True untuk Ridge). | Pipeline [('prep', ...), ('model', estimator)]. |
| `buat_baris_fitur` | 137 | membentuk SATU baris fitur dari input pengguna (dipakai halaman Prediksi), dengan rumus yang sama persis seperti siapkan_data (sudah diuji di uji_cepat.py). | waktu (pd.Timestamp jam yang diprediksi); cuaca (dict: DEWP, TEMP, PRES, Iws, Is, Ir, cbwd); riwayat_pm25 (list PM2.5 per jam, urut LAMA -> BARU, nilai terak... | DataFrame 1 baris dengan kolom = daftar_fitur(mode). |

### `preprocessing/peta_fitur.py`

peta_fitur.py - tabel "Dari 13 kolom CSV ke fitur model".

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `_id` | 58 | format angka gaya Indonesia (pembungkus utilitas_data.fmt_id). | angka, desimal. | str. |
| `_turunan` | 63 | fitur dalam 'daftar' yang berasal dari kolom ini. | satu aturan, list nama fitur. | list. |
| `jumlah_setelah_enkode` | 68 | jumlah kolom setelah one-hot untuk satu mode, dibaca dari hasil['model'][*]['n_fitur_setelah_enkode']. | - | int atau None. |
| `ringkasan_jumlah` | 74 | semua jumlah untuk kartu ringkasan, dari hasil.json. | - | dict {n_kolom_csv, n_fitur_a, n_fitur_b, n_enkode_a, n_enkode_b, n_dibuang, selisih_b_a, selisih_enkode}. |
| `bangun_tabel` | 89 | tabel 'Dari 13 kolom CSV ke fitur model'. | dict hasil.json. | (DataFrame, daftar_peringatan). Kolom: Kolom asal / Diapakan / Alasan / Mode A / Mode B. Mode A/B berisi 'tidak' atau 'N fitur: nama, nama'. Baris terakhir =... |
| `tabel_ke_markdown` | 125 | DataFrame -> tabel markdown (tanpa dependensi tabulate). | DataFrame. | str. |
| `pertanyaan_dosen` | 133 | 5 pertanyaan antisipasi dosen tentang jumlah fitur beserta jawabannya. SEMUA angka diambil dari hasil.json (dan konfigurasi.py), jadi jawabannya ikut berubah kalau fitur diubah lalu dilatih ulang. | dict hasil.json. | list of (pertanyaan, jawaban). |

### `preprocessing/utilitas_data.py`

utilitas_data.py - memuat dan memeriksa dataset, ringkasan dataset, penyimpan JSON aman.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `validasi_kolom` | 20 | cek semua kolom wajib ada. | DataFrame. | (ok: bool, kolom_hilang: list). |
| `muat_data_mentah` | 26 | baca CSV, buat kolom 'waktu', urutkan kronologis. | path CSV (default cfg.FILE_CSV). | DataFrame mentah (13 kolom asli + 'waktu'); arah angin bertipe object (aman untuk pandas 3). |
| `tambah_kolom_altair` | 45 | salin kolom 'pm2.5' ke 'pm25'. Altair/Vega-Lite menganggap titik sebagai properti bersarang sehingga grafik kosong. Judul sumbu tetap ditulis "pm2.5" di grafik. | DataFrame. | salinan DataFrame dengan kolom tambahan 'pm25'. |
| `panjang_kosong_terpanjang` | 56 | panjang deretan nilai kosong berurutan terpanjang. | Series. | int (jam). |
| `ringkasan_dataset` | 66 | angka-angka ringkas dataset (dihitung dari CSV, bukan di-hardcode). | DataFrame hasil muat_data_mentah. | dict. |
| `fmt_id` | 89 | format angka gaya Indonesia (titik ribuan, koma desimal). | angka (atau None), desimal. | str. Contoh: fmt_id(1234.567, 1) -> '1.234,6'. |
| `_bersih` | 102 | Ubah tipe numpy/NaN jadi tipe JSON biasa (NaN/inf -> None). | - | - |
| `simpan_json_aman` | 122 | tulis JSON secara atomik (tulis ke file sementara lalu ganti) supaya hasil.json tidak rusak kalau skrip terhenti di tengah jalan. | path, dict. | - |
| `muat_json` | 136 | baca JSON. | path. | dict ({} kalau file belum ada). |


## model/ : pelatihan dan prediksi

### `model/latih_semua_model.py`

latih_semua_model.py - melatih 5 model regresi PM2.5 sekali jalan, lalu menyimpan hasilnya.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `siapkan_log` | 46 | logger ke layar + file logs/latih_<waktu>.log. | - | (logger, path_file_log). |
| `fmt_waktu` | 60 | detik -> teks ramah ('45 detik' / '3.2 menit'). | - | str. |
| `info_versi` | 65 | versi Python/library saat training (untuk mendeteksi ketidakcocokan saat app dijalankan). | - | - |
| `buat_estimator` | 71 | membuat estimator sklearn (belum di-fit). | kode ('ridge','dt','rf','hgb','rf_pso'), profil (dict dari cfg.PROFIL_LATIH), params_pso (untuk 'rf_pso'). | estimator. |
| `buat_pipeline_model` | 98 | Pipeline lengkap (preprocessing + estimator). Ridge memakai StandardScaler, model pohon tidak perlu. | - | - |
| `parameter_ringkas` | 103 | parameter penting model untuk dicatat di hasil.json. | - | dict. |
| `Data` | 113 | Wadah data latih/uji yang sudah disiapkan. Atribut: df_mentah, d (semua fitur), latih, uji, info. | - | - |
| `Data.xy` | 134 | ambil fitur dan target untuk satu bagian data dan satu mode. | bagian ('latih'/'uji'), mode ('A'/'B'). | (X DataFrame, y Series). |
| `hitung_baseline` | 141 | baseline tanpa training sebagai pembanding: persistence 1 jam, persistence 24 jam, rata-rata data latih. | - | (dict untuk hasil.json, dict prediksi uji {nama: array}). |
| `sudah_selesai` | 166 | apakah model ini boleh dilewati (resume). Syarat: bukan --ulang, profil sama, dummy sama, file ada. | - | - |
| `latih_dan_simpan` | 172 | CV berurutan waktu -> fit pada seluruh data latih -> evaluasi di data uji -> simpan .joblib -> catat hasil.json. | kode model, mode 'A'/'B', objek Data, profil, nama profil, dummy (bool), folder_model, hasil (dict, diubah di tempat), path_hasil, ulang (bool), log, params_... | entri hasil model (dict) atau None kalau dilewati. |
| `uji_kejujuran` | 223 | model HGB yang SAMA dilatih ulang dengan split ACAK (jumlah baris uji sama dengan split waktu) untuk dibandingkan dengan split waktu. Hanya fit kecil (HGB), untuk halaman Uji Kejujuran Model. | - | dict {A:{split_waktu, split_acak, persistence_1jam_pada_uji_acak, ...}, B:{...}, catatan}. |
| `pilih_pemenang` | 255 | model terbaik per mode menurut RMSE rata-rata CV (BUKAN data uji). | - | {'A': kunci, 'B': kunci}. |
| `hitung_interpretasi` | 265 | permutation importance dan partial dependence untuk model terbaik tiap mode (berdasarkan CV). | - | {mode: {model, permutation, parsial}}. |
| `simpan_prediksi_uji` | 284 | simpan prediksi semua model + baseline pada data uji ke CSV (untuk grafik aktual vs prediksi). Kolom: waktu, bulan, aktual, lalu satu kolom per model ('<kode>_<mode>') dan per baseline. | - | - |
| `cetak_ringkasan` | 301 | tabel ringkas hasil di akhir (dari hasil.json) + peringatan ukuran file. | - | - |
| `baca_argumen` | 327 | baca argumen baris perintah (--cepat/--penuh, --ulang, --sampel). | list argumen atau None. | objek argparse. |
| `main` | 339 | alur utama pelatihan. | argumen CLI (list) atau None. | path hasil.json. |

### `model/prediksi.py`

prediksi.py - logika prediksi untuk halaman Prediksi Satu Input, Prediksi Massal, dan What-if (tanpa Streamlit).

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `muat_paket` | 26 | baca model terlatih. | kunci (mis. 'ridge_B'), folder artefak (default cfg.FOLDER_ARTEFAK_AKTIF). | dict {pipeline, mode, kode, nama, fitur, profil, dummy, versi} atau None kalau file tidak ada. |
| `versi_tidak_cocok` | 36 | beda versi scikit-learn antara saat training dan sekarang. | - | (versi_latih, versi_sekarang) atau None kalau sama. |
| `prediksi_satu` | 43 | prediksi pm2.5 untuk SATU jam. | paket model, waktu (Timestamp), cuaca (dict DEWP,TEMP,PRES,Iws,Is,Ir,cbwd), riwayat (list pm2.5 per jam, lama -> baru, minimal 24 nilai; wajib untuk Mode B). | float (ug/m3, >= 0). |
| `interval_prediksi` | 52 | rentang ketidakpastian 90% dari kuantil residual data uji, dikelompokkan menurut kategori PREDIKSI (pakai kuantil global kalau kategori itu punya terlalu sedikit sampel). INI PERKIRAAN KASAR dari satu tahun uji. | dict hasil.json, kunci model, nilai prediksi. | dict {bawah, atas, dasar, n}. |
| `contoh_dari_data` | 68 | ambil satu jam dari data asli sebagai contoh. | d_siap (hasil fitur_waktu.siapkan_data), waktu (Timestamp). | (waktu, cuaca dict, riwayat 24 jam lama->baru, aktual atau None) atau None kalau tidak tersedia/riwayat tidak lengkap. |
| `template_csv` | 89 | contoh file unggahan (format sama dengan CSV dataset): n_baris jam berurutan dari data asli. | df data mentah, tahun (default tahun uji), n_baris. | str CSV (bisa diunduh). |
| `validasi_unggahan` | 102 | periksa CSV unggahan sebelum diprediksi. | DataFrame hasil pd.read_csv, mode 'A'/'B'. | (ok: bool, pesan: list[str], df_bersih atau None). Pesan berisi alasan yang bisa langsung diperbaiki pengguna. |
| `prediksi_massal` | 141 | prediksi banyak baris. | paket model, d_valid (hasil validasi_unggahan). | DataFrame {waktu, prediksi, kategori, aktual (bisa kosong), galat = aktual - prediksi}. Mode B hanya mengeluarkan baris yang riwayat 24 jam-nya lengkap (bari... |

### `model/pso_random_forest.py`

pso_random_forest.py - Particle Swarm Optimization (PSO) untuk mencari hyperparameter Random Forest.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `ambil_sampel_berurutan` | 19 | ambil paling banyak 'maks' baris secara merata (urutan waktu tetap terjaga, TIDAK diacak). | X, y (terurut waktu), maks. | (X_sampel, y_sampel). |
| `_menit` | 30 | format detik menjadi teks ramah ('45 detik' atau '3.2 menit'). | detik. | str. |
| `jalankan_pso` | 35 | jalankan PSO. | X, y data LATIH (terurut waktu); buat_model(n_estimators, max_depth, min_samples_leaf) -> pipeline/model baru; batas {nama: (bawah, atas)} (default cfg.PSO_B... | dict {parameter_terbaik, rmse_cv_terbaik, rmse_cv_pembanding, riwayat_gbest (per iterasi, termasuk iterasi 0 = inisialisasi), evaluasi [{params, rmse}], n_ev... |


## evaluasi/ : penilaian dan pembuktian

### `evaluasi/bukti_eksperimen.py`

bukti_eksperimen.py - MEMBUKTIKAN angka eksperimen di hasil.json: hitung ulang dari data, bandingkan angka demi angka.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `bandingkan` | 26 | bandingkan dua struktur (dict/list/angka) secara rekursif. | a (hasil hitung ulang), b (isi hasil.json), jalur (teks lokasi), beda (list penampung). | list perbedaan [(jalur, a, b)]. |
| `hitung_ulang` | 51 | hitung ulang satu bagian eksperimen dengan fungsi training yang asli. | objek Data, nama bagian. | struktur. |
| `main` | 63 | jalankan pembuktian. | argumen CLI. | kode keluar 0 (semua cocok) atau 1. |

### `evaluasi/bukti_kode.py`

bukti_kode.py - menjawab "angka ini dari mana dan kodenya mana?".

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `_cari` | 36 | cari node fungsi/kelas (boleh 'Kelas.metode') di pohon ast. | ast.Module, nama. | node atau None. |
| `_path` | 53 | cari file kode di folder-folder proyek (cukup nama file, mis. 'fitur_waktu.py'). | - | Path atau OSError. |
| `_muat` | 62 | baca file kode dan urai dengan ast. | nama file. | (path, teks, pohon ast); OSError kalau file tidak ada. |
| `kode_fungsi` | 69 | kode asli satu fungsi/kelas dari file proyek (tanpa menjalankan file). | nama file (mis. 'fitur_waktu.py'), nama fungsi/kelas. | str kode, atau pesan kalau tidak ditemukan. |
| `lokasi_kode` | 84 | teks 'file baris N' untuk fungsi/kelas. | file, nama. | str ('file (tidak ditemukan)' kalau gagal). |
| `tabel_peta` | 95 | tabel peta hasil.json -> kode. | - | list of dict {'Bagian hasil.json', 'Isi', 'Dihasilkan oleh (file baris)', 'Fungsi', 'Dibaca halaman'}. Nomor baris dihitung langsung dari file, jadi selalu a... |
| `semua_entri_ada` | 104 | cek semua fungsi di PETA masih ada di file asalnya. | - | list entri yang hilang (kosong = aman). |

### `evaluasi/evaluasi_regresi.py`

evaluasi_regresi.py - metrik regresi, error per bulan / kategori udara / polusi parah, kuantil residual (untuk interval prediksi), validasi silang berurutan waktu, permutation importance, dan partial dependence.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `prediksi_aman` | 18 | model.predict lalu dipotong >= 0. | model, X. | array float. |
| `hitung_metrik` | 23 | MAE, RMSE, R2, MedAE, bias (rata-rata prediksi - aktual), n. | y aktual, p prediksi. | dict (satuan ug/m3 kecuali r2). |
| `_metrik_ringkas` | 40 | versi ringkas hitung_metrik (n, mae, rmse, bias) untuk tabel per bulan/kategori. | y, p. | dict. |
| `metrik_per_bulan` | 46 | error per bulan kalender. | array bulan (1-12), y, p. | {bulan: {n, mae, rmse, bias}}. |
| `metrik_per_kategori` | 52 | error per kategori udara AKTUAL. | - | {nama_pendek: {n, mae, rmse, bias}}. |
| `metrik_polusi_parah` | 64 | bandingkan error saat polusi normal vs parah (aktual > ambang). | - | {ambang, normal:{...}, parah:{...}, rasio_mae_parah_per_normal}. |
| `kuantil_residual` | 80 | kuantil residual (aktual - prediksi) untuk interval ketidakpastian. Ini PERKIRAAN kasar: dihitung dari data uji 2014, mengasumsikan sebaran galat mirip di masa depan. | - | {'global': {kuantil: nilai}, 'per_kategori_prediksi': {nama_pendek: {n, kuantil / None}}} Per kategori dikelompokkan menurut PREDIKSI (itu yang diketahui saa... |
| `evaluasi_lengkap` | 101 | semua evaluasi data uji sekaligus (disimpan ke hasil.json). | y aktual, p prediksi (sudah dipotong >= 0), bulan (array bulan tiap baris). | dict {uji, per_bulan, per_kategori, polusi_parah, kuantil_residual}. |
| `_ringkas_cv` | 116 | rata-rata dan simpangan baku RMSE/MAE/R2 dari hasil tiap lipatan. | list dict per lipatan. | dict {per_fold, rmse_rata, rmse_std, ...}. |
| `cv_regresi` | 126 | TimeSeriesSplit pada DATA LATIH (lipatan selalu: latih di masa lalu, validasi di masa depan). | buat_model() -> model/pipeline baru, X, y (terurut waktu), n_fold. | dict {per_fold:[{n_latih,n_valid,mae,rmse,r2}], rmse_rata, rmse_std, mae_rata, ...} |
| `cv_baseline` | 142 | CV untuk baseline tanpa training, pada lipatan yang SAMA dengan cv_regresi. | fungsi_prediksi(idx_latih, idx_valid) -> array prediksi untuk idx_valid. | - |
| `importance_permutasi` | 155 | permutation importance = seberapa naik RMSE kalau satu kolom diacak. | model (Pipeline), X, y (data uji), n_repeat, sampel (jumlah baris yang dipakai), seed. | list [{fitur, naik_rmse, std}] urut dari terpenting. |
| `kurva_parsial` | 172 | partial dependence (rata-rata prediksi saat satu fitur digeser, fitur lain apa adanya). | model, X (data uji), daftar fitur numerik, sampel (jumlah baris), resolusi (titik grid). | {fitur: {'grid': [...], 'rata_prediksi': [...]}} |

### `evaluasi/kategori_udara.py`

kategori_udara.py - mengubah nilai PM2.5 menjadi kategori kualitas udara (AQI PM2.5 US EPA).

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `_batas_atas` | 28 | batas atas tiap kategori udara untuk satu versi ambang. | versi ('2024'/'2012') atau None (pakai versi aktif). | array float. |
| `indeks_kategori` | 33 | nilai PM2.5 -> indeks kategori 0..5 (0 = Baik, 5 = Berbahaya). | angka atau array (ug/m3). Nilai dipotong (bukan dibulatkan) ke 1 desimal, seperti aturan AQI EPA. | int, atau array int kalau input array. |
| `info_kategori` | 45 | detail satu kategori. | indeks 0..5. | dict(indeks, nama, nama_pendek, warna, batas_bawah, batas_atas (None untuk kategori terakhir), saran). |
| `kategori_dari_nilai` | 59 | gabungan indeks_kategori + info_kategori untuk SATU nilai. | - | dict info kategori. |
| `tabel_ambang` | 64 | daftar semua kategori (untuk tabel di halaman). | - | list of dict info_kategori. |


## tampilan/ : tema, grafik, utilitas web

### `tampilan/grafik.py`

grafik.py - fungsi pembuat grafik (Plotly dan Altair) yang dipakai halaman. Fungsi hanya MEMBUAT figur; menampilkannya (st.plotly_chart / st.altair_chart) dilakukan di halaman. Tidak mengimpor streamlit.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `rapikan` | 23 | gaya seragam Plotly (latar transparan agar cocok mode terang/gelap, font tema). | fig. | fig. |
| `histogram_target` | 34 | histogram PM2.5. | df (ada kolom 'pm2.5'), skala_log (sumbu y log), batas (nilai terbesar yang digambar supaya ekor panjang tidak menggencet grafik; 0 = semua). | fig Plotly. |
| `bar_kategori` | 49 | bar proporsi jam per kategori udara, warna = warna kategori. | list 6 angka (jumlah jam per kategori, urut Baik..Berbahaya). | fig Plotly. |
| `box_per_kelompok` | 64 | boxplot PM2.5 per kelompok (mis. arah angin). | df, kolom_kelompok, urutan (list), batas (potong sumbu y). | fig. |
| `box_target` | 74 | boxplot horizontal PM2.5 (satu kotak). | Series PM2.5 tanpa NaN. | fig Plotly. |
| `heatmap_korelasi` | 81 | heatmap korelasi. | DataFrame korelasi persegi. | fig Plotly (skala -1..1, merah-biru). |
| `bar_korelasi_target` | 88 | bar korelasi tiap fitur dengan target, urut besar-kecil. | Series (index = nama fitur). | fig. |
| `altair_rata_bulanan` | 100 | bar rata-rata PM2.5 per bulan kalender. | DataFrame yang SUDAH punya kolom 'pm25' (salinan 'pm2.5'). | grafik Altair. Judul sumbu tetap 'pm2.5'. |
| `altair_kosong_per_tahun` | 115 | bar jumlah jam PM2.5 kosong per tahun. | df mentah (kolom year, pm2.5). | grafik Altair. |
| `altair_kosong_per_jam` | 124 | bar jumlah PM2.5 kosong per jam dalam sehari (0-23). | df mentah. | grafik Altair. |
| `jumlah_per_kategori` | 133 | hitung jumlah jam per kategori udara dari deret PM2.5. | Series/array (tanpa NaN). | list 6 int. |
| `scree_plot` | 140 | scree plot PCA: bar = varians tiap komponen, garis = varians kumulatif, garis putus = ambang. | scree (list proporsi varians per komponen), kumulatif (list), ambang (tuple). | fig Plotly. |
| `bar_metode` | 159 | bar horizontal membandingkan RMSE beberapa metode. | nama (list), rmse (list), warna (list hex), acuan (nilai RMSE acuan untuk garis putus, opsional). | fig Plotly. |
| `bar_berkelompok` | 173 | bar berkelompok. | kategori (list label sumbu x), seri {nama_seri: list nilai sesuai kategori}. | fig Plotly. |
| `lipatan_waktu` | 186 | gambar TimeSeriesSplit: tiap lipatan = jendela latih (membesar) lalu validasi, lalu blok uji akhir. | per_fold (list dict n_latih, n_valid dari hasil.json), n_latih_total, n_uji. | fig Plotly. |
| `garis_konvergensi` | 203 | kurva konvergensi PSO. | riwayat gbest per iterasi (iterasi 0 = inisialisasi). | fig Plotly. |
| `bar_cv_per_lipatan` | 212 | RMSE tiap lipatan validasi silang per model. | seri {nama: [rmse lipatan 1, 2, ...]}. | fig Plotly. |
| `scatter_aktual_prediksi` | 224 | sebar aktual vs prediksi + garis ideal (y = x). | aktual, prediksi (array), nama_model, maks_titik (sampel acak agar ringan). | fig Plotly. |
| `garis_waktu` | 241 | garis waktu aktual vs beberapa prediksi. | df (kolom 'waktu', 'aktual', dan kolom prediksi), kolom (list nama kolom yang digambar), nama (dict kolom -> label). | fig Plotly. |
| `histogram_residual` | 255 | histogram residual (aktual - prediksi). | array residual. | fig Plotly. |
| `scatter_residual` | 263 | residual terhadap nilai prediksi (melihat apakah galat membesar saat prediksi tinggi). | - | fig Plotly. |
| `bar_per_bulan` | 274 | bar error per bulan. | dict {bulan: {mae, rmse, ...}} dari hasil.json, metrik. | fig Plotly. |
| `bar_per_kategori` | 285 | bar error per kategori udara AKTUAL, warna = warna kategori. | dict {nama_pendek: {n, mae, rmse, bias}}, metrik ('mae', 'rmse', atau 'bias'). | fig Plotly. |
| `bar_importance` | 303 | bar permutation importance. | list [{fitur, naik_rmse, std}] urut terpenting. | fig Plotly. |
| `garis_parsial` | 312 | kurva partial dependence satu fitur. | grid (nilai fitur), rata (rata prediksi), nama_fitur. | fig. |
| `_rgba` | 320 | warna hex jadi rgba transparan. | '#RRGGBB', alpha. | str. |
| `_pita_kategori` | 326 | Batas [bawah, atas] tiap kategori udara (atas kategori terakhir = None) sesuai versi ambang aktif. | - | - |
| `gauge_pm25` | 333 | gauge (speedometer) prediksi pm2.5. Pita latar = enam kategori udara, jarum/bar = nilai prediksi dan berwarna sesuai kategorinya. | nilai (ug/m3), idx_kategori (0-5). | fig Plotly. |
| `bar_prediksi_model` | 350 | bar prediksi tiap model, warna = kategori hasil prediksinya; garis putus = nilai aktual (kalau ada). | nama (list), nilai (list), aktual (float atau None). | fig Plotly. |
| `kurva_whatif` | 366 | kurva respons prediksi saat satu variabel digeser, dengan pita warna kategori udara di latar. | x (list nilai/kategori), y (list prediksi), nama_x, titik_dasar (x, y) skenario awal, kategorik (True = bar). | fig Plotly. |

### `tampilan/tema_langit_beijing.py`

tema_langit_beijing.py - tampilan "Langit Beijing" (TERANG saja): biru langit yang kalem, kartu putih bersih.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `warna_teks_kontras` | 19 | pilih teks hitam/putih yang terbaca di atas warna latar. | '#RRGGBB'. | '#111111' atau '#FFFFFF'. |
| `_tipis` | 26 | warna hex jadi rgba transparan (untuk latar label yang lembut). | '#RRGGBB', alpha 0-1. | str. |
| `pasang_tema` | 33 | suntik CSS tema (font Google Fonts, kartu, header, tab) dan sembunyikan menu pengaturan Streamlit (supaya pengguna tidak bisa memindah ke mode gelap). Dipanggil SEKALI di app.py. | - | - |
| `header_halaman` | 87 | banner judul halaman (biru langit). Kalau idx_kategori (0-5) diberikan, ada garis tipis berwarna kategori di bawah banner sebagai aksen; warna banner sendiri tetap biru. | judul, subjudul, idx_kategori (None atau 0-5). | - |
| `kartu_kpi` | 98 | satu kartu KPI (putih, garis aksen biru). Kalau idx_kategori (0-5) diberikan, muncul label kecil berisi titik warna + nama kategori udara (bukan seluruh kartu diwarnai). | label, nilai (teks atau angka), catatan (teks kecil), idx_kategori (None atau 0-5). | - |
| `lencana_kategori` | 114 | HTML lencana berwarna penuh untuk satu kategori (dipakai hasil prediksi). | idx 0-5. | str HTML. |
| `langkah_alur` | 121 | kartu satu langkah alur kerja dengan lingkaran bernomor. | nomor, judul, isi. | - |
| `kotak_catatan` | 127 | kotak catatan ringan. | teks, jenis ('info' atau 'peringatan'). | - |

### `tampilan/utilitas_app.py`

utilitas_app.py - bantuan khusus app Streamlit: memuat data/hasil dengan cache, pesan ramah kalau artefak belum ada, format angka gaya Indonesia, dan kalimat temuan yang dibangun dari hasil.json (bukan ditulis tangan).

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `fmt` | 20 | format angka gaya Indonesia. | angka (atau None), desimal. | str. (lihat utilitas_data.fmt_id) |
| `muat_data` | 26 | data mentah (cache). | - | DataFrame dari utilitas_data.muat_data_mentah. |
| `_mtime` | 31 | waktu ubah terakhir file (0 kalau tidak ada), dipakai sebagai kunci cache. | Path. | float. |
| `_baca_hasil` | 37 | baca hasil.json dengan cache. | path (str), mtime. | dict. |
| `muat_hasil` | 42 | baca artifacts/hasil.json (cache, otomatis segar kalau file berubah). | - | dict ({} kalau belum ada). |
| `hasil_atau_berhenti` | 48 | ambil hasil.json; kalau belum ada tampilkan pesan ramah lalu hentikan halaman (st.stop). Kalau hasilnya DUMMY, tampilkan banner peringatan. | - | dict hasil. |
| `sebut_model` | 64 | 'ridge_B' -> 'Ridge Regression (Mode B)'. | kunci, hasil. | str. |
| `kalimat_temuan` | 70 | kalimat ringkasan temuan untuk Beranda, dihitung dari hasil.json. Semua angka dan arah perbandingan (menang/kalah dari baseline) ditentukan oleh data, jadi kalau hasilnya berubah kalimatnya ikut berubah. | dict hasil.json. | list[str]. |
| `indeks_kategori_rata` | 110 | indeks kategori untuk satu nilai PM2.5 (dipakai untuk mewarnai KPI/header). | - | int 0-5. |
| `persen_selisih` | 115 | selisih relatif nilai terhadap acuan dalam persen ((nilai-acuan)/acuan*100). | - | float, None kalau acuan 0/None. |
| `tampilkan_kode` | 122 | expander berisi KODE ASLI satu fungsi/kelas (diambil dari file proyek lewat bukti_kode, bukan salinan teks) beserta nama file dan nomor barisnya. | nama file, nama fungsi/kelas, judul (opsional). | - Catatan: jangan dipanggil di dalam st.expander lain (Streamlit tidak mengizinkan expander bersarang). |
| `skill_persentase` | 133 | skill score terhadap acuan dalam persen = (1 - RMSE_model / RMSE_acuan) x 100. Positif = model lebih baik dari acuan; 0 = sama; negatif = lebih buruk. | - | float atau None. |
| `tabel_semua_model` | 143 | satu tabel datar berisi semua model dan baseline (dibaca dari hasil.json) untuk dipakai berbagai halaman. | dict hasil.json. | list of dict dengan kunci: kunci, nama, mode ('A'/'B'/'-'), jenis ('Model'/'Baseline'), rmse, mae, medae, r2, cv_rmse, cv_std, ukuran_mb, waktu_latih, waktu_... |
| `_baca_prediksi` | 165 | baca prediksi_uji.csv dengan cache. | path (str), mtime. | DataFrame. |
| `muat_prediksi_uji` | 171 | baca artifacts/prediksi_uji.csv (prediksi semua model dan baseline di data uji; cache, segar kalau file berubah). | - | DataFrame, atau None kalau file belum ada. |
| `_paket_cache` | 181 | muat satu model dengan st.cache_resource (kunci cache memuat mtime). | kunci model, mtime. | dict paket atau None. |
| `muat_paket` | 186 | baca satu model terlatih dengan cache (st.cache_resource; segar kalau file berubah). | kunci model. | dict paket model, atau None kalau file .joblib belum ada. Juga menampilkan peringatan kalau versi scikit-learn berbeda. |
| `data_siap` | 202 | data mentah + semua fitur (fitur_waktu.siapkan_data), cache. | - | DataFrame. |


## alat/ : tes dan pembaruan dokumen

### `alat/buat_kamus_fungsi.py`

buat_kamus_fungsi.py - membuat dokumen/KAMUS_FUNGSI.md OTOMATIS dari kode: semua file, semua fungsi/kelas, nomor barisnya, dan penjelasan singkatnya (diambil dari docstring "Fungsi: ... Input: ... Output: ...").

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `_pisah_docstring` | 21 | pecah docstring bergaya proyek menjadi bagian Fungsi / Input / Output. | teks docstring (atau None). | dict {'Fungsi','Input','Output'} (string, bisa kosong). Docstring tanpa pola ini dimasukkan semua ke 'Fungsi'. |
| `_ringkas` | 41 | potong teks panjang untuk sel tabel dan ganti karakter / agar tabel markdown tidak rusak. | teks, maks panjang. | str. |
| `_baris_fungsi` | 47 | ubah satu node fungsi/kelas ast menjadi baris kamus (nama, baris, fungsi, input, output). | node ast, awalan nama (untuk metode kelas). | dict. |
| `kumpulkan` | 54 | telusuri semua file .py proyek lewat ast. | - | list of dict {folder, berkas, ringkasan_file, daftar:[...]}, daftar berisi fungsi dan kelas (beserta metodenya) dengan nomor baris dan penjelasan. |
| `susun_markdown` | 79 | ubah hasil kumpulkan() menjadi teks markdown. | list dari kumpulkan(). | str. |
| `tulis` | 98 | buat dan simpan dokumen/KAMUS_FUNGSI.md. | - | (path, jumlah file, jumlah fungsi tanpa docstring). |

### `alat/perbarui_panduan.py`

perbarui_panduan.py - mengisi ulang angka dan tabel di PANDUAN_HALAMAN.md dan PANDUAN_KODE.md dari artifacts/hasil.json dan CSV.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `kumpulkan_angka` | 25 | semua nilai untuk penanda ANGKA. Angka dataset dari CSV, angka fitur dari hasil.json. | dict hasil.json, DataFrame mentah. | dict {kunci: teks}. |
| `kumpulkan_blok` | 128 | isi tiap penanda BLOK. | dict hasil.json. | dict {nama: teks markdown}. |
| `isi_ulang` | 139 | ganti isi semua penanda. | teks markdown, dict angka, dict blok. | (teks baru, jumlah diganti). Error (SystemExit) kalau ada kunci penanda yang tidak dikenal. |
| `main` | 165 | baca hasil.json + CSV, isi ulang PANDUAN_HALAMAN.md. | - | - |

### `alat/uji_cepat.py`

uji_cepat.py - jalankan SEBELUM training penuh: python -m alat.uji_cepat Memeriksa: (1) data terbaca, (2) batas kategori udara, (3) tidak ada kebocoran masa depan di fitur lag/rolling, (4) buat_baris_fitur (dipakai halaman Prediksi) sama persis dengan fitur untuk training, (5) alur latih lengkap di data kecil (2.000 baris) -> artifacts_dummy/ (DUMMY, bukan hasil asli). Kalau semua lolos, tercetak: UJI CEPAT LULUS.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `cek` | 22 | catat hasil satu pengecekan. | nama, kondisi (bool), rinci (teks). | - |
| `uji_data` | 29 | cek dataset. | - | DataFrame mentah. |
| `uji_kategori` | 40 | cek batas kategori AQI 2024 (nilai batas, antar batas, dan pemotongan 1 desimal). | - | - |
| `uji_kebocoran` | 52 | pastikan fitur di jam t TIDAK berubah kalau nilai PM2.5 jam >= t diubah (tidak mengintip masa depan). | - | - |
| `uji_baris_fitur` | 71 | buat_baris_fitur (halaman Prediksi) harus sama dengan fitur vektor untuk training. | - | - |
| `uji_alur_latih` | 92 | jalankan latih_semua_model --cepat --sampel 2000 --ulang dan cek keluarannya (artifacts_dummy/). | - | - |

### `alat/uji_halaman.py`

uji_halaman.py - uji asap tiap halaman tanpa membuka browser (streamlit.testing.v1.AppTest). Jalankan: python -m alat.uji_halaman (memakai artifacts/ asli) python -m alat.uji_halaman --dummy (memakai artifacts_dummy/, untuk menguji tampilan sebelum training selesai) Lulus = tidak ada exception di halaman manapun.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `uji_satu` | 22 | jalankan satu halaman dan kembalikan daftar exception. | path file. | list str. |


## halaman/ : halaman web

### `halaman/01_beranda.py`

halaman/01_beranda.py - Beranda: KPI, alur kerja, ringkasan temuan (dari hasil.json), identitas kelompok.

### `halaman/02_tentang_dataset.py`

halaman/02_tentang_dataset.py - kamus 13 kolom, rentang waktu & kualitas data, data kosong, glosarium (tab).

### `halaman/03_eda_umum.py`

halaman/03_eda_umum.py - EDA umum: distribusi, outlier & kemiringan, korelasi, arah angin & bulan.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `korelasi` | 28 | matriks korelasi kolom numerik (cache). | 'pearson'/'spearman'. | DataFrame. |

### `halaman/04_preprocessing.py`

halaman/04_preprocessing.py - Preprocessing (lengkap). Enam tab: 1. Kolom ke fitur : tabel "Dari 13 kolom CSV ke fitur model" + pertanyaan dosen tentang jumlah fitur 2. Data kosong : ffill vs median vs interpolasi (bocor) 3. Outlier : kenapa tidak dibuang, dan bukti dari error saat polusi parah 4. Log target : hasil eksperimen, dievaluasi di skala asli 5. Split waktu dan scaling 6. Temuan EDA ke keputusan : tiap temuan EDA -> keputusan -> kode (file dan baris) + peta hasil.json ke kode

### `halaman/05_pca.py`

halaman/05_pca.py - PCA: scree plot, dengan vs tanpa PCA, SelectKBest sebagai pembanding, dan tab "Bukti dan kode".

### `halaman/06_modelling_tuning.py`

halaman/06_modelling_tuning.py - Modelling & Tuning: 5 model beserta alasannya, RF default vs RF + PSO (sebelum/sesudah tuning), validasi silang berurutan waktu, dan biaya (waktu, ukuran file).

### `halaman/07_evaluasi_interpretasi.py`

halaman/07_evaluasi_interpretasi.py - Evaluasi & Interpretasi: metrik, aktual vs prediksi, residual, error per bulan dan per kategori udara, permutation importance, dan partial dependence.

### `halaman/08_uji_kejujuran.py`

halaman/08_uji_kejujuran.py - Uji Kejujuran Model (ciri khas proyek ini).

### `halaman/09_prediksi_satu_input.py`

halaman/09_prediksi_satu_input.py - Prediksi Satu Input: gauge, kategori udara berwarna, saran kesehatan, interval ketidakpastian, dan perbandingan semua model.

### `halaman/10_prediksi_massal.py`

halaman/10_prediksi_massal.py - Prediksi Massal: unggah CSV berisi banyak jam, dapatkan prediksi tiap jam, lihat ringkasan dan unduh hasilnya.

### `halaman/11_kesimpulan_referensi.py`

halaman/11_kesimpulan_referensi.py - Kesimpulan & Referensi: temuan (dihitung dari hasil.json), keterbatasan, saran, daftar pustaka.


## halaman/tambahan/ : halaman tambahan

### `halaman/tambahan/14_whatif_simulator.py`

halaman/tambahan/14_whatif_simulator.py - What-if Simulator: geser satu variabel (suhu, titik embun, tekanan, angin, arah angin, jam, bulan, atau riwayat pm2.5) dan lihat kurva prediksi model, dengan pita warna kategori udara di latar.

| Fungsi | Baris | Fungsinya apa | Input | Output |
|---|---|---|---|---|
| `rentang` | 39 | rentang slider dari data, persentil 1 sampai 99 (agar nilai ekstrem tidak merusak skala). | nama kolom. | (min, maks, median). |
| `prediksi` | 63 | satu prediksi untuk skenario (nilai cuaca n, arah a, jam j, bulan b, riwayat konstan r). | - | float. |

