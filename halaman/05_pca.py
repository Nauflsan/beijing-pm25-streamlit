"""
halaman/05_pca.py - PCA: scree plot, dengan vs tanpa PCA, SelectKBest sebagai pembanding, dan tab "Bukti dan kode".

PCA di proyek ini adalah EKSPERIMEN PEMBANDING (Ridge saja), bukan bagian model final: kelima model final dilatih
tanpa PCA. Semua angka dibaca dari artifacts/hasil.json -> eksperimen -> pca (dihasilkan eksperimen_ringan._eksp_pca).
Kalimat kesimpulan dibangun dari angka, jadi arahnya (PCA membantu atau merugikan) ditentukan data.
"""
import pandas as pd
import streamlit as st

from evaluasi import bukti_kode as bk
from tampilan import grafik
import konfigurasi as cfg
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
tema.header_halaman("PCA", "Apakah mengurangi jumlah kolom lewat PCA membantu model? Dicoba, diukur, lalu diputuskan.")
hasil = ua.hasil_atau_berhenti()
eks = hasil.get("eksperimen")
if not eks or "pca" not in eks:
    st.info("Hasil eksperimen PCA belum ada di hasil.json. Jalankan `python -m model.latih_semua_model --penuh --ulang`.")
    st.stop()

mode = st.radio("Mode fitur", ["A", "B"], horizontal=True, format_func=lambda m: cfg.MODE_FITUR[m])
x = eks["pca"][mode]
n_awal = x["n_fitur_setelah_enkode"]
rm_tanpa = x["tanpa_pca"]["rmse"]
v95 = x["varian"]["0.95"]
sel95 = ua.persen_selisih(v95["metrik"]["rmse"], rm_tanpa)

a, b, c, d = st.columns(4)
with a:
    tema.kartu_kpi("Kolom sebelum PCA", n_awal, "setelah one-hot, dasar perbandingan")
with b:
    tema.kartu_kpi("Komponen untuk 95% varians", v95["n_komponen"], f"mengurangi {n_awal - v95['n_komponen']} kolom")
with c:
    tema.kartu_kpi("RMSE tanpa PCA", fmt(rm_tanpa), "Ridge, data uji, ug/m3")
with d:
    tema.kartu_kpi("RMSE dengan PCA 95%", fmt(v95["metrik"]["rmse"]), f"{'naik' if sel95 > 0 else 'turun'} {fmt(abs(sel95), 1)}% dibanding tanpa PCA")
st.write("")

tab_scree, tab_banding, tab_bukti = st.tabs(["Scree plot", "Dengan vs tanpa PCA", "Bukti dan kode"])

# ----------------------------------------------------------------------------- scree
with tab_scree:
    st.plotly_chart(grafik.scree_plot(x["scree"], x["kumulatif"]), width="stretch")
    pertama = x["scree"][0]
    st.markdown(f"Komponen pertama menjelaskan {fmt(100 * pertama, 1)}% varians; {v95['n_komponen']} komponen dibutuhkan untuk 95%. "
                + (f"Dari {n_awal} kolom awal, tidak ada satu komponen yang mendominasi, artinya informasinya cukup tersebar."
                   if pertama < 0.5 else "Satu komponen menjelaskan lebih dari separuh varians, artinya kolom-kolomnya sangat saling berkaitan."))
    st.caption("PCA dihitung pada fitur yang sudah di-one-hot dan distandarkan (PCA peka skala), HANYA dari data latih. "
               "Scree plot menunjukkan seberapa besar varians tiap komponen; bukan seberapa berguna komponen itu untuk memprediksi PM2.5.")

