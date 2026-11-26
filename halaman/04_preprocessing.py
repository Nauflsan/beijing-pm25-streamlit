"""
halaman/04_preprocessing.py - Preprocessing (lengkap). Enam tab:
  1. Kolom ke fitur      : tabel "Dari 13 kolom CSV ke fitur model" + pertanyaan dosen tentang jumlah fitur
  2. Data kosong         : ffill vs median vs interpolasi (bocor)
  3. Outlier             : kenapa tidak dibuang, dan bukti dari error saat polusi parah
  4. Log target          : hasil eksperimen, dievaluasi di skala asli
  5. Split waktu dan scaling
  6. Temuan EDA ke keputusan : tiap temuan EDA -> keputusan -> kode (file dan baris) + peta hasil.json ke kode

SEMUA angka model dibaca dari artifacts/hasil.json; angka data dari CSV. Setiap tab punya expander "Kode" yang menampilkan
kode ASLI fungsi penghasilnya (bukti_kode.py), supaya pertanyaan "kodenya mana?" bisa dijawab dari layar.
Kalimat kesimpulan dibangun dari angka, jadi arahnya (membantu/merugikan) ditentukan data, bukan tulisan tangan.
"""
import pandas as pd
import streamlit as st

from evaluasi import bukti_kode as bk
from tampilan import grafik
import konfigurasi as cfg
from preprocessing import peta_fitur as pf
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua
from preprocessing import utilitas_data as ud

T = cfg.KOLOM_TARGET
fmt = ua.fmt

tema.header_halaman("Preprocessing", "Dari data mentah menjadi fitur yang dipakai model, dan bukti kenapa tiap keputusan diambil.")
hasil = ua.hasil_atau_berhenti()
eks = hasil.get("eksperimen")
df = ua.muat_data()
ring = ud.ringkasan_dataset(df)
r = pf.ringkasan_jumlah(hasil)

tab_fitur, tab_kosong, tab_out, tab_log, tab_split, tab_temuan = st.tabs(
    ["Kolom ke fitur", "Data kosong", "Outlier", "Log target", "Split waktu dan scaling", "Temuan EDA ke keputusan"])

# ============================================================================= 1. kolom ke fitur
with tab_fitur:
    st.subheader(f"Dari {hasil['data']['n_kolom_asli']} kolom CSV ke fitur model")
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
    ua.tampilkan_kode("fitur_waktu.py", "siapkan_data")
    ua.tampilkan_kode("fitur_waktu.py", "buat_preprocessor_umum")
    with st.expander("Pertanyaan yang mungkin ditanya dosen tentang jumlah fitur"):
        for i, (tanya, jawab) in enumerate(pf.pertanyaan_dosen(hasil), 1):
            st.markdown(f"**{i}. {tanya}**")
            st.markdown(jawab)
            st.write("")

