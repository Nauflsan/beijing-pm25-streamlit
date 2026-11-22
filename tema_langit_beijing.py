"""
tema_langit_beijing.py - tampilan "Langit Beijing" (TERANG saja): biru langit yang kalem, kartu putih bersih.

Prinsip warna:
  - Warna dasar halaman = biru langit + putih. Tidak ada gradien pelangi.
  - Warna kategori kualitas udara (hijau sampai marun) HANYA dipakai sebagai aksen kecil yang punya arti:
    titik dan label kategori di kartu KPI, garis tipis di bawah header, dan hasil prediksi. Bukan sebagai latar besar,
    supaya halaman tidak didominasi merah.

Dipakai oleh app.py (pasang_tema) dan halaman (header_halaman, kartu_kpi, lencana_kategori, langkah_alur, kotak_catatan).
"""
import html

import streamlit as st

import konfigurasi as cfg


def warna_teks_kontras(hex_warna):
    """Fungsi: pilih teks hitam/putih yang terbaca di atas warna latar. Input: '#RRGGBB'. Output: '#111111' atau '#FFFFFF'."""
    h = hex_warna.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#111111" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"


def _tipis(hex_warna, alpha):
    """Fungsi: warna hex jadi rgba transparan (untuk latar label yang lembut). Input: '#RRGGBB', alpha 0-1. Output: str."""
    h = hex_warna.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def pasang_tema():
    """Fungsi: suntik CSS tema (font Google Fonts, kartu, header, tab) dan sembunyikan menu pengaturan Streamlit
            (supaya pengguna tidak bisa memindah ke mode gelap). Dipanggil SEKALI di app.py. Output: -"""
    judul, isi = cfg.FONT_JUDUL, cfg.FONT_ISI
    a, k, t, tp, g = cfg.WARNA_AKSEN, cfg.WARNA_KARTU, cfg.WARNA_TEKS, cfg.WARNA_TEKS_PUDAR, cfg.WARNA_GARIS
    g1, g2, g3 = cfg.GRADIEN_HEADER
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={judul.replace(' ', '+')}:wght@500;700&family={isi.replace(' ', '+')}:wght@400;600;700&display=swap');
    html, body, [class*="css"], .stMarkdown, label, p, li, td, th {{
        font-family: '{isi}', -apple-system, 'Segoe UI', Roboto, sans-serif; color: {t};
    }}
    h1, h2, h3, h4 {{ font-family: '{judul}', '{isi}', -apple-system, 'Segoe UI', sans-serif !important; color: {t}; letter-spacing: -0.01em; }}
    .block-container {{ padding-top: 4.8rem; max-width: 1180px; }}
    /* sembunyikan menu pengaturan (tema gelap/terang) dan tombol deploy */
    [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] {{ display: none !important; }}

    /* header halaman: biru langit kalem */
    .lb-header {{ background: linear-gradient(110deg, {g1} 0%, {g2} 55%, {g3} 100%); border-radius: 16px;
                  padding: 22px 28px; margin: 0 0 20px 0; border: 1px solid {g}; }}
    .lb-header h1 {{ margin: 0; padding: 0; font-size: 1.8rem; line-height: 1.25; color: {t}; }}
    .lb-header p {{ margin: 6px 0 0 0; color: #3B5068; font-size: 1.02rem; }}

    /* kartu KPI */
    .lb-kpi {{ background: {k}; border: 1px solid {g}; border-left: 5px solid {a}; border-radius: 14px;
               padding: 14px 16px; min-height: 150px; box-sizing: border-box; box-shadow: 0 1px 3px rgba(31,45,61,.06); }}
    .lb-kpi .lb-label {{ font-size: .78rem; color: {tp}; text-transform: uppercase; letter-spacing: .05em; }}
    .lb-kpi .lb-nilai {{ font-family: '{judul}', sans-serif; font-size: 1.65rem; font-weight: 700; line-height: 1.25; margin-top: 3px; color: {t}; }}
    .lb-kpi .lb-sub {{ font-size: .85rem; color: {tp}; margin-top: 4px; }}
    .lb-chip {{ display: inline-flex; align-items: center; gap: 7px; padding: 3px 11px 3px 9px; border-radius: 999px;
                font-size: .8rem; font-weight: 700; margin-top: 8px; color: {t}; }}
    .lb-chip i {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}

    /* lencana kategori (hasil prediksi) */
    .lb-lencana {{ display: inline-block; padding: 4px 14px; border-radius: 999px; font-weight: 700; font-size: .9rem; }}

    /* langkah alur kerja */
    .lb-langkah {{ background: {k}; border: 1px solid {g}; border-radius: 14px; padding: 14px 16px;
                   min-height: 128px; box-sizing: border-box; box-shadow: 0 1px 3px rgba(31,45,61,.06); }}
    .lb-langkah .lb-judul {{ display: flex; align-items: center; gap: 10px; font-family: '{judul}', sans-serif; font-weight: 700; font-size: 1.02rem; color: {t}; }}
    .lb-langkah .lb-no {{ background: {a}; color: #fff; width: 26px; height: 26px; border-radius: 50%; display: inline-flex;
                          align-items: center; justify-content: center; font-size: .85rem; flex: none; }}
    .lb-langkah .lb-isi {{ font-size: .88rem; color: {tp}; margin-top: 6px; }}

    /* kotak catatan */
    .lb-catatan {{ border-left: 4px solid {a}; background: #EAF2FA; padding: 10px 14px; border-radius: 8px; margin: 8px 0; font-size: .95rem; color: {t}; }}
    .lb-catatan.peringatan {{ border-left-color: #E8A33D; background: #FFF6E5; }}

    button[data-baseweb="tab"] {{ font-weight: 600; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def header_halaman(judul, subjudul="", idx_kategori=None):
    """
    Fungsi: banner judul halaman (biru langit). Kalau idx_kategori (0-5) diberikan, ada garis tipis berwarna kategori
            di bawah banner sebagai aksen; warna banner sendiri tetap biru.
    Input : judul, subjudul, idx_kategori (None atau 0-5). Output: -
    """
    garis = f"border-bottom: 5px solid {cfg.WARNA_KATEGORI[idx_kategori]};" if idx_kategori is not None else ""
    sub = f"<p>{html.escape(subjudul)}</p>" if subjudul else ""
    st.markdown(f'<div class="lb-header" style="{garis}"><h1>{html.escape(judul)}</h1>{sub}</div>', unsafe_allow_html=True)


def kartu_kpi(label, nilai, catatan="", idx_kategori=None):
    """
    Fungsi: satu kartu KPI (putih, garis aksen biru). Kalau idx_kategori (0-5) diberikan, muncul label kecil
            berisi titik warna + nama kategori udara (bukan seluruh kartu diwarnai).
    Input : label, nilai (teks atau angka), catatan (teks kecil), idx_kategori (None atau 0-5). Output: -
    """
    sub = f'<div class="lb-sub">{html.escape(str(catatan))}</div>' if catatan else ""
    chip = ""
    if idx_kategori is not None:
        w = cfg.WARNA_KATEGORI[idx_kategori]
        chip = (f'<div><span class="lb-chip" style="background:{_tipis(w, .16)};"><i style="background:{w};"></i>'
                f'{html.escape(cfg.NAMA_KATEGORI[idx_kategori])}</span></div>')
    st.markdown(f'<div class="lb-kpi"><div class="lb-label">{html.escape(str(label))}</div>'
                f'<div class="lb-nilai">{html.escape(str(nilai))}</div>{sub}{chip}</div>', unsafe_allow_html=True)


def lencana_kategori(idx):
    """Fungsi: HTML lencana berwarna penuh untuk satu kategori (dipakai hasil prediksi). Input: idx 0-5. Output: str HTML."""
    w = cfg.WARNA_KATEGORI[idx]
    return (f'<span class="lb-lencana" style="background:{w};color:{warna_teks_kontras(w)};">'
            f'{html.escape(cfg.NAMA_KATEGORI[idx])}</span>')


def langkah_alur(nomor, judul, isi):
    """Fungsi: kartu satu langkah alur kerja dengan lingkaran bernomor. Input: nomor, judul, isi. Output: -"""
    st.markdown(f'<div class="lb-langkah"><div class="lb-judul"><span class="lb-no">{html.escape(str(nomor))}</span>'
                f'{html.escape(judul)}</div><div class="lb-isi">{html.escape(isi)}</div></div>', unsafe_allow_html=True)


def kotak_catatan(teks, jenis="info"):
    """Fungsi: kotak catatan ringan. Input: teks, jenis ('info' atau 'peringatan'). Output: -"""
    kelas = "lb-catatan peringatan" if jenis == "peringatan" else "lb-catatan"
    st.markdown(f'<div class="{kelas}">{html.escape(teks)}</div>', unsafe_allow_html=True)