# ----------------------------------------------------------------------------- dengan vs tanpa
with tab_banding:
    baris = [("Tanpa PCA (semua kolom)", n_awal, x["tanpa_pca"], cfg.WARNA_SERI[0])]
    for kunci, v in x["varian"].items():
        baris.append((f"PCA, pertahankan {int(float(kunci) * 100)}% varians", v["n_komponen"], v["metrik"], cfg.WARNA_SERI[1]))
    for k, m in x["select_k_best"].items():
        baris.append((f"SelectKBest, pilih {k} kolom", int(k), m, cfg.WARNA_SERI[3]))
    tabel = pd.DataFrame([{"Metode": n, "Jumlah kolom": jml, "RMSE": round(m["rmse"], 2), "MAE": round(m["mae"], 2),
                           "R2": round(m["r2"], 3), "RMSE vs tanpa PCA (%)": round(ua.persen_selisih(m["rmse"], rm_tanpa), 1)}
                          for n, jml, m, _ in baris])
    st.plotly_chart(grafik.bar_metode([n for n, *_ in baris], [m["rmse"] for _, _, m, _ in baris], [w for *_, w in baris],
                                      acuan=rm_tanpa), width="stretch")
    st.dataframe(tabel, hide_index=True, width="stretch")

    pca_rows = [(n, jml, m) for n, jml, m, w in baris if n.startswith("PCA")]
    kbest_rows = [(n, jml, m) for n, jml, m, w in baris if n.startswith("SelectKBest")]
    terbaik_pca = min(pca_rows, key=lambda t: t[2]["rmse"])
    sel_t = ua.persen_selisih(terbaik_pca[2]["rmse"], rm_tanpa)
    kalimat = [f"PCA **berhasil mengurangi kolom** (mis. dari {n_awal} menjadi {v95['n_komponen']} pada 95% varians). "]
    if all(m["rmse"] > rm_tanpa for _, _, m in pca_rows):
        kalimat.append(f"Tetapi **semua varian PCA memberi RMSE lebih tinggi** dari tanpa PCA; yang terbaik ({terbaik_pca[0]}, {terbaik_pca[1]} komponen) "
                       f"masih {fmt(abs(sel_t), 1)}% lebih buruk. Jadi pengurangan kolom ini dibayar dengan akurasi.")
    elif all(m["rmse"] <= rm_tanpa for _, _, m in pca_rows):
        kalimat.append(f"Dan semua varian PCA memberi RMSE sama atau lebih baik dari tanpa PCA (terbaik {terbaik_pca[0]}, {fmt(abs(sel_t), 1)}% lebih rendah).")
    else:
        kalimat.append("Hasilnya campuran: sebagian varian PCA lebih baik dan sebagian lebih buruk dari tanpa PCA; lihat tabel.")
    if kbest_rows:
        kb = max(kbest_rows, key=lambda t: t[1])
        sel_kb = ua.persen_selisih(kb[2]["rmse"], rm_tanpa)
        kalimat.append(f" Sebagai pembanding, {kb[0]} (dari {n_awal} kolom) memberi RMSE {'hanya ' if abs(sel_kb) < 2 else ''}"
                       f"{fmt(abs(sel_kb), 1)}% {'lebih tinggi' if sel_kb > 0 else 'lebih rendah'} dibanding tanpa seleksi.")
    st.markdown("".join(kalimat))
    st.markdown("**Keputusan:** kelima model final dilatih **tanpa PCA**. PCA hanya dicoba sebagai eksperimen pembanding dengan Ridge.")
    st.caption("Dugaan kenapa PCA kurang membantu (belum diuji lebih jauh): PCA mengurutkan komponen berdasarkan varians, bukan berdasarkan "
               "kegunaannya untuk menebak pm2.5. Fitur yang paling berguna (misalnya riwayat PM2.5 1 jam lalu) bisa tercampur dengan fitur "
               "lain yang mirip, dan sebagian informasinya ikut terbuang bersama komponen bervarians kecil. SelectKBest memilih kolom "
               "berdasarkan hubungannya dengan target, sehingga lebih aman di sini.")

# ----------------------------------------------------------------------------- bukti dan kode
with tab_bukti:
    meta = hasil["meta"]
    st.markdown("**Pertanyaan: mana buktinya PCA mengurangi kolom, dan memang sudah dijalankan?**")
    tema.kotak_catatan("Jawaban singkat: PCA dijalankan oleh skrip latih (bagian eksperimen ringan), hasilnya tersimpan di "
                       "artifacts/hasil.json, dan kodenya bisa dilihat serta dijalankan ulang untuk membuktikan angkanya sama.")
    st.markdown(
        f"1. **Datanya:** `artifacts/hasil.json` -> `eksperimen` -> `pca` -> `{mode}`. Isinya jumlah kolom awal ({n_awal}), "
        f"jumlah komponen untuk 80/90/95/99% varians ({', '.join(str(v['n_komponen']) for v in x['varian'].values())}), "
        f"dan RMSE tiap varian.\n"
        f"2. **Kapan dan dengan apa dijalankan:** hasil.json diperbarui `{meta.get('diperbarui', '-')}`, profil `{meta.get('profil_terakhir', '-')}`, "
        f"Python {meta.get('versi', {}).get('python', '-')}, scikit-learn {meta.get('versi', {}).get('scikit_learn', '-')}, "
        f"seed {meta.get('seed', '-')}.\n"
        f"3. **Dipanggil dari:** `{bk.lokasi_kode('latih_semua_model.py', 'main')}` -> `eksperimen_ringan.jalankan_eksperimen` "
        f"({bk.lokasi_kode('eksperimen_ringan.py', 'jalankan_eksperimen')}). Di log training tercatat baris "
        f"`Eksperimen ringan: PCA dan SelectKBest ...`.\n"
        f"4. **Dijalankan ulang untuk membuktikan:** `python -m evaluasi.bukti_eksperimen --bagian pca` menghitung ulang PCA dari data dan "
        f"membandingkannya dengan hasil.json angka demi angka (hasilnya harus COCOK).")
    st.caption("PCA hanya eksperimen (Ridge). Model final tidak memakai PCA, lihat `buat_pipeline` di fitur_waktu.py: hanya preprocessor + estimator.")
    ua.tampilkan_kode("eksperimen_pca.py", "_eksp_pca")
    ua.tampilkan_kode("eksperimen_ringan.py", "jalankan_eksperimen")
    ua.tampilkan_kode("fitur_waktu.py", "buat_pipeline")
