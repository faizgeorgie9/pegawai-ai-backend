# Desain: Papan Tugas (Kanban) Pegawai AI — 18 Nov 2026

Status: **usulan, menunggu persetujuan Kevin**. Menggantikan pendekatan di `spec-kanban-kelola.md` (papan yang dibangun dari riwayat run).

## 1. Untuk apa Kanban, dan masalah apa yang diselesaikan

Kanban adalah papan tempat pemilik bisnis **mendelegasikan pekerjaan ke tim AI dan memantaunya sampai selesai**. Prinsip industri (Kanban University): pekerjaan terlihat, alur jelas, hambatan tampak, ada aturan eksplisit kapan kartu pindah.

Masalah yang diselesaikan untuk user kita:
| Masalah sekarang | Dengan papan tugas |
|---|---|
| Permintaan di chat "hilang" di obrolan; tidak jelas sudah dikerjakan atau belum | Setiap pekerjaan yang didelegasikan jadi kartu dengan status jelas |
| Diskusi tim "berhenti" padahal belum beres, user tidak tahu giliran siapa | Agen memindah kartu ke **Perlu Anda** dengan pertanyaan yang jelas; user menjawab di kartu dan agen lanjut |
| Membatalkan lewat chat tidak berpengaruh apa-apa | Batalkan = tombol di kartu, dan agen juga punya alat untuk membatalkan atas perintah user |
| Hasil kerja tersebar di chat | Hasil terakhir, komentar, dan riwayat langkah ada di satu kartu |
| Biaya dan jadwal tidak terlihat per pekerjaan | Kartu menampilkan jadwal, biaya, dan siapa yang mengerjakan |

Yang **bukan** tugas: setiap balasan chat. Riset produk agen (Linear, GitHub Copilot, Devin) menunjukkan sesi agen ditempelkan ke tugas yang didelegasikan, bukan ke tiap pesan.

## 2. Belajar dari Kanban Hermes

Kanban Hermes (kode lokal `hermes_cli/kanban_db.py`, `kanban_workflow.py`, `tools/kanban_tools.py`) adalah antrean kerja tahan-restart untuk agen:
- Status: triage, todo, scheduled, ready, running, blocked, review, done, archived, dengan matriks perpindahan yang ketat (running/review/scheduled tidak bisa di-drag, hanya lewat aksi).
- Kartu: judul, isi, assignee (profil agen), prioritas, induk/anak (dependensi), komentar, lampiran, riwayat event, riwayat percobaan (runs), hasil.
- Agen punya alat sendiri: buat tugas, pecah tugas, blokir (jenis: butuh input / dependensi / kemampuan / sementara), minta tinjauan, minta revisi, selesaikan dengan ringkasan, komentar.
- Dispatcher di gateway Hermes mengklaim tugas yang siap dan menjalankan agen; ada heartbeat, batas percobaan, dan auto-blokir setelah gagal berulang.

Kenapa tidak dipakai langsung sebagai mesin:
1. Satu database untuk seluruh instalasi Hermes; kita butuh data per pengguna (multi-tenant SaaS).
2. Tidak ada pencatatan biaya per tugas; padahal paket Gratis/Pro/Bisnis dan biaya USD kita bergantung pada itu.
3. Run dari dispatcher tidak lewat BFF: tidak muncul di chat, tombol Hentikan dan kartu persetujuan (Drive/Gmail) tidak terhubung.
4. Eksekutor eksternal (BFF mengklaim tugas Hermes) belum terverifikasi dan rawan bentrok klaim.

**Keputusan yang diusulkan:** tiru **model dan perilaku** Kanban Hermes (status, aksi, alat agen, aturan perpindahan, percobaan ulang), tapi simpan di Postgres kita dan jalankan lewat BFF. Papan Hermes asli tetap tidak dipakai (bisa disinkronkan nanti bila perlu).

## 3. Model

**Tugas** = satu pekerjaan yang didelegasikan. Field:
- judul, deskripsi (instruksi), pengerja (satu agen ATAU satu tim), jadwal mulai (opsional), prioritas (Normal/Penting).
- induk (untuk rencana konten: rencana = induk, tiap hari = anak).
- hasil terakhir (teks/berkas), komentar (percakapan user–agen di kartu), riwayat (event + run yang terhubung, dengan biaya).
- asal: dibuat user, dari chat, dari agen, dari rencana, dari jadwal berulang.

**Status internal (setara Hermes) → kolom untuk user:**
| Kolom user | Status internal | Arti untuk user |
|---|---|---|
| **Antre** | todo, scheduled, ready | "Akan dikerjakan" (+ lencana jam bila terjadwal) |
| **Dikerjakan** | running | "Agen sedang mengerjakan" + langkah terakhir |
| **Perlu Anda** | blocked (butuh input), review, menunggu persetujuan | "Agen menunggu jawaban / tinjauan Anda" + pertanyaannya |
| **Selesai** | done (berhasil/gagal/dibatalkan sebagai tanda) | "Sudah dikerjakan"; otomatis disembunyikan setelah 14 hari |
| (Arsip) | archived | tidak tampil; bisa dipulihkan dari filter |

