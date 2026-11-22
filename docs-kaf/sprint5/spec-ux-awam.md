# Spec UX untuk pengguna awam (Sprint 5, FE) — Pegawai AI

Dokumen untuk frontend-worker. Hanya `frontend/src` + docs. Tidak menyentuh `bff/`, `LoginModal.tsx`, `data.tsx`, `bff.ts`, `App.tsx` (lihat bagian "Butuh App.tsx").
Nomor baris mengacu ke kondisi kode saat audit (branch `feat/frontend-prototype`, 22 Nov 2026). Cek ulang nomor baris bila file sudah berubah.

## 0. Yang diperiksa

Aplikasi berjalan di http://localhost:5173, login akun pemilik agen (admin@pegawai.ai, id `default`), mode admin nyala dan mati.

| Layar | Ukuran | Hasil lihat |
|---|---|---|
| Beranda | 1280 terang, 1280 gelap, 375 terang | Kartu "Mulai dari sini", "Perlu persetujuan Anda", "Berikutnya", "Biaya bulan ini". Tidak ada daftar pegawai. Di mode gelap kotak akun di sidebar tetap putih (warna inline). |
| Chat | 375 | Daftar "Agen" per tim, tombol "Agen baru", menu titik tiga berisi "Atur agen". Peran tampil bahasa Inggris ("Project Manager", "Creative Director & QC Auditor"). |
| Tim (grup) | teks | Daftar tim, ada tim bernama "Tim Marketing Uji" (data uji). |
| Jadwal & tugas | teks | Empat kolom Antre/Dikerjakan/Perlu Anda/Selesai, isinya tugas uji ("Balas dua kata: ini tes"). |
| Pengetahuan | teks | "Sumber milik Anda", berkas tersimpan, "Dokumen bawaan". |
| Aplikasi | teks | Sudah baik: status "Tersambung", "Hubungkan", tab "Keahlian agen". |
| Pengaturan | 1280 + teks | Umum, Notifikasi, Keamanan (tembok label per agen), Pengetahuan (hanya tautan), Paket dan biaya, Data. |
| Detail pegawai `#/agen/rian` | 1280 | Kartu "Identitas" menumpuk label di atas nilai (bug CSS `.kv`), tampil Model `deepseek-v4.1-flash`, "Tingkat berpikir", warna "amber", "Persona", KPI "(token)". |
| Admin: Agen, Kemampuan, Aktivitas, Evaluasi, Layanan pelanggan, Marketing | teks | Bahasa teknis masih wajar untuk admin. Temuan hanya yang bocor ke pengguna awam atau salah data (bagian 1, P3). |
| Panggilan API | `GET /api/bots`, `/api/agents/rian/skills`, `/api/activity` | Peran bahasa Inggris dari server. Skill `memory` dan `session_search` tidak ditandai `technical`, jadi tampil ke semua pengguna. Aktivitas membawa nama alat mentah (`mcp__pegawai__kb_add_note`, `tool_call`, `manage_connections`). |

Prinsip yang dipertahankan (jangan diubah): kartu Mulai dari sini, "Perlu persetujuan Anda" dengan ActionCard, halaman Aplikasi, Pengetahuan (satu tugas per layar), pesan galat "Coba lagi", kolom Kanban dengan teks kosong yang jelas, "Topik baru", "Tampilkan langkah kerja", modal "Hubungkan {app}", token disembunyikan kecuali mode admin.

## 1. Temuan berprioritas

P1 = harus dikerjakan sprint ini (Day 2 dan Day 4, atau jargon di layar utama). P2 = sebaiknya sprint ini. P3 = catatan, boleh ditunda.

### 1a. P1

