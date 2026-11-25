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
from plotly.subplots import make_subplots

import konfigurasi as cfg
from evaluasi import kategori_udara as ku

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


# ----------------------------------------------------------------------------- PCA / preprocessing
def scree_plot(scree, kumulatif, ambang=(0.80, 0.90, 0.95, 0.99)):
    """
    Fungsi: scree plot PCA: bar = varians tiap komponen, garis = varians kumulatif, garis putus = ambang.
    Input : scree (list proporsi varians per komponen), kumulatif (list), ambang (tuple). Output: fig Plotly.
    """
    x = list(range(1, len(scree) + 1))
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=x, y=[100 * v for v in scree], name="Varians per komponen", marker_color=cfg.WARNA_SERI[0], secondary_y=False)
    fig.add_scatter(x=x, y=[100 * v for v in kumulatif], name="Kumulatif", mode="lines+markers",
                    line=dict(color=cfg.WARNA_SERI[1], width=3), secondary_y=True)
    for a in ambang:
        fig.add_hline(y=100 * a, line_dash="dot", line_color="rgba(91,107,124,.7)", secondary_y=True,
                      annotation_text=f"{int(a * 100)}%", annotation_position="bottom right")
    fig.update_xaxes(title="Komponen utama ke-", dtick=1)
    fig.update_yaxes(title="Varians per komponen (%)", secondary_y=False)
    fig.update_yaxes(title="Kumulatif (%)", range=[0, 102], secondary_y=True)
    return rapikan(fig, tinggi=400)


def bar_metode(nama, rmse, warna, acuan=None, judul_x="RMSE di data uji (ug/m3)"):
    """
    Fungsi: bar horizontal membandingkan RMSE beberapa metode. Input: nama (list), rmse (list), warna (list hex),
            acuan (nilai RMSE acuan untuk garis putus, opsional). Output: fig Plotly.
    """
    fig = go.Figure(go.Bar(x=rmse, y=nama, orientation="h", marker_color=warna,
                           text=[f"{v:.2f}".replace(".", ",") for v in rmse], textposition="outside"))
    if acuan is not None:
        fig.add_vline(x=acuan, line_dash="dot", line_color="rgba(31,45,61,.6)")
    fig.update_layout(xaxis_title=judul_x, showlegend=False, yaxis=dict(autorange="reversed"))
    fig.update_xaxes(range=[min(0, min(rmse) * 1.25), max(rmse) * 1.15])   # nilai negatif (mis. R2) tetap terlihat
    return rapikan(fig, tinggi=max(260, 44 * len(nama) + 90))


def bar_berkelompok(kategori, seri, judul_y="RMSE (ug/m3)"):
    """
    Fungsi: bar berkelompok. Input: kategori (list label sumbu x), seri {nama_seri: list nilai sesuai kategori}.
    Output: fig Plotly.
    """
    fig = go.Figure()
    for i, (nama, nilai) in enumerate(seri.items()):
        fig.add_bar(name=nama, x=kategori, y=nilai, marker_color=cfg.WARNA_SERI[i % len(cfg.WARNA_SERI)],
                    text=[f"{v:.2f}".replace(".", ",") for v in nilai], textposition="outside")
    fig.update_layout(barmode="group", yaxis_title=judul_y)
    return rapikan(fig)


def lipatan_waktu(per_fold, n_latih_total, n_uji):
    """
    Fungsi: gambar TimeSeriesSplit: tiap lipatan = jendela latih (membesar) lalu validasi, lalu blok uji akhir.
    Input : per_fold (list dict n_latih, n_valid dari hasil.json), n_latih_total, n_uji. Output: fig Plotly.
    """
    fig = go.Figure()
    nama_fold = [f"Lipatan {i + 1}" for i in range(len(per_fold))]
    fig.add_bar(y=nama_fold, x=[f["n_latih"] for f in per_fold], orientation="h", name="Latih", marker_color=cfg.WARNA_SERI[0])
    fig.add_bar(y=nama_fold, x=[f["n_valid"] for f in per_fold], orientation="h", name="Validasi", marker_color=cfg.WARNA_SERI[1])
    fig.add_bar(y=["Final"], x=[n_latih_total], orientation="h", name="Latih (semua)", marker_color=cfg.WARNA_SERI[0], showlegend=False)
    fig.add_bar(y=["Final"], x=[n_uji], orientation="h", name="Uji", marker_color=cfg.WARNA_SERI[3])
    fig.update_layout(barmode="stack", xaxis_title="Jumlah baris (urut waktu, kiri = lama, kanan = baru)",
                      yaxis=dict(autorange="reversed"))
    return rapikan(fig, tinggi=330)


