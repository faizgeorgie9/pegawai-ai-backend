# Spec: Jadwal & tugas bisa dikelola user (18 Nov 2026)

Masalah: halaman Jadwal & tugas (`frontend/src/Kanban.tsx`, data `GET /api/kanban`) hanya untuk melihat. Mengelola jadwal (`#/scheduler` di Kemampuan) hanya ada di mode admin, jadi user awam tidak bisa menghapus, menjeda, atau membuat jadwal. Keputusan user: Kanban menjadi tempat user mengelola pekerjaan tim AI-nya, dan **harus tetap sederhana untuk user awam**.

## Aturan umum
Sama dengan `spec-ux-mvp.md` "Aturan umum": branch `feat/frontend-prototype` (jangan buat branch/worktree, jangan commit/push), jangan sentuh perubahan orang lain yang belum di-commit (lihat `git status`: catalog.py, knowledge.py, main.py bagian product-images, rich.tsx, start-dev.ps1, .gitignore, migrasi 013/014, product_*). Bahasa UI awam, tanpa istilah teknis (cron, run, occurrence, profil, ID). Pakai skill design-taste-frontend untuk tampilan dan ikuti gaya yang sudah ada (`pages.css`, kelas `btn`, `Dialog` dari `ui.tsx`).

## Prinsip kesederhanaan (wajib)
- Satu kartu menampilkan paling banyak **satu tombol utama** yang terlihat. Tindakan lain ada di menu "⋯" kecil. Tidak ada deretan tombol.
- Teks tombol berupa kata kerja biasa: "Jeda", "Lanjutkan", "Hapus jadwal", "Hentikan", "Tinjau", "Buka obrolan".
- Hapus selalu minta konfirmasi satu kalimat ("Hapus jadwal 'X'? Tugas yang belum jalan tidak akan dikerjakan.").
- Setiap kolom punya satu baris penjelas pendek di bawah judulnya, mis. Menunggu: "Akan dikerjakan sesuai jadwal"; Berjalan: "Agen sedang mengerjakan"; Perlu tindakan → ganti label menjadi **"Perlu Anda"**: "Agen menunggu persetujuan atau jawaban Anda"; Selesai: "Sudah dikerjakan".
- Kolom kosong menampilkan kalimat ramah, bukan area kosong.

## Tindakan per kartu (pakai endpoint yang SUDAH ada; tidak perlu endpoint baru)
- Kartu dari jadwal (todo): utama "Jeda"; menu: "Hapus jadwal". Jadwal dijeda (Perlu Anda): utama "Lanjutkan"; menu: "Hapus jadwal". Endpoint: `api.scheduleAction(id, 'pause'|'resume')`, `api.deleteSchedule(id)`.
- Kartu berjalan: utama "Hentikan" (konfirmasi) → `api.stopRun` / `api.stopOccurrence` / `POST /groups/{gid}/stop` sesuai sumber kartu.
- Kartu rencana menunggu persetujuan / agen menunggu jawaban: utama "Tinjau" → membuka chat/grup asal (tempat kartu persetujuan sudah ada). Jangan duplikasi UI persetujuan.
- Kartu selesai/gagal: utama "Buka obrolan" bila sumbernya chat/grup; tanpa tombol bila tidak ada tujuan.
- Kartu dari Kanban Hermes (`source: 'hermes'`): tanpa tindakan.
- Setelah tindakan, muat ulang papan; tampilkan error ramah bila gagal.
Bila data kartu dari `/api/kanban` belum membawa id yang dibutuhkan (schedule id, occurrence id, run id, group id), tambahkan field itu di `bff/bff/kanban.py` (bukan di main.py) dan di parser `bff.ts`, plus perbarui test kanban yang ada.

## "Jadwal baru"
Tombol di kepala halaman membuka `Dialog` dengan form pendek:
1. "Apa yang perlu dikerjakan?" (textarea; judul diambil otomatis dari ~6 kata pertama).
2. "Siapa yang mengerjakan?" (pilih agen atau tim; tampilkan nama, bukan id).
3. "Kapan?" (jam) + "Ulangi" berupa pilihan: "Setiap hari", "Hari kerja (Sen–Jum)", atau pilih hari (chip Sen…Min).
Kirim lewat `api.createSchedule({title, prompt, days, time, bot_id | group_id})`. Lihat cara layar admin scheduler membangun input ini dan pakai ulang logikanya bila ada.
Admin-only tetap: layar scheduler teknis di Kemampuan tidak diubah.

## Penerimaan
- `npm --prefix frontend run build` lolos; `uv run pytest` di `bff` lolos (bila kanban.py diubah).
- Uji di browser bawaan (localhost, mode admin MATI): buat jadwal baru → muncul di Menunggu → Jeda → pindah ke Perlu Anda → Lanjutkan → Hapus (dengan konfirmasi) → hilang. Kartu rencana menunggu → "Tinjau" membuka grupnya. Cek lebar ponsel 375 px tidak ada scroll horizontal.
- Jangan menghapus jadwal milik user yang sudah ada saat uji; buat jadwal uji sendiri lalu hapus.
