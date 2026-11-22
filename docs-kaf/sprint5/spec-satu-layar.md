# Spec "satu layar" (Sprint 5, FE): Beranda, Chat, Detail pegawai

Untuk frontend-worker. Hanya `frontend/src`. Tidak menyentuh `bff/`, `data.tsx`, `bff.ts`, `App.tsx`, `router.ts`. Tidak ada cabang baru (tetap `feat/frontend-prototype`).
Dasar penilaian: rubrik Open Design (`purpose-hierarchy, typography, colour-contrast, layout-rhythm, copy, states, task, fit`) + craft product-ui, laws-of-ux, anti-ai-slop, state-coverage, action-states.
Kelanjutan dari `spec-ux-awam.md`. Semua keputusan di sana tetap berlaku (lihat bagian 6, "Tidak boleh mundur").

Diukur pada 22 Nov 2026, http://localhost:5173, akun admin@pegawai.ai, mode admin MATI (`pegawai-ai.admin-mode` tidak ada), Chromium headless. Skrol halaman terjadi di `.page` (Beranda, Detail) atau `.rail-body` (Chat), bukan di `document`; `document.scrollingElement.scrollHeight` selalu sama dengan tinggi viewport (800 / 812). Karena itu kolom "tinggi isi" di bawah adalah `scrollHeight` kontainer yang benar-benar menggulung. Tinggi yang dapat dipakai: 1280x800 = 800 px penuh; 375x812 = 760 px (bilah `.mbar` 52 px di atas).

Data uji: 10 pegawai (Marketing 8, Layanan pelanggan 2), 42 percakapan untuk Rian, 0 persetujuan menunggu, 0 jadwal, onboarding 2 dari 5 selesai, biaya `$0.89` tanpa batas.

## 1. Kritik per layar (rubrik)

Format: `verdict` + `findings` sesuai rubrik (maks 5, terpenting dulu). Bukti = tangkapan layar 1280x800 terang + gelap dan 375x812 terang (gelap hanya dicek untuk Beranda dan Chat 1280: kontras baik, tidak ada temuan warna).

### 1.1 Beranda (`Dashboard.tsx`, `Onboarding.tsx`, `TimAnda.tsx`, kartu biaya)

Tinggi isi `.page`: **1321 px @1280x800** (viewport 800), **1962 px @375x812** (viewport 760).

```json
{ "verdict": "polish", "findings": [
  { "area": "purpose-hierarchy", "where": "1280 dan 375, kartu Mulai dari sini",
    "problem": "Kartu onboarding 5 baris memakai 376 px (1280) / 514 px (375), dua langkah sudah dicoret, sehingga 'Perlu persetujuan Anda' baru mulai di y=502 (1280) dan y=732 (375), dan daftar pegawai di y=633 / y=978.",
    "fix": "Jadikan onboarding satu baris 'langkah berikutnya' (74 px 1280, ~122 px 375) dengan tombol 'Semua langkah' untuk membuka daftar penuh (bagian 3.1)." },
  { "area": "task", "where": "Pegawai AI Anda, 1280",
    "problem": "Daftar pegawai (510 px, 6 baris satu kolom, 3 baris isi per orang) hanya terlihat 1,5 baris di layar pertama; di 375 mulai di y=978 dan kartunya setinggi 838 px.",
    "fix": "Grid 2 kolom, baris 56 px (nama + status dalam satu baris kedua), 6 baris = 3 deret = 168 px; di 375 tampil 3 baris dahulu (bagian 3.3)." },
  { "area": "task", "where": "Biaya bulan ini, 1280 dan 375",
    "problem": "Kartu biaya ada di paling bawah (y=1166 di 1280, y=1832 di 375); 'cek biaya' butuh skrol dua layar di ponsel padahal isinya satu angka.",
    "fix": "Ubah menjadi statistik satu baris `.cost-compact` tepat di bawah dua kartu atas, dengan tautan 'Lihat rincian' ke #/pengaturan/paket (bagian 3.4)." },
  { "area": "layout-rhythm", "where": "375, kepala halaman",
    "problem": "Tombol 'Beri tugas ke tim' jatuh ke baris sendiri di bawah judul (kepala 146-186), memakan 70 px sebelum konten pertama.",
    "fix": "Kepala satu baris di ponsel: judul + subjudul di kiri, tombol 'Beri tugas' di kanan (bagian 3.5)." },
  { "area": "copy", "where": "kartu Perlu persetujuan / Berikutnya kosong, 375",
    "problem": "Dua kartu kosong masing-masing 107 px hanya untuk satu kalimat ('Tidak ada yang menunggu.'), ditumpuk di ponsel; jumlah persetujuan tidak tampil bila ada lebih dari satu.",
    "fix": "Kartu kosong dipadatkan (`data-empty`, ~84 px); judul 'Perlu persetujuan Anda' diberi pil jumlah bila > 0 (bagian 3.2)." }
] }
```

### 1.2 Chat (`ChatLayout.tsx` rail, `Chat.tsx`)

Tinggi isi: `.rail-body` **3098 px** dalam kotak 742 px @1280x800 (10 pegawai + 42 percakapan); `.rail-body` **3108 px** dalam 744 px @375 saat lembar Riwayat dibuka; `.with-rail` **845 px** dalam 760 px @375 pada `#/chat` (daftar). Area percakapan di 1280 tidak menggulung (komposer y=660-760).

