"""Aplikasi: Hermes connector catalog (Nous Portal, `hermes connectors ...`) and per-agent built-in skills (toolsets).

Connector accounts live on the Nous account, not in a profile (every profile's auth.json carries the same user_id), so
the CLI runs once against the Hermes home root and the connection is shared by all agents. `connect` prints the login URL
on stdout and then polls until the user finishes in the browser; we keep that process alive in the background.
Skills are `platform_toolsets.api_server` in each profile's config.yaml; the gateway re-reads it for every new run,
so no restart is needed. The deny list of harden.py is never shown and never written.
"""
import asyncio
import os
import re
import shutil
import subprocess
import threading
import time

from ruamel.yaml import YAML

from . import bots, config, harden, hermes
from .errors import ApiError

_ID = re.compile(r"^[a-z0-9][a-z0-9_]{0,63}$")
_CACHE_SECONDS = 60
_CLI_TIMEOUT = 40
_CONNECT_LIMIT = 180  # the user has 3 minutes to finish in the browser

CATEGORIES = [("docs", "Dokumen & catatan"), ("design", "Desain & konten"), ("marketing", "Pemasaran & SEO"),
              ("sales", "Penjualan & toko"), ("comms", "Komunikasi"), ("projects", "Proyek & tugas"),
              ("data", "Data & analitik"), ("finance", "Keuangan"), ("dev", "Pengembang"), ("other", "Lainnya")]

# id -> (name, category, one-sentence description, technical). Anything missing gets a tidied name, "other", and a generic sentence.
# shortcut: static map of the 54 connectors known today, add a line when the portal ships a new one.
_T = True
APP_INFO: dict[str, tuple[str, str, str, bool]] = {
    "notion": ("Notion", "docs", "Baca dan susun halaman catatan serta dokumen tim Anda.", False),
    "confluence": ("Confluence", "docs", "Baca dan tulis halaman wiki perusahaan Anda.", False),
    "box": ("Box", "docs", "Cari dan baca berkas yang disimpan di Box.", False),
    "pandadoc": ("PandaDoc", "docs", "Siapkan dan lacak dokumen penawaran atau kontrak.", False),
    "granola": ("Granola", "docs", "Baca catatan rapat Anda.", False),
    "circleback": ("Circleback", "docs", "Baca ringkasan dan catatan rapat Anda.", False),
    "canva": ("Canva", "design", "Buat dan ubah desain di Canva.", False),
    "higgsfield": ("Higgsfield", "design", "Buat gambar dan video dengan bantuan AI.", False),
    "memelord": ("Memelord", "design", "Buat meme dan konten ringan untuk media sosial.", False),
    "adobe_marketing_agent": ("Adobe Marketing", "design", "Kelola materi pemasaran di Adobe.", False),
    "ahrefs": ("Ahrefs", "marketing", "Lihat data SEO, kata kunci, dan situs pesaing.", False),
    "semrush": ("Semrush", "marketing", "Riset kata kunci dan pantau peringkat situs.", False),
    "sendgrid": ("SendGrid", "marketing", "Kirim dan pantau email massal.", False),
    "resend": ("Resend", "marketing", "Kirim email transaksi dan pantau hasilnya.", False),
    "customerio": ("Customer.io", "marketing", "Kelola email dan pesan otomatis ke pelanggan.", False),
    "apollo": ("Apollo", "sales", "Cari calon pelanggan dan kontak bisnis.", False),
    "peopledatalabs": ("People Data Labs", "sales", "Lengkapi data tentang orang dan perusahaan.", False),
    "shopify": ("Shopify", "sales", "Lihat produk, pesanan, dan pelanggan toko online Anda.", False),
    "intercom": ("Intercom", "sales", "Baca percakapan pelanggan dan bantu membalasnya.", False),
    "plain": ("Plain", "sales", "Kelola tiket dan pertanyaan pelanggan.", False),
    "pylon": ("Pylon", "sales", "Kelola permintaan bantuan dari pelanggan.", False),
    "slack": ("Slack", "comms", "Baca dan kirim pesan di ruang obrolan tim.", False),
    "calendly": ("Calendly", "comms", "Lihat jadwal pertemuan dan tautan janji temu.", False),
    "wispr_flow": ("Wispr Flow", "comms", "Ubah suara jadi teks untuk menulis lebih cepat.", False),
    "discordbot": ("Discord", "comms", "Ikut percakapan di server Discord.", _T),
    "clickup": ("ClickUp", "projects", "Buat dan perbarui tugas di ClickUp.", False),
    "asana": ("Asana", "projects", "Buat dan perbarui tugas proyek di Asana.", False),
    "jira": ("Jira", "projects", "Lihat dan perbarui tiket pekerjaan di Jira.", False),
    "linear": ("Linear", "projects", "Lihat dan perbarui tugas tim di Linear.", False),
    "todoist": ("Todoist", "projects", "Kelola daftar tugas pribadi di Todoist.", False),
    "ashby": ("Ashby", "projects", "Lihat kandidat dan proses rekrutmen.", False),
    "airtable": ("Airtable", "data", "Baca dan isi tabel data di Airtable.", False),
    "metabase": ("Metabase", "data", "Ambil laporan dan angka dari Metabase.", False),
    "amplitude": ("Amplitude", "data", "Lihat data perilaku pengguna produk Anda.", False),
    "posthog": ("PostHog", "data", "Lihat data kunjungan dan perilaku pengguna.", False),
    "stripe": ("Stripe", "finance", "Lihat pembayaran, pelanggan, dan langganan di Stripe.", False),
    "plaid": ("Plaid", "finance", "Baca data rekening bank yang Anda izinkan.", False),
    "ramp": ("Ramp", "finance", "Lihat pengeluaran dan kartu perusahaan.", False),
    "cashfree_payments": ("Cashfree", "finance", "Lihat pembayaran yang diterima lewat Cashfree.", False),
    "coinbase_agents": ("Coinbase Agents", "finance", "Akses layanan aset kripto di Coinbase.", _T),
    "coinbase_wallet": ("Coinbase Wallet", "finance", "Akses dompet kripto di Coinbase.", _T),
    "sentry": ("Sentry", "dev", "Lihat laporan error aplikasi.", _T),
    "datadog": ("Datadog", "dev", "Pantau kondisi sistem dan aplikasi.", _T),
    "neon": ("Neon", "dev", "Kelola basis data Neon.", _T),
    "supabase": ("Supabase", "dev", "Kelola basis data Supabase.", _T),
    "vercel": ("Vercel", "dev", "Lihat dan kelola situs yang dipasang di Vercel.", _T),
    "railway": ("Railway", "dev", "Lihat dan kelola layanan di Railway.", _T),
    "cloudflare": ("Cloudflare", "dev", "Kelola domain dan layanan di Cloudflare.", _T),
    "clickhouse": ("ClickHouse", "dev", "Jalankan kueri data di ClickHouse.", _T),
    "turso": ("Turso", "dev", "Kelola basis data Turso.", _T),
    "better_stack": ("Better Stack", "dev", "Pantau ketersediaan dan log sistem.", _T),
    "greptile": ("Greptile", "dev", "Tinjau dan telusuri kode program.", _T),
    "mintlify": ("Mintlify", "dev", "Kelola dokumentasi produk.", _T),
    "statsig": ("Statsig", "dev", "Kelola uji coba fitur dan eksperimen.", _T),
}
_CATEGORY_NAME = dict(CATEGORIES)


