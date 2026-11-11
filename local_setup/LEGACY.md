# local_setup: arsip (legacy)

Digantikan oleh BFF (`bff/`, FastAPI + Postgres + Hermes Runs API) pada 10 November 2026.

- Server Faiz di `backend_template/` (port 8080, memanggil `hermes.exe` sebagai subprocess) tidak lagi dipakai untuk menjalankan tugas. Isinya disimpan sebagai arsip. Adapter mock-nya (scheduler, WhatsApp/Email, Computer Use) tidak dipindahkan.
- Konteks bisnis aktif: Colorbox, di `bff/knowledge/` (Marketing di `colorbox/`, CS v2.1 di `cs-v2.1/`). File SOP lama di `backend_template/context/sops/` sudah diganti penunjuk.
- `backend_template/context/knowledge/colorbox_cs_sop_v1.md` adalah draf lama dan bukan pengetahuan resmi CS. CS memakai v2.1.
- `setup_hermes_bots.py` jangan dijalankan: skrip itu menimpa SOUL dan pembatasan toolset profil. Profil dikelola lewat BFF.
- Kontrak API terbaru: [docs/sprint3/kontrak-api-bff.md](../../docs/sprint3/kontrak-api-bff.md).