| # | file:baris | Teks / perilaku sekarang | Teks / perilaku baru |
|---|---|---|---|
| 1 | `Dashboard.tsx:169` (setelah `</div>` penutup `.two`) | Beranda tidak menampilkan pegawai. | Sisipkan kartu `TimAnda` (bagian 2.1). |
| 2 | `Agents.tsx:147-149` | Tombol `Ubah` (outline) membuka halaman teknis `#/agen/:id/ubah` (dropdown model, tingkat berpikir). | Ganti menjadi `<button className="btn outline" onClick={() => setDialog({ kind: 'edit', bot: b })}>Atur</button>`. Untuk admin tambahkan di bawah blok izin (2.2) tautan kecil `Pengaturan lanjutan` ke `agenPath(b.id,'ubah')`. |
| 3 | `Agents.tsx:158-179` (kartu Identitas) | Baris `Warna` menulis `amber`; `Model` menulis `Bawaan (deepseek-v4.1-flash)`; `Tingkat berpikir`; `Jenis`. | Pengguna awam: baris `Peran` (pakai `roleLabel`), `Tim`, `Status` (`statusText(b)`), `Warna` (swatch + `colorLabel`), `Dibuat`, `Jenis` = `Pegawai bawaan, tidak bisa dihapus` / `Dibuat oleh Anda`. Baris `Model` dan `Tingkat berpikir` hanya `admin`. Judul kartu tetap `Identitas`. Pindahkan ke class baru `kv-wide` (temuan 20). |
| 4 | `Agents.tsx:190-207` | KPI `Pemakaian bulan ini (token)`, `Pemakaian total (token)`, `Tugas total`. | Pengguna awam: dua KPI saja, `Percakapan` dan `Tugas dikerjakan` (ganti dari `Tugas total`), grid `kpis k2`. Dua KPI token hanya `admin` (grid tetap `k4`). |
| 5 | `Agents.tsx:181-184` (kartu `Persona`) | Judul `Persona`, kosong: `Belum ada persona.` | Judul `Tugas dan gaya bicara`; kosong: `Belum ada petunjuk tugas. Klik Atur untuk menulisnya.` (custom) / `Dikelola sistem.` (builtin). Isi tetap `b.persona`. |
| 6 | `Agents.tsx:179` (sisipkan blok baru sesudah kartu Identitas) | Tidak ada penjelasan apa yang boleh diubah. | Blok `Bisa Anda ubah` / `Diatur sistem` (bagian 2.2). |
| 7 | `Agents.tsx:117-118` dan `:130-132` (tautan `.back` "Semua agen") | Selalu ke `#/agen`, halaman daftar admin. | Pengguna awam: `<a className="back" href="#/">Beranda</a>`; admin tetap `#/agen` `Semua agen`. |
| 8 | `Agents.tsx:266` (`AgentEdit`) | Halaman teknis bisa dibuka lewat URL oleh siapa saja. | Bila `!admin`: `useEffect(() => { go(agenPath(id), true); setDialog({ kind: 'edit', bot }) })` lalu render `null`. Jangan menampilkan dropdown model untuk non-admin (keputusan di 2.3). |
| 9 | `ui-extra.tsx:80` (`memory`) | `['Ingatan', 'Mengingat hal penting antar percakapan.']` | `['Ingatan', 'Mengizinkan pegawai mengingat hal penting antar percakapan. Saklar ini hanya menyalakan atau mematikan kemampuan itu; yang sudah diingat tidak dihapus.']`. Teks ini dipakai sekaligus di detail pegawai, tab Keahlian agen (`skills-ui.tsx:96`), dan Kemampuan. |
| 10 | `skills-ui.tsx:45` (dalam `SkillSwitches`, setelah `<label className="skill-row">`) | Mematikan Ingatan tanpa umpan balik. | Bila `s.name === 'memory' && !s.enabled`, render di bawah baris `<p className="quiet small skill-note">Ingatan dimatikan. Hal yang sudah diingat tetap tersimpan.</p>`. Di dialog `SkillsSection` (`skills-ui.tsx:112`) tambahkan kalimat yang sama bila `current.name === 'memory'`. |
| 11 | `ChatLayout.tsx:377` (konfirmasi hapus sesi) | `Hapus “{title}”?` dengan tombol `Hapus`. | `<span>Hapus percakapan “{title}”? Hanya percakapan ini yang dihapus. Dokumen di Pengetahuan dan pengaturan pegawai tidak berubah.</span>`; tombol `Hapus percakapan` (`:386`) dan `Batal`. `aria-label` tombol sampah (`:412`): `Hapus percakapan ${title}`. |
| 12 | `Dialogs.tsx:396` (hapus pegawai) | `… Riwayat chat dengan {bot.name} tidak bisa dibuka lagi. Agen yang sedang bekerja tidak bisa dihapus.` | `{bot.name} dihapus dari daftar pegawai dan dari semua tim. Semua percakapan dengan {bot.name} ikut hilang. Dokumen di Pengetahuan tidak terhapus. Pegawai yang sedang bekerja tidak bisa dihapus; tunggu sampai selesai.` |
| 13 | `kb-ui.tsx:140` (`aria-label="Knowledge Base"`), `:160` (`Simpan ke Knowledge Base`), `:176` dan `:179` (`Knowledge Base: …`), komentar `:9` | Istilah Inggris "Knowledge Base" padahal halamannya bernama Pengetahuan. | Ganti semua menjadi `Pengetahuan`. `:160` → `Simpan ke Pengetahuan`. `:176` → `Pengetahuan: membaca link…`. `:179` ready → `Disimpan ke Pengetahuan: {i.name}. Ini dokumen yang bisa dibaca semua pegawai, bukan ingatan percakapan.` plus `<a className="btn link" href="#/pengetahuan">Lihat</a>`. failed → `Pengetahuan: gagal menyimpan {source}. {error}`. |
| 14 | `kb-ui.tsx:17` (`INTENT_RE`) | Kata `ingat*`, `hafal*`, `memorize`, `remember` membuat link otomatis disimpan sebagai dokumen. "Ingat link ini" lalu tersimpan ke Pengetahuan tanpa tanya. | Perilaku sebenarnya diputuskan BFF (`bff/kb.py`, milik Faiz). Di FE jangan ubah regex sendiri (tampilan "memproses" jadi tidak sinkron). Lakukan temuan 13 (jujur memberi tahu hasilnya) dan catat ketergantungan BE di bagian 5. Setelah BE menghapus kata itu, hapus `ingat\w*\|hafal\w*\|memorize\|remember` dari regex FE di commit yang sama. |
| 15 | `Pengetahuan.tsx:82` | `Semua agen Anda memakai berkas dan link ini, dan menyebut sumbernya.` | `Semua pegawai AI Anda membaca berkas dan link ini, dan menyebut sumbernya. Ini bukan ingatan percakapan: yang di sini hanya yang Anda unggah atau simpan.` |
| 16 | `steps.ts:31-50` (`LABELS`) dan `:51` | Nama alat mentah jatuh ke bentuk "Mcp  pegawai  kb add note", "Tool call", "Manage connections". Tampil di Chat (langkah kerja), Panel Aktivitas, Beranda admin. | Di awal `toolLabel` buang awalan: `const t = tool.replace(/^mcp__[a-z0-9]+__/i, '')`. Tambahkan pola (sebelum pola umum) lalu uji pada `t`: `kb_add_note` → `Menyimpan catatan ke Pengetahuan`; `kb_` lain → `Membaca Pengetahuan`; `task_complete` → `Menyelesaikan tugas`; `task_cancel` → `Membatalkan tugas`; `task_list` → `Melihat daftar tugas`; `task_ask_user` → `Bertanya kepada Anda`; `gmail_search` → `Mencari email`; `gmail_create_draft` → `Membuat draf email`; `gmail_send` → `Mengirim email`; `drive_search` → `Mencari di Drive`; `drive_read` → `Membaca berkas Drive`; `drive_create` → `Membuat berkas Drive`; `ping` → `Memeriksa sambungan`; `tool_describe` → `Membaca petunjuk alat`; `tool_search` → `Mencari alat`; `tool_call` → `Memakai alat`; `manage_connections` → `Mengatur aplikasi tersambung`. Ubah pola `^memory` dari `Membuka ingatan` menjadi `Memakai ingatan`. |
| 17 | `ui.tsx:31-32` (tambah di bawah `teamLabel`) | Peran dari server bahasa Inggris (Copywriting Specialist, dll.). | Tambah `export const roleLabel(role)` memakai peta di 2.1; sisanya tampil apa adanya. Dipakai di kartu Tim Anda, detail pegawai, `ChatLayout.tsx:150` dan `title` `:145`, `Chat.tsx:359` dan `:352`, `Panel.tsx:352`, `Dialogs.tsx:270`, `Dialogs.tsx:160`. Pencarian di `Agents.tsx:17` tetap memakai peran asli dan label baru sekaligus. `isLead` di `ChatLayout.tsx:25` tetap memeriksa peran asli. |
| 18 | `Dialogs.tsx:476` | `Agen bawaan: nama dan tugasnya diatur sistem. Anda bisa memilih model AI-nya.` | `Pegawai bawaan: nama dan tugasnya diatur sistem. Anda bisa mengubah warna dan tingkat ketelitiannya.` |
| 19 | `Dialogs.tsx:484, 495-496, 500-501, 517` (EditBotDialog) | `Tugas agen ini`, `Model AI`, `Ikuti bawaan` + `Memakai pilihan standar sistem.`, `Perubahan berlaku di tugas berikutnya.` | `Tugas dan gaya bicara` (`:484`); `aria-label` dan label `Tingkat ketelitian` (`:495-496`); `Ikuti bawaan` tetap, hint `Memakai pilihan standar sistem.`; `:517` → `Perubahan berlaku mulai tugas berikutnya. Percakapan lama tidak berubah.` Tambahkan pemilih warna (bagian 2.2). Nama model hanya untuk admin (sudah benar di `:501`, `:511`). |

