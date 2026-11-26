"""
halaman/tambahan/13_feature_engineering.py - Feature Engineering: fitur waktu siklik (sin-cos), lag dan rata-rata bergulir (tanpa kebocoran),
dan ablasi kelompok fitur.

Ablasi dibaca dari hasil.json -> eksperimen -> ablasi (Ridge Mode B, dihasilkan preprocessing/eksperimen_ablasi.py).
Ilustrasi lag memakai CSV. Semua kalimat kesimpulan dibangun dari angka.
"""
import pandas as pd
import streamlit as st

import konfigurasi as cfg
from preprocessing import fitur_waktu as fw
from tampilan import grafik
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("Feature Engineering", "Fitur buatan yang memberi model gambaran waktu dan riwayat, dan seberapa besar manfaat tiap kelompoknya.")
hasil = ua.hasil_atau_berhenti()

tab_sik, tab_lag, tab_abl = st.tabs(["Fitur waktu siklik", "Lag dan rata-rata bergulir", "Ablasi: manfaat tiap kelompok"])

with tab_sik:
    st.markdown("Jam dan bulan itu **melingkar**: jam 23 bertetangga dengan jam 0, bulan 12 dengan bulan 1. Angka biasa (0-23) membuat model mengira keduanya "
                "berjauhan. Karena itu tiap waktu diubah menjadi dua koordinat di lingkaran: `sin` dan `cos`.")
    k1, k2 = st.columns(2)
    with k1:
        st.plotly_chart(grafik.lingkaran_siklik(24, [str(j) for j in range(24)], "Jam (0-23) pada lingkaran"), width="stretch")
    with k2:
        st.plotly_chart(grafik.lingkaran_siklik(12, grafik.BULAN, "Bulan (1-12) pada lingkaran"), width="stretch")
    st.caption("Kenapa dua kolom, bukan satu: hanya dengan sin, dua waktu berbeda bisa bernilai sama (mis. jam 3 dan jam 9); cos membedakannya.")
    ua.tampilkan_kode("fitur_waktu.py", "siapkan_data")

with tab_lag:
    st.markdown("Mode B menambah **riwayat PM2.5** sebagai fitur. Semuanya hanya memakai jam-jam SEBELUM jam yang diprediksi:")
    lag_f = [f for f in hasil["fitur"]["B"] if f.startswith("pm25_lag")]
    rol_f = [f for f in hasil["fitur"]["B"] if f.startswith("pm25_rata")]
    st.markdown(f"- **Lag** ({len(lag_f)} fitur): `{'`, `'.join(lag_f)}` = nilai PM2.5 sekian jam sebelumnya.\n"
                f"- **Rata-rata bergulir** ({len(rol_f)} fitur): `{'`, `'.join(rol_f)}` = rata-rata beberapa jam sebelumnya, dihitung dari seri yang **digeser 1 jam dulu** "
                "supaya jam yang diprediksi tidak ikut masuk rata-rata.")
    d = ua.data_siap()
    mulai = d.index[(d["year"] == hasil["data"]["tahun_uji_mulai"]) & d["layak_model"]][0]
    cuplik = d.loc[mulai: mulai + 71]
    st.plotly_chart(grafik.garis_lag(cuplik["waktu"], cuplik[cfg.KOLOM_TARGET], cuplik["pm25_lag1"], cuplik["pm25_rata3"]), width="stretch")
    st.caption("Garis oranye putus-putus sama dengan garis hitam tetapi bergeser 1 jam ke kanan: itu yang dilihat model saat memprediksi. "
               "Nilai kosong diisi nilai terakhir yang diketahui (forward fill), bukan interpolasi yang memakai masa depan.")
    tema.kotak_catatan("Bukti tanpa kebocoran: alat/uji_cepat.py mengubah semua nilai PM2.5 dari jam t ke depan, lalu memastikan fitur lag dan rata-rata di jam t dan sebelumnya TIDAK berubah.")
    ua.tampilkan_kode("fitur_waktu.py", "hitung_fitur_pm")

with tab_abl:
    eks = hasil.get("eksperimen", {})
    if "ablasi" not in eks:
        st.info("Hasil ablasi belum ada di hasil.json. Jalankan training lagi.")
    else:
        abl = eks["ablasi"]
        penuh = abl["lengkap_mode_b"]["rmse"]
        nama = {"lengkap_mode_b": "Lengkap (Mode B)", "tanpa_cuaca": "Tanpa cuaca", "tanpa_waktu_siklik": "Tanpa waktu siklik",
                "tanpa_arah_angin": "Tanpa arah angin", "tanpa_lag": "Tanpa lag", "tanpa_rolling": "Tanpa rata-rata bergulir",
                "tanpa_lag_dan_rolling_(=mode_a)": "Tanpa lag dan rolling (= Mode A)", "hanya_lag1": "Hanya lag 1 jam"}
        urut = list(abl.keys())
        st.plotly_chart(grafik.bar_metode([nama.get(k, k) for k in urut], [abl[k]["rmse"] for k in urut],
                                          [cfg.WARNA_SERI[0] if k == "lengkap_mode_b" else cfg.WARNA_SERI[1] for k in urut], acuan=penuh), width="stretch")
        st.dataframe(pd.DataFrame([{"Varian": nama.get(k, k), "RMSE": round(abl[k]["rmse"], 2), "R2": round(abl[k]["r2"], 3),
                                    "Perubahan RMSE vs lengkap (%)": round(ua.persen_selisih(abl[k]["rmse"], penuh), 1)} for k in urut]),
                     hide_index=True, width="stretch")
        terbesar = max((k for k in urut if k != "lengkap_mode_b"), key=lambda k: abl[k]["rmse"])
        kecil = [nama.get(k, k) for k in urut if k.startswith("tanpa_") and k != "tanpa_lag_dan_rolling_(=mode_a)"
                 and abs(ua.persen_selisih(abl[k]["rmse"], penuh)) < 2]
        st.markdown(f"Varian dengan RMSE terburuk adalah **{nama.get(terbesar, terbesar)}** ({fmt(abl[terbesar]['rmse'])} vs {fmt(penuh)} untuk lengkap). "
                    + (f"Membuang kelompok berikut mengubah RMSE kurang dari 2%: {', '.join(kecil)}. " if kecil else "")
                    + "Artinya riwayat PM2.5 jauh lebih penting daripada fitur cuaca dan waktu di Mode B.")
        st.caption(eks.get("catatan", "Ablasi memakai Ridge (model linear); hasilnya belum tentu sama untuk model berbasis pohon."))
    ua.tampilkan_kode("eksperimen_ablasi.py", "_eksp_ablasi")
