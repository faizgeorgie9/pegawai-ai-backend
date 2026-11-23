# Catatan untuk Backend (Faiz) — Temuan Milik Backend

**Ringkasan**

- Semua temuan di bawah **milik Backend**; FE tidak memperbaikinya dan tidak boleh mengklaimnya selesai. Path relatif terhadap root `pegawai-ai-backend`, kode pada `feat/frontend-prototype` (HEAD `8d05aaf`).
- **P0 (harus sebelum demo dipercaya):** JWT tidak ditegakkan di `/api/*` sehingga pemanggil tanpa token mendapat tenant `default` (= admin); kredensial VPS dan kunci BFF tertulis di skrip repo (**rotate**); deploy mengunggah `frontend/dist` tanpa build.
- **P1:** identitas pengguna tidak sampai ke tool MCP (`_user()` selalu `default`), akun demo selain admin kosong, JWT memakai kunci proxy yang sama, bukti Hari 1 tidak cocok dengan kode, `app.pegawaiAI.com` tidak punya DNS/sertifikat.
- **P2:** webhook WhatsApp tanpa autentikasi dan selalu tenant `default`; register terbuka tanpa verifikasi/rate limit; logout tidak menginvalidasi apa pun; trap template 10 vs 5 SOUL.
- Setiap temuan diberi **hari ClickUp Backend** tujuan. Tidak ada nilai rahasia di dokumen ini.

---

## 1. Tabel prioritas

| # | Temuan | Bukti | Dampak | Hari BE |
|---|---|---|---|---|
| 1 | JWT **tidak** ditegakkan di `/api/*`; token hilang/rusak jatuh ke `user_id="default"` | `bff/bff/main.py:49,53-68,98-100` | Siapa pun yang lewat nginx (kunci disuntik untuk semua pengunjung) membaca data admin; `PATCH /bots` bisa mengubah model bot builtin | **Hari 1** (auth) + **Hari 5** (QA) |
| 2 | Tool MCP selalu berjalan sebagai `default` | `bff/bff/bridge.py:47-49`; `bff/bff/main.py:98-100` | Drive/Gmail/KB/task tool menulis ke tenant admin meski pengguna login sebagai owner/CS | **Hari 2** (MCP privileges) + Hari 1 |
| 3 | Hanya `default` yang punya agen; akun demo lain kosong | `bff/migrations/001_init.sql:17-27`; `bff/migrations/020_auth_users.sql:27-32`; `bff/bff/bots.py:59,65` | Login owner/CS/marketing menampilkan workspace kosong; demo "multi-user" tidak terbukti | **Hari 1** (login/demo) + Hari 5 |
| 4 | Kunci JWT = `BFF_API_KEY` (kunci proxy); `PyJWT` tidak dideklarasikan | `bff/bff/auth.py:9,17-19,38-49`; `bff/pyproject.toml:6-18`; `bff/uv.lock:384,667` | Rotasi kunci proxy mematikan semua sesi; instalasi bisa pecah bila `mcp` berhenti membawa PyJWT | **Hari 1** |
| 5 | Dokumen bukti Hari 1 tidak cocok dengan kode | `Sprint5_Day1_VPS_Demo_Auth_and_Security_Tiers_Evidence.md:83,86,112` vs `bff/bff/auth.py:101,123,132,136` | Klaim `access_token`/`usr_owner_01`/register role bebas salah; menyulitkan audit | **Hari 5** (finalisasi dokumen) + Hari 1 |
| 6 | `app.pegawaiAI.com` hanya `server_name`; sertifikat untuk `sslip.io` | `deploy_sprint5_day1.py:62,71,73-74`; `test_vps_day1_sprint5.py:7` | URL acceptance tidak bisa lulus TLS dengan konfigurasi ini | **Hari 1** + Hari 5 |
| 7 | Deploy mengunggah `frontend/dist` tanpa `npm run build` | `deploy_sprint5_day1.py:26-29,47-53` | UI yang live bisa lebih lama dari kode; login/Kanban bisa tidak ada di bundel | **Hari 1** + Hari 5 |
| 8 | Kredensial SSH VPS dan kunci BFF tertulis di skrip repo | `deploy_sprint5_day1.py:8,106,124`; `test_vps_day1_sprint5.py:8` | Kebocoran permanen di riwayat git; siapa pun dengan repo bisa masuk VPS | **Hari 1** (urgent; **rotate**) |
| 9 | Webhook WhatsApp tidak terautentikasi dan selalu `user_id="default"` | `bff/bff/main.py:722,732-753` | Pesan pelanggan dapat disuntikkan siapa pun yang tahu URL; routing selalu ke tenant admin | **Hari 2** (WhatsApp) |
| 10 | Register terbuka, role dipaksa `member`, tanpa verifikasi email/rate limit | `bff/bff/auth.py:104-137`; `bff/bff/main.py:119` | Spam akun di produksi; akun uji nyata tertinggal di prod | **Hari 1** |
| 11 | Logout hanya balasan `ok`; tidak ada invalidasi token | `bff/bff/main.py:146-148` | Klaim "invalidasi sesi" tidak benar; token 7 hari tetap berlaku | **Hari 1** + Hari 5 |
| 12 | `TEMPLATES` 10 peran, `bots/souls/` hanya 5 berkas | `bff/bff/bots.py:16-27,139,167` | Menambah builtin untuk 5 peran lain akan gagal saat membuat SOUL/`--clone-from` | **Hari 3** (config) |
| 13 | **Kontrak memori sudah ada (Hari 5)**, tetapi masih **profil-scoped**: `GET`/`DELETE /api/bots/{id}/memory...`; `session_search` tetap bisa membaca semua sesi satu profil | `bff/bff/memory.py`; `bff/bff/main.py` (route Ingatan); `tools/session_search_tool.py:601-628` | UI Ingatan bisa dipakai; isolasi per pengguna **belum**; risiko bocor antar anggota bila profil dibagi | Hari 4 (blueprint) → Sprint 6 (isolasi) |
| 14 | Batas KB hardcoded, tanpa binding per agen/setelan | `bff/bff/kb.py:19-24`; `bff/migrations/011_knowledge_base.sql` | "KB settings" ditunda FE karena tidak ada tempat menyimpan | **Hari 2** + Hari 3 |
| 15 | `HOUSE_SOUL` menyebut "Colorbox", dokumen menyebut "AI Top Trends" | `bff/bff/bots.py:28-35` vs `docs-kaf/bff-spec.md:149` | Dokumen arsitektur menyesatkan; sulit menjelaskan identitas ke klien | **Hari 5** (dokumen) |
| 16 | `role` di JWT tidak dipakai route mana pun | `bff/bff/auth.py:38-49` (hanya membuat klaim); `main.py:98-100` hanya mengembalikan id | "Owner/admin only" tidak bisa ditegakkan server-side | **Hari 1** + Hari 3 |

