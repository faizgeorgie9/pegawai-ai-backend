# Konfigurasi Hermes dari Sisi Frontend (Hari 2–3)

**Ringkasan**

- Satu-satunya berkas identitas per karyawan AI adalah **`SOUL.md`** (huruf besar; Linux case-sensitive). `user.md` dan `skill.md` yang disebut di ClickUp **bukan nama berkas** di Hermes terpasang: yang ada adalah `memories/USER.md` (memori profil pengguna, ditulis agen) dan `skills/<kategori>/<nama>/SKILL.md` (dokumen pengetahuan, bukan konfigurasi karyawan).
- **"Keahlian" di UI ≠ `SKILL.md`.** Yang dihidupkan/dimatikan FE adalah **toolset** Hermes (`platform_toolsets.api_server`). `SKILL.md` adalah dokumen yang dibaca agen sesuai kebutuhan dan tidak punya kontrak BFF.
- **`AGENTS.md` bukan berkas karyawan.** Ia konteks workspace/git-root yang dipakai bersama semua profil; tidak bisa menyimpan aturan per karyawan.
- FE hari ini hanya mengubah 7 field di tabel `bots` (+ menulis ulang `SOUL.md` untuk bot non-builtin). Core sudah dilindungi kode: SOUL builtin 403, deny-list tidak pernah ditampilkan/ditulis, `approvals.mode=manual` dipaksa.
- **Master Template 11 komponen masih spesifikasi penulisan prosa**, bukan schema. Belum ada tabel/editor terstruktur; jangan menjanjikan editor 11 bagian.
- Verifikasi dilakukan pada Hermes terpasang `0.22.5+3201.ga4994d4` di `%LOCALAPPDATA%\hermes` dan kode repo pada `feat/frontend-prototype` (HEAD `8d05aaf`).

Semua path repo di bawah relatif terhadap root `pegawai-ai-backend`. Path Hermes memakai `%LOCALAPPDATA%\hermes` (Windows lokal; di VPS Linux letaknya di home user service).

---

## 1. Metode dan batas verifikasi

| Aspek | Yang dilakukan | Batas |
|---|---|---|
| Hermes terpasang | Daftar berkas & direktori langsung di `%LOCALAPPDATA%\hermes`; baca `config.yaml` profil, `website/docs/**`, dan kode paket (`agent/prompt_builder.py`, `plugins/platforms/telegram/adapter.py`, `gateway/platforms/helpers.py`) | Tidak menjalankan agen; tidak mengubah berkas Hermes |
| Repo | Baca `bff/bff/{bots,apps,settings,harden,bridge,main}.py`, migrasi, dan komponen FE | BFF test tidak dijalankan di sesi audit |
| Rahasia | Tidak membuka/menyalin `bff/.env`, `frontend/.env.local`, `.env` profil | — |

---

## 2. Inventaris berkas Hermes yang benar-benar ada

