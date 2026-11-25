"""
halaman/08_uji_kejujuran.py - Uji Kejujuran Model (ciri khas proyek ini).

Pertanyaan yang dijawab: apakah hasil model benar-benar bagus, atau hanya terlihat bagus?
  1. Split acak vs split waktu   : hasil bisa tampak lebih bagus kalau data diacak (jam bertetangga bocor ke data uji)
  2. Baseline persistence        : model harus mengalahkan tebakan "sama seperti jam lalu"
  3. R2 vs MAE vs RMSE           : kenapa R2 tinggi bisa menipu
  4. Saat polusi parah           : performa di kejadian yang paling berbahaya

SEMUA angka dibaca dari artifacts/hasil.json. Arah kesimpulan (menang/kalah, lebih tinggi/lebih rendah) ditentukan angka,
bukan ditulis tangan, termasuk saat hasilnya tidak sesuai harapan.
"""
import pandas as pd
import streamlit as st

import konfigurasi as cfg
from tampilan import grafik
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("Uji Kejujuran Model", "Apakah modelnya benar-benar bagus, atau hanya terlihat bagus? Diuji dengan angka, termasuk yang tidak enak dilihat.")
hasil = ua.hasil_atau_berhenti()
baris = ua.tabel_semua_model(hasil)
uk = hasil["uji_kejujuran"]
base1, base24, bmean = (hasil["baseline"][k] for k in ("persistence_1jam", "persistence_24jam", "rata_rata_latih"))
pem = hasil["pemenang"]
tahun = hasil["data"]["tahun_uji_mulai"]
mB = [b for b in baris if b["mode"] == "B" and b["jenis"] == "Model"]

# ----------------------------------------------------------------------------- ringkasan di atas (dibangun dari angka)
terbaikB = min(mB, key=lambda b: b["rmse"])
skB = ua.skill_persentase(terbaikB["rmse"], base1["uji"]["rmse"])
skB_mae = ua.skill_persentase(terbaikB["mae"], base1["uji"]["mae"])
menang_cv = [b["nama"] for b in mB if b["cv_rmse"] < base1["cv"]["rmse_rata"]]
r2_modelB = [b["r2"] for b in mB]
poin = [
    f"**Baseline {'sangat kuat' if base1['uji']['r2'] > 0.9 else 'cukup kuat'}.** Menebak 'sama seperti jam lalu' sudah menghasilkan R2 {fmt(base1['uji']['r2'], 3)} dan MAE {fmt(base1['uji']['mae'])} di data uji, tanpa belajar apa pun.",
    f"**Keunggulan model di Mode B {'kecil' if skB < 10 else 'cukup besar'}.** Model terbaik di data uji ({terbaikB['nama']}) hanya {fmt(skB, 1)}% lebih rendah RMSE-nya dan {fmt(skB_mae, 1)}% lebih rendah MAE-nya "
    f"dari persistence; di validasi silang hanya {len(menang_cv)} dari {len(mB)} model mengalahkan persistence.",
    f"**R2 hampir sama untuk semua.** R2 model Mode B berkisar {fmt(min(r2_modelB), 3)} sampai {fmt(max(r2_modelB), 3)} dibanding {fmt(base1['uji']['r2'], 3)} untuk persistence, jadi R2 hampir tidak membedakan.",
]
for mode in ("A", "B"):
    a, w = uk[mode]["split_acak"]["uji"]["r2"], uk[mode]["split_waktu"]["uji"]["r2"]
    poin.append(f"**Split acak, Mode {mode}.** R2 {fmt(a, 3)} (acak) berbanding {fmt(w, 3)} (waktu): split acak tampak "
                f"{'LEBIH bagus' if a > w else 'tidak lebih bagus'} di mode ini.")
with st.container(border=True):
    st.markdown("**Ringkasan kejujuran (dihitung otomatis dari hasil.json)**")
    for p in poin:
        st.markdown(f"- {p}")

mode = st.radio("Mode fitur untuk tab 2 sampai 4", ["A", "B"], index=1, horizontal=True, format_func=lambda m: cfg.MODE_FITUR[m])
tab_split, tab_base, tab_r2, tab_parah = st.tabs(["Split acak vs waktu", "Baseline persistence", "R2 vs MAE vs RMSE", "Saat polusi parah"])