```json
{ "verdict": "polish", "findings": [
  { "area": "task", "where": "rail kiri, 1280",
    "problem": "Daftar riwayat ('Riwayat Rian · 42') baru mulai di y=689 setelah 10 pegawai; hanya satu percakapan (y=725-782) terlihat, sisanya di bawah 800. Dengan pegawai ke-11 judul riwayat hilang dari layar pertama.",
    "fix": "Ganti dua daftar tertumpuk dengan 'pemilih pegawai' satu baris (56 px) + riwayat yang menempati sisa tinggi rail dan menggulung sendiri (bagian 4.1): 10 percakapan terlihat di 1280x800." },
  { "area": "task", "where": "lembar Riwayat, 375",
    "problem": "Setelah menekan 'Riwayat', lembar menampilkan 10 pegawai dulu; judul riwayat di y=699 dan baris pertama terpotong di tepi layar (y=765-812).",
    "fix": "Sama: pemilih satu baris di atas, riwayat langsung di bawahnya (judul y~135, 10+ baris terlihat)." },
  { "area": "layout-rhythm", "where": "kepala percakapan, 375",
    "problem": "Kepala `.convo-head` setinggi 160 px (tiga deret: Riwayat+judul; Atur pegawai+Topik baru; sakelar+Detail) sebelum pesan pertama; ruang pesan tinggal 488 px.",
    "fix": "Satu deret 56 px: Riwayat | judul | Topik baru | menu titik tiga berisi Atur pegawai, Detail, Tampilkan langkah kerja (bagian 4.3)." },
  { "area": "typography", "where": "kepala percakapan, 1280",
    "problem": "Judul pegawai dipotong ('Penulis naskah dan capti…') karena empat kontrol berbagi 720 px; status dan peran dua-duanya dituliskan.",
    "fix": "Tombol 'Atur pegawai' menjadi 'Atur' (sama dengan Beranda dan Detail), subjudul hanya peran (status sudah ada di rail dan titik status) (bagian 4.3)." },
  { "area": "copy", "where": "keadaan kosong percakapan, 1280",
    "problem": "'Topik baru' muncul dua kali sekaligus di layar (kepala 17-47 dan rail y=689), plus tautan 'Buka riwayat' yang hanya menggulung rail ke bawah.",
    "fix": "Pertahankan dua tombol 'Topik baru' (kepala = aksi utama, rail = bagian dari daftar), tetapi 'Buka riwayat' kini memfokuskan baris percakapan pertama (desktop) atau membuka lembar (ponsel)." }
] }
```

### 1.3 Detail pegawai (`Agents.tsx` `AgentDetail`, `#/agen/rian`)

Tinggi isi `.page`: **2360 px @1280x800** (viewport 800), **3615 px @375x812** (viewport 760). Posisi judul bagian di 1280: Identitas y=172, Bisa Anda ubah / Diatur sistem y=418, Tugas dan gaya bicara y=760, Keahlian pegawai y=998 (kartu setinggi 843 px), Tugas terakhir y=1840. Di 375: 285 / 636 / 939 / 1310 / 1564 / 2515.

```json
{ "verdict": "polish", "findings": [
  { "area": "task", "where": "1280 dan 375",
    "problem": "'Lihat pekerjaan terakhirnya' ada di y=1840 (1280) / y=2515 (375) dan 'lihat keahliannya' di y=998 / y=1564: keduanya jauh di bawah layar pertama dan tidak ada petunjuk bahwa bagian itu ada.",
    "fix": "Tiga tab 'Ringkasan / Pekerjaan / Keahlian' tepat di bawah kepala (y=147-191 di 1280; y=260-304 di 375) memakai `.tabs` yang sudah ada (bagian 5.1)." },
  { "area": "purpose-hierarchy", "where": "kartu Identitas, 1280",
    "problem": "Kartu Identitas (222 px) mengulang apa yang sudah ada di kepala (peran, tim, status) sehingga ringkasan izin baru mulai di y=393.",
    "fix": "Hapus baris Peran, Tim, Status, Jenis (Jenis sudah tertulis di kartu 'Diatur sistem'); sisakan 'Dibuat …' sebagai satu baris kecil (bagian 5.2)." },
  { "area": "layout-rhythm", "where": "ringkasan izin, 1280",
    "problem": "Dua kartu izin setinggi 318 px dengan dua baris tiap butir dan tombol Atur di dasar kartu; di 375 ditumpuk jadi 658 px.",
    "fix": "Butir satu baris (judul kiri, keterangan kanan) di desktop, tombol Atur ke baris judul kartu, kartu 'Diatur sistem' dilipat (`<details>`) di ponsel (bagian 5.2). Perkiraan 200-250 px." },
  { "area": "copy", "where": "kartu 'Tugas dan gaya bicara'",
    "problem": "Teks persona ditampilkan penuh (`white-space: pre-wrap`) dan bisa memanjang tanpa batas sehingga mendorong semua yang lain ke bawah.",
    "fix": "Potong 3 baris + tombol 'Baca selengkapnya' bila teks > 200 karakter (bagian 5.2)." },
  { "area": "states", "where": "tab Pekerjaan / Keahlian",
    "problem": "Pemakaian, keahlian, dan tugas terakhir dimuat dalam satu `extra` sehingga satu galat menyembunyikan ketiganya; keadaan kosong 'Belum ada tugas' tidak menawarkan langkah selanjutnya yang jelas.",
    "fix": "Galat dan loading per tab (bagian 5.4); kosong menawarkan tombol 'Ajak {nama} bicara'." }
] }
```

## 2. Jalan tugas (walk) sebelum perubahan

"Terlihat" = kontrol langkah berikutnya berada seluruhnya di dalam layar pertama tanpa skrol (1280x800: y<800; 375x812: y<812). Nilai = `top` elemen (px dari atas viewport).

