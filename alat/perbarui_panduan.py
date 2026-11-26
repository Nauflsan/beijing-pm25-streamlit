"""
perbarui_panduan.py - mengisi ulang angka dan tabel di PANDUAN_HALAMAN.md dan PANDUAN_KODE.md dari artifacts/hasil.json dan CSV.

Jalankan setiap selesai training ulang:   python -m alat.perbarui_panduan
(untuk uji dengan artefak dummy:           python -m alat.perbarui_panduan --dummy)

Yang diisi ulang hanya yang dibungkus penanda:
  <!--ANGKA:kunci-->nilai<!--/ANGKA-->           angka satu baris
  <!--BLOK:nama-->isi<!--/BLOK-->                blok (tabel, tanya-jawab)
Teks di luar penanda tidak disentuh. Kunci yang tidak dikenal menghentikan skrip dengan pesan jelas.
"""
import argparse
import re
import sys

import konfigurasi as cfg
from evaluasi import bukti_kode as bk
from evaluasi import kategori_udara as ku
from preprocessing import peta_fitur as pf
from preprocessing import utilitas_data as ud

FILE_PANDUAN = [cfg.FOLDER_PROYEK / "dokumen" / n for n in ("PANDUAN_HALAMAN.md", "PANDUAN_KODE.md", "PRESENTASI.md", "LATIHAN_TANYA_JAWAB.md")]