### 1b. P2

| # | file:baris | Sekarang | Baru |
|---|---|---|---|
| 20 | `pages.css:53-57` vs `panel.css:63-65` | Dua aturan `.kv`. `panel.css` (flex kolom, anak `> div`) menang, jadi `dl.kv` di `Agents.tsx:160` dan `Settings.tsx:325` menumpuk dt di atas dd. | Tambah class `kv-wide` di `pages.css` (`display:grid; grid-template-columns:160px minmax(0,1fr); gap:8px 16px`, di bawah 640 px satu kolom, `dd{margin-bottom:8px}`). Pakai di `Agents.tsx:160` dan `Settings.tsx:325`. `.kv` panel tidak diubah. |
| 21 | `Dashboard.tsx:101` | Tombol `Minta tim Anda`; bentrok dengan kartu baru `Tim Anda` (pegawai). Tombol membuka tim pertama, bukan "semua pegawai". | `Beri tugas ke tim`. Langkah onboarding `:69` `Minta tim`/`Minta Tim Marketing menyusun rencana.` → `Beri tugas`/`Beri tugas ke tim Marketing: minta rencana konten.` (aksi `:69` dan `:70` memakai `ask`). |
| 22 | `ChatLayout.tsx:205-211` | `Tanya satu agen secara langsung. Untuk pekerjaan besar, mulai dari Tim.` lalu `Mulai dari Tim, lalu pilih agen dari daftar bila perlu.` (saling bertentangan). | text: `Ajak satu pegawai bicara langsung. Untuk pekerjaan yang butuh beberapa pegawai sekaligus, buka Tim.` Baris kedua: `<a className="empty-link" href="#/grup">Buka Tim</a>` + ` atau pilih pegawai dari daftar.` |
| 23 | `ChatLayout.tsx:275` | `Beberapa agen bekerja sama dalam satu percakapan. Pilih tim dari daftar.` | `Beberapa pegawai AI bekerja sama dalam satu percakapan. Pilih tim dari daftar, atau buat tim baru.` |
| 24 | `ChatLayout.tsx:247` | `Belum ada tim. Gabungkan 2 sampai 6 agen lewat Tim baru.` | `Belum ada tim. Tim berisi 2 sampai 6 pegawai yang mengerjakan satu tugas bersama. Klik Tim baru.` |
| 25 | `ChatLayout.tsx:126-138, 177-182`, `Chat.tsx:364`, `Dialogs.tsx:139, 404` | Kata "agen" di judul daftar, tombol, dialog. | Terapkan kosakata di 1c. Contoh: rail judul `Pegawai AI`, `Agen baru` → `Pegawai baru`, `Atur agen` → `Atur pegawai` (Chat.tsx:364, ChatLayout.tsx:177), `Hapus agen` → `Hapus pegawai`, dialog `Agen baru` → `Pegawai baru`. |
| 26 | `Dialogs.tsx:105, 180-181` (BotDialog) | Label `Persona`, galat `Persona wajib diisi, supaya agen tahu cara bekerja.`, placeholder `Jelaskan cara agen bekerja, gaya bahasanya, dan batasannya.` | Label `Tugas dan gaya bicara`; galat `Tulis tugas pegawai ini, supaya ia tahu cara bekerja.`; placeholder `Contoh: Kamu admin toko online saya. Jawab pelanggan dengan sopan dan singkat.` Di `Dialogs.tsx:175` `aria-label={`Warna ${c}`}` → `Warna ${colorLabel(c)}`. |
| 27 | `Agents.tsx:259-262, 366, 370` (AgentEdit, admin) | `Persona wajib diisi.`, `Persona`. | Boleh tetap karena admin. Bila memakai kosakata baru, samakan: `Tugas dan gaya bicara`. |
| 28 | `Settings.tsx:195, 203-228` (Keamanan) | Judul tabel `Pembatasan ini dipasang tim AITopTrends di tiap agen.` lalu tujuh label yang sama berulang per agen (tembok 10 baris). | Satu kalimat: `Demi keamanan, kemampuan di bawah ini dimatikan untuk semua pegawai, dan tindakan berisiko seperti menghapus berkas atau mengirim email selalu menunggu izin Anda.` Jika semua baris `b.denied` identik tampilkan satu baris `Semua pegawai` (label sekali) dan `Manual: perlu izin Anda`; baris per pegawai hanya bila berbeda. Kolom `Kemampuan yang dimatikan` → `Dimatikan`. |
| 29 | `Settings.tsx:340-347` | Dt `Agen`, `Tim`, `Tugas sekaligus`. | `Pegawai`, `Tim`, `Tugas berjalan bersamaan`. |
| 30 | `Settings.tsx:354` | `Dihitung dari pemakaian agen bulan ini.` | `Dihitung dari pekerjaan pegawai AI bulan ini.` |
| 31 | `composerKeys.ts:4-5`, `Group.tsx:427` | `Agen langsung membaca pesan ini di tengah pekerjaannya.` / `Agen sedang bekerja. Pesan Anda akan dikirim setelah selesai.` | `Pegawai langsung membaca pesan ini sambil bekerja.` / `Pegawai sedang bekerja. Pesan Anda dikirim setelah selesai.` |
| 32 | `Group.tsx:488` | `Menunggu giliran, dikirim setelah ronde selesai` | `Menunggu giliran, dikirim setelah semua anggota selesai menjawab` |
| 33 | `Kanban.tsx:236-237, 407, 419-421` | `Pilih agen atau tim`, `Beri tugas ke agen Anda…`, filter `Agen`/`Semua agen`. | `Pilih pegawai atau tim`, `Beri tugas ke pegawai AI Anda dan pantau sampai selesai.`, filter `Pegawai`/`Semua pegawai`. |
| 34 | `Activity.tsx:71, 75-77, 102, 112` (halaman admin, juga dipakai panel Aktivitas non-admin) | `Apa yang dikerjakan agen`, kolom `Agen`. | `Apa yang dikerjakan pegawai AI, dari yang terbaru.`, `Pegawai`, `Semua pegawai`; kosong: `Saat pegawai bekerja, catatannya muncul di sini.` |
| 35 | `Dashboard.tsx:67` | `Unggah berkas atau link agar agen mengenal bisnis Anda.` | `Unggah berkas atau link agar pegawai AI mengenal bisnis Anda.` |
| 36 | `Dashboard.tsx:66` / `Onboarding.tsx:27` | Langkah `Isi nama bisnis` tetap belum selesai padahal sidebar sudah tertulis "Colorbox" (nama bawaan dihitung belum diisi). Pengguna melihat nama itu sudah ada. | Hint: `Sekarang menampilkan "Colorbox". Ganti dengan nama bisnis Anda.` bila nama masih bawaan, selain itu hint lama. Tombol `Isi nama` → `Ganti nama`. |
| 37 | `Agents.tsx:46`, `ChatLayout.tsx:138` | `Belum ada agen. Buat agen pertama lewat tombol Agen baru.` / `Belum ada agen.` | `Belum ada pegawai AI. Klik Pegawai baru untuk membuat yang pertama.` |
| 38 | `Settings.tsx:17`, `:242-251` | Bagian `Pengetahuan` di Pengaturan hanya tombol ke halaman lain (jalan buntu satu klik). | Hapus bagian `knowledge` dari `SECTIONS` dan `KnowledgeLink`; arahkan `#/pengaturan/knowledge` ke `Umum`. Pengetahuan sudah ada di sidebar. (Bila ingin tetap, kalimat: `Berkas dan link kini ada di halaman Pengetahuan.`.) |

