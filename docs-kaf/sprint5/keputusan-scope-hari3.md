# Keputusan Scope Hari 3 — Settings, Monitoring, dan Konfigurasi Karyawan

**Ringkasan**

- Sembilan area diminta keputusannya: Skills, Tools, LLM, KB settings, Activity, Task history, Employee logs, Variables, plus Master Template. **Lima sudah ada dan cukup dipakai**, **dua ditunda** (KB settings lanjutan, Employee logs), **satu belum punya konsep** (Variables) dan diselesaikan sebagai tampilan read-only, **satu hanya dokumentasi** (Master Template).
- Prinsip yang dipakai: *reuse* halaman/komponen yang ada; hanya membangun yang punya kontrak backend nyata; yang belum ada ditandai jujur, bukan dibuatkan tombol mati.
- Ukuran: **S** = ≤ 1 hari kerja FE tanpa endpoint baru; **M/L** = butuh kontrak/schema Backend. Tidak ada item **L** yang diambil di sprint ini.
- **Ditunda bukan gagal.** Setiap penundaan di bawah adalah keputusan sadar dengan alasan, bukti, dan pemicu untuk dibuka kembali — bukan pekerjaan yang terlewat.

Path repo relatif terhadap root `pegawai-ai-backend`, kode pada `feat/frontend-prototype` (HEAD `8d05aaf`).

---

## 1. Cara membaca tabel

| Status | Arti | Tindakan FE |
|---|---|---|
| **ADA** | Kontrak backend + UI sudah jalan | Pakai/rapikan copy; tidak ada pembangunan |
| **RINGAN SEKARANG** | Bisa diselesaikan ≤ 1 hari dengan data yang sudah ada | Bangun di sprint ini |
| **TUNDA** | Butuh kontrak/schema/desain yang belum ada, atau risikonya belum termitigasi | Catat sebagai deferral; jangan tampilkan seolah berfungsi |
| **TIDAK ADA KONSEP** | Tidak ada di kode maupun produk | Definisikan dulu bersama Backend; jangan invent |

---

## 2. Tabel keputusan

| # | Area | Kondisi kode hari ini | Keputusan | Alasan | Bukti | Ukuran / dependensi |
|---|---|---|---|---|---|---|
| 1 | **Skills** | Ada: sakelar per agen, matriks lintas agen, validasi, item terlarang disembunyikan | **ADA — pakai, tanpa build** | Kontrak nyata, state dibaca ulang dari gateway, deny-list tidak bisa dihidupkan lewat UI | `frontend/src/skills-ui.tsx:12-63,66-123`; `bff/bff/main.py:308-322`; `bff/bff/apps.py:291-299,327-359` | 0 |
| 2 | **Tools** | Ada, read-only, menampilkan alasan tool disembunyikan | **ADA — pertahankan read-only** | Jalur menulis sudah ada di Skills; dua jalur tulis untuk objek yang sama akan membingungkan dan menambah risiko | `frontend/src/Platform.tsx:13-120`; `bff/bff/main.py:265`; `bff/bff/apps.py:292` | 0 (perbaikan copy opsional **S**) |
| 3 | **LLM selection** | Ada dua UX: pemilih model/effort dan tier Hemat/Seimbang/Teliti; validasi provider | **ADA — pakai, jangan diperluas** | Temperature (diminta CRE-01 0,4–0,6) tidak punya field BFF; tier menduplikasi tabel harga dan rawan melenceng | `frontend/src/ui-extra.tsx:24-120`; `frontend/src/Dialogs.tsx:413-532`; `bff/bff/settings.py:23,153-160`; `frontend/src/modelTiers.ts` | 0; temperature = **M**, dep Backend |
| 4 | **KB upload settings** | Upload berjalan (berkas/link/Drive, status per item, error terlihat). **Setelan** (chunk, batas, retensi, binding per agen) tidak ada — semua konstanta hardcoded | **TUNDA setelan; pertahankan upload** | Tidak ada schema per-agen maupun kolom setelan; item KB terikat per pengguna dan dilampirkan per pesan, bukan per karyawan | `frontend/src/Pengetahuan.tsx:42,117,226`; `frontend/src/kb-ui.tsx:12-135`; `bff/bff/kb.py:19-24`; `bff/migrations/011_knowledge_base.sql` | **L**, dep schema Backend |
| 5 | **Activity monitoring** | Ada: filter, paging, cakupan panel, retensi 90 hari | **ADA — pakai** | Sudah terhubung, tidak perlu desain baru | `frontend/src/Activity.tsx:73-102`; `bff/bff/main.py:991-1011`; `bff/bff/settings.py:16` | 0 |
| 6 | **Task history** | Ada: papan Kanban, panel detail tugas, riwayat run per agen | **ADA — pakai** | Menjawab "apa yang sudah dikerjakan" tanpa log mentah | `bff/bff/main.py:959-986`; `frontend/src/Agents.tsx:216`; `frontend/src/TaskPanel.tsx`; `frontend/src/Kanban.tsx` | 0 |
| 7 | **AI Employee logs** | Tidak ada endpoint. Log hanya berkas di `profiles/<slug>/logs/agent.log` dan `errors.log` | **TUNDA** | Log mentah memuat prompt, payload tool, dan data pelanggan; `redact.py` ada tetapi belum ada kontrak redaksi untuk endpoint log. Menampilkannya = risiko kebocoran + beban dukungan | Tidak ada route log di `bff/bff/main.py`; berkas `logs/*` per profil (inventaris di `konfigurasi-hermes-fe.md` §2) | **M**, dep kontrak redaksi Backend |
| 8 | **Variables** | Tidak ada konsep `variables` di `bff/` maupun `frontend/src` (grep kosong). Yang nyata: 7 field DB yang bisa diedit + core terlindungi | **RINGAN SEKARANG (tampilan) + definisi Backend** | Kode sudah memisahkan editable vs core; pengguna belum bisa melihatnya. Jangan buat model data "variables" baru | `bff/bff/bots.py:211-247`; `bff/bff/harden.py:27,76-80`; `konfigurasi-hermes-fe.md` §4 | **S** (blok read-only); model variabel = **tunda** |
| 9 | **Master Template** | 11 komponen berupa spesifikasi prosa; tidak ada tabel/editor; `CRE-01` tidak diimpor runtime | **DOKUMENTASI SAJA** | Schema 11 field terstruktur butuh tabel + editor + validasi (**L**), di luar sprint; memaksanya menghasilkan form kosong | `docs-kaf/sprint5/TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md:10-108`; `konfigurasi-hermes-fe.md` §5 | **S** (peta read-only); schema = **L**, sprint berikut |

