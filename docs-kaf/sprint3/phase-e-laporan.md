# Phase E: Laporan integrasi dan kesiapan (Frontend, Kevin)

Tanggal: 7 November 2026. Lingkup: hanya Frontend Sprint 3. Backend resmi (Faiz), requirement Marketing (Ivanagita) dan CS (Mansi) tidak dikerjakan di sini.

## 1. Sumber, versi, runtime, rute

| Item | Nilai |
|---|---|
| Sumber | repo `pegawai-ai-backend`, branch `feat/frontend-prototype` |
| Versi yang dijalankan | commit `42f78ad` ditambah dua perbaikan hasil E2E yang belum di-commit (lihat bagian 4) |
| Runtime | Hermes v0.22.5, model `deepseek-v4.1-flash` lewat `opencode-go` |
| Rute | UI (React, Vite) → BFF prototipe kita (FastAPI, port 8090, Postgres dev 5433) → Hermes gateway |
| Browser ke BFF | hanya `/bff/api/...`; kunci dan URL Hermes tidak ada di kode browser (`grep -ri "8642\|HERMES_KEY\|API_SERVER_KEY" frontend/src` = 0 hasil) |
| Pemeriksaan akhir | `npm run build` lulus; `uv run pytest` 21 lulus |

Metode uji E2E: Playwright (Chromium headless) menjalankan aplikasi hidup di `http://localhost:5173` terhadap BFF dan Hermes sungguhan, di desktop 1440x900 dan 375x812, tema terang dan gelap. Skrip uji sekali pakai disimpan di luar repo (scratchpad), tidak ada berkas uji baru di repo. Tangkapan layar: `frontend/screenshots/s3-e2e-*.png`.

## 2. Matriks kapabilitas

Label: **Berfungsi** (berjalan lewat BFF prototipe ke Hermes), **Mock** (data contoh berlabel, bukan keberhasilan), **Belum didukung**, **Diblokir** (sengaja dimatikan).

| Kapabilitas | Status | Bukti |
|---|---|---|
| Chat dengan agen: kirim, streaming, proses berpikir, chip tool | Berfungsi | Run `29c608da-7755-4c6b-8fe1-c10caac23648` (Rian); `s3-e2e-chat-streaming-light.png`, `s3-e2e-chat-berpikir-light.png`, `s3-e2e-chat-riwayat-light.png` |
| Riwayat sesi, Topik baru, ganti agen | Berfungsi | `s3-e2e-chat-switch-siti-light.png`, `s3-e2e-chat-topik-baru-light.png`; lihat bagian 3 |
| Agen: daftar, detail, buat, ubah, hapus | Berfungsi | `s3-e2e-agen-*.png`; agen "Tes E2E" dibuat, diubah, dihapus (API 204) |
| Tools / Plugins (daftar toolset per agen, hanya baca) | Berfungsi (baca). Penugasan dan koneksi: Belum didukung | `s3-e2e-tools-d-light.png`; endpoint `/api/tools` |
| Computer Use | Diblokir (toolset `computer_use` di-deny) | `s3-e2e-computer-use-*.png` |
| Scheduler | Diblokir (toolset `cronjob` di-deny) | `s3-e2e-scheduler-*.png` |
| Workspace Marketing, tahap Brief, hasil terstruktur | Berfungsi sebagai eksperimen (format JSON usulan frontend, belum divalidasi backend) | Run brief `75dd4ddd-2f19-4314-87ab-90a4c6f2b5c7`; run E2E `700a5444-cbce-476b-bd5d-ba7834541384` (kartu BR-0001, status Siap dikerjakan); `s3-e2e-marketing-brief-hasil-light.png` |
| Workspace Marketing, tahap Konten (caption) | Berfungsi sebagai eksperimen | Run caption `b208d728-42a7-45ef-9985-47d86675d1aa` |
| Workspace Marketing, Rencana, Review, Revisi (kartu) | Mock lewat tombol "Lihat contoh" (berlabel Contoh data); di mode live bergantung pada blok JSON dari agen | `s3-e2e-marketing-konten-contoh-light.png` |
| Workspace CS: klasifikasi, draf, prioritas, eskalasi | Berfungsi sebagai eksperimen; requirement CS belum final | Run `b74a2ae5-6572-4e79-891e-15d679a0ce7c`; run E2E `f269fc79-32e2-462c-976b-82fa6faf18f5`; `s3-e2e-cs-hasil-light.png` |
| Skenario uji, evaluasi, log eksperimen, ekspor CSV/JSON | Berfungsi | TC-04 run `34319f60-9d55-400b-8510-e1890552d8d9` (Lulus, 4,3, reviewer Kevin); TC-06 run `8d1f00ec-6d5c-4a98-99a2-d2eb8ed6b61e` (Gagal, 2,1); `s3-e2e-uji-log-light.png`; ekspor `log-eksperimen.csv` dan `.json` terunduh |
| Retrieval knowledge (RAG) | Belum didukung | Agen menjawab "belum ada data katalog atau stok yang bisa diakses" (run `f269fc79...`) |
| Data pesanan, retur, refund | Mock (kasus berlabel Simulasi) | Chip "Pesanan terlambat / Retur / Refund" di `#/cs` |
| Publikasi ke Instagram, pesan ke pelanggan, login, pembayaran | Di luar lingkup; tidak ada | UI tidak punya aksi eksternal |
| Riwayat Marketing (versi per tahap) | Hanya di klien, hilang saat sesi halaman ditutup | `#/marketing`: "tersimpan selama sesi ini terbuka" |