### 1c. Kosakata yang disarankan (satu keputusan)

Istilah "agen" tersebar di ratusan string dan merupakan jargon bagi pemilik usaha. Produk bernama Pegawai AI. Keputusan: untuk teks yang dilihat pengguna awam, "agen" menjadi "pegawai" (judul, tombol, kalimat). Jangan mengubah id, nama field API, route (`#/agen`), nama komponen, atau teks halaman admin (Agen, Kemampuan, Evaluasi). Daftar tabel 1b #25-#35 adalah cakupan sprint ini; sisanya bisa menyusul.

| Konsep | Dipakai untuk pengguna awam | Hindari |
|---|---|---|
| orang AI | pegawai AI / pegawai | agen, bot |
| kelompok | Tim (2-6 pegawai, satu percakapan) | grup |
| `bot.team` (Marketing, Layanan pelanggan) | divisi | tim (bentrok dengan Tim di sidebar). Teks `teamLabel` tetap, label kolom `Tim` di tabel menjadi `Divisi` bila pindah. |
| `persona` | Tugas dan gaya bicara | persona, SOUL, prompt |
| `model` | Tingkat ketelitian (Hemat & cepat, Seimbang, Paling teliti) | model, model AI, provider |
| `session` | percakapan / topik | sesi |
| `toolset` | keahlian / kemampuan | alat, toolset, MCP |
| token | tidak ditampilkan (biaya saja) | token (kecuali mode admin) |

### 1d. P3