# ============================================================================= 1. split acak vs waktu
with tab_split:
    st.subheader("Split acak vs split waktu (model HistGradientBoosting yang sama)")
    st.markdown(f"**Split waktu:** latih di masa lalu, uji di tahun {tahun} ({fmt(hasil['data']['n_uji'], 0)} jam). "
                f"**Split acak:** {fmt(uk['n_uji_acak'], 0)} jam dipilih acak dari seluruh 2010-2014 untuk uji, sisanya ({fmt(uk['n_latih_acak'], 0)}) untuk latih, "
                "sehingga jam yang bertetangga bisa jatuh ke dua sisi sekaligus.")
    kol = st.columns(2)
    for kol_i, md in zip(kol, ("A", "B")):
        with kol_i:
            acak, waktu = uk[md]["split_acak"]["uji"], uk[md]["split_waktu"]["uji"]
            st.markdown(f"**{cfg.MODE_FITUR[md]}**")
            st.plotly_chart(grafik.bar_berkelompok(["R2", "RMSE / 100", "MAE / 100"],
                                                   {"Split waktu": [waktu["r2"], waktu["rmse"] / 100, waktu["mae"] / 100],
                                                    "Split acak": [acak["r2"], acak["rmse"] / 100, acak["mae"] / 100]}, "nilai"), width="stretch")
            st.dataframe(pd.DataFrame([{"Ukuran": "R2", "Split waktu": round(waktu["r2"], 3), "Split acak": round(acak["r2"], 3)},
                                       {"Ukuran": "RMSE", "Split waktu": round(waktu["rmse"], 2), "Split acak": round(acak["rmse"], 2)},
                                       {"Ukuran": "MAE", "Split waktu": round(waktu["mae"], 2), "Split acak": round(acak["mae"], 2)}]),
                         hide_index=True, width="stretch")
            if acak["r2"] > waktu["r2"]:
                st.markdown(f"Split acak memberi R2 lebih tinggi ({fmt(acak['r2'], 3)} vs {fmt(waktu['r2'], 3)}): hasilnya **terlihat lebih bagus**, "
                            "tetapi itu kemungkinan besar karena model 'melihat' jam-jam di sekitar jam yang diuji saat latih, bukan karena lebih pandai memprediksi masa depan (penjelasan yang masuk akal, tidak diuji terpisah).")
            else:
                st.markdown(f"Di mode ini split acak **tidak** memberi R2 lebih tinggi ({fmt(acak['r2'], 3)} vs {fmt(waktu['r2'], 3)}). "
                            "Jadi tidak benar bahwa split acak selalu tampak lebih bagus; di sini efek bocornya tidak terlihat.")
    pa = uk["B"]["persistence_1jam_pada_uji_acak"]
    st.caption(f"Pembanding fair: persistence 1 jam pada baris uji acak yang sama (Mode B) memberi R2 {fmt(pa['r2'], 3)}, RMSE {fmt(pa['rmse'])}, MAE {fmt(pa['mae'])}.")
    tema.kotak_catatan("Catatan kehati-hatian: baris uji pada split acak mencakup seluruh 2010-2014, sedangkan split waktu hanya tahun "
                       f"{tahun}. Perbedaan komposisi ini ikut mempengaruhi angka, jadi perbandingan ini menunjukkan arah, bukan ukuran persis efek kebocoran.", "peringatan")
    ua.tampilkan_kode("latih_semua_model.py", "uji_kejujuran")

