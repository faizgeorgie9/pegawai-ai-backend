# Spec: Jembatan Drive/Gmail dengan aksi tulis + persetujuan (17 Nov 2026)

Lanjutan `spec-jembatan-google.md`. Keputusan user (jangan dibuka ulang):
- **Drive**: agen boleh membuat, mengedit, mengganti nama, dan memindah file apa pun. Menghapus = pindah ke Sampah Drive (bisa dipulihkan 30 hari) dan SELALU lewat persetujuan pengguna.
- **Gmail**: agen boleh memberi/menghapus label, menandai dibaca/belum, mengarsipkan, dan memindah ke Sampah (bisa dipulihkan) langsung. MENGIRIM email SELALU lewat persetujuan pengguna. Draf tetap boleh langsung.
- Aturan umum: aksi yang bisa dibatalkan boleh langsung; aksi permanen/keluar (hapus file, kirim email) butuh persetujuan.

## Aturan umum
Sama dengan `spec-ux-mvp.md` "Aturan umum". Jangan sentuh perubahan orang lain yang belum di-commit (product images, catalog.py, knowledge.py, test_catalog.py, rich.tsx, start-dev.ps1, .gitignore, migrasi 013/014, route product-images di main.py). Migrasi baru mulai `016_`. Token tidak pernah keluar dari BFF. Bahasa UI awam.

## Izin Google
- Drive: ganti `drive.readonly` dengan `https://www.googleapis.com/auth/drive`. Fitur impor Pengetahuan harus menerima salah satu dari keduanya. Koneksi lama yang hanya punya `drive.readonly`: alat baca tetap jalan, alat tulis menjawab "Sambungkan ulang Google Drive di halaman Aplikasi untuk memberi izin mengubah berkas."
- Gmail: tambah `https://www.googleapis.com/auth/gmail.modify` dan `https://www.googleapis.com/auth/gmail.send` (pertahankan yang ada). Koneksi tanpa izin itu: pesan "Sambungkan ulang Gmail…" yang setara.
- Kartu Aplikasi: satu kalimat per aplikasi tentang apa yang bisa dilakukan agen dan bahwa hapus file / kirim email selalu minta persetujuan Anda.

## Persetujuan (tahap A)
- Tabel `pending_actions` (id uuid, user_id, kind text, summary text, payload jsonb, status pending|approved|rejected|done|failed|expired, result text, source jsonb untuk konteks asal bila diketahui seperti bot/grup/run, created_at, decided_at). Kedaluwarsa otomatis setelah 24 jam.
- Alat berisiko tidak menjalankan aksi: ia membuat baris `pending` dan mengembalikan teks ke agen: "Menunggu persetujuan pengguna (#<id pendek>). Jangan ulangi permintaan ini; pengguna akan menyetujui atau menolak di aplikasi."
- Endpoint: `GET /api/actions?status=pending`, `POST /api/actions/{id}/approve` (menjalankan aksi lalu menyimpan hasil, idempoten, hanya dari status pending, satu transaksi), `POST /api/actions/{id}/reject`.
- UI: kartu "Perlu persetujuan Anda" berisi ringkasan yang jelas (mis. "Pindahkan 'Laporan Q3.pdf' ke Sampah Drive" / "Kirim email ke a@b.com — Subjek: …" dengan pratinjau isi), tombol "Setujui" dan "Tolak". Tampil di: Beranda bagian "Perlu persetujuan Anda" (sudah ada; gabungkan dengan rencana konten), dan di chat/grup tempat agen memintanya bila konteks asal tersedia (kalau tidak, cukup Beranda + badge angka di menu Beranda). Setelah diputuskan, kartu menunjukkan hasil ("Sudah dipindahkan ke Sampah" / "Terkirim" / "Ditolak").
- Agen diberi tahu hasilnya: alat `action_status(id)` agar agen bisa mengecek; tidak perlu memaksa pesan baru ke agen.

## Alat Drive (tahap A)
- `drive_create(name, content, folder_id?, kind=doc|text)`: membuat Google Doc (dari teks) atau berkas teks.
- `drive_update(file_id, content)`: mengganti isi Google Doc/berkas teks (tidak untuk PDF/biner; jawab ramah bila tidak didukung).
- `drive_rename(file_id, new_name)`, `drive_move(file_id, folder_id)`.
- `drive_trash(file_id)` → lewat persetujuan; saat disetujui: set `trashed=true` (bukan hapus permanen). Tidak ada alat hapus permanen.
- Validasi id, ukuran isi wajar (mis. maks 1 MB teks), pesan error ramah.

## Alat Gmail (tahap B)
- `gmail_label(message_id, add[], remove[])` (termasuk label sistem UNREAD/INBOX untuk tandai dibaca/arsip), `gmail_trash(message_id)` langsung (bisa dipulihkan).
- `gmail_send(to, subject, body, reply_to_message_id?)` → lewat persetujuan; saat disetujui kirim (balasan memakai threadId + header In-Reply-To/References bila reply_to diberikan). Validasi alamat, batasi jumlah penerima (mis. maks 10).
- `gmail_send_draft(draft_id)` → lewat persetujuan.

## Penerimaan
- pytest + build lolos; test di `bff/tests/test_bridge.py` / `test_actions.py` (HTTP Google di-mock): alat berisiko hanya membuat pending dan TIDAK memanggil Google; approve memanggil endpoint yang benar sekali (idempoten, approve kedua 409); reject tidak memanggil Google; expired tidak bisa di-approve; izin lama memberi pesan sambungkan ulang; trash memakai `trashed=true`, bukan delete.
- Uji nyata tahap A: minta Mira membuat Google Doc uji kecil di Drive, mengganti namanya, lalu meminta memindahkannya ke Sampah → kartu persetujuan muncul → Setujui → file ada di Sampah. (Drive pengguna perlu disambungkan ulang dengan izin baru — bila belum, berhenti di titik itu dan laporkan; jangan login atas nama pengguna.)
