"""
uji_halaman.py - uji asap tiap halaman tanpa membuka browser (streamlit.testing.v1.AppTest).
Jalankan:  python -m alat.uji_halaman            (memakai artifacts/ asli)
           python -m alat.uji_halaman --dummy    (memakai artifacts_dummy/, untuk menguji tampilan sebelum training selesai)
Lulus = tidak ada exception di halaman manapun.
"""
import os
import sys
from pathlib import Path

if "--dummy" in sys.argv:
    os.environ["PM25_DUMMY"] = "1"   # harus di-set SEBELUM konfigurasi diimpor

from streamlit.testing.v1 import AppTest  # noqa: E402

import konfigurasi as cfg  # noqa: E402

RAKYAT = Path(__file__).resolve().parent.parent   # folder proyek (alat/ ada satu tingkat di bawahnya)
HALAMAN = sorted(p for p in (RAKYAT / "halaman").rglob("*.py"))


def uji_satu(path):
    """Fungsi: jalankan satu halaman dan kembalikan daftar exception. Input: path file. Output: list str."""
    at = AppTest.from_file(str(path), default_timeout=180).run()
    return [str(e.value) for e in at.exception]


if __name__ == "__main__":
    gagal = 0
    print(f"Artefak yang dipakai: {cfg.FOLDER_ARTEFAK_AKTIF}")
    for p in [RAKYAT / "app.py", *HALAMAN]:
        err = uji_satu(p)
        print(("OK     " if not err else "GAGAL  ") + str(p.relative_to(RAKYAT)))
        for e in err:
            print("        ", e[:300])
        gagal += bool(err)
    print("\nSEMUA HALAMAN LULUS" if not gagal else f"\n{gagal} HALAMAN GAGAL")
    sys.exit(1 if gagal else 0)