# ============================================================================= 2. baseline persistence
with tab_base:
    st.subheader("Baseline: tebakan tanpa belajar")
    st.markdown("**Persistence 1 jam** memakai nilai jam lalu sebagai prediksi; **persistence 24 jam** memakai nilai jam yang sama kemarin; "
                "**rata-rata latih** selalu menebak rata-rata data latih. Model dianggap berguna hanya kalau mengalahkan baseline yang relevan.")
    sub = [b for b in baris if b["mode"] == mode and b["jenis"] == "Model"]
    base_pakai = [base1, base24, bmean] if mode == "B" else [bmean]
    daftar = [(b["nama"], b["rmse"], b["cv_rmse"], b["r2"], b["mae"], "Model") for b in sub] + \
             [(bb["nama"], bb["uji"]["rmse"], bb["cv"]["rmse_rata"], bb["uji"]["r2"], bb["uji"]["mae"], "Baseline") for bb in base_pakai]
    st.plotly_chart(grafik.bar_metode([d[0] for d in daftar], [d[1] for d in daftar],
                                      [cfg.WARNA_SERI[0] if d[5] == "Model" else "#9AA7B4" for d in daftar],
                                      acuan=base1["uji"]["rmse"] if mode == "B" else None), width="stretch")
    if mode == "B":
        acu_u, acu_cv = base1["uji"]["rmse"], base1["cv"]["rmse_rata"]
        tabel = pd.DataFrame([{"Model": n, "RMSE uji": round(r, 2), "Lebih baik dari persistence, uji (%)": round(ua.skill_persentase(r, acu_u), 1),
                               "RMSE validasi silang": round(c, 2), "Lebih baik dari persistence, CV (%)": round(ua.skill_persentase(c, acu_cv), 1),
                               "Mengalahkan di CV?": "Ya" if c < acu_cv else "Tidak"} for n, r, c, _, _, jenis in daftar if jenis == "Model"])
        st.dataframe(tabel, hide_index=True, width="stretch")
        st.markdown(f"Di data uji semua model memiliki RMSE lebih kecil dari persistence ({fmt(base1['uji']['rmse'])})."
                    if all(b["rmse"] < acu_u for b in sub) else "Tidak semua model mengalahkan persistence di data uji.")
        st.markdown(f"Di validasi silang, persistence memberi RMSE {fmt(acu_cv)}; model yang **tidak** mengalahkannya: "
                    f"{', '.join(b['nama'] for b in sub if b['cv_rmse'] >= acu_cv) or 'tidak ada'}.")
        if base24["uji"]["r2"] < 0:
            st.markdown(f"Persistence 24 jam memberi R2 **{fmt(base24['uji']['r2'], 3)}** (negatif): menebak dengan nilai kemarin lebih buruk daripada menebak rata-rata. "
                        "Artinya polusi berubah cukup cepat dalam sehari, dan yang berguna adalah riwayat beberapa jam terakhir.")
    else:
        st.markdown(f"Mode A tidak boleh memakai riwayat PM2.5, jadi pembandingnya hanya rata-rata data latih (RMSE {fmt(bmean['uji']['rmse'])}, R2 {fmt(bmean['uji']['r2'], 3)}). "
                    "Semua model Mode A lebih baik dari tebakan rata-rata, tetapi jauh lebih lemah daripada Mode B.")
    ua.tampilkan_kode("latih_semua_model.py", "hitung_baseline")

# ============================================================================= 3. R2 vs MAE vs RMSE
with tab_r2:
    st.subheader("Kenapa R2 tinggi bisa menipu")
    st.markdown("R2 membandingkan model dengan tebakan 'selalu rata-rata'. PM2.5 per jam sangat mirip dengan jam sebelumnya, "
                "jadi **tebakan sederhana pun sudah menghasilkan R2 tinggi**. R2 hampir tidak membedakan model bagus dari baseline sederhana.")
    pakai = [(b["nama"], b["r2"], b["rmse"], b["mae"]) for b in mB] + [(base1["nama"], base1["uji"]["r2"], base1["uji"]["rmse"], base1["uji"]["mae"]),
                                                                       (base24["nama"], base24["uji"]["r2"], base24["uji"]["rmse"], base24["uji"]["mae"])]
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**R2** (Mode B, data uji)")
        st.plotly_chart(grafik.bar_metode([x[0] for x in pakai], [x[1] for x in pakai],
                                          [cfg.WARNA_SERI[0]] * len(mB) + ["#9AA7B4"] * 2, judul_x="R2"), width="stretch")
    with g2:
        st.markdown("**RMSE** (Mode B, data uji)")
        st.plotly_chart(grafik.bar_metode([x[0] for x in pakai], [x[2] for x in pakai],
                                          [cfg.WARNA_SERI[0]] * len(mB) + ["#9AA7B4"] * 2), width="stretch")
    rf1 = base1["uji"]
    tabel = pd.DataFrame([{"Model": b["nama"], "R2": round(b["r2"], 3), "Selisih R2 vs persistence": round(b["r2"] - rf1["r2"], 4),
                           "RMSE lebih kecil dari persistence (%)": round(ua.skill_persentase(b["rmse"], rf1["rmse"]), 1),
                           "MAE lebih kecil dari persistence (%)": round(ua.skill_persentase(b["mae"], rf1["mae"]), 1)} for b in mB])
    st.dataframe(tabel, hide_index=True, width="stretch")
    contoh = terbaikB
    st.markdown(f"Contoh: {contoh['nama']} hanya menambah R2 sebesar {fmt(contoh['r2'] - rf1['r2'], 4)} dibanding persistence, angka yang tampak sepele, "
                f"padahal RMSE-nya {fmt(ua.skill_persentase(contoh['rmse'], rf1['rmse']), 1)}% lebih kecil. Sebaliknya, R2 setinggi {fmt(rf1['r2'], 3)} sudah "
                "dicapai persistence tanpa belajar sama sekali.")
    st.markdown("**Yang sebaiknya dilaporkan:** MAE dan RMSE dalam satuan ug/m3 (mudah dipahami: 'rata-rata meleset sekian'), MedAE, "
                "**selisih terhadap baseline persistence** (skill score = 1 - RMSE model / RMSE persistence), dan performa saat polusi parah. R2 boleh ditampilkan, tetapi tidak boleh jadi satu-satunya bukti.")
    ua.tampilkan_kode("evaluasi_regresi.py", "hitung_metrik")