| Layar | Tugas | Kontrol langkah berikutnya | 1280x800 | 375x812 | Catatan |
|---|---|---|---|---|---|
| Beranda | Lihat apa yang perlu saya setujui | judul 'Perlu persetujuan Anda' + isi kartu / tombol Tinjau | **PASS** (kartu y=502-609) | **FAIL** (kartu y=732-839; isi 'Tidak ada yang menunggu' di y~802, tombol Tinjau akan jatuh di bawah 812) | Di 1280 bila ada ActionCard ~180 px tetap terlihat sebagian. |
| Beranda | Lihat siapa pegawai saya dan apa yang dikerjakan | kartu 'Pegawai AI Anda' | **FAIL** (kartu y=633; hanya Mira penuh + separuh Rian; 8 pegawai lain di bawah) | **FAIL** (kartu y=978) | Tampil, tetapi tidak dapat dibaca sebagai daftar tanpa skrol. |
| Beranda | Beri tugas | 'Beri tugas ke tim' (primer, kanan atas) | **PASS** (y=42-78) | **PASS** (y=146-186) | Tombol paling menonjol di kedua ukuran. |
| Beranda | Cek biaya bulan ini | angka biaya | **FAIL** (kartu y=1166) | **FAIL** (kartu y=1832) | Butuh skrol 1,5 / 2,5 layar. |
| Chat | Ajak pegawai bicara | pegawai di rail + komposer | **PASS** (rail y=58+, komposer y=660-760) | **PASS** di `#/chat` (pegawai pertama y=301); **PASS** di percakapan (komposer y=700-800) | |
| Chat | Buka percakapan lama | judul riwayat + baris percakapan | **FAIL** (judul y=689, hanya 1 baris y=725-782; 41 lainnya tersembunyi) | **FAIL** (tombol 'Riwayat' terlihat y=60-100, tetapi isi lembar: judul y=699, baris pertama terpotong) | Di 1280 lulus hanya bila pegawai ≤ 9. |
| Chat | Mulai topik baru | 'Topik baru' | **PASS** (kepala y=17-47; rail y=689-719) | **PASS** (kepala deret ke-2, y=112-152) | Dua salinan di layar 1280. |
| Detail | Ubah pengaturan pegawai | 'Atur' | **PASS** (kepala y=87-123, primer kedua) | **PASS** (y=204-244) | |
| Detail | Lihat pekerjaan terakhirnya | tabel Tugas terakhir | **FAIL** (y=1840) | **FAIL** (y=2515) | Tidak ada tautan lompat. |
| Detail | Lihat keahliannya | kartu Keahlian pegawai | **FAIL** (y=998) | **FAIL** (y=1564) | |

Ringkas: di 1280x800 **5 lulus, 5 gagal** (lulus: Setujui, Beri tugas, Ajak bicara, Topik baru, Atur; gagal: Lihat pegawai, Cek biaya, Percakapan lama, Pekerjaan, Keahlian). Di 375x812 **4 lulus, 6 gagal** (lulus: Beri tugas, Ajak bicara, Topik baru, Atur). Target setelah perubahan: 10 dari 10 di 1280x800, dan di 375 semua kecuali 'Lihat siapa pegawai' yang lulus sebagian (pegawai pertama terlihat, sisanya lewat 'Lihat semua').

## 3. Beranda: perubahan

Urutan baru di `Dashboard.tsx`: `PageHead` → `Onboarding` (satu baris) → `.two` (Perlu persetujuan | Berikutnya) → kartu biaya kompak → `TimAnda`. (Biaya naik di atas pegawai: baris 64-92 px yang murah, supaya ia tetap di layar pertama di ponsel.) Blok admin di bawah tidak berubah.

### 3.1 Onboarding satu baris (`Onboarding.tsx`)

Default tertutup (ringkas); `Semua langkah` membuka daftar lama (`.onb-list`, markup langkah tidak berubah). Tombol X tetap menyimpan `pa.onboarding.closed`. State `open` hanya di komponen, tidak disimpan. Bila `left === 0` atau `closed` komponen tetap `null`.

```tsx
const [open, setOpen] = useState(false)
const done = steps.length - left
<section className="panel-card onboard onboard-row" aria-labelledby="onb-h">
  <div className="onb-bar">
    <span className="onb-ring num" aria-hidden="true">{done}/{steps.length}</span>
    <span className="onb-text">
      <h2 id="onb-h" className="onb-kicker">Mulai dari sini · {done} dari {steps.length} langkah selesai</h2>
      <b>{next.title}</b>
    </span>
    <span className="onb-ctrl">
      <a className="btn sm primary" href={next.href}>{next.action}</a>
      <button type="button" className="btn link small" aria-expanded={open} aria-controls="onb-list" onClick={() => setOpen((v) => !v)}>
        {open ? 'Sembunyikan langkah' : 'Semua langkah'}
      </button>
      <button className="icon-btn" aria-label="Tutup panduan awal" onClick={...existing...}><Icon d={CLOSE} size={16} /></button>
    </span>
  </div>
  {open && <ol id="onb-list" className="onb-list">{...existing li...}</ol>}
</section>
```

CSS (`pages.css`, ganti `.onb-head` yang tidak dipakai lagi; `.onb-list`, `.onb-step`, `.onb-mark`, `.onb-text small` tetap):

```css
.onboard-row { padding: var(--s-3) var(--s-4); gap: 0; }
.onb-bar { display: flex; align-items: center; gap: var(--s-3); min-height: 48px; }
.onb-ring { flex: none; display: grid; place-items: center; width: 40px; height: 40px; border: 2px solid var(--accent); border-radius: 50%; background: var(--accent-wash); color: var(--accent-ink); font-size: var(--t-small); font-weight: 600; }
.onb-bar .onb-text { flex: 1; min-width: 0; }
.onb-kicker { padding: 0; font-size: var(--t-small); font-weight: 500; color: var(--muted); }   /* menimpa .panel-card h2 */
.onb-bar .onb-text b { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--t-lead); font-weight: 600; }
.onb-ctrl { display: flex; align-items: center; gap: var(--s-3); flex: none; }
.onboard-row .onb-list { margin-top: var(--s-2); border-top: 1px solid var(--rule); }
@media (max-width: 640px) {
  .onb-bar { flex-wrap: wrap; row-gap: var(--s-2); }
  .onb-bar .onb-text b { white-space: normal; }
  .onb-ctrl { flex: 1 1 100%; justify-content: space-between; }
  .onb-ctrl .btn.primary { height: 40px; }
}
```
Warna: aksen dipakai hanya untuk kemajuan (arti), tombol primer tetap `.btn.primary` hitam. Tinggi: 12+48+12+2 = **74 px** desktop; ponsel ≈ 122 px (baris judul 48 + gap 8 + baris kontrol 40 + padding 24 + 2).
Loading: selama `!stepsReady` render pengisi `<div className="panel-card onboard-row onb-skel" aria-hidden="true" />` dengan `min-height: 74px` (hanya bila `pa.onboarding.closed` belum '1'; ekspor `export const onboardingClosed = () => read(CLOSED)`), supaya halaman tidak melompat.
Keadaan: error dari `work/kb/conn` tidak menghalangi (langkah dihitung belum selesai, perilaku lama). Fokus: tombol primer `focus-visible` bawaan `.btn`.

