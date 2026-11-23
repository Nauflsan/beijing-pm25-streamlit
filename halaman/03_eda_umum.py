"""
halaman/03_eda_umum.py - EDA umum: distribusi, outlier & kemiringan, korelasi, arah angin & bulan.

Semua angka dihitung dari CSV. Kalimat interpretasi dibuat dari angka itu (bukan teks tetap), supaya tidak
keliru kalau data diganti.
"""
import pandas as pd
import streamlit as st

from tampilan import grafik
import konfigurasi as cfg
from evaluasi import kategori_udara as ku
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua
from preprocessing import utilitas_data as ud

T = cfg.KOLOM_TARGET
df = ua.muat_data()
valid = df[T].dropna()
ring = ud.ringkasan_dataset(df)

tema.header_halaman("EDA Umum", "Seperti apa sebaran PM2.5, mana yang ekstrem, dan variabel apa yang berhubungan dengannya.")

tab_dist, tab_out, tab_kor, tab_arah = st.tabs(["Distribusi", "Outlier dan kemiringan", "Korelasi", "Arah angin dan bulan"])


@st.cache_data(show_spinner=False)
def korelasi(metode):
    """Fungsi: matriks korelasi kolom numerik (cache). Input: 'pearson'/'spearman'. Output: DataFrame."""
    kolom = [T] + cfg.KOLOM_CUACA_NUMERIK
    return df[kolom].corr(method=metode)


# ----------------------------------------------------------------------------- distribusi
with tab_dist:
    a, b, c, d = st.columns(4)
    with a:
        tema.kartu_kpi("Rata-rata", f"{ua.fmt(ring['pm25_mean'], 1)}", "ug/m3", ku.indeks_kategori(ring["pm25_mean"]))
    with b:
        tema.kartu_kpi("Median", f"{ua.fmt(ring['pm25_median'], 1)}", "ug/m3", ku.indeks_kategori(ring["pm25_median"]))
    with c:
        tema.kartu_kpi("Skewness", ua.fmt(ring["pm25_skew"], 2), "positif = ekor panjang ke kanan")
    with d:
        tema.kartu_kpi("Nilai maksimum", ua.fmt(ring["pm25_max"], 0), "ug/m3", ku.indeks_kategori(ring["pm25_max"]))
    st.write("")
    arah = "lebih besar dari" if ring["pm25_mean"] > ring["pm25_median"] else "tidak lebih besar dari"
    st.markdown(f"Rata-rata ({ua.fmt(ring['pm25_mean'], 1)}) {arah} median ({ua.fmt(ring['pm25_median'], 1)}) dan skewness "
                f"{ua.fmt(ring['pm25_skew'], 2)}. " + ("Artinya sebagian besar jam bernilai rendah-sedang, sedangkan sejumlah kecil jam "
                "bernilai sangat tinggi menarik rata-rata ke atas." if ring["pm25_skew"] > 1 else "Sebaran relatif simetris."))
    k1, k2 = st.columns([3, 1])
    with k2:
        skala_log = st.toggle("Sumbu jumlah skala log", value=False, help="Skala log membuat ekor kanan yang jarang terlihat jelas.")
        batas = st.slider("Potong tampilan di (ug/m3)", 100, int(ring["pm25_max"]), 300, step=50,
                          help="Hanya untuk tampilan grafik; data tidak dibuang.")
    with k1:
        st.plotly_chart(grafik.histogram_target(df, skala_log=skala_log, batas=batas), width="stretch")
    st.markdown("**Proporsi jam menurut kategori kualitas udara**")
    st.plotly_chart(grafik.bar_kategori(grafik.jumlah_per_kategori(valid)), width="stretch")
    st.caption(f"Ambang AQI versi {cfg.VERSI_AMBANG_AKTIF} ({cfg.TANGGAL_AKSES_SUMBER}). {cfg.CATATAN_AMBANG}")

