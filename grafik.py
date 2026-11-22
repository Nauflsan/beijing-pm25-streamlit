"""
grafik.py - fungsi pembuat grafik (Plotly dan Altair) yang dipakai halaman. Fungsi hanya MEMBUAT figur; menampilkannya
(st.plotly_chart / st.altair_chart) dilakukan di halaman. Tidak mengimpor streamlit.

GOTCHA Altair: nama kolom 'pm2.5' mengandung titik, Altair/Vega-Lite menganggapnya properti bersarang sehingga grafik
kosong. Jadi untuk Altair selalu pakai salinan kolom 'pm25' (utilitas_data.tambah_kolom_altair) dan beri judul sumbu "pm2.5".
Plotly tidak bermasalah dengan titik.
"""
import altair as alt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import konfigurasi as cfg
import kategori_udara as ku

T = cfg.KOLOM_TARGET
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
LABEL_PM = "pm2.5 (ug/m3)"


def rapikan(fig, tinggi=380, judul=None):
    """Fungsi: gaya seragam Plotly (latar transparan agar cocok mode terang/gelap, font tema). Input: fig. Output: fig."""
    fig.update_layout(title=judul, height=tinggi, margin=dict(l=10, r=10, t=50 if judul else 20, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=f"{cfg.FONT_ISI}, sans-serif", color=cfg.WARNA_TEKS), colorway=cfg.WARNA_SERI,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    fig.update_xaxes(gridcolor=cfg.WARNA_GARIS)
    fig.update_yaxes(gridcolor=cfg.WARNA_GARIS)
    return fig


def histogram_target(df, skala_log=False, batas=200):
    """
    Fungsi: histogram PM2.5. Input: df (ada kolom 'pm2.5'), skala_log (sumbu y log), batas (nilai terbesar yang digambar
            supaya ekor panjang tidak menggencet grafik; 0 = semua). Output: fig Plotly.
    """
    nilai = df[T].dropna()
    if batas:
        nilai = nilai[nilai <= batas]
    fig = px.histogram(x=nilai, nbins=60, color_discrete_sequence=[cfg.WARNA_NETRAL], labels={"x": LABEL_PM})
    fig.update_layout(bargap=0.03, yaxis_title="Jumlah jam", xaxis_title=LABEL_PM)
    if skala_log:
        fig.update_yaxes(type="log")
    return rapikan(fig)


def bar_kategori(jumlah_per_kategori):
    """
    Fungsi: bar proporsi jam per kategori udara, warna = warna kategori. Input: list 6 angka (jumlah jam per kategori,
            urut Baik..Berbahaya). Output: fig Plotly.
    """
    total = float(sum(jumlah_per_kategori)) or 1.0
    persen = [100 * v / total for v in jumlah_per_kategori]
    fig = go.Figure(go.Bar(x=cfg.NAMA_KATEGORI_PENDEK, y=persen, marker_color=cfg.WARNA_KATEGORI,
                           marker_line_color="rgba(128,128,128,.6)", marker_line_width=1,
                           text=[f"{p:.1f}%".replace(".", ",") for p in persen], textposition="outside"))
    fig.update_layout(yaxis_title="Persen jam (%)", xaxis_title="Kategori kualitas udara", showlegend=False)
    fig.update_yaxes(range=[0, max(persen) * 1.18])
    return rapikan(fig)


def box_per_kelompok(df, kolom_kelompok, urutan=None, batas=None):
    """Fungsi: boxplot PM2.5 per kelompok (mis. arah angin). Input: df, kolom_kelompok, urutan (list), batas (potong sumbu y). Output: fig."""
    d = df[[T, kolom_kelompok]].dropna()
    fig = px.box(d, x=kolom_kelompok, y=T, category_orders={kolom_kelompok: urutan} if urutan else None,
                 color_discrete_sequence=[cfg.WARNA_NETRAL], labels={T: LABEL_PM})
    if batas:
        fig.update_yaxes(range=[0, batas])
    return rapikan(fig)


def box_target(nilai):
    """Fungsi: boxplot horizontal PM2.5 (satu kotak). Input: Series PM2.5 tanpa NaN. Output: fig Plotly."""
    fig = px.box(x=nilai, labels={"x": LABEL_PM}, color_discrete_sequence=[cfg.WARNA_NETRAL])
    fig.update_layout(xaxis_title=LABEL_PM)
    return rapikan(fig, tinggi=240)


def heatmap_korelasi(matriks):
    """Fungsi: heatmap korelasi. Input: DataFrame korelasi persegi. Output: fig Plotly (skala -1..1, merah-biru)."""
    fig = px.imshow(matriks, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto")
    fig.update_layout(coloraxis_colorbar=dict(title="r"))
    return rapikan(fig, tinggi=460)


def bar_korelasi_target(seri):
    """Fungsi: bar korelasi tiap fitur dengan target, urut besar-kecil. Input: Series (index = nama fitur). Output: fig."""
    s = seri.sort_values()
    warna = [cfg.WARNA_SERI[4] if v < 0 else cfg.WARNA_SERI[0] for v in s.values]
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h", marker_color=warna,
                           text=[f"{v:.2f}".replace(".", ",") for v in s.values], textposition="outside"))
    fig.update_layout(xaxis_title="Korelasi dengan pm2.5", showlegend=False)
    fig.update_xaxes(range=[min(-0.05, s.min() * 1.3), max(0.05, s.max() * 1.3)])
    return rapikan(fig, tinggi=340)


