# Pegawai AI — Digital Workforce Backend & Studio
> **PT AI Top Trends (Sprint 2 POC)**  
> Minimal Proof of Concept: Multi-Agent Collaboration Engine powered by **Hermes Agent** and **DeepSeek V4.1 Flash** (via Opencode Zen).

---

## 📌 Ringkasan Proyek

Repository ini menyediakan shared backend development template, arsitektur REST API, alur multi-agent otonom (Pemasaran, Customer Support, Sales), dan Web Dashboard mini untuk tim pengembang Pegawai AI (Intern 1, Intern 2 & 3 Workflows, dan Intern 4 Frontend).

### Fitur Utama:
- **Zero-Dependency Python Server:** Dibuat dengan `http.server` bawaan tanpa ketergantungan kompleks.
- **DeepSeek V4.1 Flash via Opencode:** Terhubung langsung ke model performa tinggi DeepSeek V4.1 Flash.
- **Alur Multi-Agent Dinamis Berdasarkan Divisi:**
  - **Divisi Pemasaran & Kreatif (3 Agen):** Rian (Copywriter AIDA), Diana (QC Auditor & Scoring Kritis), Budi (Visual Specialist & Prompt Generator).
  - **Divisi Customer Support (2 Agen):** Siti (Frontline Support Empatik) & Hendra (CS Team Lead & Quality Assurance).
  - **Divisi Penjualan / Sales (2 Agen):** Doni (B2B Lead Qualification BANT) & Maya (Senior Commercial Proposal & ROI).
  - **Mode Agen Tunggal (Single Agent):** 1 Agen mandiri untuk respon cepat.
- **Dynamic Pillow Visual Generator:** Otomatis merender banner 1080x1080 px sesuai topik tugas.
- **7 Fixture Mock Siap Pakai:** Memungkinkan tim frontend (Intern 4) mengembangkan UI secara independen.

---

## 🚀 Panduan Memulai (Quick Start)

