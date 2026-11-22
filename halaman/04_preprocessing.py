"""
halaman/04_preprocessing.py - Preprocessing.

STATUS: sebagian (Tahap 2). Sudah ada: tabel "Dari 13 kolom CSV ke fitur model" + pertanyaan antisipasi dosen.
Menyusul di Tahap 3: perbandingan isi data kosong, outlier, transformasi log target, split waktu, scaling
(hasil eksperimennya sudah ada di hasil.json["eksperimen"]).

Semua jumlah (13 kolom, 11/17 fitur, 14/20 kolom setelah one-hot) dibaca dari hasil.json lewat peta_fitur.py.
"""
import streamlit as st

import konfigurasi as cfg
import peta_fitur as pf
import tema_langit_beijing as tema
import utilitas_app as ua

tema.header_halaman("Preprocessing", "Dari data mentah menjadi fitur yang dipakai model.")
hasil = ua.hasil_atau_berhenti()

tema.kotak_catatan("Halaman ini masih dilengkapi bertahap. Bagian berikut sudah siap; perbandingan cara mengisi data kosong, "
                   "outlier, log target, split waktu, dan scaling menyusul.")

st.subheader(f"Dari {hasil['data']['n_kolom_asli']} kolom CSV ke fitur model")
r = pf.ringkasan_jumlah(hasil)
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    tema.kartu_kpi("Kolom di CSV", r["n_kolom_csv"], f"{r['n_dibuang']} tidak dipakai sebagai fitur")
with c2:
    tema.kartu_kpi("Fitur Mode A", r["n_fitur_a"], "cuaca + waktu, tanpa riwayat PM2.5")
with c3:
    tema.kartu_kpi("Fitur Mode B", r["n_fitur_b"], f"Mode A + {r['selisih_b_a']} fitur riwayat PM2.5")
with c4:
    tema.kartu_kpi("Kolom Mode A setelah one-hot", r["n_enkode_a"] if r["n_enkode_a"] is not None else "-", "yang benar-benar masuk model")
with c5:
    tema.kartu_kpi("Kolom Mode B setelah one-hot", r["n_enkode_b"] if r["n_enkode_b"] is not None else "-", "yang benar-benar masuk model")
st.write("")

tabel, peringatan = pf.bangun_tabel(hasil)
for p in peringatan:
    st.warning(p)
st.table(tabel.set_index("Kolom asal"))
st.caption("Jumlah di tabel dibaca dari artifacts/hasil.json (kunci 'fitur' dan 'n_fitur_setelah_enkode'). "
           "Aturan 'diapakan' dan alasannya adalah keputusan desain yang ditulis di peta_fitur.py.")

with st.expander("Tentang jumlah fitur", expanded=False):
    for i, (tanya, jawab) in enumerate(pf.pertanyaan_dosen(hasil), 1):
        st.markdown(f"**{i}. {tanya}**")
        st.markdown(jawab)
        st.write("")