### 3.2 Persetujuan dan Berikutnya (`Dashboard.tsx`)

- Kartu kosong: tambah `data-empty={w && w.waiting.length === 0 && approvals.length === 0 ? '' : undefined}` pada kartu persetujuan, dan `data-empty={w && upcoming.length === 0 ? '' : undefined}` pada "Berikutnya". CSS:
```css
.panel-card[data-empty] { padding-bottom: var(--s-3); }
.panel-card[data-empty] .state-note { padding: var(--s-1) 0 var(--s-2); }
```
Tinggi kosong 107 → **~84 px**.
- Judul persetujuan: `<h2 id="need-h">Perlu persetujuan Anda{count > 0 && <span className="pill warn count-pill">{count}</span>}</h2>` dengan `count = approvals.length + (w?.waiting.length ?? 0)`; `.count-pill { margin-left: var(--s-2); vertical-align: middle; }`. Tombol `Tinjau` (`btn primary sm`) dan ActionCard tidak berubah.
- Batas daftar `.ledger` tetap `slice(0, 5)` dan "Dan N lainnya".
- Loading/error: tidak berubah (`Loading shape="ledger" rows={2}`, `ErrorLine` dengan "Coba lagi").

### 3.3 Pegawai AI Anda (`TimAnda.tsx`)

Perubahan DOM:
- Hapus `<p className="team-sub">`. Ganti dengan `<header className="team-head"><h2 id="team-h">Pegawai AI Anda</h2><span className="quiet small">{bots.length} pegawai · {working} sedang bekerja</span></header>` (`working = bots.filter(b => b.status !== 'idle').length`).
- `<ul className="ledger team-grid">`; kartu `<section className="panel-card team-card" data-collapsed={!showAll || undefined} ...>`.
- Baris `li.team-row`: avatar 36, `.ledger-main` dua baris saja: nama (tautan ke `#/agen/:id`, tetap) dan `<small className="team-status"><span className="status-dot" .../> <span className="team-status-text">{b.status === 'idle' && !b.deleteError ? `Siap · ${roleLabel(b.role)}` : statusText(b)}</span></small>`. Hapus `<small>{roleLabel}</small>` terpisah. `title` pada `.team-status-text` = teks penuh. Dua tombol `Ajak bicara` (`btn soft sm`) dan `Atur` (`btn outline sm`) tetap, `aria-label` tetap.
- Tombol `team-more`: render bila `sorted.length > 3`; atribut `data-few={sorted.length <= 6 || undefined}`. Label tetap `Lihat semua {N} pegawai` / `Tampilkan lebih sedikit`, `aria-expanded`.
- `shown = showAll ? sorted : sorted.slice(0, 6)` (tetap).

CSS (`pages.css`, ubah/tambah di blok `.team-*`):
```css
.team-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--s-3); padding-bottom: var(--s-2); }
.team-head h2 { padding-bottom: 0; }
.team-head .quiet { white-space: nowrap; }
.team-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: var(--s-5); }
.team-grid > li + li { border-top: 0; }                       /* matikan .ledger li + li */
.team-grid > li { border-top: 1px solid var(--rule); }
.team-grid > li:nth-child(-n+2) { border-top: 0; }
.team-row { min-height: 56px; padding: var(--s-2) 0; }
@media (max-width: 900px) {
  .team-grid { grid-template-columns: minmax(0, 1fr); }
  .team-grid > li:nth-child(2) { border-top: 1px solid var(--rule); }
}
@media (max-width: 640px) {
  .team-card[data-collapsed] .team-grid > li:nth-child(n+4) { display: none; }   /* ponsel: 3 pegawai dulu */
}
@media (min-width: 641px) { .team-more[data-few] { display: none; } }
```
Aturan `.team-sub` dan `.team-row .ledger-main small` (nowrap + ellipsis) tetap. Ukuran: kolom 480 px → teks ~262 px, cukup untuk "Siap · Penulis naskah dan caption" (~215 px). Tinggi kartu 1280: 16 + 32 + 168 + 48 + 8 = **~272 px** (sebelumnya 510). Ponsel: baris ~100 px (tanpa baris ketiga), 3 baris + judul + tombol 'Lihat semua 10 pegawai' ≈ 460 px (sebelumnya 838).
Keadaan: kosong (`Empty` 'Belum ada pegawai AI' + `Pegawai baru`) dan galat (kartu `null` bila `loadState==='error' && bots.length===0`) tidak berubah; tambahkan galat inline bila `loadState==='error'` tetapi ada data: tidak perlu.
Kontras: nama berwarna `color-mix(--bot 55%, --text)` tetap (sudah dicek di mode gelap, terbaca); status memakai `--muted`.

### 3.4 Biaya sebagai statistik kompak (`Dashboard.tsx`, `ui-extra.tsx` CostMeter tidak berubah)

```tsx
<section className="panel-card cost-card cost-compact" aria-labelledby="cost-h">
  <h2 id="cost-h">Biaya bulan ini</h2>
  {me ? <CostMeter u={me.usage} /> : <p className="quiet state-note">Belum terbaca.</p>}
  <a className="btn link small cost-more" href="#/pengaturan/paket">Lihat rincian</a>
  {admin && me && <p className="quiet small cost-admin">Pemakaian: <span className="num">{nf.format(me.usage.tokens_month)}</span> token</p>}
</section>
```
```css
.cost-compact { flex-direction: row; flex-wrap: wrap; align-items: center; gap: var(--s-2) var(--s-4); padding: var(--s-3) var(--s-4); }
.cost-compact h2 { padding: 0; flex: none; min-width: 112px; font-size: var(--t-body); font-weight: 500; color: var(--muted); }
.cost-compact .cost-meter { flex: 1; min-width: 0; }
.cost-compact .cost-spent { font-size: 20px; font-weight: 600; line-height: 1.2; }   /* sesudah aturan .cost-card .cost-spent */
.cost-compact .state-note { padding: 0; flex: 1; }
.cost-compact .cost-admin { flex: 1 1 100%; }
@media (max-width: 640px) {
  .cost-compact h2 { flex: 1; min-width: 0; }
  .cost-compact .cost-meter { order: 3; flex: 1 1 100%; }
  .cost-compact .cost-more { order: 2; }
}
```
Isi tidak berubah (`$0.89`, "bulan ini, tanpa batas biaya", pil "perkiraan"; bila ada batas: bilah `.set-meter` 6 px + pil Hampir habis/Terlampaui + kalimat sisa tetap tampil karena itu keadaan penting). Tinggi: 1280 **~64 px** (tanpa batas), ~84 bila ada batas; ponsel ~92 px.

