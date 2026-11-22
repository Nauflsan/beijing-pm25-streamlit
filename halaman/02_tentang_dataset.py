"""
halaman/02_tentang_dataset.py - kamus 13 kolom, rentang waktu & kualitas data, data kosong, glosarium (tab).

Semua angka dataset dihitung dari CSV lewat utilitas_data.ringkasan_dataset (tidak ditulis tangan).
Penjelasan arti kolom ditulis tangan karena berasal dari dokumentasi dataset, bukan hasil hitung.
"""
import html

import pandas as pd
import streamlit as st

import grafik
import konfigurasi as cfg
import kategori_udara as ku
import tema_langit_beijing as tema
import utilitas_app as ua
import utilitas_data as ud

T = cfg.KOLOM_TARGET
df = ua.muat_data()
ring = ud.ringkasan_dataset(df)
kolom_asli = [c for c in df.columns if c != "waktu"]

tema.header_halaman("Tentang Dataset", f"{ua.fmt(ring['n_baris'], 0)} baris x {ring['n_kolom_asli']} kolom, per jam, "
                                       f"{ring['waktu_awal'][:10]} sampai {ring['waktu_akhir'][:10]}")

KAMUS = {   # [TERKAIT] jumlah baris harus sama dengan jumlah kolom CSV (dicek di bawah)
    "No": ("Nomor urut baris", "tanpa satuan"),
    "year": ("Tahun pengukuran", "tahun"),
    "month": ("Bulan pengukuran (1-12)", "bulan"),
    "day": ("Tanggal dalam bulan", "hari"),
    "hour": ("Jam pengukuran (0-23)", "jam"),
    "pm2.5": ("Konsentrasi partikel halus berdiameter <= 2,5 mikrometer. INI TARGET yang diprediksi", "ug/m3"),
    "DEWP": ("Titik embun (indikator kelembapan udara)", "derajat C"),
    "TEMP": ("Suhu udara", "derajat C"),
    "PRES": ("Tekanan udara", "hPa"),
    "cbwd": ("Arah angin gabungan: NE, NW, SE, atau cv (di dokumentasi dataset asli: angin tenang/berubah-ubah; cek sumber kelompok)", "kategori"),
    "Iws": ("Kecepatan angin kumulatif", "m/s"),
    "Is": ("Akumulasi jam salju", "jam"),
    "Ir": ("Akumulasi jam hujan", "jam"),
}

tab_kamus, tab_kualitas, tab_kosong, tab_glosarium = st.tabs(
    [f"Kamus {ring['n_kolom_asli']} kolom", "Rentang dan kualitas data", "Data kosong", "Glosarium"])

# ----------------------------------------------------------------------------- kamus
with tab_kamus:
    tak_ada = [c for c in kolom_asli if c not in KAMUS]
    if tak_ada:
        st.warning(f"Kolom CSV belum ada di kamus (tambahkan di halaman/02_tentang_dataset.py): {tak_ada}")
    tabel = pd.DataFrame([{"Kolom": c, "Arti": KAMUS.get(c, ("-", "-"))[0], "Satuan": KAMUS.get(c, ("-", "-"))[1],
                           "Tipe di CSV": str(df[c].dtype),
                           "Peran": "Target (Y)" if c == T else ("Fitur (lihat Preprocessing)" if c not in ("No", "year", "day") else "Bukan fitur")}
                          for c in kolom_asli])
    st.table(tabel.set_index("Kolom"))
    st.markdown("**Contoh 5 baris pertama**")
    st.dataframe(df[kolom_asli].head(), hide_index=True, width="stretch")
    st.caption("Sel pm2.5 yang kosong di baris-baris awal memang kosong di data aslinya (bukan error tampilan).")
    tema.kotak_catatan(f"Peran 'Fitur' dan 'Bukan fitur' diringkas lengkap beserta alasannya di halaman Preprocessing "
                       f"(tabel 'Dari {ring['n_kolom_asli']} kolom CSV ke fitur model').")

# ----------------------------------------------------------------------------- kualitas
with tab_kualitas:
    selisih = df["waktu"].diff().dropna()
    teratur = bool((selisih == pd.Timedelta(hours=1)).all())
    a, b, c = st.columns(3)
    with a:
        tema.kartu_kpi("Rentang waktu", f"{ring['waktu_awal'][:10]}", f"sampai {ring['waktu_akhir'][:10]}")
    with b:
        tema.kartu_kpi("Interval antar baris", "tepat 1 jam" if teratur else "TIDAK seragam",
                       "tidak ada jam yang hilang" if teratur else "ada jam yang bolong, cek data")
    with c:
        tema.kartu_kpi("Waktu ganda (duplikat)", ua.fmt(int(df["waktu"].duplicated().sum()), 0), "baris dengan waktu yang sama")
    st.write("")
    st.markdown(f"**Lokasi:** {cfg.STASIUN_CATATAN}")
    st.markdown(f"**Sumber dataset:** {cfg.SUMBER_DATASET}")
    st.markdown("**Ringkasan statistik tiap kolom numerik**")
    num = [T] + cfg.KOLOM_CUACA_NUMERIK
    stat = pd.DataFrame({
        "min": df[num].min(), "median": df[num].median(), "rata-rata": df[num].mean(), "maks": df[num].max(),
        "skewness": df[num].skew(), "% bernilai 0": (df[num] == 0).mean() * 100}).round(2)
    st.dataframe(stat, width="stretch")
    st.caption("Skewness positif besar = ekor panjang ke kanan. '% bernilai 0' menunjukkan kolom yang hampir selalu nol "
               "(umumnya Is dan Ir).")

