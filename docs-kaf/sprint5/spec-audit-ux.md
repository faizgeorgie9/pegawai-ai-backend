# Audit UX frontend Pegawai AI dan spesifikasi perbaikan

Tanggal audit: 25 Nov 2026. Cabang: `feat/frontend-prototype`. Aplikasi yang diaudit: Vite `http://127.0.0.1:5173/`, BFF 8090.
Akun: `admin@pegawai.ai` (Super Admin, mode admin nyala) dan `cs@colorbox.co.id` (Staf, tanpa pegawai AI, tampilan sederhana).
Layar: 1280×800 dan 375×812, terang dan gelap (gelap diperiksa di Beranda, Marketing, Kanban, Aplikasi, Tim, Detail).
Bukti: `docs-kaf/sprint5/audit-ux/*.png` (96 berkas; indeks di bagian 7) dan angka ukur dari skrip probe di halaman
(`scrollWidth/clientWidth`, kotak yang bisa di-scroll, teks terpotong `text-overflow`, target sentuh < 32 px, kontras WCAG).

Aturan yang dipakai (tetap, dari `CLAUDE.md` dan spesifikasi sebelumnya): bahasa Indonesia sederhana, satu tugas per layar,
langkah berikut yang jelas, galat dan kondisi kosong yang manusiawi, tidak ada kontrol mati, tanpa jargon di tampilan biasa.
Keputusan lama yang **dipertahankan**: istilah teknis (kode alat, ID model, token, status mentah `done`, ringkasan inggris di
Aktivitas) boleh tampil **hanya** di mode admin (`useAdminMode()`), tersaring di semua yang saya cek; halaman admin tetap
memakai kata "Agen", "Kemampuan", "Evaluasi" (spec-ux-awam bagian 1c); biaya dalam USD sampai backend menyediakan rupiah.
Tidak ada font, palet, atau gaya baru. Semua nilai memakai token `frontend/src/styles.css`.

---

## 1. Ringkasan temuan

| Prioritas | Jumlah | Arti |
|---|---|---|
| P1 | 8 | Rusak, menyesatkan, atau memaksa pengguna menebak. Wajib diperbaiki sebelum demo. |
| P2 | 22 | Tidak konsisten atau kurang jelas, tapi alur tetap jalan. |
| P3 | 14 | Poles. |

Yang sudah baik dan **jangan diubah**: skip-link dan `:focus-visible` global, sidebar dan drawer 375, kartu "Mulai dari sini",
dialog Atur (pemilih warna dan tingkat ketelitian), galat login (`Email atau kata sandi salah.`), Pengaturan > Keamanan
(satu kalimat), kondisi kosong Kanban, kontras teks biasa (probe: nol pelanggaran selain tombol nonaktif), tidak ada
overflow horizontal dokumen di semua rute pada 375.

Akar masalah yang berulang (bukan sekadar gejala):
1. Kotak yang bisa di-scroll di dalam kotak lain (Marketing `.cat-chips`, Evaluasi `ul.cases`, daftar kartu Kanban) karena `max-height` + `overflow:auto` dipakai sebagai cara menahan konten panjang.
2. CSS menumpuk tambalan: aturan yang sama ada di beberapa berkas (`.seg` di admin/pages/workspace.css, `.page-head` di tiga berkas, `.ws-agent*` di dua). Tiap tambalan memakai `:has()` atau `@media` baru, sehingga satu kasus (kartu "Perlu disambungkan ulang") luput.
3. `<label>` membungkus kontrol **dan** konten lain (Marketing `Field`), jadi nama aksesibel kolom Produk acuan berisi ±1.000 karakter.
4. Angka yang di-hardcode dan saling bertentangan ("1.216 produk" di Marketing, "1.206 produk" di Kemampuan; fakta: `bff/knowledge/colorbox/product-catalog.md` berisi **1.206**).
5. Klien API `api.catalog.*` (bff.ts) memanggil `/catalog/search`, `/catalog/products`, `/catalog/categories` yang **404** di BFF; rute yang benar adalah `GET /products/search`.

---

## 2. Marketing (formulir) · kolom "Produk acuan": rancangan pengganti

### 2.1 Masalah yang diukur (bukti `10-…`, `11-…`, `12-…`, `15-…`)

| Gejala | Ukuran |
|---|---|
| Kotak chip `div.cat-chips` | 303×156 px, isi 309×472 px: scroll vertikal **dan** horizontal sekaligus (1280). Di 375: 293×156, isi 309×568; chip terpanjang 309 px lebih lebar dari kotak sehingga terpotong tepat sebelum harga ("Rp 29"). |
| Fokus keyboard | 12 chip = 12 perhentian Tab sebelum kolom "Kanal". Outline fokus terpotong tepi kotak scroll. |
| Nama aksesibel kolom | `<label class="field">` membungkus chip: nama kolom = judul + hint + 12 chip (±1.000 karakter). |
| Bahasa label | "katalog resmi, 1.216 produk" padahal hanya 12 produk yang bisa dipilih dan jumlah sebenarnya 1.206. |
| Hint | "Produk dari katalog resmi. Klik untuk memakai sebagai acuan." dengan ikon centang 14 px: terbaca sebagai status "sudah terverifikasi", bukan petunjuk. |
| Tata letak | Kolom setinggi 12 chip membuat baris berikutnya turun dan menyisakan lubang kosong di bawah "Tujuan kampanye". |
| Pilihan | Setelah memilih, teks kolom berubah menjadi "Nama (Rp x - WARNA)" yang bisa diketik ulang: tidak jelas apakah nilai ini dari katalog atau tulisan sendiri. Chip aktif hanya berubah warna hijau tipis. |
| Data | Backend: pencarian hanya kata utuh bahasa Inggris, ≥3 huruf, OR antar kata, maksimum 20 baris, satu baris per **warna** (mis. "Denim Midi Skirt with Cargo Pocket" muncul untuk BEIGE dan OFF WHITE). `jaket`, `kemeja`, `de` = 0 hasil. Latensi ±20 ms. |

### 2.2 Keputusan rancangan

Ganti kolom + chip dengan **satu komponen** `ProductPicker` (combobox dengan daftar `listbox` mengambang, pola WAI-ARIA APG
"Combobox with list autocomplete, manual selection"). Tiga keadaan yang selalu terlihat jelas:

| Keadaan | Tampilan | Arti untuk pengguna |
|---|---|---|
| A. Belum dipilih | Kolom pencarian + teks bantuan tetap | "Cari lalu pilih satu." |
| B. Dari katalog | Kartu pilihan, tanda hijau **Dari katalog resmi** | "Nama dan harga ini dijamin dari katalog." |
| C. Tulisan sendiri | Kartu pilihan, tanda abu **Tulisan sendiri, tidak dicek ke katalog** | "Ini bukan produk katalog." Tidak ada asumsi. |

Daftar pilihan **tidak** mendorong tata letak (posisi absolut di bawah kolom), hanya punya **satu** scroll vertikal, tidak ada
scroll horizontal, tidak ada teks yang dipotong (nama membungkus sampai 2 baris, harga di kolom kanan tidak pernah terpotong).

### 2.3 Berkas

| Berkas | Tindakan |
|---|---|
| `frontend/src/ProductPicker.tsx` | Baru. Komponen + konstanta `CATALOG_TOTAL = 1206` + daftar `POPULAR` (12 produk lama, diubah menjadi `{name, price:number, colors:string[], category}`). |
| `frontend/src/ProductPicker.css` | Baru, diimpor oleh `ProductPicker.tsx`. Semua kelas `pp-*`. |
| `frontend/src/bff.ts` | Hapus blok `catalog: {products, search, categories}` (404). Tambah `productsSearch: (q: string, signal?: AbortSignal) => call<{ data: CatalogProduct[]; count: number }>('GET', \`/products/search?q=${encodeURIComponent(q)}&limit=20\`, undefined, signal)` dan tipe `CatalogProduct = { id:number; category:string; name:string; price:number; price_original:number|null; colors:string[]; sizes:string[]; url:string }`. Tidak ada pemakai lain `api.catalog` (grep: nol di `*.tsx`). |
| `frontend/src/Marketing.tsx` | Hapus `VERIFIED_CATALOG_SUGGESTIONS`, JSX `.cat-pick/.cat-chips`, dan pembungkus `<label>` untuk kolom ini. Pakai `<ProductPicker/>`. |
| `frontend/src/Platform.tsx:68` | Teks "1.206 produk" memakai `CATALOG_TOTAL` dari `ProductPicker.tsx` (satu sumber). |
| `frontend/src/admin.css` | Hapus `.cat-pick`, `.cat-chips`, `.cat-chip` (dan `.ws .cat-chip` di media 640). |

### 2.4 Markup (React)

```tsx
// Marketing.tsx, di dalam .mk-grid (lihat 3.2), menggantikan <Field label="Produk acuan ...">
<ProductPicker
  id="mk-product"
  value={form.product}
  onChange={(v) => setForm({ ...form, product: v })}
  error={tried ? errs.product : ''}
/>
```