| Nama di ClickUp | Berkas/direktori aktual | Cakupan | Isi/fungsi (terverifikasi) | Ada sekarang | Dikelola FE |
|---|---|---|---|---|---|
| `soul.md` | **`SOUL.md`** di `HERMES_HOME` dan `profiles/<slug>/SOUL.md` | **per profil (per karyawan)** | Slot identitas #1, disuntik verbatim setelah pemindaian injection; hanya dibaca dari `HERMES_HOME`, tidak dari cwd (`agent/prompt_builder.py:1513-1559`, `:1532` memakai literal `SOUL.md`) | Root + **11 profil** (`budi, coder, diana, hendra, mira, reza, rian, sari, siti, vino, wulan`) | ✅ bot pengguna (BFF menulis ulang seluruh berkas); ❌ builtin |
| `user.md` | **`memories/USER.md`** | per profil | Profil pengguna (batas **1.375 karakter**), snapshot dibekukan saat sesi mulai, ditulis agen lewat tool `memory` target `user` (`website/docs/user-guide/features/memory.md:17-18`) | **Hanya root** (`%LOCALAPPDATA%\hermes\memories\USER.md`); **tidak ada satu pun profil yang punya** | ❌ tidak ada API/UI |
| — (catatan agen) | **`memories/MEMORY.md`** | per profil | Catatan agen sendiri (batas **2.200 karakter**), ditulis tool `memory` (`memory.md:17-18,178-183`) | Root + sebagian profil (mis. `profiles/rian/memories/MEMORY.md`) | ❌ |
| `skill.md` | **`skills/<kategori>/<nama>/SKILL.md`** | per profil | Dokumen pengetahuan on-demand, slash command; agen dapat membuat/mengeditnya (`memory.md:88` menyarankan skill untuk fakta yang selalu dibutuhkan) | Ya (mis. `profiles/rian/skills/` 19 entri, `budi` 16) | ❌ (dan sebaiknya tetap ❌) |
| `agents.md` | **`AGENTS.md`** / `agents.md` (+ `.hermes.md`, `CLAUDE.md`) | **workspace/git-root, dibagi semua profil** | Instruksi proyek digabung dari git-root → cwd (`prompt_builder.py:1590-1705`); varian huruf kecil **diterima** sebagai fallback (`:1605`) | Hanya berkas repo/workspace (mis. `hermes-agent/AGENTS.md`) | n/a — bukan per karyawan |
| — (konfigurasi) | **`config.yaml`** | per profil | `model.default/provider`, `platform_toolsets`, `approvals.mode`, `mcp_servers` | Semua profil | Sebagian: toolset (`apps.py`), model/effort (DB → per run), approvals dikunci |
| — (meta Desktop) | `profile.yaml` | per profil | Metadata UI Desktop saja (warna/bentuk/judul/grup) | Semua profil | ❌ BFF tidak membacanya |
| — (runtime) | `skills/`, `logs/agent.log`, `logs/errors.log`, `state.db` | per profil | Dokumen skill; log runtime; penyimpanan sesi | Ya | ❌ tidak ada endpoint |

**Konsekuensi yang harus dipatuhi implementasi:**

1. **Jangan pakai nama huruf kecil di VPS.** `prompt_builder.py:1532` membentuk path literal `SOUL.md`; `soul.md` huruf kecil tidak dimuat di Linux. `agents.md` huruf kecil **boleh** (fallback eksplisit di `:1605`), tetapi `SOUL.md` tidak.
2. **`USER.md` tidak ada di profil mana pun** — jangan tampilkan meter kapasitas 1.375 karakter seolah berisi data. Kalau nanti ditampilkan, ambil ukuran sebenarnya dari berkas.
3. **`AGENTS.md` tidak bisa menjadi tempat aturan per karyawan.** Semua profil dalam satu cwd membacanya; aturan khusus karyawan harus masuk `SOUL.md` (atau field DB baru).
4. **`MEMORY.md`/`USER.md` adalah memori, bukan setelan.** Memotong/mengosongkannya adalah operasi destruktif (lihat `telegram-dan-memori-ux.md`), bukan "simpan konfigurasi".

### 2.1 Tiga koreksi istilah yang harus dipakai di UI dan dokumen

| Istilah ClickUp | Istilah yang benar | Bukti |
|---|---|---|
| "skill.md" (berkas karyawan) | **Dokumen skill** `skills/**/SKILL.md`; yang dikelola UI adalah **toolset** | `bff/bff/apps.py:291-299,324-359`; `frontend/src/skills-ui.tsx:12-63` |
| "user.md" | **Memori profil pengguna** `memories/USER.md` | `memory.md:17-18`; hanya ada di root home |
| "Variables" | **Field yang bisa diedit klien** (persona/warna/model), bukan `.env` | Tidak ada konsep `variables` di `bff/` maupun `frontend/src` (grep); Hermes menyebut variabel `.env` sebagai kredensial/setelan, **bukan** memori (`memory.md:88`) |

---

## 3. Yang dikelola FE hari ini (kontrak nyata)