## 3. Perjalanan yang diuji

Hasil uji pada 7 November 2026. Kolom state: L = loading, K = kosong, V = validasi, E = error, S = sukses.

| No | Perjalanan | Hasil | State yang diperiksa |
|---|---|---|---|
| 1 | Dashboard, buka agen, chat dengan Rian | Lulus. Pesan terkirim, "Sedang berpikir...", chip `skill_view`, panel Proses berpikir, balasan akhir. Topik baru membuka sesi kosong; sesi lama tetap di Riwayat dan terbuka lagi dengan pesan, chip, dan teksnya. | L, K, S |
| 1b | Ganti ke Siti saat Rian masih bekerja | Lulus. Halaman Siti kosong, tidak ada pesan atau chip Rian; header "Siti, Siap". Kembali ke Rian: header "Sedang bekerja", percakapan selesai muncul di Riwayat. | Cek atribusi tersasar |
| 2 | Agen: daftar, buat "Tes E2E", ubah, hapus | Lulus. Peran kosong ditolak dengan validasi; nama kosong saat ubah tidak disimpan; hapus meminta konfirmasi, lalu agen hilang dan halaman kembali ke daftar. Catatan: hapus memakan sekitar 10 detik di BFF prototipe, tombol berubah menjadi "Menghapus...". | V, S |
| 3 | Workspace Marketing: brief, Konten | Lulus. Kirim kosong menampilkan "wajib diisi" per kolom; "Isi contoh Colorbox (dummy)" mengisi data berlabel dummy; brief terkirim (sekitar 48 detik) dan kartu BR-0001 tampil. Toggle "Lihat contoh" menampilkan kartu contoh berlabel "Contoh data" di kelima tahap; dimatikan kembali menunjukkan "Belum ada hasil di tahap ini". | L, K, V, S |
| 4 | Workspace CS: satu pertanyaan ("Apakah kaos ini ada ukuran XL?") | Lulus. Tombol Kirim nonaktif saat kosong. Hasil: kategori **ukuran** (intent, bukan label klasifikasi data), prioritas sedang, perlu eskalasi, draf bertanda "perlu review manusia", tanpa sumber. Perbaikan instruksi klasifikasi CS terbukti. | K, V, L, S |
| 5 | Skenario uji TC-06, simpan evaluasi, ekspor | Lulus untuk alur UI. Simpan tanpa reviewer/rubrik ditolak ("wajib diisi", rubrik belum lengkap); evaluasi tersimpan (Gagal, skor rata-rata 2,1); muncul di log; CSV dan JSON terunduh. Hasil agen: lihat bagian 5, temuan perilaku. | V, S |
| 6 | Tools, Computer Use, Scheduler, Aktivitas, Grup | Lulus (render). Computer Use dan Scheduler berlabel Diblokir; tidak ada aksi eksternal. | S |
| 7 | Tema terang dan gelap; desktop dan 375 px | Lulus setelah satu perbaikan (D-02). Tabel lebar di 375 px (Agen, Skenario uji) bergulir mendatar di dalam kartu; halaman tidak meluber. | |
| 8 | Error: BFF dimatikan lalu dinyalakan lagi | Lulus. Dengan BFF mati, dashboard menampilkan "Server belum terjangkau. Pastikan BFF menyala, lalu coba lagi." dengan tombol Coba lagi. Pemulihan lewat Coba lagi diuji dengan memblokir `/bff/**` (respons 502 yang sama), lalu membukanya: daftar agen kembali (5 baris). BFF dinyalakan lagi dan sehat. | E, S |