`value` tetap string yang dikirim ke brief (kunci `form.product`, dipakai `briefPrompt`, `validate`, `COLORBOX_SAMPLE`).
Komponen menyimpan sendiri `picked: {kind:'catalog'|'custom', label:string, sub?:string} | null` dan **menurunkan** keadaannya
dari `value` saat mount (nilai awal kosong = A; `COLORBOX_SAMPLE.product` = C karena bukan hasil pencarian; setelah
"Isi contoh Colorbox" tampil kartu C "Tulisan sendiri"; supaya contoh tetap terbaca sebagai katalog, `COLORBOX_SAMPLE` diubah
menjadi objek yang ikut menandai `kind:'catalog'`, lihat 2.9).

Keadaan A (struktur DOM):

```html
<div class="field pp" data-state="search" id="mk-product-wrap">
  <label class="pp-label" for="mk-product">Produk acuan</label>
  <p class="pp-help" id="mk-product-help">
    Cari di 1.206 produk katalog resmi Colorbox. Ketik nama dalam bahasa Inggris, misalnya <b>denim</b>, <b>blazer</b>, <b>skirt</b>.
    Pilih satu dari daftar, atau tulis sendiri.
  </p>
  <div class="pp-box">
    <svg class="pp-ico" aria-hidden="true">…kaca pembesar 16px…</svg>
    <input id="mk-product" class="pp-input" role="combobox" type="text" autocomplete="off" spellcheck="false"
           aria-autocomplete="list" aria-expanded="false" aria-controls="mk-product-list"
           aria-describedby="mk-product-help mk-product-err" aria-invalid="false"
           placeholder="Ketik nama produk…" />
    <button type="button" class="pp-clear icon-btn" aria-label="Hapus tulisan" hidden>×</button>
    <div class="pp-pop" id="mk-product-pop" hidden>
      <div class="pp-sub" id="mk-product-sub">Contoh populer</div>            <!-- atau: "20 produk teratas untuk “denim”" -->
      <ul class="pp-list" id="mk-product-list" role="listbox" aria-labelledby="mk-product-sub">
        <li class="pp-opt" role="option" id="mk-product-o0" aria-selected="false">
          <span class="pp-name">Oversize Long Sleeve Checks Blazer</span>
          <span class="pp-price num">Rp 299.900</span>
          <span class="pp-meta">Outerwear & Jackets · DUSTY OLIVE</span>
          <s class="pp-was num" hidden>Rp 359.900</s>
        </li>
        …
        <li class="pp-opt pp-opt-own" role="option" id="mk-product-oN" aria-selected="false">
          Pakai tulisan saya: <b>“jaket denim”</b> <span class="pp-meta">tidak dicek ke katalog</span>
        </li>
      </ul>
      <div class="pp-foot" role="status">Menampilkan 20 produk pertama. Ketik lebih spesifik untuk mempersempit.</div>
    </div>
  </div>
  <small class="field-err" id="mk-product-err" role="alert"></small>
  <div class="sr" role="status" aria-live="polite" id="mk-product-live"></div>
</div>
```

Keadaan B/C (ganti `.pp-box` dengan kartu, `label` tetap, `for` menunjuk tombol "Ganti"):

```html
<div class="field pp" data-state="chosen">
  <span class="pp-label" id="mk-product-lab">Produk acuan</span>
  <div class="pp-chosen" data-kind="catalog" role="group" aria-labelledby="mk-product-lab">
    <svg class="pp-chosen-ico" aria-hidden="true">…centang-lingkaran 20px (catalog) / pensil 20px (custom)…</svg>
    <div class="pp-chosen-body">
      <b class="pp-chosen-name">Oversize Long Sleeve Checks Blazer</b>
      <span class="pp-chosen-sub num">DUSTY OLIVE · Rp 299.900</span>
      <span class="pill ok">Dari katalog resmi</span>                       <!-- custom: <span class="pill plain">Tulisan sendiri, tidak dicek ke katalog</span> -->
    </div>
    <div class="pp-chosen-act">
      <button type="button" class="btn soft sm" id="mk-product-change">Ganti</button>
      <button type="button" class="icon-btn" aria-label="Hapus produk acuan">×</button>
    </div>
  </div>
</div>
```

### 2.5 Perilaku (mesin keadaan)

Konstanta: `MIN_CHARS = 3` (karena backend membuang kata < 3 huruf), `DEBOUNCE_MS = 250`, `LIMIT = 20`.

| Peristiwa | Hasil |
|---|---|
| Fokus kolom (A), teks kosong | Buka popup dengan judul "Contoh populer" + 12 baris `POPULAR`, tanpa fetch. `aria-expanded=true`. |
| Mengetik < 3 karakter | Tetap tampilkan "Contoh populer", tidak fetch. Pada baris bantuan tidak ada perubahan. |
| Mengetik ≥ 3 karakter | Tunggu 250 ms, batalkan fetch sebelumnya (`AbortController`), panggil `api.productsSearch(q, signal)`. Selama menunggu: popup menampilkan 3 baris skeleton `.skel` (tinggi 56 px) bila belum ada hasil, atau hasil lama dengan `opacity:.6` dan `aria-busy="true"` pada `ul`. Live region: "Mencari…". |
| Hasil datang | Judul popup: `{n} produk untuk “{q}”` (n=20: `20 produk teratas untuk “{q}”`). Live region: sama. Tampilkan baris + baris terakhir "Pakai tulisan saya". Jika `count===20` tampilkan `.pp-foot` "Menampilkan 20 produk pertama. Ketik lebih spesifik untuk mempersempit." |
| 0 hasil | Ganti `ul` dengan `.pp-empty`: judul "Tidak ada produk untuk “{q}”." isi "Katalog memakai nama Inggris. Coba: jacket, shirt, pants, skirt, bag." (lima kata itu `btn link` yang mengisi kolom). Baris "Pakai tulisan saya" tetap ada di bawahnya. Live region: sama. |
| Gagal jaringan | `.pp-empty`: "Daftar produk belum bisa dimuat." + tombol `Coba lagi` + "Anda tetap bisa menulis nama produk sendiri." Baris "Pakai tulisan saya" tetap ada. |
| ↓ | Popup tertutup: buka. Terbuka: pindah opsi aktif berikutnya (melingkar tidak; berhenti di ujung). `aria-activedescendant` = id opsi aktif; opsi aktif `scrollIntoView({block:'nearest'})`. |
| ↑ / Home / End | Pindah ke sebelumnya / pertama / terakhir. |
| Enter | Jika ada opsi aktif: pilih (selalu `preventDefault()` agar formulir tidak terkirim). Jika tidak ada dan teks ≥ 2 karakter: pilih "Pakai tulisan saya". |
| Esc | Popup terbuka: tutup, pertahankan teks. Popup tertutup dan ada teks: kosongkan teks. |
| Tab / klik di luar (blur) | Tutup popup. Jika teks tidak kosong dan belum dipilih: **otomatis menjadi keadaan C** (tulisan sendiri), tidak ada teks yang hilang dan tidak ada asumsi karena tanda "Tulisan sendiri" terlihat. Klik opsi harus memakai `onMouseDown={e=>e.preventDefault()}` pada popup agar blur tidak menyela. |
| Pilih baris katalog | `onChange(\`${name} (Rp ${fmt(price)}${price_original ? `, harga normal Rp ${fmt(price_original)}` : ''} - ${colors.join('/')})\`)`; keadaan B; fokus pindah ke tombol "Ganti"; live region "Dipilih: {name}, {warna}, Rp {harga}". |
| "Ganti" | Kembali ke A, kolom berisi nama produk terpilih (terpilih semua teks), popup terbuka. |
| "×" pada kartu | Kosongkan `value`, kembali ke A, fokus ke kolom. |
| `tried && error` | Kolom mendapat `aria-invalid="true"`, `.pp-box` border `var(--negative)`, `#mk-product-err` berisi pesan. Pesan baru: `Produk acuan wajib diisi. Pilih dari katalog atau tulis sendiri.` (ganti `validate()` di Marketing.tsx). Saat submit gagal, fokus ke kolom galat pertama (lihat P1-02). |
| Perubahan `value` dari luar ("Isi contoh Colorbox", reset) | Komponen menyelaraskan `picked` (efek pada `value`): kosong → A; selain itu → kartu. |

Cache: simpan hasil per `q` (huruf kecil, spasi dirapikan) dalam `Map` di `useRef` selama komponen hidup agar mengetik-hapus tidak memanggil ulang.

### 2.6 Baris opsi (satu kolom, tidak pernah terpotong)

`.pp-opt` adalah grid dua kolom, tinggi minimum 56 px, padding `var(--s-2) var(--s-3)`:

```
┌───────────────────────────────────────────────────────┐
│ Oversize Long Sleeve Checks Blazer          Rp 299.900 │  baris 1: nama (kolom 1, 14px/500, boleh 2 baris) | harga (kolom 2, 14px/600, num, rata kanan)
│ Outerwear & Jackets · DUSTY OLIVE            Rp 359.900 │  baris 2: kategori · warna (13px --muted)        | harga normal dicoret (12px --muted, hanya bila ada)
└───────────────────────────────────────────────────────┘
```