| Datastore | Baca | Tulis | Batas yang sudah ditegakkan |
|---|---|---|---|
| `SOUL.md` per profil | Tidak langsung; hanya hash di tabel versi (`bff/bff/versions.py:57-86`), tanpa endpoint | Ditulis saat bot dibuat (`bots.py:170`) dan saat edit bot non-builtin (`bots.py:255-256`) | Builtin → **403** (`bots.py:214-223`) |
| Baris `bots` (name, role, team, color, persona, model, provider, reasoning_effort) | `GET /api/bots`, `GET /api/bots/{id}` (`main.py:245,255`) | `PATCH /api/bots/{id}` (`main.py:260`) | `EDITABLE` (`bots.py:211`); builtin hanya `color` + `RUN_FIELDS` (`bots.py:218-220`) |
| `config.yaml` → toolset | `GET /api/tools`, `GET /api/agents/{slug}/skills`, `GET /api/skills` (`main.py:265,308,313`) | `PUT /api/agents/{slug}/skills` (`main.py:318`) | `HIDDEN = harden.DENY ∪ {clarify, discord, …}` (`apps.py:292`); `TECHNICAL` hanya mode admin (`apps.py:293`); deny-list tidak pernah masuk daftar baru (`apps.py:327-328`) |
| Model & effort | `GET /api/models` (`settings.py:112-151`) | Disimpan di DB, dikirim per run (`settings.py:23`); divalidasi `check_model` (`settings.py:153-160`) | Hanya provider yang terautentikasi di gateway |
| `approvals` | `GET /api/settings/security` (`main.py:555`) | Tidak ada | Dipaksa `manual` (`harden.py:76-80`) |
| Setelan workspace (nama perusahaan, bahasa, zona waktu, notifikasi) | `GET /api/settings` (`main.py:545`) | `PATCH /api/settings` (`main.py:550`) | `settings.py:19-22,55-90`; bukan per karyawan |
| `memories/MEMORY.md`+`USER.md`, `skills/**/SKILL.md`, `logs/*` | Tidak ada | Tidak ada | Tidak ada kontrak BFF sama sekali |

**Catatan penting:** `GET /bots/{id}` mengembalikan `persona`/`about`, **bukan** isi SOUL efektif. Untuk bot builtin, `persona` jatuh ke satu baris `TEMPLATES` (`bots.py:71-75`), sedangkan SOUL sebenarnya 2,4–2,7 KB. Jadi UI saat ini tidak bisa menunjukkan "apa yang sebenarnya diperintahkan ke karyawan".

---

## 4. Kontrak: yang boleh diedit klien vs core yang dilindungi

### 4.1 Boleh diedit klien (mode pengguna biasa)

| Field | Batas | Catatan UI |
|---|---|---|
| `persona` | ≤ 2.000 karakter, wajib (`bots.py:239-241`) | Mengganti template: `template` di-null-kan (`bots.py:251-252`) |
| `color` | Salah satu `COLORS` (`bots.py:240-243`) | Aman untuk builtin |
| `model`, `provider`, `reasoning_effort` | `RUN_FIELDS` (`settings.py:23`); provider harus terautentikasi (`settings.py:153-160`) | Aman untuk builtin |
| `name`, `role`, `team` | Hanya bot **non-builtin** (`bots.py:218-220`) | Mengubah nama ikut menulis ulang SOUL |

### 4.2 Core yang dilindungi (tidak boleh diedit klien)

| Objek | Mekanisme perlindungan | Bukti |
|---|---|---|
| SOUL/identitas bot builtin | 403 saat PATCH field selain warna/model | `bots.py:214-223` |
| Aturan bersama (`HOUSE_SOUL`: sebut "Colorbox", balasan < 60 kata, `[SILENT]`, maks. 2 revisi) | Disuntik BFF saat membuat SOUL; tidak dapat diubah lewat API | `bots.py:28-35,137-144` |
| Tool berbahaya (`terminal`, `file`, `code_execution`, `browser`, `computer_use`, `cronjob`, `delegation`) | `harden.DENY`; tidak pernah ditampilkan atau ditulis | `harden.py:27`; `apps.py:292,327-328` |
| `approvals.mode` | Dipaksa `manual` setiap hardening | `harden.py:76-80` |
| Kredensial (`.env` profil, API key, token OAuth) | Tidak pernah dibaca/ditampilkan FE | `bots.py:122-127` hanya mengganti baris `API_SERVER_KEY` |
| Memori & log profil | Tidak ada endpoint | grep `memories\|MEMORY.md` di `bff/` = kosong |

### 4.3 Aturan produk untuk FE

