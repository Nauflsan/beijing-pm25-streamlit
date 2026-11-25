"""
halaman/09_prediksi_satu_input.py - Prediksi Satu Input: gauge, kategori udara berwarna, saran kesehatan, interval
ketidakpastian, dan perbandingan semua model.

Dua cara mengisi input:
  1. Ambil dari data asli (untuk demo): pilih tanggal dan jam di tahun uji; cuaca + riwayat 24 jam diisi otomatis dan nilai
     AKTUAL ikut ditampilkan sebagai pembanding.
  2. Isi manual lewat st.form (Mode B juga butuh riwayat PM2.5 24 jam terakhir lewat st.data_editor).
Model dibaca dari artifacts/models/*.joblib (tidak ada training di web). Rumus fitur sama persis dengan training
(fitur_waktu.buat_baris_fitur, diuji di uji_cepat).
"""
import datetime as dt

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
T = cfg.KOLOM_TARGET
tema.header_halaman("Prediksi Satu Input", "Masukkan kondisi satu jam, lihat perkiraan pm2.5, kategori udara, saran, dan seberapa yakin modelnya.")
hasil = ua.hasil_atau_berhenti()
tahun = hasil["data"]["tahun_uji_mulai"]

c1, c2 = st.columns([2, 3])
with c1:
    mode = st.radio("Mode fitur", ["B", "A"], horizontal=True, format_func=lambda m: cfg.MODE_FITUR[m].split(":")[0] + (" (dengan riwayat)" if m == "B" else " (tanpa riwayat)"))
kunci_mode = [k for k, m in hasil["model"].items() if m["mode"] == mode]
with c2:
    pem = hasil["pemenang"].get(mode)
    kunci = st.selectbox("Model", kunci_mode, index=kunci_mode.index(pem) if pem in kunci_mode else 0,
                         format_func=lambda k: ua.sebut_model(k, hasil), help="Bawaan: model terbaik menurut validasi silang.")
paket = ua.muat_paket(kunci)
if paket is None:
    st.error(f"File model {kunci}.joblib tidak ditemukan di artifacts/models/. Jalankan `python -m model.latih_semua_model --penuh`.")
    st.stop()
if mode == "A":
    tema.kotak_catatan("Mode A tidak memakai riwayat PM2.5, hanya cuaca dan waktu. Hasilnya jauh lebih kasar dan cenderung meremehkan "
                       "polusi parah; gunakan Mode B kalau riwayat 24 jam terakhir tersedia.", "peringatan")

# ============================================================================= sumber input
sumber = st.radio("Sumber input", ["Ambil dari data asli (untuk demo)", "Isi manual"], horizontal=True)
waktu = cuaca = riwayat = aktual = None

if sumber.startswith("Ambil"):
    d = ua.data_siap()
    uji = d[d["layak_model"] & (d["year"] >= tahun)]
    tmin, tmax = uji["waktu"].min().date(), uji["waktu"].max().date()
    w_parah, w_bersih = uji.loc[uji[T].idxmax(), "waktu"], uji.loc[uji[T].idxmin(), "waktu"]
    if "demo_tgl" not in st.session_state:
        st.session_state["demo_tgl"], st.session_state["demo_jam"] = w_parah.date(), int(w_parah.hour)

    def _isi_contoh(w):
        """Fungsi: isi tanggal dan jam contoh lewat st.session_state (dipanggil tombol contoh). Input: Timestamp. Output: -"""
        st.session_state["demo_tgl"], st.session_state["demo_jam"] = w.date(), int(w.hour)

    b1, b2, b3, b4 = st.columns([2, 1, 2, 2])
    with b1:
        tgl = st.date_input("Tanggal", min_value=tmin, max_value=tmax, key="demo_tgl")
    with b2:
        jam = st.selectbox("Jam", list(range(24)), key="demo_jam")
    with b3:
        st.write("")
        st.button("Contoh: polusi paling parah", on_click=_isi_contoh, args=(w_parah,), width="stretch")
    with b4:
        st.write("")
        st.button("Contoh: udara paling bersih", on_click=_isi_contoh, args=(w_bersih,), width="stretch")
    contoh = pr.contoh_dari_data(d, pd.Timestamp(tgl) + pd.Timedelta(hours=int(jam)))
    if contoh is None:
        st.warning("Jam itu tidak punya riwayat 24 jam yang lengkap di data. Pilih jam lain.")
        st.stop()
    waktu, cuaca, riwayat, aktual = contoh