# ============================================================================= 2. data kosong
with tab_kosong:
    st.subheader("Data kosong: tiga cara mengisi, satu yang adil")
    a, b, c = st.columns(3)
    with a:
        tema.kartu_kpi("Jam pm2.5 kosong", fmt(ring["n_kosong_target"], 0), f"{fmt(ring['persen_kosong_target'], 2)}% dari semua jam")
    with b:
        tema.kartu_kpi("Baris dibuang karena fitur belum lengkap", fmt(hasil["data"]["n_baris_dibuang_fitur_tidak_lengkap"], 0),
                       "baris awal yang riwayat lag-nya belum ada")
    with c:
        tema.kartu_kpi("Baris layak dipakai model", fmt(hasil["data"]["n_baris_layak_model"], 0), "target ada dan semua fitur lengkap")
    st.write("")
    if not eks:
        st.info("Eksperimen belum ada di hasil.json.")
    else:
        isi = eks["isi_kosong"]
        nama_metode = {"ffill": "Forward fill (dipakai)", "median_latih": "Median data latih", "interpolasi_bocor": "Interpolasi linear (BOCOR)"}
        warna = [cfg.WARNA_SERI[0], cfg.WARNA_SERI[3], cfg.WARNA_SERI[1]]
        urut = ["ffill", "median_latih", "interpolasi_bocor"]
        k1, k2 = st.columns([3, 2])
        with k1:
            st.plotly_chart(grafik.bar_metode([nama_metode[k] for k in urut], [isi[k]["rmse"] for k in urut], warna,
                                              acuan=isi["ffill"]["rmse"]), width="stretch")
        with k2:
            st.dataframe(pd.DataFrame({
                "Cara": [nama_metode[k] for k in urut],
                "Pakai masa depan?": ["tidak", "tidak", "YA (bocor)"],
                "RMSE": [round(isi[k]["rmse"], 2) for k in urut],
                "R2": [round(isi[k]["r2"], 3) for k in urut]}), hide_index=True, width="stretch")
        terbaik = min(isi, key=lambda k: isi[k]["rmse"])
        sel_interp = ua.persen_selisih(isi["ffill"]["rmse"], isi["interpolasi_bocor"]["rmse"])
        sel_med = ua.persen_selisih(isi["median_latih"]["rmse"], isi["ffill"]["rmse"])
        kalimat = (f"RMSE terkecil dicapai **{nama_metode[terbaik]}** ({fmt(isi[terbaik]['rmse'])}). ")
        if terbaik == "interpolasi_bocor":
            kalimat += ("Tetapi interpolasi menghitung nilai kosong dari titik sebelum DAN sesudahnya, jadi saat model memprediksi satu jam ia "
                        f"ikut 'mengintip' masa depan. Selisihnya dari forward fill hanya {fmt(abs(sel_interp), 2)}%, dan itu harga yang tidak "
                        "layak untuk hasil yang tidak bisa terjadi di dunia nyata. ")
        kalimat += (f"Median data latih memberi RMSE {fmt(sel_med, 2)}% {'lebih tinggi' if sel_med > 0 else 'lebih rendah'} dibanding forward fill. "
                    "Forward fill dipilih karena hanya memakai masa lalu.")
        st.markdown(kalimat)
        st.caption("Eksperimen memakai Ridge Mode B, dievaluasi di data uji pada baris yang sama untuk ketiga cara (adil).")
    st.markdown("Baris yang pm2.5-nya kosong **tidak dipakai sebagai target** latih maupun uji; pengisian hanya untuk membentuk fitur riwayat.")
    ua.tampilkan_kode("fitur_waktu.py", "isi_pm")
    ua.tampilkan_kode("eksperimen_preprocessing.py", "_eksp_isi_kosong")

# ============================================================================= 3. outlier
with tab_out:
    st.subheader("Outlier: tidak dibuang, karena justru bagian paling penting")
    a, b, c = st.columns(3)
    with a:
        tema.kartu_kpi("Batas outlier (aturan IQR)", fmt(ring["batas_outlier_iqr"], 0), "Q3 + 1,5 x IQR, ug/m3")
    with b:
        tema.kartu_kpi("Jam di atas batas", fmt(ring["n_outlier_iqr"], 0), f"{fmt(100 * ring['n_outlier_iqr'] / (ring['n_baris'] - ring['n_kosong_target']), 2)}% dari jam bernilai")
    with c:
        pb = hasil["baseline"]["persistence_1jam"]["polusi_parah"]
        tema.kartu_kpi(f"Jam polusi parah di data uji (> {fmt(pb['ambang'], 0)})", fmt(pb["parah"]["n"], 0) if pb.get("parah") else "-",
                       "dipakai untuk menilai model saat polusi tinggi")
    st.write("")
    baris = []
    for nama, ent in [("Persistence 1 jam (baseline)", hasil["baseline"]["persistence_1jam"])] + \
                     [(ua.sebut_model(k, hasil), m) for k, m in hasil["model"].items()]:
        pp = ent["polusi_parah"]
        if pp.get("normal") and pp.get("parah"):
            baris.append({"Model": nama, "MAE saat normal": round(pp["normal"]["mae"], 1), "MAE saat parah": round(pp["parah"]["mae"], 1),
                          "Berapa kali lipat": round(pp["parah"]["mae"] / pp["normal"]["mae"], 1), "Bias saat parah": round(pp["parah"]["bias"], 1)})
    tabel = pd.DataFrame(baris)
    st.dataframe(tabel, hide_index=True, width="stretch")
    mb = hasil["model"][hasil["pemenang"]["B"]]["polusi_parah"]
    ma = hasil["model"][hasil["pemenang"]["A"]]["polusi_parah"]
    st.markdown(
        f"Saat polusi parah, error model terbaik Mode B sekitar **{fmt(mb['parah']['mae'] / mb['normal']['mae'], 1)} kali** error saat normal, "
        f"dan Mode A sekitar **{fmt(ma['parah']['mae'] / ma['normal']['mae'], 1)} kali**. "
        + ("Bias negatif berarti model cenderung menebak LEBIH RENDAH dari kenyataan saat polusi parah (meremehkan). "
           if mb["parah"]["bias"] < 0 else "")
        + "Kalau kejadian ekstrem dibuang dari data, kita kehilangan kemampuan menilai bagian yang paling berbahaya bagi kesehatan.")
    st.caption("Kemungkinan besar titik-titik ekstrem adalah kejadian polusi nyata (dugaan, belum diverifikasi ke sumber data). "
               "Keputusan: tidak dibuang; dampaknya dinilai lewat MedAE dan metrik polusi parah.")
    ua.tampilkan_kode("evaluasi_regresi.py", "metrik_polusi_parah")

