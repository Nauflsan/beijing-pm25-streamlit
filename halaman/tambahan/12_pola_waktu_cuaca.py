"""
halaman/tambahan/12_pola_waktu_cuaca.py - Pola Waktu & Cuaca: heatmap jam x bulan, pola musiman, pola harian, dan arah angin x bulan.

Semua dari CSV (tidak butuh hasil training). Kalimat interpretasi dibangun dari angka (jam/bulan puncak dihitung, bukan ditulis tangan).
Pola ini menjadi alasan memakai fitur waktu siklik (jam dan bulan) di halaman Preprocessing dan Feature Engineering.
"""
import streamlit as st

import konfigurasi as cfg
from tampilan import grafik
from tampilan import tema_langit_beijing as tema
from tampilan import utilitas_app as ua

fmt = ua.fmt
T = cfg.KOLOM_TARGET
df = ua.muat_data()
tema.header_halaman("Pola Waktu dan Cuaca", "Kapan polusi biasanya tinggi: menurut jam, bulan, tahun, dan arah angin.")

tab_hm, tab_musim, tab_jam, tab_angin = st.tabs(["Heatmap jam x bulan", "Musiman per tahun", "Pola harian", "Arah angin x bulan"])

with tab_hm:
    pivot = df.pivot_table(index="hour", columns="month", values=T, aggfunc="mean")
    pivot.columns = [grafik.BULAN[m - 1] for m in pivot.columns]
    st.plotly_chart(grafik.heatmap_pola(pivot), width="stretch")
    jam_p, bulan_p = pivot.stack().idxmax()
    jam_r, bulan_r = pivot.stack().idxmin()
    st.markdown(f"Rata-rata tertinggi pada jam **{jam_p}** di bulan **{bulan_p}** ({fmt(pivot.stack().max(), 1)} ug/m3) dan terendah pada jam **{jam_r}** "
                f"di bulan **{bulan_r}** ({fmt(pivot.stack().min(), 1)} ug/m3). Sumbu vertikal = jam (0-23), horizontal = bulan.")
    st.caption("Ada pola jam dan pola bulan sekaligus, sehingga keduanya dimasukkan sebagai fitur (dalam bentuk sin-cos).")

with tab_musim:
    pt = df.pivot_table(index="month", columns="year", values=T, aggfunc="mean")
    pt.index = [grafik.BULAN[m - 1] for m in pt.index]
    st.plotly_chart(grafik.garis_banyak(pt, "Bulan"), width="stretch")
    rata_bulan = df.groupby("month")[T].mean()
    st.markdown(f"Rata-rata bulanan tertinggi di **{grafik.BULAN[int(rata_bulan.idxmax()) - 1]}** ({fmt(rata_bulan.max(), 1)}) dan terendah di "
                f"**{grafik.BULAN[int(rata_bulan.idxmin()) - 1]}** ({fmt(rata_bulan.min(), 1)}) menurut seluruh data. Garis tiap tahun menunjukkan "
                "apakah pola musim berulang; kalau garisnya berjauhan, pola musim saja tidak cukup untuk meramal tahun berikutnya.")

with tab_jam:
    per_jam = df.groupby("hour")[T].agg(["mean", "median"]).rename(columns={"mean": "rata-rata", "median": "median"})
    st.plotly_chart(grafik.garis_banyak(per_jam, "Jam dalam sehari"), width="stretch")
    rentang_jam = per_jam["rata-rata"].max() - per_jam["rata-rata"].min()
    sebaran_harian = df.groupby(df["waktu"].dt.date)[T].mean().std()
    st.markdown(f"Rata-rata tertinggi pada jam **{int(per_jam['rata-rata'].idxmax())}** ({fmt(per_jam['rata-rata'].max(), 1)}) dan terendah pada jam "
                f"**{int(per_jam['rata-rata'].idxmin())}** ({fmt(per_jam['rata-rata'].min(), 1)}), selisih {fmt(rentang_jam, 1)} ug/m3. "
                f"Sebagai pembanding, simpangan baku rata-rata HARIAN {fmt(sebaran_harian, 1)} ug/m3, jadi pola jam "
                + ("lebih kecil daripada perbedaan antar hari: jam saja tidak banyak menjelaskan polusi." if rentang_jam < sebaran_harian
                   else "cukup besar dibanding perbedaan antar hari."))

with tab_angin:
    pa = df.pivot_table(index=cfg.KOLOM_ARAH_ANGIN, columns="month", values=T, aggfunc="mean").reindex(cfg.KELAS_ARAH_ANGIN)
    pa.columns = [grafik.BULAN[m - 1] for m in pa.columns]
    st.plotly_chart(grafik.heatmap_pola(pa), width="stretch")
    rata_arah = df.groupby(cfg.KOLOM_ARAH_ANGIN)[T].mean().reindex(cfg.KELAS_ARAH_ANGIN)
    st.markdown("Rata-rata menurut arah angin: " + ", ".join(f"**{k}** {fmt(v, 1)}" for k, v in rata_arah.items()) +
                f". Arah **{rata_arah.idxmax()}** tertinggi dan **{rata_arah.idxmin()}** terendah. Kotak yang kosong berarti arah itu tidak pernah muncul di bulan tersebut.")
    st.caption("Arah angin dan bulan saling terkait (arah tertentu lebih sering di musim tertentu), jadi perbedaan ini tidak bisa langsung "
               "dibaca sebagai pengaruh arah angin saja.")
