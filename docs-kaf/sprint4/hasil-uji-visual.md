# Studi kelayakan: visual model memakai baju (Tahap 3)

Tanggal: 2026-11-16. Status: **belum bisa diuji; tidak ada gambar yang dibuat.** Tidak ada yang dijanjikan.

## Temuan

1. **Tool "Membuat gambar" (`image_generate`) di Hermes mendukung foto acuan.** Di `tools/image_generation_tool.py` ada mode edit/image-to-image
   (`source_images`, `reference_image_urls`) untuk model yang punya `edit_endpoint` (mis. FLUX.2 Pro Edit, Nano Banana Pro/2,
   GPT Image 1.5/2, Seedream v5, Qwen Image, Kling Image v3). Tiap model punya batas jumlah gambar acuan (`max_reference_images`).
   Model tanpa `edit_endpoint` menolak foto acuan dengan pesan jelas.
2. **Di instalasi ini tool itu tidak aktif.** Dicek langsung dengan `check_image_generation_requirements()` di venv Hermes:
   `check_fal_api_key()` = False dan tidak ada backend gambar plugin yang dipilih, sehingga hasilnya False. `FAL_KEY` belum diisi
   (di `.env` Hermes hanya berupa baris komentar), dan profil bot tidak punya kunci gambar.
3. Ada `GOOGLE_API_KEY` di `.env` Hermes, tetapi tidak dipakai di sini: memilihnya sebagai backend gambar berarti mengaktifkan
   layanan berbayar baru, itu keputusan pemilik akun, bukan bagian tugas ini.

## Yang diperlukan agar bisa dicoba

- Isi `FAL_KEY` (akun fal.ai) atau pilih backend gambar plugin yang sudah punya kunci, lalu pilih satu model dengan `edit_endpoint`.
- Uji paling banyak 3 produk lokal (foto di `bff/assets/product-images/`), satu foto produk sebagai acuan per percobaan, lalu nilai
  secara manual seberapa dekat potongan, warna, dan detail jahitan dengan foto resmi. Risiko yang perlu dinilai: baju berubah bentuk,
  logo/sablon rusak, dan hak pakai foto produk sebagai bahan generasi.

## Perubahan kode

Tidak ada. Alur produksi tidak disentuh.