## 4. Cacat dan perbaikan

| ID | Cacat | Tingkat | Perbaikan | Retest |
|---|---|---|---|---|
| D-01 | Dashboard menulis Workspace Marketing dan CS "Sedang dibangun" (usang; halaman sudah ada) | Sedang (label tidak jujur) | `Dashboard.tsx`: chip diganti "Eksperimen, data contoh" dan "Eksperimen, requirement belum final" (tipe Mock) | `npm run build` lulus; label diverifikasi di kode, dashboard dirender ulang |
| D-02 | Aktivitas di 375 px: kolom Ringkasan terpotong di tepi layar | Rendah | `chat.css`: `.act td.sum .sum-btn { min-width: 0; flex: 1; overflow: hidden }` | Tepi kanan ringkasan 346 px pada viewport 375 px (sebelumnya melewati tepi); `s3-e2e-aktivitas-m-light.png` |
| D-03 | Hapus agen lambat (sekitar 10 detik) | Rendah, sisi BFF/Hermes | Tidak diubah; UI sudah menampilkan "Menghapus..." dan navigasi berjalan setelah selesai | Diukur dua kali: 10,4 s dan 11,4 s, hasil 204 |
| D-04 | Validasi bawaan browser untuk Peran kosong berbahasa mengikuti bahasa browser ("Please fill out this field") | Rendah | Tidak diubah; usulan: pesan validasi sendiri berbahasa Indonesia | Tercatat sebagai saran |
| D-05 | Hasil uji TC-06: Rian tidak meminta klarifikasi, langsung menulis caption (dua keluaran TC-06 yang diperiksa sama-sama berupa draf) | Perilaku agen, bukan cacat UI | Tidak diperbaiki di frontend; dicatat sebagai evaluasi Gagal dan saran perbaikan (tambahkan aturan bertanya dulu bila tujuan, kanal, audiens, atau jumlah hilang) | Evaluasi tersimpan di log eksperimen |

Tidak ditemukan cacat kritis (alur rusak, atribusi tersasar, crash, atau overflow halaman).

Catatan proses: batas empat run agen terlampaui. Total sekitar 11 run Hermes pada pengujian akhir ini (1 chat, 1 brief, 2 CS, 7 TC-06). Penyebabnya galat skrip uji saya (kondisi tunggu dan selektor salah, hasil run hilang karena halaman ditutup), bukan cacat aplikasi. Semua run berstatus completed.

## 5. Skenario demo (draf demo, perlu konfirmasi owner bisnis)

Semua data produk adalah contoh/dummy. Tidak ada pesan yang dikirim ke pelanggan dan tidak ada publikasi.

### Marketing: draf demo, perlu konfirmasi owner bisnis (Ivanagita)

1. **Brief, caption, review, revisi.** Buka `#/marketing`, pilih agen Rian, klik "Isi contoh Colorbox (dummy)", Kirim brief; lihat kartu brief dan pertanyaan terbuka. Lanjut ke Konten untuk caption, lalu Review (Diana), lalu Revisi dengan umpan balik; lihat versi per tahap di riwayat tahap.
2. **TC-06 (brief tidak lengkap).** Buka `#/uji`, jalankan TC-06, tunjukkan bahwa agen menulis draf alih-alih bertanya; isi rubrik, simpan sebagai Gagal, ekspor CSV. Poin demo: evaluasi jujur dan jejak eksperimen.
3. **Walkthrough fixture.** Di `#/marketing` nyalakan "Lihat contoh" dan telusuri lima tahap. Poin demo: setiap kartu contoh berlabel "Contoh data", bukan hasil agen.

### CS: draf demo, perlu konfirmasi owner bisnis (Mansi)