### 3.5 Kepala halaman ponsel (`ui-extra.tsx` `PageHead`, `Dashboard.tsx`)

`PageHead` mendapat prop opsional `inline?: boolean` → `<header className={'page-head' + (inline ? ' head-inline' : '')}>`; Beranda memakai `inline`. Tombol: `<a className="btn primary" href={ask} aria-label="Beri tugas ke tim">Beri tugas<span className="hide-sm"> ke tim</span></a>`.
```css
.hide-sm { }
@media (max-width: 640px) {
  .page-head.head-inline { flex-wrap: nowrap; align-items: flex-start; gap: var(--s-3); }
  .head-inline .head-actions { flex: none; }
  .head-inline p { font-size: var(--t-small); }
  .hide-sm { display: none; }
}
```
Tinggi kepala ponsel ~52 px (sebelumnya 131 hingga ujung tombol).

### 3.6 Perkiraan setelah (Beranda)

Hitungan dari ukuran terukur (`[INFERENCE]`, belum dirender).

| Elemen | 1280x800 top-bottom | 375x812 top-bottom |
|---|---|---|
| Kepala + Beri tugas | 24-78 | 76-128 |
| Onboarding satu baris (+ tombol langkah berikutnya) | 102-176 | 152-274 |
| Persetujuan / Berikutnya (kosong) | 200-284 | 298-382 (+24) / 406-490 |
| Biaya kompak | 308-372 | 514-606 |
| Pegawai AI Anda | 396-668 (6 pegawai terlihat) | 630-~1090 (pegawai pertama y~680-780 terlihat penuh) |
| Tinggi isi `.page` | **~716 (padding bawah 48) < 800, tanpa skrol** | ~1250 (3 pegawai + tombol), skrol wajar |

Bila satu ActionCard (~190 px) menunggu: 1280 tetap muat (kartu pegawai berakhir ~774). Ponsel: persetujuan di y=298 (lulus), biaya y~620 (lulus), pegawai pertama terlihat (lulus).

## 4. Chat: perubahan

### 4.1 Rail: pemilih pegawai + riwayat (`ChatLayout.tsx`, `chat.css`)

State baru di `ChatLayout`: `const [whoOpen, setWhoOpen] = useState(false)`. Kontrak: saat `bot` ada, daftar pegawai tertutup dan diganti baris pemilih; saat `bot` tidak ada (ponsel `#/chat`) daftar tampil penuh seperti sekarang. `useEffect(() => { setOpen(false); setWhoOpen(false) }, [route])` (menggantikan baris `setOpen(false)`).

Struktur `Rail` children (di dalam `.rail-body`):
```tsx
{bot && (
  <section className="rail-who" aria-label="Pegawai yang sedang dibuka">
    <button type="button" className="who-btn" aria-expanded={whoOpen} aria-controls="who-list"
            style={{ ['--bot' as string]: botColor(bot) }} onClick={() => setWhoOpen((v) => !v)}>
      <BotAvatar bot={bot} size={32} />
      <span className="bot-text">
        <span className="bot-name"><b>{bot.name}</b></span>
        <small className="st">{roleLabel(bot.role)}</small>
      </span>
      <span className="who-change">{whoOpen ? 'Tutup' : 'Ganti pegawai'}</span>
      <Icon d={I.down} size={16} />
    </button>
  </section>
)}
<div id="who-list" className="who-list" hidden={!!bot && !whoOpen}>
  {...pesan loading/error/kosong + Object.entries(teams) tetap (kode lama tanpa perubahan)...}
</div>
{bot && <History bot={bot} hist={hist} sid={sid} />}
```
`I` diimpor dari `./ui` (sudah ada `I.down`). Memilih pegawai mengubah rute → daftar menutup sendiri. Tombol pemilih mengganti label menjadi "Tutup" saat terbuka; `Escape` menutup (`onKeyDown` pada `.rail-who`).

`History`: tidak berubah selain `id="chat-history"` tetap; judul 'Riwayat {nama} · N', tombol 'Topik baru', baris `SessionRow` (ganti nama, hapus) tetap. Loading `Memuat riwayat...`, galat `ErrorLine` + "Coba lagi", kosong `Belum ada percakapan dengan {nama}.` tetap.

`showHistory()` (dipakai 'Buka riwayat' di keadaan kosong `Chat.tsx`): ganti isi:
```ts
function showHistory() {
  setWhoOpen(false)
  setOpen(true)   // ponsel: buka lembar
  window.setTimeout(() => document.querySelector<HTMLElement>('#chat-history .sess-main')?.focus(), 50)
}
```
(`.sess-main` adalah tautan; bila bukan elemen fokus, beri `tabIndex={-1}` atau pakai `a` di dalamnya. Worker memeriksa markup `SessionRow`.)