def kumpulkan_angka(hasil, df):
    """
    Fungsi: semua nilai untuk penanda ANGKA. Angka dataset dari CSV, angka fitur dari hasil.json.
    Input : dict hasil.json, DataFrame mentah. Output: dict {kunci: teks}.
    """
    ring = ud.ringkasan_dataset(df)
    r = pf.ringkasan_jumlah(hasil)
    f1 = lambda x: ud.fmt_id(x, 1)
    f2 = lambda x: ud.fmt_id(x, 2)
    eks = hasil.get("eksperimen", {})
    pca = {m: eks.get("pca", {}).get(m) for m in ("A", "B")}
    pers = lambda a, b: (a - b) / b * 100
    ekstra = {}
    if pca["A"] and pca["B"]:
        for m in ("A", "B"):
            x, k = pca[m], m.lower()
            ekstra.update({f"pca_awal_{k}": str(x["n_fitur_setelah_enkode"]), f"pca_k95_{k}": str(x["varian"]["0.95"]["n_komponen"]),
                           f"pca_rmse95_{k}": f2(x["varian"]["0.95"]["metrik"]["rmse"]), f"pca_rmse_tanpa_{k}": f2(x["tanpa_pca"]["rmse"]),
                           f"pca_naik_{k}": f1(pers(x["varian"]["0.95"]["metrik"]["rmse"], x["tanpa_pca"]["rmse"]))})
        ekstra["kbest15_rmse_b"] = f2(pca["B"]["select_k_best"]["15"]["rmse"])
    if eks:
        isi, lg, sk = eks["isi_kosong"], eks["log_target"], eks["skala"]
        ekstra.update({"isi_ffill": f2(isi["ffill"]["rmse"]), "isi_median": f2(isi["median_latih"]["rmse"]),
                       "isi_interp": f2(isi["interpolasi_bocor"]["rmse"]),
                       "log_a_asli": f2(lg["A"]["skala_asli"]["rmse"]), "log_a_log": f2(lg["A"]["target_log1p"]["rmse"]),
                       "log_b_asli": f2(lg["B"]["skala_asli"]["rmse"]), "log_b_log": f2(lg["B"]["target_log1p"]["rmse"]),
                       "skala_b_dengan": ud.fmt_id(sk["B"]["dengan_skala"]["rmse"], 3), "skala_b_tanpa": ud.fmt_id(sk["B"]["tanpa_skala"]["rmse"], 3)})
    pem = hasil.get("pemenang", {})
    for m in ("A", "B"):
        if pem.get(m):
            pp = hasil["model"][pem[m]]["polusi_parah"]
            ekstra[f"parah_{m.lower()}_kali"] = f1(pp["parah"]["mae"] / pp["normal"]["mae"])
    # --- model, baseline, skill, PSO, uji kejujuran, polusi parah (halaman 6-8)
    f3 = lambda x: ud.fmt_id(x, 3)
    b1 = hasil["baseline"]["persistence_1jam"]
    for kunci, m in hasil["model"].items():
        for met, desimal in (("rmse", 2), ("mae", 2), ("medae", 2), ("r2", 3)):
            ekstra[f"m_{kunci}_{met}"] = ud.fmt_id(m["uji"][met], desimal)
        ekstra[f"cv_{kunci}"] = f2(m["cv"]["rmse_rata"])
        if m["mode"] == "B":
            ekstra[f"skill_{kunci}"] = f1((1 - m["uji"]["rmse"] / b1["uji"]["rmse"]) * 100)
    for kunci, b in hasil["baseline"].items():
        ekstra.update({f"b_{kunci}_rmse": f2(b["uji"]["rmse"]), f"b_{kunci}_mae": f2(b["uji"]["mae"]),
                       f"b_{kunci}_r2": f3(b["uji"]["r2"]), f"b_{kunci}_cv": f2(b["cv"]["rmse_rata"])})
    mB = [m for m in hasil["model"].values() if m["mode"] == "B"]
    ekstra["n_menang_cv_b"] = str(sum(1 for m in mB if m["cv"]["rmse_rata"] < b1["cv"]["rmse_rata"]))
    ekstra["n_model_b"] = str(len(mB))
    ekstra["total_waktu_detik"] = ud.fmt_id(sum(m["waktu_cv_detik"] + m["waktu_latih_detik"] for m in hasil["model"].values()), 0)
    ekstra["total_mb"] = f1(sum(m["ukuran_file_mb"] for m in hasil["model"].values()))
    if "pso" in hasil:
        ps = hasil["pso"]
        ekstra.update({"pso_fit_pembanding": f2(ps["rmse_cv_pembanding"]), "pso_fit_terbaik": f2(ps["rmse_cv_terbaik"]),
                       "pso_n_eval": str(ps["n_evaluasi"]), "pso_detik": ud.fmt_id(ps["waktu_detik"], 0),
                       "pso_partikel": str(ps["pengaturan"]["partikel"]), "pso_iterasi": str(ps["pengaturan"]["iterasi"]),
                       "pso_n_estimators": str(ps["parameter_terbaik"]["n_estimators"]), "pso_max_depth": str(ps["parameter_terbaik"]["max_depth"]),
                       "pso_min_leaf": str(ps["parameter_terbaik"]["min_samples_leaf"])})
    uk = hasil.get("uji_kejujuran")
    if uk:
        for md in ("A", "B"):
            ekstra[f"uj_acak_r2_{md.lower()}"] = f3(uk[md]["split_acak"]["uji"]["r2"])
            ekstra[f"uj_waktu_r2_{md.lower()}"] = f3(uk[md]["split_waktu"]["uji"]["r2"])
    for md in ("A", "B"):
        k = pem.get(md)
        if not k:
            continue
        m = hasil["model"][k]
        ekstra[f"pem_{md.lower()}_nama"] = m["nama"]
        ekstra[f"pem_{md.lower()}_cv"] = f2(m["cv"]["rmse_rata"])
        pp = m["polusi_parah"]
        ekstra[f"pem_{md.lower()}_parah_mae"] = f1(pp["parah"]["mae"])
        ekstra[f"pem_{md.lower()}_parah_bias"] = f1(pp["parah"]["bias"])
        ekstra[f"kq05_{md.lower()}"] = f1(m["kuantil_residual"]["global"]["0.05"])
        ekstra[f"kq95_{md.lower()}"] = f1(m["kuantil_residual"]["global"]["0.95"])
        inter = hasil.get("interpretasi", {}).get(md)
        if inter:
            ekstra[f"imp_top_{md.lower()}"] = inter["permutation"][0]["fitur"]
            ekstra[f"imp_top_{md.lower()}_nilai"] = f1(inter["permutation"][0]["naik_rmse"])
    # model terbaik menurut DATA UJI per mode (bukan menurut CV; keduanya ditampilkan di dokumen presentasi)
    for md in ("A", "B"):
        kandidat = [m for m in hasil["model"].values() if m["mode"] == md]
        tb = min(kandidat, key=lambda m: m["uji"]["rmse"])
        k = md.lower()
        ekstra.update({f"terbaik_uji_{k}_nama": tb["nama"], f"terbaik_uji_{k}_rmse": f2(tb["uji"]["rmse"]), f"terbaik_uji_{k}_mae": f2(tb["uji"]["mae"]),
                       f"terbaik_uji_{k}_r2": f3(tb["uji"]["r2"])})
        pm_ = hasil["model"][pem[md]]
        ekstra.update({f"pem_{k}_rmse": f2(pm_["uji"]["rmse"]), f"pem_{k}_mae": f2(pm_["uji"]["mae"]), f"pem_{k}_r2": f3(pm_["uji"]["r2"])})
    ekstra["terbaik_uji_b_skill"] = f1((1 - min(m["uji"]["rmse"] for m in mB) / b1["uji"]["rmse"]) * 100)
    ekstra["n_lag_roll"] = str(r["selisih_b_a"])
    ekstra["parah_n"] = ud.fmt_id(b1["polusi_parah"]["parah"]["n"], 0)
    ekstra["b_persist_parah_mae"] = f1(b1["polusi_parah"]["parah"]["mae"])
    ekstra.update({"n_latih": ud.fmt_id(hasil["data"]["n_latih"], 0), "n_uji": ud.fmt_id(hasil["data"]["n_uji"], 0)})
    return {**ekstra,
        "n_baris": ud.fmt_id(ring["n_baris"], 0),
        "tahun_awal": ring["waktu_awal"][:4], "tahun_akhir": ring["waktu_akhir"][:4],
        "n_kosong": ud.fmt_id(ring["n_kosong_target"], 0), "persen_kosong": ud.fmt_id(ring["persen_kosong_target"], 2),
        "mean": ud.fmt_id(ring["pm25_mean"], 1), "median": ud.fmt_id(ring["pm25_median"], 1),
        "skew": ud.fmt_id(ring["pm25_skew"], 2), "n_outlier_iqr": ud.fmt_id(ring["n_outlier_iqr"], 0),
        "kategori_rata": cfg.NAMA_KATEGORI[ku.indeks_kategori(ring["pm25_mean"])],
        "n_kolom_csv": str(r["n_kolom_csv"]), "n_dibuang": str(r["n_dibuang"]),
        "n_fitur_a": str(r["n_fitur_a"]), "n_fitur_b": str(r["n_fitur_b"]),
        "n_enkode_a": str(r["n_enkode_a"]), "n_enkode_b": str(r["n_enkode_b"]),
    }