# ----------------------------------------------------------------------------- Altair
def altair_rata_bulanan(df_altair):
    """
    Fungsi: bar rata-rata PM2.5 per bulan kalender. Input: DataFrame yang SUDAH punya kolom 'pm25' (salinan 'pm2.5').
    Output: grafik Altair. Judul sumbu tetap 'pm2.5'.
    """
    rata = df_altair.groupby("month", as_index=False)[cfg.KOLOM_TARGET_ALTAIR].mean()
    rata["bulan"] = [BULAN[m - 1] for m in rata["month"]]
    return (alt.Chart(rata).mark_bar(color=cfg.WARNA_NETRAL, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(x=alt.X("bulan:N", sort=BULAN, title="Bulan"),
                    y=alt.Y(f"{cfg.KOLOM_TARGET_ALTAIR}:Q", title="Rata-rata pm2.5 (ug/m3)"),
                    tooltip=[alt.Tooltip("bulan:N", title="Bulan"),
                             alt.Tooltip(f"{cfg.KOLOM_TARGET_ALTAIR}:Q", title="Rata-rata pm2.5", format=".1f")])
            .properties(height=320))


def altair_kosong_per_tahun(df):
    """Fungsi: bar jumlah jam PM2.5 kosong per tahun. Input: df mentah (kolom year, pm2.5). Output: grafik Altair."""
    k = (df.assign(kosong=df[T].isna().astype(int)).groupby("year", as_index=False)["kosong"].sum())
    return (alt.Chart(k).mark_bar(color=cfg.WARNA_SERI[1], cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(x=alt.X("year:O", title="Tahun"), y=alt.Y("kosong:Q", title="Jam dengan pm2.5 kosong"),
                    tooltip=[alt.Tooltip("year:O", title="Tahun"), alt.Tooltip("kosong:Q", title="Jam kosong")])
            .properties(height=300))


def altair_kosong_per_jam(df):
    """Fungsi: bar jumlah PM2.5 kosong per jam dalam sehari (0-23). Input: df mentah. Output: grafik Altair."""
    k = (df.assign(kosong=df[T].isna().astype(int)).groupby("hour", as_index=False)["kosong"].sum())
    return (alt.Chart(k).mark_bar(color=cfg.WARNA_SERI[2], cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(x=alt.X("hour:O", title="Jam dalam sehari"), y=alt.Y("kosong:Q", title="Jam dengan pm2.5 kosong"),
                    tooltip=[alt.Tooltip("hour:O", title="Jam"), alt.Tooltip("kosong:Q", title="Jam kosong")])
            .properties(height=300))


def jumlah_per_kategori(nilai):
    """Fungsi: hitung jumlah jam per kategori udara dari deret PM2.5. Input: Series/array (tanpa NaN). Output: list 6 int."""
    idx = ku.indeks_kategori(np.asarray(nilai, dtype=float))
    return [int((idx == i).sum()) for i in range(len(cfg.NAMA_KATEGORI))]