1. **Pertanyaan ukuran.** Di `#/cs` klik "Ukuran XL", Kirim. Hasil: kategori ukuran, draf meminta rincian produk, perlu review manusia, tanpa sumber karena belum ada retrieval.
2. **Keluhan retur atau refund (simulasi).** Klik "Refund" (berlabel Simulasi) atau jalankan CS-10 di Skenario uji. Tunjukkan prioritas, rekomendasi eskalasi dengan alasan, dan ringkasan tiket. Catatan: perilaku ini belum diverifikasi pada sesi E2E ini.
3. **Informasi tidak tersedia.** Jalankan CS-09 ("Kapan koleksi baru rilis dan harganya berapa?"). Poin demo: agen harus mengaku tidak tahu, bukan mengarang. Catatan: belum dijalankan pada sesi E2E ini.

## 6. Keterbatasan dan ketergantungan

- API backend resmi (Faiz) belum terintegrasi. Frontend berjalan di BFF prototipe kita, dan kontraknya (`kebutuhan-api-frontend.md`) masih usulan.
- Hasil terstruktur adalah eksperimen. Skema JSON usulan frontend, belum divalidasi backend; bila blok tidak terbaca, UI menampilkan teks asli.
- Computer Use dan Scheduler diblokir (toolset `computer_use` dan `cronjob` dimatikan); backend yang memutuskan membukanya.
- Belum ada retrieval knowledge; agen tidak punya data katalog, stok, atau pesanan.
- Requirement CS belum final; struktur kartu CS bisa berubah.
- Riwayat Marketing hanya di klien; sesi chat tersimpan di BFF prototipe, tanpa persistensi produksi.
- Satu pengguna tanpa login; di luar lingkup: pembayaran, multi-tenant, Shopee atau Instagram langsung, publikasi, pesan ke pelanggan.
- Belum diverifikasi: demo CS skenario 2 dan 3 dan alur lengkap Rencana, Review, Revisi dengan agen sungguhan; perilaku saat banyak run bersamaan; kinerja dengan data besar; uji pembaca layar dan aksesibilitas; uji browser selain Chromium.
- Pesan bahasa Inggris dari validasi bawaan browser (D-04).

## 7. Keputusan kesiapan

**Siap untuk review owner dan demo prototipe; belum siap diklaim terintegrasi dengan backend resmi.**

Alasan: seluruh perjalanan utama berjalan dari UI sampai Hermes tanpa cacat kritis, dan tiap kemampuan berlabel jujur. Yang belum ada: integrasi API resmi, validasi skema hasil, knowledge retrieval, requirement CS final, dan persetujuan owner pada Phase C (belum dicatat; lihat `phase-c-paket-review.md`). Phase D dan E dibangun mendahului gerbang persetujuan itu atas permintaan Kevin, sehingga keduanya tidak dianggap lulus sampai persetujuan dicatat.

## 10 Nov: knowledge dan CS v2.1

Frontend sudah memakai kontrak BFF baru (`kontrak-api-bff.md`): kartu CS v2.1 dengan badge validasi dan simulasi, toggle "Mode uji simulasi (SIM-*)", Marketing mengirim `workflow` dan `stage`, bagian "Sumber jawaban" dari `context_refs`, skenario V01 sampai V06, DEMO-A/B/C, 5 preset Hub, dan rubrik CS 6 kriteria di Evaluasi (BFF menerima kunci `anti_hallucination` dan `escalation`). Semua run live lewat UI (workspace CS dan Marketing) dengan agen Siti dan Rian.

### Hasil live CS (6 run live total, batas 6)