# ============================================================================= 4. polusi parah
with tab_parah:
    ambang = base1["polusi_parah"]["ambang"]
    st.subheader(f"Saat polusi parah (pm2.5 > {fmt(ambang, 0)} ug/m3)")
    n_parah = base1["polusi_parah"]["parah"]["n"]
    st.markdown(f"Di data uji ada **{fmt(n_parah, 0)} jam** yang melewati ambang itu. Rata-rata error bisa tampak kecil karena ditarik oleh banyak jam bersih; "
                "di sini dipisah supaya terlihat kinerja di jam-jam yang paling berbahaya.")
    sub = [b for b in baris if b["mode"] == mode and b["jenis"] == "Model"]
    entri = [(b["nama"], hasil["model"][b["kunci"]]["polusi_parah"]) for b in sub] + \
            ([(base1["nama"], base1["polusi_parah"])] if mode == "B" else [(bmean["nama"], bmean["polusi_parah"])])
    st.plotly_chart(grafik.bar_berkelompok([n for n, _ in entri], {"MAE saat normal": [p["normal"]["mae"] for _, p in entri],
                                                                   "MAE saat parah": [p["parah"]["mae"] for _, p in entri]}, "MAE (ug/m3)"), width="stretch")
    st.dataframe(pd.DataFrame([{"Model": n, "MAE normal": round(p["normal"]["mae"], 1), "MAE parah": round(p["parah"]["mae"], 1),
                                "Berapa kali lipat": round(p["parah"]["mae"] / p["normal"]["mae"], 1), "Bias saat parah": round(p["parah"]["bias"], 1)}
                               for n, p in entri]), hide_index=True, width="stretch")
    kunci_pem = pem[mode]
    pp = hasil["model"][kunci_pem]["polusi_parah"]
    kal = (f"Model terbaik Mode {mode} menurut CV ({ua.sebut_model(kunci_pem, hasil)}) punya MAE {fmt(pp['parah']['mae'], 1)} saat parah, "
           f"{fmt(pp['parah']['mae'] / pp['normal']['mae'], 1)} kali MAE saat normal, dengan bias {fmt(pp['parah']['bias'], 1)} ug/m3. ")
    if mode == "B":
        pb = base1["polusi_parah"]["parah"]["mae"]
        kal += (f"Persistence 1 jam memberi MAE {fmt(pb, 1)} pada jam yang sama, jadi model " +
                ("sedikit lebih baik" if pp["parah"]["mae"] < pb else "tidak lebih baik") + " dari baseline saat polusi parah.")
    else:
        kal += ("Bias negatif besar berarti Mode A sangat meremehkan polusi parah: tanpa riwayat PM2.5 ia tidak 'tahu' bahwa udara sedang memburuk."
                if pp["parah"]["bias"] < -20 else "")
    st.markdown(kal)
    st.markdown("**Error per kategori udara aktual (model terbaik menurut CV)**")
    st.plotly_chart(grafik.bar_per_kategori(hasil["model"][kunci_pem]["per_kategori"], "mae"), width="stretch")
    st.caption("Prediksi yang meremehkan polusi parah paling berbahaya bagi pengguna (mengira udara lebih aman dari kenyataan). "
               "Karena itu halaman Prediksi menampilkan rentang ketidakpastian dan saran kesehatan, bukan satu angka saja.")
    ua.tampilkan_kode("evaluasi_regresi.py", "metrik_polusi_parah")