def app_key(connector: str) -> str:
    """Portal ids carry an `_mcp` suffix on some apps (clickup_mcp); the map uses the bare name."""
    return connector[:-4] if connector.endswith("_mcp") else connector


def tidy_name(connector: str) -> str:
    return " ".join(w.capitalize() for w in app_key(connector).split("_"))


def app_view(connector: str, connected: bool, accounts: list[str]) -> dict:
    name, cat, text, technical = APP_INFO.get(app_key(connector), (tidy_name(connector), "other", "Hubungkan agar agen bisa memakai aplikasi ini.", False))
    return {"id": connector, "name": name, "category": cat, "category_name": _CATEGORY_NAME[cat], "description": text,
            "status": "connected" if connected else "not_connected", "accounts": accounts, "technical": technical}


def parse_list(out: str) -> list[tuple[str, bool]]:
    """`hermes connectors list`: '<connector>  connected|not connected' per line."""
    rows = []
    for line in out.splitlines():
        m = re.match(r"^(\S+)\s+(connected|not connected)\s*$", line.strip())
        if m and _ID.match(m.group(1)):
            rows.append((m.group(1), m.group(2) == "connected"))
    return rows


def parse_accounts(out: str) -> list[tuple[str, str, str]]:
    """`hermes connectors accounts`: '<connector>  <name>  <status>' (columns padded with 2+ spaces; the name may hold spaces)."""
    rows = []
    for line in out.splitlines():
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) == 3 and _ID.match(parts[0]):
            rows.append((parts[0], parts[1].replace(" (unnamed)", ""), parts[2]))
    return rows


