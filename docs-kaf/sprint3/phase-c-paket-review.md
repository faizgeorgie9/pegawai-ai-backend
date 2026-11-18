# Phase C: Paket review untuk project owner (Frontend, Kevin)

Tanggal paket: 7 November 2026. Lingkup: hanya Frontend Sprint 3.

> **Belum disetujui — diisi oleh project owner. Phase D/E tidak dianggap lulus sebelum persetujuan ini dicatat.**
>
> Catatan jujur: Phase D (buat/ubah agen, Tools, Computer Use, Scheduler, workspace Marketing dan CS dengan hasil terstruktur) dan Phase E (integrasi ke Hermes lewat BFF prototipe, uji E2E, laporan) **sudah dibangun mendahului gerbang persetujuan ini, atas permintaan Kevin**. Umpan balik dari owner akan diterapkan setelahnya, dan hasilnya dicatat di tabel "Umpan balik dan log perbaikan" di bawah.

## 1. Versi yang direview

| Item | Nilai |
|---|---|
| Repo | `pegawai-ai-backend` (folder `frontend/` dan `bff/`) |
| Branch | `feat/frontend-prototype` |
| Commit dasar | `42f78ad562dda8f416f62f0116c38c3dcf626666` ("feat: workspace Marketing dan CS, skenario uji, dan evaluasi reviewer") |
| Perubahan setelah commit dasar | Perbaikan hasil E2E (label status dashboard, tampilan Aktivitas di 375 px) belum di-commit pada saat paket ini ditulis; commit yang disetujui dicatat di bagian 6 |
| Runtime | Hermes v0.22.5, model `deepseek-v4.1-flash` via `opencode-go`, rute UI → BFF prototipe → Hermes |

### Cara menjalankan

Prasyarat: Node.js 22+, `uv`, Hermes gateway berjalan (`hermes gateway run`), Postgres dev, dan `bff/.env` (lihat README bagian "Menjalankan BFF").

```powershell
cd pegawai-ai-backend
.\start-dev.ps1          # menyalakan BFF (8090) dan frontend (5173), lalu membuka browser
# atau manual:
#   bff:       cd bff; uv run uvicorn bff.main:app --host 127.0.0.1 --port 8090 --loop asyncio:SelectorEventLoop
#   frontend:  cd frontend; npm run dev -- --port 5173
```

Buka `http://localhost:5173/`. Pemeriksaan cepat: `http://localhost:5173/bff/api/health` harus mengembalikan `{"ok":true,"db":true,"hermes":true}`.
Tanpa BFF, antarmuka tetap tampil dan menunjukkan pesan kesalahan ramah dengan tombol coba lagi.

### Daftar layar dan tangkapan layar

Semua path relatif terhadap `pegawai-ai-backend/frontend/screenshots/`.

| Layar | Rute | Desktop | Mobile 375 px |
|---|---|---|---|
| Dashboard | `#/` | `s3-dashboard.png` | `s3-dashboard-mobile.png` |
| Chat | `#/chat/<agen>` | `s3-chat.png` | `s3-chat-mobile.png` |
| Daftar agen | `#/agen` | `s3-agen-list.png` | `s3-agen-list-mobile.png` |
| Detail agen | `#/agen/<id>` | `s3-agen-detail.png` | `s3-agen-detail-mobile.png` |
| Ubah agen | `#/agen/<id>/ubah` | `s3-agen-edit.png` | `s3-agen-edit-mobile.png` |
| Tools / Plugins | `#/tools` | `s3-tools.png` | `s3-tools-mobile.png` |
| Computer Use (diblokir) | `#/computer-use` | `s3-computer-use.png` | `s3-computer-use-mobile.png` |
| Scheduler (diblokir) | `#/scheduler` | `s3-scheduler.png` | `s3-scheduler-mobile.png` |
| Workspace Marketing | `#/marketing` | `s3-marketing.png`, `s3-ws-marketing-brief.png`, `s3-ws-marketing-konten.png`, `s3-ws-marketing-contoh.png` | `s3-ws-marketing-mobile.png`, `s3-marketing-mobile.png` |
| Workspace CS | `#/cs` | `s3-cs.png`, `s3-ws-cs-hasil.png` | `s3-ws-cs-mobile.png` |
| Skenario uji | `#/uji` | `s3-uji-desktop.png` | `s3-uji-mobile.png` |
| Aktivitas | `#/aktivitas` | `s3-aktivitas.png` | `s3-aktivitas-mobile.png` |
| Grup | `#/grup/<id>` | `s3-grup.png` | (lihat `tahap2-mobile-live-grup.png`) |

Tangkapan layar uji E2E akhir (tema terang dan gelap, desktop dan 375 px): `s3-e2e-*.png` di folder yang sama, termasuk `s3-e2e-<layar>-d-light.png`, `-d-dark.png` (dashboard dan chat), `-m-light.png`, `-m-dark.png`.

