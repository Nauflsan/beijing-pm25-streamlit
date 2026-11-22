"""
peta_fitur.py - tabel "Dari 13 kolom CSV ke fitur model".

SEMUA JUMLAH dibaca dari hasil.json (kunci "data" -> "n_kolom_asli", "fitur" -> "A"/"B",
dan "model" -> <kunci> -> "n_fitur_setelah_enkode"), bukan ditulis tangan. Yang ditulis tangan hanya
ATURAN (diapakan + alasan) per kolom, karena itu keputusan desain, bukan angka hasil.

Dipakai oleh: halaman/04_preprocessing.py dan perbarui_panduan.py (PANDUAN_HALAMAN.md).
File ini tidak mengimpor streamlit.
"""
import pandas as pd

import konfigurasi as cfg
import utilitas_data as ud

# [TERKAIT] kalau kolom baru ditambah di fitur_waktu.py, tambahkan awalan namanya ke "awalan" di bawah,
# kalau tidak muncul peringatan "fitur belum terpetakan" di halaman Preprocessing.
_LAG = ", ".join(str(k) for k in cfg.LAG_JAM)
_ROLL = ", ".join(str(w) for w in cfg.JENDELA_ROLLING_JAM)

ATURAN = [
    {"kolom": "No", "aksi": "Dibuang", "awalan": (), "tepat": (),
     "alasan": "Nomor urut baris. Tidak membawa informasi cuaca atau waktu; kalau dipakai, model hanya menghafal urutan."},
    {"kolom": "year", "aksi": "Dibuang dari fitur (dipakai untuk membentuk waktu dan membagi data)", "awalan": (), "tepat": (),
     "alasan": f"Data uji (tahun >= {cfg.TAHUN_UJI_MULAI}) berada di luar rentang tahun data latih, jadi angka tahun tidak bisa "
               "dipelajari dengan benar. Tahun dipakai untuk split waktu."},
    {"kolom": "month", "aksi": "Diubah sin-cos (bulan_sin, bulan_cos)", "awalan": ("bulan_",), "tepat": (),
     "alasan": "Bulan 12 dan bulan 1 sebenarnya bertetangga. Angka biasa 1-12 membuat model mengira keduanya jauh; "
               "pasangan sin-cos membentuk 'lingkaran' bulan."},
    {"kolom": "day", "aksi": "Dibuang dari fitur (dipakai untuk membentuk waktu)", "awalan": (), "tepat": (),
     "alasan": "Tanggal dalam bulan tidak punya pola yang masuk akal terhadap polusi; pola musim sudah dibawa bulan dan pola "
               "harian dibawa jam. Pengaruhnya belum diuji ablasi."},
    {"kolom": "hour", "aksi": "Diubah sin-cos (jam_sin, jam_cos)", "awalan": ("jam_",), "tepat": (),
     "alasan": "Jam 23 dan jam 0 bertetangga. Sin-cos membuat jam berputar seperti jam dinding."},
    {"kolom": cfg.KOLOM_TARGET, "aksi": f"Target (Y). Mode B: dibuat lag {_LAG} jam dan rata-rata bergulir {_ROLL} jam",
     "awalan": ("pm25_lag", "pm25_rata"), "tepat": (),
     "alasan": "Mode A tidak boleh memakai PM2.5 sebagai input. Mode B memakai masa lalunya, digeser 1 jam dulu "
               "sebelum dirata-rata supaya jam yang diprediksi tidak ikut mengintip."},
    {"kolom": "DEWP", "aksi": "Dipakai langsung", "awalan": (), "tepat": ("DEWP",),
     "alasan": "Titik embun (kelembapan udara). Sudah numerik; Ridge distandarkan, model pohon tidak butuh."},
    {"kolom": "TEMP", "aksi": "Dipakai langsung", "awalan": (), "tepat": ("TEMP",),
     "alasan": "Suhu. Sudah numerik dan bermakna."},
    {"kolom": "PRES", "aksi": "Dipakai langsung", "awalan": (), "tepat": ("PRES",),
     "alasan": "Tekanan udara. Sudah numerik dan bermakna."},
    {"kolom": cfg.KOLOM_ARAH_ANGIN, "aksi": "One-hot (NE, NW, SE, cv)", "awalan": (), "tepat": (cfg.KOLOM_ARAH_ANGIN,),
     "alasan": "Arah angin adalah kategori tanpa urutan. One-hot mencegah model menganggap NE < NW < SE < cv."},
    {"kolom": "Iws", "aksi": "Dipakai langsung", "awalan": (), "tepat": ("Iws",),
     "alasan": "Kecepatan angin kumulatif. Sebaran miring ke kanan, tetapi tidak ditransformasi: model pohon tidak terpengaruh "
               "dan Ridge distandarkan."},
    {"kolom": "Is", "aksi": "Dipakai langsung", "awalan": (), "tepat": ("Is",),
     "alasan": "Akumulasi jam salju. Hampir selalu 0, tetap dipakai karena nilai tidak nolnya mungkin bermakna "
               "(lihat ablasi 'tanpa cuaca' di halaman Feature Engineering)."},
    {"kolom": "Ir", "aksi": "Dipakai langsung", "awalan": (), "tepat": ("Ir",),
     "alasan": "Akumulasi jam hujan. Hampir selalu 0, tetap dipakai dengan alasan yang sama dengan Is."},
]