---

## 2. Rincian dan saran perbaikan

### 2.1 Otorisasi `/api/*` (temuan #1, #16)

**Fakta:** `auth_context_middleware` menangkap **semua** exception dan membiarkan `user_id="default"` (`main.py:55-62`). Hanya `/api/auth/me` yang benar-benar menolak token (`main.py:131-143`). `require_key` (`main.py:92-96`) hanya membuktikan permintaan lewat nginx, dan nginx menyuntik kunci itu untuk semua pengunjung.

**Saran:**

1. Pisahkan router: `public` (login/register/verify) vs `api` yang mewajibkan Bearer valid; untuk router `api`, **tolak** token hilang/kedaluwarsa dengan 401 alih-alih fallback.
2. Tambahkan dependency `require_role(...)` untuk route tulis (bots, settings, skills) dan untuk operasi destruktif mendatang (memori).
3. Uji: tanpa token, token rusak, token kedaluwarsa, role `member` vs `owner` — semuanya harus punya ekspektasi eksplisit.
4. Setelah itu, FE baru boleh mengklaim "core tidak bisa diubah klien".

### 2.2 Identitas di MCP bridge (temuan #2)

**Fakta:** `bridge._user()` memanggil `current_user()` (`bridge.py:47-49`), tetapi panggilan tool MCP tidak membawa header `Authorization`, sehingga ContextVar berisi `default`.

**Saran:** bawa identitas pemilik run secara eksplisit — mis. header internal per run (`X-Pegawai-User`) atau lookup `bot → user_id` di dalam bridge — lalu uji dengan akun `user_owner` bahwa KB/Drive/Gmail/task tool menulis ke tenant yang benar. Ini juga prasyarat isolasi KB per agen (Hari 2).

### 2.3 Data demo (temuan #3)