Aturan nilai: warna ditulis apa adanya dari katalog (huruf kapital), kategori apa adanya. Bila `price_original` ada, harga
tampil sebagai harga katalog saat ini, harga normal dicoret, dan di nilai brief ditambah ", harga normal Rp X" (agar agen
tidak mengira diskon karangan). Baris `.pp-opt-own`: teks 14 px, `“…”` tebal, sub "tidak dicek ke katalog" 13 px `--muted`.

### 2.7 CSS (`ProductPicker.css`, hanya token)

```css
.pp { position: relative; gap: var(--s-2); }
.pp-label { font-size: 13px; font-weight: 500; }
.pp-help { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }   /* tidak diberi ikon centang */
.pp-box { position: relative; }
.pp-input { width: 100%; height: 40px; padding: 0 40px 0 36px; }                   /* 36 kiri = ikon, 40 kanan = tombol hapus */
.pp-ico { position: absolute; left: 12px; top: 12px; width: 16px; height: 16px; color: var(--muted); pointer-events: none; }
.pp-clear { position: absolute; right: 4px; top: 2px; width: 36px; height: 36px; }
.pp[data-invalid] .pp-input { border-color: var(--negative); }
.pp-pop { position: absolute; left: 0; right: 0; top: calc(100% + 4px); z-index: 30;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-card);
  box-shadow: 0 6px 24px rgba(0, 0, 0, .14); overflow: hidden;                       /* sama dengan .popmenu di chat.css:70 */
  animation: rise var(--m-in) var(--ease); }
:root[data-theme="dark"] .pp-pop { box-shadow: 0 6px 24px rgba(0, 0, 0, .45); }
.pp-sub { padding: var(--s-2) var(--s-3); font-size: 12px; font-weight: 600; color: var(--muted); border-bottom: 1px solid var(--rule); background: var(--raised); }
.pp-list { max-height: min(320px, 45vh); overflow-y: auto; overflow-x: hidden; overscroll-behavior: contain; }  /* SATU scroll */
.pp-opt { display: grid; grid-template-columns: minmax(0, 1fr) auto; column-gap: var(--s-3); row-gap: 2px; align-items: start;
  min-height: 56px; padding: var(--s-2) var(--s-3); border-bottom: 1px solid var(--rule); cursor: pointer; }
.pp-opt:last-child { border-bottom: 0; }
.pp-name { grid-column: 1; font-size: 14px; font-weight: 500; overflow-wrap: break-word; }   /* TIDAK pakai ellipsis */
.pp-price { grid-column: 2; grid-row: 1; font-size: 14px; font-weight: 600; text-align: right; white-space: nowrap; }
.pp-meta { grid-column: 1; font-size: 13px; color: var(--muted); }
.pp-was { grid-column: 2; grid-row: 2; font-size: 12px; color: var(--muted); text-align: right; white-space: nowrap; }
.pp-opt[aria-selected="true"], .pp-opt:hover { background: var(--accent-wash); box-shadow: inset 3px 0 0 var(--accent); }
.pp-opt-own { grid-template-columns: minmax(0, 1fr); background: var(--raised); }
.pp-empty { padding: var(--s-4) var(--s-3); display: grid; gap: var(--s-2); font-size: 14px; }
.pp-foot { padding: var(--s-2) var(--s-3); font-size: 12px; color: var(--muted); border-top: 1px solid var(--rule); background: var(--raised); }
.pp-chosen { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: var(--s-3); align-items: start; padding: var(--s-3);
  border: 1px solid var(--border); border-left-width: 3px; border-radius: var(--radius-control); background: var(--surface); }
.pp-chosen[data-kind="catalog"] { border-left-color: var(--st-done); }
.pp-chosen[data-kind="custom"]  { border-left-color: var(--control); }
.pp-chosen-ico { width: 20px; height: 20px; margin-top: 1px; }
.pp-chosen[data-kind="catalog"] .pp-chosen-ico { color: var(--st-done); }
.pp-chosen-body { display: grid; gap: var(--s-1); min-width: 0; justify-items: start; }
.pp-chosen-name { font-size: 14px; font-weight: 600; overflow-wrap: anywhere; }
.pp-chosen-sub { font-size: 13px; color: var(--muted); }
.pp-chosen-act { display: flex; gap: var(--s-1); align-items: center; }
@media (max-width: 640px) {
  .pp-input, .pp-chosen-act .btn { min-height: 44px; }
  .pp-opt { min-height: 60px; }
  .pp-chosen { grid-template-columns: auto minmax(0, 1fr); }
  .pp-chosen-act { grid-column: 1 / -1; justify-content: flex-end; }
}
```

Fokus: kolom memakai `:focus-visible` global (outline 2 px `--accent`). Opsi aktif ditandai dengan latar + bar kiri (tidak hanya warna);
di mode kontras tinggi pakai `outline: 2px solid` bila `forced-colors`. Tidak ada `overflow:hidden` pada leluhur `.field`/`.ws-form`
(sudah saya cek: `.ws-form` dan `.fgrid` tidak memotong), jadi popup tidak terpotong; `.pp-pop` memotong dirinya sendiri hanya untuk radius sudut.
Pada 375, saat fokus: `inputRef.current.scrollIntoView({block:'center'})` agar popup dan kolom terlihat di atas keyboard layar.

### 2.8 Kondisi yang harus tampil (checklist visual)

| Kondisi | Yang terlihat |
|---|---|
| Awal | Label, teks bantuan 2 baris, kolom 40 px kosong dengan placeholder `Ketik nama produk…`. Tidak ada chip, tidak ada scroll. |
| Fokus kosong | Popup "Contoh populer" 12 baris, tinggi maks 320 px, satu scroll vertikal. |
| Mengetik `denim` | Skeleton ±300 ms lalu "20 produk teratas untuk “denim”" dan `.pp-foot`. |
| Mengetik `jaket` | `.pp-empty` "Tidak ada produk untuk “jaket”." + saran jacket/shirt/pants/skirt/bag + "Pakai tulisan saya: “jaket”". |
| Dipilih | Kartu B hijau. Kolom pencarian hilang. |
| Tulisan sendiri | Kartu C abu. |
| Galat kirim | Pesan merah di bawah kartu/kolom, fokus pada elemen pertama komponen. |
| Gelap | Semua dari token; popup `--surface` di atas `--ground`, bayangan lebih pekat. |
| 375 | Popup selebar kolom (±343 px), nama membungkus, harga tidak terpotong, baris ≥ 60 px. |

### 2.9 Perubahan kecil di Marketing.tsx yang menyertai

* `COLORBOX_SAMPLE.product` tetap string yang sama; tambahkan `const SAMPLE_KIND = 'catalog'` hanya bila Anda ingin kartu hijau: **jangan**. Karena contoh itu ditulis tangan, tampilkan kartu C. (Keputusan: jujur lebih baik daripada menandai hijau tanpa pengecekan.)
* Hapus komentar/konstanta yang tidak terpakai setelah memindahkan data populer.
* Uji manual: `Isi contoh Colorbox` → kartu C → `Ganti` → cari `blazer` → pilih → kartu B → kirim formulir (nilai di brief berformat `Nama (Rp 299.900 - WARNA)`).

### 2.10 Kriteria penerimaan

1. Pada 1280 dan 375, terang dan gelap, tidak ada elemen di sekitar kolom ini yang punya `scrollWidth > clientWidth`; hanya `.pp-list` yang punya `scrollHeight > clientHeight` (probe: nested = `section.page.ws` dan `ul.pp-list` saja).
2. Tidak ada teks produk yang terpotong: untuk 20 hasil `denim`, `getBoundingClientRect().right` setiap `.pp-price` ≤ kanan `.pp-pop`; tidak ada `text-overflow: ellipsis` di `.pp-*`.
3. `ariaSnapshot` menunjukkan `combobox "Produk acuan"` (nama pendek), bukan nama ±1.000 karakter; jumlah perhentian Tab dari "Tujuan kampanye" ke "Kanal media sosial" ≤ 4 (kolom, Ganti/Hapus bila terpilih).
4. Keyboard penuh: ↓ membuka dan bergerak, Enter memilih tanpa mengirim formulir, Esc menutup, Tab keluar tanpa kehilangan teks (menjadi kartu C).
5. `jaket` → pesan "Tidak ada produk…" dan pilihan "Pakai tulisan saya". Memutus jaringan → "Daftar produk belum bisa dimuat." dan "Coba lagi".
6. Label menyebut 1.206 di satu tempat saja (`CATALOG_TOTAL`) dan sama dengan Kemampuan.
7. Hanya request `GET /bff/api/products/search?q=…&limit=20`; tidak ada request ke `/catalog/*`; request dibatalkan saat mengetik cepat (tab Network menunjukkan `canceled`).
8. `npm run build` dan tes yang ada lulus (tidak diubah oleh tugas ini).

