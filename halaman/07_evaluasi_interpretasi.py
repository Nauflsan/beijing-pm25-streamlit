"""
halaman/07_evaluasi_interpretasi.py - Evaluasi & Interpretasi: metrik, aktual vs prediksi, residual, error per bulan dan per
kategori udara, permutation importance, dan partial dependence.

Angka metrik, per bulan/kategori, kuantil residual, dan interpretasi dibaca dari artifacts/hasil.json.
Grafik aktual-vs-prediksi dan residual membaca artifacts/prediksi_uji.csv (dibuat skrip latih). Kalau file itu belum ada,
bagian tersebut menampilkan pesan ramah, sisanya tetap jalan.
"""
import pandas as pd
import streamlit as st

import konfigurasi as cfg
from tampilan import grafik
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("Evaluasi dan Interpretasi", "Seberapa meleset modelnya, kapan dan di mana melesetnya, dan fitur apa yang paling dipakai.")
hasil = ua.hasil_atau_berhenti()
baris = ua.tabel_semua_model(hasil)
base1 = hasil["baseline"]["persistence_1jam"]

c_mode, c_model = st.columns([2, 3])
with c_mode:
    mode = st.radio("Mode fitur", ["A", "B"], horizontal=True, format_func=lambda m: f"Mode {m}")
kunci_mode = [k for k, m in hasil["model"].items() if m["mode"] == mode]
default = kunci_mode.index(hasil["pemenang"][mode]) if hasil["pemenang"].get(mode) in kunci_mode else 0
with c_model:
    kunci = st.selectbox("Model yang dievaluasi", kunci_mode, index=default, format_func=lambda k: ua.sebut_model(k, hasil),
                         help="Bawaan: model terbaik menurut validasi silang untuk mode ini.")
m = hasil["model"][kunci]
u = m["uji"]
tahun = hasil["data"]["tahun_uji_mulai"]

# --- KPI --------------------------------------------------------------------------------------
acuan_nama, acuan = ("persistence 1 jam", base1["uji"]) if mode == "B" else ("rata-rata data latih", hasil["baseline"]["rata_rata_latih"]["uji"])
sk = ua.skill_persentase(u["rmse"], acuan["rmse"])
k1, k2, k3, k4 = st.columns(4)
with k1:
    tema.kartu_kpi("MAE", f"{fmt(u['mae'])} ug/m3", f"{acuan_nama}: {fmt(acuan['mae'])}")
with k2:
    tema.kartu_kpi("RMSE", f"{fmt(u['rmse'])} ug/m3", f"{acuan_nama}: {fmt(acuan['rmse'])}")
with k3:
    tema.kartu_kpi("R2", fmt(u["r2"], 3), f"{acuan_nama}: {fmt(acuan['r2'], 3)}")
with k4:
    tema.kartu_kpi("Dibanding " + acuan_nama, f"{'+' if sk >= 0 else ''}{fmt(sk, 1)}%", "RMSE lebih kecil = positif" if sk >= 0 else "RMSE lebih besar = negatif")
st.caption(f"Data uji: tahun {tahun}, {fmt(u['n'], 0)} jam. MedAE (kesalahan tipikal) {fmt(u['medae'])} ug/m3; "
           f"bias rata-rata {fmt(u['bias'], 1)} ug/m3 (negatif = cenderung menebak lebih rendah).")

tab_metrik, tab_ap, tab_res, tab_err, tab_int = st.tabs(
    ["Metrik semua model", "Aktual vs prediksi", "Residual", "Error per bulan dan kategori", "Interpretasi"])

# ============================================================================= metrik
with tab_metrik:
    st.markdown("**Cara membaca metrik**")
    st.markdown("- **MAE**: rata-rata meleset sekian ug/m3.\n- **RMSE**: seperti MAE tetapi lebih menghukum kesalahan besar.\n"
                "- **MedAE**: meleset 'tipikal' (median), tidak terseret lonjakan ekstrem.\n"
                "- **R2**: bagian variasi data yang dijelaskan model (bisa menipu, lihat halaman Uji Kejujuran).")
    tabel = pd.DataFrame([{"Model": b["nama"] + ("  (baseline)" if b["jenis"] == "Baseline" else ""), "RMSE": round(b["rmse"], 2),
                           "MAE": round(b["mae"], 2), "MedAE": round(b["medae"], 2), "R2": round(b["r2"], 3)}
                          for b in baris if b["mode"] == mode or (b["jenis"] == "Baseline" and b["kunci"] == "rata_rata_latih")]).sort_values("RMSE")
    st.dataframe(tabel, hide_index=True, width="stretch")
    ua.tampilkan_kode("evaluasi_regresi.py", "hitung_metrik")