1. Panel karyawan harus menyatakan status: **"Dikelola sistem"** (builtin) vs **"Bisa Anda ubah"** — data sudah tersedia dari `builtin` (`frontend/src/Agents.tsx:67,175,292`).
2. Jangan tampilkan editor untuk field yang tidak ada di `EDITABLE`. Kontrol mati tanpa alasan = bug persepsi.
3. Semua perubahan yang memicu tulis SOUL harus diberi konsekuensi jelas: "Persona baru berlaku pada percakapan berikutnya".
4. **Belum aman mengklaim "core tidak bisa diubah" selama otorisasi belum ditegakkan:** siapa pun yang memegang kunci proxy bisa `PATCH` model bot builtin karena middleware jatuh ke `default` (`main.py:53-68`). Ini temuan Backend, tercatat di `catatan-untuk-backend.md` #1.

---

## 5. Master Template (11 komponen) → konfigurasi

Sumber: `docs-kaf/sprint5/TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md:10-108` (11 bagian) dan contoh kerja `docs-kaf/sprint5/CRE-01_CONTENT_STRATEGIST.md`.

| # | Komponen template | Mendarat di | Terstruktur? |
|---|---|---|---|
| 1 | Scope of Work & Boundaries | `SOUL.md` (prosa) | ❌ |
| 2 | Persona, Language & Tone of Voice | `SOUL.md` + field `persona` | ❌ prosa |
| 3 | Triggers & Use Cases | `SOUL.md` | ❌ |
| 4 | Modular Skills & Capabilities | **Dua objek berbeda:** toolset `platform_toolsets.api_server` dan dokumen `skills/**/SKILL.md` | Toolset ✅; dokumen ❌ |
| 5 | SOP & Task Execution Pattern | `SOUL.md` | ❌ |
| 6 | Operating Rules & Prohibitions | `SOUL.md` | ❌ |
| 7 | Tools, Integrations & Permissions | `harden.DENY`, toolset, `approvals.mode` | ✅ ditegakkan |
| 8 | Knowledge Base & Memory Needs | `kb_items`/`kb_chunks` (per pengguna) + `memories/MEMORY.md`+`USER.md` (per profil) | KB ✅; memori ❌ |
| 9 | Input & Expected Output Standards | `SOUL.md` | ❌ |
| 10 | Approval & Escalation Rules | `approvals.mode=manual` + kartu aksi (`frontend/src/ActionCard.tsx`) + tool `clarify` | ✅ kasar (tanpa L1/L2/L3) |
| 11 | Model Recommendation & KPIs | `bots.model/provider/reasoning_effort`; KPI hanya rubrik evaluasi (`evaluations`) | Model ✅; KPI ❌ |

**Kesimpulan:** "Master Template" saat ini = **panduan menulis `SOUL.md`**, bukan schema yang bisa disimpan. `CRE-01` tidak diimpor ke runtime mana pun. Schema 11 field terstruktur butuh tabel + editor baru (ukuran **L**) dan berada di luar Sprint 5.

**Yang bisa dilakukan FE sekarang (S):** tampilkan peta "komponen mana yang terisi" secara read-only di halaman detail, dengan label jujur: komponen 1–3, 5, 6, 9 = "tertulis di identitas"; 4, 7, 10, 11 = "diatur sistem"; 8 = "sebagian". Jangan membuat form 11 bagian.

---

## 6. Pertanyaan terbuka untuk Backend Hari 3

