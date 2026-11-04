"""Bots (stage 4): list, create (Hermes profile + SOUL + key + hardening) and delete."""
import asyncio
import re
import secrets
import subprocess
import time
import unicodedata

from . import config, db, engine, groups, harden, hermes
from .errors import ApiError

COLORS = {"amber", "teal", "indigo", "sky", "rose", "green", "red", "slate", "plain"}  # same names as the frontend swatches
TEMPLATES = {
    "rian": "Menulis naskah dan caption yang santai, jujur, dan enak dibaca di HP.",
    "diana": "Menilai mutu naskah dan memberi skor serta catatan perbaikan.",
    "budi": "Merancang arah visual dan menyusun prompt aset gambar.",
    "siti": "Membalas pelanggan dengan empatik, jelas, dan sopan.",
    "hendra": "Memimpin tim CS dan mengaudit mutu balasan sebelum dikirim.",
}
HOUSE_SOUL = """# {name} — {role}, AI Top Trends

Kamu {name}, {role} di tim {team} AI Top Trends (perusahaan sintetis untuk proyek Pegawai AI).

## Kepribadian dan peran dari pengguna
{persona}

## Aturan bersama
- Sebut perusahaan "AI Top Trends", tanpa "PT".
- Balasan singkat dan langsung ke inti; di luar naskah panjang, usahakan di bawah 60 kata.
- Di grup, kalau tidak ada yang perlu kamu tambahkan, balas hanya [SILENT], tanpa kata lain.
- Paling banyak 2 putaran revisi, lalu rangkum dalam 3 poin dan serahkan ke @user.
- Jangan mengarang fakta, angka, atau fitur yang tidak disebut di permintaan. Bila ragu, tanya satu baris.
- Naskah selalu draf; jangan bilang sudah dipublikasikan atau disetujui.
"""


def _about(b: dict) -> str:
    """Short persona summary for the Info tab: the user's own persona (clipped), else the template's line."""
    text = (b.get("persona") or "").strip() or TEMPLATES.get(b.get("template") or "", "")
    return text if len(text) <= 280 else text[:280].rstrip() + "…"


def view(b: dict) -> dict:
    return {"id": b["id"], "name": b["name"], "role": b["role"], "team": b["team"], "color": b["color"],
            "builtin": b["builtin"], "about": _about(b), **engine.bot_state(b["id"])}


async def list_bots(user_id: str) -> list[dict]:
    rows = await db.q("select * from bots where user_id = %s and deleted_at is null order by builtin desc, created_at, id",
                      user_id)
    return [view(b) for b in rows]


async def get_bot(user_id: str, bot_id: str) -> dict:
    b = await db.q1("select * from bots where id = %s and user_id = %s and deleted_at is null", bot_id, user_id)
    if not b:
        raise ApiError(404, "Bot tidak ditemukan")
    return b


async def templates() -> list[dict]:
    rows = await db.q("select * from bots where builtin order by created_at, id")
    return [{"id": r["id"], "name": r["name"], "role": r["role"], "team": r["team"], "color": r["color"],
             "description": TEMPLATES.get(r["id"], "")} for r in rows]


# ---------- create ----------

def _line(v, label: str, required=True) -> str:
    if not isinstance(v, str):
        raise ApiError(400, f"{label} wajib diisi")
    v = " ".join(v.split())  # single line, no control characters
    if required and not v:
        raise ApiError(400, f"{label} wajib diisi")
    if len(v) > 40:
        raise ApiError(400, f"{label} maksimal 40 karakter")
    return v


def make_slug(name: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_.lower())[:24]


async def _free_slug(base: str) -> str:
    n = 1
    while True:
        slug = base if n == 1 else f"{base[:24 - len(str(n))]}{n}"
        taken = await db.q1("select 1 as x from bots where id = %s", slug)
        if not taken and not (config.HERMES_HOME / "profiles" / slug).exists():
            return slug
        n += 1


