"""
eksperimen_ringan.py - pintu masuk eksperimen ringan (Ridge saja, hitungan detik). Dipanggil dari model/latih_semua_model.py.

Eksperimen dipisah per topik supaya mudah dicari:
  eksperimen_preprocessing.py : isi data kosong, skala, log target
  eksperimen_pca.py           : PCA dan SelectKBest
  eksperimen_ablasi.py        : ablasi kelompok fitur
  eksperimen_umum.py          : pembantu bersama (skor_ridge)
Hasilnya masuk hasil.json["eksperimen"]. Catatan: Ridge model linear, jadi kesimpulan ablasi/PCA belum tentu sama
untuk model berbasis pohon.
"""
from preprocessing.eksperimen_ablasi import _eksp_ablasi
from preprocessing.eksperimen_pca import _eksp_pca
from preprocessing.eksperimen_preprocessing import _eksp_isi_kosong, _eksp_skala_dan_log


def jalankan_eksperimen(df_mentah, d_siap, latih, uji, log=print):
    """
    Fungsi: jalankan semua eksperimen ringan.
    Input : df_mentah (hasil muat_data_mentah), d_siap (hasil siapkan_data), latih, uji (hasil bagi_waktu), log.
    Output: dict {skala, log_target, isi_kosong, pca, ablasi, catatan}.
    """
    log("Eksperimen ringan (Ridge): skala dan log target ...")
    skala, log_t = _eksp_skala_dan_log(latih, uji)
    log("Eksperimen ringan: cara isi data kosong ...")
    isi = _eksp_isi_kosong(df_mentah, d_siap["layak_model"].to_numpy())
    log("Eksperimen ringan: PCA dan SelectKBest ...")
    pca = _eksp_pca(latih, uji)
    log("Eksperimen ringan: ablasi kelompok fitur ...")
    ablasi = _eksp_ablasi(latih, uji)
    return {"skala": skala, "log_target": log_t, "isi_kosong": isi, "pca": pca, "ablasi": ablasi,
            "catatan": "Semua eksperimen memakai Ridge (model linear) dan dievaluasi di data uji; "
                       "hasilnya belum tentu sama untuk model berbasis pohon."}