| # | file:baris | Catatan |
|---|---|---|
| 39 | `Dashboard.tsx:91` | Baris admin `Scheduler` bertuliskan `Aktif · Colorbox 5-Agent Automation` tetap (hardcode, bukan status nyata). Ganti `detail` menjadi `Tugas berulang ada di Jadwal & tugas` atau hapus baris. |
| 40 | `Dashboard.tsx:86` | `Agen` / `Daftar, buat, ubah, hapus` (admin). Biarkan. |
| 41 | `Dashboard.tsx:171-173`, seluruh `CostMeter` | Biaya tampil dalam dolar (`$0.89`). Pemilik usaha Indonesia lebih paham rupiah. Keputusan produk, label berasal dari BFF (`cost.label`); catat sebagai ketergantungan BE bila ingin rupiah. |
| 42 | `Marketing.tsx:174-180`, `Platform.tsx:191-217` | Admin: nama pegawai tetap `Bimo, Meda, Raka, Bram, Vina` sedangkan pegawai nyata (Mira, Rian, Diana, ...). Salah data untuk QA, bukan jargon. Catat, jangan diubah sprint ini. |
| 43 | `Platform.tsx:58` | `Tidak ada data toolset yang bisa ditampilkan.` → `Tidak ada data kemampuan yang bisa ditampilkan.` |
| 44 | `Activity.tsx` kolom Ringkasan | Pratinjau dari mesin berbahasa Inggris (`Reading tool details · 1 tool`). Hanya BE yang bisa menerjemahkan; catat di bagian 5. |
| 45 | `Uji.tsx:22`, `:657-667`, `Compare.tsx:81-85` | Admin: `Rute`, `Hash persona`, `Versi mesin agen`. Biarkan (QA). |
| 46 | `CS.tsx:223-224`, `ResultCards.tsx:211, 254` | `Intent dan prioritas`, `Rekomendasi eskalasi`. Tampil pada halaman admin; bila nanti dibuka untuk staf CS: `Maksud pelanggan dan prioritas`, `Perlu diteruskan ke atasan?`. |
| 47 | `Panel.tsx:238` | `Diingat ulang` (admin). Biarkan. |

## 2. Komponen baru dan perubahan Day 2

### 2.1 Kartu `Tim Anda` di Beranda

File baru: `frontend/src/TimAnda.tsx` (komponen `TimAnda`), dipasang di `Dashboard.tsx` setelah `.two` (setelah baris 169, sebelum `.cost-card` di baris 171). Alasan posisi: Beranda menjawab "apa yang perlu saya lakukan hari ini". Persetujuan dan jadwal harus di atas, daftar pegawai adalah referensi.

Data: `const { bots, setDialog } = useData()`. Tanpa panggilan API baru.

Urutan: `status !== 'idle'` dulu (sedang bekerja di atas), lalu kontak utama (`/project manager/i`, sama seperti `isLead`), lalu urutan asli. Tampilkan 6 baris; bila lebih, tombol teks di bawah daftar `Lihat semua {N} pegawai` (`btn link`, toggle `showAll`, `aria-expanded`) yang membuka sisanya di tempat. Jangan menautkan ke `#/agen` (halaman admin).

Struktur DOM (pakai class yang sudah ada):

```
<section className="panel-card team-card" aria-labelledby="team-h">
  <h2 id="team-h">Tim Anda</h2>
  <p className="quiet small team-sub">Pegawai AI yang bekerja untuk bisnis Anda.</p>
  <ul className="ledger">
    <li className="team-row" style={{'--bot': botColor(b)}}>
      <BotAvatar bot={b} size={36} />
      <span className="ledger-main">
        <a className="team-name" href={'#' + agenPath(b.id)}><b>{b.name}</b></a>
        <small>{roleLabel(b.role)}</small>
        <small className="team-status"><span className="status-dot" data-s={b.status} role="img" aria-label={...} /> {statusText(b)}</small>
      </span>
      <span className="team-actions">
        <a className="btn soft sm" href={'#' + botPath(b.id)} aria-label={`Ajak ${b.name} bicara`}>Ajak bicara</a>
        <button type="button" className="btn quiet-btn sm" aria-label={`Atur ${b.name}`} onClick={() => setDialog({ kind: 'edit', bot: b })}>Atur</button>
      </span>
    </li>
  </ul>
</section>
```

Isi baris:
- Avatar: `BotAvatar` 36 px, warna dari `--bot`.
- Nama: `b.name`, `.ledger-main b` (500) berwarna `color-mix(in srgb, var(--bot) 55%, var(--text))` seperti `.bot-text b` (`chat.css:49`). Nama menjadi tautan ke detail `#/agen/:id`; teks tautan tidak bergaris bawah (`text-decoration:none`), hover garis bawah.
- Baris kedua: `roleLabel(b.role)` (peta di bawah), `small`, `var(--muted)`.
- Baris ketiga: status. Titik `.status-dot` (8 px, `data-s`) lalu `statusText(b)`: `Siap` / `Sedang bekerja: …` / `Berdiskusi di grup: …`. `aria-label` titik: `Siap` / `Bekerja` / `Berdiskusi` (sama seperti `ChatLayout.tsx:152`). Teks status dipotong 1 baris (`text-overflow: ellipsis`); `Gagal dihapus…` dari `deleteError` tampil via `statusText`.
- `Ajak bicara`: `btn soft sm` ke `#/chat/{id}` (`botPath`). `Atur`: `btn quiet-btn sm`, membuka `EditBotDialog` lewat `setDialog({ kind: 'edit', bot: b })` (sama seperti `Chat.tsx:363`).

Peta peran (`roleLabel`, `ui.tsx`): hanya untuk tampilan, kunci cocok persis dengan `role` dari server; tidak ketemu = tampil apa adanya.

| Peran dari server | Tampil |
|---|---|
| Project Manager | Pengatur tugas tim |
| Copywriting Specialist | Penulis naskah dan caption |
| Creative Director & QC Auditor | Penilai mutu konten |
| Visual Designer & Art Director | Perancang visual |
| Visual Designer | Perancang visual |
| Strategist | Penyusun strategi |
| Researcher | Peneliti produk dan pasar |
| Writer | Penulis |
| Frontline Support Specialist | Penjawab pelanggan |
| CS Team Lead & Quality Auditor | Ketua layanan pelanggan |

Peta warna (`colorLabel`, `ui.tsx`): amber `Jingga`, teal `Hijau toska`, indigo `Nila`, sky `Biru langit`, rose `Merah muda`, green `Hijau`, red `Merah`, slate `Abu-abu`, `plain` `Netral`. Hex lain: `Warna khusus`.

