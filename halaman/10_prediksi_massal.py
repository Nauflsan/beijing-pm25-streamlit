"""
halaman/10_prediksi_massal.py - Prediksi Massal: unggah CSV berisi banyak jam, dapatkan prediksi tiap jam, lihat ringkasan
dan unduh hasilnya.

Format unggahan = format CSV dataset (kolom year, month, day, hour, pm2.5, DEWP, TEMP, PRES, cbwd, Iws, Is, Ir), baris terurut per jam.
  - Mode A: pm2.5 boleh kosong (hanya cuaca + waktu yang dipakai).
  - Mode B: kolom pm2.5 harus terisi sebagai riwayat; jam harus berurutan tanpa celah karena lag dihitung dari baris-baris sebelumnya.
Validasi (kolom, arah angin, urutan, jumlah baris) ada di model/prediksi.py:validasi_unggahan dan memberi pesan yang bisa langsung diperbaiki.
"""
import pandas as pd
import streamlit as st

import konfigurasi as cfg
from evaluasi import evaluasi_regresi as ev
from evaluasi import kategori_udara as ku
from model import prediksi as pr
from tampilan import grafik
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("Prediksi Massal", "Unggah CSV berisi banyak jam, dapatkan prediksi tiap jam beserta ringkasannya.")
hasil = ua.hasil_atau_berhenti()

c1, c2 = st.columns([2, 3])
with c1:
    mode = st.radio("Mode fitur", ["B", "A"], horizontal=True, format_func=lambda m: "Mode B (dengan riwayat)" if m == "B" else "Mode A (tanpa riwayat)")
kunci_mode = [k for k, m in hasil["model"].items() if m["mode"] == mode]
with c2:
    pem = hasil["pemenang"].get(mode)
    kunci = st.selectbox("Model", kunci_mode, index=kunci_mode.index(pem) if pem in kunci_mode else 0, format_func=lambda k: ua.sebut_model(k, hasil))
paket = ua.muat_paket(kunci)
if paket is None:
    st.error(f"File model {kunci}.joblib tidak ditemukan di artifacts/models/. Jalankan `python -m model.latih_semua_model --penuh`.")
    st.stop()

st.subheader("1. Unduh template")
st.markdown("Format file sama dengan CSV dataset. Kolom wajib: `year, month, day, hour, DEWP, TEMP, PRES, cbwd, Iws, Is, Ir`.")
st.markdown("Untuk **Mode B** kolom `pm2.5` wajib terisi (riwayat) dan baris harus berurutan per jam tanpa celah; 24 jam pertama dipakai sebagai "
            "riwayat sehingga tidak ikut diprediksi. Untuk **Mode A** kolom `pm2.5` boleh kosong (kalau ada, dipakai untuk menghitung error).")
df_data = ua.muat_data()
st.download_button("Unduh template CSV (72 jam contoh dari data asli)", data=pr.template_csv(df_data), file_name="template_prediksi_massal.csv",
                   mime="text/csv")

st.subheader("2. Unggah file")
file = st.file_uploader("File CSV", type=["csv"], help=f"Maksimal {fmt(pr.MAKS_BARIS_MASSAL, 0)} baris.")
if file is None:
    st.info("Belum ada file. Unduh template lalu ubah isinya, atau unggah potongan CSV dataset asli.")
    st.stop()
try:
    df_up = pd.read_csv(file)
except Exception as e:  # noqa: BLE001  (pesan ramah untuk file rusak)
    st.error(f"File tidak bisa dibaca sebagai CSV: {e}")
    st.stop()

ok, pesan, d_valid = pr.validasi_unggahan(df_up, mode)
if not ok:
    for p in pesan:
        st.error(p)
    st.stop()
for p in pesan:
    st.warning(p)

hasil_pred = pr.prediksi_massal(paket, d_valid)
if hasil_pred.empty:
    st.warning("Tidak ada baris yang bisa diprediksi (riwayat belum cukup).")
    st.stop()

st.subheader("3. Hasil")
a, b, c = st.columns(3)
with a:
    tema.kartu_kpi("Baris diprediksi", fmt(len(hasil_pred), 0), f"dari {fmt(len(d_valid), 0)} baris di file")
with b:
    tema.kartu_kpi("Rata-rata prediksi", f"{fmt(hasil_pred['prediksi'].mean(), 1)} ug/m3", "seluruh baris", ku.indeks_kategori(hasil_pred["prediksi"].mean()))
with c:
    ada = hasil_pred["aktual"].notna()
    if ada.any():
        m = ev.hitung_metrik(hasil_pred.loc[ada, "aktual"], hasil_pred.loc[ada, "prediksi"])
        tema.kartu_kpi("Error vs aktual (MAE)", f"{fmt(m['mae'])} ug/m3", f"RMSE {fmt(m['rmse'])}, dari {fmt(m['n'], 0)} jam beraktual")
    else:
        tema.kartu_kpi("Error vs aktual", "-", "kolom pm2.5 kosong, jadi tidak bisa dihitung")
st.write("")
st.markdown("**Jumlah jam menurut kategori prediksi**")
st.plotly_chart(grafik.bar_kategori(grafik.jumlah_per_kategori(hasil_pred["prediksi"])), width="stretch")

if ada.any():
    st.markdown("**Prediksi vs aktual**")
    st.plotly_chart(grafik.garis_waktu(hasil_pred.rename(columns={"prediksi": "p"}).assign(aktual=hasil_pred["aktual"]), ["p"], {"p": "Prediksi"}), width="stretch")
else:
    st.markdown("**Prediksi per jam**")
    st.line_chart(hasil_pred.set_index("waktu")["prediksi"])

st.dataframe(hasil_pred, hide_index=True, width="stretch")
st.download_button("Unduh hasil (CSV)", data=hasil_pred.to_csv(index=False), file_name="hasil_prediksi_massal.csv", mime="text/csv")
st.caption("Setiap baris diprediksi terpisah dengan model yang sama seperti halaman Prediksi Satu Input. Hasil Mode B bergantung pada kebenaran riwayat pm2.5 di file.")
ua.tampilkan_kode("prediksi.py", "validasi_unggahan")
ua.tampilkan_kode("prediksi.py", "prediksi_massal")