---

## 3. Ringkasan keputusan

| Keputusan | Item |
|---|---|
| **Pakai apa adanya** | Skills, Tools (read-only), LLM, Activity, Task history |
| **Bangun ringan sekarang** | Blok "dikelola sistem vs bisa Anda ubah" + peta 11 komponen read-only + copy yang jujur |
| **Tunda dengan alasan** | KB settings lanjutan, Employee logs, editor `SKILL.md`, schema Master Template, model "Variables", temperature LLM |
| **Jangan bangun sama sekali di sprint ini** | Editor `AGENTS.md`, editor `config.yaml` di luar toolset, penulisan `.env`, UI memori penuh, renderer Telegram kustom |

---

## 4. Rincian keputusan yang paling sering disalahpahami

### 4.1 "Skills" di UI bukan `SKILL.md`

Yang dihidupkan adalah **toolset** (`platform_toolsets.api_server`), bukan dokumen `skills/**/SKILL.md`. Karena itu:

- Label UI sebaiknya menjelaskan kemampuan, bukan berkas: "Keahlian" sudah tepat, tetapi tooltip/deskripsi harus menyebut "kemampuan yang bisa dipakai agen", bukan "dokumen".
- Menambah/mengedit `SKILL.md` dari UI **tidak** diusulkan: 44+ dokumen di satu profil, tanpa versioning, dan agen sendiri bisa menulisnya.

### 4.2 KB: upload tetap, "settings" ditunda

- Yang ada: unggah berkas (TXT/MD/CSV/PDF/DOCX ≤ 10 MB), simpan link, Drive, status per item, pesan gagal yang terlihat (`frontend/src/Pengetahuan.tsx:42,117`; `frontend/src/kb-ui.tsx:12-135`).
- Yang tidak ada: ukuran chunk, jumlah chunk per run, retensi, kuota per agen, binding KB ke karyawan. Semuanya konstanta di `bff/bff/kb.py:19-24`.
- **Jangan** menampilkan slider "ukuran chunk" atau "retensi" — tidak ada tempat menyimpannya. Kalau klien bertanya, jawab: "Belum tersedia; saat ini sistem memilih ukuran otomatis."

### 4.3 Employee logs: kenapa sengaja tidak ditampilkan

Tiga alasan yang harus dipertahankan sampai ada kontrak:

1. **Kebocoran:** log memuat prompt sistem, potongan SOUL, payload tool, dan kadang data pelanggan.
2. **Kebingungan:** pengguna non-teknis membaca stack trace sebagai "sistem rusak".
3. **Beban dukungan:** setiap baris log menjadi tiket.

Alternatif yang aman sekarang: Activity (sudah ada) + status run + pesan error yang sudah diterjemahkan BFF. Jika nanti dibutuhkan, bentuk yang disarankan adalah **"kesalahan terbaru" terkurasi** (maks. 20 baris, teredaksi, per agen), bukan tail log.

### 4.4 Variables: definisi yang harus disepakati

Kata "Variables" tidak ada di kode. Ada dua kemungkinan arti, dan keduanya harus dijawab Backend Hari 3:

| Tafsir | Kenyataan | Sikap FE |
|---|---|---|
| Field yang bisa diedit klien | 7 field DB (`bots.py:211`) | Tampilkan sebagai "bisa Anda ubah" |
| Variabel `.env` / rahasia | Kredensial per profil; Hermes menyebutnya kredensial, bukan memori (`memory.md:88`) | **Jangan pernah** masuk UI klien |

Sampai ada jawaban, FE memakai istilah **"Pengaturan yang bisa Anda ubah"** dan tidak memakai kata "variabel".

### 4.5 Master Template: dokumentasi, bukan fitur

Peta 11 komponen → konfigurasi ada di `konfigurasi-hermes-fe.md` §5. FE hanya boleh menampilkan **status terisi/tidak** secara read-only. Membuat form 11 bagian tanpa schema akan menghasilkan data yang tidak dibaca runtime — lebih buruk daripada tidak ada.

---

## 5. "Ditunda" bukan "gagal"

| Item ditunda | Yang tetap diselesaikan | Bukti penutupan |
|---|---|---|
| KB settings | Upload + error handling + halaman Pengetahuan | `Pengetahuan.tsx`, `kb-ui.tsx`; QA Hari 5 menguji upload, bukan setelan |
| Employee logs | Activity + status run + pesan error manusiawi | `Activity.tsx`; `main.py:991-1011` |
| Schema Master Template | Dokumen peta + keputusan "dokumentasi saja" | `konfigurasi-hermes-fe.md` §5; dokumen ini |
| Model "Variables" | Blok read-only editable vs core | `konfigurasi-hermes-fe.md` §4 |
| Memori (UI penuh) | Rencana UX + label "Direncanakan" | `telegram-dan-memori-ux.md` §7 |
| Renderer Telegram kustom | Analisis + rekomendasi native | `telegram-dan-memori-ux.md` §2-4 |

Aturan pelaporan yang harus dipakai di Hari 5:

1. Tulis **"Ditunda (keputusan Hari 3)"** untuk item di atas — bukan "gagal", bukan "selesai".
2. Jangan menambahkan tombol/placeholder yang terlihat aktif untuk fitur yang ditunda.
3. Kalau ada yang bertanya "kok tidak ada?", jawab dengan alasan + pemicu pembukaan di §6.

---

## 6. Pemicu membuka kembali keputusan

| Item | Buka kembali jika… | Prasyarat minimum |
|---|---|---|
| KB settings | Klien butuh kuota/retensi per agen, atau ada keluhan kualitas pencarian | Schema setelan + endpoint + validasi Backend |
| Employee logs | Ada kebutuhan dukungan nyata yang tidak terjawab Activity | Kontrak redaksi + endpoint terkurasi + uji kebocoran |
| Memori (baca/hapus) | Blueprint tenant isolation disepakati (Hari 4 Backend) | Kontrak `GET/DELETE` + izin owner/admin + audit |
| Schema Master Template | Backend mulai menyimpan role terstruktur | Kontrak read-only dulu; editor belakangan |
| Temperature LLM | Ada bukti kualitas yang membutuhkan nilai tetap per peran | Field `RUN_FIELDS` + validasi + uji regresi |
| Renderer Telegram | Ada keluhan nyata bahwa tabel tidak terbaca **setelah** uji sampel live | Sampel live + keputusan Backend `rich_messages` |

---

## 7. Dampak ke QA Hari 5

| Diuji | Tidak diuji (dan boleh disebut sebagai deferral) |
|---|---|
| Sakelar Skills per agen (simpan → muat ulang → state benar) | Setelan KB (chunk/retensi/kuota) |
| PATCH bot: persona/warna/model; 403 untuk field builtin | Edit `SKILL.md`, `AGENTS.md`, `config.yaml` |
| Baca Activity + Task history + riwayat run | Log mentah karyawan |
| Batas editable vs core terlihat di UI | Schema Master Template / form 11 bagian |
| Upload KB + link + error terlihat | Hapus/kelola memori jangka panjang |

Bukti QA yang harus disimpan: request/response tersanitasi untuk PATCH bot dan PUT skills, plus tangkapan layar pesan 403/400. Jangan mencatat nilai rahasia.

---

## 8. Rujukan

- `docs-kaf/sprint5/konfigurasi-hermes-fe.md` — inventaris Hermes, kontrak editable/core, peta Master Template.
- `docs-kaf/sprint5/TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md` — 11 komponen wajib.
- Kode: `bff/bff/{bots,apps,settings,harden,kb}.py`, `bff/bff/main.py`; `frontend/src/{skills-ui,Platform,ui-extra,Dialogs,Pengetahuan,kb-ui,Activity,Agents,TaskPanel}.tsx`.
- ClickUp: Hari 3 `z8xxqwh79u`; induk `z8xxqwh792`.
