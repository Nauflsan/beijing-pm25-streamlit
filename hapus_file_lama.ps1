# Jalankan di folder web_pm25_beijing SETELAH mengekstrak zip (file baru sudah ada di subfolder).
# Menghapus file lama di folder utama yang sekarang sudah pindah ke preprocessing/, model/, evaluasi/, tampilan/, alat/, dokumen/.
$lama = @("utilitas_data.py","fitur_waktu.py","peta_fitur.py","eksperimen_ringan.py","latih_semua_model.py","pso_random_forest.py",
          "evaluasi_regresi.py","kategori_udara.py","bukti_kode.py","bukti_eksperimen.py","tema_langit_beijing.py","grafik.py",
          "utilitas_app.py","uji_cepat.py","uji_halaman.py","perbarui_panduan.py","PANDUAN_HALAMAN.md","PANDUAN_KODE.md","STATUS_PROYEK.md")
foreach ($f in $lama) { if (Test-Path $f) { Remove-Item $f; "dihapus: $f" } }
Get-ChildItem -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
"Selesai. Cek: git status"