## 2. Sebelum dan sesudah

| Area | Sprint 2 | Sprint 3 |
|---|---|---|
| Chat desktop terang | `chat-desktop-light.png` | `s3-chat.png` |
| Chat desktop gelap | `chat-desktop-dark-think.png` | `s3-e2e-chat-rian-d-dark.png` |
| Chat ponsel | `chat-phone-light.png` | `s3-chat-mobile.png` |
| Beranda / kantor | `tahap2-desktop-offline-home.png` | `s3-dashboard.png` |
| Daftar bot / agen | `tahap2-desktop-offline-bot.png` | `s3-agen-list.png` |
| Aktivitas | `tahap2-desktop-offline-aktivitas.png`, `panel-desktop-aktivitas.png` | `s3-aktivitas.png` |
| Dialog buat bot | `tahap2-desktop-dialog-bot-baru.png` | `s3-agen-edit.png` (halaman ubah penuh) |
| Grup | `tahap2-desktop-live-grup.png` | `s3-grup.png` |
| Ponsel, home | `tahap2-mobile-offline-home.png` | `s3-dashboard-mobile.png` |
| Hal baru (tidak ada di Sprint 2) | - | Tools, Computer Use, Scheduler, workspace Marketing, workspace CS, Skenario uji |

Perubahan utama: kartu Paket/kuota dihapus dari tampilan (di luar PRD), "Bot" dinamai ulang "Agen", ada Dashboard, halaman Agen lengkap, dan semua kemampuan diberi label jujur (Berfungsi, Contoh data, Belum didukung, Diblokir).

## 3. Referensi

- Wireframe: `docs/sprint3/wireframe/index.html` (tangkapan layar di `docs/sprint3/wireframe/screenshots/`).
- Catatan referensi dan inspirasi: `docs/sprint3/referensi-ui.md`.
- Fondasi UI Phase A: `docs/sprint3/phase-a-fondasi-ui.md`; kebutuhan API: `docs/sprint3/kebutuhan-api-frontend.md`; konteks: `docs/sprint3/konteks-sprint3.md`.
- Situs referensi: Malika Agent https://malika.ai/ (demo `#demo`), pegawAI https://pegawai.biz.id/ (aplikasi `#app`), Solvion https://solvion.id/, Officeverse https://officeverse.id/. Klaim fitur di situs itu adalah materi pemasaran dan belum diverifikasi. Video referensi YouTube Phase A belum ditinjau; Kevin meninjaunya sendiri.

## 4. Checklist owner

Beri tanda pada kolom Status (Setuju / Perlu perubahan) dan isi catatan.

| No | Area yang dinilai | Di mana melihatnya | Status | Catatan |
|---|---|---|---|---|
| 1 | Tata letak utama (sidebar, area utama, panel samping, tema terang/gelap, layar sempit) | Semua layar | | |
| 2 | Navigasi (urutan menu, rute, tombol kembali, label status "Diblokir") | Sidebar | | |
| 3 | Dashboard (ringkasan, tugas aktif, aktivitas terbaru, status kapabilitas) | `#/` | | |
| 4 | Chat (kirim, streaming, proses berpikir, chip tool, riwayat, Topik baru) | `#/chat/rian` | | |
| 5 | Pemilihan agen dan identitas (nama, peran, tim, status teks, ganti agen tanpa konten nyasar) | Sidebar, header chat | | |
| 6 | Daftar dan detail agen (cari, filter tim, buat, ubah, hapus) | `#/agen`, `#/agen/<id>` | | |
| 7 | Struktur halaman Tools / Plugins (ketersediaan, penugasan, status koneksi) | `#/tools` | | |
| 8 | Struktur halaman Computer Use (tugas, status, aktivitas; diblokir) | `#/computer-use` | | |
| 9 | Struktur halaman Scheduler (job, status; diblokir) | `#/scheduler` | | |
| 10 | Struktur workspace Marketing (lima tahap, kartu hasil terstruktur) | `#/marketing` | | |
| 11 | Struktur workspace CS (percakapan, kartu hasil, eskalasi) | `#/cs` | | |
| 12 | Label mock dan data (Contoh data, Dummy, Assumptions, "belum divalidasi backend", Simulasi) | Semua workspace | | |
| 13 | Skenario uji dan log eksperimen (rubrik, ekspor CSV/JSON) | `#/uji` | | |

## 5. Umpan balik dan log perbaikan

| No | Tanggal | Pemberi umpan balik | Layar | Umpan balik | Prioritas | Perbaikan (commit) | Retest | Status |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |

## 6. Catatan persetujuan

| Item | Isi |
|---|---|
| Reviewer | |
| Tanggal | |
| Versi yang disetujui (commit/tag) | |
| Catatan | |

Belum disetujui — diisi oleh project owner. Phase D/E tidak dianggap lulus sebelum persetujuan ini dicatat.