Keadaan:
- Kosong (`bots.length === 0`, `loadState === 'ok'`): di dalam kartu, `<Empty title="Belum ada pegawai AI">Buat pegawai pertama Anda untuk mulai mendelegasikan pekerjaan.</Empty>` dengan tombol `<a className="btn primary" href="#/agen/baru">Pegawai baru</a>`.
- Memuat: Dashboard sudah menahan seluruh halaman selama `loadState === 'loading'` (`Dashboard.tsx:57`); tidak perlu loader kartu.
- Galat: ditangani Dashboard (`:58`, `ErrorLine` dengan `Coba lagi`). Bila `bots` kosong tetapi `loadState === 'error'` jangan tampil kartu.
- Gagal menyimpan di dialog: ditangani `EditBotDialog` (`problem-bar`). Setelah simpan, `refreshBots()` sudah dipanggil, kartu ikut berubah.
- Pegawai sedang bekerja: titik berdenyut (animasi `pulse` yang sudah ada), tidak menonaktifkan tombol.

Layout desktop (≥ 901 px, lebar kartu penuh seperti `.cost-card`, tanpa grid ganda):
- Kartu `panel-card` (padding `16px 24px 8px`), judul `h2` 16 px/600 (aturan `.panel-card h2`), sub `13px` `var(--muted)`, jarak judul ke sub 0, sub ke daftar 8 px.
- Baris `team-row`: grid tiga kolom `grid-template-columns: 36px minmax(0,1fr) auto`, `column-gap: 12px`, `align-items: center`, `min-height: 64px`, `padding: 8px 0`. Pemisah `border-top: 1px solid var(--rule)` antar baris (aturan `.ledger li + li` sudah ada).
- `team-actions`: `display:flex; gap:8px`. Tombol 28 px tinggi (`.btn.sm`).
- Batas 6 baris ≈ 6 × 64 = 384 px; `Lihat semua` memakai `.ledger-more` (48 px).

Layout 375 px (≤ 640 px):
- `team-row` menjadi dua baris: `grid-template-columns: 36px minmax(0,1fr)`, `grid-template-areas: "av main" "act act"`, `row-gap: 8px`, `padding: 12px 0`.
- `team-actions` menempati `act`: `display:grid; grid-template-columns: 1fr 1fr; gap:8px`; tombol tinggi 40 px (override `.team-row .btn.sm {height:40px}` di media query) supaya mudah disentuh. `Ajak bicara` kiri (soft), `Atur` kanan (`btn outline sm` di mobile agar terlihat sebagai tombol).
- Teks peran dan status satu baris dengan ellipsis; kartu tidak boleh melebihi lebar (semua anak `min-width:0`).
- Padding kartu mengikuti `.panel-card` (tidak ada override).

Mode gelap: hanya token (`--surface`, `--border`, `--rule`, `--muted`, `--st-*`, `--c-*`, `--raised`, `--active`). Dilarang warna heks langsung. Avatar memakai `color-mix` dari `--bot` (sudah mengikuti tema). Fokus: `:focus-visible` global (2 px `--accent`).

CSS: tambahkan ± 25 baris di `pages.css` (blok `.team-*`); tidak membuat file CSS baru.

Aksesibilitas: setiap tombol punya `aria-label` bernama pegawai; daftar `ul` dengan `li`; urutan Tab: nama, Ajak bicara, Atur; titik status memakai `role="img"` + `aria-label`, bukan hanya warna (teks status juga ada).

### 2.2 Detail pegawai (`AgentDetail`) dan blok "Bisa Anda ubah / Diatur sistem"

Header (`Agents.tsx:133-156`):
- Tombol: `Chat` (primary) → ganti teks `Ajak bicara`; `Atur` (outline, membuka `EditBotDialog`); `Hapus` (danger, bila `!b.builtin`) tidak berubah.
- Baris sub (`:138-140`): `{roleLabel(b.role)} · {teamLabel(b.team)} · {statusText(b)}`.

Blok baru, sisipkan setelah kartu Identitas (`Agents.tsx:179`), sebelum `Persona`:

```
<div className="two perm-block">
  <section className="cbox perm-edit" aria-labelledby="perm-edit-h">
    <h2 id="perm-edit-h">Bisa Anda ubah</h2>
    <ul className="perm-list">  // 3-4 <li>: <b>judul</b> <small className="quiet">nilai saat ini / penjelasan</small>
    <button className="btn soft" onClick={() => setDialog({ kind: 'edit', bot: b })}>Atur</button>
  </section>
  <section className="cbox perm-locked" aria-labelledby="perm-locked-h">
    <h2 id="perm-locked-h">Diatur sistem</h2>
    <ul className="perm-list"> ... </ul>
    <a className="btn link" href="#/pengaturan/keamanan">Lihat batasan keamanan</a>
  </section>
</div>
```

Isi diturunkan dari `b.builtin`:

| Baris | `builtin === false` (dibuat pengguna) | `builtin === true` (bawaan) |
|---|---|---|
| Bisa Anda ubah | `Nama` — nilai `b.name` | (tidak ada; pindah ke Diatur sistem) |
| | `Tugas dan gaya bicara` — `Petunjuk yang mengatur cara {nama} bekerja` | (pindah) |
| | `Warna` — `colorLabel(b.color)` + swatch | `Warna` — sama |
| | `Tingkat ketelitian` — `TIERS.find(t=>t.id===tierOf(b.model))?.label` bila `b.model`, selain itu `Ikuti bawaan` | sama |
| Diatur sistem | `Aturan inti` — `Cara dasar {nama} bekerja dan menjaga data bisnis Anda.` | sama |
| | `Izin keamanan` — `Tindakan berisiko, misalnya menghapus berkas atau mengirim email, selalu menunggu izin Anda.` | sama |
| | (tidak ada) | `Nama dan tugas` — `Pegawai bawaan: dikelola tim AITopTrends.` |