# ----------------------------------------------------------------------------- Modelling / Evaluasi / Uji kejujuran
def garis_konvergensi(riwayat, nama_y="RMSE CV terbaik (sampel PSO)"):
    """Fungsi: kurva konvergensi PSO. Input: riwayat gbest per iterasi (iterasi 0 = inisialisasi). Output: fig Plotly."""
    fig = go.Figure(go.Scatter(x=list(range(len(riwayat))), y=riwayat, mode="lines+markers",
                               line=dict(color=cfg.WARNA_SERI[0], width=3)))
    fig.update_layout(xaxis_title="Iterasi (0 = inisialisasi acak)", yaxis_title=nama_y, showlegend=False)
    fig.update_xaxes(dtick=1)
    return rapikan(fig, tinggi=320)


def bar_cv_per_lipatan(seri, judul_y="RMSE validasi (ug/m3)"):
    """
    Fungsi: RMSE tiap lipatan validasi silang per model. Input: seri {nama: [rmse lipatan 1, 2, ...]}. Output: fig Plotly.
    """
    fig = go.Figure()
    for i, (nama, nilai) in enumerate(seri.items()):
        fig.add_bar(name=nama, x=[f"Lipatan {j + 1}" for j in range(len(nilai))], y=nilai,
                    marker_color=cfg.WARNA_SERI[i % len(cfg.WARNA_SERI)])
    fig.update_layout(barmode="group", yaxis_title=judul_y)
    return rapikan(fig, tinggi=360)


def scatter_aktual_prediksi(aktual, prediksi, nama_model, maks_titik=3000, seed=42):
    """
    Fungsi: sebar aktual vs prediksi + garis ideal (y = x). Input: aktual, prediksi (array), nama_model, maks_titik (sampel
            acak agar ringan). Output: fig Plotly.
    """
    n = len(aktual)
    idx = np.random.RandomState(seed).choice(n, size=min(maks_titik, n), replace=False)
    a, p = np.asarray(aktual)[idx], np.asarray(prediksi)[idx]
    batas = float(max(a.max(), p.max()))
    fig = go.Figure()
    fig.add_scatter(x=a, y=p, mode="markers", name=nama_model, marker=dict(size=4, opacity=.45, color=cfg.WARNA_SERI[0]))
    fig.add_scatter(x=[0, batas], y=[0, batas], mode="lines", name="Ideal (prediksi = aktual)",
                    line=dict(color=cfg.WARNA_SERI[4], dash="dash"))
    fig.update_layout(xaxis_title="Aktual pm2.5 (ug/m3)", yaxis_title="Prediksi pm2.5 (ug/m3)")
    return rapikan(fig, tinggi=420)


def garis_waktu(df, kolom, nama):
    """
    Fungsi: garis waktu aktual vs beberapa prediksi. Input: df (kolom 'waktu', 'aktual', dan kolom prediksi), kolom (list nama
            kolom yang digambar), nama (dict kolom -> label). Output: fig Plotly.
    """
    fig = go.Figure()
    fig.add_scatter(x=df["waktu"], y=df["aktual"], name="Aktual", mode="lines", line=dict(color="#1F2D3D", width=2))
    for i, k in enumerate(kolom):
        fig.add_scatter(x=df["waktu"], y=df[k], name=nama.get(k, k), mode="lines",
                        line=dict(color=cfg.WARNA_SERI[(i + 1) % len(cfg.WARNA_SERI)], width=1.6))
    fig.update_layout(yaxis_title="pm2.5 (ug/m3)", xaxis_title="Waktu")
    return rapikan(fig, tinggi=380)


def histogram_residual(residual):
    """Fungsi: histogram residual (aktual - prediksi). Input: array residual. Output: fig Plotly."""
    fig = px.histogram(x=residual, nbins=70, color_discrete_sequence=[cfg.WARNA_SERI[0]])
    fig.add_vline(x=0, line_dash="dash", line_color=cfg.WARNA_SERI[4])
    fig.update_layout(xaxis_title="Residual = aktual - prediksi (ug/m3)", yaxis_title="Jumlah jam", bargap=0.02)
    return rapikan(fig, tinggi=330)


