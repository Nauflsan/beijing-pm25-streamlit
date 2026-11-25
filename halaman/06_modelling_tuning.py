"""
halaman/06_modelling_tuning.py - Modelling & Tuning: 5 model beserta alasannya, RF default vs RF + PSO (sebelum/sesudah tuning),
validasi silang berurutan waktu, dan biaya (waktu, ukuran file).

SEMUA angka dibaca dari artifacts/hasil.json. Kalimat kesimpulan dibangun dari angka, jadi menang/kalahnya ditentukan data.
Setiap tab punya expander "Kode" yang menampilkan kode ASLI fungsi penghasilnya.
"""
import pandas as pd
import streamlit as st

import konfigurasi as cfg
from tampilan import grafik
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("Modelling dan Tuning", "Lima model regresi, dengan dan tanpa riwayat PM2.5, dan apakah tuning PSO benar-benar membantu.")
hasil = ua.hasil_atau_berhenti()
baris = ua.tabel_semua_model(hasil)
base1 = hasil["baseline"]["persistence_1jam"]
ALASAN = {
    "ridge": "Model linear paling sederhana, jadi tolok ukur. Regularisasi L2 menjaga koefisien tetap stabil walau fitur lag saling berkorelasi tinggi.",
    "dt": "Satu pohon keputusan: mudah dibaca sebagai aturan jika-maka dan menangkap hubungan non-linear. Mudah overfit, jadi kedalamannya dibatasi.",
    "rf": "Banyak pohon yang diacak lalu dirata-rata: mengurangi overfit pohon tunggal, tahan outlier, tidak butuh scaling.",
    "hgb": "Boosting: pohon dibangun berurutan, tiap pohon memperbaiki galat sebelumnya. Biasanya kuat untuk data tabular dan cepat di CPU.",
    "rf_pso": "Random Forest yang hyperparameter-nya dicari PSO, bukan ditebak manual. Diuji apakah pencarian otomatis memberi hasil lebih baik.",
}
mode = st.radio("Mode fitur", ["A", "B"], horizontal=True, format_func=lambda m: cfg.MODE_FITUR[m])

tab_model, tab_pso, tab_cv, tab_biaya = st.tabs(["Lima model", "RF vs RF + PSO", "Validasi silang", "Waktu dan ukuran"])

