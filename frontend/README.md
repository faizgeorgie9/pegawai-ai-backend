# Pegawai AI — Frontend

React + Vite. Semua permintaan browser lewat `/bff/api/...`; proxy Vite meneruskannya ke BFF lokal di
`127.0.0.1:8090` dan menambahkan `BFF_API_KEY` dari `.env.local` (kunci tidak pernah sampai ke browser).

## Menjalankan

```bash
npm install
npm run dev                 # data asli dari BFF
npm run dev:mock            # data contoh untuk endpoint yang belum ada di BFF
npm run dev:mock -- --port 5199 --strictPort
npm run build               # tsc --noEmit + vite build
```

`npm run dev:mock` tetap **butuh BFF hidup**: login, daftar pegawai, dan halaman dasar dibaca dari BFF.
Mode contoh hanya menjawab endpoint baru dan menambahkan field baru pada jawaban BFF.

## Mode contoh (`dev:mock`)

Saat aktif, pojok kiri bawah menampilkan lencana **“Mode contoh: data palsu”** (`role="status"`).
Lencana itu berarti angka dan berkas di layar adalah contoh, bukan data pelanggan sungguhan.

Yang berubah saat mode contoh aktif:

- Endpoint baru dijawab di browser (Telegram, akun AI, posting Instagram, percakapan/WhatsApp,
  Output, template dan pembuatan tim di Mulai, cara kerja, lampiran contoh).
- Jawaban BFF yang sudah ada didekorasi (aksi persetujuan palsu, sesi Telegram, tautan asal Output,
  jumlah percakapan) tanpa menutupi galat BFF.
- Berkas contoh (PNG/WAV/WebM/PDF/CSV/DOCX/XLSX/ZIP) dibuat di memori oleh `mock-assets.ts`.
  Tidak ada berkas biner contoh di repo.

**Mock tidak pernah ikut build produksi.** `VITE_MOCK_API === '1'` diganti literal saat kompilasi,
sehingga cabang `import('./mock-api')` dibuang; `mock-api.ts` juga melempar galat bila termuat di
`import.meta.env.PROD`; `vite.config.ts` menolak build produksi yang masih membawa `VITE_MOCK_API=1`.
Pemeriksaan setelah `npm run build`:

```bash
grep -rl "__PA_MOCK__" dist     # harus kosong
ls dist/assets | grep -i mock   # harus kosong
```

Di PowerShell: `Get-ChildItem dist -Recurse | Select-String -Pattern "__PA_MOCK__" -List` dan
`Get-ChildItem dist/assets | Where-Object Name -match 'mock'`.

## Konsol `__mock`

Buka DevTools → Console di halaman mana pun saat `dev:mock`.

| Perintah | Arti |
|---|---|
| `__mock.set('handover','pages')` | pilih nilai skenario |
| `__mock.get()` | lihat semua nilai yang aktif |
| `__mock.reset()` | kembali ke nilai awal, hapus latensi dan `pa.mock.handover` / `pa.mock.fresh` |
| `__mock.latency(1500)` | jeda jawaban mock dalam ms (awal 400; `0` = seketika) |
| `__mock.emit('handover')` | kirim satu event “pelanggan butuh manusia” (toast + lencana + kartu Beranda) |

Setelah `set`, **muat ulang halaman** agar data dibaca ulang (kecuali `emit`).
Nilai disimpan di `localStorage['pa.mock']`; latensi di `pa.mock.latency`; data demo di
`pa.mock.demo`, `pa.mock.social`, `pa.mock.handover`, `pa.mock.fresh`.

Catatan: `__mock.reset()` **tidak** menghapus sesi `/demo` dan draf persetujuan yang sudah dibuat.
Untuk membersihkannya: `localStorage.removeItem('pa.mock.demo'); localStorage.removeItem('pa.mock.social')`
lalu muat ulang.

## Daftar skenario

Nilai **(awal)** adalah nilai sebelum diubah. Semua kunci boleh dikombinasikan.