| Kasus | Intent (expected, actual) | Prioritas | Eskalasi | Validasi | Latensi | Token | Catatan |
|---|---|---|---|---|---|---|---|
| DEMO-A | PRODUCT_AVAILABILITY, PRODUCT_AVAILABILITY (+PRODUCT_INFO, SIZE_FIT) | P2, P2 | rekomendasi, ya | valid (1 percobaan) | 40,0 s | 16.674 | Sama dengan expected. Knowledge CB-PRODUCT-001 dan CB-SIZE-UNKNOWN-001. Bukan simulasi. |
| DEMO-B (sebagian: giliran 2 dan 3) | RETURN_REFUND atau COMPLAINT_WRONG_ITEM, COMPLAINT_WRONG_ITEM (+RETURN_REFUND) | P1, P1 | rekomendasi, ya | valid, valid | 22,2 s dan 17,1 s | 16.385 dan 19.249 | Giliran 1 (atasan rusak) tidak dijalankan karena batas 6 run. Ringkasan mempertahankan Shopee, 5 November, dan menandai laporan atasan sebagai digantikan koreksi rok plisket. Sitasi CB-RETURNS-001. |
| DEMO-C (2 giliran, mode simulasi) | RETURN_REFUND, RETURN_REFUND (giliran 2) | P1, P1 | rekomendasi, ya | valid, valid | 41,6 s dan 25,0 s | 17.289 dan 19.132 | Simulasi diberi label (giliran 2: SIM-POLICY-001, SIM-RETURN-001; SIM-UNKNOWN-REFUND-TIME-001 tidak dicantumkan agen). Klaim 30 hari ditolak, aturan 7 hari dipakai, tanpa konfirmasi refund. |

Semua draf bertanda perlu tinjauan manusia. Aktivitas mencatat "Rekomendasi eskalasi" untuk tiap run yang merekomendasikan eskalasi; tidak ada teks "sudah dieskalasi".

### Marketing (1 run live, tahap Brief, Rian)

`workflow:"marketing"`, `stage:"brief"`, validasi `not_applicable`, 25,9 s, 32.272 token. `context_refs` memuat 4 file knowledge (brand-profile, brand-guidelines, content-pillars, content-research, klasifikasi Public Data atau Research Findings, sumber Hub SRC-01 dan SRC-06) dan 5 produk katalog "Regular Fit Short Sleeve Graphic T-Shirt" (SRC-02, URL produk, 2026-11-09). Bagian "Sumber jawaban" menampilkan semuanya.

### Verifikasi lain

- Evaluasi tersimpan dan dimuat ulang untuk dua rubrik (9 dimensi Marketing, 6 kriteria CS); baris uji dihapus dari log setelahnya. Kasus bergiliran dikirim berurutan dalam satu sesi (diperiksa pada POST: giliran 2 membawa `session_id`).
- Tanpa error konsol; tanpa overflow horizontal di 375 px; terang dan gelap diperiksa.
- Temuan: toast "selesai" menampilkan JSON mentah untuk run CS. Diperbaiki: toast memakai draf balasan.
- Tidak dijalankan: DEMO-B giliran 1, V01 sampai V06 dan preset Hub secara live (hemat token). Kartu dan Evaluasi dicek lewat pemutaran ulang run yang sudah ada.
- Screenshot: `frontend/screenshots/s3-cs21-*.png`.

### DEMO-B, all 3 turns live (10 Nov 2026, follow-up)

Agent siti ran `workflow:"cs"` in one session (`web-9c8eb6a637f1`) with real turns through the BFF, so the history was not embedded in the prompt. No simulation mode was used.

| Turn | Intent (secondary) | Priority | Escalation | Validation | Latency | Tokens |
|---|---|---|---|---|---|---|
| 1, damaged top | COMPLAINT_DAMAGED (RETURN_REFUND) | P1 | recommended, `recommendation_only` | valid, 1st try | 33.1 s | 17,634 |
| 2, refund, DEMO-CBX-002, 5 Nov | RETURN_REFUND (COMPLAINT_DAMAGED) | P1 | recommended | valid, 1st try | 18.9 s | 19,745 |
| 3, correction to the pleated skirt with the wrong colour | COMPLAINT_WRONG_ITEM (RETURN_REFUND) | P1 | recommended | valid, 1st try | 13.7 s | 22,371 |

**Comparison with Expected (turn 3):**
- Primary intent COMPLAINT_WRONG_ITEM is allowed by Expected. P1 and escalation recommended match.
- Context: the "top" claim is marked superseded. The summary keeps DEMO-CBX-002, 5 November, the refund request and the corrected item.
- Grounding: the 7-day rule is cited with CB-RETURNS-001 (refund-policy URL, 2026-11-07). There is no refund approval and no promise about processing time, because CB-REFUND-TIMING-UNKNOWN-001 is unknown.

**Verdict: pass.**

**Notes for the CS review (tone, not a violation):**
- The turn 3 draft apologises for "kekeliruan catatan" ("the error in our notes"), although the correction came from the customer.
- Every draft is signed "Siti, Layanan Pelanggan Colorbox".