Kalimat penutup kartu kiri (kecil, `quiet small`): `Perubahan berlaku mulai tugas berikutnya.` Kartu kanan berikon gembok `Icon` kecil (path sederhana boleh ditambah di `ui.tsx` sebagai `LOCK`) di sebelah `h2`, `aria-hidden`.

Layout desktop: `.two` (dua kolom sama lebar, gap 16 px), tiap kartu `.cbox` (padding 24, gap 8). `perm-list li`: `display:flex; flex-direction:column; padding: 8px 0; border-top: 1px solid var(--rule)` (baris pertama tanpa garis). Tombol `Atur` di bawah daftar kiri, `margin-top: 8px; align-self:flex-start`.

Layout 375 px: `.two` sudah satu kolom di bawah 900 px (`pages.css:73`); kartu bertumpuk, "Bisa Anda ubah" di atas, "Diatur sistem" di bawah; tombol `Atur` lebar penuh (`width:100%`, tinggi 44 px) di bawah 640 px.

Gelap: token saja; kartu kanan memakai `background: var(--raised)` supaya terbaca "terkunci" dibanding kartu kiri `--surface`.

Perubahan EditBotDialog (`Dialogs.tsx:413-532`):
- Tambah pemilih warna sebelum "Tingkat ketelitian", untuk custom dan builtin: `<div className="field"><span id="ec-l">Warna</span><div className="swatches" role="radiogroup" aria-labelledby="ec-l">` memakai `COLORS` dan `swatch` (sama persis seperti `BotDialog:171-178`), state `color` awal `bot.color || 'plain'`. Kirim `patch.color = color` bila berubah (BFF sudah menerima untuk builtin, lihat `AgentEdit` `Agents.tsx:303`). `aria-label` swatch memakai `colorLabel`.
- Kata-kata sesuai #18, #19. Radio `Ikuti bawaan` dan tiga tingkat tetap; tidak menambah dropdown model.
- Setelah simpan: `flash('{nama} disimpan')`. Ganti `Dialogs.tsx:461` `Agen ${…} disimpan` → `${name.trim()} disimpan`.

### 2.3 Keputusan: halaman Agen untuk non-admin