def kumpulkan_blok(hasil):
    """Fungsi: isi tiap penanda BLOK. Input: dict hasil.json. Output: dict {nama: teks markdown}."""
    tabel, peringatan = pf.bangun_tabel(hasil)
    teks_tabel = pf.tabel_ke_markdown(tabel)
    if peringatan:
        teks_tabel += "\n\n" + "\n".join(f"> PERINGATAN: {p}" for p in peringatan)
    tj = "\n\n".join(f"**{i}. {q}**\n\n{a}" for i, (q, a) in enumerate(pf.pertanyaan_dosen(hasil), 1))
    peta = pf.tabel_ke_markdown(__import__("pandas").DataFrame(bk.tabel_peta()))
    return {"tabel_kolom_ke_fitur": teks_tabel, "tanya_jawab_fitur": tj, "peta_hasil": peta}


def isi_ulang(teks, angka, blok):
    """
    Fungsi: ganti isi semua penanda. Input: teks markdown, dict angka, dict blok. Output: (teks baru, jumlah diganti).
    Error (SystemExit) kalau ada kunci penanda yang tidak dikenal.
    """
    diganti = {"n": 0}

    def ganti_angka(m):
        """Fungsi: pengganti regex untuk satu penanda ANGKA. Input: objek match. Output: teks penanda berisi angka baru (keluar dengan pesan kalau kunci tidak dikenal)."""
        if m.group(1) not in angka:
            sys.exit(f"Kunci ANGKA tidak dikenal di PANDUAN_HALAMAN.md: {m.group(1)}")
        diganti["n"] += 1
        return f"<!--ANGKA:{m.group(1)}-->{angka[m.group(1)]}<!--/ANGKA-->"

    def ganti_blok(m):
        """Fungsi: pengganti regex untuk satu penanda BLOK. Input: objek match. Output: teks penanda berisi blok baru (keluar dengan pesan kalau kunci tidak dikenal)."""
        if m.group(1) not in blok:
            sys.exit(f"Kunci BLOK tidak dikenal di PANDUAN_HALAMAN.md: {m.group(1)}")
        diganti["n"] += 1
        return f"<!--BLOK:{m.group(1)}-->\n{blok[m.group(1)]}\n<!--/BLOK-->"

    teks = re.sub(r"<!--ANGKA:(\w+)-->.*?<!--/ANGKA-->", ganti_angka, teks, flags=re.S)
    teks = re.sub(r"<!--BLOK:(\w+)-->.*?<!--/BLOK-->", ganti_blok, teks, flags=re.S)
    return teks, diganti["n"]


