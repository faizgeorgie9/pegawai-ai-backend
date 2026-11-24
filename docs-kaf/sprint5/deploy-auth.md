# Deploy Auth (Kritis 1 & 2) — JWT wajib, kunci proxy keluar dari Nginx

Dokumen ini **rencana** untuk deploy ke VPS `139.190.107.151`. Belum diterapkan.
Berkas kode terkait: `bff/bff/main.py`, `bff/bff/auth.py`, `bff/bff/config.py`, `bff/bff/bridge.py`,
`bff/migrations/022_users_token_version.sql`, `frontend/src/{App,adminMode,bff,Settings,LoginModal}.ts(x)`.

Tidak ada nilai rahasia di dokumen ini. Jangan pernah menulis isi `JWT_SECRET` / `BFF_API_KEY` ke log,
commit, atau chat.

---

## 1. Yang berubah dan mengapa urutannya penting

| # | Perubahan | Akibat bila salah urutan |
|---|---|---|
| 1 | Semua route `/api/*` (kecuali daftar publik §2) menolak tanpa Bearer JWT yang valid | Kode lama masih menerima `X-Pegawai-AI-Key`; memasang Nginx baru lebih dulu akan membuat semua request browser 401 |
| 2 | JWT ditandatangani `JWT_SECRET` baru, bukan `BFF_API_KEY` | BFF **gagal start** bila `JWT_SECRET` kosong/terlalu pendek/sama dengan `BFF_API_KEY` |
| 3 | Logout menaikkan `users.token_version` (migrasi 022, aditif) | Migrasi otomatis saat start; kolom baru aman untuk kode lama |
| 4 | Registrasi 403 kecuali `ALLOW_REGISTER=true` | – |
| 5 | Nginx berhenti menyuntik `X-Pegawai-AI-Key` | Hanya aman **setelah** kode baru berjalan |

**Urutan wajib: env → kode + restart → verifikasi → Nginx → verifikasi.**

Semua sesi lama akan diminta login sekali (token lama ditandatangani kunci berbeda). Itu diterima.

---

## 2. Endpoint publik yang tetap tanpa JWT (disengaja)

| Endpoint | Alasan | Pengaman |
|---|---|---|
| `GET /api/health` | health check | tidak ada data pengguna |
| `POST /api/auth/login` | pintu masuk | verifikasi kata sandi |
| `POST /api/auth/register` | hanya bila dibuka | `403` kecuali `ALLOW_REGISTER=true` |
| `POST /api/auth/logout` | idempoten | token lama (bila ada) diinvalidasi; tanpa token tetap `200` |
| `GET /api/product-images/{name}` | `<img>` tidak bisa mengirim header | nama whitelist, tanpa path traversal |
| `GET/POST /api/whatsapp/webhook` | Meta/Evolution | GET: verify token; POST: **belum** ada signature (lihat §8) |
| `POST /api/telegram/webhook[/{bot_id}]` | Telegram | `X-Telegram-Bot-Api-Secret-Token` |
| `GET /api/connections/{family}/callback` | browser kembali dari Google | baris `oauth_states.state` sekali pakai, tidak bisa ditebak |

Catatan: `GET /api/whatsapp/webhook` **tanpa** parameter `hub.*` (halaman status) sekarang memerlukan JWT.
`/api/whatsapp/qr`, `/api/whatsapp/connection`, `/api/telegram/status` tidak lagi publik.

---

## 3. Environment yang ditambahkan

Di `/home/ubuntu/pegawai-ai/bff/.env` (mode `600`, pemilik `ubuntu`):

```
JWT_SECRET=<acak 32+ karakter, berbeda dari BFF_API_KEY>
# ALLOW_REGISTER tidak perlu ditulis; default mati. Isi "true" hanya bila pendaftaran dibuka.
# SERVICE_USER_ID=<id user>   # opsional, untuk webhook yang tidak punya bot
```

Buat nilai tanpa mencetaknya:

```bash
cd /home/ubuntu/pegawai-ai/bff
python3 - <<'PY'
import secrets
from pathlib import Path
p = Path('.env')
lines = [ln for ln in p.read_text(encoding='utf-8').splitlines() if not ln.startswith('JWT_SECRET=')]
lines.append('JWT_SECRET=' + secrets.token_urlsafe(48))
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY
chmod 600 .env
```

`BFF_API_KEY` tetap boleh ada untuk proxy Vite saat pengembangan. **Tidak ada route `/api` yang
memakainya lagi**; MCP bridge memakai `MCP_BRIDGE_KEY` + loopback (`127.0.0.1`).

---

## 4. Deploy kode

Rilis harus memuat migrasi `022_users_token_version.sql`. `db.migrate()` menerapkannya otomatis saat
startup (satu transaksi per berkas), jadi tidak ada langkah SQL manual.

```bash
# dari mesin build: kirim rilis seperti biasa ke /home/ubuntu/releases/<sha>/{bff,www,SHA}
/home/ubuntu/deploy-pegawai-ai.sh <sha>
```

Skrip akan: backup (termasuk `pg_dump`) → rsync backend → `uv sync` bila perlu → restart →
tunggu `/api/health` → rsync frontend. Bila health gagal, skrip rollback otomatis.

Sebelum restart, pastikan §3 sudah ditulis. Bila `JWT_SECRET` kosong, startup berhenti dengan pesan:

```
RuntimeError: JWT_SECRET belum diatur. Isi bff/.env dengan JWT_SECRET=<acak 32+ karakter,
berbeda dari BFF_API_KEY>, lalu nyalakan ulang BFF.
```

---

## 5. Verifikasi sebelum menyentuh Nginx

Nginx **masih** menyuntik kunci lama; kode baru mengabaikannya. Yang diuji di sini adalah penolakan token.

```bash
BASE=https://139.190.107.151.sslip.io

curl -sk -o /dev/null -w '%{http_code}\n' $BASE/api/health          # 200
curl -sk -o /dev/null -w '%{http_code}\n' $BASE/api/me              # 401
curl -sk -o /dev/null -w '%{http_code}\n' $BASE/api/bots            # 401
curl -sk -o /dev/null -w '%{http_code}\n' -H 'Authorization: Bearer bogus' $BASE/api/bots  # 401
curl -sk -o /dev/null -w '%{http_code}\n' $BASE/api/product-images/cbx-01-contrast-stitch-chambray-shirt.jpg  # 200
curl -sk -o /dev/null -w '%{http_code}\n' -X POST $BASE/api/auth/register \
  -H 'Content-Type: application/json' -d '{"name":"x","email":"x@x.test","password":"rahasia123"}'  # 403
```

Login dan satu route terproteksi + logout (jangan mencetak token):

```bash
TOKEN=$(curl -sk -X POST $BASE/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@pegawai.ai","password":"<kata-sandi>"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')
curl -sk -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" $BASE/api/auth/me   # 200
curl -sk -o /dev/null -w '%{http_code}\n' -X POST -H "Authorization: Bearer $TOKEN" $BASE/api/auth/logout  # 200
curl -sk -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" $BASE/api/auth/me   # 401
unset TOKEN
```

Cek migrasi & log (memakai `.env` tanpa mencetak nilainya):

```bash
curl -s http://127.0.0.1:8090/api/health
cd /home/ubuntu/pegawai-ai/bff && uv run python - <<'PY'
import asyncio
from bff import db
async def main():
    await db.open_pool()
    col = await db.q1("select column_name from information_schema.columns "
                      "where table_name='users' and column_name='token_version'")
    n = await db.q1("select count(*)::int as n from schema_migrations")
    print("token_version:", bool(col), "| migrations:", n["n"])
    await db.close_pool()
asyncio.run(main())
PY
sudo journalctl -u pegawai-ai-bff --since -2min | grep -iE 'traceback|exception|critical' || echo 'log bersih'
```

---

## 6. Perubahan Nginx (diterapkan setelah §5 lulus)

Hapus **hanya** baris penyuntik kunci. Nilai kunci tidak perlu ditulis di mana pun.