# ----------------------------------------------------------------------------- outlier
with tab_out:
    a, b, c = st.columns(3)
    with a:
        tema.kartu_kpi("Batas outlier (aturan IQR)", f"{ua.fmt(ring['batas_outlier_iqr'], 0)}", "Q3 + 1,5 x IQR, ug/m3")
    with b:
        tema.kartu_kpi("Jam di atas batas", ua.fmt(ring["n_outlier_iqr"], 0), f"{ua.fmt(100 * ring['n_outlier_iqr'] / len(valid), 2)}% dari jam bernilai")
    with c:
        tema.kartu_kpi("Skewness pm2.5", ua.fmt(ring["pm25_skew"], 2), "lihat tab Distribusi")
    st.write("")
    st.markdown(f"Aturan IQR menandai {ua.fmt(ring['n_outlier_iqr'], 0)} jam. Titik-titik ini berada di ekor kanan sebaran, "
                "bukan terpencil sendiri; kemungkinan besar kejadian polusi nyata dan bukan salah ukur (dugaan, belum diverifikasi "
                "ke sumber data). Cara proyek ini memperlakukannya dibahas di halaman Preprocessing.")
    num = [T] + cfg.KOLOM_CUACA_NUMERIK
    tabel = pd.DataFrame({
        "skewness": df[num].skew(), "% bernilai 0": (df[num] == 0).mean() * 100,
        "jumlah outlier IQR": {k: int(((df[k] < df[k].quantile(.25) - 1.5 * (df[k].quantile(.75) - df[k].quantile(.25))) |
                                      (df[k] > df[k].quantile(.75) + 1.5 * (df[k].quantile(.75) - df[k].quantile(.25)))).sum()) for k in num}}).round(2)
    st.dataframe(tabel, width="stretch")
    st.caption("Is dan Ir hampir selalu 0, sehingga hampir semua nilai tidak nolnya otomatis tampil sebagai 'outlier' menurut IQR. "
               "Itu artefak aturan IQR, bukan kesalahan data.")
    st.plotly_chart(grafik.box_target(valid), width="stretch")

# ----------------------------------------------------------------------------- korelasi
with tab_kor:
    metode = st.radio("Metode korelasi", ["pearson", "spearman"], horizontal=True,
                      format_func=lambda m: "Pearson (hubungan linear)" if m == "pearson" else "Spearman (hubungan berurutan, tahan outlier)")
    mat = korelasi(metode)
    k1, k2 = st.columns([3, 2])
    with k1:
        st.plotly_chart(grafik.heatmap_korelasi(mat), width="stretch")
    with k2:
        dengan_target = mat[T].drop(T)
        st.plotly_chart(grafik.bar_korelasi_target(dengan_target), width="stretch")
    terkuat = dengan_target.abs().idxmax()
    st.markdown(f"Korelasi terkuat dengan pm2.5 menurut metode ini adalah **{terkuat}** (r = {ua.fmt(dengan_target[terkuat], 2)}). "
                + ("Semua korelasi cuaca dengan pm2.5 tergolong lemah (|r| < 0,3), jadi cuaca saja diperkirakan belum cukup "
                   "menjelaskan PM2.5; ini yang diuji lewat Mode A di halaman Modelling." if dengan_target.abs().max() < 0.3
                   else "Ada hubungan yang cukup kuat; lihat bar di samping."))
    st.caption("Korelasi hanya menangkap hubungan lurus antar dua variabel. Hubungan non-linear dan pengaruh riwayat PM2.5 "
               "(autokorelasi) tidak terlihat di sini.")

# ----------------------------------------------------------------------------- arah angin dan bulan
with tab_arah:
    k1, k2 = st.columns(2)
    with k1:
        st.markdown("**pm2.5 menurut arah angin**")
        st.plotly_chart(grafik.box_per_kelompok(df, cfg.KOLOM_ARAH_ANGIN, urutan=cfg.KELAS_ARAH_ANGIN, batas=400), width="stretch")
        ringkas = (df.groupby(cfg.KOLOM_ARAH_ANGIN)[T].agg(["count", "mean", "median"]).reindex(cfg.KELAS_ARAH_ANGIN).round(1)
                   .rename(columns={"count": "jumlah jam bernilai", "mean": "rata-rata", "median": "median"}))
        st.dataframe(ringkas, width="stretch")
        st.caption("Sumbu boxplot dipotong di 400 hanya untuk tampilan.")
    with k2:
        st.markdown("**Rata-rata pm2.5 per bulan**")
        st.altair_chart(grafik.altair_rata_bulanan(ud.tambah_kolom_altair(df)), width="stretch")
        rb = df.groupby("month")[T].mean()
        st.caption(f"Tertinggi bulan {grafik.BULAN[int(rb.idxmax()) - 1]} ({ua.fmt(rb.max(), 1)}), "
                   f"terendah bulan {grafik.BULAN[int(rb.idxmin()) - 1]} ({ua.fmt(rb.min(), 1)}). "
                   "Pola jam x bulan yang lebih rinci ada di halaman Pola Waktu dan Cuaca.")