def _id(angka, desimal=0):
    """Fungsi: format angka gaya Indonesia (pembungkus utilitas_data.fmt_id). Input: angka, desimal. Output: str."""
    return ud.fmt_id(angka, desimal)


def _turunan(aturan, daftar):
    """Fungsi: fitur dalam 'daftar' yang berasal dari kolom ini. Input: satu aturan, list nama fitur. Output: list."""
    return [f for f in daftar if f in aturan["tepat"] or any(f.startswith(a) for a in aturan["awalan"])]


def jumlah_setelah_enkode(hasil, mode):
    """Fungsi: jumlah kolom setelah one-hot untuk satu mode, dibaca dari hasil['model'][*]['n_fitur_setelah_enkode']. Output: int atau None."""
    nilai = {m["n_fitur_setelah_enkode"] for m in hasil.get("model", {}).values() if m.get("mode") == mode}
    return nilai.pop() if len(nilai) == 1 else (None if not nilai else max(nilai))


def ringkasan_jumlah(hasil):
    """
    Fungsi: semua jumlah untuk kartu ringkasan, dari hasil.json.
    Output: dict {n_kolom_csv, n_fitur_a, n_fitur_b, n_enkode_a, n_enkode_b, n_dibuang, selisih_b_a, selisih_enkode}.
    """
    a, b = hasil["fitur"]["A"], hasil["fitur"]["B"]
    out = {"n_kolom_csv": hasil["data"]["n_kolom_asli"], "n_fitur_a": len(a), "n_fitur_b": len(b),
           "n_enkode_a": jumlah_setelah_enkode(hasil, "A"), "n_enkode_b": jumlah_setelah_enkode(hasil, "B")}
    # kolom yang tidak menghasilkan fitur sama sekali di Mode A maupun B (target pm2.5 tidak dihitung: ia jadi lag di Mode B)
    out["n_dibuang"] = sum(1 for r in ATURAN if not _turunan(r, a + b))
    out["selisih_b_a"] = len(b) - len(a)
    out["selisih_enkode"] = (out["n_enkode_b"] - out["n_enkode_a"]) if out["n_enkode_a"] and out["n_enkode_b"] else None
    return out