Rekomendasi: ya, tapi hanya detail. Alasan: kartu Tim Anda butuh tujuan untuk "lihat pegawai ini" tanpa menambah item sidebar.
- Terbuka untuk semua: `#/agen/:id` (`AgentDetail`), melalui nama di kartu Tim Anda. Konten pengguna awam diatur di 1a #3-#7.
- Tetap khusus admin: `#/agen` (daftar), `#/agen/baru` boleh dibuka lewat tombol `Pegawai baru`/rail (tetap dialog), `#/agen/:id/ubah` (`AgentEdit`) dialihkan ke dialog `EditBotDialog` untuk non-admin (1a #8). Dropdown model teknis tidak pernah tampil ke non-admin.
- Tidak perlu perubahan `App.tsx`: rute sudah dirender tanpa cek admin (`App.tsx:97-100`); sidebar item `Agen` tetap di grup Admin.

## 3. Salinan Day 4 (W7), ringkasan

| Topik | Perubahan | Rujukan |
|---|---|---|
| Ingatan | Saklar hanya menyalakan/mematikan kemampuan; yang sudah diingat tidak dihapus. | 1a #9, #10 |
| Pengetahuan ≠ ingatan | Halaman dan baris status KB menyebut "dokumen, bukan ingatan percakapan"; istilah "Knowledge Base" diganti Pengetahuan. | 1a #13, #15 |
| `ingat/hafal` memicu simpan dokumen | FE jujur memberi tahu hasil; perbaikan perilaku di BFF. | 1a #14, bagian 5 |
| Hapus sesi | Teks menyebut hanya percakapan itu yang dihapus. | 1a #11 |
| Hapus pegawai | Menyebut Pengetahuan tidak ikut terhapus. | 1a #12 |

## 4. Pedoman visual (ringkas)

- Pakai kelas yang sudah ada: `panel-card` (kartu Beranda), `cbox` (kartu detail), `ledger`/`ledger-row`/`ledger-main`/`ledger-more` (baris daftar), `two` (dua kolom), `btn soft|outline|quiet-btn|link|primary` dengan `.sm`, `pill`, `status-dot`, `swatch(es)`, `empty-box` lewat `Empty`, `problem-bar`, `note-box`, `quiet`, `small`.
- Token: jarak `--s-1…--s-7` (4/8/12/16/24/32/48), radius `--radius-card` 8, `--radius-control` 6, ukuran huruf 13/14/16/24, warna `--surface/--raised/--border/--rule/--muted/--accent/--st-*/--c-*`. Tidak ada gradasi, bayangan, atau warna heks baru. Font DM Sans.
- Breakpoint yang sudah dipakai: 900 px (`.two` jadi satu kolom, rail jadi sheet), 640 px (tabel jadi kartu, `kpis` satu kolom, dialog layar penuh). Jangan menambah breakpoint baru.
- Target sentuh di 375 px: tombol baru minimal 40 px tinggi (override lokal); tombol utama di kartu detail 44 px.
- Gerak: hanya animasi yang sudah ada (`pulse` titik status, `rise`); hormati `prefers-reduced-motion` (sudah global).
- Mode gelap: semua warna lewat token; periksa dengan `document.documentElement.dataset.theme='dark'`.
- Fokus: `:focus-visible` global; tombol ikon punya `aria-label`.
- Layar baru jangan menambah item sidebar; Beranda tetap satu halaman.

Kriteria penerimaan visual:
1. Beranda 1280: kartu Tim Anda tampil di bawah dua kartu persetujuan/jadwal, lebar sama dengan kartu Biaya, baris sejajar, tidak ada baris lebih dari 64 px kecuali `Lihat semua`.
2. Beranda 375: tiap pegawai dua baris (identitas, lalu dua tombol sama lebar 40 px); tidak ada scroll horizontal; teks peran terpotong dengan ellipsis.
3. Gelap: tidak ada permukaan putih di kartu Tim Anda; titik status dan pil terbaca.
4. Detail pegawai: label di kiri dan nilai di kanan (1280), dua kartu Bisa Anda ubah / Diatur sistem berdampingan (1280) dan bertumpuk (375).
5. Pengguna non-admin tidak melihat kata `token`, `model`, nama model (`deepseek-…`), `Persona`, `amber`, atau `Tingkat berpikir` di Beranda, detail pegawai, Chat, dan dialog Atur.

## 5. Butuh App.tsx (diterapkan setelah tugas auth/sesi selesai)

| # | file:baris | Sekarang | Baru |
|---|---|---|---|
| A1 | `App.tsx:217-231` | Kotak akun di sidebar memakai style inline warna tetap (`#f1f5f9`, `#0f172a`, `#e2e8f0`, `#fecaca`, `#b91c1c`); di mode gelap tetap putih terang (terlihat di audit). | Pindah ke class (mis. `.side-user`) di CSS dengan token `--raised`, `--text`, `--muted`, `--border`, `--bad-ink`. Tombol `Keluar` `btn quiet-btn sm danger-text`. |
| A2 | `App.tsx:221` | `{authUser.role.toUpperCase()} • {authUser.company}` → `ADMIN • Colorbox`. | `Pemilik` bila role `owner`/`admin`, `Staf` untuk lainnya, lalu ` · {company}`. Nama peran ditampilkan dalam huruf biasa. |
| A3 | `App.tsx:172-174` | Item `Tim` bentrok dengan kartu `Tim Anda` (pegawai) dan kolom "Tim" Kanban. | Label `Tim` → `Kerja tim` (ikon sama). Teks Chat/Intro dan `GroupLayout` memakai `Tim` sebagai nama fitur; bila A3 diterapkan ubah `ChatLayout.tsx:205, 275` supaya konsisten (`buka Kerja tim`). Jika tidak ingin mengubah sidebar, biarkan `Tim` dan jangan tambah A3. |
| A4 | `App.tsx:113` | `Mau diberi tahu saat agen selesai, walau tab ini tidak dibuka?` | `Mau diberi tahu saat pegawai selesai bekerja, walau tab ini tidak dibuka?` |
| A5 | `App.tsx:194-211` (grup Admin) | `Marketing (formulir)`, `Evaluasi`, `Agen` | Boleh tetap; ini halaman admin. Tidak perlu perubahan. |
| A6 | `App.tsx:316` dan komponen `RunsPill` | `Layanan pelanggan`, `Evaluasi` pada kartu pekerjaan berjalan | Bahasa sudah jelas; tidak perlu perubahan. |

Ketergantungan backend (catat, tidak dikerjakan di sini):
1. `bff/kb.py` `INTENT_RE`: keluarkan `ingat*`, `hafal*`, `memorize`, `remember` atau minta konfirmasi sebelum menyimpan link sebagai dokumen. FE menyamakan regex setelahnya.
2. `Activity` ringkasan berbahasa Inggris dari mesin (`Reading tool details · 1 tool`).
3. Biaya dalam rupiah bila diinginkan (`cost.label`).
4. Opsional: `GET /bots/{id}/config` untuk blok Diatur sistem yang membaca nilai nyata (sekarang teks tetap dari `builtin`).
5. Ingatan: isolasi per pengguna (catatan Day 4: memori profil belum per-user). Teks FE tidak menjanjikan isolasi.

## 6. File yang disentuh worker

| File | Perubahan |
|---|---|
| `frontend/src/TimAnda.tsx` | Baru: kartu Tim Anda (2.1). |
| `frontend/src/Dashboard.tsx` | Pasang `<TimAnda />` (setelah baris 169); teks #21, #35, #36, #39. |
| `frontend/src/Agents.tsx` | Detail: tombol Atur, identitas ramah awam, blok izin, KPI, tautan kembali, `kv-wide`; `AgentEdit` dialihkan untuk non-admin; teks #5, #37. |
| `frontend/src/Dialogs.tsx` | EditBotDialog: pemilih warna, teks #18, #19, #26; hapus pegawai #12; `colorLabel`/`roleLabel`. |
| `frontend/src/ui.tsx` | `roleLabel`, `colorLabel`, ikon `LOCK`. |
| `frontend/src/ui-extra.tsx` | Teks `memory` (#9). |
| `frontend/src/skills-ui.tsx` | Catatan Ingatan (#10). |
| `frontend/src/steps.ts` | `toolLabel` (#16). |
| `frontend/src/kb-ui.tsx` | Teks Pengetahuan (#13); regex (#14) mengikuti BE. |
| `frontend/src/Pengetahuan.tsx` | Teks #15. |
| `frontend/src/ChatLayout.tsx` | Konfirmasi hapus percakapan (#11), Intro (#22-#24), kosakata (#25), `roleLabel`. |
| `frontend/src/Chat.tsx`, `Panel.tsx`, `Group.tsx`, `composerKeys.ts` | `roleLabel`, kosakata, teks #31, #32. |
| `frontend/src/Settings.tsx` | Keamanan (#28), paket (#29, #30), bagian Pengetahuan (#38), `kv-wide`. |
| `frontend/src/Kanban.tsx`, `Activity.tsx`, `Platform.tsx` | Kosakata dan teks #33, #34, #43. |
| `frontend/src/pages.css` | `.team-*`, `.perm-*`, `.kv-wide`, `.kpis.k2`, aturan 375 px. |
| `frontend/src/App.tsx` | Hanya setelah tugas lain selesai: A1-A4 (bagian 5). |

Verifikasi akhir: `cd frontend && npm run build`; cek manual Beranda, detail pegawai, dialog Atur, hapus percakapan, saklar Ingatan di 1280 dan 375, terang dan gelap, mode admin mati dan nyala.