# ============================================================================= 4. log target
with tab_log:
    st.subheader("Log target: dicoba, dievaluasi di skala asli")
    if not eks:
        st.info("Eksperimen belum ada di hasil.json.")
    else:
        lg = eks["log_target"]
        st.plotly_chart(grafik.bar_berkelompok(
            ["Mode A", "Mode B"],
            {"Target asli": [lg["A"]["skala_asli"]["rmse"], lg["B"]["skala_asli"]["rmse"]],
             "Target log1p": [lg["A"]["target_log1p"]["rmse"], lg["B"]["target_log1p"]["rmse"]]}), width="stretch")
        for mode in ("A", "B"):
            asli, lg_r = lg[mode]["skala_asli"]["rmse"], lg[mode]["target_log1p"]["rmse"]
            naik = ua.persen_selisih(lg_r, asli)
            st.markdown(f"- Mode {mode}: RMSE {fmt(asli)} (target asli) berbanding {fmt(lg_r)} (log1p), "
                        f"**{'naik' if naik > 0 else 'turun'} {fmt(abs(naik), 1)}%**.")
        buruk = all(lg[m]["target_log1p"]["rmse"] > lg[m]["skala_asli"]["rmse"] for m in ("A", "B"))
        st.markdown("Kesimpulan: " + ("transformasi log **memperburuk** RMSE di kedua mode, jadi tidak dipakai di model final. "
                                      "Dugaan penyebab: prediksi dikembalikan ke skala asli dengan expm1, sehingga selisih kecil di skala log "
                                      "membesar di skala asli, terutama untuk nilai tinggi. Ini dugaan, belum diuji lebih lanjut."
                                      if buruk else "log memberi hasil campuran; lihat angka di atas sebelum memutuskan."))
        st.caption("Model dilatih pada log1p(pm2.5), lalu prediksinya diubah balik dengan expm1 dan DIEVALUASI di skala asli "
                   "(ug/m3), karena itu skala yang bermakna untuk kualitas udara.")
    ua.tampilkan_kode("eksperimen_preprocessing.py", "_eksp_skala_dan_log")

# ============================================================================= 5. split dan scaling
with tab_split:
    st.subheader("Split berdasarkan waktu")
    d = hasil["data"]
    a, b, c = st.columns(3)
    with a:
        tema.kartu_kpi("Data latih", fmt(d["n_latih"], 0), f"{d['rentang_latih'][0][:10]} sampai {d['rentang_latih'][1][:10]}")
    with b:
        tema.kartu_kpi("Data uji", fmt(d["n_uji"], 0), f"{d['rentang_uji'][0][:10]} sampai {d['rentang_uji'][1][:10]}")
    with c:
        tema.kartu_kpi("Aturan pembagian", f"tahun >= {d['tahun_uji_mulai']} jadi uji", "latih selalu di masa lalu, uji di masa depan")
    st.write("")
    cv = hasil["model"]["ridge_B"]["cv"]["per_fold"]
    st.markdown(f"**Validasi silang berurutan waktu ({len(cv)} lipatan)** pada data latih: tiap lipatan melatih di masa lalu dan "
                "menguji di bagian waktu setelahnya, tidak pernah sebaliknya.")
    st.plotly_chart(grafik.lipatan_waktu(cv, d["n_latih"], d["n_uji"]), width="stretch")
    ua.tampilkan_kode("fitur_waktu.py", "bagi_waktu")

    st.subheader("Scaling")
    if eks:
        sk = eks["skala"]
        tabel = pd.DataFrame([{"Mode": m, "RMSE dengan skala": round(sk[m]["dengan_skala"]["rmse"], 3),
                               "RMSE tanpa skala": round(sk[m]["tanpa_skala"]["rmse"], 3),
                               "Selisih (%)": round(ua.persen_selisih(sk[m]["tanpa_skala"]["rmse"], sk[m]["dengan_skala"]["rmse"]), 3)}
                              for m in ("A", "B")])
        st.dataframe(tabel, hide_index=True, width="stretch")
        kecil = all(abs(x) < 1 for x in tabel["Selisih (%)"])
        st.markdown("Ridge dilatih dengan StandardScaler (rata-rata 0, simpangan baku 1) di dalam Pipeline, sehingga hanya belajar dari "
                    "data latih. Di eksperimen ini selisihnya " + ("**sangat kecil** (di bawah 1%), jadi scaling tidak mengubah hasil secara berarti. "
                    if kecil else "**cukup terlihat**, jadi scaling berpengaruh. ")
                    + "Model berbasis pohon (Decision Tree, Random Forest, HistGradientBoosting) tidak memakai scaler karena tidak peka skala.")
    ua.tampilkan_kode("fitur_waktu.py", "buat_pipeline")