Triage Hermes tidak ditampilkan di MVP.

**Tugas berulang** (jadwal): templat yang membuat satu tugas baru setiap waktunya tiba. Jadwal yang ada sekarang dimigrasikan ke sini.

## 4. Cara tugas lahir
1. **Tambah cepat** di kolom Antre: ketik judul → pilih agen/tim → (opsional) jadwal. Satu baris, Enter.
2. **Dari chat**: tombol kecil "Jadikan tugas" di pesan user; atau agen sendiri membuat tugas saat user meminta pekerjaan yang lebih dari satu balasan.
3. **Dari rencana konten**: rencana yang dibuat tim muncul sebagai satu kartu induk di **Perlu Anda** ("Setujui rencana"). Setujui → anak per hari masuk Antre. **Batalkan rencana** → induk + semua anak diarsipkan (memperbaiki bug rencana muncul lagi).
4. **Dari tugas berulang**.

## 5. Kartu dan panel detail (tetap sederhana)
- Kartu: judul, avatar pengerja, satu baris status (mis. pertanyaan agen / jam jadwal / langkah terakhir), biaya bila selesai, **satu tombol utama**, menu "⋯".
- Klik kartu → panel samping: instruksi, hasil terakhir, kolom komentar ("Balas ke agen…"), riwayat langkah (ringkas; detail teknis hanya mode admin), tombol aksi.

Aksi per kolom (utama tebal):
| Kolom | Aksi |
|---|---|
| Antre | **Kerjakan sekarang**; ⋯ Ubah, Jadwalkan ulang, Batalkan |
| Dikerjakan | **Hentikan**; ⋯ Buka obrolan |
| Perlu Anda | **Jawab** / **Setujui**; ⋯ Minta revisi (dengan catatan), Batalkan |
| Selesai | **Lihat hasil**; ⋯ Ulangi, Arsipkan |

Drag-and-drop hanya untuk perpindahan yang diizinkan (mis. Selesai → Antre = ulangi; ke Dikerjakan tidak bisa di-drag), sama seperti Hermes.

## 6. Agen ikut mengelola papan (lewat jembatan MCP `pegawai` yang sudah ada)
Alat baru: `task_list`, `task_create` (judul, instruksi, pengerja, jadwal, induk), `task_comment`, `task_ask_user` (pindah ke Perlu Anda dengan pertanyaan), `task_request_review` (hasil siap ditinjau), `task_complete` (dengan ringkasan hasil), `task_cancel` (arsip; bisa dipulihkan, jadi boleh langsung atas perintah user).
Dengan ini "batalkan semuanya" di chat benar-benar membatalkan, dan diskusi tim yang menunggu jawaban otomatis muncul di Perlu Anda.

## 7. Eksekusi (BFF sebagai dispatcher)
- Penjadwal BFF yang sudah ada diperluas: setiap tick mengambil tugas `ready` (jadwal tiba / "Kerjakan sekarang"), menjalankan agen atau tim lewat gateway dengan konteks tugas (instruksi + komentar terakhir), dan menautkan run ke tugas (biaya, Hentikan, persetujuan Drive/Gmail tetap jalan).
- Saat run selesai: bila agen memanggil alat tugas, statusnya mengikuti; bila tidak, default ke **Perlu Anda – tinjau hasil** (tidak pernah diam-diam "selesai").
- User membalas di kartu → tugas kembali `ready` dan agen melanjutkan dengan balasan itu.
- Batas: maks 2 percobaan otomatis, batas waktu per run, gagal berulang → Perlu Anda dengan pesan ramah.
- Batas WIP sederhana: satu tugas berjalan per agen; sisanya antre.

## 8. MVP vs nanti
**MVP (diusulkan untuk dikerjakan sekarang):** tabel tugas + komentar + event; 4 kolom; tambah cepat; panel detail; aksi per kolom; rencana sebagai induk/anak dengan Setujui/Batalkan; tugas berulang menggantikan jadwal; dispatcher BFF; alat agen (§6); balasan chat tidak lagi jadi kartu; migrasi jadwal lama.
**Nanti:** dependensi antar tugas, pecah tugas otomatis oleh agen (swarm/decompose), banyak papan, label/checklist, lampiran unggahan di kartu, notifikasi WhatsApp/email, tampilan kalender, metrik alur, sinkron dengan Kanban Hermes asli.

## 9. Risiko
- Ukuran kerja besar (perkiraan 2–3 hari kerja agen): dipecah tahap A (data + papan + aksi user), B (dispatcher + migrasi jadwal/rencana), C (alat agen + Perlu Anda otomatis).
- Perubahan perilaku penjadwal yang sudah dipakai demo; migrasi harus menjaga jadwal yang ada.

Sumber: Kanban University principles; Microsoft Azure Boards Kanban quickstart; Linear agent interaction docs; Devin session API; GitHub Copilot coding agent docs; Hermes Kanban docs + kode lokal di `%LOCALAPPDATA%\hermes\hermes-agent`.