**Fakta:** `bots` di-seed dengan `user_id='default'` (`001_init.sql:17-27`); migrasi 020 menambah `user_owner/user_cs/user_marketing/user_demo` tanpa agen (`020_auth_users.sql:27-32`); semua query bot memfilter `user_id` (`bots.py:59,65`).

**Saran (pilih satu, tulis di dokumen):**

- **A:** seed agen/grup/KB untuk tiap akun demo; atau
- **B:** nyatakan `admin@pegawai.ai` satu-satunya akun demo berisi, dan sembunyikan akun lain dari modal login.

Tanpa keputusan ini, acceptance "data tidak tertukar" tidak bisa dibuktikan.

### 2.4 Rahasia dan dependensi (temuan #4, #8)

**Fakta:** `_get_secret()` memakai `config.BFF_API_KEY` atau fallback hardcoded (`auth.py:17-19`); `import jwt` ada (`auth.py:9`) tetapi `PyJWT` tidak ada di `bff/pyproject.toml:6-18` (hanya transitif via `mcp`, terlihat di `uv.lock:384,667`). Kredensial SSH dan kunci proxy tertulis di `deploy_sprint5_day1.py:8,106,124` dan `test_vps_day1_sprint5.py:8`; kata sandi akun demo juga tertulis di skrip uji (`test_vps_day1_sprint5.py:55-77`).

**Saran:**

1. **Rotate** kredensial VPS dan kunci BFF; anggap keduanya bocor permanen.
2. Pindahkan ke secret manager/env; gunakan SSH key, bukan kata sandi.
3. Tambahkan `PyJWT` ke dependensi langsung.
4. Perkenalkan `AUTH_JWT_SECRET` terpisah dari `BFF_API_KEY`; rotasi kunci proxy tidak boleh mematikan sesi.
5. Hapus akun uji yang dibuat `test_vps_day1_sprint5.py:117-130` di produksi.

### 2.5 Bukti vs kode (temuan #5)

| Klaim dokumen | Kode |
|---|---|
| Respons `{ok, access_token, token_type, user}` (`Evidence.md:80-93`) | `{"token": …, "user": …}` (`auth.py:101,136`) |
| `user.id = "usr_owner_01"` (`Evidence.md:86`) | `user_owner` (`020_auth_users.sql:29`) |
| Register menerima role `cs/marketing/owner` (`Evidence.md:112`) | Dipaksa `member` (`auth.py:123,132`) |
| "Login live di `/demo`" (`Evidence.md:17`) | Uji hanya membuktikan `GET /demo` = HTML 200; bundel `frontend/dist` yang ada belum memuat login |
| "Logout invalidasi sesi" | `/auth/logout` no-op (`main.py:146-148`) |

**Saran:** perbarui dokumen bukti agar mengutip respons nyata (tersanitasi), dan tandai klaim yang belum diuji sebagai belum diuji. Jangan mencampur "kode ada" dengan "sudah diverifikasi live".

### 2.6 Domain dan deploy (temuan #6, #7)

**Fakta:** nginx memakai `server_name app.pegawaiAI.com …` tetapi `ssl_certificate` hanya untuk `139.190.107.151.sslip.io` (`deploy_sprint5_day1.py:62,71,73-74`); semua uji menargetkan host sslip (`test_vps_day1_sprint5.py:7`). Deploy mengunggah `frontend/dist` apa adanya (`deploy_sprint5_day1.py:26-29,47-53`), tanpa `npm run build` dan tanpa assertion hash aset.

**Saran:** sediakan DNS + sertifikat untuk `app.pegawaiAI.com` (atau ubah URL acceptance secara resmi), jalankan build di pipeline, lalu assert bahwa aset yang live memuat string penanda versi. Simpan tangkapan layar login sukses/gagal/terlindungi.

### 2.7 WhatsApp (temuan #9)

**Fakta:** `POST /api/whatsapp/webhook` terdaftar di router `public` **dan** `api` (`main.py:732-733`), lalu memanggil `route_and_process_message(user_id="default", …)` (`main.py:742-750`). Tidak ada verifikasi signature.

**Saran:** wajibkan `X-Hub-Signature-256` (atau secret path), petakan nomor/akun ke tenant yang benar, dan tolak payload tanpa tanda tangan. Route `public` sebaiknya hanya untuk verifikasi GET.

### 2.8 Register dan logout (temuan #10, #11)