---

## 3. Tabel prioritas

Format: **ID · Layar · Masalah (bukti) · Perbaikan persis · Cek penerimaan · Slice**.
Kelas CSS bertanda ⚑ adalah kontrak antara slice TSX dan slice CSS (bagian 5).

### 3.1 P1 (rusak atau menyesatkan)

| ID | Layar | Masalah (bukti) | Perbaikan | Penerimaan | Slice |
|---|---|---|---|---|---|
| P1-01 | Marketing · Produk acuan | Lihat bagian 2: dua scrollbar, harga terpotong, hint lemah, 12 produk padahal "1.216", angka salah (fakta 1.206), nama aksesibel ±1.000 karakter, 404 pada klien katalog. `10-`,`11-`,`12-`,`15-` | Bagian 2 seluruhnya. | Bagian 2.10 | S1 |
| P1-02 | Marketing · tata letak formulir tahap 1 | (a) `.fgrid` `auto-fill minmax(260px)` menghasilkan 3 kolom dengan lubang di bawah "Tujuan kampanye" (`15-`). (b) Placeholder terpotong di 303 px: "Contoh: Inspirasi pakaian kuliah yang santa". (c) "Jumlah slide/output" memakai placeholder `5` yang tampak seperti isi. (d) Galat "Produk atau topik wajib diisi." tidak cocok dengan label. (e) Ringkasan galat "Lengkapi 5 kolom wajib di atas" ada di bawah, fokus tidak pindah. (f) Ada **dua** "Pengaturan tambahan": satu di dalam formulir, satu di bawah halaman (`14-`). (g) Stepper 375 pecah 3+2 tanpa garis (`11-`). (h) `Field` = `<label>` pembungkus. | (a) Tambah `.mk-grid` di `admin.css`: `display:grid; grid-template-columns: repeat(6, minmax(0,1fr)); gap: var(--s-4)`; Tujuan `grid-column: span 6`, Produk `span 6`, Kanal/Format/Jumlah `span 2` masing-masing; `@media (max-width: 760px)` semua `span 6`. Terapkan `className="mk-grid"` menggantikan `fgrid` pada form tahap 1 (bagian "Pengaturan tambahan" tetap `fgrid`). (b) Placeholder: `Contoh: inspirasi gaya kuliah di Instagram`. (c) Nilai awal `count: '5'` di `blankForm`, label `Jumlah slide`, placeholder dihapus, teks bantu `Isi 1 sampai 10.` (galat lama tetap). (d) `validate()`: `Produk acuan wajib diisi. Pilih dari katalog atau tulis sendiri.` (e) Pada submit gagal: ringkasan galat dipindah **di atas** tombol (sudah di atas tombol; tambahkan `tabIndex={-1}`, `ref`, `.focus()` pada ringkasan, dan `aria-describedby`), dan fokus ke kolom pertama yang galat. (f) Hapus `<details className="opts">` kedua (yang di luar form, baris ±820 `Pengaturan tambahan`) bila isinya sama dengan yang di dalam form; bila berbeda, ubah judulnya menjadi `Catatan tambahan tim` dan jelaskan isinya. (g) Stepper: ganti kelas `stepper` menjadi `mk-stepper` di `admin.css`: `display:flex; overflow-x:auto; scroll-snap-type:x mandatory`; tiap langkah `flex: 0 0 auto; min-width: 88px`; garis penghubung tetap; 375: satu baris bergulir, langkah aktif `scrollIntoView({inline:'center'})`. (h) Ubah `Field` menjadi `<div className="field">` + `<label htmlFor>` + `id` pada kontrol + `aria-describedby` galat; kolom tahap lain dipakai ulang. | 1280: tidak ada lubang >16 px antar baris; 375: kolom tunggal; `input#...` tiap kolom punya nama aksesibel = labelnya; submit kosong memindahkan fokus ke "Tujuan kampanye"; hanya satu "Pengaturan tambahan" di halaman. | S1 |
| P1-03 | Marketing · tahap 5 Persetujuan | `checklist` default **semua true** (`Marketing.tsx:~236`): daftar periksa sudah tercentang sebelum ada hasil; "Setujui" aktif walau "Belum ada hasil di tahap Persetujuan"; pratinjau 5 slide memakai `img: '/output/carousel_latest/slide_*.png'` hard-coded: semua 404 (`naturalWidth 0`, hanya teks alt terlihat, `16-…tahap5`, `18-`) dan menampilkan konten kampanye contoh milik orang lain; teks "Klik tombol di atas untuk menjalankan tahap ini" menunjuk tombol yang tidak ada; "Quality Gate" dan "Model AI: Diperiksa manusia" jargon. | (1) Default semua `false`. (2) `Setujui` dan `Minta revisi`, `Tolak`: `disabled` bila `outs.length === 0` **atau** (`Setujui` saja) ada centang yang belum dicentang; di bawahnya `<p className="quiet small">Setujui aktif setelah semua 5 poin diperiksa.</p>` (`aria-live="polite"`). (3) Pratinjau hanya dirender dari gambar hasil nyata (`shown?.result?.images`/hasil tahap 3); bila tidak ada, ganti seluruh blok dengan `<Empty title="Belum ada gambar untuk diperiksa">Jalankan tahap Desain grafis dulu.</Empty>` dan hapus array `PREVIEW_SLIDES`. Tambahkan `onError` pada `<img>` yang menukar ke kotak abu `.mk-img-miss` "Gambar tidak bisa dimuat". (4) Salin kosong: `Belum ada hasil di tahap Persetujuan. Selesaikan tahap sebelumnya dulu.` dengan tombol `Ke tahap Desain grafis` (`setStage(2)`). (5) Judul: `5. Periksa dan setujui`; baris agen: `Anda` / `Pemeriksa akhir`, tanpa `Model AI:` (sembunyikan baris model bila `modelInfo` bukan model). | Tahap 5 tanpa hasil: 0 centang, 3 tombol keputusan nonaktif, tidak ada `<img>` rusak (`document.images` semua `naturalWidth>0`), tidak ada teks "Quality Gate". | S1 |
| P1-04 | Aplikasi · kartu "Tersambung" | Kartu `data-s="reconnect"` (Google Drive, Gmail) rusak: tombol "Sambungkan ulang / Putuskan" berada di kolom kanan `.app-row` sehingga judul dan paragraf terjepit; pada 375 judul pecah huruf per huruf ("Goo/gle/Drive", "Gm/ail") dan menimpa pil "Perlu disambungkan ulang" (`25b-aplikasi-375-light`); pada 1280 tombol melayang di tengah kartu dengan ruang kosong (`25b-aplikasi-1280-light`). Judul grup berbunyi "Tersambung · 3" padahal 2 dari 3 perlu disambungkan ulang. Kartu Canva: teks `Akun: canva_mcp_akan-dusk` memperlihatkan ID teknis (akun admin saja? gating `shownAccounts(..., admin)`: aman untuk staf, tetap salah bentuk untuk admin). | **CSS (S2, `pages.css`)**: (1) hapus aturan `.app-row:has(.connect-acct) > .app-card-act` dan `:not(:has(...))` pada media 640. (2) Tambah: `.app-row { grid-template-columns: minmax(0,1fr) auto }` tetap untuk baris sehat (satu baris: kepala + tombol). (3) `.app-row[data-s="reconnect"], .app-row[data-s="broken"], .app-row[data-s="needs_scope"] { grid-template-columns: minmax(0,1fr); }` dengan `> * { grid-column: 1 / -1; }` dan `> .app-card-act { grid-row: auto; justify-content: flex-start; margin-top: var(--s-2); }`. (4) Pada ≤ 640: `.app-row > .app-card-act { grid-column: 1 / -1; grid-row: auto; justify-content: flex-start; }` untuk semua status. (5) `.app-card-head .app-top h3 { overflow-wrap: break-word; }` (ganti `anywhere`, yang membuat lebar minimum nol). **TSX (S3, `connections.tsx`)**: pisahkan grup: `Tersambung · {n}` hanya `status==='connected'`; baru grup `Perlu dihubungkan ulang · {m}` untuk `reconnect|broken|needs_scope` (judul `h2`, kelas `apps-group`, kartu urut sama). Ganti baris admin `Akun: <b>{account}</b>` menjadi `Akun: {account}` (tanpa tebal, `overflow-wrap:anywhere`). | 375 dan 1280: tiap kartu punya urutan vertikal kepala → pesan → tombol; nama "Google Drive" tidak pernah pecah antar huruf (lebar judul ≥ 80 px); jumlah di judul grup = jumlah kartu di bawahnya dan "Perlu dihubungkan ulang" muncul bila ada. | S2 + S3 |
| P1-05 | Jadwal & tugas · kartu selesai | Tombol "⋮" menonjol keluar dari kartu (kanan kartu 1500 px, tombol 1490–1522), `ul.kb-cards` punya scroll horizontal tersembunyi (197 vs 211 px), menu "Ulangi / Arsipkan" menutupi kartu di bawah (`50-kanban-menu-1280-light`). Penyebabnya: baris `.kc-act` berisi biaya + "Lihat hasil" + "⋮" ≈ 235 px di kartu 197 px. | **TSX (S4, `Kanban.tsx` ±baris 92-110)**: pindahkan `<span className="kc-cost num">` ke dalam `.kc-foot` (baris bersama chip), sehingga `.kc-act` hanya `[Lihat hasil][⋮]`. **CSS (S2)**: `.kb-cards { overflow-x: hidden; }`, `.kcard { min-width: 0; }`, `.kc-act { flex-wrap: wrap; min-width: 0; }`, `.kc-act .kc-menu { flex: none; margin-left: auto; }`, `.kc-menu .popmenu { right: 0; left: auto; max-width: calc(100vw - 32px); }`. | Probe di 1280: tidak ada `ul.kb-cards` dengan `X`; kanan tombol ⋮ ≤ kanan kartu − 8 px; menu terbuka tidak melewati kanan kolom. | S2 + S4 |
| P1-06 | Jadwal & tugas · akun tanpa pegawai | Untuk Staf (nol pegawai), pemilih "siapa mengerjakan" berupa `<select>` **kosong** tanpa label dan tombol "Jadwalkan/Tambah" tetap tampak bisa dipakai (`103-staf-kanban-1280-light`): kontrol mati. | `Kanban.tsx`: bila `bots.length === 0` render, menggantikan baris input, `<div className="kb-none"><p>Belum ada pegawai AI untuk diberi tugas.</p><a className="btn primary" href="#/agen/baru">Buat pegawai</a></div>` dan sembunyikan form; tambahkan `aria-label="Dikerjakan oleh"` dan `<option value="">Pilih pegawai</option>` (nilai awal) pada select untuk kasus ≥1 pegawai. Tombol "Tambah" `disabled` sampai teks tidak kosong **dan** pegawai terpilih. | Staf tanpa pegawai: tidak ada `<select>` kosong; satu kalimat + satu tombol. Admin: select punya label aksesibel. | S4 |
| P1-07 | Evaluasi · 375 | Dua scroll bertumpuk: halaman bergulir **dan** `ul.cases` (341×487, isi 1899 px) bergulir sendiri; `textarea#turn-0` juga bergulir (291×157, isi 197). Pada 1280 `ul.cases` juga 584×480 isi 1542 (`29-uji-*`). Pengguna terjebak scroll di tengah halaman. | `workspace.css` (S1): `.cases { max-height: none; overflow: visible; }` pada `@media (max-width: 900px)`; pada ≥ 901 tetap `max-height: calc(100vh - 280px); overflow-y:auto` **hanya** bila kolom kanan sticky; textarea giliran: `field-sizing: content; min-height: 96px; max-height: none; resize: vertical`. | 375: probe nested = `section.page.ws` saja; 1280: `ul.cases` boleh satu scroll, tanpa scroll halaman ganda. | S1 |
| P1-08 | Pengaturan · Umum/Notifikasi | "Mode admin": teks "**Sembunyikan** halaman dan rincian teknis dari menu" tapi kotak **dicentang "Nyala"** justru menampilkan menu Admin: arti terbalik. Semua saklar di Pengaturan memakai `<input type=checkbox>` asli 13×13 px berlabel "Nyala/Mati", berbeda dari saklar `.tgl` di Chat dan Layanan pelanggan (`26-`, `60-`). | `Settings.tsx` baris ±147: judul `Tampilan admin`, hint `Tampilkan menu Admin dan rincian teknis. Matikan untuk melihat tampilan yang sama dengan staf.` Ganti semua `<label className="set-check"><input type="checkbox">` dengan `<Switch checked label="Nyala" onChange/>` dari `ws-common.tsx` (sudah ada: `role="switch"`, kelas `.tgl`, 36×20; di ≤ 640 `min-height: 40`). Label dinamis `Nyala`/`Mati` tetap. | Semua kontrol bolak-balik di Pengaturan memakai `.tgl`; tidak ada `input` 13×13; teks Tampilan admin tidak lagi berisi kata "Sembunyikan". | S6 |