else:
    with st.form("form_manual"):
        f1, f2 = st.columns(2)
        with f1:
            tgl = st.date_input("Tanggal", value=dt.date(tahun, 1, 15))
        with f2:
            jam = st.selectbox("Jam", list(range(24)), index=8)
        g = st.columns(4)
        dewp = g[0].number_input("DEWP, titik embun (derajat C)", -40.0, 30.0, -10.0, step=1.0)
        temp = g[1].number_input("TEMP, suhu (derajat C)", -25.0, 45.0, 0.0, step=1.0)
        pres = g[2].number_input("PRES, tekanan (hPa)", 980.0, 1050.0, 1018.0, step=1.0)
        iws = g[3].number_input("Iws, angin kumulatif (m/s)", 0.0, 600.0, 10.0, step=1.0)
        h = st.columns(3)
        is_ = h[0].number_input("Is, jam salju", 0.0, 30.0, 0.0, step=1.0)
        ir = h[1].number_input("Ir, jam hujan", 0.0, 30.0, 0.0, step=1.0)
        arah = h[2].selectbox("cbwd, arah angin", cfg.KELAS_ARAH_ANGIN, index=1)
        tabel_riwayat = None
        if mode == "B":
            st.markdown(f"**Riwayat pm2.5 {fw.RIWAYAT_MINIMAL} jam terakhir** (ug/m3). Baris paling bawah = 1 jam sebelum jam di atas.")
            tabel_riwayat = st.data_editor(pd.DataFrame({"jam_sebelumnya": list(range(fw.RIWAYAT_MINIMAL, 0, -1)),
                                                         "pm2.5": [60.0] * fw.RIWAYAT_MINIMAL}),
                                           hide_index=True, disabled=["jam_sebelumnya"], num_rows="fixed", width="stretch")
        kirim = st.form_submit_button("Prediksi", type="primary")
    if kirim:
        st.session_state["input_manual"] = {
            "waktu": pd.Timestamp(tgl) + pd.Timedelta(hours=int(jam)),
            "cuaca": {"DEWP": dewp, "TEMP": temp, "PRES": pres, "Iws": iws, "Is": is_, "Ir": ir, cfg.KOLOM_ARAH_ANGIN: arah},
            "riwayat": None if tabel_riwayat is None else [float(v) for v in tabel_riwayat["pm2.5"]]}
    if "input_manual" not in st.session_state:
        st.info("Isi data di atas lalu tekan Prediksi.")
        st.stop()
    im = st.session_state["input_manual"]
    waktu, cuaca, riwayat = im["waktu"], im["cuaca"], im["riwayat"]
    if mode == "B" and (riwayat is None or any(pd.isna(v) for v in riwayat)):
        st.warning("Riwayat pm2.5 belum lengkap atau mode berubah setelah form dikirim. Tekan Prediksi lagi.")
        st.stop()

# ============================================================================= prediksi
nilai = pr.prediksi_satu(paket, waktu, cuaca, riwayat)
idx = ku.indeks_kategori(nilai)
info = ku.info_kategori(idx)
rentang = pr.interval_prediksi(hasil, kunci, nilai)

st.subheader(f"Hasil untuk {waktu:%d-%m-%Y %H:00}")
k1, k2 = st.columns([3, 4])
with k1:
    st.plotly_chart(grafik.gauge_pm25(nilai, idx), width="stretch")
with k2:
    st.markdown(tema.lencana_kategori(idx), unsafe_allow_html=True)
    st.markdown(f"**Perkiraan pm2.5: {fmt(nilai, 1)} ug/m3** ({ua.sebut_model(kunci, hasil)})")
    st.markdown(info["saran"])
    lo_k, hi_k = ku.indeks_kategori(rentang["bawah"]), ku.indeks_kategori(rentang["atas"])
    teks_kat = cfg.NAMA_KATEGORI[lo_k] if lo_k == hi_k else f"{cfg.NAMA_KATEGORI[lo_k]} sampai {cfg.NAMA_KATEGORI[hi_k]}"
    st.markdown(f"**Rentang perkiraan 90%:** {fmt(rentang['bawah'], 1)} sampai {fmt(rentang['atas'], 1)} ug/m3 (kategori: {teks_kat}).")
    st.caption(f"Rentang ini PERKIRAAN KASAR dari {rentang['dasar']}" + (f" (n = {fmt(rentang['n'], 0)} jam)" if rentang["n"] else "") +
               f", tahun {tahun}. Bukan jaminan statistik: kondisi di luar pola data uji bisa meleset lebih jauh.")
    if aktual is not None:
        ia = ku.indeks_kategori(aktual)
        st.markdown(f"**Nilai aktual di data:** {fmt(aktual, 1)} ug/m3 ({cfg.NAMA_KATEGORI[ia]}); selisih prediksi {fmt(nilai - aktual, 1)} ug/m3 "
                    + ("(kategori sama)." if ia == idx else "(kategori berbeda)."))

with st.expander("Input yang dipakai"):
    st.dataframe(pd.DataFrame([{**{k: v for k, v in cuaca.items()}, "waktu": f"{waktu:%Y-%m-%d %H:00}"}]), hide_index=True, width="stretch")
    if riwayat is not None:
        st.caption(f"pm2.5 {len(riwayat)} jam terakhir (lama ke baru): " + ", ".join(fmt(v, 0) for v in riwayat))

# ============================================================================= bandingkan semua model
st.subheader("Bandingkan semua model untuk input yang sama")
nama, vals = [], []
for k in kunci_mode:
    pk = ua.muat_paket(k)
    if pk is not None:
        nama.append(ua.sebut_model(k, hasil))
        vals.append(pr.prediksi_satu(pk, waktu, cuaca, riwayat))
if mode == "B":
    nama.append("Persistence 1 jam (nilai jam lalu)")
    vals.append(float(riwayat[-1]))
st.plotly_chart(grafik.bar_prediksi_model(nama, vals, aktual), width="stretch")
tabel = pd.DataFrame({"Model": nama, "Prediksi (ug/m3)": [round(v, 1) for v in vals],
                      "Kategori": [cfg.NAMA_KATEGORI[ku.indeks_kategori(v)] for v in vals]})
if aktual is not None:
    tabel["Selisih dari aktual"] = [round(v - aktual, 1) for v in vals]
st.dataframe(tabel, hide_index=True, width="stretch")
sebaran = max(vals) - min(vals)
st.caption(f"Selisih prediksi antar model {fmt(sebaran, 1)} ug/m3. Kalau semua model berdekatan, input ini 'mudah'; kalau berjauhan, "
           "hasilnya kurang pasti. Aplikasi ini bahan belajar, bukan alat keputusan kesehatan.")
ua.tampilkan_kode("prediksi.py", "prediksi_satu")
ua.tampilkan_kode("prediksi.py", "interval_prediksi")
ua.tampilkan_kode("fitur_waktu.py", "buat_baris_fitur")