**Fakta:** register terbuka lewat nginx, role dipaksa `member`, tanpa verifikasi email dan tanpa rate limit khusus (`auth.py:104-137`). Logout hanya mengembalikan `{"ok": true}` (`main.py:146-148`).

**Saran:** rate limit per IP/email, verifikasi email atau undangan, dan — bila klaim "logout invalidasi" dipertahankan — tambahkan `jti` + daftar cabut atau perpendek masa token. Jika tidak, ubah copy menjadi "keluar di perangkat ini".

### 2.9 Konfigurasi Hermes (temuan #12, #14, #15)

- **Trap template:** `TEMPLATES` memuat 10 peran (`bots.py:16-27`), `bots/souls/` hanya 5 (hendra, siti, budi, diana, rian); `_soul` membaca berkas (`bots.py:139`) dan `--clone-from` memakai id template (`bots.py:167`). Batasi builtin ke 5 atau lengkapi berkas lebih dulu.
- **KB:** batas ada di konstanta (`kb.py:19-24`), item terikat per pengguna (`migrations/011`). FE menunda "KB settings" sampai ada schema per agen.
- **Doc drift:** `HOUSE_SOUL` menyebut Colorbox (`bots.py:28-35`), `docs-kaf/bff-spec.md:149` menyebut "AI Top Trends". Samakan agar dokumen arsitektur tidak menyesatkan.

### 2.10 Kontrak yang ditunggu FE

| Kontrak | Dipakai untuk | Hari BE |
|---|---|---|
| `GET /api/bots/{id}/config` (SOUL efektif teredaksi + toolset + model) | Menampilkan identitas yang benar-benar dipakai | Hari 3 |
| **`GET /api/bots/{id}/memory`** (sudah ada) | Kapasitas/isi memori; lihat §2.11 | Hari 4 (selesai Hari 5) |
| **`DELETE /api/bots/{id}/memory/{item_id}`** dan **`DELETE /api/bots/{id}/memory?confirm=true`** (sudah ada) | "Lupakan" dengan konfirmasi; lihat §2.11 | Hari 4 (selesai Hari 5) |
| Setelan KB per agen (chunk/retensi/kuota) | Halaman setelan KB | Hari 2/3 |
| Error terkurasi "kesalahan terbaru" | Alternatif log mentah | Hari 3 (keputusan) |

### 2.11 Kontrak "Ingatan" yang sudah diimplementasikan (Hari 5) — mohon direview

Implementasi kecil dan terisolasi; FE hanya memakai route ini.

| Method + path | Body/query | Respons | Catatan |
|---|---|---|---|
| `GET /api/bots/{bot_id}/memory` | — | `{items:[{id,text}], about_you:[{id,text}], limit:{used,max}, about_limit:{used,max}}` | `items` = `MEMORY.md`, `about_you` = `USER.md`; `limit` = karakter, bukan entri |
| `DELETE /api/bots/{bot_id}/memory/{item_id}` | — | `204` | `item_id` = `m-<16 hex>` / `u-<16 hex>` (hash teks + store). Id lama → `409`; id rusak → `404` |
| `DELETE /api/bots/{bot_id}/memory` | `?confirm=true` atau body `{"confirm": true}` | `204` | Mengosongkan **kedua** store; tanpa konfirmasi → `400` |
| `DELETE /api/bots/{bot_id}/sessions/{sid}` | — | `204` | Sudah ada; memakai `DELETE /api/sessions/{sid}` milik Hermes lalu menghapus baris `chat_sessions` |