# ============================================================================= aktual vs prediksi
with tab_ap:
    dfp = ua.muat_prediksi_uji()
    if dfp is None or kunci not in dfp.columns:
        st.info("File artifacts/prediksi_uji.csv belum ada (dibuat otomatis oleh skrip latih). Jalankan `python -m model.latih_semua_model --penuh`.")
    else:
        st.plotly_chart(grafik.scatter_aktual_prediksi(dfp["aktual"], dfp[kunci], ua.sebut_model(kunci, hasil)), width="stretch")
        st.caption("Titik yang rapat di sekitar garis putus berarti prediksi dekat dengan kenyataan. Dibatasi 3.000 titik acak agar ringan.")
        bulan_ada = sorted(dfp["bulan"].unique())
        pilih = st.select_slider("Bulan yang ditampilkan", options=bulan_ada, value=bulan_ada[0], format_func=lambda b: grafik.BULAN[int(b) - 1])
        sub = dfp[dfp["bulan"] == pilih]
        kolom = [kunci] + (["persistence_1jam"] if mode == "B" else [])
        st.plotly_chart(grafik.garis_waktu(sub, kolom, {kunci: ua.sebut_model(kunci, hasil), "persistence_1jam": "Persistence 1 jam"}), width="stretch")
        bp = m["polusi_parah"].get("parah")
        if mode == "A":
            st.markdown("Mode A tidak memakai riwayat PM2.5, jadi ia mengikuti pola umum (musim, jam, cuaca) tetapi tidak mengikuti naik-turun "
                        "tajam dari jam ke jam." + (f" Saat polusi parah (> {fmt(m['polusi_parah']['ambang'], 0)} ug/m3) bias rata-ratanya "
                                                   f"{fmt(bp['bias'], 1)} ug/m3, artinya ia {'meremehkan' if bp['bias'] < 0 else 'melebihkan'} lonjakan." if bp else ""))
        else:
            st.markdown("Mode B memakai nilai jam-jam sebelumnya, sehingga kurvanya ikut bergerak mengikuti aktual. Garis persistence (nilai jam lalu) "
                        "ikut digambar karena itu pesaing yang harus dikalahkan: bandingkan seberapa dekat masing-masing garis dengan garis aktual.")

# ============================================================================= residual
with tab_res:
    kq = m["kuantil_residual"]["global"]
    st.markdown(f"Residual = aktual - prediksi. Separuh residual berada di antara {fmt(float(kq['0.25']), 1)} dan {fmt(float(kq['0.75']), 1)} ug/m3, "
                f"dan 90% berada di antara {fmt(float(kq['0.05']), 1)} dan {fmt(float(kq['0.95']), 1)} ug/m3 (median {fmt(float(kq['0.5']), 1)}).")
    dfp = ua.muat_prediksi_uji()
    if dfp is not None and kunci in dfp.columns:
        res = dfp["aktual"] - dfp[kunci]
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(grafik.histogram_residual(res), width="stretch")
        with g2:
            st.plotly_chart(grafik.scatter_residual(dfp[kunci], res), width="stretch")
        st.caption("Kiri: sebaran residual (idealnya simetris di sekitar 0). Kanan: residual terhadap nilai prediksi; kalau titik melebar ke kanan "
                   "berarti galat makin besar saat prediksi tinggi.")
    else:
        st.info("Grafik residual butuh artifacts/prediksi_uji.csv (belum ada).")
    st.markdown("**Kuantil residual per kategori PREDIKSI** (dasar interval ketidakpastian di halaman Prediksi):")
    baris_k = []
    for nama in cfg.NAMA_KATEGORI_PENDEK:
        e = m["kuantil_residual"]["per_kategori_prediksi"].get(nama)
        if e and e["kuantil"]:
            q = e["kuantil"]
            baris_k.append({"Kategori prediksi": nama, "Jumlah jam": e["n"], "Batas bawah 5%": round(q["0.05"], 1),
                            "Median": round(q["0.5"], 1), "Batas atas 95%": round(q["0.95"], 1), "Lebar 90% (ug/m3)": round(q["0.95"] - q["0.05"], 1)})
    if baris_k:
        st.dataframe(pd.DataFrame(baris_k), hide_index=True, width="stretch")
        lebar = [b["Lebar 90% (ug/m3)"] for b in baris_k]
        st.markdown("Lebar rentang " + ("**membesar** saat prediksi masuk kategori yang lebih tinggi, jadi ketidakpastian lebih besar justru saat udara lebih buruk."
                                        if lebar[-1] > lebar[0] else "tidak membesar saat prediksi tinggi.") +
                    " Ini perkiraan kasar dari data uji, bukan jaminan statistik.")
        st.caption("Kategori dengan kurang dari 30 jam tidak ditampilkan karena terlalu sedikit untuk dipercaya.")

