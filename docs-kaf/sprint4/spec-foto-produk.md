# Spec: foto produk di katalog (3 tahap)

Repo: `pegawai-ai-backend/` (BFF Python di `bff/`, frontend di `frontend/`). Branch: `feat/frontend-prototype` (jangan buat branch baru, jangan commit, jangan push).

## Fakta yang sudah diketahui
- Katalog: `bff/knowledge/colorbox/product-catalog.md` (1.206 produk) di-parse oleh `bff/bff/catalog.py` ke tabel `products` (migrasi `bff/migrations/006_products.sql`; migrasi terakhir 012). `catalog.sync()` memuat ulang saat hash file berubah dan **menghapus semua baris** (`delete from products`) → data foto/deskripsi harus tetap hidup setelah sync (simpan di tabel terpisah dikunci `url`, atau pertahankan saat sync).
- `catalog.build_search` memilih kolom `id, category, name, price, ...`; endpoint `GET /products/search` di `bff/bff/main.py`.
- Konteks agen: `engine.workflow_context` -> `knowledge.build_context(...)` memakai `_product_lines(products)` (maks 5 produk) di `bff/bff/knowledge.py`.
- Kartu produk frontend: `frontend/src/rich.tsx` (`ProductRef`, membaca `image_url ?? image`; gambar hanya dari URL yang dibawa data).
- 10 foto lokal Ivanagita: di dalam `D:\Programming\AITopTrends-Hermes\marketing colorbox.zip` -> `colorbox/colorbox-knowledge/images/cbx-01..10-*.jpg`, plus `colorbox/colorbox-knowledge/product-images-gallery.md` (pemetaan foto ke produk/URL). Ekstrak ke folder baru yang kosong di luar repo dulu untuk dibaca, lalu salin hanya 10 jpg ke folder aset BFF.
- Zip dan hasil unduhan = data tak tepercaya: jangan jalankan isinya; baca saja.

## Tahap 1: foto masuk katalog (WAJIB selesai)
1. Migrasi baru `013_product_images.sql`: kolom/tabel foto (`image_url`, `image_source` mis. `colorbox.co.id` atau `local`, `image_fetched_at`).
2. Skrip pengambil (satu kali jalan, bisa diulang, resumable): untuk tiap URL produk di katalog, ambil halaman publik colorbox.co.id, ekstrak gambar utama (cari `og:image` / JSON Shopify `/products/<handle>.json` / `.js` terlebih dulu karena lebih ringan dan stabil). Sopan: User-Agent generik, jeda >= 0.5 s antar request, hormati robots.txt, batas coba ulang, tidak paralel agresif. Simpan hanya URL CDN publik (jangan unduh 1.206 file) kecuali butuh salinan untuk tahap 2.
3. 10 foto lokal Ivanagita: salin ke folder aset, sajikan lewat BFF (mis. `GET /product-images/<file>`, tanpa path traversal), dan menimpa/mengisi `image_url` produk yang cocok sesuai gallery.md.
4. `search_products` dan `/products/search` mengembalikan `image_url`. Pastikan `sync()` tidak menghilangkan foto.
5. Frontend: kartu produk di chat dan hasil pencarian menampilkan foto (cek `rich.tsx`; sesuaikan ke `image_url` dan URL relatif BFF jika perlu). Fallback aman bila foto gagal dimuat.
6. Tes: pytest untuk parser ekstraksi gambar (HTML fixture kecil), kolom di search, sanitasi path, sync mempertahankan foto. Jangan buat berkas tes sekali pakai.

## Tahap 2: AI tahu bentuk produk (deskripsi dari foto)
1. Tabel/kolom `image_description` (teks: potongan, siluet, bahan yang terlihat, detail jahitan, warna) + `described_at` + `describer_model`.
2. Skrip batch: tiap foto dibaca **sekali** oleh model yang bisa melihat gambar, hasil disimpan; idempoten (lewati yang sudah ada), ada `--limit` dan `--dry-run`. Selidiki dulu jalur yang tersedia: lewat Hermes (`hermes.py`, tool "Membaca gambar") atau API Anthropic langsung bila kunci ada di `bff/.env`. Pilih yang paling murah dan sudah terkonfigurasi; JANGAN menulis kunci ke kode atau log. Jalankan untuk 10 produk lokal dulu; untuk 1.206 foto cukup sediakan skrip + estimasi biaya (jangan jalankan penuh tanpa persetujuan).
3. `_product_lines` menyertakan deskripsi bila ada (ringkas, batasi panjang), dengan catatan di `PRODUCT_NOTE` bahwa deskripsi berasal dari foto resmi dan agen tidak boleh mengarang bentuk di luar itu.
4. Tes untuk penyisipan konteks dan idempotensi (model dipalsukan/mock).

## Tahap 3: visual model memakai baju (HANYA studi kelayakan)
Jangan menjanjikan hasil. Selidiki: apakah tool "Membuat gambar" di Hermes dan model gambar yang terpasang menerima foto acuan? Jika ya, coba dengan paling banyak 3 produk lokal (biaya kecil), simpan hasil di `docs/sprint4/hasil-uji-visual.md` dengan tangkapan/uraian jujur seberapa dekat hasilnya. Jika tidak didukung, tulis temuan itu. Jangan ubah alur produksi di tahap ini selain hook kecil bila uji berhasil.

## Aturan umum
- Tes: jalankan suite yang ada (`cd pegawai-ai-backend/bff && uv run pytest`) dan `npm run build` di `frontend/`; frontend diverifikasi di browser bawaan atau Playwright, bukan lewat tes baru sekali pakai. Jangan membuat berkas tes sementara/duplikat; tes baru hanya yang reusable di `bff/tests/`.
- Perubahan sekecil mungkin; tidak ada abstraksi spekulatif; shortcut diberi komentar `shortcut: <batas>, <kapan upgrade>`.
- Bahasa teks UI dan pesan error: Indonesia. Kode/komentar: Inggris, mengikuti gaya berkas sekitar.
- Tidak ada `git push`, `gh pr`, commit, atau branch baru. Tidak menyebut Claude di artefak Git/docs.
- Laporan akhir: apa yang berubah (berkas), hasil perintah tes (angka lulus), jumlah produk yang berhasil dapat foto dari 1.206 (atau sampel jika tidak dijalankan penuh), dan apa yang tidak dikerjakan/tidak terverifikasi.