**Otorisasi:** setiap route memanggil `bots.get_bot(current_user(), bot_id)`; agen milik akun lain → `404`. Catatan: middleware auth global masih jatuh ke `default` untuk token hilang (temuan #1), jadi route ini mewarisi celah itu sampai JWT ditegakkan.

**Mekanisme Hermes yang dipakai (bukan format baru):**

- Berkas: `%LOCALAPPDATA%/hermes/profiles/<bot>/memories/MEMORY.md` dan `USER.md`.
- Delimiter: `"\n§\n"`; setiap entri di-strip, entri kosong dibuang (`tools/memory_tool_store.py:26`).
- Tulis: temp file + `os.replace`, tanpa newline di akhir; baca `utf-8-sig` (BOM aman).
- Lock: berkas `<berkas>.lock`, byte 0, `fcntl.flock`/`msvcrt.locking` — protokol yang sama dengan `MemoryStore._file_lock` (`tools/memory_tool_store.py:259-299`). Semua mutasi membaca ulang di dalam lock; lock sibuk → `409`, bukan tulis buta.
- Batas karakter: 2.200 (`MEMORY.md`) / 1.375 (`USER.md`), dibaca dari `config.yaml` profil lalu instalasi, fallback default Hermes.

**Caveat tenant (penting):** memori tetap **milik profil/pegawai**, bukan pengguna akhir. Semua orang yang memakai pegawai yang sama melihat dan bisa menghapus ingatan yang sama; UI menyatakan ini. Jangan memasarkan sebagai "ingatan pribadi per pengguna" sampai opsi A/B/C di `telegram-dan-memori-ux.md` §7 diputuskan.

**Tes:** `bff/tests/test_memory.py` (21 tes: format, id, 404/409, konfirmasi, lock dua thread, replace saat pembaca aktif). Total suite **312 lulus**. Bukti live: hapus satu `204`, kosongkan `204` (`used=0`), id lama `409`, tanpa konfirmasi `400`; `MEMORY.md` dipulihkan byte-identik.

**Yang perlu keputusan Faiz:** (a) apakah "kosongkan" sebaiknya per-store, (b) apakah perlu audit trail (siapa menghapus apa), (c) apakah route memakai `/bots/{id}` atau diseragamkan ke `/agents/{slug}`.

---

## 3. Cara memverifikasi tanpa menyimpan rahasia

```bash
# Lewat proxy dev (kunci disuntik server-side, tidak perlu ditulis di dokumen)
curl -s http://localhost:5173/bff/api/bots | jq '.bots | length'      # tanpa Authorization
curl -s http://localhost:5173/bff/api/auth/me | jq .                  # harus 401

# Dengan token (simpan di variabel shell, jangan di berkas)
TOKEN=$(curl -s -X POST http://localhost:5173/bff/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@colorbox.co.id","password":"<isi-saat-uji>"}' | jq -r .token)
curl -s http://localhost:5173/bff/api/auth/me -H "Authorization: Bearer $TOKEN" | jq .user.id
```

Ekspektasi setelah #1 diperbaiki: permintaan tanpa token → **401**, bukan daftar bot tenant admin.

---

## 4. Bukan temuan Backend (jangan dikerjakan di sini)

| Temuan | Pemilik |
|---|---|
| `DataProvider` menyimpan state sebelum login dan tidak reload setelah login (`frontend/src/data.tsx:99-112,154`) | FE |
| Modal login mengisi kredensial admin dan chip login cepat | FE |
| `adminMode` hanya localStorage, bukan kontrol akses (`frontend/src/adminMode.ts:3-4`) | FE (tetap perlu role server dari #1/#16) |
| Tidak ada interceptor 401 / validasi token saat boot | FE |
| Prefill kata sandi di bundel publik | FE |

---

## 5. Urutan yang disarankan

1. **Hari 1:** rotate rahasia → hapus kredensial dari skrip → tegakkan JWT di router `api` → pisahkan `AUTH_JWT_SECRET` → deklarasikan `PyJWT` → build di deploy.
2. **Hari 1/5:** putuskan model tenant demo (#3) → DNS/sertifikat atau ubah URL acceptance (#6) → perbaiki dokumen bukti (#5).
3. **Hari 2:** identitas MCP (#2) → signature WhatsApp + tenant (#9).
4. **Hari 3:** trap template (#12) → kontrak `config` read-only → setelan KB bila disetujui.
5. **Hari 4:** kontrak memori + keputusan isolasi tenant (opsi A/B/C di `telegram-dan-memori-ux.md` §7).
6. **Hari 5:** QA ulang dan finalisasi dokumen; pastikan deferral FE tidak dilaporkan sebagai kegagalan.

---

## 6. Rujukan

- `docs-kaf/sprint5/konfigurasi-hermes-fe.md` — konteks konfigurasi & pertanyaan Hari 3.
- `docs-kaf/sprint5/keputusan-scope-hari3.md` — item FE yang ditunda karena kontrak di atas.
- `docs-kaf/sprint5/telegram-dan-memori-ux.md` — kebutuhan Telegram/memori dan opsi isolasi.
- ClickUp Backend Sprint 5 (`local://s5-others.md`): Hari 1 auth/deploy/security, Hari 2 KB/MCP/WhatsApp, Hari 3 config/Master Template, Hari 4 Telegram/memori, Hari 5 QA.