def _cli_env() -> dict:
    return {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1", "HERMES_HOME": str(config.HERMES_HOME)}


def _hermes_exe() -> str:
    return shutil.which("hermes") or "hermes"


def _run(args: list[str], timeout: int = _CLI_TIMEOUT) -> tuple[int, str, str]:
    try:
        p = subprocess.run([_hermes_exe(), *args], capture_output=True, timeout=timeout, env=_cli_env())
    except (OSError, subprocess.TimeoutExpired):
        raise ApiError(502, "Layanan aplikasi belum menjawab. Coba lagi sebentar.")
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


_cache: dict = {"at": 0.0, "rows": None}
_lock = asyncio.Lock()


def invalidate() -> None:
    _cache["at"] = 0.0


def _load_catalog() -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(2) as ex:  # both CLI calls take ~5 s: run them side by side
        f_acc = ex.submit(_run, ["connectors", "accounts"])
        code, out, _ = _run(["connectors", "list"])
        rows = parse_list(out)
        if code != 0 or not rows:
            raise ApiError(503, "Daftar aplikasi belum bisa dimuat. Coba lagi sebentar.")
        labels: dict[str, list[str]] = {}
        try:  # account labels are a nicety: a failure here must not hide the catalog
            for c, name, st in parse_accounts(f_acc.result()[1]):
                if "(retired)" not in st:
                    labels.setdefault(c, []).append(name)
        except ApiError:
            pass
    return [app_view(c, ok, labels.get(c, [])) for c, ok in rows]


async def catalog(fresh: bool = False) -> list[dict]:
    async with _lock:  # one CLI call at a time; the CLI takes ~5 s
        if fresh or _cache["rows"] is None or time.monotonic() - _cache["at"] > _CACHE_SECONDS:
            _cache["rows"] = await asyncio.to_thread(_load_catalog)
            _cache["at"] = time.monotonic()
        return _cache["rows"]


def _check_id(app: str) -> str:
    if not _ID.match(app or ""):
        raise ApiError(404, "Aplikasi tidak ditemukan")
    return app


async def _known(app: str) -> dict:
    row = next((r for r in await catalog() if r["id"] == _check_id(app)), None)
    if not row:
        raise ApiError(404, "Aplikasi tidak ditemukan")
    return row


_pending: dict[str, subprocess.Popen] = {}
_URL = re.compile(r"^https://\S+$")


def _reap(app: str, proc: subprocess.Popen) -> None:
    try:
        proc.wait(timeout=_CONNECT_LIMIT)
    except subprocess.TimeoutExpired:
        proc.kill()
    finally:
        if _pending.get(app) is proc:
            _pending.pop(app, None)
        invalidate()


def _start_connect(app: str) -> dict:
    old = _pending.get(app)
    if old and old.poll() is None:  # same login still open: hand the user the same link
        url = getattr(old, "login_url", None)
        if url:
            return {"url": url}
        old.kill()
    try:  # argument list, no shell; the id was validated against the portal's own list
        proc = subprocess.Popen([_hermes_exe(), "connectors", "connect", app], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                stdin=subprocess.DEVNULL, env=_cli_env(), text=True, encoding="utf-8", errors="replace")
    except OSError:
        raise ApiError(502, "Layanan aplikasi belum menjawab. Coba lagi sebentar.")
    found: list[str] = []

    def read() -> None:
        for line in proc.stdout:  # keep draining so the CLI never blocks on a full pipe
            line = line.strip()
            if not found and _URL.match(line):
                found.append(line)

    threading.Thread(target=read, daemon=True).start()
    end = time.monotonic() + 30
    while time.monotonic() < end and not found and proc.poll() is None:
        time.sleep(0.2)
    if found:
        proc.login_url = found[0]  # type: ignore[attr-defined]
        _pending[app] = proc
        threading.Thread(target=_reap, args=(app, proc), daemon=True).start()
        return {"url": found[0]}
    if proc.poll() is None:
        proc.kill()
        raise ApiError(504, "Halaman login belum siap. Coba lagi sebentar.")
    invalidate()
    if proc.returncode == 0:  # already connected or skipped: nothing to open
        return {"connected": True}
    raise ApiError(502, "Aplikasi ini belum bisa dihubungkan sekarang. Coba lagi nanti.")


async def connect(app: str) -> dict:
    row = await _known(app)
    if row["status"] == "connected":
        return {"connected": True}
    return await asyncio.to_thread(_start_connect, app)


def _disconnect(app: str) -> None:
    _, acc_out, _ = _run(["connectors", "accounts"])
    names = [n for c, n, st in parse_accounts(acc_out) if c == app and "(retired)" not in st]
    if not names:
        return
    for n in names if len(names) > 1 else [None]:
        args = ["connectors", "disconnect", app, "--yes"] + (["--alias", n] if n else [])
        code, _, _ = _run(args)
        if code != 0:
            raise ApiError(502, "Aplikasi belum bisa diputus. Coba lagi sebentar.")


async def disconnect(app: str) -> None:
    await _known(app)
    proc = _pending.pop(app, None)
    if proc and proc.poll() is None:
        proc.kill()
    await asyncio.to_thread(_disconnect, app)
    invalidate()


def _connected_now(app: str) -> bool:
    code, out, _ = _run(["connectors", "list"])
    return dict(parse_list(out)).get(app, False) if code == 0 else False


async def status(app: str) -> dict:
    """Polled by the browser while the user logs in: connected as soon as the portal says so."""
    await _known(app)
    ok = await asyncio.to_thread(_connected_now, app)
    if ok:
        invalidate()
    proc = _pending.get(app)
    return {"status": "connected" if ok else "not_connected", "waiting": bool(proc and proc.poll() is None) and not ok}


# ---- skills (built-in toolsets) ----

# Never offered to anyone: the harden.py deny list, plus channels and the toolset the BFF itself needs (clarify).
HIDDEN = set(harden.DENY) | {"clarify", "discord", "discord_admin", "yuanbao"}
TECHNICAL = {"skills", "kanban", "x_search", "context_engine", "a2a"}  # visible in admin mode only


def visible_skills(gateway_rows: list[dict]) -> list[dict]:
    return [{"name": t["name"], "label": t.get("label") or t["name"], "description": t.get("description") or "",
             "enabled": t.get("enabled") is True, "technical": t["name"] in TECHNICAL}
            for t in gateway_rows if t.get("name") and t["name"] not in HIDDEN]


async def _gateway_rows(slug: str) -> list[dict]:
    r = await hermes.call(slug, "GET", "/v1/toolsets", timeout=10)
    data = r.json().get("data") if r.status_code == 200 else None
    if not isinstance(data, list):
        raise ApiError(502, "Daftar keahlian belum bisa dimuat. Coba lagi sebentar.")
    return data


async def agent_skills(user_id: str, slug: str) -> list[dict]:
    await bots.get_bot(user_id, slug)  # 404 for unknown or foreign agents; also validates the slug shape
    return visible_skills(await _gateway_rows(slug))


async def all_skills(user_id: str) -> dict:
    rows = await bots.list_bots(user_id)

    async def one(b: dict) -> dict:
        try:
            return {"id": b["id"], "name": b["name"], "ok": True, "skills": visible_skills(await _gateway_rows(b["id"]))}
        except ApiError:
            return {"id": b["id"], "name": b["name"], "ok": False, "skills": []}
    return {"agents": await asyncio.gather(*(one(b) for b in rows))}


def apply_toolset(current: list[str], name: str, enabled: bool) -> list[str]:
    """New api_server list. The deny list always stays out and clarify always stays in."""
    out = [t for t in current if t not in harden.DENY and t != name]
    if enabled:
        out.append(name)
    return out + [t for t in sorted(harden.ALLOW) if t not in out]


def _write_toolset(slug: str, name: str, enabled: bool, gateway_enabled: list[str]) -> None:
    path = hermes.profile_dir(slug) / "config.yaml"
    yaml = YAML()  # round-trip: keeps other keys and comments
    yaml.preserve_quotes = True
    data = yaml.load(path.read_text(encoding="utf-8")) or {}
    if data.get("platform_toolsets") is None:
        data["platform_toolsets"] = {}
    current = data["platform_toolsets"].get("api_server")
    if not isinstance(current, list):
        current = gateway_enabled
    new = apply_toolset(list(current), name, enabled)
    if new != list(current):
        with path.open("w", encoding="utf-8") as f:
            data["platform_toolsets"]["api_server"] = new
            yaml.dump(data, f)


async def set_skill(user_id: str, slug: str, name: str, enabled: bool) -> list[dict]:
    await bots.get_bot(user_id, slug)
    if not isinstance(name, str) or not _ID.match(name) or name in HIDDEN:
        raise ApiError(400, "Keahlian ini tidak bisa diubah.")
    rows = await _gateway_rows(slug)
    if name not in {t.get("name") for t in rows}:
        raise ApiError(404, "Keahlian tidak ditemukan")
    await asyncio.to_thread(_write_toolset, slug, name, bool(enabled), [t["name"] for t in rows if t.get("enabled")])
    return visible_skills(await _gateway_rows(slug))  # the gateway re-reads config.yaml per request: this is the real state