def scatter_residual(prediksi, residual, maks_titik=3000, seed=42):
    """Fungsi: residual terhadap nilai prediksi (melihat apakah galat membesar saat prediksi tinggi). Output: fig Plotly."""
    n = len(prediksi)
    idx = np.random.RandomState(seed).choice(n, size=min(maks_titik, n), replace=False)
    fig = go.Figure(go.Scatter(x=np.asarray(prediksi)[idx], y=np.asarray(residual)[idx], mode="markers",
                               marker=dict(size=4, opacity=.45, color=cfg.WARNA_SERI[2])))
    fig.add_hline(y=0, line_dash="dash", line_color=cfg.WARNA_SERI[4])
    fig.update_layout(xaxis_title="Prediksi pm2.5 (ug/m3)", yaxis_title="Residual (ug/m3)")
    return rapikan(fig, tinggi=330)


def bar_per_bulan(per_bulan, metrik="mae"):
    """Fungsi: bar error per bulan. Input: dict {bulan: {mae, rmse, ...}} dari hasil.json, metrik. Output: fig Plotly."""
    bulan = sorted(int(b) for b in per_bulan)
    nilai = [per_bulan[str(b)][metrik] for b in bulan]
    fig = go.Figure(go.Bar(x=[BULAN[b - 1] for b in bulan], y=nilai, marker_color=cfg.WARNA_SERI[0],
                           text=[f"{v:.1f}".replace(".", ",") for v in nilai], textposition="outside"))
    fig.update_layout(yaxis_title=f"{metrik.upper()} (ug/m3)", showlegend=False)
    fig.update_yaxes(range=[0, max(nilai) * 1.18])
    return rapikan(fig, tinggi=330)


def bar_per_kategori(per_kategori, metrik="mae"):
    """
    Fungsi: bar error per kategori udara AKTUAL, warna = warna kategori. Input: dict {nama_pendek: {n, mae, rmse, bias}},
            metrik ('mae', 'rmse', atau 'bias'). Output: fig Plotly.
    """
    nama = [n for n in cfg.NAMA_KATEGORI_PENDEK if n in per_kategori]
    warna = [cfg.WARNA_KATEGORI[cfg.NAMA_KATEGORI_PENDEK.index(n)] for n in nama]
    nilai = [per_kategori[n][metrik] for n in nama]
    fig = go.Figure(go.Bar(x=nama, y=nilai, marker_color=warna, marker_line_color="rgba(91,107,124,.7)", marker_line_width=1,
                           text=[f"{v:.1f}".replace(".", ",") for v in nilai], textposition="outside",
                           customdata=[per_kategori[n]["n"] for n in nama],
                           hovertemplate="%{x}<br>" + metrik.upper() + " %{y:.1f}<br>n = %{customdata} jam<extra></extra>"))
    fig.update_layout(yaxis_title=f"{metrik.upper()} (ug/m3)", xaxis_title="Kategori udara aktual", showlegend=False)
    lo, hi = min(0, min(nilai) * 1.3), max(nilai) * 1.2
    fig.update_yaxes(range=[lo, hi])
    return rapikan(fig, tinggi=340)


def bar_importance(tabel, n=10):
    """Fungsi: bar permutation importance. Input: list [{fitur, naik_rmse, std}] urut terpenting. Output: fig Plotly."""
    t = tabel[:n][::-1]
    fig = go.Figure(go.Bar(x=[x["naik_rmse"] for x in t], y=[x["fitur"] for x in t], orientation="h",
                           error_x=dict(type="data", array=[x["std"] for x in t]), marker_color=cfg.WARNA_SERI[0]))
    fig.update_layout(xaxis_title="Kenaikan RMSE saat kolom diacak (ug/m3)", showlegend=False)
    return rapikan(fig, tinggi=max(280, 34 * len(t) + 90))


def garis_parsial(grid, rata, nama_fitur):
    """Fungsi: kurva partial dependence satu fitur. Input: grid (nilai fitur), rata (rata prediksi), nama_fitur. Output: fig."""
    fig = go.Figure(go.Scatter(x=grid, y=rata, mode="lines+markers", line=dict(color=cfg.WARNA_SERI[1], width=3)))
    fig.update_layout(xaxis_title=nama_fitur, yaxis_title="Rata-rata prediksi pm2.5 (ug/m3)", showlegend=False)
    return rapikan(fig, tinggi=280)


