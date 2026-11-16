# Walkthrough self-service: pegawai AI (Sprint 4, hari 4-5)

Tanggal uji: 16 Nov 2026 (dini hari, WIB). Penguji berperan sebagai pengguna non-teknis di browser bawaan.
Cabang: `feat/frontend-prototype`. Tumpukan layanan: Hermes asli (gateway 8642, v0.22.5), server BFF (8090), frontend (5173), Postgres uji di port 5433.
Model: bawaan paling murah (`deepseek-v4.1-flash`). Total 7 tugas model sungguhan (batas 12). Tidak ada kredensial atau data pribadi di dokumen ini.

Arti hasil: berhasil / sebagian / gagal / tidak diuji.

## Ringkasan cepat

| Langkah | Hasil | Perlu bantuan teknis AITopTrends? |
|---|---|---|
| 1. Buat agen | sebagian | Ya, batas paket Gratis (3 agen) menghentikan; paket hanya bisa diganti lewat API |
| 2. Ubah agen: model dan tingkat berpikir | berhasil | Tidak |
| 3. Chat dengan agen | berhasil | Tidak |
| 4. Knowledge Base: berkas dan link website | berhasil | Tidak |
| 5. Grup dengan lima peran | berhasil | Tidak |
| 6. Permintaan rencana multi-hari, kartu persetujuan | sebagian | Perbaikan sudah dibuat (lihat catatan) |
| 7. Setujui rencana, cek Jadwal | berhasil | Tidak |
| 8. Satu kejadian jatuh tempo: Writer lalu Visual | berhasil | Tidak |
| 9. Kanban mencerminkan pekerjaan | berhasil | Tidak |
| 10. Biaya dalam USD | berhasil | Tidak |
| 11. Kartu draft di Alat (Hubungkan aplikasi) | berhasil (draft) | Ya, sambungan akun belum dibuat |

## Detail per langkah

### 1. Buat agen
- Yang dilakukan pengguna: Agen > Agen baru > tab Buat sendiri, isi nama (Mira), peran (Project Manager), tim (Marketing), persona, lalu Buat agen.
- Hasil: sebagian.
- Bukti: percobaan pertama ditolak dengan pesan "Batas penggunaan tercapai. Coba lagi nanti." karena paket Gratis hanya mengizinkan 3 agen (sudah ada 5 agen bawaan). Pesan itu menyesatkan (bukan soal waktu) dan menyebut "bot". Sudah diperbaiki: pesan sekarang menyebut batas yang kena ("Batas jumlah agen di paket Anda tercapai. Hapus agen yang tidak dipakai, atau hubungi tim AITopTrends untuk menaikkan paket."). Layar ganti paket sengaja disembunyikan di UI, jadi pengguna tidak bisa menaikkan paket sendiri. Untuk melanjutkan uji, paket diganti ke Bisnis lewat API (`PUT /me/plan`). Setelah itu Mira berhasil dibuat lewat UI (id `mira`); proses membuat agen memakan sekitar 40 detik dan UI menampilkan bilah proses "bisa sampai 40 detik". Empat agen lain (Sari/Strategist, Reza/Researcher, Wulan/Writer, Vino/Visual Designer) dibuat lewat API untuk menghemat waktu; tidak diuji lewat UI.
- Catatan: agen yang dibuat di luar UI baru muncul setelah halaman dimuat ulang.
- Perlu bantuan teknis: ya, untuk menaikkan paket.

### 2. Ubah agen: model dan tingkat berpikir
- Yang dilakukan: Agen > Mira > Ubah, ubah Tingkat berpikir ke Rendah, Simpan. Daftar Model tersedia.
- Hasil: berhasil. Halaman detail menampilkan "Tingkat berpikir: Rendah" dan model "Bawaan (deepseek-v4.1-flash)".
- Catatan UX (belum diperbaiki): daftar Model adalah daftar panjang nama teknis (claude-opus-4-8, gpt-5.6-terra, dst., sekitar 40 pilihan) tanpa penjelasan mana yang murah atau cepat. Pengguna awam akan bingung; perlu nama ramah dan petunjuk harga.
- Perlu bantuan teknis: tidak untuk fungsi; ya untuk menyusun daftar model yang ditawarkan ke pengguna.

### 3. Chat dengan agen
- Yang dilakukan: Chat > Mira > tulis "Halo Mira, sebutkan dalam satu kalimat apa tugasmu di tim."
- Hasil: berhasil. Jawaban satu kalimat sesuai persona. Tugas `cf6016df`, 8.741 token masuk, 46 keluar, biaya di bawah $0.01.
- Catatan: jawaban diawali baris kecil berbahasa Inggris ("No tools needed.") yang berasal dari proses berpikir model; muncul sebagai judul lipatan. Tidak merusak, tetapi terlihat teknis.
- Perlu bantuan teknis: tidak.