# ============================================================================= bulan dan kategori
with tab_err:
    ukuran = st.radio("Ukuran error", ["mae", "rmse"], horizontal=True, format_func=str.upper)
    e1, e2 = st.columns(2)
    with e1:
        st.markdown("**Per bulan**")
        st.plotly_chart(grafik.bar_per_bulan(m["per_bulan"], ukuran), width="stretch")
    with e2:
        st.markdown("**Per kategori udara aktual**")
        st.plotly_chart(grafik.bar_per_kategori(m["per_kategori"], ukuran), width="stretch")
    pb = m["per_bulan"]
    terburuk = max(pb, key=lambda b: pb[b][ukuran])
    terbaik = min(pb, key=lambda b: pb[b][ukuran])
    st.markdown(f"Error {ukuran.upper()} terbesar di bulan **{grafik.BULAN[int(terburuk) - 1]}** ({fmt(pb[terburuk][ukuran], 1)}) dan terkecil di "
                f"**{grafik.BULAN[int(terbaik) - 1]}** ({fmt(pb[terbaik][ukuran], 1)}). ")
    st.markdown("**Bias per kategori** (rata-rata prediksi - aktual; negatif = meremehkan):")
    st.plotly_chart(grafik.bar_per_kategori(m["per_kategori"], "bias"), width="stretch")
    pk = m["per_kategori"]
    pola = [k for k in cfg.NAMA_KATEGORI_PENDEK if k in pk]
    if len(pola) >= 2:
        st.markdown(f"Pada kategori **{pola[0]}** bias {fmt(pk[pola[0]]['bias'], 1)}, sedangkan pada **{pola[-1]}** bias {fmt(pk[pola[-1]]['bias'], 1)}. "
                    + ("Model cenderung terlalu tinggi saat udara bersih dan terlalu rendah saat udara sangat buruk, pola khas model yang 'menarik' prediksi ke rata-rata."
                       if pk[pola[0]]["bias"] > 0 > pk[pola[-1]]["bias"] else ""))
    ua.tampilkan_kode("evaluasi_regresi.py", "metrik_per_kategori")

# ============================================================================= interpretasi
with tab_int:
    inter = hasil["interpretasi"][mode]
    st.markdown(f"Interpretasi dihitung untuk **{ua.sebut_model(inter['model'], hasil)}**, yaitu model terbaik Mode {mode} menurut validasi silang.")
    perm = inter["permutation"]
    st.markdown("**Permutation importance**: seberapa naik RMSE kalau satu kolom diacak (makin besar = makin diandalkan model).")
    st.plotly_chart(grafik.bar_importance(perm), width="stretch")
    total = sum(max(p["naik_rmse"], 0) for p in perm)
    st.markdown(f"Kolom paling berpengaruh: **{perm[0]['fitur']}** (RMSE naik {fmt(perm[0]['naik_rmse'], 1)} ug/m3 saat diacak, "
                f"sekitar {fmt(100 * max(perm[0]['naik_rmse'], 0) / total, 0) if total else '-'}% dari seluruh kenaikan). "
                "Ini menunjukkan ketergantungan model pada kolom itu, bukan hubungan sebab-akibat di atmosfer.")
    st.markdown("**Partial dependence**: rata-rata prediksi saat satu fitur digeser dan fitur lain apa adanya.")
    fitur_pd = list(inter["parsial"].keys())
    kol = st.columns(2)
    for i, f in enumerate(fitur_pd):
        with kol[i % 2]:
            st.markdown(f"`{f}`")
            st.plotly_chart(grafik.garis_parsial(inter["parsial"][f]["grid"], inter["parsial"][f]["rata_prediksi"], f), width="stretch")
    if any(f.endswith(("_sin", "_cos")) for f in fitur_pd):
        st.caption("Fitur berakhiran _sin dan _cos adalah dua sisi dari satu pasangan (jam atau bulan), jadi kurva salah satunya tidak "
                   "bisa dibaca terpisah dan bisa tampak bergerigi.")
    if "ridge" in inter["model"]:
        st.caption("Karena model ini Ridge (linear), kurva partial dependence berupa garis lurus: tiap fitur punya pengaruh yang konstan.")
    else:
        st.caption("Kurva yang melengkung menunjukkan model menangkap hubungan non-linear.")
    ua.tampilkan_kode("evaluasi_regresi.py", "importance_permutasi")
    ua.tampilkan_kode("evaluasi_regresi.py", "kurva_parsial")