# ----------------------------------------------------------------------------- prediksi
def _rgba(hex_warna, alpha):
    """Fungsi: warna hex jadi rgba transparan. Input: '#RRGGBB', alpha. Output: str."""
    h = hex_warna.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def _pita_kategori():
    """Batas [bawah, atas] tiap kategori udara (atas kategori terakhir = None) sesuai versi ambang aktif."""
    atas = list(cfg.AMBANG_BATAS_ATAS[cfg.VERSI_AMBANG_AKTIF])
    bawah = [0.0] + atas
    return [(b, a) for b, a in zip(bawah, atas + [None])]


def gauge_pm25(nilai, idx_kategori):
    """
    Fungsi: gauge (speedometer) prediksi pm2.5. Pita latar = enam kategori udara, jarum/bar = nilai prediksi dan berwarna
            sesuai kategorinya. Input: nilai (ug/m3), idx_kategori (0-5). Output: fig Plotly.
    """
    maks = max(300.0, nilai * 1.2)
    steps = [{"range": [b, a if a is not None else maks], "color": _rgba(w, .35)}
             for (b, a), w in zip(_pita_kategori(), cfg.WARNA_KATEGORI)]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=nilai, number={"suffix": " ug/m3", "valueformat": ".1f", "font": {"size": 44}},
        gauge={"axis": {"range": [0, maks]}, "bar": {"color": cfg.WARNA_KATEGORI[idx_kategori], "thickness": .38}, "steps": steps,
               "borderwidth": 1, "bordercolor": "rgba(91,107,124,.6)"}))
    fig.update_layout(height=300, margin=dict(l=30, r=30, t=30, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=f"{cfg.FONT_ISI}, sans-serif", color=cfg.WARNA_TEKS))
    return fig


def bar_prediksi_model(nama, nilai, aktual=None):
    """
    Fungsi: bar prediksi tiap model, warna = kategori hasil prediksinya; garis putus = nilai aktual (kalau ada).
    Input : nama (list), nilai (list), aktual (float atau None). Output: fig Plotly.
    """
    warna = [cfg.WARNA_KATEGORI[ku.indeks_kategori(v)] for v in nilai]
    fig = go.Figure(go.Bar(x=nilai, y=nama, orientation="h", marker_color=warna, marker_line_color="rgba(91,107,124,.7)",
                           marker_line_width=1, text=[f"{v:.1f}".replace(".", ",") for v in nilai], textposition="outside"))
    if aktual is not None:
        fig.add_vline(x=aktual, line_dash="dash", line_color="#1F2D3D",
                      annotation_text=f"aktual {aktual:.1f}".replace(".", ","), annotation_position="top")
    fig.update_layout(xaxis_title="Prediksi pm2.5 (ug/m3)", showlegend=False, yaxis=dict(autorange="reversed"))
    fig.update_xaxes(range=[0, max(max(nilai), aktual or 0) * 1.2 + 1])
    return rapikan(fig, tinggi=max(240, 52 * len(nama) + 90))


def kurva_whatif(x, y, nama_x, titik_dasar=None, kategorik=False):
    """
    Fungsi: kurva respons prediksi saat satu variabel digeser, dengan pita warna kategori udara di latar.
    Input : x (list nilai/kategori), y (list prediksi), nama_x, titik_dasar (x, y) skenario awal, kategorik (True = bar).
    Output: fig Plotly.
    """
    fig = go.Figure()
    ymaks = max(y) * 1.15 + 5
    for (b, a), w in zip(_pita_kategori(), cfg.WARNA_KATEGORI):
        if b < ymaks:
            fig.add_hrect(y0=b, y1=min(a if a is not None else ymaks, ymaks), fillcolor=_rgba(w, .13), line_width=0, layer="below")
    if kategorik:
        fig.add_bar(x=x, y=y, marker_color=cfg.WARNA_SERI[0], text=[f"{v:.1f}".replace(".", ",") for v in y], textposition="outside")
    else:
        fig.add_scatter(x=x, y=y, mode="lines+markers", line=dict(color=cfg.WARNA_SERI[0], width=3))
    if titik_dasar is not None:
        fig.add_scatter(x=[titik_dasar[0]], y=[titik_dasar[1]], mode="markers", name="Skenario awal",
                        marker=dict(size=13, color="#1F2D3D", symbol="diamond"))
    fig.update_layout(xaxis_title=nama_x, yaxis_title="Prediksi pm2.5 (ug/m3)", showlegend=False)
    fig.update_yaxes(range=[0, ymaks])
    return rapikan(fig, tinggi=400)