# ============================================================================= 1. lima model
with tab_model:
    st.markdown(f"Ada **5 model** x 2 mode fitur, kecuali RF + PSO yang hanya di Mode B: **{len(hasil['model'])} model terlatih**. "
                "Semuanya regresi (memprediksi angka pm2.5), dilatih pada data 2010-2013 dan diuji pada 2014.")
    kolom = st.columns(2)
    for i, kode in enumerate(cfg.URUTAN_MODEL):
        kunci = f"{kode}_B"
        param = hasil["model"].get(kunci, {}).get("parameter", {})
        with kolom[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{i + 1}. {cfg.NAMA_MODEL[kode]}**")
                st.markdown(ALASAN[kode])
                st.caption("Parameter: " + ", ".join(f"{k} = {v}" for k, v in param.items()))
    st.write("")

    data_mode = [b for b in baris if b["mode"] == mode and b["jenis"] == "Model"]
    pembanding = [b for b in baris if b["jenis"] == "Baseline" and b["kunci"] in (("persistence_1jam", "rata_rata_latih") if mode == "B" else ("rata_rata_latih",))]
    gabung = data_mode + pembanding
    warna = [cfg.WARNA_SERI[0] if b["jenis"] == "Model" else "#9AA7B4" for b in gabung]
    acuan = base1["uji"]["rmse"] if mode == "B" else None
    st.plotly_chart(grafik.bar_metode([b["nama"] for b in gabung], [b["rmse"] for b in gabung], warna, acuan=acuan), width="stretch")
    st.caption("Biru = model, abu-abu = baseline (tanpa training). Garis putus = persistence 1 jam." if mode == "B"
               else "Biru = model, abu-abu = baseline rata-rata data latih (Mode A tidak boleh memakai riwayat PM2.5, jadi tidak dibandingkan dengan persistence).")
    tabel = pd.DataFrame([{"Model": b["nama"], "RMSE": round(b["rmse"], 2), "MAE": round(b["mae"], 2), "MedAE": round(b["medae"], 2),
                           "R2": round(b["r2"], 3), "RMSE validasi silang": f"{b['cv_rmse']:.2f} (+- {b['cv_std']:.2f})".replace(".", ","),
                           **({"Lebih baik dari persistence (%)": round(ua.skill_persentase(b["rmse"], base1["uji"]["rmse"]), 1)} if mode == "B" else {})}
                          for b in gabung])
    st.dataframe(tabel, hide_index=True, width="stretch")

    terbaik_uji = min(data_mode, key=lambda b: b["rmse"])
    terbaik_cv = min(data_mode, key=lambda b: b["cv_rmse"])
    kal = [f"Di data uji, RMSE terkecil dicapai **{terbaik_uji['nama']}** ({fmt(terbaik_uji['rmse'])}). "
           f"Menurut validasi silang pada data latih, yang terbaik **{terbaik_cv['nama']}** ({fmt(terbaik_cv['cv_rmse'])})."]
    if terbaik_uji["kunci"] != terbaik_cv["kunci"]:
        kal.append(" Keduanya berbeda: model dipilih lewat validasi silang (bukan data uji) supaya pemilihan tidak mengintip data uji; "
                   "selisih antar model dekat sehingga urutannya mudah bergeser.")
    if mode == "B":
        menang_uji = [b["nama"] for b in data_mode if b["rmse"] < base1["uji"]["rmse"]]
        menang_cv = [b["nama"] for b in data_mode if b["cv_rmse"] < base1["cv"]["rmse_rata"]]
        kal.append(f" Dibanding persistence 1 jam: {len(menang_uji)} dari {len(data_mode)} model lebih baik di data uji, "
                   f"dan {len(menang_cv)} dari {len(data_mode)} lebih baik di validasi silang.")
        belum = [b["nama"] for b in data_mode if b["nama"] not in menang_cv]
        if belum:
            kal.append(f" Yang belum mengalahkan persistence di validasi silang: {', '.join(belum)}.")
    st.markdown("".join(kal))
    ua.tampilkan_kode("latih_semua_model.py", "buat_estimator")
    ua.tampilkan_kode("latih_semua_model.py", "latih_dan_simpan")

# ============================================================================= 2. RF vs RF+PSO
with tab_pso:
    pso = hasil["pso"]
    pg = pso["pengaturan"]
    st.subheader("Random Forest biasa vs Random Forest + PSO")
    a, b, c, d = st.columns(4)
    with a:
        tema.kartu_kpi("Partikel x iterasi", f"{pg['partikel']} x {pg['iterasi']}", "ukuran pencarian (diperkecil untuk laptop i3)")
    with b:
        tema.kartu_kpi("Evaluasi fitness", f"{pso['n_evaluasi']}", f"{pso['n_cache_hit']} kombinasi sama tidak dihitung ulang")
    with c:
        tema.kartu_kpi("Data fitness", f"{fmt(pg['sampel'], 0)} baris", f"sampel data latih, {pg['n_fold']} lipatan berurutan waktu")
    with d:
        tema.kartu_kpi("Lama PSO", f"{fmt(pso['waktu_detik'], 0)} detik", "di laptop kalian")
    st.write("")
    st.markdown("**Ruang pencarian** (semua bilangan bulat) dan hasilnya:")
    rf, rp = hasil["model"]["rf_B"]["parameter"], hasil["model"]["rf_pso_B"]["parameter"]
    st.dataframe(pd.DataFrame([{"Parameter": k, "Batas bawah": pg["batas"][k][0], "Batas atas": pg["batas"][k][1],
                                "RF default": rf[k], "RF + PSO": rp[k]} for k in pg["batas"]]), hide_index=True, width="stretch")
    st.plotly_chart(grafik.garis_konvergensi(pso["riwayat_gbest"]), width="stretch")
    st.caption("PSO hanya memakai data latih (TimeSeriesSplit); data uji 2014 tidak pernah dilihat PSO. Iterasi 0 adalah partikel acak awal.")

    st.subheader("Sebelum dan sesudah tuning, di tiga tingkat")
    m0, m1 = hasil["model"]["rf_B"], hasil["model"]["rf_pso_B"]
    fit0, fit1 = pso["rmse_cv_pembanding"], pso["rmse_cv_terbaik"]
    tingkat = [
        ("1. Sampel fitness PSO (tempat PSO mencari)", fit0, fit1),
        ("2. Validasi silang penuh, data latih", m0["cv"]["rmse_rata"], m1["cv"]["rmse_rata"]),
        ("3. Data uji 2014 (belum pernah dilihat)", m0["uji"]["rmse"], m1["uji"]["rmse"]),
    ]
    st.dataframe(pd.DataFrame([{"Tingkat": n, "RMSE RF default": round(x, 3), "RMSE RF + PSO": round(y, 3),
                                "Perubahan (%)": round(ua.persen_selisih(y, x), 2),
                                "Hasil": "PSO lebih baik" if y < x else "PSO lebih buruk"} for n, x, y in tingkat]),
                 hide_index=True, width="stretch")
    st.dataframe(pd.DataFrame([{"Ukuran": "MAE uji", "RF default": round(m0["uji"]["mae"], 2), "RF + PSO": round(m1["uji"]["mae"], 2)},
                               {"Ukuran": "R2 uji", "RF default": round(m0["uji"]["r2"], 3), "RF + PSO": round(m1["uji"]["r2"], 3)},
                               {"Ukuran": "Ukuran file (MB)", "RF default": round(m0["ukuran_file_mb"], 2), "RF + PSO": round(m1["ukuran_file_mb"], 2)}]),
                 hide_index=True, width="stretch")
    menang = [y < x for _, x, y in tingkat]
    if all(menang):
        kesimpulan = "PSO memberi hasil lebih baik di ketiga tingkat, jadi tuning terbukti membantu."
    elif menang[0] and not menang[2]:
        kesimpulan = ("PSO memang menemukan parameter yang lebih baik di sampel tempat ia mencari, tetapi perbaikan itu **tidak terbawa ke data uji**. "
                      "Artinya tuning belum terbukti membantu di sini; selisihnya kecil dan kemungkinan masuk wilayah derau. "
                      "Kemungkinan PSO sedikit menyesuaikan diri dengan sampel fitness (dugaan, belum diuji lebih jauh).")
    elif not any(menang):
        kesimpulan = "PSO tidak lebih baik di ketiga tingkat; Random Forest dengan parameter default sudah cukup."
    else:
        kesimpulan = "Hasilnya campuran antar tingkat; lihat tabel sebelum menyimpulkan."
    st.markdown(f"**Kesimpulan:** {kesimpulan} Karena itu halaman Evaluasi dan Uji Kejujuran memperlakukan RF + PSO sebagai satu model "
                "pembanding, bukan sebagai model yang dijamin lebih baik.")
    st.markdown("**Lima kombinasi terbaik yang pernah dievaluasi PSO** (RMSE di sampel fitness):")
    terbaik5 = sorted(pso["evaluasi"], key=lambda e: e["rmse"])[:5]
    st.dataframe(pd.DataFrame([{**e["params"], "RMSE": round(e["rmse"], 3)} for e in terbaik5]), hide_index=True, width="stretch")
    ua.tampilkan_kode("pso_random_forest.py", "jalankan_pso")

# ============================================================================= 3. validasi silang
with tab_cv:
    st.subheader("Validasi silang berurutan waktu (TimeSeriesSplit)")
    model_mode = [b for b in baris if b["mode"] == mode and b["jenis"] == "Model"]
    seri = {b["nama"]: [f["rmse"] for f in hasil["model"][b["kunci"]]["cv"]["per_fold"]] for b in model_mode}
    if mode == "B":
        seri["Persistence 1 jam"] = [f["rmse"] for f in base1["cv"]["per_fold"]]
    st.plotly_chart(grafik.bar_cv_per_lipatan(seri), width="stretch")
    fold = hasil["model"][model_mode[0]["kunci"]]["cv"]["per_fold"]
    st.caption("Tiap lipatan melatih di masa lalu dan menguji di bagian waktu setelahnya. Ukuran (latih / validasi): " +
               "; ".join(f"lipatan {i + 1}: {fmt(f['n_latih'], 0)} / {fmt(f['n_valid'], 0)}" for i, f in enumerate(fold)) + ".")
    st.dataframe(pd.DataFrame([{"Model": b["nama"], "RMSE rata-rata": round(b["cv_rmse"], 2), "Simpangan baku antar lipatan": round(b["cv_std"], 2)}
                               for b in sorted(model_mode, key=lambda b: b["cv_rmse"])]), hide_index=True, width="stretch")
    rentang = max(max(v) - min(v) for v in seri.values())
    st.markdown(f"Hasil tiap lipatan berbeda cukup jauh (selisih RMSE antar lipatan hingga {fmt(rentang, 1)} ug/m3 pada model yang sama), "
                "jadi perbedaan antar model yang kecil sebaiknya dibaca hati-hati.")
    ua.tampilkan_kode("evaluasi_regresi.py", "cv_regresi")

# ============================================================================= 4. waktu dan ukuran
with tab_biaya:
    st.subheader("Waktu training dan ukuran file")
    modl = [b for b in baris if b["jenis"] == "Model"]
    st.dataframe(pd.DataFrame([{"Model": b["nama"], "Mode": b["mode"], "Waktu validasi silang (detik)": round(b["waktu_cv"], 1),
                                "Waktu latih akhir (detik)": round(b["waktu_latih"], 1), "Ukuran file (MB)": round(b["ukuran_mb"], 2),
                                "Kolom masuk model": hasil["model"][b["kunci"]]["n_fitur_setelah_enkode"]} for b in modl]),
                 hide_index=True, width="stretch")
    total_cv = sum(b["waktu_cv"] for b in modl)
    total_fit = sum(b["waktu_latih"] for b in modl)
    total_mb = sum(b["ukuran_mb"] for b in modl)
    c1, c2, c3 = st.columns(3)
    with c1:
        tema.kartu_kpi("Total waktu model", f"{fmt(total_cv + total_fit, 0)} detik", "validasi silang + latih akhir, belum termasuk PSO")
    with c2:
        tema.kartu_kpi("Waktu PSO", f"{fmt(hasil['pso']['waktu_detik'], 0)} detik", "pencarian hyperparameter")
    with c3:
        tema.kartu_kpi("Total ukuran model", f"{fmt(total_mb, 1)} MB", f"file terbesar {fmt(max(b['ukuran_mb'] for b in modl), 1)} MB (batas GitHub 100 MB)")
    st.caption("Semua model dilatih di CPU laptop tanpa GPU. Ukuran kecil memudahkan deploy: file model ikut di repo dan dibaca langsung oleh web.")