```diff
--- /etc/nginx/sites-enabled/default.before-auth
+++ /etc/nginx/sites-enabled/default
@@ location /bff/  (proxy ke 127.0.0.1:8090) @@
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header X-Forwarded-Proto $scheme;
         proxy_set_header Authorization $http_authorization;
-        proxy_set_header X-Pegawai-AI-Key <NILAI BFF_API_KEY>;
         proxy_read_timeout 3600s;

@@ location /api/  (proxy ke 127.0.0.1:8090/api/) @@
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header X-Forwarded-Proto $scheme;
         proxy_set_header Authorization $http_authorization;
-        proxy_set_header X-Pegawai-AI-Key <NILAI BFF_API_KEY>;
         proxy_read_timeout 3600s;
```

Perintah yang tepat (menghapus baris itu di kedua berkas; keduanya harus sama):

```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
sudo cp -a /etc/nginx/sites-enabled/default   /root/nginx-default.$STAMP.bak
sudo cp -a /etc/nginx/sites-available/default /root/nginx-available-default.$STAMP.bak

sudo grep -n 'X-Pegawai-AI-Key' /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default
sudo sed -i -E '/^[[:space:]]*proxy_set_header[[:space:]]+X-Pegawai-AI-Key[[:space:]]+.*;[[:space:]]*$/d' \
  /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default
sudo grep -n 'X-Pegawai-AI-Key' /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default || echo 'kunci sudah tidak ada'

# Pastikan header Authorization diteruskan di kedua location (tambahkan bila belum ada):
sudo grep -n 'proxy_set_header Authorization' /etc/nginx/sites-enabled/default

sudo nginx -t && sudo systemctl reload nginx
```

`reload` graceful: koneksi SSE lama ditutup oleh upstream, pembaca SSE baru (fetch + Bearer) menyambung
ulang otomatis dalam 3 detik.

---

## 7. Verifikasi setelah Nginx

Ulangi seluruh perintah §5, lalu dari browser:

1. `https://139.190.107.151.sslip.io/demo/` → login admin.
2. Grup menu **Admin** langsung terlihat tanpa mengubah Pengaturan.
3. Buka **Chat**, **Jadwal & tugas**, **Pengetahuan**, dan **Ingatan** satu agen: data termuat, indikator
   "Menyambung ulang…" tidak muncul terus-menerus (SSE memakai Bearer).
4. **Keluar** → login lagi → grup Admin tetap muncul (preferensi mode admin dibersihkan saat logout).
5. Login akun staf (`cs@colorbox.co.id`): tidak ada grup Admin; buka `#/agen` → kembali ke Beranda;
   di Pengaturan tidak ada sakelar "Mode admin".

Cek cepat SSE dengan curl (token dari login, jangan dicetak):

```bash
curl -skN --max-time 5 -H "Authorization: Bearer $TOKEN" $BASE/api/events | head -5
# harus ada baris "retry:" / ": keepalive" dan tidak 401
```

---

## 8. Rollback

Kode: rilis sebelumnya masih ada di `/home/ubuntu/releases/`. Karena migrasi 022 aditif, kode lama
mengabaikan `token_version`; **jangan** drop kolom.

```bash
sudo systemctl stop pegawai-ai-bff
# pulihkan bff/ dari rilis sebelumnya (rsync --delete, kecualikan .venv dan .env), atau:
sudo tar xzf /home/ubuntu/backups/<deploy-terakhir>/app.tar.gz -C /home/ubuntu
sudo systemctl start pegawai-ai-bff
curl -s http://127.0.0.1:8090/api/health

# Nginx: pulihkan hanya bila kode lama juga dipulihkan (kode lama butuh kunci):
sudo cp -a /root/nginx-default.<STAMP>.bak /etc/nginx/sites-enabled/default
sudo cp -a /root/nginx-available-default.<STAMP>.bak /etc/nginx/sites-available/default
sudo nginx -t && sudo systemctl reload nginx
```

`JWT_SECRET` boleh tetap di `.env` saat rollback (kode lama mengabaikannya). Token yang diterbitkan
sebelum rollback akan ditolak kode lama (kunci berbeda) — pengguna login sekali lagi.