def bangun_tabel(hasil):
    """
    Fungsi: tabel 'Dari 13 kolom CSV ke fitur model'.
    Input : dict hasil.json. Output: (DataFrame, daftar_peringatan).
            Kolom: Kolom asal | Diapakan | Alasan | Mode A | Mode B. Mode A/B berisi 'tidak' atau 'N fitur: nama, nama'.
            Baris terakhir = total (jumlah fitur sebelum dan sesudah one-hot, dari hasil.json).
    Peringatan berisi: fitur di hasil.json yang tidak punya kolom asal di ATURAN, atau jumlah kolom CSV tidak cocok.
    """
    a, b = hasil["fitur"]["A"], hasil["fitur"]["B"]
    n_enc_a, n_enc_b = jumlah_setelah_enkode(hasil, "A"), jumlah_setelah_enkode(hasil, "B")
    baris, terpakai = [], set()

    def sel(turunan):
        return "tidak" if not turunan else f"{len(turunan)} fitur: " + ", ".join(turunan)

    for r in ATURAN:
        ta, tb = _turunan(r, a), _turunan(r, b)
        terpakai.update(ta + tb)
        baris.append({"Kolom asal": r["kolom"], "Diapakan": r["aksi"], "Alasan": r["alasan"],
                      "Mode A": sel(ta), "Mode B": sel(tb)})
    ringkas = ringkasan_jumlah(hasil)
    baris.append({"Kolom asal": f"TOTAL ({ringkas['n_kolom_csv']} kolom CSV)", "Diapakan": "-",
                  "Alasan": "Jumlah fitur sebelum one-hot lalu sesudah one-hot (arah angin menjadi beberapa kolom).",
                  "Mode A": f"{ringkas['n_fitur_a']} fitur, jadi {n_enc_a} kolom setelah one-hot",
                  "Mode B": f"{ringkas['n_fitur_b']} fitur, jadi {n_enc_b} kolom setelah one-hot"})
    peringatan = []
    tak_terpetakan = [f for f in a + b if f not in terpakai]
    if tak_terpetakan:
        peringatan.append(f"Fitur belum terpetakan ke kolom asal (tambahkan di peta_fitur.ATURAN): {sorted(set(tak_terpetakan))}")
    if len(ATURAN) != ringkas["n_kolom_csv"]:
        peringatan.append(f"Jumlah baris aturan ({len(ATURAN)}) tidak sama dengan jumlah kolom CSV di hasil.json "
                          f"({ringkas['n_kolom_csv']}). Cek peta_fitur.ATURAN.")
    return pd.DataFrame(baris), peringatan


def tabel_ke_markdown(df):
    """Fungsi: DataFrame -> tabel markdown (tanpa dependensi tabulate). Input: DataFrame. Output: str."""
    kepala = "| " + " | ".join(df.columns) + " |"
    garis = "|" + "|".join(["---"] * len(df.columns)) + "|"
    isi = ["| " + " | ".join(str(v).replace("|", "/").replace("\n", " ") for v in row) + " |" for row in df.to_numpy()]
    return "\n".join([kepala, garis, *isi])