### 3.2 P2 (tidak konsisten atau kurang jelas)

| ID | Layar | Masalah (bukti) | Perbaikan | Penerimaan | Slice |
|---|---|---|---|---|---|
| P2-01 | Beranda 375 | Kartu biaya: urutan visual kacau: "Biaya bulan ini → Pemakaian: 6.205.737 token → Lihat rincian → **$0.90** USD …" (`02-beranda-375-light`). Teks "bulan ini, tanpa batas biaya" mengulang "bulan ini" dan memakai kata "batas biaya" yang kabur. Angka token muncul dua kali (kartu biaya dan petak "Pemakaian bulan ini (token)"). | `Dashboard.tsx` (`CostMeter`): urutan DOM = judul, angka, keterangan, rincian, tautan. Teks admin: `{$} USD` + `perkiraan` + `Tanpa batas biaya yang diatur.` Hapus baris "Pemakaian: … token" dari kartu (tetap di petak statistik, admin saja). `pages.css`: `.cost-card` grid `1fr auto`, 375 jadi satu kolom dengan "Lihat rincian" di bawah angka. | 375: angka terlihat sebelum tautan; tidak ada dua tampilan token yang sama. | S6 + S2 |
| P2-02 | Beranda · "Pegawai AI Anda" | Daftar 6 baris dengan dua tombol per baris ("Ajak bicara" + "Atur") padahal spec-ux-awam hanya meminta tombol utama; "Atur" dan tautan nama bersaing. | Biarkan (keputusan lama), tapi `a.team-name` target klik 245×16 px → tambah `padding-block: 6px` (tinggi ≥ 28) dan `min-height:44` ≤ 640 (sudah di aturan 640; hanya desktop yang kurang). | Probe: `a.team-name` tinggi ≥ 28 px di 1280. | S2 |
| P2-03 | Tim (daftar & kepala) | Susunan avatar tumpuk memotong huruf pertama ("D", "M" separuh hilang): `.avatar-stack .bot-avatar + .bot-avatar { margin-left:-8px }` dengan `outline: 2px` warna `--ground` (`22-grup-1280-light`, `112-`). | `chat.css`: `.avatar-stack { --ring: var(--stack-ring, var(--ground)); }`, `.bot-avatar { box-shadow: 0 0 0 2px var(--ring); outline: 0; position: relative; }`, `.bot-avatar + .bot-avatar { margin-left: -6px; }`, z-index menurun (`:nth-child(1){z-index:3}`, 2 → 2, 3 → 1) agar huruf kiri utuh. Baris terpilih/hover mengisi `--stack-ring` sesuai latarnya. | Huruf pertama tiap avatar terbaca penuh pada daftar dan kepala; cincin menyatu dengan latar baris terpilih. | S2 |
| P2-04 | Tim · percakapan | Pita "Rencana menunggu persetujuan Anda" menempel dan memotong gelembung terakhir ("antre satu") tanpa jarak (`22-grup`, `112-grup`). | `Group.tsx`: pita jadi anak terakhir area pesan (bukan overlay absolut) dengan `margin-top: var(--s-3)`; `chat.css` `.convo-body { padding-bottom: var(--s-4) }`. | Pita tidak menutupi gelembung; ada jarak ≥ 12 px. | S5 + S2 |
| P2-05 | Chat 1280 | Dua tombol bernama sama "Topik baru" (daftar riwayat dan kepala percakapan) dan header daftar bernama "Pegawai AI" persis seperti merek di sidebar. | `ChatLayout.tsx`/`Chat.tsx`: pertahankan "Topik baru" hanya di daftar riwayat (`+ Topik baru`); tombol kepala dihapus pada ≥ 901 px (tetap di 375). Judul daftar `Pegawai AI` → `Pegawai`. | Satu "Topik baru" tampak pada 1280. | S5 |
| P2-06 | Chat 375 | Kepala: tombol "Riwayat", nama, "Topik baru", kebab "⋮" 3 titik pucat; subjudul terpotong "Penulis naskah dan …". | `chat.css`: subjudul `white-space: normal; -webkit-line-clamp: 2`; kebab `color: var(--text)` bukan `--faint`. | Subjudul terbaca ≥ 2 baris; ikon ⋮ kontras ≥ 3:1. | S2 |
| P2-07 | Jadwal & tugas 375 | Tombol kepala hanya "berulang" (kata "Tugas" disembunyikan `hide-sm`) sehingga artinya hilang; pemilih pegawai tersembunyi di balik tautan "Untuk Rian · Ubah" (`23-kanban-375-light`). | `Kanban.tsx:521`: label tetap `Berulang` di 375 dengan ikon ulang 16 px; `aria-label` penuh sudah ada. Tautan "Untuk Rian · Ubah" → tombol `btn link` "Untuk Rian. Ganti" (`aria-expanded` ke `.tq-opts`). | Label tombol terbaca sebagai satu kata bermakna dengan ikon; kontrol Ganti ≥ 40 px. | S4 |
| P2-08 | Jadwal & tugas | Kartu: tulisan `< $0.01 USD` (`.kc-cost::after` menambah " USD"), stripe kiri kuning/oranye tanpa arti, kolom "Dikerjakan" berjudul biru sedangkan lainnya hitam, "Tambah" nonaktif tampak sebagai blok abu kotor. | `workspace.css` baris 373 (`.kc-cost::after` USD) hapus (S1); `Kanban.tsx`: kartu non-admin tidak menampilkan biaya; judul kolom semua `var(--text)`, penanda status berupa titik 8 px `--st-*` di sebelah hitungan; tombol primer nonaktif lihat P2-20. Stripe kiri hanya untuk `priority>0` (pil "Penting" sudah ada). | Kartu staf tanpa biaya; stripe hanya pada tugas penting. | S4 + S1 |
| P2-09 | Jadwal & tugas · panel hasil | ID acak "7bba0272" dan status mentah `done` di kepala panel (admin), "Hasil terakhir" sama dengan ringkasan di atasnya, "Percakapan: Belum ada percakapan" padahal ada hasil, `<details>` Riwayat memakai segitiga bawaan peramban (`51-kanban-panel-1280-light`). Tombol "Kirim catatan" dengan placeholder "Balas ke pegawai…". | `TaskPanel.tsx`: ID hanya di mode admin dalam `<small className="quiet">`; hapus blok "Hasil terakhir" bila teksnya sama dengan ringkasan; blok "Percakapan" tampil hanya bila ada pesan; ganti `<details>` dengan `.btn link` + chevron `Icon` seperti `ThinkingBlock`; placeholder `Tulis catatan untuk Rian…` selaras tombol `Kirim catatan`. | Tidak ada pengulangan teks; chevron konsisten. | S4 |
| P2-10 | Tugas berulang (dialog) | Input waktu tampil `09:00 AM` (12 jam, mengikuti peramban) untuk pengguna Indonesia (`53-kanban-berulang-1280-light`). | `Kanban.tsx` dialog: ganti `<input type="time">` menjadi dua `<select>` Jam (00–23) dan Menit (00, 15, 30, 45) berlabel `Kapan?` dan teks `WIB` (zona waktu dari Pengaturan), atau `<input type="time" lang="id-ID">` ditambah `step=900` bila tetap native; wajib tampil 24 jam. | Tampil `09.00`, bukan AM/PM. | S4 |
| P2-11 | Aplikasi 375 (dan staf) | Subjudul halaman terpotong "…agar pegawai AI" dengan elipsis: kalimat tidak lengkap (`pages.css:660` `.page.apps .page-head p {white-space:nowrap; text-overflow:ellipsis}`). Kategori `.apps-cats` bergulir horizontal tersembunyi tanpa petunjuk selain gradient. | `pages.css` (S2): hapus aturan nowrap/ellipsis; biarkan membungkus. Kategori 375: tetap satu baris bergulir tetapi tambah `scroll-snap`, dan `<button>` pertama aktif `scrollIntoView`. | Subjudul tampil utuh dalam 2 baris di 375. | S2 |
| P2-12 | Pengetahuan 375 | Nama berkas terpotong elipsis ("product-size-reference.…", "customer-inquiry-patter…") sehingga pengguna tidak tahu berkas yang mana (`24-pengetahuan-375-light`). Tombol "Lihat/Hapus" teks polos tanpa batas, jarak antar baris besar. | `pages.css`: `.kb-rname { white-space: normal; overflow-wrap: anywhere; display: block; }` (dua baris), `.kb-row` grid `1fr auto`, tombol aksi `btn quiet-btn sm` min-height 40 di 375. | Nama berkas terbaca penuh. | S2 |
| P2-13 | Pengetahuan | Kalimat penjelas atas panjang (3 baris di 375) mencampur tiga hal (siapa membaca, jenis berkas, Drive). | `Pengetahuan.tsx`: pecah menjadi dua: `Semua pegawai AI membaca ini dan menyebut sumbernya.` dan di bawah kotak tempel link: `TXT, MD, CSV, PDF, DOCX · maks. 10 MB.` Tautan Drive: `Drive pribadi perlu disambungkan dulu di Aplikasi.` hanya muncul bila Drive belum tersambung. | Satu pesan per baris. | S6 |
| P2-14 | Atur (dialog) | Radio tingkat ketelitian 13×13 px (`input 13x13` di probe) terlalu kecil di 375; fokus awal jatuh pada tombol tutup "×" (cincin biru di `33-atur-dialog-375`) alih-alih pilihan saat ini. | `Dialogs.tsx` (`EditBotDialog` ±baris 518-560): kelas `.tier-radio` pada `<input type=radio>` dengan `width:20px;height:20px` (aturannya di `pages.css`, S2) dan seluruh `<label>` baris `min-height:56px`; beri `data-autofocus` pada swatch terpilih (dipakai `Dialog`, lihat P3-12). | Radio ≥ 20 px; fokus awal pada pilihan saat ini. | S6 + S2 |
| P2-15 | Detail pegawai | Dua tombol "Atur" (kepala dan kartu "Bisa Anda ubah"); dua KPI token yang nilainya sama (2.823.961) karena semua pemakaian terjadi bulan ini (admin). Warna agen membuat judul coklat (kontras dihitung OK). | `Agents.tsx`: hapus tombol "Atur" di kartu (pertahankan di kepala); kartu "Bisa Anda ubah" diberi judul `Pengaturan pegawai` dan baris `Warna`, `Tingkat ketelitian` jadi tombol-baris yang membuka dialog Atur. KPI "Pemakaian total" disembunyikan bila sama dengan bulan ini (`total === month`). | Satu tombol Atur per layar. | S6 |
| P2-16 | Layanan pelanggan, Marketing, Kemampuan (kepala) | Pil teknis "Alur 4 pegawai AI aktif", kode "CRE-01…04", "Model AI: DeepSeek V4.1 Flash", "Mode uji simulasi", "Intent dan prioritas", "tiket", "Rekomendasi eskalasi", "Computer Use Nonaktif" muncul di halaman admin tanpa penanda admin. | Halaman admin boleh teknis, tapi beri satu penanda konsisten: kelas `.admin-tag` (⚑ didefinisikan di `styles.css`, S2): pil 12 px `--plain-bg` `--plain-ink` bertuliskan `Admin`; terapkan pada: baris "Model AI: …" Marketing (hanya tampil bila `admin`), tab "Computer Use". Ganti kata: `Intent dan prioritas` → `Maksud pelanggan dan tingkat penting`, `Rekomendasi eskalasi` → `Perlu diteruskan ke manusia?`, `Ringkasan tiket` → `Ringkasan masalah`, `Mode uji simulasi` → `Mode uji (tidak mengirim apa pun)`. | Tidak ada kata di daftar itu pada UI staf; admin melihat `Admin` tag. | S1 |
| P2-17 | Marketing · header agen 375 | Nama agen "Content Strategist (CRE-01)" membungkus 3 baris di samping pil (`11-marketing-375-light`). | `admin.css`: `.ws-agent-head .ws-row { align-items: flex-start; flex-wrap: wrap }`, pil turun ke bawah nama pada ≤ 640; tampilkan peran dulu: `Content Strategist` (tanpa kode) dengan kode di `title`. | Nama tidak membungkus lebih dari 1 baris di 375. | S1 |
| P2-18 | Marketing · tahap 3 | Kartu formulir hanya ±685 px lebar di 1215 px area (kolom kanan kosong), sedangkan tahap 1 selebar penuh (`16-marketing-tahap3`). Penyebab: `.ws-grid` 2 kolom (`minmax(0,1fr) 260px`) dengan kolom riwayat kosong tetapi tidak `data-solo`. | `Marketing.tsx`: `data-solo` aktif bila `inStage.length===0`, bukan hanya `outs.length===0`. | Lebar kartu sama di semua tahap tanpa hasil. | S1 |
| P2-19 | Marketing · "Jalankan semua langkah (4 Pegawai AI)" | Tombol memulai 4 pekerjaan AI berbiaya tanpa konfirmasi, tanpa perkiraan waktu. | `Marketing.tsx`: klik membuka `Dialog` `Jalankan semua langkah?` isi `Empat pegawai AI akan bekerja berurutan (±10 menit) dan memakai kuota. Anda bisa menghentikannya kapan saja.` tombol `Mulai` / `Batal`. | Klik pertama hanya membuka dialog. | S1 |
| P2-20 | Semua tombol primer nonaktif | `Kirim`, `Tambah`, `Simpan`, `Buat pegawai`, `Buat tugas berulang`, `Tambah link` memakai `opacity:.45` di atas warna primer: terlihat seperti blok abu kotor tanpa alasan. Probe kontras gelap: 2.82:1 (`Tambah`, `Kirim`, `Simpan`); `Tambah link` 2.82:1 (terang) dan 4.09:1 (gelap). | `styles.css`: `.btn.primary:disabled { background: var(--active); color: var(--muted); opacity: 1; border-color: var(--border); }` (kontras `--muted` di `--active` ≥ 5:1 terang; gelap ≈ 6:1). Untuk formulir yang alasan nonaktifnya tidak jelas, tambah `title`/teks bantu (Kanban: "Tulis tugasnya dulu"). | Probe kontras: nol pelanggaran pada tombol nonaktif. | S2 (+ teks di S4/S6) |
| P2-21 | Aktivitas | (a) Ringkasan berbahasa Inggris untuk admin ("Reading tool details · 1 tool", "Canva Mcp · list folder items +1", "Searching tools · …"): bocor di tabel admin; (b) kolom "Durasi" dan "Buka" berisi "–" di semua baris yang diperiksa (kolom mati); (c) sel `td.sum` setinggi 42 px sementara sel lain 45 px sehingga garis pemisah baris kolom Ringkasan naik 3 px dan terlihat bergeser (`30-aktivitas-1280-light`); (d) 375: 17.641 px tinggi halaman karena tiap baris jadi kartu 260 px. | (a) `Activity.tsx`: peta terjemah di sisi tampilan: `Reading tool details · N tool` → `Membaca petunjuk alat (N)`, `Searching tools · …` → `Mencari alat: …`, `X Mcp · a b c` → `X: a b c`; sisanya tampil apa adanya. (b) Sembunyikan kolom bila seluruh nilainya kosong (`rows.every(r => !r.duration)`). (c) `panel.css`: `.act td.sum { padding: 0; height: 100%; } .act .sum-btn { display: block; width: 100%; min-height: 44px; padding: 0 var(--s-3); text-align: left; }`. (d) 375: kartu 4 baris (Waktu + Kegiatan, Pegawai + Status, Ringkasan) dengan `padding: var(--s-2) var(--s-3)` dan tinggi ≈ 120 px; memuat 20 baris per halaman, tombol "Muat lagi" (sudah ada) di akhir. | Garis antar-baris sejajar; tidak ada teks Inggris dari daftar; 375: 20 baris ≤ 3.200 px. | S1 |
| P2-22 | Evaluasi · Bandingkan | "Jumlah percobaan" dan pilihnya terpusat sementara semua kolom rata kiri; segmen "Diulang beberapa kali / Dua agen" tanpa label (`72-uji-bandingkan-1280-light`); label "Public Data · 9 Nov 2026" diulang di tiap kasus; tab aktif naik 2 px dari tab lain. | `workspace.css`/`Uji.tsx`: `.cmp-opts` kolom rata kiri; segmen diberi `<span className="field-label">Cara membandingkan</span>`; hapus baris sumber dari daftar (tetap di detail); `.kb-tabs`/`[role=tab]` samakan `border-bottom` 2 px transparan pada tab tak aktif. | Tidak ada elemen terpusat di panel; segmen punya label. | S1 |