# ============================================================================= 6. temuan EDA -> keputusan -> kode
with tab_temuan:
    st.subheader("Temuan EDA, keputusan, dan letak kodenya")
    ac1 = df[T].ffill().autocorr(1)
    base = hasil["baseline"]["persistence_1jam"]["uji"]
    korelasi_cuaca = df[[T] + cfg.KOLOM_CUACA_NUMERIK].corr()[T].drop(T).abs().max()
    baris = [
        ("pm2.5 kosong", f"{fmt(ring['n_kosong_target'], 0)} jam ({fmt(ring['persen_kosong_target'], 2)}%)",
         "Baris kosong tidak jadi target; kosong di fitur lag diisi forward fill (hanya masa lalu).",
         [("fitur_waktu.py", "isi_pm"), ("fitur_waktu.py", "siapkan_data")]),
        ("Sebaran miring, banyak outlier", f"skewness {fmt(ring['pm25_skew'], 2)}; {fmt(ring['n_outlier_iqr'], 0)} jam di atas batas IQR",
         "Outlier tidak dibuang; error dinilai juga dengan MedAE dan khusus saat polusi parah.",
         [("evaluasi_regresi.py", "metrik_polusi_parah"), ("evaluasi_regresi.py", "hitung_metrik")]),
        ("Korelasi cuaca dengan pm2.5 lemah", f"korelasi terkuat |r| = {fmt(korelasi_cuaca, 2)}",
         "Dibuat dua mode fitur: Mode A (cuaca + waktu) dan Mode B (tambah riwayat PM2.5).",
         [("fitur_waktu.py", "daftar_fitur"), ("fitur_waktu.py", "hitung_fitur_pm")]),
        ("PM2.5 sangat mirip dengan jam lalu", f"autokorelasi lag 1 jam = {fmt(ac1, 3)}; persistence 1 jam R2 = {fmt(base['r2'], 3)} di data uji",
         "Persistence dijadikan baseline wajib; model harus mengalahkannya.",
         [("latih_semua_model.py", "hitung_baseline")]),
        ("Arah angin adalah kategori", f"{len(cfg.KELAS_ARAH_ANGIN)} kategori ({', '.join(cfg.KELAS_ARAH_ANGIN)})",
         "One-hot encoding di dalam Pipeline.", [("fitur_waktu.py", "buat_preprocessor_umum")]),
        ("Jam dan bulan melingkar", "jam 23 bertetangga dengan jam 0; bulan 12 dengan bulan 1",
         "Diubah ke pasangan sin dan cos.", [("fitur_waktu.py", "siapkan_data")]),
        ("Data berurutan waktu", f"{fmt(d['n_latih'], 0)} baris latih (sampai {d['rentang_latih'][1][:4]}), {fmt(d['n_uji'], 0)} baris uji ({d['rentang_uji'][0][:4]})",
         "Split berdasarkan waktu dan validasi silang TimeSeriesSplit, bukan acak.",
         [("fitur_waktu.py", "bagi_waktu"), ("evaluasi_regresi.py", "cv_regresi")]),
    ]
    # st.table (bukan st.dataframe) supaya teks panjang membungkus dan tidak terpotong
    st.table(pd.DataFrame([{"Temuan EDA": t, "Bukti (dari data dan hasil.json)": b, "Keputusan": k,
                            "Kode (file dan baris)": "; ".join(f"{bk.lokasi_kode(f, fn)} ({fn})" for f, fn in kode)}
                           for t, b, k, kode in baris]).set_index("Temuan EDA"))
    st.caption("Nomor baris dihitung langsung dari file saat halaman dibuka, jadi selalu cocok dengan kode terbaru.")

    st.subheader("Peta lengkap: bagian hasil.json dihasilkan oleh kode yang mana")
    st.table(pd.DataFrame(bk.tabel_peta()).set_index("Bagian hasil.json"))
    meta = hasil["meta"]
    st.caption(f"hasil.json terakhir diperbarui {meta.get('diperbarui', '-')}, profil '{meta.get('profil_terakhir', '-')}', "
               f"Python {meta.get('versi', {}).get('python', '-')}, scikit-learn {meta.get('versi', {}).get('scikit_learn', '-')}, "
               f"seed {meta.get('seed', '-')}.")