CSS (`chat.css`, ubah `.rail-body` dan `.history`, tambah `who-*`):
```css
.rail-body { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; padding: 0 8px 8px; } /* sebelumnya overflow-y: auto */
.rail-who { flex: none; padding-bottom: var(--s-2); border-bottom: 1px solid var(--rule); }
.who-btn { display: flex; align-items: center; gap: var(--s-3); width: 100%; min-height: 56px; padding: var(--s-2); border: 1px solid var(--border); border-radius: var(--radius-control); background: var(--surface); color: inherit; font: inherit; text-align: left; cursor: pointer; transition: background-color var(--m-in) var(--ease); }
.who-btn:hover { background: var(--raised); }
.who-btn[aria-expanded="true"] { border-color: var(--control); }
.who-btn svg { flex: none; color: var(--muted); transition: transform var(--m-in) var(--ease); }
.who-btn[aria-expanded="true"] svg { transform: rotate(180deg); }
.who-change { flex: none; font-size: var(--t-small); font-weight: 500; color: var(--link); }
.who-list { flex: 0 1 auto; min-height: 0; max-height: min(50vh, 420px); overflow-y: auto; margin-top: var(--s-2); }
.who-list[hidden] { display: none; }
.rail-body > .history { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; margin-top: var(--s-3); }
.rail-body > .history > ul { flex: 1; min-height: 0; overflow-y: auto; }
@media (prefers-reduced-motion: reduce) { .who-btn, .who-btn svg { transition: none; } }
```
Di blok ≤900 px (ponsel, belum ada pegawai terpilih) tambahkan agar halaman daftar tetap bergulir seperti sekarang:
```css
.with-rail:not([data-picked]) .rail-body { display: block; overflow: visible; }
.with-rail:not([data-picked]) .who-list { max-height: none; overflow: visible; }
```
Fokus: `.who-btn` memakai `:focus-visible` global. Target sentuh ponsel: `min-height: 56px` (>44).

Perkiraan 1280x800 (pegawai terpilih, 42 percakapan): kepala rail 0-58; pemilih 58-123; judul riwayat + 'Topik baru' ~135-169; daftar percakapan mulai y=169 dan terlihat sampai y=792: **10 baris** (58 px). Pemilih terbuka (max-height 420): riwayat tersisa ~ 40 px + 2 baris, menggulung sendiri; tidak ada skrol rail keseluruhan.

### 4.2 Halaman `#/chat` ponsel (daftar)

Tidak berubah strukturnya (lulus: pegawai pertama y=301, 8 pegawai terlihat). Hanya `intro` dipadatkan: `.with-rail:not([data-picked]) .intro .empty p { font-size: var(--t-small); }` dan `.with-rail:not([data-picked]) .intro h1 { font-size: 20px; }` (~-20 px).

### 4.3 Kepala percakapan (`Chat.tsx`, `chat.css`)

Desktop (≥641 px) tetap semua kontrol, dengan dua perubahan: teks tombol `Atur pegawai` → `Atur`; subjudul `{roleLabel(bot.role)}` saja (status keluar dari subjudul; `statusText` tetap muncul di tooltip `title` pada `.convo-title p` dan di rail). Admin tetap menambah ` · {model}`.

Ponsel (≤640 px): satu deret 56 px. Tambahkan menu titik tiga dan sembunyikan kontrol panjang:
```tsx
<header className="convo-head" ...>
  <button className="btn soft sm rail-open" onClick={onRail}>Riwayat</button>
  <BotAvatar bot={bot} size={36} />
  <div className="convo-title">...</div>
  <span className="convo-extras">  {/* desktop saja */}
    <button className="btn soft sm" onClick={() => setDialog({ kind: 'edit', bot })}>Atur</button>
  </span>
  <button className="btn soft sm convo-new" ...>Topik baru</button>
  <span className="convo-extras">
    <button className="switch" role="switch" aria-checked={showThink} onClick={toggleThink}><span className="knob" aria-hidden="true" />Tampilkan langkah kerja</button>
    <PanelButtons />
  </span>
  <span className="convo-more">  {/* ponsel saja */}
    <button className="icon-btn" aria-label={`Menu ${bot.name}`} aria-expanded={more} onClick={(e) => { e.stopPropagation(); setMore((v) => !v) }}><Icon d={DOTS} /></button>
    {more && (
      <div className="popmenu" role="menu">
        <button role="menuitem" onClick={() => { setMore(false); setDialog({ kind: 'edit', bot }) }}><Icon d={PENCIL} />Atur pegawai</button>
        <button role="menuitem" aria-checked={showThink} onClick={toggleThink}>Tampilkan langkah kerja{showThink ? ': nyala' : ': mati'}</button>
        <PanelButtons />
      </div>
    )}
  </span>
</header>
```
`more` ditutup lewat `document.addEventListener('click')` seperti `menu` di `ChatLayout`.
```css
.convo-more { display: none; position: relative; }
@media (max-width: 640px) {
  .convo-head { flex-wrap: nowrap; gap: var(--s-2); min-height: 56px; padding-block: var(--s-2); }
  .convo-head .bot-avatar { display: none; }               /* nama cukup; ruang untuk judul */
  .convo-title { flex: 1 1 0; min-width: 0; }
  .convo-extras { display: none; }
  .convo-more { display: block; }
  .convo-more .popmenu { right: 0; min-width: 220px; }
}
```
Tinggi kepala ponsel 160 → **56 px**; area pesan 488 → ~592 px. 'Topik baru' (90 px) dan 'Riwayat' (73 px) tetap terlihat di deret itu; judul memperoleh ~104 px (nama utuh, peran dipotong dengan ellipsis).

Perkiraan Chat:

| Tugas | 1280x800 | 375x812 |
|---|---|---|
| Ajak bicara | rail pemilih y=58, komposer y=660 | `#/chat` pegawai y~280; percakapan komposer y=700 |
| Buka percakapan lama | 10 baris riwayat y=169-792 | tombol Riwayat y=60-100; di lembar: judul y~135, 10+ baris |
| Topik baru | kepala y=17-47 + rail y=135 | kepala deret tunggal y=60-100 |
| Skrol rail | tidak ada (riwayat menggulung sendiri) | lembar tidak menggulung kecuali riwayat |

## 5. Detail pegawai: tab (`Agents.tsx` `AgentDetail`)

### 5.1 Tab