### 1. Prasyarat
- Python 3.10+
- [Hermes Agent CLI](https://github.com/NousResearch/Hermes-Agent) terinstall di lokal (`hermes --version`)
- Library gambar (Pillow):
  ```bash
  pip install -r local_setup/backend_template/requirements.txt
  ```

### 2. Setup Environment Variables
Salin template konfigurasi `.env`:
```bash
cp local_setup/backend_template/.env.example local_setup/backend_template/.env
```
Buka file `local_setup/backend_template/.env` dan masukkan API Key:
```env
OPENCODE_ZEN_API_KEY=your_opencode_zen_api_key_here
HERMES_PROVIDER=opencode
HERMES_MODEL=deepseek-v4.1-flash
PORT=8080
```

### 3. Menjalankan Server Backend
Masuk ke folder backend template:
```bash
cd local_setup/backend_template
python server.py
```
Server akan aktif di: **`http://127.0.0.1:8080`**

- **Web Dashboard:** Buka browser di [http://127.0.0.1:8080](http://127.0.0.1:8080)
- **Health Check:** [http://127.0.0.1:8080/health](http://127.0.0.1:8080/health)

---

## Menjalankan BFF

BFF (`bff/`) adalah backend untuk frontend: kuota, run di latar belakang, grup bot, dan log aktivitas. Browser hanya bicara ke BFF (lewat proxy `/bff` di Vite); key Hermes tidak pernah sampai ke browser. Spesifikasi: `docs/bff-spec.md`.

Prasyarat: Python 3.12+, [uv](https://docs.astral.sh/uv/), PostgreSQL, dan gateway Hermes yang berjalan di `127.0.0.1:8642` (multiplex profil aktif).

1. **Buat database** (sekali; akan diminta password user `postgres`):
   ```powershell
   & "D:\Program Files\PostgreSQL\18\bin\createdb.exe" -h 127.0.0.1 -p 5432 -U postgres pegawai_ai
   ```
   Tabel dibuat otomatis saat BFF pertama kali jalan.
2. **Isi `bff/.env`**: salin `bff/.env.example` menjadi `bff/.env`, lalu isi
   - `DATABASE_URL=postgresql://postgres:PASSWORD_ANDA@127.0.0.1:5432/pegawai_ai`
   - `BFF_API_KEY`: buat dengan `python -c "import secrets; print(secrets.token_urlsafe(32))"`
3. **Samakan key di frontend**: tulis `BFF_API_KEY=<nilai yang sama>` di `frontend/.env.local`. Proxy Vite mengirimnya sebagai header `X-Pegawai-AI-Key`.
4. **Batasi alat bot** (sekali, aman diulang): `cd bff; uv run python -m bff.harden`. Perintah ini mematikan terminal, file, eksekusi kode, browser, dan computer use pada API server lima bot bawaan, dan memasang approval manual. Hermes Desktop tidak terpengaruh.
5. **Jalankan**: `.\start-dev.ps1` dari folder ini (atau klik dua kali `start-dev.bat`). Perintah BFF-nya: `cd bff; uv run uvicorn bff.main:app --host 127.0.0.1 --port 8090 --loop asyncio:SelectorEventLoop` (flag `--loop` wajib di Windows karena psycopg tidak bisa memakai loop bawaan).
6. **Cek**: `http://127.0.0.1:8090/api/health` harus menjawab `{"ok":true,"db":true,"hermes":true}`.

Tes: `cd bff; uv run pytest`.

---

## 📡 Ringkasan Kontrak REST API

### 1. `POST /api/v1/agent/execute`
Menjalankan pipeline eksekusi agen Hermes.

**Headers:**
```http
Content-Type: application/json
X-Pegawai-AI-Key: dev-pegawai-ai-2026
X-Department: marketing
```

**Request Body:**
```json
{
  "customer_id": "cust_aitt_001",
  "department": "marketing",
  "prompt": "Promo Servis AC Mobil Musim Hujan: Diskon 30% dan Pembersihan Evaporator Gratis",
  "agent_mode": "auto",
  "provider": "opencode",
  "model": "deepseek-v4.1-flash",
  "timeout_seconds": 180
}
```

**Nilai `department` yang didukung:**
- `marketing` (3 Agen: Rian, Diana, Budi)
- `customer_support` (2 Agen: Siti, Hendra)
- `sales` (2 Agen: Doni, Maya)
- `general` (Single/Analyst)

**Nilai `agent_mode`:**
- `auto` (Sesuai divisi)
- `single` (1 agen tunggal)
- `multi` (3 agen kolaborasi)

### 2. Mock Endpoints (Khusus Frontend / Testing)
- `GET /api/v1/mocks/mock_marketing_success.json`
- `GET /api/v1/mocks/mock_customer_support_success.json`
- `GET /api/v1/mocks/mock_sales_success.json`
- `GET /api/v1/mocks/mock_validation_error_400.json`
- `GET /api/v1/mocks/mock_unauthorized_401.json`

---

## 📂 Struktur Direktori

```
project6/
├── local_setup/
│   ├── backend_template/
│   │   ├── server.py              # Server REST HTTP Backend
│   │   ├── index.html             # Web Dashboard Mini (Multi-Agent UI)
│   │   ├── requirements.txt       # Dependencies (Pillow)
│   │   ├── .env.example           # Template environment variables
│   │   ├── config.example.yaml    # Template konfigurasi profil PT AI Top Trends
│   │   └── context/sops/          # SOP Divisi (Marketing, CS, Sales)
│   ├── mock_fixtures/             # 7 Berkas JSON mock untuk Frontend
│   ├── S2-01A_Technical_Research_Report.md
│   └── S2-02A_Backend_Architecture_API_Contract.md # Spesifikasi Kontrak Lengkap
├── pegawai_ai_cli.py              # Skrip CLI standalone
├── README.md                      # Dokumentasi Utama
└── .gitignore                     # Proteksi credential & file biner
```

---

## 🔒 Catatan Keamanan
- Kunci API asli **TIDAK PERNAH** dikomit ke repository Git.
- File `.env` sudah masuk ke `.gitignore`.
- Selalu gunakan `.env.example` saat mendistribusikan konfigurasi ke anggota tim baru.