### 3.3 P3 (poles)

| ID | Layar | Masalah | Perbaikan | Slice |
|---|---|---|---|---|
| P3-01 | Masuk/Daftar | Kartu dipusatkan vertikal sehingga saklar Masuk/Daftar melompat ±88 px saat berganti (`01-masuk-gagal-375`, `01-daftar-375`). | `LoginModal.tsx`/`chat.css`: kartu `align-self: start; margin-top: clamp(48px, 12vh, 120px)`, tidak dipusatkan. | S6 + S2 |
| P3-02 | Aktivitas | Tidak ada keadaan kosong yang diuji; teks bantu waktu `18 Nov, 10.59`. | Tambah `Saat pegawai bekerja, catatannya muncul di sini.` jika kosong. | S1 |
| P3-03 | Evaluasi | Baris terpilih abu (`--active`) sulit dibedakan dari hover (`--raised`). | `.cases li[aria-current]` pakai `--accent-wash` + bar kiri 3 px `--accent`. | S1 |
| P3-04 | Pengaturan > Data | "Lama simpan log aktivitas 90 hari" tampak seperti nilai yang bisa diubah. | Tambah teks `Tidak bisa diubah` (`quiet small`) dan ganti "log" menjadi "catatan". | S6 |
| P3-05 | Pengaturan > Paket | Pil "perkiraan" diulang 6 kali. | Satu keterangan `Semua angka biaya di bawah ini perkiraan.` di atas tabel; pil hanya pada baris yang `priced===false`. | S6 |
| P3-06 | Pengaturan > Notifikasi | "Notifikasi browser: Belum diizinkan" + tombol "Izinkan": status dan aksi bercampur. | Judul `Notifikasi di peramban`, hint dua keadaan: `Belum aktif. Klik Izinkan, lalu pilih Izinkan di jendela peramban.` / `Aktif.` (pil `ok`). | S6 |
| P3-07 | Beranda · Mulai dari sini | "Ganti nama" tampil dua kali (kepala dan baris "Isi nama bisnis"), langkah "Isi nama bisnis" bilang "Sekarang menampilkan Colorbox" padahal sudah. | Saat daftar terbuka, sembunyikan tombol di kepala; teks baris: `Nama bisnis Anda tampil di menu samping.` | S6 |
| P3-08 | Chat | Judul riwayat berbahasa Inggris dari data lama (bukan bug UI); status nama pengguna terpotong "Siti Rahma (CS Lea…" di sidebar. | `App.tsx`: nama `title=` penuh dan `max-width` 160 px 2 baris. | S6 |
| P3-09 | Chat (admin) | Ringkasan berpikir mentah berbahasa Inggris ("I should call taskcomplete with summary.", "User says "tes" (test).") tampil di satu baris untuk admin tanpa penanda. | `ui.tsx` `ThinkingBlock`: awali ringkasan admin dengan tag `Admin` (kelas `.admin-tag`); non-admin tak berubah. | S5 |
| P3-10 | Kemampuan | Skeleton bertahan ≥ 6 detik tanpa teks terlihat; tab "Computer Use" + "Nonaktif" (sudah dijelaskan). | `ui-extra.tsx` `Loading shape="ledger"`: tampilkan `text` secara visual (`.skel-text` di bawah skeleton, 13 px `--muted`). | S6 |
| P3-11 | Marketing | Tombol "Isi contoh Colorbox" mengambang di kanan kepala form tanpa konteks. | Ubah menjadi `btn link` di bawah judul: `Isi contoh Colorbox (untuk mencoba)`. | S1 |
| P3-12 | Dialog (semua) | Fokus awal ke tombol tutup; Esc menutup (baik). Dialog panel tugas 930 px vs dialog lain 637 px. | `ui.tsx` `Dialog`: `autoFocus` ke elemen `[data-autofocus]` bila ada, jika tidak ke kontrol pertama non-tutup. Lebar panel tugas tetap. | S5 |
| P3-13 | Pegawai baru (dialog) | "prompt aset gambar" di deskripsi templat Budi. | `Dialogs.tsx`/data templat: `Merancang arah visual dan menyusun petunjuk untuk membuat gambar.` | S6 |
| P3-14 | CSS | Aturan ganda lintas berkas (`.seg` ×3, `.page-head` ×3, `.ws-agent*` ×2, `.sum-btn` ×3); tambalan beruntun bertanda "FE-1", "Sprint 5 Day 5 QA" di `pages.css`. | S2 dan S1 menggabungkan: satu definisi per selektor di berkas pemiliknya (`styles.css` untuk komponen umum: `.seg`, `.tgl`, `.pill`), hapus duplikat dan komentar tambalan. | S1 + S2 |