| Kunci | Nilai | Yang terlihat |
|---|---|---|
| `attachments` | `ok` (awal), `empty`, `gone`, `slow`, `huge` | `gone`: berkas 404 “Berkas ini sudah tidak tersedia.”; `slow`: berkas tiba setelah 4 dtk; `huge`: video 90 MB + tautan 404 |
| `artifactLink` | `on` (awal), `off` | `off`: `POST /artifacts/{id}/link` 404, UI memakai blob biasa |
| `skills` | `list` (awal: 3 item), `empty`, `full` (30), `staff` (`can_edit:false`), `fail` (daftar 500), `slowscan` (simpan 6 dtk) | halaman Cara kerja |
| `ai` | `none` (awal), `ok` (OpenRouter + Anthropic), `invalid` (Anthropic ditolak), `orinvalid` (OpenRouter ditolak), `fail` (daftar 500), `keyreject` (kunci baru 422) | Pengaturan → Akun AI |
| `telegram` | `none` (awal), `pending`, `connected`, `error`, `fail` (baca 500) | tab Telegram pegawai |
| `telegramExpiry` | `600` (awal, detik), mis. `20` | umur tautan/QR; habis → “Tautan sudah kedaluwarsa.” |
| `telegramConfirm` | `confirm` (awal), `never` | `never`: pairing tidak pernah selesai |
| `telegramPending` | `off` (awal), `on` | dengan `telegram=connected`: “Tersambung” **dan** “Meminta izin · 1” (Dewi) sekaligus; **Izinkan** memindahkannya ke daftar yang boleh memakai bot |
| `instagram` | `disconnected` (awal), `connected`, `personal`, `reconnect`, `broken`, `notconfigured` | kartu Instagram di Aplikasi |
| `canva` | sama seperti `instagram`, tanpa `personal` | kartu Canva di Aplikasi |
| `posts` | `mixed` (awal: terbit/menunggu/gagal), `empty`, `publishing`, `fail` (daftar 500) | daftar “Posting Instagram” setelah **Lihat posting**; `fail` → “Daftar posting belum bisa dimuat.” |
| `publish` | `ok` (awal), `fail` | hasil setelah **Setujui**: “Terbit di Instagram.” atau “Instagram menolak gambar ini…” |
| `approval` | `pending` (awal), `expired`, `fail` | kartu persetujuan `/demo posting`: `expired` → “Kedaluwarsa.” tanpa tombol; `fail` → **Setujui**/**Tolak** 500 dan pesan “Persetujuan belum bisa dikirim…” |
| `socialMedia` | `carousel` (awal), `image`, `reel` | media di kartu persetujuan: 3 gambar carousel, 1 gambar, atau 1 video reel |
| `output` | `many` (awal, 30), `few` (3), `empty`, `fail` (500), `slow` (3 dtk) | halaman Output |
| `outputSources` | `auto` (awal), `group`, `task`, `both` | `both`: berkas non-gambar pertama menampilkan **Buka tim** (`#/grup/mock-grp-1`), berikutnya **Lihat di Jadwal & tugas** (`#/kanban`) |
| `outputCounts` | `on` (awal), `off` | `off`: BFF mengirim `counts:null`; chip tanpa angka dan teks “24 hasil” (tanpa “dari 30”) |
| `whatsapp` | `real` (awal), `ready`, `notconfigured`, `error`, `fail` | status WhatsApp di kartu Aplikasi/tab pegawai |
| `handover` | `queue` (awal), `empty`, `fail` (daftar 500), `pages`, `noresume`, `actionfail` | antrean Pelanggan/Beranda; lihat tabel khusus di bawah |
| `handoverPing` | `off` (awal), `auto` | `auto`: 8 dtk setelah halaman dimuat `mock-conv-3` minta manusia + event `handover` |
| `a2a` | `on` (awal), `off` | sesi “Brief carousel dari Rian” dan tanda antar-pegawai |
| `onboarding` | `off` (awal), `fresh`, `limit`, `teamfail` | alur `#/mulai`; lihat tabel khusus di bawah |
| `templates` | `real` (awal), `sample`, `few`, `fail` | daftar template pegawai di Mulai |

### `handover`

| Nilai | Hasil |
|---|---|
| `queue` | 5 percakapan contoh: 2 minta manusia (`mock-conv-1`, `mock-conv-5`), 1 diambil alih (`mock-conv-2`), 2 dijawab bot |
| `empty` | tidak ada percakapan; angka semua 0 |
| `fail` | `GET /conversations` 500 → daftar menampilkan galat + **Coba lagi** |
| `pages` | 39 percakapan (32 minta manusia). Filter **Perlu manusia** memuat 30 baris + **Muat lebih banyak**; halaman kedua 2 baris. Beranda menampilkan 3 nama + “Dan 29 lainnya di Pelanggan”. Buka `mock-conv-1`: benang memuat 4 pesan terbaru + **Muat pesan sebelumnya** (total 6) |
| `noresume` | `mock-conv-2` berstatus diambil alih **tanpa** kalimat “Kembali otomatis pukul …” |
| `actionfail` | daftar dan detail tetap terbaca; **Ambil alih** / **Kembalikan** gagal 500 → “Aksi belum bisa dikirim. Coba lagi sebentar.” dan keadaan tidak berubah |

### `onboarding`

| Nilai | Hasil |
|---|---|
| `fresh` | `GET /bots` dan `GET /groups` mulai kosong; hasil `POST` disimpan di `pa.mock.fresh` |
| `limit` | seperti `fresh`, tetapi pegawai ke-4 ditolak 402 dan `GET /me` membawa `limits.max_bots: 3` |
| `teamfail` | pegawai berhasil dibuat, tetapi `POST /groups` 500; layar akhir “Tim Anda siap” + catatan “Tim belum bisa dibuat. Anda bisa membuatnya nanti di halaman Tim.” |

## Perintah `/demo` di Chat

Ketik di kotak pesan pegawai (mis. `#/chat/siti`). Mock menjawab sebagai run `mock-run-N`, memutar
tiga potongan teks, lalu selesai dengan lampiran contoh.

| Perintah | Hasil |
|---|---|
| `/demo gambar` | 1 PNG 1080×1350 |
| `/demo galeri` | 4 gambar (1:1, 4:5, 16:9) |
| `/demo video` | 1 WebM 16:9, 2 dtk, ada thumbnail |
| `/demo video besar` | 1 video 90 MB (uji “terlalu besar, unduh saja”) |
| `/demo suara` | 1 WAV 2 dtk |
| `/demo dokumen` | PDF + DOCX |
| `/demo tabel` | CSV 12 baris × 5 kolom + XLSX |
| `/demo semua` | satu dari tiap jenis |
| `/demo rusak` | 1 lampiran yang selalu 404 |
| `/demo posting` | teks “Draf postingan siap…” + kartu persetujuan `social_publish_post` (3 gambar, 380 huruf) |
| `/demo posting panjang` | sama, keterangan 2.340 huruf (melewati batas 2.200) |

Kartu persetujuan muncul di Beranda (dan di chat yang sesinya sama). Sesudah **Setujui**, status
berubah `approved` → `done`/`failed` dalam 2 dtk sesuai skenario `publish`, dan daftar posting ikut
berubah.

## Skenario cepat untuk menguji cabang UI

Semua perintah dijalankan di Console, lalu halaman dimuat ulang (kecuali yang menyebut klik).

| Cabang | Perintah | Yang harus terlihat | Bukti |
|---|---|---|---|
| Telegram tersambung + permintaan izin | `__mock.reset(); __mock.set('telegram','connected'); __mock.set('telegramPending','on')` → `#/agen/siti?tab=telegram` | “Tersambung”, 2 orang diizinkan, “Meminta izin · 1” (Dewi) | `after/mock-telegram-connected-pending-1280.png`, `…-375-gelap.png` |
| OpenRouter perlu disambungkan ulang | `__mock.set('ai','orinvalid')` → `#/pengaturan/akun-ai` | “Perlu disambungkan ulang”, “Kunci ini tidak lagi diterima.”, **Sambungkan ulang**; klik tombol itu → “OpenRouter tersambung.” | `after/mock-ai-openrouter-invalid-1280.png` |
| Kartu persetujuan 1 gambar | `/demo posting`, lalu `__mock.set('socialMedia','image')` → `#/` | pratinjau satu gambar persegi, tanpa “3 gambar” | `after/mock-approval-single-image-1280.png` |
| Kartu persetujuan reel | `__mock.set('socialMedia','reel')` → `#/` | satu pemutar video `post-reel` | `after/mock-approval-reel-1280.png`, `…-375-gelap.png` |
| Persetujuan kedaluwarsa | `__mock.set('approval','expired')` → `#/` | “Kedaluwarsa.”, tanpa tombol Setujui/Tolak | `after/mock-approval-expired-1280.png` |
| Setujui/Tolak gagal | `__mock.set('approval','fail')` → `#/`, klik **Setujui** (atau **Tolak**) | “Persetujuan belum bisa dikirim. Coba lagi sebentar.”, kartu tetap menunggu | `after/mock-approval-fail-1280.png` |
| Daftar posting gagal dimuat | `__mock.set('instagram','connected'); __mock.set('posts','fail')` → `#/aplikasi`, klik **Lihat posting** | “Daftar posting belum bisa dimuat. Coba lagi sebentar.” | `after/mock-instagram-posts-fail-1280.png` |
| Daftar percakapan >1 halaman | `__mock.set('handover','pages')` → `#/pelanggan` | 30 baris + **Muat lebih banyak**; klik → 32 baris, tombol hilang | `after/mock-pelanggan-list-more-1280.png`, `…-375-terang.png` |
| Pesan lama | `handover=pages` → `#/pelanggan/mock-conv-1` | 4 pesan + **Muat pesan sebelumnya**; klik → 6 pesan urut waktu | `after/mock-pelanggan-thread-older-1280.png` |
| Beranda “Dan N lainnya” | `handover=pages` → `#/` | “Pelanggan butuh manusia 32”, 3 baris, “Dan 29 lainnya di Pelanggan” | `after/mock-beranda-needs-human-more-1280.png` |
| Ambil alih gagal | `__mock.set('handover','actionfail')` → `#/pelanggan/mock-conv-1`, klik **Ambil alih** | “Aksi belum bisa dikirim…”, banner tetap “meminta bantuan manusia” | `after/mock-handover-action-fail-1280.png` |
| Diambil alih tanpa `resume_at` | `__mock.set('handover','noresume')` → `#/pelanggan/mock-conv-2` | “Diambil alih oleh Anda.” tanpa “Kembali otomatis pukul …” | `after/mock-handover-human-no-resume-1280.png` |
| Asal hasil: tim | `__mock.set('outputSources','group')` → `#/output`, buka PDF `katalog-koleksi.pdf` | tautan **Buka tim** → `#/grup/mock-grp-1` | `after/mock-output-source-group-1280.png` |
| Asal hasil: tugas | `__mock.set('outputSources','both')` → `#/output`, buka CSV `stok-gudang.csv` (dengan `task`, tautan ini ada di berkas non-gambar pertama) | tautan **Lihat di Jadwal & tugas** → `#/kanban` | `after/mock-output-source-task-1280.png` |
| Output tanpa angka | `__mock.set('outputCounts','off')` → `#/output` | chip tanpa angka, “24 hasil” (tanpa “dari 30”) | `after/mock-output-counts-null-1280.png`, `…-375-terang.png` |
| Tim gagal dibuat saat Mulai | `__mock.set('onboarding','teamfail')` → `#/mulai`, pilih usaha → **Buat 3 pegawai** | “Tim Anda siap” + “Tim belum bisa dibuat…” | `after/mock-onboarding-team-fail-1280.png` |

Screenshot ada di `docs-kaf/sprint6/after/`. Semua diambil di Chromium headless, 1280×800 atau
375×812; tidak ada `scrollWidth > clientWidth` pada tangkapan 375.

## Untuk pengembang backend

Bentuk jawaban yang ditiru mock mengikuti `docs-kaf/sprint6/kontrak-tambahan-fe-platform.md`
(K1–K5) dan `spec-layar-fitur-baru.md` §2.2. Bila kontrak berubah, ubah mock dan tangkapan di atas
bersamaan; jangan mengubah komponen UI hanya agar cocok dengan mock.