# ----------------------------------------------------------------------------- data kosong
with tab_kosong:
    a, b, c, d = st.columns(4)
    with a:
        tema.kartu_kpi("Jam pm2.5 kosong", ua.fmt(ring["n_kosong_target"], 0), f"{ua.fmt(ring['persen_kosong_target'], 2)}% dari semua jam")
    with b:
        tema.kartu_kpi("Kosong di kolom lain", ua.fmt(ring["kosong_kolom_lain"], 0), "hanya pm2.5 yang berlubang" if ring["kosong_kolom_lain"] == 0 else "ada kolom lain yang berlubang")
    with c:
        tema.kartu_kpi("Kekosongan berurutan terpanjang", f"{ring['panjang_kosong_terpanjang_jam']} jam", "deret kosong tanpa putus")
    with d:
        awal = int(df[T].isna().to_numpy()[: 24].sum())
        tema.kartu_kpi("Kosong di 24 jam pertama", f"{awal} dari 24", "belum ada riwayat yang bisa dipakai")
    st.write("")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Jam kosong per tahun**")
        st.altair_chart(grafik.altair_kosong_per_tahun(df), width="stretch")
    with g2:
        st.markdown("**Jam kosong menurut jam dalam sehari**")
        st.altair_chart(grafik.altair_kosong_per_jam(df), width="stretch")
    st.markdown("**Cara proyek ini menanganinya** (detail dan perbandingan di halaman Preprocessing)")
    st.markdown(
        "- Baris yang pm2.5-nya kosong **tidak dipakai sebagai target** latih maupun uji, supaya model tidak belajar dari angka karangan.\n"
        "- Untuk membentuk fitur riwayat (lag dan rata-rata bergulir) nilai kosong diisi dengan nilai terakhir yang diketahui "
        "(*forward fill*), yang hanya memakai masa lalu.\n"
        "- Baris awal yang riwayatnya belum lengkap dibuang, bukan diisi dengan nilai dari masa depan.")

# ----------------------------------------------------------------------------- glosarium
with tab_glosarium:
    st.markdown("**Kategori kualitas udara (AQI PM2.5, US EPA)**")
    baris = ""
    for k in ku.tabel_ambang():
        batas = f"{ua.fmt(k['batas_bawah'], 1)} sampai {ua.fmt(k['batas_atas'], 1)}" if k["batas_atas"] is not None else f"{ua.fmt(k['batas_bawah'], 1)} ke atas"
        baris += (f"<tr><td style='background:{k['warna']};color:{tema.warna_teks_kontras(k['warna'])};font-weight:700;'>"
                  f"{html.escape(k['nama'])}</td><td>{batas}</td><td>{html.escape(k['saran'])}</td></tr>")
    st.markdown(f"<table style='width:100%;border-collapse:collapse;'><thead><tr><th>Kategori</th><th>pm2.5 (ug/m3)</th>"
                f"<th>Ringkasan saran</th></tr></thead><tbody>{baris}</tbody></table>", unsafe_allow_html=True)
    st.caption(f"Ambang versi {cfg.VERSI_AMBANG_AKTIF}. Sumber: {cfg.SUMBER_AMBANG} (diakses {cfg.TANGGAL_AKSES_SUMBER}). {cfg.CATATAN_AMBANG}")
    st.write("")
    istilah = [
        ("PM2.5", "Partikel udara berdiameter 2,5 mikrometer atau lebih kecil, cukup kecil untuk masuk jauh ke paru-paru. Satuan ug/m3."),
        ("MAE", "Mean Absolute Error: rata-rata selisih mutlak prediksi dan kenyataan. Satuannya sama dengan pm2.5, mudah dibaca: 'rata-rata meleset sekian ug/m3'."),
        ("RMSE", "Akar rata-rata kuadrat selisih. Lebih 'marah' pada kesalahan besar, jadi berguna untuk melihat meleset saat polusi parah."),
        ("MedAE", "Median selisih mutlak: kesalahan 'tipikal' yang tidak terseret lonjakan ekstrem."),
        ("R2", "Berapa bagian variasi data yang dijelaskan model (1 = sempurna, 0 = tidak lebih baik dari menebak rata-rata, bisa negatif). "
               "R2 tinggi belum tentu berarti berguna; lihat halaman Uji Kejujuran Model."),
        ("Baseline persistence", "Tebakan paling sederhana: nilai jam lalu (atau kemarin) dipakai sebagai prediksi. Model harus mengalahkan ini agar layak dipakai."),
        ("Lag dan rata-rata bergulir", "Nilai PM2.5 beberapa jam sebelumnya, dan rata-rata beberapa jam terakhir. Dipakai di Mode B."),
        ("Split waktu", "Membagi data berdasarkan urutan waktu: latih di masa lalu, uji di masa depan. Berbeda dengan split acak yang mencampur jam-jam bertetangga."),
        ("Data bocor (data leakage)", "Informasi dari data uji atau masa depan yang ikut masuk saat latih sehingga hasil terlihat lebih bagus dari kenyataan."),
        ("PSO", "Particle Swarm Optimization: banyak 'partikel' mencari kombinasi hyperparameter terbaik dengan saling meniru posisi terbaik."),
    ]
    st.table(pd.DataFrame(istilah, columns=["Istilah", "Arti"]).set_index("Istilah"))