```tsx
const TABS = [['ringkasan', 'Ringkasan'], ['pekerjaan', 'Pekerjaan'], ['keahlian', 'Keahlian']] as const
type TabId = (typeof TABS)[number][0]
const [tab, setTab] = useState<TabId>(() => {
  const t = new URLSearchParams(location.hash.split('?')[1] ?? '').get('tab')
  return TABS.some(([id]) => id === t) ? (t as TabId) : 'ringkasan'
})
function onKey(e: React.KeyboardEvent) {     // panah kiri/kanan, Home, End (salin pola Platform.tsx:265-275)
  ...
}
```
Pasang di bawah `<header className="page-head">`, menggantikan kartu-kartu lama:
```tsx
<div className="tabs" role="tablist" aria-label="Bagian detail pegawai" onKeyDown={onKey}>
  {TABS.map(([id, label]) => (
    <button key={id} id={'tab-' + id} type="button" role="tab" aria-selected={tab === id} aria-controls={'panel-' + id} tabIndex={tab === id ? 0 : -1} onClick={() => setTab(id)}>{label}</button>
  ))}
</div>
<div id={'panel-' + tab} role="tabpanel" aria-labelledby={'tab-' + tab} className="tab-body">...</div>
```
Gaya memakai `.tabs` / `.tab-body` di `pages.css:95-102` apa adanya (tinggi tab 44 px, garis bawah hitam untuk tab terpilih, 640 px: padding 12). Tanpa perubahan router: `?tab=` hanya dibaca saat mount (tidak ditulis); `#/agen/rian?tab=keahlian` tetap menuju `agen-detail` karena router memotong `?` (`router.ts:28`). Kepala halaman (avatar, nama, `peran · tim · status`, `Ajak bicara`, `Atur`, `Hapus`) tetap di atas tab sehingga tombol tidak ikut berpindah.

### 5.2 Tab Ringkasan (default)

Urutan: (a) KPI, (b) `.two.perm-block` ringkasan izin, (c) kartu "Tugas dan gaya bicara" (dipotong), (d) baris `Dibuat …`, (e) admin: kartu `Identitas` lama hanya berisi baris admin (`Warna`, `Model`, `Tingkat berpikir`) + tautan 'Pengaturan lanjutan' (tetap `admin &&`).

- **Hapus** kartu "Identitas" untuk non-admin (peran/tim/status sudah di kepala; `Jenis` sudah ada di "Diatur sistem" untuk bawaan dan "Dibuat oleh Anda" ditambahkan sebagai butir pertama kartu "Bisa Anda ubah" untuk non-bawaan: `<li><b>Jenis</b><small>Dibuat oleh Anda</small></li>`).
- Baris kecil di akhir tab: `<p className="quiet small">Dibuat {stamp(b.createdAt)}</p>` (hanya bila `b.createdAt`).
- **KPI**: `dl.kpis k2` (admin `k4`) seperti sekarang, dengan `extra.state` per bagian: `Loading shape="ledger" rows={1}` bila memuat; `ErrorLine` + 'Coba lagi' bila galat (hanya mengganti KPI, tidak menghilangkan ringkasan izin).
- **Ringkasan izin**: DOM sekarang dipertahankan, dengan perubahan:
  - Judul kartu "Bisa Anda ubah" menjadi `<header className="perm-head"><h2 id="perm-edit-h">Bisa Anda ubah</h2><button className="btn soft sm" onClick={...edit}>Atur</button></header>`; tombol `Atur` di dasar kartu dihapus; kalimat "Perubahan berlaku mulai tugas berikutnya." tetap di bawah daftar.
  - `.perm-list li` di desktop jadi satu baris: 
  ```css
  .perm-head { display: flex; align-items: center; justify-content: space-between; gap: var(--s-3); }
  .perm-head h2 { padding-bottom: 0; }
  @media (min-width: 901px) {
    .perm-list li { flex-direction: row; align-items: baseline; justify-content: space-between; gap: var(--s-4); }
    .perm-list small { text-align: right; max-width: 62%; }
  }
  ```
  - Kartu "Diatur sistem" menjadi `<details className="cbox perm-locked" open={wide}><summary><h2 id="perm-locked-h"><Icon d={LOCK} size={16} /> Diatur sistem</h2></summary>...</details>` dengan `const [wide] = useState(() => window.matchMedia('(min-width: 901px)').matches)`; di ponsel tertutup (hemat ~280 px), di desktop terbuka. `summary { cursor: pointer; list-style: none; }` + `.perm-locked > summary::-webkit-details-marker { display: none }`; tambah chevron `Icon d={I.down}` di kanan summary (memutar saat `[open]`). Tautan 'Lihat batasan keamanan' tetap di dalam.
- **Persona**: `<p className={'persona' + (long && !all ? ' persona-clamp' : '')}>` dengan `long = (b.persona ?? '').length > 200`, `const [all, setAll] = useState(false)`; tombol `<button className="btn link small" aria-expanded={all} onClick={() => setAll(v => !v)}>{all ? 'Tampilkan lebih sedikit' : 'Baca selengkapnya'}</button>` hanya bila `long`. 
  ```css
  .persona-clamp { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  ```
  Kosong: teks lama ('Dikelola sistem.' / 'Belum ada petunjuk tugas. Klik Atur untuk menulisnya.') tetap.

Perkiraan 1280x800, Ringkasan: kepala 69-123; tab 147-191; KPI 215-303; ringkasan izin 327-~560; persona 584-~700; `Dibuat` ~724-745; tinggi isi ~790 (≤ viewport + padding). Semua tugas Detail ada di atas y=560. Ponsel: kepala 113-244; tab 260-304; KPI 328-426; 'Bisa Anda ubah' + Atur 450-~700; 'Diatur sistem' hanya satu baris ringkas ~56 px.

### 5.3 Tab Pekerjaan

```tsx
{tab === 'pekerjaan' && (
  extra.state === 'loading' ? <Loading text="Memuat pekerjaan..." shape="table" /> :
  extra.state === 'error' ? <ErrorLine text={extra.error} onRetry={extra.retry} /> :
  <div className="block">
    <header><h2>Tugas terakhir</h2></header>
    {runs.length === 0 ? <Empty title="Belum ada tugas"><a className="btn primary" href={'#' + botPath(b.id)}>Ajak {b.name} bicara</a></Empty> : ...tabel lama tanpa perubahan...}
  </div>
)}
```
Tabel 8 baris (434 px) selesai sebelum y=700 di 1280. Ponsel memakai kartu per baris (aturan `.act` lama / tabel yang ada); tidak diubah.

### 5.4 Tab Keahlian

