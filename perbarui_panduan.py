"""
perbarui_panduan.py - mengisi ulang angka dan tabel di PANDUAN_HALAMAN.md dari artifacts/hasil.json dan CSV.

Jalankan setiap selesai training ulang:   python perbarui_panduan.py
(untuk uji dengan artefak dummy:           python perbarui_panduan.py --dummy)

Yang diisi ulang hanya yang dibungkus penanda:
  <!--ANGKA:kunci-->nilai<!--/ANGKA-->           angka satu baris
  <!--BLOK:nama-->isi<!--/BLOK-->                blok (tabel, tanya-jawab)
Teks di luar penanda tidak disentuh. Kunci yang tidak dikenal menghentikan skrip dengan pesan jelas.
"""
import argparse
import re
import sys

import konfigurasi as cfg
import kategori_udara as ku
import peta_fitur as pf
import utilitas_data as ud

FILE_PANDUAN = cfg.FOLDER_PROYEK / "PANDUAN_HALAMAN.md"


def kumpulkan_angka(hasil, df):
    """
    Fungsi: semua nilai untuk penanda ANGKA. Angka dataset dari CSV, angka fitur dari hasil.json.
    Input : dict hasil.json, DataFrame mentah. Output: dict {kunci: teks}.
    """
    ring = ud.ringkasan_dataset(df)
    r = pf.ringkasan_jumlah(hasil)
    return {
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
    return {"tabel_kolom_ke_fitur": teks_tabel, "tanya_jawab_fitur": tj}


def isi_ulang(teks, angka, blok):
    """
    Fungsi: ganti isi semua penanda. Input: teks markdown, dict angka, dict blok. Output: (teks baru, jumlah diganti).
    Error (SystemExit) kalau ada kunci penanda yang tidak dikenal.
    """
    diganti = {"n": 0}

    def ganti_angka(m):
        if m.group(1) not in angka:
            sys.exit(f"Kunci ANGKA tidak dikenal di PANDUAN_HALAMAN.md: {m.group(1)}")
        diganti["n"] += 1
        return f"<!--ANGKA:{m.group(1)}-->{angka[m.group(1)]}<!--/ANGKA-->"

    def ganti_blok(m):
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
    teks = FILE_PANDUAN.read_text(encoding="utf-8")
    baru, n = isi_ulang(teks, kumpulkan_angka(hasil, df), kumpulkan_blok(hasil))
    FILE_PANDUAN.write_text(baru, encoding="utf-8")
    print(f"PANDUAN_HALAMAN.md diperbarui: {n} penanda diisi ulang dari {folder / cfg.NAMA_FILE_HASIL}")
    if hasil.get("meta", {}).get("dummy"):
        print("Catatan: ini dari artefak DUMMY; angka fitur sama dengan hasil asli, tetapi jalankan ulang tanpa --dummy setelah training penuh.")


if __name__ == "__main__":
    main()