---

## 4. Konvensi yang dipakai semua slice

* Kosakata (tetap spec-ux-awam 1c): pegawai (bukan agen) di tampilan biasa; admin tetap "Agen".
* Tombol: satu primer (`btn primary`) per layar/dialog; aksi sekunder `btn soft` atau `btn outline`; tautan `btn link`. Tinggi 36 px desktop, ≥ 40 px di ≤ 640 (sudah ada). Tidak menambah varian baru.
* Radius: `--radius-control` (6) kontrol, `--radius-card` (8) kartu. Spasi: kelipatan `--s-*`.
* Satu scroll per daerah: jangan beri `overflow:auto` pada kontainer yang sudah ada di dalam halaman yang bergulir, kecuali daftar panjang yang jelas (riwayat Chat, `.pp-list`), maksimum satu per layar.
* Kontrol tidak boleh dipotong elipsis jika memuat identitas (nama berkas, produk): bungkus 2 baris.
* Teks teknis hanya di bawah `useAdminMode()` dan diberi `.admin-tag` bila sendirian di barisnya.

---

## 5. Slice kerja (tidak saling menyentuh berkas)

Semua slice: cabang `feat/frontend-prototype`, jangan membuat cabang, jangan commit, jangan menjalankan build mid-flight; setelah semua selesai, Main menjalankan `npm run build` dan uji visual 1280/375 terang/gelap.