### 4. Knowledge Base: berkas dan link website
- Yang dilakukan: klik ikon klip dan pilih berkas kecil `kebijakan-colorbox.txt` (isi: garansi cat 18 bulan, kode promo HEMAT25). Lalu tulis "Simpan website ini ke Knowledge Base: https://example.com . Lalu jawab ... berapa bulan garansi cat dan apa kode promo bulan ini?"
- Hasil: berhasil. Berkas muncul sebagai chip "tersimpan". Link disimpan ("Knowledge Base: tersimpan, Example Domain"). Jawaban agen benar dan menyebut sumber: 18 bulan, kode HEMAT25, `[kebijakan-colorbox.txt]`. Tugas `3dd2b736`, 9.013 token masuk, 236 keluar.
- Catatan uji: pemilih berkas asli tidak bisa dijalankan dari browser bawaan, jadi berkas dimasukkan lewat skrip yang memicu penangan UI yang sama. Unggah lewat dialog sistem operasi belum dicoba manual.
- Perlu bantuan teknis: tidak. (Drive pribadi belum tersedia, lihat langkah 11.)

### 5. Grup dengan lima peran Colorbox marketing
- Yang dilakukan: Grup > Grup baru, nama "Tim Marketing Uji", centang Mira (PM), Sari (Strategist), Reza (Researcher), Wulan (Writer), Vino (Visual).
- Hasil: berhasil. Grup dibuat dengan lima anggota (batas paket Gratis hanya 1 grup; paket Bisnis dipakai).
- Perlu bantuan teknis: tidak, selain batas paket.

### 6. Permintaan rencana multi-hari, kartu persetujuan
- Yang dilakukan: di grup, tulis "@Mira susun rencana konten 2 hari berurutan mulai besok untuk Kaos Basic Colorbox, jam 09:00."
- Hasil: sebagian. Percobaan pertama ("buat rencana konten 2 hari ...") hanya menghasilkan teks biasa dan Mira menyebut tiga anggota lain, sehingga diskusi berantai mulai berjalan (satu tugas Sari dibatalkan lewat tombol Berhenti). Penyebab: tidak ada instruksi yang mengajarkan agen format rencana, sehingga kartu persetujuan hanya muncul bila model kebetulan menulisnya. Diperbaiki (commit `303982f`): instruksi grup sekarang menjelaskan format rencana dan meminta agen tidak menyebut @anggota lain di pesan rencana. Setelah perbaikan, permintaan kedua menghasilkan kartu "Rencana konten, 2 hari" dengan tombol Setujui rencana dan Minta revisi (tugas `e2558c41`).
- Catatan: bergantung pada kepatuhan model; kartu belum dijamin muncul 100%. Tombol Minta revisi tidak dicoba.
- Perlu bantuan teknis: perbaikan sudah masuk; pantau di uji berulang.

### 7. Setujui rencana, cek Jadwal
- Yang dilakukan: klik Setujui rencana, lalu buka Kemampuan > Jadwal.
- Hasil: berhasil. Muncul jadwal "Rencana Konten Kaos Basic Colorbox (2 hari)" dengan dua kejadian (Sel 17 Nov 09.00 WIB dan Rab 18 Nov 09.00 WIB), agen Wulan dan Vino, status Terjadwal, "Berikutnya: Sel, 17 Nov". Tanggal "mulai besok" benar.
- Catatan: Jadwal juga berisi jadwal peninggalan uji sebelumnya (Rangkuman harian oleh Rian, Konten 3 hari Colorbox). Itu akan jalan sungguhan pukul 09.00 bila server menyala; layanan dimatikan di akhir uji ini.
- Perlu bantuan teknis: tidak.

### 8. Satu kejadian jatuh tempo: Writer lalu Visual
- Yang dilakukan: waktu kejadian "Hari 1" dimajukan ke 3 menit dari sekarang lewat basis data (hanya untuk uji), lalu ditunggu.
- Hasil: berhasil. Pukul 00.27 kejadian mulai otomatis: Wulan (Writer) menulis naskah carousel (tugas `9558df0c`), lalu Vino (Visual) menulis arahan visual berdasarkan naskah itu (tugas `2f9b9895`). Selesai 00.28; status Selesai, biaya di bawah $0.01. Kejadian Hari 2 tetap Terjadwal.
- Perlu bantuan teknis: tidak.