def _hermes_cli(*args: str, timeout=120) -> None:
    try:
        r = subprocess.run([config.HERMES_BIN, *args], capture_output=True, timeout=timeout, shell=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ApiError(502, "Perintah Hermes gagal dijalankan atau terlalu lama")
    if r.returncode != 0:
        raise ApiError(502, "Hermes menolak perintah (kode %d)" % r.returncode)


def _rewrite_key(slug: str) -> None:
    """Replace only the API_SERVER_KEY line; every other byte stays. The new value is never logged."""
    env = hermes.profile_dir(slug) / ".env"
    lines = env.read_bytes().splitlines(keepends=True) if env.exists() else []
    new = b"API_SERVER_KEY=" + secrets.token_urlsafe(32).encode()
    for i, ln in enumerate(lines):
        if ln.startswith(b"API_SERVER_KEY="):
            lines[i] = new + ln[len(ln.rstrip(b"\r\n")):]
            break
    else:
        if lines and not lines[-1].endswith(b"\n"):
            lines[-1] += b"\r\n"
        lines.append(new + b"\r\n")
    env.write_bytes(b"".join(lines))


def _soul(name: str, role: str, team: str, template: str | None, persona: str | None) -> str:
    if template:
        src = (config.SOULS_DIR / f"{template}.md").read_text(encoding="utf-8")
        tpl_name = next(b for b in ("Rian", "Diana", "Budi", "Siti", "Hendra") if b.lower() == template)
        body = src.split("\n", 1)[1] if "\n" in src else ""
        body = re.sub(rf"\b{tpl_name}\b", name, body)
        return f"# {name} — {role}, AI Top Trends\n\nPeran kamu: {role} (tim {team}).\n{body}"
    return HOUSE_SOUL.format(name=name, role=role, team=team, persona=persona.strip())


async def create_bot(user_id: str, body: dict) -> dict:
    name, role, team = _line(body.get("name"), "Nama"), _line(body.get("role"), "Peran"), _line(body.get("team"), "Tim")
    color = body.get("color") or "plain"
    template, persona = body.get("template"), body.get("persona")
    if color not in COLORS:
        raise ApiError(400, "Warna tidak dikenal")
    if bool(template) == bool(persona):
        raise ApiError(400, "Pilih salah satu: template atau persona")
    if template and template not in TEMPLATES:
        raise ApiError(400, "Template tidak dikenal")
    if persona and (not isinstance(persona, str) or len(persona) > 2000 or not persona.strip()):
        raise ApiError(400, "Persona wajib diisi (maksimal 2000 karakter)")
    base = make_slug(name)
    if not base:
        raise ApiError(400, "Nama harus memuat huruf atau angka")
    plan = await engine.get_plan(user_id)
    n = (await db.q1("select count(*)::int as n from bots where user_id = %s and deleted_at is null", user_id))["n"]
    if n >= plan["max_bots"]:
        raise ApiError(402, "Batas jumlah bot di paket Anda tercapai. Naikkan paket untuk menambah bot.", upgrade=True)
    slug = await _free_slug(base)
    try:
        await asyncio.to_thread(_hermes_cli, "profile", "create", slug, "--clone-from", template or "rian", "--no-alias")
        await asyncio.to_thread(_rewrite_key, slug)
        (hermes.profile_dir(slug) / "SOUL.md").write_text(_soul(name, role, team, template, persona), encoding="utf-8")
        await asyncio.to_thread(harden.harden, slug)
        await _wait_served(slug)
        left = await asyncio.to_thread(harden.verify, slug, 20)
        if left:
            raise ApiError(502, "Pembatasan alat bot belum aktif")
        row = await db.q1("insert into bots (id, user_id, name, role, team, color, template, persona, builtin) "
                          "values (%s, %s, %s, %s, %s, %s, %s, %s, false) returning *",
                          slug, user_id, name, role, team, color, template, persona)
    except Exception as e:
        await asyncio.to_thread(_cleanup, slug)
        if isinstance(e, ApiError):
            raise
        raise ApiError(500, "Gagal membuat bot")
    engine.hub.publish("*", "bot_status", {"bot_id": slug, "status": "idle", "activity": None})
    return view(row)


def _cleanup(slug: str) -> None:
    try:
        _hermes_cli("profile", "delete", slug, "-y", timeout=60)
    except ApiError:
        pass


async def _wait_served(slug: str) -> float:
    """Wait until the gateway serves the new profile (it rescans every 30 s). Returns seconds waited."""
    start = time.monotonic()
    while time.monotonic() - start < 40:
        try:
            r = await hermes.call(slug, "GET", "/v1/models", timeout=5)
            if r.status_code == 200:
                return time.monotonic() - start
        except ApiError:
            pass
        await asyncio.sleep(2)
    raise ApiError(504, "Bot dibuat tetapi belum aktif di gateway. Coba lagi sebentar.")


# ---------- adopt old sessions ----------

async def adopt_sessions() -> None:
    """Startup: register Hermes api_server sessions made before the BFF existed (stage-1 web chats) so they show in history.
    Group sessions (grup-*) are excluded. Idempotent. A bot that does not answer is skipped; it is retried next start."""
    for b in await db.q("select id, user_id from bots where builtin and deleted_at is null"):
        try:
            r = await hermes.call(b["id"], "GET", "/api/sessions?limit=200")
            if r.status_code != 200:
                continue
            ids = [s["id"] for s in r.json().get("data", []) if isinstance(s.get("id"), str) and s.get("source") == "api_server"
                   and not s["id"].startswith("grup-")]
        except (ApiError, ValueError):
            continue
        for sid in ids:  # shortcut: one insert per session, limit 200 per bot; fine for a few hundred, batch if it grows
            await db.ex("insert into chat_sessions (session_id, user_id, bot_id) values (%s, %s, %s) on conflict do nothing",
                        sid, b["user_id"], b["id"])


# ---------- delete ----------

async def delete_bot(user_id: str, bot_id: str) -> None:
    b = await get_bot(user_id, bot_id)
    if b["builtin"]:
        raise ApiError(403, "Bot bawaan tidak bisa dihapus")
    busy = await db.q1("select 1 as x from runs where bot_id = %s and status = any(%s) limit 1", bot_id, list(engine.ACTIVE))
    if busy or any(lv.bot == bot_id for lv in engine.LIVE.values()):
        raise ApiError(409, "Bot sedang bekerja. Hentikan tugasnya dulu.")
    await asyncio.to_thread(_hermes_cli, "profile", "delete", bot_id, "-y", timeout=60)
    await groups.remove_bot_from_groups(bot_id)
    await db.ex("delete from chat_sessions where bot_id = %s", bot_id)
    await db.ex("update bots set deleted_at = now() where id = %s", bot_id)
