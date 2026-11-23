"""
bukti_eksperimen.py - MEMBUKTIKAN angka eksperimen di hasil.json: hitung ulang dari data, bandingkan angka demi angka.

Cara pakai (di folder proyek, env aktif):
  python -m evaluasi.bukti_eksperimen                    # semua eksperimen (Ridge, hitungan detik)
  python -m evaluasi.bukti_eksperimen --bagian pca       # hanya PCA   (pilihan: pca, isi_kosong, skala, log_target, ablasi)
  python -m evaluasi.bukti_eksperimen --dummy            # uji alur terhadap artifacts_dummy/ (sampel 2.000 baris)

Hasil: tiap bagian dicetak COCOK atau BEDA (beserta angka yang berbeda). Toleransi 1e-6 relatif. Kalau BEDA, penyebab
paling umum: versi library berbeda dari saat training (lihat meta di hasil.json), atau hasil.json berasal dari profil/sampel lain.
Memakai fungsi yang SAMA dengan yang dipakai saat training (eksperimen_ringan.py), bukan salinan.
"""
import argparse
import math
import sys

from preprocessing import eksperimen_ablasi, eksperimen_pca, eksperimen_preprocessing
import konfigurasi as cfg
from model import latih_semua_model as lt
from preprocessing import utilitas_data as ud

BAGIAN = ["pca", "isi_kosong", "skala", "log_target", "ablasi"]
TOL = 1e-6


def bandingkan(a, b, jalur="", beda=None):
    """
    Fungsi: bandingkan dua struktur (dict/list/angka) secara rekursif. Input: a (hasil hitung ulang), b (isi hasil.json),
            jalur (teks lokasi), beda (list penampung). Output: list perbedaan [(jalur, a, b)].
    """
    beda = [] if beda is None else beda
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                beda.append((f"{jalur}/{k}", a.get(k, "(tidak ada)"), b.get(k, "(tidak ada)")))
            else:
                bandingkan(a[k], b[k], f"{jalur}/{k}", beda)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            beda.append((jalur + " (panjang)", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            bandingkan(x, y, f"{jalur}[{i}]", beda)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not math.isclose(float(a), float(b), rel_tol=TOL, abs_tol=1e-9):
            beda.append((jalur, a, b))
    elif a != b:
        beda.append((jalur, a, b))
    return beda


def hitung_ulang(data, bagian):
    """Fungsi: hitung ulang satu bagian eksperimen dengan fungsi training yang asli. Input: objek Data, nama bagian. Output: struktur."""
    if bagian == "pca":
        return eksperimen_pca._eksp_pca(data.latih, data.uji)
    if bagian == "isi_kosong":
        return eksperimen_preprocessing._eksp_isi_kosong(data.df_mentah, data.d["layak_model"].to_numpy())
    if bagian == "ablasi":
        return eksperimen_ablasi._eksp_ablasi(data.latih, data.uji)
    skala, log_t = eksperimen_preprocessing._eksp_skala_dan_log(data.latih, data.uji)
    return skala if bagian == "skala" else log_t


def main(argv=None):
    """Fungsi: jalankan pembuktian. Input: argumen CLI. Output: kode keluar 0 (semua cocok) atau 1."""
    ap = argparse.ArgumentParser(description="Hitung ulang eksperimen dan bandingkan dengan hasil.json")
    ap.add_argument("--bagian", choices=BAGIAN + ["semua"], default="semua")
    ap.add_argument("--dummy", action="store_true", help="bandingkan dengan artifacts_dummy/ (sampel 2.000 baris)")
    args = ap.parse_args(argv)
    folder = cfg.FOLDER_ARTEFAK_DUMMY if args.dummy else cfg.FOLDER_ARTEFAK
    hasil = ud.muat_json(folder / cfg.NAMA_FILE_HASIL)
    if "eksperimen" not in hasil:
        print(f"hasil.json di {folder} tidak punya bagian 'eksperimen'. Jalankan latih_semua_model.py dulu.")
        return 1
    print(f"Membandingkan dengan {folder / cfg.NAMA_FILE_HASIL}")
    print(f"hasil.json dibuat {hasil['meta'].get('diperbarui')} | profil {hasil['meta'].get('profil_terakhir')} | "
          f"library saat training: {hasil['meta'].get('versi')}")
    data = lt.Data(sampel=2000 if args.dummy else None)
    gagal = 0
    for bagian in (BAGIAN if args.bagian == "semua" else [args.bagian]):
        baru = hitung_ulang(data, bagian)
        beda = bandingkan(baru, hasil["eksperimen"][bagian], bagian)
        print(f"\n[{bagian}] " + ("COCOK, semua angka sama dengan hasil.json" if not beda else f"BEDA di {len(beda)} nilai"))
        for jalur, a, b in beda[:8]:
            print(f"    {jalur}: hitung ulang = {a} | hasil.json = {b}")
        if bagian == "pca" and not beda:
            for mode in ("A", "B"):
                x = baru[mode]
                print(f"    Mode {mode}: {x['n_fitur_setelah_enkode']} kolom awal -> " +
                      ", ".join(f"{int(float(k) * 100)}% varians = {v['n_komponen']} komponen (RMSE {v['metrik']['rmse']:.2f})"
                                for k, v in x["varian"].items()) + f" | tanpa PCA RMSE {x['tanpa_pca']['rmse']:.2f}")
        gagal += bool(beda)
    print("\nSEMUA COCOK" if not gagal else f"\n{gagal} bagian BEDA")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