def pertanyaan_dosen(hasil):
    """
    Fungsi: 5 pertanyaan antisipasi dosen tentang jumlah fitur beserta jawabannya. SEMUA angka diambil dari hasil.json
            (dan konfigurasi.py), jadi jawabannya ikut berubah kalau fitur diubah lalu dilatih ulang.
    Input : dict hasil.json. Output: list of (pertanyaan, jawaban).
    """
    r = ringkasan_jumlah(hasil)
    a, b = hasil["fitur"]["A"], hasil["fitur"]["B"]
    n_cuaca = sum(1 for f in a if f in cfg.KOLOM_CUACA_NUMERIK)
    n_siklik = sum(1 for f in a if f.startswith(("jam_", "bulan_")))
    n_arah = sum(1 for f in a if f == cfg.KOLOM_ARAH_ANGIN)
    n_lag = sum(1 for f in b if f.startswith("pm25_lag"))
    n_roll = sum(1 for f in b if f.startswith("pm25_rata"))
    n_kelas = len(cfg.KELAS_ARAH_ANGIN)
    n_latih = hasil["data"]["n_latih"]
    nama_dibuang = [x["kolom"] for x in ATURAN if not _turunan(x, a + b)]

    q1 = (f"Datanya {r['n_kolom_csv']} kolom, kok fitur Mode A cuma {r['n_fitur_a']}? Ke mana sisanya?",
          f"{r['n_kolom_csv']} kolom itu dibagi tiga peran. (1) Target: {cfg.KOLOM_TARGET}, ini yang diprediksi sehingga tidak boleh "
          f"jadi input di Mode A. (2) Tidak dipakai sebagai fitur ({r['n_dibuang']} kolom): {', '.join(nama_dibuang)}. No hanya nomor "
          f"urut, year hanya dipakai membagi data latih dan uji (tahun uji di luar rentang latih), day hanya dipakai membentuk "
          f"waktu. (3) Sisanya jadi fitur: {n_cuaca} kolom cuaca dipakai langsung, month dan hour masing-masing jadi sin dan cos "
          f"({n_siklik} fitur), dan arah angin ({n_arah} fitur). Totalnya {n_cuaca} + {n_siklik} + {n_arah} = {r['n_fitur_a']} fitur.")
    q2 = (f"Kenapa Mode B punya {r['n_fitur_b']} fitur dan dari mana tambahan {r['selisih_b_a']} fitur itu?",
          f"Mode B = Mode A ditambah riwayat PM2.5: {n_lag} fitur lag ({', '.join(f for f in b if f.startswith('pm25_lag'))}) "
          f"dan {n_roll} fitur rata-rata bergulir ({', '.join(f for f in b if f.startswith('pm25_rata'))}). "
          f"{r['n_fitur_a']} + {n_lag} + {n_roll} = {r['n_fitur_b']}. Riwayat ini hanya memakai jam-jam SEBELUM jam yang diprediksi "
          f"(digeser 1 jam dulu), jadi tidak mengintip masa depan. Mode A sengaja dipertahankan sebagai versi tanpa riwayat "
          f"supaya terlihat seberapa besar bantuan riwayat PM2.5.")
    q3 = (f"Kenapa {r['n_fitur_a']} fitur menjadi {r['n_enkode_a']} kolom dan {r['n_fitur_b']} menjadi {r['n_enkode_b']}? "
          f"Bukankah fiturnya sama?",
          f"Bedanya karena one-hot encoding arah angin. Arah angin satu fitur dengan {n_kelas} kategori ({', '.join(cfg.KELAS_ARAH_ANGIN)}), "
          f"model butuh angka, jadi satu kolom itu dipecah menjadi {n_kelas} kolom 0/1. Satu fitur menjadi {n_kelas} kolom, "
          f"bertambah {n_kelas - 1}: {r['n_fitur_a']} + {n_kelas - 1} = {r['n_enkode_a']} (Mode A) dan "
          f"{r['n_fitur_b']} + {n_kelas - 1} = {r['n_enkode_b']} (Mode B). Jumlah 'fitur' dihitung sebelum one-hot, jumlah 'kolom' sesudahnya.")
    q4 = ("Kenapa jam dan bulan dibuat dua kolom (sin dan cos), bukan satu angka saja?",
          "Jam dan bulan itu melingkar: jam 23 bertetangga dengan jam 0, bulan 12 dengan bulan 1. Kalau dipakai sebagai angka biasa, "
          "model mengira 23 dan 0 berjauhan. Satu sudut di lingkaran butuh dua koordinat; kalau cuma sin, dua waktu berbeda bisa "
          "punya nilai sama (misalnya jam 3 dan jam 9), jadi cos diperlukan untuk membedakannya. Itu sebabnya month dan hour "
          "masing-masing menghasilkan dua fitur.")
    kalimat_pca = ""
    try:
        pca_b = hasil["eksperimen"]["pca"]["B"]
        v = pca_b["varian"]["0.95"]
        kalimat_pca = (f" Di eksperimen Ridge Mode B, PCA yang mempertahankan 95% varians memakai {v['n_komponen']} dari "
                       f"{pca_b['n_fitur_setelah_enkode']} komponen dengan RMSE {_id(v['metrik']['rmse'], 2)}, dibanding "
                       f"{_id(pca_b['tanpa_pca']['rmse'], 2)} tanpa PCA (data uji).")
    except (KeyError, TypeError):
        pass
    q5 = (f"Apakah {r['n_enkode_b']} kolom tidak terlalu banyak? Perlu PCA atau pengurangan fitur?",
          f"{'Relatif terhadap data, tidak banyak' if n_latih / r['n_enkode_b'] >= 200 else 'Untuk data sekecil ini jumlahnya cukup banyak (data kecil seperti ini biasanya hanya hasil uji dummy)'}: ada {_id(n_latih)} baris latih untuk {r['n_enkode_b']} kolom, sekitar "
          f"{_id(n_latih / r['n_enkode_b'])} baris per kolom. Risiko overfitting dikendalikan dengan validasi silang berurutan waktu "
          f"dan evaluasi di tahun yang tidak pernah dilihat saat latih; model pohon juga dibatasi kedalaman dan jumlah sampel daun. "
          f"Fitur lag saling berkorelasi tinggi, itu wajar dan tidak merusak model pohon.{kalimat_pca} "
          f"Perbandingan lengkap dengan dan tanpa PCA ada di halaman PCA.")
    return [q1, q2, q3, q4, q5]