Bila ingin mengembalikan data sesi: menghapus `token_version` tidak diperlukan dan tidak dianjurkan.
Bila benar-benar perlu membatalkan semua sesi: naikkan `token_version` semua baris satu kali.

---

## 9. Risiko yang masih terbuka setelah deploy ini

- **Skrip lama di root repo** (`deploy_sprint5_day1.py`, `deploy_vps_day4.py`, `redeploy_all_vps.py`,
  `apply_security_hardening.py`) masih memuat `X-Pegawai-AI-Key` / nilai kunci lama. Skrip itu bukan
  runtime dan sekarang akan mendapat 401; jangan dipakai lagi. Setelah Nginx bersih, **rotasi
  `BFF_API_KEY`** dan hapus nilainya dari skrip (temuan audit #8).
- **WhatsApp POST** masih belum memverifikasi signature Meta/Evolution. Endpoint publik; sarankan
  menambahkan `X-Hub-Signature-256` (Meta) atau header `apikey` Evolution dan menolak bila kosong.
- **Rate limit login** belum ditambahkan (audit Fase 4).
- Tab **Daftar** masih tampil di halaman login; server menjawab 403 dengan pesan jelas. Menyembunyikan
  tab adalah pekerjaan FE terpisah (butuh endpoint konfigurasi publik).
- Akun demo non-admin masih workspace kosong (temuan tenant, di luar lingkup auth).

---

## 10. Telegram: agen nyata, bukan balasan template (migrasi 023)

Sebelum rilis ini, pesan Telegram dibalas dari template kata kunci dan status chat (`chat_id` → bot/sesi)
hanya ada di memori proses: hilang saat restart, dan setiap balasan memakai tenant `default`. Sekarang:

| Hal | Perilaku baru |
|---|---|
| Balasan | Satu run Hermes sungguhan lewat jalur yang sama dengan chat web (`engine.chat_turn`): instruksi CS, pengetahuan/KB, dan pencatatan biaya yang sama. |
| Identitas | Run milik **pemilik bot** (`auth.service_user(bot_id)`), bukan `default`. Chat baru memakai bot default (`TELEGRAM_DEFAULT_BOT`, bawaan `siti`). |
| Sesi | `telegram_chats` (migrasi `023_telegram_chats.sql`, aditif) menyimpan `chat_id` → `user_id`, `bot_id`, `session_id`. Sesi didaftarkan juga di `chat_sessions`, jadi muncul di riwayat chat web. |
| `/reset` | Sesi baru pada pesan berikutnya; pegawai AI tetap. |
| `/agent <nama>` | Hanya pegawai AI aktif milik pemilik chat itu. Nama lain dijawab "tidak tersedia". |
| Webhook | `POST /api/telegram/webhook[/{bot_id}]` menjawab `200` segera; run berjalan di background task. Selama menunggu, `sendChatAction: typing` dikirim tiap ~4 detik. |
| Gagal/timeout | Balasan Indonesia sederhana (mis. "Maaf, Siti sedang tidak bisa menjawab. Coba lagi sebentar lagi."), detail hanya di log. Tidak ada stack trace ke pelanggan. |
| CS | Jawaban terstruktur CS (`customer_reply_draft`) dikirim sebagai teks pelanggan; JSON mentah tidak pernah dikirim. |

Tidak ada environment baru yang wajib. `TELEGRAM_DEFAULT_BOT` opsional. Migrasi berjalan otomatis saat BFF
start (satu transaksi per berkas); tidak ada langkah SQL manual. Setelah restart, cek:

```bash
cd /home/ubuntu/pegawai-ai/bff && uv run python - <<'PY'
import asyncio
from bff import db
async def main():
    await db.open_pool()
    t = await db.q1("select to_regclass('public.telegram_chats') as t")
    n = await db.q1("select count(*)::int as n from schema_migrations")
    print("telegram_chats:", bool(t["t"]), "| migrations:", n["n"])
    await db.close_pool()
asyncio.run(main())
PY
```

Kirim satu pesan ke bot; log BFF harus menunjukkan run agent (bukan balasan template), dan baris
`telegram_chats` untuk chat itu harus bertambah. Jangan mencetak token bot atau isi pesan pelanggan ke log
produksi.