def main():
    """Fungsi: baca hasil.json + CSV, isi ulang PANDUAN_HALAMAN.md. Output: -"""
    ap = argparse.ArgumentParser(description="Isi ulang angka di PANDUAN_HALAMAN.md dari hasil.json")
    ap.add_argument("--dummy", action="store_true", help="pakai artifacts_dummy/ (hanya untuk uji)")
    args = ap.parse_args()
    folder = cfg.FOLDER_ARTEFAK_DUMMY if args.dummy else cfg.FOLDER_ARTEFAK
    hasil = ud.muat_json(folder / cfg.NAMA_FILE_HASIL)
    if not hasil or "model" not in hasil:
        sys.exit(f"hasil.json tidak ditemukan di {folder}. Jalankan latih_semua_model.py dulu.")
    if hasil.get("meta", {}).get("dummy") and not args.dummy:
        sys.exit("hasil.json ini bertanda DUMMY. Jalankan training asli dulu (--penuh).")
    df = ud.muat_data_mentah()
    angka, blok = kumpulkan_angka(hasil, df), kumpulkan_blok(hasil)
    for berkas in FILE_PANDUAN:
        if not berkas.exists():
            print(f"(lewati {berkas.name}: file tidak ada)")
            continue
        baru, n = isi_ulang(berkas.read_text(encoding="utf-8"), angka, blok)
        berkas.write_text(baru, encoding="utf-8")
        print(f"{berkas.name} diperbarui: {n} penanda diisi ulang dari {folder / cfg.NAMA_FILE_HASIL}")
    from alat import buat_kamus_fungsi
    path_kamus, n_file, kosong = buat_kamus_fungsi.tulis()
    print(f"{path_kamus.name} dibuat ulang: {n_file} file kode dibaca, {kosong} fungsi tanpa docstring.")
    if hasil.get("meta", {}).get("dummy"):
        print("Catatan: ini dari artefak DUMMY; angka fitur sama dengan hasil asli, tetapi jalankan ulang tanpa --dummy setelah training penuh.")


if __name__ == "__main__":
    main()