| Slice | Berkas yang dimiliki (eksklusif) | Item |
|---|---|---|
| **S1 · Marketing + halaman admin ws** | `src/Marketing.tsx`, `src/ProductPicker.tsx` (baru), `src/ProductPicker.css` (baru), `src/bff.ts`, `src/Platform.tsx`, `src/Uji.tsx`, `src/CS.tsx`, `src/Activity.tsx`, `src/ws-common.tsx`, `src/workspace.css`, `src/admin.css`, `src/panel.css` | P1-01, P1-02, P1-03, P1-07, P2-08 (bagian `.kc-cost::after`), P2-16, P2-17, P2-18, P2-19, P2-21, P2-22, P3-02, P3-03, P3-11, P3-14 (bagian miliknya). `ws-common.tsx`: `ConfirmSwitch` judul `Ganti agen?` → `Ganti pegawai?`. `bff.ts`: hanya mengganti blok `catalog`. |
| **S2 · CSS inti** (tanpa TSX) | `src/styles.css`, `src/chat.css`, `src/pages.css` | P1-04 (CSS), P1-05 (CSS), P2-01 (CSS), P2-02, P2-03, P2-04 (CSS), P2-06, P2-11, P2-12, P2-20, P3-01 (CSS), P3-14 (bagian miliknya). Kontrak kelas ⚑: `.app-row[data-s]`, `.kc-foot .kc-cost`, `.cost-card`, `.admin-tag` didefinisikan di **`styles.css`** (S2) agar bisa dipakai S1, S5, S6; S1 tidak mendefinisikannya ulang di `admin.css`. |
| **S3 · Aplikasi** | `src/connections.tsx`, `src/skills-ui.tsx`, `src/gmail-ui.tsx`, `src/pick-ui.tsx` | P1-04 (TSX: pisah grup, label akun). |
| **S4 · Jadwal & tugas** | `src/Kanban.tsx`, `src/TaskPanel.tsx`, `src/PlanCard.tsx` | P1-05 (TSX), P1-06, P2-07, P2-08, P2-09, P2-10. |
| **S5 · Chat dan Tim** | `src/Chat.tsx`, `src/Group.tsx`, `src/ChatLayout.tsx`, `src/ui.tsx`, `src/LiveSteps.tsx`, `src/rich.tsx` | P2-04 (TSX), P2-05, P3-09, P3-12. `ui.tsx` juga memuat `Dialog` dan `ThinkingBlock`. |
| **S6 · Beranda, Pegawai, Pengaturan, Pengetahuan, shell** | `src/App.tsx`, `src/Dashboard.tsx`, `src/Onboarding.tsx`, `src/TimAnda.tsx`, `src/Agents.tsx`, `src/Dialogs.tsx`, `src/Settings.tsx`, `src/Pengetahuan.tsx`, `src/kb-ui.tsx`, `src/LoginModal.tsx`, `src/ui-extra.tsx`, `src/Summary.tsx` | P1-08, P2-01 (TSX), P2-13, P2-14, P2-15, P3-01 (TSX), P3-04..P3-08, P3-10, P3-13. `Settings.tsx` mengimpor `Switch` dari `ws-common.tsx` (hanya baca). |

Berkas yang tidak diubah siapa pun: `main.tsx`, `router.ts`, `data.tsx`, `session-cache.ts`, `useRun.ts`, `results.ts`, `steps.ts`, `scenarios.ts`, `fixtures.ts`, `Compare.tsx`, `ResultCards.tsx`, `ActionCard.tsx`, `PlanCard.tsx` (kecuali S4 bila perlu), `app-logos*.ts*`, `modelTiers.ts`, `adminMode.ts`, `composerKeys.ts`, `useSmoothText.ts`, `panel.css` (S1).

Urutan dan ketergantungan: S1…S6 dapat berjalan paralel. Satu-satunya kontrak lintas-slice: (a) kelas `.admin-tag` dan pembaruan `.btn.primary:disabled` (S2), dipakai S1/S5/S6 setelah S2 selesai; sampai saat itu tampil tanpa gaya, tidak merusak; (b) ⚑ `kc-cost` dipindah di S4 dan gayanya di S2; (c) `Switch` dari `ws-common.tsx` (sudah ada). Tidak ada slice yang mengedit berkas slice lain.

---

## 6. Matriks verifikasi (dijalankan Main setelah semua slice selesai)

Untuk tiap rute: `#/`, `#/agen`, `#/agen/rian`, `#/agen/rian/ubah`, `#/chat`, `#/chat/rian`, `#/grup`, `#/kanban`, `#/pengetahuan`, `#/aplikasi` (dua tab), `#/pengaturan/{umum,notifikasi,keamanan,paket,data}`, `#/marketing` (5 tahap), `#/cs`, `#/tools`, `#/uji` (3 tab), `#/aktivitas`, plus Masuk/Daftar, dan akun Staf: 1280×800 dan 375×812, terang dan gelap.

Pemeriksaan otomatis yang saya pakai (skrip probe, tersalin dari sesi audit; jalankan lagi di tab):
* `document.documentElement.scrollWidth <= innerWidth` (tidak ada overflow horizontal) pada 375.
* Daftar elemen `overflow:auto|scroll` yang benar-benar bergulir: harus ≤ 1 per layar selain `section.page`; tidak ada yang bergulir pada dua sumbu.
* Elemen dengan `text-overflow: ellipsis` yang terpotong: hanya judul percakapan di sidebar Chat dan ID admin (boleh), tidak ada nama berkas/produk/aksi.
* Target sentuh di 375: semua `button, a, input, select` ≥ 40 px tinggi (kecuali tautan inline dalam kalimat).
* Kontras WCAG: teks < 24 px ≥ 4.5:1 (termasuk tombol nonaktif) di terang dan gelap.
* Tab keyboard Marketing tahap 1: urutan Tujuan → Produk (≤ 3 perhentian) → Kanal → Format → Jumlah → Pengaturan tambahan → Kirim.
* Tidak ada `img.naturalWidth === 0` di halaman manapun.

---

## 7. Indeks tangkapan layar (`docs-kaf/sprint5/audit-ux/`)

| Berkas | Isi |
|---|---|
| `01-masuk-1280-light`, `01-masuk-375-light`, `01-daftar-375-light`, `01-masuk-gagal-375-light` | Masuk, Daftar, galat |
| `02-beranda-{1280-light,1280-dark,375-light}` | Beranda |
| `10-marketing-1280-light`, `11-…-375-light`, `12-…-1280-dark`, `13-…-375-dark`, `14-…-scroll`, `15-…-validasi`, `17-…-chip-fokus` | Marketing tahap 1 (Produk acuan: P1-01/02) |
| `16-marketing-tahap{2,3,4,5}-1280-light`, `18-marketing-tahap5-bawah-1280-light` | Tahap 2 sampai 5 (P1-03, P2-18) |
| `20-tim-*` (rute `#/agen` = tabel "Agen" admin), `21-chat-*`, `22-grup-*` (Tim), `23-kanban-*`, `24-pengetahuan-*`, `25-aplikasi-*` (memuat), `25b-aplikasi-*` (P1-04), `26-pengaturan-*`, `27-cs-*`, `28-tools-*`, `29-uji-*`, `30-aktivitas-*` | Layar utama 1280 dan 375 |
| `31-detail-*`, `32-ubah-*`, `33-atur-dialog-*`, `80-agen-baru-1280-light`, `81-detail-{pekerjaan,keahlian,ingatan}-*` | Detail pegawai, Atur, Pegawai baru |
| `40-chat-topik-*`, `90-drawer-375-light`, `91-riwayat-375-light`, `92-onboarding-1280-light` | Chat dengan percakapan, drawer, riwayat, daftar langkah awal |
| `50-kanban-menu-1280-light`, `51-kanban-panel-1280-light`, `52-kanban-filter-1280-light`, `53-kanban-berulang-1280-light` | Menu kartu, panel hasil, filter, dialog tugas berulang (P1-05, P2-09, P2-10) |
| `60-…63-pengaturan-{notifikasi,keamanan,paket,data}-*`, `70-kemampuan-1280-light`, `71-aplikasi-keahlian-*`, `72-uji-bandingkan-*`, `73-uji-ringkasan-*`, `82-tim-baru-1280-light` | Subhalaman dan dialog |
| `100…106-staf-*` | Akun Staf (tanpa pegawai): Beranda, Tim, Chat, Kanban (P1-06), Pengetahuan, Aplikasi, Pengaturan |
| `110-kanban-1280-dark`, `111-aplikasi-{1280,375}-dark`, `112-grup-1280-dark`, `113-detail-1280-dark` | Mode gelap |

Catatan cakupan jujur: kondisi "galat server" dan unggahan berkas/lampiran Chat tidak dipicu (tidak ada cara aman tanpa mengubah data
atau memutus BFF); dialog "Hapus topik" dan "Putuskan aplikasi" sudah tercatat di bukti sprint sebelumnya (`live-07`, `uji-16`).
Pencarian katalog Indonesia (`jaket`, `kemeja`) mengembalikan nol karena indeks teks BFF berbahasa Inggris dan tanpa awalan;
perbaikan di sisi server (cari awalan `:*`, sinonim Indonesia) dicatat untuk backend di luar lingkup ini, dan rancangan bagian 2
sudah menanganinya dengan saran kata Inggris dan opsi "Pakai tulisan saya".
