"""
halaman/tambahan/14_whatif_simulator.py - What-if Simulator: geser satu variabel (suhu, titik embun, tekanan, angin, arah angin, jam,
bulan, atau riwayat pm2.5) dan lihat kurva prediksi model, dengan pita warna kategori udara di latar.

Ini menunjukkan bagaimana MODEL merespons perubahan input, bukan hubungan sebab-akibat di atmosfer.
Mode B memakai riwayat pm2.5 KONSTAN (semua 24 jam sama dengan nilai yang dipilih) supaya satu variabel bisa digeser tanpa kerumitan.
"""
import numpy as np
import pandas as pd
import streamlit as st

import konfigurasi as cfg
from evaluasi import kategori_udara as ku
from model import prediksi as pr
from preprocessing import fitur_waktu as fw
from tampilan import grafik
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("What-if Simulator", "Geser satu variabel, lihat bagaimana prediksi model berubah.")
hasil = ua.hasil_atau_berhenti()
df = ua.muat_data()
tahun = hasil["data"]["tahun_uji_mulai"]

c1, c2 = st.columns([2, 3])
with c1:
    mode = st.radio("Mode fitur", ["A", "B"], horizontal=True, format_func=lambda m: "Mode A (cuaca + waktu)" if m == "A" else "Mode B (dengan riwayat)")
kunci_mode = [k for k, m in hasil["model"].items() if m["mode"] == mode]
with c2:
    pem = hasil["pemenang"].get(mode)
    kunci = st.selectbox("Model", kunci_mode, index=kunci_mode.index(pem) if pem in kunci_mode else 0, format_func=lambda k: ua.sebut_model(k, hasil))
paket = ua.muat_paket(kunci)
if paket is None:
    st.error(f"File model {kunci}.joblib tidak ditemukan di artifacts/models/.")
    st.stop()


def rentang(kolom):
    """Fungsi: rentang slider dari data, persentil 1 sampai 99 (agar nilai ekstrem tidak merusak skala). Input: nama kolom. Output: (min, maks, median)."""
    lo, hi = df[kolom].quantile([.01, .99])
    return float(lo), float(hi), float(df[kolom].median())


st.subheader("Skenario awal")
g = st.columns(4)
nilai = {}
for i, k in enumerate(["TEMP", "DEWP", "PRES", "Iws"]):
    lo, hi, med = rentang(k)
    nilai[k] = g[i].slider(k, lo, hi, med)
h = st.columns(4)
nilai["Is"], nilai["Ir"] = 0.0, 0.0
arah = h[0].selectbox("cbwd, arah angin", cfg.KELAS_ARAH_ANGIN, index=1)
jam = h[1].slider("Jam", 0, 23, 12)
bulan = h[2].slider("Bulan", 1, 12, 1)
riw_median = float(df[cfg.KOLOM_TARGET].median())
riw = h[3].slider("pm2.5 riwayat (konstan)", 0.0, 400.0, riw_median) if mode == "B" else None

opsi = ["TEMP", "DEWP", "PRES", "Iws", "cbwd", "jam", "bulan"] + (["pm2.5 riwayat (konstan)"] if mode == "B" else [])
geser = st.selectbox("Variabel yang digeser", opsi)


def prediksi(n, a, j, b, r):
    """Fungsi: satu prediksi untuk skenario (nilai cuaca n, arah a, jam j, bulan b, riwayat konstan r). Output: float."""
    cuaca = {**n, cfg.KOLOM_ARAH_ANGIN: a}
    return pr.prediksi_satu(paket, pd.Timestamp(year=tahun, month=int(b), day=15, hour=int(j)), cuaca,
                            None if r is None else [r] * fw.RIWAYAT_MINIMAL)


kategorik = geser in ("cbwd", "jam", "bulan")
if geser == "cbwd":
    grid = list(cfg.KELAS_ARAH_ANGIN)
elif geser == "jam":
    grid = list(range(24))
elif geser == "bulan":
    grid = list(range(1, 13))
elif geser == "pm2.5 riwayat (konstan)":
    grid = list(np.linspace(0, 400, 33))
else:
    lo, hi, _ = rentang(geser)
    grid = list(np.linspace(lo, hi, 25))

hasil_y = []
for v in grid:
    n, a, j, b, r = dict(nilai), arah, jam, bulan, riw
    if geser in nilai:
        n[geser] = v
    elif geser == "cbwd":
        a = v
    elif geser == "jam":
        j = v
    elif geser == "bulan":
        b = v
    else:
        r = v
    hasil_y.append(prediksi(n, a, j, b, r))
dasar = prediksi(nilai, arah, jam, bulan, riw)
x_dasar = {"cbwd": arah, "jam": jam, "bulan": bulan, "pm2.5 riwayat (konstan)": riw}.get(geser, nilai.get(geser))
st.subheader(f"Prediksi saat {geser} digeser")
st.plotly_chart(grafik.kurva_whatif(grid, hasil_y, geser, titik_dasar=(x_dasar, dasar), kategorik=kategorik and geser == "cbwd"), width="stretch")
i_min, i_maks = int(np.argmin(hasil_y)), int(np.argmax(hasil_y))
st.markdown(f"Skenario awal diprediksi **{fmt(dasar, 1)} ug/m3** ({cfg.NAMA_KATEGORI[ku.indeks_kategori(dasar)]}). "
            f"Saat **{geser}** digeser, prediksi berkisar dari {fmt(min(hasil_y), 1)} (di {grid[i_min] if kategorik else fmt(grid[i_min], 1)}) "
            f"sampai {fmt(max(hasil_y), 1)} (di {grid[i_maks] if kategorik else fmt(grid[i_maks], 1)}) ug/m3, selisih {fmt(max(hasil_y) - min(hasil_y), 1)} ug/m3.")
if mode == "B" and geser != "pm2.5 riwayat (konstan)":
    st.caption("Di Mode B riwayat PM2.5 sangat dominan, jadi menggeser variabel cuaca biasanya hanya sedikit mengubah prediksi. Coba geser 'pm2.5 riwayat'.")
st.caption("Ini menunjukkan respons MODEL terhadap perubahan input, bukan hubungan sebab-akibat di atmosfer; variabel lain dianggap tetap padahal di dunia nyata saling terkait. "
           "Is dan Ir diset 0 (hampir selalu 0 di data).")
ua.tampilkan_kode("prediksi.py", "prediksi_satu")