### 9. Kanban mencerminkan pekerjaan
- Hasil: berhasil. Hari 1 muncul di kolom Selesai dengan biaya, tugas grup dan chat muncul dengan agen, grup, sumber (Chat, Grup, Jadwal), waktu, dan biaya; tugas yang dibatalkan ditandai "Dibatalkan"; kejadian mendatang ada di kolom Menunggu (sebelumnya "Antre", diganti agar jelas). Kanban Hermes tersambung (hanya dibaca, 0 tugas).
- Catatan: tugas gagal lama (mis. "Tidak bisa menghubungi Hermes. Pastikan gateway berjalan.") masih tampil dengan kata teknis karena tersimpan di riwayat; pesan baru sudah diganti. Papan memuat butuh beberapa detik.
- Perlu bantuan teknis: tidak.

### 10. Biaya dalam USD
- Hasil: berhasil. Pengaturan > Paket dan pemakaian menampilkan biaya bulan ini dalam USD ($0.51, berlabel "perkiraan" karena sebagian harga belum diverifikasi), rincian per agen (Mira < $0.01), per model, dan per hari, serta panel Biaya di samping chat. Tujuh tugas uji ini menambah sekitar $0.01 dari total.
- Perlu bantuan teknis: tidak; verifikasi harga model oleh tim AITopTrends agar label "perkiraan" hilang.

### 11. Tab Alat dan Hubungkan aplikasi (draft)
- Hasil: berhasil sebagai draft. Kartu Google Drive, Gmail, Notion berlabel "Draft" dan "Belum tersedia"; tombol Hubungkan menjelaskan "Belum bisa". Daftar alat tiap agen memakai nama Indonesia (Pencarian web, Membaca gambar, Ingatan, dst.).
- Perlu bantuan teknis: ya, sambungan akun (OAuth) belum dibuat.

## Pass bahasa (ringkas)
Satu kata satu konsep: agen (bukan bot), tugas (bukan run), alat (bukan toolset/Tools), jadwal (bukan Scheduler), biaya/batas, percakapan (bukan sesi), server/mesin agen (bukan BFF/Hermes/gateway), Layanan pelanggan (bukan CS), Evaluasi (menu dan judul sama), Anda (bukan kamu). "Token" dipertahankan dengan penjelasan satu kalimat di panel Biaya dan di Pengaturan > Paket dan pemakaian. Tidak ada yang dipindahkan: model dan tingkat berpikir ada di Ubah agen, sumber Knowledge Base di Pengaturan > Knowledge base dan lewat chat, jadwal di Kemampuan > Jadwal, sambungan aplikasi di Kemampuan > Hubungkan aplikasi.

## Sisa penghambat MVP
1. Pengguna tidak bisa menaikkan paket sendiri; paket Gratis (3 agen, 1 grup, 1 tugas bersamaan) menghalangi alur lima peran. Perlu keputusan produk (layar paket atau kontak).
2. Daftar model mentah (sekitar 40 nama teknis) tanpa saran; pembuatan agen lambat (sampai 40 detik).
3. Kartu rencana bergantung pada kepatuhan model terhadap format JSON; perlu uji ulang dengan beberapa model.
4. Layar Evaluasi memuat istilah uji tim (mis. TC-05, "simulasi") yang tidak cocok untuk pengguna akhir; sebaiknya disembunyikan dari pengguna biasa.
5. Notifikasi lain: judul lipatan berbahasa Inggris dari proses berpikir model, dan tombol "Arahkan sekarang"/"Antre" saat agen bekerja kurang jelas bagi pemula.

## Yang masih draft
Hubungkan aplikasi (Google Drive, Gmail, Notion): hanya rancangan tampilan. Computer Use: nonaktif, berisi contoh. Harga model berlabel "perkiraan" bila belum diverifikasi.

## Yang masih perlu uji dengan Hermes asli
- Unggah berkas lewat dialog sistem operasi (PDF, DOCX) dan Google Docs publik; hanya TXT dan satu link website yang diuji.
- Tombol Minta revisi pada kartu rencana, rencana lebih dari 2 hari, dan kejadian yang gagal atau dilewati karena batas biaya.
- Persetujuan tindakan agen ("Agen meminta izin") dan pertanyaan balik ("Agen bertanya") di UI.
- Grup lima anggota dengan diskusi berantai penuh (dihentikan sengaja untuk hemat biaya).
- Evaluasi/Uji dan Layanan pelanggan end to end; tidak dijalankan di sesi ini.
- Pilihan model selain bawaan.

## Lingkungan
Postgres di port 5433 sudah berjalan sebelum uji dimulai (milik sesi sebelumnya) dan dibiarkan menyala. Hermes, BFF, dan frontend dimulai dengan `start-dev.ps1` lalu dihentikan di akhir dengan `stop-dev.ps1`.