`<div className="cbox"><h2>Keahlian pegawai</h2><AgentSkills slug={id} /></div>` (komponen sudah punya loading `Memuat keahlian...` dan galat 'Daftar keahlian belum bisa dimuat. Coba lagi sebentar.' + 'Coba lagi'). Agar seluruh daftar muat di 1280x800 (kartu sekarang 843 px):
```css
@media (min-width: 901px) {
  .skill-sw .skill-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: var(--s-6); }
  .skill-sw .skill-list li:nth-last-child(-n+2):nth-child(odd), .skill-sw .skill-list li:last-child { border-bottom: 0; }
}
```
Perkiraan tinggi kartu ~ 450-480 px. Catatan skrol `.skill-note` (Ingatan dimatikan) tetap di dalam `li`.
Tab di ponsel tetap satu kolom.

### 5.5 Perkiraan Detail

| Tugas | Sebelum 1280 / 375 | Sesudah 1280 / 375 |
|---|---|---|
| Ubah pengaturan | y=87 / 204 (lulus) | y=87 / 204 + tombol Atur di kartu izin y~395 / ~455 |
| Lihat pekerjaan terakhirnya | y=1840 / 2515 | tab 'Pekerjaan' y=147-191 / 260-304 (1 klik, isi mulai y=215 / 328) |
| Lihat keahliannya | y=998 / 1564 | tab 'Keahlian' y=147-191 / 260-304 |
| Tinggi isi `.page` | 2360 / 3615 | Ringkasan ~790 / ~1150; Pekerjaan ~700 / ~1500 (tabel kartu); Keahlian ~700 / ~1600 |

## 6. Tidak boleh mundur (keputusan awam sebelumnya yang dipertahankan)

Kartu 'Mulai dari sini' dan isi langkahnya; 'Perlu persetujuan Anda' dengan ActionCard; 'Pegawai AI Anda' dengan `Ajak bicara` + `Atur` per pegawai, urutan bekerja-dulu; nama menaut ke detail `#/agen/:id` (bukan halaman admin); 'Kontak utama' di rail; 'Atur' membuka `EditBotDialog`; 'Topik baru'; 'Tampilkan langkah kerja' (teks penuh tetap di menu ponsel dan kepala desktop); `roleLabel` untuk semua peran; kosakata 'pegawai' dan 'Tingkat ketelitian'; ringkasan 'Bisa Anda ubah' / 'Diatur sistem' + tautan 'Lihat batasan keamanan'; tautan kembali 'Beranda' (non-admin) / 'Semua agen' (admin); token hanya mode admin (baris token di biaya tetap `admin &&`); biaya tetap dalam dolar sesuai label BFF; galat 'Coba lagi'; blok admin di Beranda dan 'Pengaturan lanjutan' di Detail.

## 7. Berkas yang disentuh worker

| Berkas | Perubahan |
|---|---|
| `frontend/src/Onboarding.tsx` | Baris ringkas + `open`, ekspor `onboardingClosed` (3.1) |
| `frontend/src/Dashboard.tsx` | Urutan, `PageHead inline`, tombol 'Beri tugas', `data-empty`, pil jumlah, biaya kompak, placeholder onboarding (3.1-3.5) |
| `frontend/src/TimAnda.tsx` | Header, grid, baris dua-garis, tombol `team-more` (3.3) |
| `frontend/src/ui-extra.tsx` | Prop `inline` pada `PageHead` saja |
| `frontend/src/pages.css` | `.onboard-row/.onb-*`, `.team-*`, `.cost-compact`, `.head-inline`, `.hide-sm`, `.count-pill`, `.perm-head`, `.persona-clamp`, aturan `.skill-sw` |
| `frontend/src/ChatLayout.tsx` | `whoOpen`, pemilih pegawai, `showHistory` (4.1) |
| `frontend/src/Chat.tsx` | Kepala percakapan: `Atur`, subjudul peran, `convo-extras`, `convo-more` + state `more` (4.3) |
| `frontend/src/chat.css` | `.rail-body`, `.rail-who`, `.who-*`, `.history` dalam rail, `.convo-more`, aturan ≤640 (4.1-4.3) |
| `frontend/src/Agents.tsx` | Tab, ringkasan izin, persona terpotong, tab Pekerjaan/Keahlian (bagian 5); `AgentList`/`AgentEdit` tidak diubah |

Tidak menyentuh `skills-ui.tsx`, `Panel.tsx`, `router.ts`, `data.tsx`, BFF.

## 8. Cara memverifikasi (untuk Main)

Login admin@pegawai.ai, mode admin mati (`localStorage` tanpa `pegawai-ai.admin-mode`). Emulasi 1280x800 dan 375x812 (DPR 2, mobile), terang lalu `document.documentElement.dataset.theme='dark'`. Ukur skrol dari kontainer yang menggulung:

```js
[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 2 && ['auto','scroll'].includes(getComputedStyle(e).overflowY)).map(e => ({ c: e.className, sh: e.scrollHeight, ch: e.clientHeight }))
```
Kriteria lulus @1280x800 (`#/`, `#/chat/rian`, `#/agen/rian`):
1. Beranda: `.page` `scrollHeight` ≤ 800 (dengan ≤ 6 pegawai terlihat); 'Perlu persetujuan', daftar pegawai (y_bawah < 800), biaya (y_bawah < 800), 'Beri tugas ke tim' semua di layar pertama.
2. Chat: `.rail-body` tidak menggulung (`scrollHeight` = `clientHeight`); `#chat-history` top < 200; ≥ 8 baris `.sess` di dalam y<800.
3. Detail: tab 'Pekerjaan' dan 'Keahlian' top < 200; 'Atur' top < 130.
Kriteria @375x812: kepala Beranda satu deret (tinggi < 60); 'Perlu persetujuan' top < 320; biaya top < 650; pegawai pertama top < 720; Chat percakapan `.convo-head` tinggi ≤ 60; Detail tab top < 320.
Cek juga: fokus keyboard pada `.who-btn`, tab Detail (panah kiri/kanan), `Semua langkah`; tidak ada teks terpotong pada nama pegawai; uji pegawai 0, 1, 11; uji `loadState` memuat dan galat; contoh persona > 200 karakter; kontras gelap pada `.onb-ring` dan `.who-btn`.
