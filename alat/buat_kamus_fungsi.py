"""
buat_kamus_fungsi.py - membuat dokumen/KAMUS_FUNGSI.md OTOMATIS dari kode: semua file, semua fungsi/kelas, nomor barisnya, dan
penjelasan singkatnya (diambil dari docstring "Fungsi: ... Input: ... Output: ...").

Jalankan:  python -m alat.buat_kamus_fungsi
Karena dibuat dari kode, dokumen ini tidak bisa salah atau basi: tinggal dijalankan ulang setelah kode berubah
(alat.perbarui_panduan juga memanggilnya). Syaratnya hanya satu: tiap fungsi punya docstring (aturan proyek).
"""
import ast
import re

import konfigurasi as cfg

FOLDER_URUT = [("", "Root"), ("preprocessing", "preprocessing/ : persiapan data"), ("model", "model/ : pelatihan dan prediksi"),
               ("evaluasi", "evaluasi/ : penilaian dan pembuktian"), ("tampilan", "tampilan/ : tema, grafik, utilitas web"),
               ("alat", "alat/ : tes dan pembaruan dokumen"), ("halaman", "halaman/ : halaman web"), ("halaman/tambahan", "halaman/tambahan/ : halaman tambahan")]
FILE_ABAI = {"__init__.py"}
BAGIAN = ("Fungsi", "Input", "Output")


def _pisah_docstring(doc):
    """
    Fungsi: pecah docstring bergaya proyek menjadi bagian Fungsi / Input / Output. Input: teks docstring (atau None).
    Output: dict {'Fungsi','Input','Output'} (string, bisa kosong). Docstring tanpa pola ini dimasukkan semua ke 'Fungsi'.
    """
    if not doc:
        return {b: "" for b in BAGIAN}
    teks = " ".join(doc.split())
    pola = re.compile(r"(Fungsi|Input|Output)\s*:\s*")
    bagian = {b: "" for b in BAGIAN}
    pos = [(m.start(), m.end(), m.group(1)) for m in pola.finditer(teks)]
    if not pos:
        bagian["Fungsi"] = teks
        return bagian
    for i, (s, e, nama) in enumerate(pos):
        akhir = pos[i + 1][0] if i + 1 < len(pos) else len(teks)
        bagian[nama] = teks[e:akhir].strip()
    return bagian


def _ringkas(teks, maks=230):
    """Fungsi: potong teks panjang untuk sel tabel dan ganti karakter | agar tabel markdown tidak rusak. Input: teks, maks panjang. Output: str."""
    teks = teks.replace("|", "/")
    return teks if len(teks) <= maks else teks[: maks - 3].rstrip() + "..."


def _baris_fungsi(node, awalan=""):
    """Fungsi: ubah satu node fungsi/kelas ast menjadi baris kamus (nama, baris, fungsi, input, output). Input: node ast, awalan nama (untuk metode kelas). Output: dict."""
    d = _pisah_docstring(ast.get_docstring(node))
    return {"nama": awalan + node.name, "baris": node.lineno, "fungsi": _ringkas(d["Fungsi"]) or "(belum ada docstring)",
            "input": _ringkas(d["Input"], 160), "output": _ringkas(d["Output"], 160)}


def kumpulkan():
    """
    Fungsi: telusuri semua file .py proyek lewat ast. Output: list of dict {folder, berkas, ringkasan_file, daftar:[...]},
            daftar berisi fungsi dan kelas (beserta metodenya) dengan nomor baris dan penjelasan.
    """
    hasil = []
    for folder, judul in FOLDER_URUT:
        base = cfg.FOLDER_PROYEK / folder if folder else cfg.FOLDER_PROYEK
        for p in sorted(base.glob("*.py")):
            if p.name in FILE_ABAI:
                continue
            tree = ast.parse(p.read_text(encoding="utf-8"))
            doc = ast.get_docstring(tree) or ""
            ringkasan = " ".join(doc.split("\n\n")[0].split())
            daftar = []
            for n in tree.body:
                if isinstance(n, ast.FunctionDef):
                    daftar.append(_baris_fungsi(n))
                elif isinstance(n, ast.ClassDef):
                    daftar.append(_baris_fungsi(n))
                    daftar += [_baris_fungsi(m, f"{n.name}.") for m in n.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("__")]
            hasil.append({"judul_folder": judul, "berkas": (f"{folder}/" if folder else "") + p.name, "ringkasan_file": ringkasan, "daftar": daftar})
    return hasil


def susun_markdown(data):
    """Fungsi: ubah hasil kumpulkan() menjadi teks markdown. Input: list dari kumpulkan(). Output: str."""
    baris = ["# KAMUS FUNGSI", "",
             "Dibuat OTOMATIS dari kode dan docstring oleh `python -m alat.buat_kamus_fungsi`. Jangan diedit manual; ubah docstring di kodenya.",
             "Kolom: nama fungsi, nomor baris di file, fungsinya apa, input, output.", ""]
    folder_sekarang = None
    for f in data:
        if f["judul_folder"] != folder_sekarang:
            folder_sekarang = f["judul_folder"]
            baris += ["", f"## {folder_sekarang}", ""]
        baris += [f"### `{f['berkas']}`", "", f["ringkasan_file"] or "(tanpa ringkasan)", ""]
        if f["daftar"]:
            baris += ["| Fungsi | Baris | Fungsinya apa | Input | Output |", "|---|---|---|---|---|"]
            for d in f["daftar"]:
                baris.append(f"| `{d['nama']}` | {d['baris']} | {d['fungsi']} | {d['input'] or '-'} | {d['output'] or '-'} |")
            baris.append("")
    return "\n".join(baris) + "\n"


def tulis():
    """Fungsi: buat dan simpan dokumen/KAMUS_FUNGSI.md. Output: (path, jumlah file, jumlah fungsi tanpa docstring)."""
    data = kumpulkan()
    path = cfg.FOLDER_PROYEK / "dokumen" / "KAMUS_FUNGSI.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(susun_markdown(data), encoding="utf-8")
    tanpa_doc = sum(1 for f in data for d in f["daftar"] if d["fungsi"].startswith("(belum"))
    return path, len(data), tanpa_doc


if __name__ == "__main__":
    p, n, kosong = tulis()
    print(f"{p.name} dibuat: {n} file kode dibaca; {kosong} fungsi/kelas belum punya docstring.")