| # | Pertanyaan | Kenapa penting | Usulan FE |
|---|---|---|---|
| 1 | **Apa source of truth identitas:** `SOUL.md` atau kolom DB? Saat ini keduanya ditulis, tetapi DB hanya menyimpan `persona`, bukan SOUL efektif. | Tanpa jawaban, UI tidak bisa menampilkan "apa yang diperintahkan" dan edit bisa tampak tidak berefek. | Tetapkan DB = input, `SOUL.md` = hasil generate satu arah; sediakan `GET /api/bots/{id}/config` (SOUL teredaksi + toolset + model). |
| 2 | **Apakah klien boleh membaca SOUL efektif?** | Membangun kepercayaan dan menjelaskan kenapa perilaku berbeda; juga menghindari dukungan "kok agennya begini". | Endpoint read-only, redaksi bagian internal, khusus pemilik bot. |
| 3 | **`USER.md` per profil:** siapa pemiliknya kalau satu profil dipakai beberapa anggota workspace? | Hermes hanya mendukung satu `USER.md` per profil; ini bertabrakan dengan tenant isolation. | Jangan tampilkan sebelum model kepemilikan disepakati; catat sebagai risiko di blueprint memori. |
| 4 | **Kontrak memori:** baca ukuran/isi, hapus per store, audit. | Hari 4 hanya plan; tanpa kontrak, UI memori tidak boleh dibangun. | `GET/DELETE /api/agents/{slug}/memory?store=memory\|user`, khusus owner/admin, konfirmasi berlapis. |
| 5 | **Apakah `SKILL.md` akan pernah dikelola?** | 44+ dokumen di `profiles/rian`; membuka editor berarti membuka permukaan serangan & beban dukungan. | **Tidak** di Sprint 5; kalau perlu, hanya baca daftar nama. |
| 6 | **Apakah "Variables" berarti `.env` per karyawan?** | Di Hermes, variabel `.env` = kredensial, bukan setelan klien. | Tegaskan: klien hanya mengedit persona/warna/model; kredensial tidak pernah masuk UI. |
| 7 | **`AGENTS.md`:** apakah ada kebutuhan aturan per workspace yang berbeda per klien? | Semua profil di satu cwd berbagi `AGENTS.md`; salah pakai = aturan klien A bocor ke klien B. | Jika perlu, jadikan field DB/SOUL per karyawan, bukan berkas workspace. |
| 8 | **Schema Master Template:** apakah Backend Hari 3 akan membuat tabel role terstruktur? | Menentukan apakah FE hanya menampilkan peta atau perlu editor. | Jika ya: minta kontrak read-only dulu; editor 11 bagian ditunda. |
| 9 | **Case sensitivity & deploy:** siapa yang menjamin `SOUL.md` huruf besar di VPS? | `soul.md` huruf kecil tidak dimuat di Linux; gejalanya "agen kehilangan identitas" tanpa error. | Tambahkan assertion di skrip deploy/test: berkas ada dengan nama tepat. |
| 10 | **Trap template:** `TEMPLATES` berisi 10 peran (`bots.py:16-27`) tetapi `bots/souls/` hanya 5 (hendra, siti, budi, diana, rian). | Menambah baris builtin untuk 5 peran lain akan gagal di `_soul` (`bots.py:139`) dan `--clone-from` (`bots.py:168`). | Batasi builtin ke 5 yang punya SOUL, atau lengkapi berkas dulu. |
| 11 | **Otorisasi tulis konfigurasi:** kapan `PATCH /bots` mewajibkan JWT + role? | "Protected core" hanya nyata jika penulisnya terautentikasi. | Middleware menolak token hilang/kedaluwarsa untuk router `api`; role dicek untuk field sensitif. |

---

## 7. Rekomendasi urutan kerja FE (Hari 3)

1. **Sekarang, tanpa backend baru:** blok "Dikelola sistem vs bisa Anda ubah" di detail karyawan; perbaiki copy "Keahlian" agar tidak menyiratkan dokumen skill; tambah penjelasan "berlaku pada percakapan berikutnya" saat menyimpan persona.
2. **Sekarang, bergantung Backend Hari 3:** `GET /bots/{id}/config` read-only (SOUL teredaksi + toolset + model) — setelah itu baru pertimbangkan tampilan identitas lengkap.
3. **Tunda:** editor `SKILL.md`, editor memori, schema 11 komponen, editor `AGENTS.md`.
4. **Jangan bangun:** apa pun yang menulis `.env`, `config.yaml` di luar toolset, atau `approvals`.

---

## 8. Rujukan

- Hermes terpasang: `agent/prompt_builder.py:1513-1559,1590-1705`; `website/docs/user-guide/features/memory.md:17-18,88,178-183`; `config.yaml` profil `rian`.
- Repo: `bff/bff/bots.py:16-35,71-75,137-144,211-256`; `bff/bff/apps.py:291-299,324-359`; `bff/bff/harden.py:27,76-80`; `bff/bff/settings.py:19-23,112-160`; `bff/bff/versions.py:57-86`; `frontend/src/Agents.tsx:67,175,210-216,292`; `frontend/src/skills-ui.tsx:12-63`.
- Dokumen internal: `docs-kaf/sprint5/TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md`; `docs-kaf/sprint5/CRE-01_CONTENT_STRATEGIST.md`; `docs-kaf/bff-spec.md:149`.
- ClickUp: induk `z8xxqwh792` (Hari 2 `z8xxqwh79t`, Hari 3 `z8xxqwh79u`).
