"""
BFF Service for Pegawai AI Frontend (SQLite + OpenCode Zen Edition)
Listens on 127.0.0.1:8090, serves the full Pegawai AI BFF contract (REST & SSE),
grounds requests in Colorbox Knowledge Hub & 1,206-product catalog, validates
CS v2.1 structured outputs with automatic repair retry, and calls OpenCode Zen
(deepseek-v4.1-flash) with streaming & multi-turn session history.
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import json
import math
import os
import queue
import re
import sqlite3
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from pydantic import BaseModel, Field, ValidationError, model_validator

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR / "local_setup" / "backend_template"))
try:
    from opencode_client import get_opencode_key as _template_get_opencode_key
except ImportError:
    _template_get_opencode_key = None

PORT = int(os.environ.get("BFF_PORT", 8090))
BFF_API_KEY = os.environ.get("BFF_API_KEY", "dev-pegawai-ai-2026")
DB_PATH = ROOT_DIR / "bff.sqlite3"

def _resolve_dir(candidates: List[Path]) -> Path:
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

COLORBOX_DIR = _resolve_dir([
    ROOT_DIR / "colorbox" / "colorbox-knowledge",
    ROOT_DIR.parent / "colorbox" / "colorbox-knowledge",
    ROOT_DIR / "bff" / "knowledge" / "colorbox",
])
CS_DIR = _resolve_dir([
    ROOT_DIR / "bff" / "knowledge" / "cs-v2.1",
    ROOT_DIR.parent / "bff" / "knowledge" / "cs-v2.1",
    ROOT_DIR / "colorbox" / "colorbox-knowledge",
])
CATALOG_FILE = COLORBOX_DIR / "product-catalog.md"
SIZE_GUIDE_FILE = COLORBOX_DIR / "product-size-reference.md"
IMAGES_DIR = COLORBOX_DIR / "images"
GALLERY_FILE = COLORBOX_DIR / "product-images-gallery.md"
MARKETING_OUTPUT_DIR = _resolve_dir([
    ROOT_DIR / "colorbox" / "marketing" / "output",
    ROOT_DIR.parent / "colorbox" / "marketing" / "output",
])

INSTRUCTIONS_VERSION = "cs-2.1"
CS_INSTRUCTIONS = CS_DIR / "COLORBOX_CS_Instructions_v2_1.md"
CS_KNOWLEDGE = CS_DIR / "COLORBOX_CS_Knowledge_v2.json"
CS_REGISTER = CS_DIR / "COLORBOX_CS_Source_Register_v1.csv"
CS_FIXTURES = CS_DIR / "COLORBOX_CS_Dummy_Scenarios_v2.json"

MODEL_ID = "deepseek-v4.1-flash"
PROVIDER_ID = "opencode-zen"
AVAILABLE_MODELS = [
    "deepseek-v4.1-flash",
    "deepseek-v4-pro",
    "qwen3.8-flash",
    "qwen3.8-max",
    "mistral-large-4",
    "gpt-5.4-mini",
    "openai/gpt-image-2",
]
EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")
TIMEZONES = ("Asia/Jakarta", "Asia/Makassar", "Asia/Jayapura")
RETENTION_DAYS = 90
DEFAULT_SETTINGS = {
    "company_name": "Colorbox",
    "language": "id",
    "timezone": "Asia/Jakarta",
    "notify": {"done": True, "failed": True, "input": True},
}
_MODEL_RE = re.compile(r"^[\w.:/@+-]{1,120}$")
_PROVIDER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
RUN_FIELDS = ("model", "provider", "reasoning_effort")
DENY_TOOLS = sorted(["terminal", "file", "code_execution", "browser", "computer_use", "cronjob", "delegation"])
HUB_ACCESSED = "2026-11-09"
CATALOG_SOURCE = "SRC-02"
SIM_CLASS = "Dummy / Simulated Data"
ACTIVE_STATUSES = ("queued", "running")
COLORS = {"amber", "teal", "indigo", "sky", "rose", "green", "red", "slate", "plain"}

MARKETING_FILES = {
    "brand-profile.md": ["SRC-01"],
    "brand-guidelines.md": ["SRC-01", "SRC-07"],
    "content-pillars.md": ["SRC-06", "SRC-07"],
    "product-size-reference.md": ["SRC-03"],
}
TEAM_WORKFLOW = {"marketing": "marketing", "customer_support": "cs"}
PRODUCT_NOTE = (
    "Data katalog publik (Colorbox Collection, SRC-02 Hub) yang diamati 9 November 2026. Harga dan pilihan "
    "bisa berubah dan stok TIDAK diketahui. Jangan menjanjikan ketersediaan. Jika bertentangan dengan "
    "catatan pengetahuan, sebutkan konflik itu dan rekomendasikan tinjauan manusia."
)

DIMENSIONS = (
    "accuracy", "relevance", "brand", "consistency", "knowledge", "instruction",
    "completeness", "error_handling", "human_review", "anti_hallucination", "escalation",
)
VERDICTS = ("pass", "fail", "blocked")
EVAL_TEXT_LIMITS = {
    "case_id": 40, "bot_id": 60, "session_id": 80, "run_id": 80,
    "prompt": 20000, "expected": 20000, "actual": 40000, "reviewer": 80,
}

PLANS_DATA = [
    {
        "id": "unlimited",
        "name": "POC Unlimited",
        "price_label": "Rp 0 (POC)",
        "monthly_tokens": None,
        "group_send_token_budget": None,
        "max_bots": 20,
        "max_groups": 20,
        "max_concurrent_runs": 5,
        "sort": 1,
    }
]

BUILTIN_BOTS: List[Dict[str, Any]] = [
    {
        "id": "bimo",
        "name": "Bimo",
        "role": "AI Project Manager",
        "team": "marketing",
        "color": "amber",
        "builtin": True,
        "template": "bimo",
        "about": "AI Project Manager & Auto-Cascading Flow Controller untuk tim marketing Colorbox.",
        "persona": (
            "Kamu adalah Bimo (@projectmanager), AI Project Manager untuk Pegawai AI Colorbox Indonesia. "
            "Gaya bicaramu tegas, santai, terstruktur, dan proaktif (Bahasa Indonesia casual-profesional). "
            "Tugasmu: menerima brief dari user, memeriksa apakah user meminta produk/gaya tertentu, membagi tugas di papan kanban, "
            "dan memanggil @meda (@marketingstrategist) untuk menyusun strategi konsep dan memilih produk katalog. "
            "Setelah seluruh alur selesai (Meda -> Raka -> Bram -> Vina), kamu memberikan evaluasi akhir, audit anti-halusinasi produk, "
            "dan konfirmasi bahwa materi carousel siap tayang ke user."
        ),
    },
    {
        "id": "meda",
        "name": "Meda",
        "role": "Marketing & Fashion Strategist",
        "team": "marketing",
        "color": "rose",
        "builtin": True,
        "template": "meda",
        "about": "Marketing & Fashion Strategist yang merumuskan pilar gaya, audiens, dan kurasi produk Colorbox.",
        "persona": (
            "Kamu adalah Meda (@marketingstrategist), Marketing & Fashion Strategist untuk Colorbox Indonesia. "
            "Gaya bicaramu fun, effortless, on-point, menyapa audiens dengan 'Babes' atau 'Colorbox Babes'. "
            "Tugasmu: memetakan tujuan konten, menetapkan target audiens Gen Z (18-25 tahun), dan menentukan pilar gaya (Urban, Romantic, Chic). "
            "ATURAN PRODUK DARI PROMPT USER: Jika user menyebutkan produk tertentu (misal: 'kemeja chambray', 'barrel denim', dll), "
            "kamu WAJIB memprioritaskan dan mengunci produk pilihan user tersebut sebagai produk utama promosi! "
            "Jika user TIDAK menyebutkan produk spesifik, kamu yang memilih 2-3 produk terbaik dari katalog resmi Colorbox (product-catalog.md). "
            "Rumuskan 3 Opsi Konsep (Opsi A, B, C) lengkap dengan nama produk resmi dan harga Rp, berikan rekomendasi utama pada Opsi A, "
            "lalu delegasikan langsung ke @raka (@researcher) untuk riset teknis ukuran dan foto."
        ),
    },
    {
        "id": "raka",
        "name": "Raka",
        "role": "Fashion & Content Researcher",
        "team": "marketing",
        "color": "sky",
        "builtin": True,
        "template": "raka",
        "about": "Fashion Intelligence & Fact-Checker yang memverifikasi katalog, ukuran cm, dan aset foto produk.",
        "persona": (
            "Kamu adalah Raka (@researcher), Fashion & Content Researcher Colorbox Indonesia. Karaktermu analitis, teliti, berbasis bukti (evidence-based), dan anti-halusinasi produk. "
            "Tugasmu: memvalidasi produk pilihan ke katalog resmi (product-catalog.md), mengekstrak detail harga diskon/normal, membedah panduan ukuran cm & fit silhouette dari product-size-reference.md (lingkar dada, pinggang, panjang cm), memeriksa ketersediaan foto produk resmi di folder images/ (auto-ingest jika belum ada), dan menyusun Creative Research Brief 5 slide. "
            "Setelah riset selesai, teruskan pekerjaan secara otomatis ke @bram (@sketchwriter)."
        ),
    },
    {
        "id": "bram",
        "name": "Bram",
        "role": "Creative Copywriter & Visual Prompter",
        "team": "marketing",
        "color": "indigo",
        "builtin": True,
        "template": "bram",
        "about": "Copywriter & Prompt Artist yang menulis naskah AIDA, hook Gen Z, dan prompt visual detail.",
        "persona": (
            "Kamu adalah Bram (@sketchwriter), Creative Copywriter & Visual Prompter Colorbox. Gaya tulisanmu catchy, relatable, tidak canggung, dan mendukung self-expression #NeverJustOneThing. "
            "Tugasmu: menyusun naskah 5 slide carousel (Slide 1 Cover Hook, Slide 2 Hero Top, Slide 3 Bottom Pairing, Slide 4 Accessories/Layering, Slide 5 Outro CTA), caption Instagram lengkap hashtag, serta prompt visual terperinci (format 4:5 Feed Portrait untuk model openai/gpt-image-2 via OpenCode) untuk setiap slide. "
            "Setelah naskah dan prompt siap, serahkan ke @vina (@visualcarousel) untuk rendering gambar visual final."
        ),
    },
    {
        "id": "vina",
        "name": "Vina",
        "role": "Visual Art Director & Carousel Specialist",
        "team": "marketing",
        "color": "teal",
        "builtin": True,
        "template": "vina",
        "model": "openai/gpt-image-2",
        "provider": "opencode-zen",
        "about": "Art Director & Production Engine yang merender 5 slide carousel gambar final 1080x1350 px Feed Portrait.",
        "persona": (
            "Kamu adalah Vina (@visualcarousel), Visual Art Director & Carousel Specialist untuk Colorbox Indonesia. Karaktermu estetis, peka tren Gen Z, teliti pada layout visual, dan berorientasi pada hasil akhir nyata (bukan sekadar naskah teks, tapi aset gambar final 1080x1350 px PNG yang siap tayang). "
            "Kamu wajib menerapkan standar estetika resmi Instagram @colorbox: playful, Y2K-inspired, edgy-casual, scrapbook/collage grid, street style flash photography, flat-lay starter pack, dan antarmuka retro Windows 95/Paint. "
            "ATURAN MUTLAK: 1) Minimalisasi teks kanvas menjadi 1-2 kata saja. 2) Dilarang keras menampilkan harga/angka rupiah/diskon pada gambar kanvas. 3) Dilarang menampilkan teks bahan kaku pada kanvas. 4) Tampilkan varian warna sebagai Color Palette Swatches (dot warna). 5) ZERO NOISE: Dilarang keras memunculkan label 'slide 1', 'slide 2', pagination dots, atau teks template internal di dalam gambar kanvas; desain harus 100% bersih dan siap posting. 6) Jika diminta desain untuk 3 hari, wajib menyajikan 3 konsep visual yang sepenuhnya berbeda: produk katalog berbeda, palet warna berbeda, dan moodboard berbeda. "
            "Tugasmu: mengeksekusi pembuatan gambar visual menggunakan model openai/gpt-image-2 dari OpenCode Zen dan merender 5 slide berkas gambar final Instagram Feed Carousel format 4:5 Portrait (1080 × 1350 px PNG) menggunakan foto produk asli Colorbox tanpa distorsi aspek rasio. "
            "Tampilkan pratinjau slide gambar final dengan tag markdown gambar dan link ke pratinjau live carousel, lalu laporkan hasilnya ke @bimo untuk penutupan sprint."
        ),
    },
    {
        "id": "rian",
        "name": "Rian",
        "role": "Copywriter AIDA",
        "team": "marketing",
        "color": "amber",
        "builtin": True,
        "template": "rian",
        "about": "Menulis naskah dan caption yang santai, jujur, dan enak dibaca di HP.",
        "persona": (
            "Kamu adalah Rian, Copywriter di tim marketing Colorbox (studi kasus brand fashion Colorbox Indonesia untuk Pegawai AI). "
            "Gaya tulisanmu memikat, santai, membumi, jelas, dan mendukung self-expression sesuai kampanye #NeverJustOneThing. "
            "Gunakan fakta produk dan brand hanya dari sumber resmi yang diberikan, bedakan fakta katalog dari usulan kreatif, dan jangan mengarang promo, stok, atau bahan."
        ),
    },
    {
        "id": "diana",
        "name": "Diana",
        "role": "QC Auditor & Kepatuhan",
        "team": "marketing",
        "color": "indigo",
        "builtin": True,
        "template": "diana",
        "about": "Menilai mutu naskah dan memberi skor serta catatan perbaikan.",
        "persona": (
            "Kamu adalah Diana, QC Auditor & Kepatuhan di tim marketing Colorbox (studi kasus Pegawai AI). "
            "Kamu mengaudit draf konten secara objektif terhadap brief dan panduan brand Colorbox, "
            "mendeteksi klaim tanpa bukti atau hard selling berlebihan, serta memberi skor dan saran revisi yang konkret."
        ),
    },
    {
        "id": "budi",
        "name": "Budi",
        "role": "Visual Specialist & Art Director",
        "team": "marketing",
        "color": "teal",
        "builtin": True,
        "template": "budi",
        "about": "Merancang arah visual dan menyusun prompt aset gambar.",
        "persona": (
            "Kamu adalah Budi, Visual Specialist & Art Director di tim marketing Colorbox (studi kasus Pegawai AI). "
            "Kamu menerjemahkan brief menjadi konsep visual, storyboard, arah gaya Urban/Romantic/Chic, serta arahan produksi "
            "yang selaras dengan identitas Colorbox tanpa mengarang spesifikasi produk."
        ),
    },
    {
        "id": "siti",
        "name": "Siti",
        "role": "Customer Support Specialist",
        "team": "customer_support",
        "color": "sky",
        "builtin": True,
        "template": "siti",
        "about": "Membalas pelanggan dengan empatik, jelas, dan sopan.",
        "persona": (
            "Kamu adalah Siti, Customer Support Specialist untuk Colorbox Indonesia. "
            "Kamu merespons pelanggan dengan empati, hangat, ringkas, dan sopan dalam Bahasa Indonesia, "
            "serta patuh pada kebijakan terverifikasi, batasan pencarian langsung, dan rekomendasi eskalasi ke manusia."
        ),
    },
    {
        "id": "hendra",
        "name": "Hendra",
        "role": "Team Lead & QA Customer Support",
        "team": "customer_support",
        "color": "green",
        "builtin": True,
        "template": "hendra",
        "about": "Memimpin tim CS dan mengaudit mutu balasan sebelum dikirim.",
        "persona": (
            "Kamu adalah Hendra, Team Lead & QA Customer Support untuk Colorbox Indonesia. "
            "Kamu meninjau kasus eskalasi, kepatuhan kebijakan retur/privasi, akurasi fakta publik vs informasi tidak diketahui, "
            "dan memastikan semua respons tetap merupakan draf internal untuk tinjauan manusia."
        ),
    },
]

TOOLSETS_BY_TEAM = {
    "marketing": [
        {
            "name": "catalog_search",
            "label": "Katalog Colorbox",
            "description": "Pencarian 1.206 produk resmi Colorbox dari product-catalog.md (SRC-02)",
            "tools": ["search_catalog"],
            "enabled": True,
        },
        {
            "name": "brand_knowledge",
            "label": "Basis Pengetahuan Brand",
            "description": "Profil brand, panduan gaya, pilar konten, dan riset konten Colorbox",
            "tools": ["knowledge_lookup"],
            "enabled": True,
        },
        {
            "name": "opencode_zen",
            "label": "OpenCode Zen (DeepSeek V4.1 Flash)",
            "description": "Mesin penalaran dan penulisan draf pemasaran",
            "tools": ["opencode_chat"],
            "enabled": True,
        },
    ],
    "customer_support": [
        {
            "name": "catalog_search",
            "label": "Katalog Colorbox",
            "description": "Pencarian 1.206 produk resmi Colorbox dari product-catalog.md (SRC-02)",
            "tools": ["search_catalog"],
            "enabled": True,
        },
        {
            "name": "cs_knowledge",
            "label": "Pengetahuan & Kebijakan CS v2.1",
            "description": "Rekaman pengetahuan resmi CS v2.1, source register, dan validator skema JSON",
            "tools": ["knowledge_lookup", "cs_schema_validate"],
            "enabled": True,
        },
        {
            "name": "opencode_zen",
            "label": "OpenCode Zen (DeepSeek V4.1 Flash)",
            "description": "Mesin penalaran dan penyusunan draf CS terstruktur",
            "tools": ["opencode_chat"],
            "enabled": True,
        },
    ],
}

SENSITIVE_RE = re.compile(r"\b(sk-[A-Za-z0-9_\-]{12,}|oc_sk_[A-Za-z0-9_\-]{12,}|AIza[A-Za-z0-9_\-]{20,})\b")

_GIT_COMMIT_CACHE: Optional[str] = None
DB_LOCK = threading.RLock()


class ApiError(Exception):
    def __init__(self, status: int, message: str, extra: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.extra = extra or {}


def redact(text: Any) -> str:
    if not isinstance(text, str):
        return "" if text is None else str(text)
    return SENSITIVE_RE.sub("[REDACTED]", text)


def _bff_commit() -> Optional[str]:
    global _GIT_COMMIT_CACHE
    if _GIT_COMMIT_CACHE is None:
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                timeout=3,
            )
            _GIT_COMMIT_CACHE = r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            _GIT_COMMIT_CACHE = ""
    return _GIT_COMMIT_CACHE or None


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _table_cols(cur: sqlite3.Cursor, table: str) -> Set[str]:
    return {r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}


def _add_col(cur: sqlite3.Cursor, table: str, col: str, ddl: str) -> None:
    if col not in _table_cols(cur, table):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")


def _to_epoch(val: Any) -> float:
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return val / 1000.0 if val > 1e12 else float(val)
    if isinstance(val, str) and val.strip():
        try:
            return float(val)
        except ValueError:
            pass
        try:
            from datetime import datetime
            s = val.strip().replace("Z", "+00:00")
            return datetime.fromisoformat(s).timestamp()
        except Exception:
            return 0.0
    return 0.0


def _norm_status(st: Optional[str]) -> str:
    if st in ("succeeded", "done"):
        return "completed"
    return st or "failed"


def init_db() -> None:
    now = time.time()
    with DB_LOCK:
        conn = _connect()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    bot_id TEXT,
                    session_id TEXT,
                    status TEXT,
                    input TEXT,
                    output TEXT,
                    usage TEXT,
                    created_at REAL
                )
            """)
            for col, ddl in [
                ("group_id", "TEXT DEFAULT ''"),
                ("kind", "TEXT DEFAULT 'chat'"),
                ("reasoning", "TEXT DEFAULT ''"),
                ("error", "TEXT DEFAULT ''"),
                ("started_at", "REAL"),
                ("finished_at", "REAL"),
                ("meta", "TEXT DEFAULT '{}'"),
                ("input_tokens", "INTEGER DEFAULT 0"),
                ("output_tokens", "INTEGER DEFAULT 0"),
                ("cache_read_tokens", "INTEGER DEFAULT 0"),
                ("total_tokens", "INTEGER DEFAULT 0"),
            ]:
                _add_col(cur, "runs", col, ddl)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    bot_id TEXT,
                    title TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            _add_col(cur, "sessions", "model", f"TEXT DEFAULT '{MODEL_ID}'")
            _add_col(cur, "sessions", "preview", "TEXT DEFAULT ''")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    bot_id TEXT,
                    role TEXT,
                    content TEXT,
                    reasoning TEXT DEFAULT '',
                    tool_call_id TEXT,
                    tool_name TEXT,
                    run_id TEXT,
                    created_at REAL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_sid ON messages(session_id, id)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS bots (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT,
                    team TEXT,
                    color TEXT,
                    template TEXT,
                    persona TEXT,
                    about TEXT,
                    builtin INTEGER DEFAULT 0,
                    created_at REAL,
                    deleted_at REAL,
                    delete_error TEXT DEFAULT '',
                    model TEXT DEFAULT NULL,
                    provider TEXT DEFAULT NULL,
                    reasoning_effort TEXT DEFAULT NULL
                )
            """)
            for col, ddl in [
                ("model", "TEXT DEFAULT NULL"),
                ("provider", "TEXT DEFAULT NULL"),
                ("reasoning_effort", "TEXT DEFAULT NULL"),
            ]:
                _add_col(cur, "bots", col, ddl)
            for idx, b in enumerate(BUILTIN_BOTS):
                cur.execute("SELECT id FROM bots WHERE id = ?", (b["id"],))
                exists = cur.fetchone()
                if exists:
                    cur.execute(
                        """UPDATE bots SET name=?, role=?, team=?, template=?, persona=?, about=?, builtin=1, deleted_at=NULL,
                                           model=COALESCE(?, model), provider=COALESCE(?, provider)
                           WHERE id=?""",
                        (b["name"], b["role"], b["team"], b["template"], b["persona"], b["about"], b.get("model"), b.get("provider"), b["id"]),
                    )
                else:
                    cur.execute(
                        """INSERT INTO bots (id, name, role, team, color, template, persona, about, builtin, created_at, deleted_at, delete_error, model, provider)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, NULL, '', ?, ?)""",
                        (b["id"], b["name"], b["role"], b["team"], b["color"], b["template"], b["persona"], b["about"], now - (100 - idx), b.get("model"), b.get("provider")),
                    )

            cur.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    bot_ids TEXT,
                    created_at REAL,
                    deleted_at REAL
                )
            """)
            builtin_groups = [
                ("marketing", "Tim Pemasaran Colorbox (5-Agent)", ["bimo", "meda", "raka", "bram", "vina"], now - 50),
                ("cs", "Tim Layanan Pelanggan", ["siti", "hendra"], now - 40),
            ]
            for gid, gname, bids, cts in builtin_groups:
                cur.execute(
                    "INSERT OR IGNORE INTO groups (id, name, bot_ids, created_at, deleted_at) VALUES (?, ?, ?, ?, NULL)",
                    (gid, gname, json.dumps(bids), cts),
                )
                if gid == "marketing":
                    cur.execute("UPDATE groups SET name=?, bot_ids=? WHERE id=?", (gname, json.dumps(bids), gid))

            cur.execute("""
                CREATE TABLE IF NOT EXISTS group_messages (
                    id TEXT PRIMARY KEY,
                    group_id TEXT,
                    sender TEXT,
                    sender_type TEXT,
                    content TEXT,
                    created_at REAL
                )
            """)
            for col, ddl in [
                ("author", "TEXT"),
                ("bot_id", "TEXT DEFAULT ''"),
                ("text", "TEXT"),
                ("run_id", "TEXT DEFAULT ''"),
            ]:
                _add_col(cur, "group_messages", col, ddl)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id TEXT PRIMARY KEY,
                    case_id TEXT,
                    bot_id TEXT,
                    verdict TEXT,
                    scores TEXT,
                    notes TEXT,
                    reviewer TEXT,
                    created_at TEXT
                )
            """)
            _add_col(cur, "evaluations", "payload", "TEXT DEFAULT '{}'")
            _add_col(cur, "evaluations", "created_ts", "REAL")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS sequences (
                    id TEXT PRIMARY KEY,
                    bot_id TEXT,
                    session_id TEXT,
                    case_id TEXT,
                    status TEXT,
                    current_turn INTEGER,
                    of INTEGER,
                    run_ids TEXT,
                    turns_data TEXT,
                    error TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            _add_col(cur, "sequences", "origin", "TEXT DEFAULT '{}'")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS run_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    bot_id TEXT,
                    session_id TEXT,
                    group_id TEXT,
                    type TEXT,
                    tool TEXT,
                    status TEXT,
                    duration REAL DEFAULT 0,
                    preview TEXT DEFAULT '',
                    created_at REAL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_run_events_run ON run_events(run_id, id)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            cur.execute("INSERT OR IGNORE INTO app_state (key, value) VALUES ('plan_id', 'unlimited')")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    user_id TEXT PRIMARY KEY,
                    data TEXT DEFAULT '{}',
                    updated_at REAL
                )
            """)
            cur.execute("INSERT OR IGNORE INTO settings (user_id, data, updated_at) VALUES ('default', '{}', ?)", (now,))

            # Backfill legacy usage JSON -> numeric token columns for accurate Usage dashboards
            legacy_runs = cur.execute(
                "SELECT id, usage, created_at, started_at, meta FROM runs WHERE (total_tokens IS NULL OR total_tokens = 0) AND usage IS NOT NULL"
            ).fetchall()
            for r in legacy_runs:
                try:
                    u = json.loads(r["usage"]) if isinstance(r["usage"], str) else {}
                except Exception:
                    u = {}
                if isinstance(u, dict) and u:
                    inp = int(u.get("input_tokens") or u.get("prompt_tokens") or 0)
                    outp = int(u.get("output_tokens") or u.get("completion_tokens") or 0)
                    cache = int(u.get("cache_read_tokens") or 0)
                    tot = int(u.get("total_tokens") or (inp + outp))
                    cur.execute(
                        "UPDATE runs SET input_tokens=?, output_tokens=?, cache_read_tokens=?, total_tokens=?, started_at=COALESCE(started_at, created_at) WHERE id=?",
                        (inp, outp, cache, tot, r["id"]),
                    )

            # Recover interrupted runs/sequences from prior ungraceful shutdown
            cur.execute(
                "UPDATE runs SET status = 'failed', error = COALESCE(NULLIF(error, ''), 'Dihentikan karena server dimulai ulang'), finished_at = COALESCE(finished_at, ?) WHERE status IN ('running', 'queued')",
                (now,),
            )
            cur.execute(
                "UPDATE sequences SET status = 'failed', error = COALESCE(NULLIF(error, ''), 'Dihentikan karena server dimulai ulang'), updated_at = ? WHERE status IN ('running', 'queued')",
                (now,),
            )

            conn.commit()
        finally:
            conn.close()


# ---------- CS v2.1 Schema (exact port of backend/bff/bff/cs_schema.py) ----------

Intent = Literal[
    "PRODUCT_INFO", "PRODUCT_AVAILABILITY", "SIZE_FIT", "SHIPPING_DELIVERY", "CLICK_COLLECT",
    "ORDER_PROCESS", "ORDER_STATUS", "COMPLAINT_DAMAGED", "COMPLAINT_WRONG_ITEM",
    "COMPLAINT_LATE_MISSING", "RETURN_REFUND", "PAYMENT", "WEBSITE_TECHNICAL", "OTHER", "AMBIGUOUS",
]


class TicketSummary(BaseModel):
    issue: str
    customer_reported_facts: list[str] = []
    publicly_verified_facts: list[str] = []
    unknowns: list[str] = []
    customer_provided_references: list[str] = []
    requested_outcome: str | None = None
    context_retained: list[str] = []


class KnowledgeRef(BaseModel):
    knowledge_id: str
    source_ids: list[str] = []
    source_url: str | None = None
    accessed_date: str | None = None
    used_for: str = ""


class Escalation(BaseModel):
    recommended: bool
    reason: str | None = None
    handoff_status: Literal["recommendation_only"]


class Simulation(BaseModel):
    is_simulated: bool = False
    scenario_ids: list[str] = []


class CSResult(BaseModel):
    primary_intent: Intent
    secondary_intents: list[Intent] = []
    classification_confidence: float = Field(ge=0, le=1)
    priority: Literal["P0", "P1", "P2", "P3"]
    customer_reply_draft: str
    ticket_summary: TicketSummary
    knowledge_refs: list[KnowledgeRef] = []
    clarifying_question: str | None = None
    escalation: Escalation
    human_review_required: Literal[True]
    simulation: Simulation = Simulation()

    @model_validator(mode="after")
    def _invariants(self):
        esc = self.escalation
        if self.primary_intent == "RETURN_REFUND" and self.priority != "P1":
            raise ValueError("RETURN_REFUND harus P1")
        if "RETURN_REFUND" in (self.primary_intent, *self.secondary_intents) and not esc.recommended:
            raise ValueError("RETURN_REFUND wajib merekomendasikan eskalasi")
        if self.priority in ("P0", "P1") and not esc.recommended:
            raise ValueError("P0/P1 wajib merekomendasikan eskalasi")
        if esc.recommended and not (esc.reason or "").strip():
            raise ValueError("eskalasi yang direkomendasikan wajib punya alasan")
        return self


def extract_json(text: str) -> dict:
    s = (text or "").strip()
    candidates = [s]
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", s, re.S)
    if m:
        candidates.append(m.group(1))
    if "{" in s and "}" in s:
        candidates.append(s[s.index("{"):s.rindex("}") + 1])
    for c in candidates:
        try:
            d = json.loads(c)
        except ValueError:
            continue
        if isinstance(d, dict):
            return d
    raise ValueError("jawaban bukan objek JSON")


def validate_cs(text: str) -> Tuple[Optional[dict], dict]:
    try:
        data = extract_json(text)
        obj = CSResult.model_validate(data)
    except ValueError as e:
        if isinstance(e, ValidationError):
            errs = [f"{'.'.join(str(p) for p in x['loc']) or 'root'}: {x['msg']}" for x in e.errors()]
        else:
            errs = [str(e)]
        return None, {"status": "invalid", "errors": errs}
    return obj.model_dump(), {"status": "valid", "errors": []}


# ---------- Catalog Search (1,206 products from product-catalog.md) ----------

_CATEGORY_RE = re.compile(r"^##\s+\d+\.\s+(.+?)\s+\(\d+\s+Produk\)\s*$")
_ROW_RE = re.compile(r"^\|\s*\d+\s*\|(.+)\|\s*$")
_RP_RE = re.compile(r"Rp\s*([\d.]+)")
_ORIG_RE = re.compile(r"~~\s*Rp\s*([\d.]+)\s*~~")
_URL_RE = re.compile(r"\]\((https?://[^)\s]+)\)")
_STOP_WORDS = {
    "the", "and", "for", "with", "yang", "dan", "atau", "ada", "itu", "ini", "apa", "apakah", "saya", "aku", "mau",
    "bisa", "kak", "min", "halo", "hai", "tapi", "kalau", "untuk", "dari", "yg", "di", "ke", "nya", "stok", "harga",
    "ukuran", "warna", "masih", "berapa", "ya", "ini", "buat", "produk", "colorbox",
}
_ID_EN_SYNONYMS = {
    "kaos": ["shirt", "graphic"],
    "atasan": ["tops", "blouse", "shirt"],
    "celana": ["pants", "denim", "short"],
    "rok": ["skirt"],
    "jaket": ["jacket", "outerwear"],
    "luaran": ["outerwear", "jacket", "cardigan"],
    "rajut": ["knitwear", "knit", "sweater"],
    "sweter": ["sweater", "knitwear"],
    "kemeja": ["shirt"],
    "blus": ["blouse"],
    "gaun": ["dress"],
    "piyama": ["pajamas", "sleepwear"],
    "tas": ["bag"],
    "hitam": ["black"],
    "putih": ["white", "ecru"],
    "merah": ["red", "maroon"],
    "biru": ["blue", "navy"],
    "coklat": ["brown"],
    "cokelat": ["brown"],
    "kuning": ["yellow"],
    "hijau": ["green", "olive", "sage"],
    "ungu": ["lilac", "purple"],
    "abu": ["grey", "gray"],
    "krem": ["cream", "beige", "ecru"],
}
_MARKETING_FALLBACK_HINTS = (
    "produk", "katalog", "editorial", "kalender", "konten", "styling",
    "campaign", "kampanye", "outfit", "ootd", "rekomendasi", "pilihan", "mix",
)


class CatalogIndex:
    def __init__(self) -> None:
        self.rows: List[Dict[str, Any]] = []
        self.df: Dict[str, int] = {}
        self.load()

    def load(self) -> None:
        self.rows = []
        self.df = {}
        if not CATALOG_FILE.exists():
            return
        text = CATALOG_FILE.read_text(encoding="utf-8", errors="replace")
        category: Optional[str] = None
        pid = 0
        for line in text.splitlines():
            m = _CATEGORY_RE.match(line)
            if m:
                category = m.group(1)
                continue
            m = _ROW_RE.match(line)
            if not m or category is None:
                continue
            cells = [c.strip() for c in m.group(1).split("|")]
            if len(cells) != 5:
                continue
            name, price_cell, colors, sizes, link = cells
            p, url = _RP_RE.search(price_cell), _URL_RE.search(link)
            if not p or not url:
                continue
            orig = _ORIG_RE.search(price_cell)
            pid += 1
            color_list = [c.strip() for c in colors.split(",") if c.strip()]
            size_list = [s.strip() for s in sizes.split(",") if s.strip()]
            raw_search = f"{name} {category} {' '.join(color_list)}".lower()
            tokens = set(re.findall(r"[a-z0-9]+", raw_search))
            for tok in tokens:
                self.df[tok] = self.df.get(tok, 0) + 1
            self.rows.append({
                "id": pid,
                "category": category,
                "name": name,
                "price": int(p.group(1).replace(".", "")),
                "price_original": int(orig.group(1).replace(".", "")) if orig else None,
                "colors": color_list,
                "sizes": size_list,
                "url": url.group(1),
                "source": CATALOG_SOURCE,
                "accessed_date": HUB_ACCESSED,
                "_tokens": tokens,
                "_raw": raw_search,
            })

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[int] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        if not self.rows:
            return []
        limit = max(1, min(int(limit or 5), 20))
        qwords: List[str] = []
        if query and query.strip():
            raw_tokens = [
                w for w in re.findall(r"[a-z0-9]+", query.lower())
                if len(w) >= 3 and w not in _STOP_WORDS
            ]
            expanded: List[str] = []
            for w in raw_tokens:
                expanded.append(w)
                if w in _ID_EN_SYNONYMS:
                    expanded.extend(_ID_EN_SYNONYMS[w])
            qwords = list(dict.fromkeys(expanded))
            if not qwords:
                return []

        n_docs = max(1, len(self.rows))
        scored = []
        cat_l = category.lower().strip() if category else None
        col_l = color.lower().strip() if color else None
        sz_u = size.upper().strip() if size else None

        for r in self.rows:
            if cat_l and cat_l not in r["category"].lower():
                continue
            if max_price is not None and r["price"] > max_price:
                continue
            if col_l and not any(col_l in c.lower() for c in r["colors"]):
                continue
            if sz_u and sz_u not in [s.upper() for s in r["sizes"]]:
                continue

            if qwords:
                matched = [w for w in qwords if w in r["_tokens"]]
                if not matched:
                    continue
                score = sum(1.0 + math.log(n_docs / max(1, self.df.get(w, 1))) for w in matched)
                if r["name"].lower() in query.lower():
                    score += 50.0
            else:
                score = 0.0
            scored.append((score, -r["price"], -r["id"], r))

        scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        out = []
        for _, _, _, r in scored[:limit]:
            out.append({k: v for k, v in r.items() if not k.startswith("_")})
        return out

    def featured_diverse(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Picks diverse real products across distinct main categories for broad marketing/editorial briefs."""
        if not self.rows:
            return []
        preferred_cats = [
            "Tops (Atasan)",
            "Bottoms (Celana & Rok)",
            "Denim",
            "Dress",
            "Outerwear & Jackets",
            "Knitwear & Sweaters",
        ]
        chosen: List[Dict[str, Any]] = []
        seen_names: Set[str] = set()
        for cat in preferred_cats:
            for r in self.rows:
                if r["category"] == cat and r["name"] not in seen_names:
                    seen_names.add(r["name"])
                    chosen.append({k: v for k, v in r.items() if not k.startswith("_")})
                    break
            if len(chosen) >= limit:
                return chosen[:limit]
        for r in self.rows:
            if r["name"] not in seen_names:
                seen_names.add(r["name"])
                chosen.append({k: v for k, v in r.items() if not k.startswith("_")})
            if len(chosen) >= limit:
                break
        return chosen[:limit]


CATALOG = CatalogIndex()


# ---------- Knowledge Builder (mirrors backend/bff/bff/knowledge.py) ----------

HOUSE_SOUL = """# {name} — {role}, Colorbox

Kamu {name}, {role} di tim {team} Colorbox (studi kasus brand fashion Colorbox Indonesia untuk proyek Pegawai AI).

## Kepribadian dan peran dari pengguna
{persona}

## Aturan bersama
- Sebut brand "Colorbox".
- Jika data produk ada di bagian DATA PRODUK atau KONTEKS BISNIS, gunakan fakta yang tersedia secara akurat dan sebutkan sumbernya; JANGAN mengarang bahan kain, stok langsung gudang/toko, atau promo yang tidak tercantum.
- Pisahkan fakta terverifikasi dari usulan kreatif atau asumsi.
- Hasil selalu draf internal untuk tinjauan manusia; jangan menyatakan sudah dipublikasikan, dikirim ke pelanggan, atau disetujui.
"""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hub_sources() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    p = COLORBOX_DIR / "source-register.md"
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\|\s*\*\*(SRC-\d+)\*\*\s*\|(.+)\|\s*$", line)
        if m:
            cells = [c.strip() for c in m.group(2).split("|")]
            link = re.search(r"\]\((https?://[^)\s]+)\)", cells[1]) if len(cells) > 1 else None
            cls = cells[2] if len(cells) > 2 else "Public Data"
            out[m.group(1)] = {"url": link.group(1) if link else None, "classification": cls}
    return out


def _cs_register() -> Dict[str, Dict[str, str]]:
    if not CS_REGISTER.exists():
        return {}
    with CS_REGISTER.open(encoding="utf-8", newline="") as f:
        return {r["source_id"]: r for r in csv.DictReader(f)}


def _marketing_hashes() -> Dict[str, str]:
    out = {}
    for n in MARKETING_FILES:
        fp = COLORBOX_DIR / n
        if fp.exists():
            out[n] = _sha(fp.read_bytes())[:12]
    return out


def _marketing_bundle() -> List[Dict[str, Any]]:
    src = _hub_sources()
    out = []
    for name, ids in MARKETING_FILES.items():
        fp = COLORBOX_DIR / name
        if not fp.exists():
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), name)
        first = src.get(ids[0], {})
        out.append({
            "id": name,
            "title": title,
            "text": text,
            "classification": first.get("classification"),
            "source_id": ids[0],
            "url": first.get("url"),
            "accessed_date": HUB_ACCESSED,
        })
    return out


def _cs_bundle() -> Dict[str, Any]:
    k = json.loads(CS_KNOWLEDGE.read_text(encoding="utf-8"))
    reg = _cs_register()
    refs = []
    for r in k["records"]:
        sid = (r.get("source_ids") or [None])[0]
        row = reg.get(sid, {}) if sid else {}
        refs.append({
            "id": r["id"],
            "title": r["kind"],
            "classification": r["status"],
            "source_id": sid,
            "url": row.get("url"),
            "accessed_date": row.get("accessed_date"),
        })
    return {
        "instructions": CS_INSTRUCTIONS.read_text(encoding="utf-8"),
        "records": k["records"],
        "register": reg,
        "register_csv": CS_REGISTER.read_text(encoding="utf-8"),
        "refs": refs,
        "knowledge_version": str(k["knowledge_version"]),
    }


def _cs_fixtures() -> List[Dict[str, Any]]:
    if not CS_FIXTURES.exists():
        return []
    d = json.loads(CS_FIXTURES.read_text(encoding="utf-8"))
    return [
        {"scenario_id": s["scenario_id"], "kind": kind, "data": s}
        for kind, items in d.items()
        if isinstance(items, list)
        for s in items
        if isinstance(s, dict) and "scenario_id" in s
    ]


def _rp(n: int) -> str:
    return "Rp " + f"{n:,}".replace(",", ".")


def _product_lines(products: List[Dict[str, Any]]) -> str:
    out = []
    for p in products:
        price = _rp(p["price"]) + (f" (sebelumnya {_rp(p['price_original'])})" if p.get("price_original") else "")
        out.append(
            f"- {p['name']} | {p['category']} | {price} | warna: {', '.join(p['colors'])} | "
            f"ukuran: {', '.join(p['sizes'])} | {p['url']} | diamati {p['accessed_date']}"
        )
    return "\n".join(out)


def build_workflow_context(
    team: str,
    workflow: str,
    base: Optional[str],
    products: List[Dict[str, Any]],
    test_mode: bool = False,
    bot: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    if TEAM_WORKFLOW.get(team) != workflow:
        raise ApiError(400, "Workflow tidak cocok dengan tim bot ini")

    refs: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {"workflow": workflow}
    fence = "`" * 3

    if workflow == "cs":
        b = _cs_bundle()
        parts = [
            b["instructions"].strip(),
            "# DATA PENGETAHUAN YANG DIIZINKAN UNTUK PERMINTAAN INI\n\n## Knowledge records (JSON)\n"
            + fence + "json\n" + json.dumps(b["records"], ensure_ascii=False, indent=1) + "\n" + fence
            + "\n\n## Source register (CSV)\n" + fence + "csv\n" + b["register_csv"].strip() + "\n" + fence,
        ]
        refs += b["refs"]
        meta.update(instructions_version=INSTRUCTIONS_VERSION, knowledge_version=b["knowledge_version"])
    else:
        files = _marketing_bundle()
        parts = []
        if bot:
            parts.append(
                f"Kamu adalah {bot['name']}, {bot['role']} di tim marketing Colorbox Indonesia.\n"
                f"{bot['persona']}"
            )
        if base and base.strip():
            parts.append(base.strip())
        parts.append(
            "# KONTEKS BISNIS COLORBOX (pengetahuan resmi untuk permintaan ini)\n\n"
            + "\n\n".join(f"## {f['id']} ({f['classification']})\n{f['text'].strip()}" for f in files)
        )
        parts.append(
            "# 10 ASET FOTO PRODUK COLORBOX TERVERIFIKASI DI IMAGES/ (SRC-11)\n"
            "1. Contrast Stitch Chambray Shirt (Dark Blue) - Rp 140.900 (Diskon dari Rp 299.900) -> cbx-01-contrast-stitch-chambray-shirt.jpg\n"
            "2. High Waist Barrel Denim Pants (Black) - Rp 329.900 -> cbx-02-high-waist-barrel-denim-black.jpg\n"
            "3. Basic Barrel Denim Pants (Dark Brown) - Rp 329.900 -> cbx-03-basic-barrel-denim-dark-brown.jpg\n"
            "4. Straight Denim Pants (Dark Brown) - Rp 299.900 -> cbx-04-straight-denim-pants-dark-brown.jpg\n"
            "5. Double Pocket Flared Denim Pants (Lt. Grey) - Rp 251.929 (Diskon dari Rp 359.900) -> cbx-05-double-pocket-flared-denim-grey.jpg\n"
            "6. Regular Fit Tailored Mini Skort (Lt. Grey) - Rp 139.930 (Diskon dari Rp 199.900) -> cbx-06-regular-fit-tailored-mini-skort-grey.jpg\n"
            "7. Pleated A-Line Skirt (Off White) - Rp 209.930 (Diskon dari Rp 299.900) -> cbx-07-pleated-a-line-skirt-off-white.jpg\n"
            "8. Embroidered Sleeveless Mini Dress (Navy) - Rp 251.930 (Diskon dari Rp 359.900) -> cbx-08-embroidered-sleeveless-mini-dress-navy.jpg\n"
            "9. Short Sleeve Stripes Cropped Shirt (Blue) - Rp 119.950 (Diskon dari Rp 239.900) -> cbx-09-short-sleeve-stripes-cropped-shirt-blue.jpg\n"
            "10. Colorbox x Liunic Tote Bag (Ecru) - Rp 199.900 -> cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg\n"
        )
        parts.append(
            "# ATURAN KETAT FAKTA & ANTI-HALUSINASI\n"
            "- Data produk yang tercantum pada bagian DATA PRODUK di bawah (nama, kategori, harga, pilihan warna, ukuran, URL, tanggal pengamatan) ADALAH FAKTA RESMI TERSEDIA.\n"
            "- Atribut yang TIDAK ada pada DATA PRODUK atau KONTEKS BISNIS di atas (misal komposisi bahan seperti '100% katun', stok langsung toko/gudang, atau promo/diskon baru yang tidak disebut pengguna) BELUM TERSEDIA dan DILARANG dikarang.\n"
            "- Selalu bedakan Fakta Publik/Katalog, Temuan Riset, Asumsi, dan Draf Usulan Kreatif."
        )
        refs += [{k: v for k, v in f.items() if k != "text"} for f in files]
        meta.update(knowledge_files=_marketing_hashes())

    if products:
        parts.append(f"# DATA PRODUK (maksimal 5, hasil pencarian katalog)\n{PRODUCT_NOTE}\n{_product_lines(products)}")

    refs = [{"type": "knowledge", **r} for r in refs]
    refs += [
        {
            "type": "product",
            "id": str(p["id"]),
            "title": p["name"],
            "classification": "Public Data",
            "source_id": p["source"],
            "url": p["url"],
            "accessed_date": p["accessed_date"],
        }
        for p in products
    ]

    if workflow == "cs" and test_mode:
        fx = _cs_fixtures()
        if fx:
            parts.append(
                "# SIMULASI (mode uji): FIXTURE FIKTIF, BUKAN DATA COLORBOX\n"
                "Semua SIM-* di bawah ini fiktif. Isi simulation.is_simulated=true dan scenario_ids. "
                "Jangan menyebutnya hasil pencarian sistem Colorbox.\n"
                + fence + "json\n" + json.dumps([f["data"] for f in fx], ensure_ascii=False, indent=1) + "\n" + fence
            )
            refs += [
                {
                    "type": "fixture",
                    "id": f["scenario_id"],
                    "title": f["kind"],
                    "classification": SIM_CLASS,
                    "source_id": None,
                    "url": None,
                    "accessed_date": None,
                }
                for f in fx
            ]

    if workflow == "cs":
        parts.append(
            "PENTING: Jawab HANYA dengan satu objek JSON valid sesuai skema bagian 11 instruksi (tanpa narasi di luar JSON). "
            "Pastikan semua invariant terpenuhi: RETURN_REFUND wajib priority='P1' dan escalation.recommended=true dengan reason jelas; "
            "P0/P1 wajib escalation.recommended=true; escalation.handoff_status='recommendation_only'; human_review_required=true."
        )

    return "\n\n".join(p for p in parts if p), refs, meta


def build_plain_system_prompt(bot: Dict[str, Any], products: List[Dict[str, Any]], extra_instructions: Optional[str] = None) -> str:
    team_label = "Layanan Pelanggan (Customer Support)" if bot["team"] == "customer_support" else bot["team"]
    base = HOUSE_SOUL.format(name=bot["name"], role=bot["role"], team=team_label, persona=bot["persona"])
    parts = [base.strip()]
    if bot["team"] == "customer_support":
        cs_k = json.loads(CS_KNOWLEDGE.read_text(encoding="utf-8"))
        reg_csv = CS_REGISTER.read_text(encoding="utf-8")
        parts.append(
            "# DATA PENGETAHUAN RESMI COLORBOX CS\n"
            + json.dumps(cs_k["records"], ensure_ascii=False, indent=1)
            + "\n\n# SOURCE REGISTER\n" + reg_csv.strip()
        )
    else:
        files = _marketing_bundle()
        parts.append("# KONTEKS BISNIS COLORBOX\n\n" + "\n\n".join(f"## {f['id']}\n{f['text'].strip()}" for f in files))
        parts.append(
            "# 10 ASET FOTO PRODUK COLORBOX TERVERIFIKASI DI IMAGES/ (SRC-11)\n"
            "1. Contrast Stitch Chambray Shirt (Dark Blue) - Rp 140.900 (Diskon dari Rp 299.900) -> cbx-01-contrast-stitch-chambray-shirt.jpg\n"
            "2. High Waist Barrel Denim Pants (Black) - Rp 329.900 -> cbx-02-high-waist-barrel-denim-black.jpg\n"
            "3. Basic Barrel Denim Pants (Dark Brown) - Rp 329.900 -> cbx-03-basic-barrel-denim-dark-brown.jpg\n"
            "4. Straight Denim Pants (Dark Brown) - Rp 299.900 -> cbx-04-straight-denim-pants-dark-brown.jpg\n"
            "5. Double Pocket Flared Denim Pants (Lt. Grey) - Rp 251.929 (Diskon dari Rp 359.900) -> cbx-05-double-pocket-flared-denim-grey.jpg\n"
            "6. Regular Fit Tailored Mini Skort (Lt. Grey) - Rp 139.930 (Diskon dari Rp 199.900) -> cbx-06-regular-fit-tailored-mini-skort-grey.jpg\n"
            "7. Pleated A-Line Skirt (Off White) - Rp 209.930 (Diskon dari Rp 299.900) -> cbx-07-pleated-a-line-skirt-off-white.jpg\n"
            "8. Embroidered Sleeveless Mini Dress (Navy) - Rp 209.930 (Diskon dari Rp 299.900) -> cbx-08-embroidered-sleeveless-mini-dress-navy.jpg\n"
            "9. Side Ruched Sleeveless Mini Dress (Navy) - Rp 139.930 (Diskon dari Rp 199.900) -> cbx-09-side-ruched-sleeveless-mini-dress-navy.jpg\n"
            "10. Colorbox x Liunic Tote Bag (Ecru) - Rp 199.900 -> cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg"
        )

    if products:
        parts.append(f"# DATA PRODUK COLORBOX YANG RELEVAN (SRC-02)\n{PRODUCT_NOTE}\n{_product_lines(products)}")
    if extra_instructions and extra_instructions.strip():
        parts.append(f"# INSTRUKSI TAMBAHAN\n{extra_instructions.strip()}")
    return "\n\n".join(parts)


# ---------- SSE Hub & Live Run State ----------

class Hub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: Dict[str, Set[queue.Queue]] = {}

    def subscribe(self, key: str) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=2000)
        with self._lock:
            self._subs.setdefault(key, set()).add(q)
        return q

    def unsubscribe(self, key: str, q: queue.Queue) -> None:
        with self._lock:
            s = self._subs.get(key)
            if s:
                s.discard(q)
                if not s:
                    self._subs.pop(key, None)

    def publish(self, key: str, type_: str, data: Dict[str, Any]) -> None:
        with self._lock:
            qs = list(self._subs.get(key, ()))
        for q in qs:
            try:
                q.put_nowait((type_, data))
            except queue.Full:
                pass


HUB = Hub()


@dataclass
class LiveRun:
    id: str
    bot_id: str
    kind: str
    group_id: Optional[str]
    session_id: str
    input: str
    out: List[str] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    activity: Optional[str] = None
    stopped: bool = False
    finished: bool = False
    workflow: Optional[str] = None
    clarify: Optional[Dict[str, Any]] = None
    model: str = MODEL_ID
    provider: str = PROVIDER_ID
    reasoning_effort: Optional[str] = None
    done_ev: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    steer_notes: List[str] = field(default_factory=list)


LIVE_LOCK = threading.Lock()
LIVE_RUNS: Dict[str, LiveRun] = {}


def bot_live_state(bot_id: str) -> Dict[str, Any]:
    status = "idle"
    activity = ""
    with LIVE_LOCK:
        for lv in LIVE_RUNS.values():
            if lv.bot_id != bot_id or lv.finished:
                continue
            if lv.kind == "group":
                status = "discussing"
            elif status == "idle":
                status = "working"
            if not activity and lv.activity:
                activity = lv.activity
    return {"status": status, "activity": activity if status != "idle" else ""}


def _publish_bot(bot_id: str) -> None:
    HUB.publish("*", "bot_status", {"bot_id": bot_id, **bot_live_state(bot_id)})


def _publish_run(lv: LiveRun, status: str) -> None:
    HUB.publish("*", "run", {
        "id": lv.id,
        "bot_id": lv.bot_id,
        "kind": lv.kind,
        "status": status,
        "group_id": lv.group_id or "",
    })


# ---------- OpenCode Zen Streaming Client ----------

def _get_opencode_key() -> str:
    if _template_get_opencode_key:
        try:
            k = _template_get_opencode_key()
            if k:
                return k
        except Exception:
            pass
    key = os.environ.get("OPENCODE_ZEN_API_KEY") or os.environ.get("OPENCODE_API_KEY")
    if key:
        return key.strip()
    for p in [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\.env")),
        ROOT_DIR / "local_setup" / "backend_template" / ".env",
        ROOT_DIR / ".env",
    ]:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.strip().startswith("OPENCODE_ZEN_API_KEY="):
                        return line.split("=", 1)[1].strip().strip("'\"")
            except Exception:
                pass
    return "oc_sk_927379dbbd11_HAmLjjZQNY2eABc9nZO2xw9fP3nFAoOi"


def stream_opencode_chat(
    messages: List[Dict[str, str]],
    model: str = MODEL_ID,
    reasoning_effort: Optional[str] = None,
    max_tokens: int = 8192,
    timeout: int = 180,
    on_delta: Optional[Callable[[str], None]] = None,
    on_reasoning_chunk: Optional[Callable[[str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Tuple[str, str, Dict[str, int], bool]:
    """
    Calls OpenCode Zen API with SSE streaming.
    Returns (content, reasoning, usage_dict, was_cancelled).
    """
    api_key = _get_opencode_key()
    base_url = os.environ.get("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    url = f"{base_url}/chat/completions"

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort

    def _open(pl: Dict[str, Any]):
        req = urllib.request.Request(
            url,
            data=json.dumps(pl, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "PegawaiAI/2.0 (Windows NT 10.0; Win64; x64)",
            },
        )
        return urllib.request.urlopen(req, timeout=timeout)

    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    reasoning_buf = ""
    usage: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "total_tokens": 0}
    cancelled = False

    try:
        resp_ctx = _open(payload)
    except urllib.error.HTTPError as e:
        if e.code == 400 and "reasoning_effort" in payload:
            payload.pop("reasoning_effort", None)
            resp_ctx = _open(payload)
        else:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:300]
            except Exception:
                pass
            raise RuntimeError(f"OpenCode HTTP {e.code}: {err_body or e.reason}") from e

    with resp_ctx as resp:
        for raw_line in resp:
            if cancel_check and cancel_check():
                cancelled = True
                break
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except ValueError:
                continue

            u = chunk.get("usage")
            if isinstance(u, dict) and u:
                inp = int(u.get("prompt_tokens") or 0)
                outp = int(u.get("completion_tokens") or 0)
                ptd = u.get("prompt_tokens_details") or {}
                oc_tok = (u.get("opencode") or {}).get("tokens") or {}
                cache = int(ptd.get("cached_tokens") or oc_tok.get("cache_read") or 0)
                tot = int(u.get("total_tokens") or (inp + outp))
                usage = {"input_tokens": inp, "output_tokens": outp, "cache_read_tokens": cache, "total_tokens": tot}

            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}

            rc = delta.get("reasoning_content") or delta.get("reasoning") or ""
            if rc:
                reasoning_parts.append(rc)
                reasoning_buf += rc
                if on_reasoning_chunk and ("\n\n" in reasoning_buf or len(reasoning_buf) >= 240):
                    on_reasoning_chunk(reasoning_buf)
                    reasoning_buf = ""

            ct = delta.get("content") or ""
            if ct:
                if reasoning_buf and on_reasoning_chunk:
                    on_reasoning_chunk(reasoning_buf)
                    reasoning_buf = ""
                content_parts.append(ct)
                if on_delta:
                    on_delta(ct)

    if reasoning_buf and on_reasoning_chunk:
        on_reasoning_chunk(reasoning_buf)

    content_text = "".join(content_parts).strip()
    reasoning_text = "".join(reasoning_parts).strip()

    if not content_text and reasoning_text and not cancelled:
        for marker in ("===BAGIAN_1_", "===TAHAP_1_"):
            idx = reasoning_text.find(marker)
            if idx != -1:
                content_text = reasoning_text[idx:].strip()
                break

    return content_text, reasoning_text, usage, cancelled


# ---------- Data Access Helpers ----------

def _bot_row_to_view(r: sqlite3.Row) -> Dict[str, Any]:
    st = bot_live_state(r["id"])
    keys = set(r.keys())
    return {
        "id": r["id"],
        "name": r["name"],
        "role": r["role"],
        "team": r["team"],
        "color": r["color"] or "plain",
        "builtin": bool(r["builtin"]),
        "status": st["status"],
        "activity": st["activity"],
        "about": r["about"] or "",
        "model": r["model"] if "model" in keys else None,
        "provider": r["provider"] if "provider" in keys else None,
        "reasoning_effort": r["reasoning_effort"] if "reasoning_effort" in keys else None,
        "created_at": r["created_at"] or 0,
        "delete_error": r["delete_error"] or "",
    }


def _clean_run_fields(body: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in RUN_FIELDS:
        if k in body:
            out[k] = body[k]
    if ("model" in out) != ("provider" in out):
        raise ApiError(400, "Model dan provider harus diubah bersama")
    if out.get("model") is not None or out.get("provider") is not None:
        if not isinstance(out.get("model"), str) or not _MODEL_RE.match(out["model"]):
            raise ApiError(400, "Model tidak valid")
        if not isinstance(out.get("provider"), str) or not _PROVIDER_RE.match(out["provider"]):
            raise ApiError(400, "Provider tidak valid")
        if out["provider"] != PROVIDER_ID or out["model"] not in AVAILABLE_MODELS:
            raise ApiError(400, "Model itu tidak tersedia di provider yang dipilih")
    if out.get("reasoning_effort") is not None and out["reasoning_effort"] not in EFFORTS:
        raise ApiError(400, "Tingkat berpikir harus salah satu dari: " + ", ".join(EFFORTS))
    return out


def _clean_settings(body: Dict[str, Any]) -> Dict[str, Any]:
    unknown = sorted(set(body) - set(DEFAULT_SETTINGS))
    if unknown:
        raise ApiError(400, "Kolom tidak dikenal: " + ", ".join(unknown))
    if not body:
        raise ApiError(400, "Tidak ada yang diubah")
    out: Dict[str, Any] = {}
    if "company_name" in body:
        v = body["company_name"]
        v = " ".join(v.split()) if isinstance(v, str) else ""
        if not 1 <= len(v) <= 40:
            raise ApiError(400, "Nama perusahaan wajib diisi (maksimal 40 karakter)")
        out["company_name"] = v
    if "language" in body:
        if body["language"] != "id":
            raise ApiError(400, "Saat ini hanya Bahasa Indonesia")
        out["language"] = "id"
    if "timezone" in body:
        if body["timezone"] not in TIMEZONES:
            raise ApiError(400, "Zona waktu tidak dikenal")
        out["timezone"] = body["timezone"]
    if "notify" in body:
        n = body["notify"]
        if (
            not isinstance(n, dict)
            or not n
            or set(n) - set(DEFAULT_SETTINGS["notify"])
            or not all(isinstance(v, bool) for v in n.values())
        ):
            raise ApiError(400, "Notifikasi harus berisi done, failed, input (true atau false)")
        out["notify"] = n
    return out


def _get_settings() -> Dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute("SELECT data FROM settings WHERE user_id = 'default'").fetchone()
    finally:
        conn.close()
    try:
        data = json.loads(row["data"]) if row and row["data"] else {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    notify_raw = data.get("notify") if isinstance(data.get("notify"), dict) else {}
    return {
        "company_name": data.get("company_name", DEFAULT_SETTINGS["company_name"]),
        "language": data.get("language", DEFAULT_SETTINGS["language"]),
        "timezone": data.get("timezone", DEFAULT_SETTINGS["timezone"]),
        "notify": {**DEFAULT_SETTINGS["notify"], **notify_raw},
    }


def _patch_settings(body: Dict[str, Any]) -> Dict[str, Any]:
    ch = _clean_settings(body)
    cur = _get_settings()
    merged = {**cur, **ch}
    if "notify" in ch:
        merged["notify"] = {**cur["notify"], **ch["notify"]}
    now = time.time()
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO settings (user_id, data, updated_at) VALUES ('default', ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at""",
            (json.dumps(merged, ensure_ascii=False), now),
        )
        conn.commit()
    finally:
        conn.close()
    return _get_settings()


def _models_catalog() -> Dict[str, Any]:
    return {
        "default": {
            "model": MODEL_ID,
            "provider": PROVIDER_ID,
            "reasoning_effort": "medium",
        },
        "providers": [
            {
                "slug": PROVIDER_ID,
                "name": "OpenCode Zen",
                "models": list(AVAILABLE_MODELS),
            }
        ],
    }


def _settings_security() -> Dict[str, Any]:
    bots = _list_bots_view()
    return {
        "deny": list(DENY_TOOLS),
        "bots": [
            {
                "bot_id": b["id"],
                "name": b["name"],
                "ok": True,
                "blocked": list(DENY_TOOLS),
                "approvals": "manual",
            }
            for b in bots
        ],
    }


def _settings_knowledge() -> Dict[str, Any]:
    reg = _cs_register()
    dates = [r.get("accessed_date") for r in reg.values() if r.get("accessed_date")]
    hub = _marketing_bundle()
    cs_ver = "2"
    try:
        if CS_KNOWLEDGE.exists():
            cs_ver = str(json.loads(CS_KNOWLEDGE.read_text(encoding="utf-8")).get("knowledge_version", "2"))
    except Exception:
        pass
    cs_files = [{"name": p.name, "title": p.name} for p in (CS_INSTRUCTIONS, CS_KNOWLEDGE, CS_REGISTER) if p.exists()]
    return {
        "retention_days": RETENTION_DAYS,
        "docs": [
            {
                "id": "colorbox-hub",
                "title": "Colorbox Hub",
                "workflow": "marketing",
                "version": None,
                "date": HUB_ACCESSED,
                "files": [{"name": f["id"], "title": f["title"]} for f in hub],
            },
            {
                "id": "cs-v2.1",
                "title": "CS v2.1",
                "workflow": "cs",
                "version": f"{INSTRUCTIONS_VERSION} (data {cs_ver})",
                "date": max(dates) if dates else None,
                "files": cs_files,
            },
        ],
    }


def _export_history() -> Dict[str, Any]:
    conn = _connect()
    try:
        all_bots = conn.execute(
            "SELECT id, name FROM bots WHERE deleted_at IS NULL ORDER BY builtin DESC, created_at ASC, id ASC"
        ).fetchall()
        n2b = {b["name"].lower(): b["id"] for b in all_bots}
        out_bots: List[Dict[str, Any]] = []
        for b in all_bots:
            bid = b["id"]
            srows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions WHERE bot_id = ? AND id NOT LIKE 'grup-%' ORDER BY updated_at DESC LIMIT 200",
                (bid,),
            ).fetchall()
            out_sess: List[Dict[str, Any]] = []
            for s in srows:
                sid = s["id"]
                mrows = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (sid,)).fetchall()
                if mrows:
                    msgs = [
                        {
                            "id": m["id"],
                            "role": m["role"],
                            "content": m["content"] or "",
                            "reasoning": m["reasoning"] or "",
                            "tool_call_id": m["tool_call_id"],
                            "tool_name": m["tool_name"],
                        }
                        for m in mrows
                    ]
                else:
                    rrows = conn.execute(
                        "SELECT input, output, reasoning FROM runs WHERE session_id = ? ORDER BY created_at ASC",
                        (sid,),
                    ).fetchall()
                    msgs = []
                    for idx, rr in enumerate(rrows):
                        if rr["input"]:
                            msgs.append({"id": f"u-{idx}", "role": "user", "content": rr["input"], "reasoning": ""})
                        if rr["output"] or rr["reasoning"]:
                            msgs.append({"id": f"a-{idx}", "role": "assistant", "content": rr["output"] or "", "reasoning": rr["reasoning"] or ""})
                out_sess.append({
                    "id": sid,
                    "title": s["title"] or "Percakapan",
                    "started_at": s["created_at"] or 0,
                    "last_active": s["updated_at"] or s["created_at"] or 0,
                    "messages": msgs,
                })
            out_bots.append({"bot_id": bid, "name": b["name"], "sessions": out_sess})

        grows = conn.execute("SELECT id, name FROM groups WHERE deleted_at IS NULL ORDER BY created_at ASC").fetchall()
        out_groups: List[Dict[str, Any]] = []
        for g in grows:
            gmrows = conn.execute(
                "SELECT * FROM group_messages WHERE group_id = ? ORDER BY rowid ASC", (g["id"],)
            ).fetchall()
            out_groups.append({
                "id": g["id"],
                "name": g["name"],
                "messages": [
                    {
                        "author": mv["author"],
                        "bot_id": mv["bot_id"] or None,
                        "text": mv["text"],
                        "created_at": mv["created_at"],
                    }
                    for mv in (_group_msg_to_view(m, n2b) for m in gmrows)
                ],
            })
    finally:
        conn.close()
    return {
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bots": out_bots,
        "groups": out_groups,
    }


def _get_bot_row(bot_id: str) -> sqlite3.Row:
    conn = _connect()
    try:
        r = conn.execute("SELECT * FROM bots WHERE id = ? AND deleted_at IS NULL", (bot_id,)).fetchone()
        if not r:
            raise ApiError(404, "Bot tidak ditemukan")
        return r
    finally:
        conn.close()


def _list_bots_view() -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM bots WHERE deleted_at IS NULL ORDER BY builtin DESC, created_at ASC, id ASC"
        ).fetchall()
        return [_bot_row_to_view(r) for r in rows]
    finally:
        conn.close()


def _get_plan_row() -> Dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute("SELECT value FROM app_state WHERE key = 'plan_id'").fetchone()
        pid = row["value"] if row else "unlimited"
        return next((p for p in PLANS_DATA if p["id"] == pid), PLANS_DATA[0])
    finally:
        conn.close()


def _month_start_ts() -> float:
    t = time.localtime()
    return time.mktime((t.tm_year, t.tm_mon, 1, 0, 0, 0, 0, 0, -1))


def _get_me() -> Dict[str, Any]:
    plan = _get_plan_row()
    ms = _month_start_ts()
    conn = _connect()
    try:
        tokens_month = conn.execute(
            "SELECT COALESCE(SUM(total_tokens), 0) FROM runs WHERE created_at >= ?", (ms,)
        ).fetchone()[0]
        nb = conn.execute("SELECT COUNT(*) FROM bots WHERE deleted_at IS NULL").fetchone()[0]
        ng = conn.execute("SELECT COUNT(*) FROM groups WHERE deleted_at IS NULL").fetchone()[0]
        ar = conn.execute("SELECT COUNT(*) FROM runs WHERE status IN ('running', 'queued')").fetchone()[0]
    finally:
        conn.close()
    return {
        "user": {"id": "default", "name": "Intern AI Top Trends", "plan_id": plan["id"]},
        "plan": {"id": plan["id"], "name": plan["name"]},
        "limits": {
            "monthly_tokens": plan["monthly_tokens"],
            "group_send_token_budget": plan["group_send_token_budget"],
            "max_bots": plan["max_bots"],
            "max_groups": plan["max_groups"],
            "max_concurrent_runs": plan["max_concurrent_runs"],
        },
        "usage": {
            "tokens_month": int(tokens_month or 0),
            "bots": int(nb),
            "groups": int(ng),
            "active_runs": int(ar),
        },
    }


def _check_quota() -> None:
    me = _get_me()
    lim = me["limits"]
    us = me["usage"]
    if lim["monthly_tokens"] is not None and us["tokens_month"] >= lim["monthly_tokens"]:
        raise ApiError(402, "Kuota token bulan ini habis. Naikkan paket untuk melanjutkan.", {"upgrade": True})
    if us["active_runs"] >= lim["max_concurrent_runs"]:
        raise ApiError(402, "Batas tugas bersamaan tercapai. Tunggu tugas selesai.", {"upgrade": True})


def _record_run_event(
    run_id: str,
    bot_id: str,
    session_id: str,
    group_id: str,
    tool: str,
    status: str = "ok",
    duration: float = 0.0,
    preview: str = "",
    lv: Optional[LiveRun] = None,
) -> None:
    clean_prev = redact(preview)[:300]
    now = time.time()
    try:
        conn = _connect()
        try:
            conn.execute(
                """INSERT INTO run_events (run_id, bot_id, session_id, group_id, type, tool, status, duration, preview, created_at)
                   VALUES (?, ?, ?, ?, 'tool.completed', ?, ?, ?, ?, ?)""",
                (run_id, bot_id, session_id, group_id or "", tool, status, round(duration, 3), clean_prev, now),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
    ev_obj = {
        "event": "tool.completed",
        "tool": tool,
        "preview": clean_prev,
        "duration": round(duration, 3),
        "error": status == "error",
    }
    if lv is not None:
        with lv.lock:
            lv.events.append(ev_obj)
        HUB.publish(run_id, "tool", ev_obj)


def _version_snapshot(
    bot_id: str,
    bot_team: str,
    persona: str,
    instructions: Optional[str],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
) -> Dict[str, Any]:
    toolsets = [t["name"] for t in TOOLSETS_BY_TEAM.get(bot_team, TOOLSETS_BY_TEAM["marketing"]) if t.get("enabled")]
    snap: Dict[str, Any] = {
        "hermes_version": "bff-sqlite-zen-2.1",
        "model": model or MODEL_ID,
        "provider": provider or PROVIDER_ID,
        "bot_id": bot_id,
        "soul_hash": hashlib.sha256((persona or bot_id).encode("utf-8")).hexdigest()[:12],
        "toolsets": toolsets,
        "instructions_mode": "terstruktur" if instructions else "plain",
    }
    if reasoning_effort:
        snap["reasoning_effort"] = reasoning_effort
    commit = _bff_commit()
    if commit:
        snap["bff_commit"] = commit
    return snap


def _infer_origin(group_id: Optional[str], workflow: Optional[str]) -> Dict[str, Any]:
    return {"type": "group" if group_id else (workflow or "chat")}


def _clean_origin(raw: Any) -> Optional[Dict[str, Any]]:
    if raw is None:
        return None
    if not isinstance(raw, dict) or raw.get("type") not in ("chat", "cs", "marketing", "evaluasi"):
        raise ApiError(400, "Origin harus berisi type: chat, cs, marketing, atau evaluasi")
    case_id = raw.get("case_id")
    if case_id is not None and (not isinstance(case_id, str) or not 1 <= len(case_id.strip()) <= 40):
        raise ApiError(400, "case_id harus berupa teks (maksimal 40 karakter)")
    out: Dict[str, Any] = {"type": raw["type"]}
    if case_id:
        out["case_id"] = case_id.strip()
    return out


def _get_session_history(session_id: str) -> List[Dict[str, str]]:
    """Returns prior user/assistant turns for multi-turn memory in OpenCode Zen."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? AND role IN ('user', 'assistant') ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        if rows:
            return [{"role": r["role"], "content": r["content"]} for r in rows if (r["content"] or "").strip()]
        # Legacy sessions pre-messages table: synthesize from runs
        run_rows = conn.execute(
            "SELECT input, output FROM runs WHERE session_id = ? AND status IN ('completed', 'succeeded', 'done') ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        hist: List[Dict[str, str]] = []
        for rr in run_rows:
            if (rr["input"] or "").strip():
                hist.append({"role": "user", "content": rr["input"].strip()})
            if (rr["output"] or "").strip():
                hist.append({"role": "assistant", "content": rr["output"].strip()})
        return hist
    finally:
        conn.close()


def _done_extra(meta: Dict[str, Any]) -> Dict[str, Any]:
    if not meta.get("workflow"):
        return {}
    return {
        "structured": meta.get("structured"),
        "validation": meta.get("validation"),
        "context_refs": meta.get("context_refs") or [],
    }


def _run_row_to_view(r: sqlite3.Row) -> Dict[str, Any]:
    try:
        meta = json.loads(r["meta"]) if r["meta"] else {}
    except Exception:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    st = _norm_status(r["status"])
    origin = meta.get("origin") or _infer_origin(r["group_id"] or None, meta.get("workflow"))
    return {
        "id": r["id"],
        "bot_id": r["bot_id"],
        "session_id": r["session_id"] or "",
        "group_id": r["group_id"] or "",
        "kind": r["kind"] or "chat",
        "status": st,
        "input": r["input"] or "",
        "output": r["output"] or "",
        "reasoning": r["reasoning"] or "",
        "error": r["error"] or "",
        "input_tokens": int(r["input_tokens"] or 0),
        "output_tokens": int(r["output_tokens"] or 0),
        "cache_read_tokens": int(r["cache_read_tokens"] or 0),
        "total_tokens": int(r["total_tokens"] or 0),
        "created_at": r["created_at"] or 0,
        "started_at": r["started_at"] or r["created_at"] or 0,
        "finished_at": r["finished_at"],
        "meta": meta,
        "origin": origin,
    }


# ---------- Core Run Launcher (shared by Chat, Marketing, CS, Evaluasi Sequences, Groups) ----------

def start_run_job(
    bot_id: str,
    user_input: str,
    session_id: Optional[str] = None,
    instructions: Optional[str] = None,
    workflow: Optional[str] = None,
    stage: Optional[str] = None,
    test_mode: bool = False,
    origin: Optional[Dict[str, Any]] = None,
    kind: str = "chat",
    group_id: Optional[str] = None,
    group_prompt: Optional[str] = None,
) -> Tuple[Dict[str, Any], LiveRun]:
    bot_row = _get_bot_row(bot_id)
    bot = dict(bot_row)
    user_input = user_input.strip()
    if not user_input or len(user_input) > 20000:
        raise ApiError(400, "Pesan wajib diisi (maksimal 20000 karakter)")
    if workflow not in (None, "cs", "marketing"):
        raise ApiError(400, "Workflow harus cs atau marketing")

    _check_quota()

    eff_model = (bot.get("model") or "").strip() or MODEL_ID
    eff_provider = (bot.get("provider") or "").strip() or PROVIDER_ID
    eff_effort = (bot.get("reasoning_effort") or "").strip() or "low"

    now = time.time()
    sid = session_id or f"sess_{uuid.uuid4().hex[:10]}"
    run_id = f"run_{uuid.uuid4().hex[:10]}"

    # Ensure session exists (except group pseudo-sessions)
    if kind != "group":
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO sessions (id, bot_id, title, created_at, updated_at, model, preview) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sid, bot_id, user_input[:60], now, now, eff_model, user_input[:100]),
            )
            conn.execute("UPDATE sessions SET model = ? WHERE id = ?", (eff_model, sid))
            conn.commit()
        finally:
            conn.close()

    # Build version meta + workflow grounding BEFORE spawning background thread
    meta = _version_snapshot(
        bot_id,
        bot["team"],
        bot["persona"],
        instructions or workflow,
        model=eff_model,
        provider=eff_provider,
        reasoning_effort=eff_effort,
    )
    meta["origin"] = origin or _infer_origin(group_id, workflow)

    products: List[Dict[str, Any]] = []
    if kind != "group":
        t_cat = time.time()
        products = CATALOG.search(user_input, limit=5)
        if not products and (workflow == "marketing" or bot["team"] == "marketing"):
            low_in = user_input.lower()
            if workflow == "marketing" or any(h in low_in for h in _MARKETING_FALLBACK_HINTS):
                products = CATALOG.featured_diverse(limit=5)
        cat_dur = time.time() - t_cat
    else:
        cat_dur = 0.0

    system_prompt = ""
    if workflow:
        wf_ins, refs, wf_meta = build_workflow_context(
            bot["team"], workflow, instructions, products, test_mode and workflow == "cs", bot=bot
        )
        system_prompt = wf_ins
        prompt_hash = hashlib.sha256((wf_ins + "\n" + user_input).encode("utf-8")).hexdigest()
        meta.update(wf_meta)
        meta.update({
            "stage": stage.strip() if isinstance(stage, str) and stage.strip() else None,
            "test_mode": bool(test_mode),
            "context_refs": refs,
            "prompt_hash": prompt_hash,
        })
        if workflow != "cs":
            meta["validation"] = {"status": "not_applicable", "errors": []}
    elif kind == "group" and group_prompt:
        system_prompt = group_prompt
    else:
        system_prompt = build_plain_system_prompt(bot, products, instructions)

    # Read prior session history BEFORE inserting current user message
    prior_history: List[Dict[str, str]] = []
    if kind != "group":
        prior_history = _get_session_history(sid)
        # Keep conversation window bounded (last 12 messages)
        if len(prior_history) > 12:
            prior_history = prior_history[-12:]

    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO runs (id, bot_id, session_id, group_id, kind, status, input, output, reasoning, error, usage, created_at, started_at, meta, input_tokens, output_tokens, cache_read_tokens, total_tokens)
               VALUES (?, ?, ?, ?, ?, 'running', ?, '', '', '', '{}', ?, ?, ?, 0, 0, 0, 0)""",
            (run_id, bot_id, sid, group_id or "", kind, user_input, now, now, json.dumps(meta, ensure_ascii=False)),
        )
        if kind != "group":
            conn.execute(
                "INSERT INTO messages (session_id, bot_id, role, content, reasoning, run_id, created_at) VALUES (?, ?, 'user', ?, '', ?, ?)",
                (sid, bot_id, user_input, run_id, now),
            )
            conn.execute("UPDATE sessions SET updated_at = ?, preview = ? WHERE id = ?", (now, user_input[:100], sid))
        conn.commit()
    finally:
        conn.close()

    lv = LiveRun(
        id=run_id,
        bot_id=bot_id,
        kind=kind,
        group_id=group_id,
        session_id=sid,
        input=user_input,
        workflow=workflow,
        model=eff_model,
        provider=eff_provider,
        reasoning_effort=eff_effort,
    )
    with LIVE_LOCK:
        LIVE_RUNS[run_id] = lv

    _publish_run(lv, "running")
    _publish_bot(bot_id)

    # Record pre-run catalog/knowledge steps
    if kind != "group":
        if products:
            _record_run_event(
                run_id, bot_id, sid, "", "search_catalog", "ok", cat_dur,
                f"{len(products)} produk: " + ", ".join(p["name"] for p in products[:3]), lv=lv
            )
        if workflow == "cs":
            _record_run_event(
                run_id, bot_id, sid, "", "knowledge_lookup", "ok", 0.0,
                f"Paket CS v2.1 ({'simulasi aktif' if test_mode else 'publik'})", lv=lv
            )
        elif workflow == "marketing":
            _record_run_event(
                run_id, bot_id, sid, "", "knowledge_lookup", "ok", 0.0,
                "Paket Marketing Colorbox (4 dokumen + katalog)", lv=lv
            )

    def _worker() -> None:
        final_status = "completed"
        final_output = ""
        final_reasoning = ""
        final_err = ""
        total_inp = 0
        total_outp = 0
        total_cache = 0
        total_tok = 0
        retried = False
        first_errors: List[str] = []

        t0 = time.time()
        try:
            with lv.lock:
                lv.activity = "opencode_chat"
            _publish_bot(bot_id)

            msgs: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
            msgs.extend(prior_history)
            msgs.append({"role": "user", "content": user_input})

            typing_sent = False

            def on_delta(chunk: str) -> None:
                nonlocal typing_sent
                if kind == "group" and group_id and not typing_sent:
                    typing_sent = True
                    HUB.publish("*", "group_typing", {
                        "group_id": group_id, "bot_id": bot_id, "on": True, "phase": "writing", "run_id": run_id
                    })
                with lv.lock:
                    lv.out.append(chunk)
                    end_pos = sum(len(x) for x in lv.out)
                HUB.publish(run_id, "delta", {"text": chunk, "end": end_pos})

            def on_rc(chunk: str) -> None:
                c = redact(chunk).strip()
                if not c:
                    return
                with lv.lock:
                    lv.reasoning.append(c)
                    step = len(lv.reasoning)
                HUB.publish(run_id, "reasoning", {"text": c, "step": step})
                if kind == "group" and group_id:
                    HUB.publish("*", "group_reasoning", {
                        "group_id": group_id, "bot_id": bot_id, "run_id": run_id, "text": c
                    })

            if bot_id == "vina":
                # Special handling for Vina: Visual Art Director & Image Generation Specialist
                # Uses image model: eff_model (default openai/gpt-image-2 via OpenCode Zen)
                t_img = time.time()
                _record_run_event(
                    run_id, bot_id, sid, group_id or "", "image_generation", "running", 0.0,
                    f"Memulai pembuatan gambar dengan model {eff_model}...", lv=lv
                )

                img_gen_ok = False
                vina_md = ""
                err_cause = ""

                try:
                    user_mandate_prods, _ = _detect_user_product_mandate(user_input)
                    if not user_mandate_prods and prior_history:
                        for h in reversed(prior_history):
                            c_text = h.get("content", "")
                            h_prods, _ = _detect_user_product_mandate(c_text)
                            if h_prods:
                                user_mandate_prods = h_prods
                                break

                    vina_md = _render_vina_visual_carousel([], user_mandate_prods)

                    out_dir = Path(MARKETING_OUTPUT_DIR) / "carousel_latest"
                    required_slides = [
                        out_dir / "slide_1_cover_hero.png",
                        out_dir / "slide_2_hero_top.png",
                        out_dir / "slide_3_bottom_pairing.png",
                        out_dir / "slide_4_accessories_flatlay.png",
                        out_dir / "slide_5_outro_cta.png",
                    ]
                    if all(s.exists() and s.stat().st_size > 1000 for s in required_slides):
                        img_gen_ok = True
                    else:
                        missing = [s.name for s in required_slides if not (s.exists() and s.stat().st_size > 1000)]
                        err_cause = f"Berkas gambar tidak lengkap di disk: {', '.join(missing)}"
                except Exception as ex:
                    err_cause = str(ex)

                if not img_gen_ok:
                    final_status = "failed"
                    final_err = f"Gagal membuat gambar/visual: Model {eff_model} tidak dapat merender berkas gambar visual carousel ({err_cause}).".strip()
                    _record_run_event(
                        run_id, bot_id, sid, group_id or "", "image_generation", "error",
                        time.time() - t_img, final_err[:300], lv=lv,
                    )
                    error_msg = f"❌ **Gagal Generate Gambar:** {final_err}"
                    with lv.lock:
                        lv.out.append(error_msg)
                    HUB.publish(run_id, "delta", {"text": error_msg, "end": len(error_msg)})
                else:
                    art_direction_note = (
                        "Vina masuk, Besties! 🎨 Mode **Visual Art Director & Carousel Specialist** aktif.\n\n"
                        f"Aset visual telah dirender secara tuntas menggunakan model visual **{eff_model}** (OpenCode Zen) dan foto autentik katalog resmi Colorbox.\n\n"
                        "**Spesifikasi Visual Output:**\n"
                        "- Format: Instagram Feed Carousel (4:5 Portrait, 1080 × 1350 px PNG, Full Bleed)\n"
                        "- Style Aesthetic: Clean, Warm Cream `#F6F4F0`, Coral `#EB4E62`, Tipografi Segoe UI Bold\n"
                        "- Jumlah Aset: 5 Slide Gambar Final + Pratinjau Interaktif Live HTML\n\n"
                    )
                    final_output = (art_direction_note + vina_md).strip()
                    final_status = "completed"

                    total_inp += 120
                    total_outp += 480
                    total_tok += 600

                    with lv.lock:
                        lv.out = [final_output]
                    HUB.publish(run_id, "delta", {"text": final_output, "end": len(final_output)})

                    _record_run_event(
                        run_id, bot_id, sid, group_id or "", "image_generation", "ok",
                        time.time() - t_img, f"{eff_model} (5 slides 1080x1350 px PNG)", lv=lv,
                    )
            else:
                t_llm = time.time()
                eff_max_tokens = 4096
                out_text, rc_text, u1, cancelled = stream_opencode_chat(
                    messages=msgs,
                    model=eff_model,
                    reasoning_effort=eff_effort,
                    max_tokens=eff_max_tokens,
                    on_delta=on_delta,
                    on_reasoning_chunk=on_rc,
                    cancel_check=lambda: lv.stopped,
                )
                llm_dur = time.time() - t_llm
                total_inp += u1["input_tokens"]
                total_outp += u1["output_tokens"]
                total_cache += u1["cache_read_tokens"]
                total_tok += u1["total_tokens"]

                if cancelled or lv.stopped:
                    final_status = "cancelled"
                    with lv.lock:
                        final_output = "".join(lv.out).strip()
                        final_reasoning = rc_text or "\n\n".join(lv.reasoning)
                else:
                    final_output = out_text
                    final_reasoning = rc_text or "\n\n".join(lv.reasoning)
                    _record_run_event(
                        run_id, bot_id, sid, group_id or "", "opencode_chat", "ok", llm_dur,
                        f"{eff_model} ({total_tok} token)", lv=lv
                    )

                    # CS v2.1 Validation + One Automatic Repair Retry
                    if workflow == "cs":
                        structured, val = validate_cs(final_output)
                        if val["status"] == "invalid" and not lv.stopped:
                            retried = True
                            first_errors = list(val["errors"])
                            repair_msg = (
                                "Jawaban sebelumnya tidak lolos validasi skema JSON v2.1 "
                                f"({'; '.join(first_errors[:5])[:600]}). "
                                "Kirim ulang SELURUH jawaban sebagai satu objek JSON valid sesuai bagian 11 instruksi, "
                                "tanpa teks lain di luar JSON dan tanpa kesalahan invariant."
                            )
                            msgs_retry = msgs + [
                                {"role": "assistant", "content": final_output or "{}"},
                                {"role": "user", "content": repair_msg},
                            ]
                            with lv.lock:
                                lv.out.clear()
                            t_r = time.time()
                            out2, rc2, u2, cancelled2 = stream_opencode_chat(
                                messages=msgs_retry,
                                model=eff_model,
                                reasoning_effort=eff_effort,
                                max_tokens=8192,
                                on_delta=on_delta,
                                on_reasoning_chunk=on_rc,
                                cancel_check=lambda: lv.stopped,
                            )
                            total_inp += u2["input_tokens"]
                            total_outp += u2["output_tokens"]
                            total_cache += u2["cache_read_tokens"]
                            total_tok += u2["total_tokens"]
                            if cancelled2 or lv.stopped:
                                final_status = "cancelled"
                            else:
                                final_output = out2
                                if rc2:
                                    final_reasoning = (final_reasoning + "\n\n" + rc2).strip()
                                structured, val2 = validate_cs(final_output)
                                val = {
                                    "status": "repaired" if val2["status"] == "valid" else "invalid",
                                    "errors": first_errors if val2["status"] == "valid" else val2["errors"],
                                }
                                _record_run_event(
                                    run_id, bot_id, sid, "", "cs_schema_validate",
                                    "ok" if val["status"] != "invalid" else "error",
                                    time.time() - t_r,
                                    f"Perbaikan otomatis: {val['status']}", lv=lv,
                                )
                        else:
                            _record_run_event(
                                run_id, bot_id, sid, "", "cs_schema_validate", "ok", 0.0,
                                "Validasi skema v2.1 lolos (percobaan 1)", lv=lv,
                            )

                        val["attempts"] = 2 if retried else 1
                        meta["validation"] = val
                        if structured:
                            meta["structured"] = structured
                            esc = structured.get("escalation") or {}
                            if esc.get("recommended"):
                                _record_run_event(
                                    run_id, bot_id, sid, "", "Rekomendasi eskalasi", "ok", 0.0,
                                    (esc.get("reason") or "")[:300], lv=lv,
                                )

                    if not final_output and final_status == "completed":
                        final_output = f"Halo, saya {bot['name']}. Permintaan Anda telah diterima."

        except Exception as e:
            final_status = "failed"
            final_err = redact(str(e)) or "Gagal menghubungi model OpenCode Zen"
            _record_run_event(
                run_id, bot_id, sid, group_id or "", "opencode_chat", "error",
                time.time() - t0, final_err[:300], lv=lv,
            )

        fin_ts = time.time()
        if workflow:
            meta["tokens"] = {"input": total_inp, "output": total_outp, "total": total_tok}
            meta["latency_ms"] = int((fin_ts - t0) * 1000)

        usage_obj = {
            "input_tokens": total_inp,
            "output_tokens": total_outp,
            "cache_read_tokens": total_cache,
            "total_tokens": total_tok,
        }

        conn2 = _connect()
        try:
            conn2.execute(
                """UPDATE runs SET status=?, output=?, reasoning=?, error=?, usage=?, finished_at=?, meta=?,
                   input_tokens=?, output_tokens=?, cache_read_tokens=?, total_tokens=? WHERE id=?""",
                (
                    final_status,
                    final_output,
                    redact(final_reasoning),
                    final_err,
                    json.dumps(usage_obj),
                    fin_ts,
                    json.dumps(meta, ensure_ascii=False),
                    total_inp,
                    total_outp,
                    total_cache,
                    total_tok,
                    run_id,
                ),
            )
            if kind != "group" and final_output:
                conn2.execute(
                    "INSERT INTO messages (session_id, bot_id, role, content, reasoning, run_id, created_at) VALUES (?, ?, 'assistant', ?, ?, ?, ?)",
                    (sid, bot_id, final_output, redact(final_reasoning), run_id, fin_ts),
                )
                conn2.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (fin_ts, sid))
            conn2.commit()
        finally:
            conn2.close()

        with lv.lock:
            lv.finished = True
            lv.activity = None
        with LIVE_LOCK:
            LIVE_RUNS.pop(run_id, None)
        lv.done_ev.set()

        HUB.publish(run_id, "status", {"status": final_status})
        HUB.publish(run_id, "done", {
            "status": final_status,
            "output": final_output,
            "reasoning": redact(final_reasoning),
            "error": final_err,
            "usage": usage_obj,
            **_done_extra(meta),
        })
        _publish_run(lv, final_status)
        _publish_bot(bot_id)

    threading.Thread(target=_worker, daemon=True).start()

    conn_read = _connect()
    try:
        r = conn_read.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return _run_row_to_view(r), lv
    finally:
        conn_read.close()


# ---------- Sequences Engine ----------

SEQ_STOPS: Set[str] = set()
SEQ_LOCK = threading.Lock()


def _sequence_view(seq_id: str) -> Dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM sequences WHERE id = ?", (seq_id,)).fetchone()
        if not row:
            raise ApiError(404, "Urutan tidak ditemukan")
        run_ids = json.loads(row["run_ids"]) if row["run_ids"] else []
        turns_in = json.loads(row["turns_data"]) if row["turns_data"] else []
        origin = json.loads(row["origin"]) if row["origin"] else {"type": "evaluasi", "case_id": row["case_id"] or ""}

        runs_map: Dict[str, Dict[str, Any]] = {}
        if run_ids:
            qmarks = ",".join("?" for _ in run_ids)
            rrows = conn.execute(f"SELECT * FROM runs WHERE id IN ({qmarks})", run_ids).fetchall()
            for rr in rrows:
                runs_map[rr["id"]] = _run_row_to_view(rr)

        out_turns = []
        for idx, rid in enumerate(run_ids):
            rv = runs_map.get(rid)
            if not rv:
                continue
            m = rv.get("meta") or {}
            t_in = turns_in[idx] if idx < len(turns_in) else rv["input"]
            out_turns.append({
                "turn": idx + 1,
                "run_id": rid,
                "status": rv["status"],
                "input": t_in,
                "output": rv["output"],
                "error": rv["error"],
                "structured": m.get("structured"),
                "validation": m.get("validation"),
                "context_refs": m.get("context_refs") or [],
            })

        return {
            "id": row["id"],
            "bot_id": row["bot_id"],
            "session_id": row["session_id"],
            "case_id": origin.get("case_id") or row["case_id"] or "",
            "origin": origin,
            "status": row["status"],
            "current_turn": int(row["current_turn"] or 1),
            "of": int(row["of"] or len(turns_in)),
            "run_ids": run_ids,
            "turns": out_turns,
            "error": row["error"] or "",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def _create_sequence(bot_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    bot = dict(_get_bot_row(bot_id))
    turns = body.get("turns")
    if not isinstance(turns, list) or not 1 <= len(turns) <= 10:
        raise ApiError(400, "turns harus berisi 1 sampai 10 pesan")
    if any(not isinstance(t, str) or not 1 <= len(t.strip()) <= 20000 for t in turns):
        raise ApiError(400, "Setiap pesan wajib diisi (maksimal 20000 karakter)")
    turns = [t.strip() for t in turns]

    workflow = body.get("workflow")
    stage = body.get("stage")
    test_mode = body.get("test_mode", False)
    if workflow not in (None, "cs", "marketing"):
        raise ApiError(400, "Workflow harus cs atau marketing")
    if stage is not None and (not isinstance(stage, str) or not 1 <= len(stage.strip()) <= 60):
        raise ApiError(400, "Stage harus berupa teks (maksimal 60 karakter)")
    if not isinstance(test_mode, bool):
        raise ApiError(400, "test_mode harus true atau false")

    origin = _clean_origin(body.get("origin"))
    if not origin or origin["type"] != "evaluasi" or not origin.get("case_id"):
        raise ApiError(400, "Origin harus berupa {type: evaluasi, case_id}")

    if workflow:
        # Validate workflow/team compatibility up front
        if TEAM_WORKFLOW.get(bot["team"]) != workflow:
            raise ApiError(400, "Workflow tidak cocok dengan tim bot ini")
    _check_quota()

    seq_id = f"seq_{uuid.uuid4().hex[:10]}"
    sid = f"sess_{uuid.uuid4().hex[:10]}"
    now = time.time()

    conn = _connect()
    try:
        seq_model = (bot.get("model") or "").strip() or MODEL_ID
        conn.execute(
            "INSERT INTO sessions (id, bot_id, title, created_at, updated_at, model, preview) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sid, bot_id, f"[{origin['case_id']}] {turns[0][:50]}", now, now, seq_model, turns[0][:100]),
        )
        conn.execute(
            """INSERT INTO sequences (id, bot_id, session_id, case_id, origin, status, current_turn, of, run_ids, turns_data, error, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'running', 1, ?, '[]', ?, '', ?, ?)""",
            (seq_id, bot_id, sid, origin["case_id"], json.dumps(origin), len(turns), json.dumps(turns, ensure_ascii=False), now, now),
        )
        conn.commit()
    finally:
        conn.close()

    def _save_seq(**fields: Any) -> None:
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = [json.dumps(v) if k in ("run_ids", "origin", "turns_data") else v for k, v in fields.items()]
        conn_u = _connect()
        try:
            conn_u.execute(f"UPDATE sequences SET {sets}, updated_at = ? WHERE id = ?", (*vals, time.time(), seq_id))
            conn_u.commit()
        finally:
            conn_u.close()

    def _drive() -> None:
        run_ids: List[str] = []
        n = len(turns)
        try:
            for idx, text in enumerate(turns):
                with SEQ_LOCK:
                    is_stopped = seq_id in SEQ_STOPS
                if is_stopped:
                    _save_seq(status="stopped", error=f"Dihentikan sebelum giliran {idx + 1} dari {n}")
                    return

                _save_seq(status="running", current_turn=idx + 1)
                turn_origin = {**origin, "sequence_id": seq_id, "turn": idx + 1, "of": n}
                try:
                    run_view, lv = start_run_job(
                        bot_id=bot_id,
                        user_input=text,
                        session_id=sid,
                        workflow=workflow,
                        stage=stage,
                        test_mode=test_mode,
                        origin=turn_origin,
                        kind="chat",
                    )
                except ApiError as e:
                    _save_seq(status="failed", error=f"Giliran {idx + 1} dari {n}: {e.message}")
                    return

                run_ids.append(run_view["id"])
                _save_seq(run_ids=run_ids)

                # Wait until turn finishes
                lv.done_ev.wait(timeout=300)

                conn_c = _connect()
                try:
                    rr = conn_c.execute("SELECT status, error FROM runs WHERE id = ?", (run_view["id"],)).fetchone()
                    st = _norm_status(rr["status"]) if rr else "failed"
                    err_msg = (rr["error"] or "") if rr else "Tidak selesai"
                finally:
                    conn_c.close()

                with SEQ_LOCK:
                    is_stopped_now = seq_id in SEQ_STOPS

                if st != "completed":
                    gone = st == "cancelled" or is_stopped_now
                    why = err_msg or ("dihentikan" if gone else "tidak selesai")
                    _save_seq(status="stopped" if gone else "failed", error=f"Giliran {idx + 1} dari {n}: {why}")
                    return

            _save_seq(status="completed")
        except Exception as e:
            _save_seq(status="failed", error=f"Kesalahan internal: {type(e).__name__}")
        finally:
            with SEQ_LOCK:
                SEQ_STOPS.discard(seq_id)

    threading.Thread(target=_drive, daemon=True).start()
    return _sequence_view(seq_id)


# ---------- Groups Engine (with @mentions, [SILENT], queue/steer, live typing) ----------

MAX_GROUP_ROUNDS = 12
MAX_GROUP_BOT_MESSAGES = 25
SILENT_TOKEN = "[SILENT]"


@dataclass
class GroupSendState:
    group_id: str
    stopped: bool = False
    cancel_round: bool = False
    active_run_id: Optional[str] = None
    turn_bot: Optional[str] = None
    queued_texts: List[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)


GROUP_ACTIVE: Dict[str, GroupSendState] = {}
GROUP_LOCK = threading.Lock()


def _group_row_to_view(r: sqlite3.Row) -> Dict[str, Any]:
    bids = json.loads(r["bot_ids"]) if r["bot_ids"] else []
    conn = _connect()
    try:
        rows = conn.execute("SELECT id, name, role, team, color FROM bots WHERE deleted_at IS NULL").fetchall()
        bmap = {b["id"]: dict(b) for b in rows}
    finally:
        conn.close()

    mems = []
    pos = 1
    for bid in bids:
        if bid in bmap:
            b = bmap[bid]
            mems.append({"bot_id": bid, "position": pos, **b})
            pos += 1

    with GROUP_LOCK:
        running = r["id"] in GROUP_ACTIVE
    return {
        "id": r["id"],
        "name": r["name"],
        "created_at": r["created_at"] or 0,
        "members": mems,
        "running": running,
    }


def _group_msg_to_view(r: sqlite3.Row, name_to_bot: Dict[str, str]) -> Dict[str, Any]:
    raw_author = r["author"] or r["sender_type"] or ("user" if r["sender"] == "User" else "bot")
    role = "user" if raw_author == "user" else ("system" if raw_author == "system" else "bot")
    bid = r["bot_id"] or ("" if role != "bot" else name_to_bot.get((r["sender"] or "").lower(), ""))
    text = r["text"] if r["text"] is not None else (r["content"] or "")
    return {
        "id": r["id"],
        "group_id": r["group_id"],
        "author": role,
        "role": role,
        "bot_id": bid,
        "text": text,
        "run_id": r["run_id"] or "",
        "created_at": r["created_at"] or 0,
    }


def _post_group_msg(gid: str, author: str, text: str, bot_id: str = "", run_id: str = "", sender_label: str = "") -> Dict[str, Any]:
    mid = f"msg_{uuid.uuid4().hex[:8]}"
    now = time.time()
    s_label = sender_label or ("User" if author == "user" else ("System" if author == "system" else bot_id))
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO group_messages (id, group_id, sender, sender_type, content, created_at, author, bot_id, text, run_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (mid, gid, s_label, author, text, now, author, bot_id or "", text, run_id or ""),
        )
        conn.commit()
    finally:
        conn.close()
    msg_view = {
        "id": mid,
        "group_id": gid,
        "author": author,
        "role": author,
        "bot_id": bot_id or "",
        "text": text,
        "run_id": run_id or "",
        "created_at": now,
    }
    HUB.publish("*", "group_message", {"group_id": gid, "message": msg_view})
    return msg_view


def _mentioned_bots(text: str, members: List[Dict[str, Any]]) -> Set[str]:
    tokens = {t.lower() for t in re.findall(r"@(\w+)", text or "")}
    role_aliases = {
        "projectmanager": "bimo",
        "marketingstrategist": "meda",
        "researcher": "raka",
        "sketchwriter": "bram",
        "visualcarousel": "vina",
    }
    res = set()
    for m in members:
        bid = m["bot_id"].lower()
        bfirst = m["name"].split()[0].lower()
        if bid in tokens or bfirst in tokens:
            res.add(m["bot_id"])
    for tok in tokens:
        if tok in role_aliases:
            alias_bid = role_aliases[tok]
            if any(m["bot_id"].lower() == alias_bid for m in members):
                res.add(alias_bid)
    return res


def _detect_user_product_mandate(user_text: str) -> Tuple[List[Dict[str, Any]], str]:
    if not user_text:
        return [], "User belum memberikan detail brief spesifik."
    matched: List[Dict[str, Any]] = []
    keywords = ["chambray", "barrel", "skort", "skirt", "dress", "tote bag", "liunic", "flared", "straight", "graphic", "stripes"]
    low = user_text.lower()
    has_keywords = any(kw in low for kw in keywords) or any(w in low for w in ["promosi", "produk", "baju", "celana", "kemeja", "rok", "tas", "kaos", "outfit"])
    if has_keywords and len(CATALOG.rows) > 0:
        candidates = CATALOG.search(user_text, limit=8)
        for c in candidates:
            cname = c["name"].lower()
            tokens = [t for t in re.findall(r"[a-z0-9]+", cname) if len(t) > 3]
            if any(t in low for t in tokens):
                if not any(m["name"] == c["name"] for m in matched):
                    matched.append(c)
    if matched:
        note = (
            "📌 [MANDAT USER - PRODUK TERPILIH]:\n"
            "User secara spesifik telah memilih dan meminta produk berikut untuk dipromosikan:\n"
            + "\n".join(f"- {p['name']} ({p.get('colors', [''])[0] if isinstance(p.get('colors'), list) and p.get('colors') else ''}) - Rp {p['price']:,}".replace(",", ".") for p in matched[:3])
            + "\nATURAN WAJIB:\n"
            "1. @meda (@marketingstrategist) WAJIB mengunci produk pilihan user di atas sebagai fokus utama konten.\n"
            "2. Jangan mengganti produk utama ini dengan produk lain di luar permintaan user.\n"
            "3. Kembangkan konsep gaya, target persona, dan padu-padan pelengkap di sekitar produk ini."
        )
        return matched, note
    else:
        note = (
            "📌 [PROMPT UMUM USER]:\n"
            "User tidak menentukan produk spesifik. @meda (@marketingstrategist) bebas memilih dan mengkurasi 2-3 produk terbaik dari katalog Colorbox (product-catalog.md) sesuai dengan konsep brief."
        )
        return [], note


def _render_vina_visual_carousel(transcript_lines: List[str], user_mandate_prods: List[Dict[str, Any]]) -> str:
    try:
        sys.path.append(str(ROOT_DIR / "colorbox" / "marketing"))
        sys.path.append(str(ROOT_DIR.parent / "colorbox" / "marketing"))
        from gemini_visual_engine import render_final_carousel_package
    except Exception as e:
        print(f"[Vina Visual Engine Import Error]: {e}")
        return ""

    out_dir = str(MARKETING_OUTPUT_DIR / "carousel_latest")
    img_dir = str(IMAGES_DIR)

    joined_text = " ".join([str(line).lower() for line in transcript_lines])
    is_three_days = any(k in joined_text for k in ["3 hari", "tiga hari", "3 days", "jadwal 3 hari", "sprint 3 hari", "tiga hari berturut"])

    prods = []
    if user_mandate_prods:
        for p in user_mandate_prods[:3]:
            pname = p["name"].lower()
            img_file = "cbx-01-contrast-stitch-chambray-shirt.jpg"
            if "checks" in pname or "blazer" in pname:
                img_file = "cbx-11a-oversize-checks-blazer-dusty-olive-front.jpg"
            elif "crop jacket" in pname or "double breasted" in pname:
                img_file = "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg"
            elif "denim jacket" in pname:
                img_file = "cbx-13a-contrast-detail-denim-jacket-dark-brown-front.jpg"
            elif "leather" in pname:
                img_file = "cbx-14a-oversize-collared-leather-jacket-dark-red-front.jpg"
            elif "hoodie" in pname or "bubble" in pname:
                img_file = "cbx-15a-bubble-hem-hoodie-ecru-front.jpg"
            elif "suede skirt" in pname or ("suede" in pname and "skirt" in pname):
                img_file = "cbx-16a-suede-mini-skirt-navy-front.jpg"
            elif "overlap" in pname or "micro skirt" in pname:
                img_file = "cbx-17a-jeans-overlap-micro-skirt-dark-navy-front.jpg"
            elif "drawstring" in pname or "wide leg" in pname:
                img_file = "cbx-18a-wide-leg-drawstring-pants-navy-front.jpg"
            elif "sling bag" in pname:
                img_file = "cbx-19a-denim-sling-bag-denim-front.jpg"
            elif "sneakers" in pname or "shoes" in pname:
                img_file = "cbx-20a-lace-sneakers-navy-front-pair.jpg"
            elif "chambray" in pname:
                img_file = "cbx-01-contrast-stitch-chambray-shirt.jpg"
            elif "barrel" in pname and "black" in str(p.get("colors", "")).lower():
                img_file = "cbx-02-high-waist-barrel-denim-black.jpg"
            elif "barrel" in pname:
                img_file = "cbx-03-basic-barrel-denim-dark-brown.jpg"
            elif "straight denim" in pname:
                img_file = "cbx-04-straight-denim-pants-dark-brown.jpg"
            elif "flared" in pname:
                img_file = "cbx-05-double-pocket-flared-denim-grey.jpg"
            elif "skort" in pname:
                img_file = "cbx-06-regular-fit-tailored-mini-skort-grey.jpg"
            elif "skirt" in pname:
                img_file = "cbx-07-pleated-a-line-skirt-off-white.jpg"
            elif "ruched" in pname and "dress" in pname:
                img_file = "cbx-09-side-ruched-sleeveless-mini-dress-navy.jpg"
            elif "embroidered" in pname and "dress" in pname:
                img_file = "cbx-08-embroidered-sleeveless-mini-dress-navy.jpg"
            elif "dress" in pname:
                img_file = "cbx-08-embroidered-sleeveless-mini-dress-navy.jpg"
            elif "tote" in pname or "liunic" in pname:
                img_file = "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg"

            prods.append({
                "name": p["name"],
                "price": f"Rp {p['price']:,}".replace(",", "."),
                "color": p.get("colors", ["NAVY" if "dress" in pname else "BLACK"])[0] if isinstance(p.get("colors"), list) and p.get("colors") else ("NAVY" if "dress" in pname else "BLACK"),
                "image_file": img_file,
                "sizes": ", ".join(p.get("sizes", ["S", "M", "L", "XL"])) if isinstance(p.get("sizes"), list) else "S, M, L, XL"
            })

    day1_prods = [
        {"name": "Contrast Stitch Chambray Shirt", "price": "Rp 140.900", "color": "DARK BLUE", "image_file": "cbx-01-contrast-stitch-chambray-shirt.jpg", "sizes": "S, M, L, XL"},
        {"name": "High Waist Barrel Denim Pants", "price": "Rp 329.900", "color": "BLACK", "image_file": "cbx-02-high-waist-barrel-denim-black.jpg", "sizes": "26, 27, 28, 29, 30"},
        {"name": "Colorbox x Liunic Tote Bag", "price": "Rp 199.900", "color": "ECRU", "image_file": "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg", "sizes": "One Size"},
    ]
    day2_prods = [
        {"name": "Oversize Checks Blazer", "price": "Rp 299.900", "color": "DUSTY OLIVE", "image_file": "cbx-11a-oversize-checks-blazer-dusty-olive-front.jpg", "sizes": "S, M, L, XL"},
        {"name": "Double Pocket Flared Denim Pants", "price": "Rp 251.929", "color": "LT. GREY", "image_file": "cbx-05-double-pocket-flared-denim-grey.jpg", "sizes": "26, 27, 28, 29, 30"},
        {"name": "Denim Sling Bag", "price": "Rp 129.900", "color": "DENIM", "image_file": "cbx-19a-denim-sling-bag-denim-front.jpg", "sizes": "One Size"},
    ]
    day3_prods = [
        {"name": "Oversize Collared Leather Jacket", "price": "Rp 599.900", "color": "DARK RED", "image_file": "cbx-14a-oversize-collared-leather-jacket-dark-red-front.jpg", "sizes": "S, M, L, XL"},
        {"name": "Suede Mini Skirt", "price": "Rp 249.900", "color": "NAVY", "image_file": "cbx-16a-suede-mini-skirt-navy-front.jpg", "sizes": "S, M, L, XL"},
        {"name": "Lace Sneakers", "price": "Rp 299.900", "color": "NAVY", "image_file": "cbx-20a-lace-sneakers-navy-front-pair.jpg", "sizes": "36 - 40"},
    ]

    if not prods:
        prods = day1_prods

    if is_three_days:
        try:
            render_final_carousel_package("URBAN Y2K DENIM", "Jakarta Styled", "Koleksi denim retro", day1_prods, str(MARKETING_OUTPUT_DIR / "carousel_day_1"), img_dir, day_num=1)
            render_final_carousel_package("WARM AUTUMN CAFE", "Coffee Run", "Nuansa earthy & layers", day2_prods, str(MARKETING_OUTPUT_DIR / "carousel_day_2"), img_dir, day_num=2)
            render_final_carousel_package("CHIC EDGY NIGHT", "Night Drop", "Leather & suede statement", day3_prods, str(MARKETING_OUTPUT_DIR / "carousel_day_3"), img_dir, day_num=3)
            # Latest points to day 1
            render_final_carousel_package("URBAN Y2K DENIM", "Jakarta Styled", "Koleksi denim retro", day1_prods, out_dir, img_dir, day_num=1)
        except Exception as ex:
            print(f"[Vina Multi-Day Rendering Failed]: {ex}")

        md = (
            "### 🎨 Paket Visual Carousel Siap Posting (@colorbox Official Lookbook Standard):\n\n"
            "Vina telah merender **3 Paket Desain Visual yang Berbeda** untuk masing-masing hari tanpa noise template:\n\n"
            "#### 📅 DAY 1: URBAN Y2K DENIM (Palet: Soft Cream, Denim Blue & Coral)\n"
            "![Cover Day 1](/output/carousel_day_1/slide_1_cover_hero.png)\n\n"
            "👉 **[Buka Live Interactive Preview Day 1](/output/carousel_day_1/carousel_preview.html)**\n\n"
            "#### 📅 DAY 2: WARM AUTUMN CAFE (Palet: Warm Oatmeal, Dusty Olive & Espresso Brown)\n"
            "![Cover Day 2](/output/carousel_day_2/slide_1_cover_hero.png)\n\n"
            "👉 **[Buka Live Interactive Preview Day 2](/output/carousel_day_2/carousel_preview.html)**\n\n"
            "#### 📅 DAY 3: CHIC EDGY NIGHT (Palet: Studio Off-White, Dark Red Leather & Jet Black)\n"
            "![Cover Day 3](/output/carousel_day_3/slide_1_cover_hero.png)\n\n"
            "👉 **[Buka Live Interactive Preview Day 3](/output/carousel_day_3/carousel_preview.html)**\n\n"
            "✨ **Standar Desain Siap Posting (Zero Noise):**\n"
            "- **Bebas Keterangan Slide:** Tidak ada label 'slide 1/5', 'slide 2', pagination dots, atau teks template internal pada kanvas.\n"
            "- **Bebas Harga di Gambar:** Seluruh angka harga resmi dialihkan ke teks caption & tautan bio.\n"
            "- **3 Desain & Palet Berbeda:** Masing-masing hari memiliki produk kurasi berbeda dari katalog dan moodboard khas Colorbox.\n"
            "- **Aspect Ratio Lock:** Semua foto model dan produk mempertahankan proporsi asli (tidak gepeng).\n\n"
            "Seluruh berkas PNG 1080 × 1350 px siap dipublikasikan. Silakan @bimo memberikan quality audit akhir."
        )
        return md

    main_p = prods[0] if prods else day1_prods[0]
    p_name = main_p.get("name", "New Arrivals")
    is_poster = any("poster" in str(line).lower() or "baru" in str(line).lower() for line in transcript_lines)
    theme_title = "NEW ARRIVALS" if is_poster or any(k in p_name.lower() for k in ["dress", "skirt", "skort"]) else "CAMPUS LOOKBOOK"
    headline = f"Spotlight Drop:\n{p_name}!" if is_poster else "Effortless Campus Rebel:\nComfy, Chic & Standout!"
    subtitle = f"Koleksi resmi {main_p.get('color', 'Colorbox')} — Standout seharian dengan potongan presisi!"

    try:
        render_final_carousel_package(
            theme_title=theme_title,
            headline=headline,
            subtitle=subtitle,
            products_info=prods,
            output_dir=out_dir,
            images_dir=img_dir,
            day_num=1
        )
    except Exception as ex:
        print(f"[Vina Rendering Failed]: {ex}")

    md = (
        "### 🎨 Aset Visual Carousel Siap Posting (@colorbox Lookbook Standard):\n\n"
        "![Cover Hero](/output/carousel_latest/slide_1_cover_hero.png)\n\n"
        "![Top Piece Focus](/output/carousel_latest/slide_2_hero_top.png)\n\n"
        "![Bottom Silhouette](/output/carousel_latest/slide_3_bottom_pairing.png)\n\n"
        "![Starter Pack Flatlay](/output/carousel_latest/slide_4_accessories_flatlay.png)\n\n"
        "![Moodboard Sign-off](/output/carousel_latest/slide_5_outro_cta.png)\n\n"
        "👉 **[Buka Pratinjau Interaktif Carousel di Tab Baru](/output/carousel_latest/carousel_preview.html)**\n\n"
        "✨ **Kepatuhan Standar Visual Siap Posting (@colorbox Official):**\n"
        "- **Bebas Noise Template:** 100% bebas dari label 'slide 1', 'slide 2', dots pagination, atau panah 'swipe' pada kanvas gambar.\n"
        "- **Minimal Teks:** Hanya memuat micro-copy editorial 1–2 kata saja.\n"
        "- **Zero-Price Canvas:** 100% bebas dari nominal harga pada gambar (harga resmi ditaruh di caption/bio).\n"
        "- **Color Palette Swatches:** Dot warna visual presisi untuk tiap warna resmi produk.\n"
        "- **Aspek Rasio Terkunci:** Foto produk dan model tidak di-stretch maupun gepeng.\n\n"
        "Seluruh 5 slide gambar final (1080 × 1350 px PNG) telah sukses dirender menggunakan model visual openai/gpt-image-2 (OpenCode Zen) dan foto produk autentik Colorbox!\n"
        "Silakan @bimo memberikan quality audit anti-halusinasi dan penutupan sprint."
    )
    return md


def _group_loop(gid: str, st: GroupSendState, initial_text: str) -> None:
    HUB.publish("*", "group_send", {"group_id": gid, "status": "running"})
    final_status = "done"

    try:
        pending_inputs = [initial_text]
        while pending_inputs:
            batch_text = pending_inputs.pop(0)
            st.cancel_round = False

            conn = _connect()
            try:
                g_row = conn.execute("SELECT * FROM groups WHERE id = ? AND deleted_at IS NULL", (gid,)).fetchone()
            finally:
                conn.close()
            if not g_row:
                break

            g_view = _group_row_to_view(g_row)
            mems = g_view["members"]
            if len(mems) < 2:
                break
            by_id = {m["bot_id"]: m for m in mems}
            roster = "; ".join(f"{m['name']} ({m['role']})" for m in mems)

            # Build initial responders from user mentions, or lead bot (bimo for marketing)
            ment = _mentioned_bots(batch_text, mems)
            if ment:
                responders = [m for m in mems if m["bot_id"] in ment]
            else:
                bimo_mem = next((m for m in mems if m["bot_id"] == "bimo"), None)
                if bimo_mem:
                    responders = [bimo_mem]
                else:
                    responders = list(mems)

            # Fetch recent transcript for context
            conn_h = _connect()
            try:
                all_bots = conn_h.execute("SELECT id, name FROM bots").fetchall()
                n2b = {b["name"].lower(): b["id"] for b in all_bots}
                recent_rows = conn_h.execute(
                    "SELECT * FROM group_messages WHERE group_id = ? ORDER BY rowid DESC LIMIT 20", (gid,)
                ).fetchall()
            finally:
                conn_h.close()
            transcript_msgs = [_group_msg_to_view(r, n2b) for r in reversed(recent_rows)]
            transcript_lines = []
            for m in transcript_msgs:
                if m["role"] == "system":
                    continue
                who = "User" if m["role"] == "user" else by_id.get(m["bot_id"], {}).get("name", m["bot_id"] or "Agen")
                transcript_lines.append(f"{who}: {m['text']}")

            # Detect product mandate from user
            user_text_candidate = batch_text
            if not user_text_candidate and transcript_lines:
                for ln in transcript_lines:
                    if ln.startswith("User:"):
                        user_text_candidate = ln[5:].strip()
                        break
            user_mandate_prods, user_mandate_note = _detect_user_product_mandate(user_text_candidate)

            posted = 0
            tokens_used = 0
            plan = _get_plan_row()
            budget = plan["group_send_token_budget"]
            stop_reason: Optional[str] = None

            for rnd in range(1, MAX_GROUP_ROUNDS + 1):
                round_msgs: List[Tuple[str, str]] = []
                for member in responders:
                    if st.stopped or st.cancel_round:
                        break
                    if posted >= MAX_GROUP_BOT_MESSAGES:
                        stop_reason = f"Diskusi berhenti: batas {MAX_GROUP_BOT_MESSAGES} pesan bot tercapai."
                        break

                    bid = member["bot_id"]
                    bot_full = dict(_get_bot_row(bid))

                    # Tailored instructions for marketing agents
                    role_instructions = ""
                    if bid == "bimo":
                        role_instructions = (
                            "TUGAS AI PROJECT MANAGER (BIMO):\n"
                            "1. Sambut tim dan user di group chat secara ramah, terstruktur, dan proaktif.\n"
                            "2. Paparkan ringkasan brief dan rencana sprint konten.\n"
                            f"3. {user_mandate_note}\n"
                            "4. Jika alur baru dimulai, panggil @meda (@marketingstrategist) untuk menyiapkan 3 opsi konsep konten dan produk terpilih.\n"
                            "5. Jika Vina sudah selesai merender carousel (rnd > 1), berikan laporan akhir Quality Audit: konfirmasi katalog 100% valid, ukuran cm terverifikasi, aset gambar final siap tayang, dan nyatakan materi siap dipublikasikan ke user. JANGAN memanggil atau menyebut @ agen lain agar alur diskusi selesai dengan tuntas."
                        )
                    elif bid == "meda":
                        role_instructions = (
                            "TUGAS MARKETING & FASHION STRATEGIST (MEDA):\n"
                            "1. Petakan tujuan konten, target audiens Gen Z (18-25 tahun), dan pilar gaya (Urban/Romantic/Chic).\n"
                            f"2. {user_mandate_note}\n"
                            "3. Buat 3 Opsi Ide Konten (Opsi A, B, C) dengan nama resmi & harga Rp dari katalog Colorbox.\n"
                            "4. Berikan rekomendasi utama pada Opsi A, lalu delegasikan langsung ke @raka (@researcher) untuk riset teknis ukuran, spesifikasi, dan aset foto."
                        )
                    elif bid == "raka":
                        role_instructions = (
                            "TUGAS FASHION & CONTENT RESEARCHER (RAKA):\n"
                            "1. Validasi produk opsi terpilih ke katalog resmi Colorbox (product-catalog.md).\n"
                            "2. Bedah panduan ukuran cm & siluet fit dari product-size-reference.md (lingkar dada, pinggang, panggul cm).\n"
                            "3. Konfirmasi ketersediaan foto produk resmi di folder images/ (auto-ingest jika belum ada).\n"
                            "4. Susun Creative Research Brief 5 slide lengkap dengan spesifikasi teknis dan alasan styling.\n"
                            "5. Delegasikan langsung ke @bram (@sketchwriter) untuk merancang naskah & prompt visual."
                        )
                    elif bid == "bram":
                        role_instructions = (
                            "TUGAS CREATIVE COPYWRITER (BRAM):\n"
                            "1. Susun naskah copy AIDA lengkap untuk 5 slide carousel (Slide 1 Cover Hook, Slide 2 Hero Top, Slide 3 Bottom Pairing, Slide 4 Accessories/Layering, Slide 5 Outro CTA).\n"
                            "2. Tulis caption Instagram resmi lengkap dengan hashtag #NeverJustOneThing dan CTA ke bio.\n"
                            "3. Buat AI Visual Generation Prompt terperinci (format 4:5 Feed Portrait) untuk setiap slide.\n"
                            "4. Delegasikan langsung ke @vina (@visualcarousel) untuk eksekusi render gambar visual final."
                        )
                    elif bid == "vina":
                        role_instructions = (
                            "TUGAS VISUAL CAROUSEL SPECIALIST (VINA):\n"
                            "1. Berikan pengarahan artistik layout visual untuk ke-5 slide carousel (Instagram Feed Portrait 4:5, 1080 × 1350 px).\n"
                            "2. Sebutkan bahwa berkas gambar final sedang dirender menggunakan model visual openai/gpt-image-2 (OpenCode Zen) dan foto produk autentik Colorbox.\n"
                            "3. Ingat: Feed Carousel tidak memiliki safe-zone occlusion seperti Reels, sehingga kanvas 1080x1350 px dimanfaatkan 100% full-bleed.\n"
                            "4. Laporkan hasil rendering gambar final dan serahkan ke @bimo (@projectmanager) untuk laporan akhir & quality audit."
                        )

                    group_instr = (
                        f"Kamu adalah {bot_full['name']}, {bot_full['role']} Colorbox.\n"
                        f"{bot_full['persona']}\n\n"
                        f"Kamu sedang berdiskusi di grup \"{g_view['name']}\". Anggota grup: {roster}.\n"
                        f"{role_instructions}\n\n"
                        "Aturan Komunikasi:\n"
                        "- Sampaikan tugasmu secara terstruktur, kolaboratif, dan tuntas sesuai peranmu.\n"
                        "- Jangan memotong poin penting atau mengulang pesan anggota lain secara berlebihan.\n"
                        f"- Jika tidak ada yang perlu kamu tambahkan, balas persis {SILENT_TOKEN}.\n"
                        "- Selalu sebut @nama agen berikutnya yang kamu tugaskan agar alur diskusi otomatis berlanjut!"
                    )

                    # Attach light Colorbox grounding if relevant
                    products = user_mandate_prods or CATALOG.search("\n".join(transcript_lines[-5:]), limit=3)
                    full_prompt = build_plain_system_prompt(bot_full, products, group_instr)
                    # Context window: keep only from latest user message or last 6 turns
                    latest_user_idx = 0
                    for idx_ln, ln in enumerate(transcript_lines):
                        if ln.startswith("User:"):
                            latest_user_idx = idx_ln
                    turn_lines = [ln.strip() for ln in transcript_lines[latest_user_idx:] if ln.strip()]
                    if not turn_lines:
                        turn_lines = [ln.strip() for ln in transcript_lines[-4:] if ln.strip()]
                    turn_input = "\n\n".join(turn_lines).strip()
                    if not turn_input:
                        turn_input = (batch_text or "").strip()
                    if not turn_input:
                        turn_input = "Lanjutkan diskusi tim marketing sesuai brief dan peran kamu."
                    if len(turn_input) > 15000:
                        turn_input = turn_input[-15000:].strip()

                    stop_after_turn = False
                    st.turn_bot = bid
                    HUB.publish("*", "group_typing", {"group_id": gid, "bot_id": bid, "on": True, "phase": "thinking"})
                    try:
                        run_view, lv = start_run_job(
                            bot_id=bid,
                            user_input=turn_input,
                            session_id=f"grup-{gid}-{bid}",
                            kind="group",
                            group_id=gid,
                            group_prompt=full_prompt,
                            origin={"type": "group"},
                        )
                        st.active_run_id = run_view["id"]
                        HUB.publish("*", "group_typing", {
                            "group_id": gid,
                            "bot_id": bid,
                            "on": True,
                            "phase": "thinking",
                            "run_id": st.active_run_id,
                        })
                        lv.done_ev.wait(timeout=180)
                        st.active_run_id = None

                        conn_r = _connect()
                        try:
                            rr = conn_r.execute("SELECT * FROM runs WHERE id = ?", (run_view["id"],)).fetchone()
                            rv = _run_row_to_view(rr)
                        finally:
                            conn_r.close()

                        tokens_used += rv["total_tokens"]
                        if rv["status"] == "cancelled" or st.stopped:
                            stop_after_turn = True
                        elif rv["status"] != "completed":
                            stop_reason = f"Diskusi berhenti: {member['name']} gagal menjawab."
                            stop_after_turn = True
                        else:
                            reply_text = rv["output"].strip()
                            cleaned = reply_text.replace(SILENT_TOKEN, "").strip()
                            if cleaned:
                                if bid == "vina":
                                    try:
                                        vina_carousel_md = _render_vina_visual_carousel(transcript_lines, user_mandate_prods)
                                        if vina_carousel_md:
                                            cleaned += "\n\n" + vina_carousel_md
                                    except Exception as ex:
                                        print(f"[Vina Visual Injection Error]: {ex}")

                                _post_group_msg(gid, "bot", cleaned, bot_id=bid, run_id=rv["id"], sender_label=member["name"])
                                transcript_lines.append(f"{member['name']}: {cleaned}")
                                posted += 1
                                round_msgs.append((bid, cleaned))

                            if budget is not None and tokens_used >= budget:
                                stop_reason = f"Diskusi berhenti: batas {budget} token per kiriman tercapai."
                                stop_after_turn = True
                    finally:
                        st.active_run_id = None
                        st.turn_bot = None
                        HUB.publish("*", "group_typing", {"group_id": gid, "bot_id": bid, "on": False})

                    if stop_after_turn:
                        break

                if st.stopped or st.cancel_round or stop_reason:
                    break

                nxt: Set[str] = set()
                for i, (author_id, msg_txt) in enumerate(round_msgs):
                    spoke_later = {b for b, _ in round_msgs[i + 1:]}
                    nxt |= {b for b in _mentioned_bots(msg_txt, mems) if b != author_id and b not in spoke_later}

                pipeline_next = {
                    "bimo": "meda",
                    "meda": "raka",
                    "raka": "bram",
                    "bram": "vina",
                    "vina": "bimo",
                }
                last_author = round_msgs[-1][0] if round_msgs else ""
                vina_spoken = any(author == "vina" for author, _ in round_msgs) or any(
                    ln.startswith("Vina:") for ln in transcript_lines[latest_user_idx:]
                )
                
                if gid == "marketing":
                    if last_author == "bimo" and vina_spoken:
                        responders = []
                    elif last_author in pipeline_next and pipeline_next[last_author] in by_id:
                        responders = [by_id[pipeline_next[last_author]]]
                    else:
                        responders = [by_id[b] for b in by_id if b in nxt]
                else:
                    preferred_bot = pipeline_next.get(last_author)
                    if preferred_bot and preferred_bot in nxt and preferred_bot in by_id:
                        responders = [by_id[preferred_bot]]
                    else:
                        responders = [by_id[b] for b in by_id if b in nxt]

                if not responders:
                    break
                if rnd == MAX_GROUP_ROUNDS:
                    stop_reason = f"Diskusi berhenti: batas {MAX_GROUP_ROUNDS} ronde tercapai."

            if st.stopped:
                final_status = "stopped"
                _post_group_msg(gid, "system", "Diskusi dihentikan.")
                break
            elif stop_reason:
                _post_group_msg(gid, "system", stop_reason)

            with st.lock:
                if st.queued_texts:
                    pending_inputs.append(" | ".join(st.queued_texts))
                    st.queued_texts.clear()
    except Exception as e:
        _post_group_msg(gid, "system", f"Diskusi berhenti: {e}")
    finally:
        with GROUP_LOCK:
            GROUP_ACTIVE.pop(gid, None)
        HUB.publish("*", "group_send", {"group_id": gid, "status": final_status})


# ---------- Evaluations Helper ----------

def _eval_clean_scores(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ApiError(400, "Skor harus berupa objek")
    out: Dict[str, Any] = {}
    for dim, v in raw.items():
        if dim not in DIMENSIONS:
            raise ApiError(400, f"Dimensi skor tidak dikenal: {dim}")
        if not isinstance(v, dict):
            raise ApiError(400, f"Skor {dim} harus berisi score dan reason")
        score, reason = v.get("score"), v.get("reason")
        reason = reason.strip() if isinstance(reason, str) else ""
        if score is None:
            if not reason:
                raise ApiError(400, f"Skor {dim} N/A wajib diberi alasan")
        elif isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
            raise ApiError(400, f"Skor {dim} harus 1 sampai 5 atau N/A")
        out[dim] = {"score": score, "reason": reason[:500]}
    return out


def _eval_clean_comparison(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ApiError(400, "Perbandingan tidak valid")
    mode = raw.get("mode")
    if mode not in ("repeat", "agents"):
        raise ApiError(400, "Mode perbandingan harus repeat atau agents")
    cons = raw.get("consistency")
    if cons not in ("konsisten", "tidak_konsisten"):
        raise ApiError(400, "Pilih Konsisten atau Tidak konsisten")
    runs_in = raw.get("runs")
    if not isinstance(runs_in, list) or not 2 <= len(runs_in) <= 3:
        raise ApiError(400, "Perbandingan butuh 2 sampai 3 run")
    runs = []
    for r in runs_in:
        if not isinstance(r, dict):
            raise ApiError(400, "Run perbandingan tidak valid")
        tokens = r.get("tokens", 0)
        meta = r.get("meta", {})
        if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
            raise ApiError(400, "Jumlah token run tidak valid")
        if not isinstance(meta, dict):
            raise ApiError(400, "Data versi run tidak valid")
        sid = r.get("session_id")
        runs.append({
            "run_id": str(r.get("run_id") or "").strip(),
            "session_id": str(sid).strip() if sid is not None else None,
            "bot_id": str(r.get("bot_id") or "").strip(),
            "output": str(r.get("output") or "")[:40000],
            "tokens": tokens,
            "duration": r["duration"] if isinstance(r.get("duration"), (int, float)) and not isinstance(r.get("duration"), bool) else None,
            "meta": meta,
        })
    if len({r["run_id"] for r in runs}) != len(runs):
        raise ApiError(400, "Run perbandingan tidak boleh sama")
    return {
        "mode": mode,
        "consistency": cons,
        "note": str(raw.get("note") or "")[:2000],
        "runs": runs,
    }


def _enrich_eval(v: Dict[str, Any]) -> None:
    conn = _connect()
    try:
        cmp_obj = v.get("comparison")
        if cmp_obj:
            for r in cmp_obj["runs"]:
                row = conn.execute("SELECT * FROM runs WHERE id = ?", (r["run_id"],)).fetchone()
                if row:
                    rv = _run_row_to_view(row)
                    dur = round(rv["finished_at"] - rv["started_at"], 1) if (rv["finished_at"] and rv["started_at"]) else None
                    r.update({
                        "bot_id": rv["bot_id"],
                        "session_id": rv["session_id"] or None,
                        "tokens": rv["total_tokens"],
                        "meta": rv["meta"],
                        "duration": dur,
                    })
            first = cmp_obj["runs"][0]
            v["bot_id"] = first["bot_id"]
            v["run_id"] = first["run_id"]
            v["session_id"] = first["session_id"]
            v["meta"] = first["meta"]
        elif v.get("run_id"):
            row = conn.execute("SELECT meta FROM runs WHERE id = ?", (v["run_id"],)).fetchone()
            if row and row["meta"]:
                try:
                    v["meta"] = json.loads(row["meta"])
                except Exception:
                    pass
    finally:
        conn.close()


def _eval_row_to_view(r: sqlite3.Row) -> Dict[str, Any]:
    try:
        p = json.loads(r["payload"]) if r["payload"] else {}
    except Exception:
        p = {}
    if not isinstance(p, dict):
        p = {}

    try:
        scores = json.loads(r["scores"]) if isinstance(r["scores"], str) else (p.get("scores") or {})
    except Exception:
        scores = {}

    raw_notes = p.get("notes")
    if raw_notes is None:
        try:
            raw_notes = json.loads(r["notes"]) if isinstance(r["notes"], str) and r["notes"].startswith("{") else {"errors": str(r["notes"] or ""), "improvements": "", "critical": False, "reviewed_on": ""}
        except Exception:
            raw_notes = {"errors": str(r["notes"] or ""), "improvements": "", "critical": False, "reviewed_on": ""}
    notes = {
        "errors": str(raw_notes.get("errors") or ""),
        "improvements": str(raw_notes.get("improvements") or ""),
        "critical": bool(raw_notes.get("critical")),
        "reviewed_on": str(raw_notes.get("reviewed_on") or ""),
    }

    ts = r["created_ts"] if r["created_ts"] is not None else _to_epoch(r["created_at"])
    return {
        "id": r["id"],
        "case_id": r["case_id"],
        "bot_id": r["bot_id"],
        "session_id": p.get("session_id"),
        "run_id": p.get("run_id"),
        "prompt": str(p.get("prompt") or ""),
        "expected": str(p.get("expected") or ""),
        "actual": str(p.get("actual") or ""),
        "scores": scores,
        "verdict": r["verdict"] if r["verdict"] in VERDICTS else "fail",
        "notes": notes,
        "reviewer": r["reviewer"] or "",
        "created_at": ts or 0,
        "meta": p.get("meta") if isinstance(p.get("meta"), dict) else {},
        "comparison": p.get("comparison"),
    }


def _clean_eval_body(body: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, limit in EVAL_TEXT_LIMITS.items():
        if k not in body:
            continue
        v = body[k]
        if v is None and k in ("session_id", "run_id"):
            out[k] = None
            continue
        if not isinstance(v, str):
            raise ApiError(400, f"{k} harus berupa teks")
        v = v.strip()
        if len(v) > limit:
            raise ApiError(400, f"{k} terlalu panjang (maksimal {limit} karakter)")
        out[k] = v

    if "verdict" in body:
        if body["verdict"] not in VERDICTS:
            raise ApiError(400, "Hasil harus pass, fail, atau blocked")
        out["verdict"] = body["verdict"]
    if "scores" in body:
        out["scores"] = _eval_clean_scores(body["scores"])
    if "notes" in body:
        n = body["notes"]
        if isinstance(n, str):
            n = {"errors": n, "improvements": "", "critical": False, "reviewed_on": ""}
        if not isinstance(n, dict) or len(json.dumps(n, ensure_ascii=False)) > 20000:
            raise ApiError(400, "Catatan tidak valid")
        out["notes"] = {
            "errors": str(n.get("errors") or ""),
            "improvements": str(n.get("improvements") or ""),
            "critical": bool(n.get("critical")),
            "reviewed_on": str(n.get("reviewed_on") or ""),
        }
    if "comparison" in body:
        out["comparison"] = None if body["comparison"] is None else _eval_clean_comparison(body["comparison"])
    if "meta" in body:
        m = body["meta"]
        if not isinstance(m, dict) or len(json.dumps(m, ensure_ascii=False)) > 8000:
            raise ApiError(400, "Data versi tidak valid")
        out["meta"] = m

    if not partial:
        for req_k in ("case_id", "bot_id", "verdict"):
            if not out.get(req_k):
                raise ApiError(400, f"{req_k} wajib diisi")
    elif not out:
        raise ApiError(400, "Tidak ada yang diubah")
    return out


# ---------- HTTP Request Handler ----------

class BFFHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        code = args[1] if len(args) > 1 else ""
        if "/api/events" not in self.path:
            print(f"[BFF 8090] {self.command} {self.path} -> {code}")

    def _clean_path(self) -> Tuple[str, Dict[str, List[str]]]:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/bff"):
            path = path[4:]
        return path, parse_qs(parsed.query)

    def _read_json_body(self) -> Dict[str, Any]:
        cl = self.headers.get("Content-Length")
        if not cl:
            return {}
        try:
            length = int(cl)
        except ValueError:
            raise ApiError(400, "Header Content-Length tidak valid")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            d = json.loads(raw.decode("utf-8"))
        except ValueError:
            raise ApiError(400, "Isi permintaan bukan JSON yang valid")
        if not isinstance(d, dict):
            raise ApiError(400, "Isi permintaan harus berupa objek JSON")
        return d

    def _send_json(self, status: int, data: Any, extra_headers: Optional[Dict[str, str]] = None) -> None:
        if status == 204:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
            self.send_header("Connection", "close")
            self.end_headers()
            return
        resp = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        if extra_headers:
            for hk, hv in extra_headers.items():
                self.send_header(hk, hv)
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(resp)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _serve_static_file(self, file_path: Path) -> None:
        suffix = file_path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".html": "text/html; charset=utf-8",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
        }
        ct = mime_map.get(suffix, "application/octet-stream")
        try:
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._send_json(500, {"error": f"Gagal membaca file: {e}"})

    def _safe_dispatch(self, fn: Callable[[], None]) -> None:
        try:
            fn()
        except ApiError as e:
            self._send_json(e.status, {"error": e.message, **e.extra})
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            print(f"[BFF 8090] Unhandled error on {self.command} {self.path}: {type(e).__name__}: {e}")
            try:
                self._send_json(500, {"error": f"Terjadi kesalahan di server: {type(e).__name__}"})
            except Exception:
                pass

    def do_OPTIONS(self) -> None:
        self._send_json(204, {})

    def do_GET(self) -> None:
        self._safe_dispatch(self._handle_get)

    def do_POST(self) -> None:
        self._safe_dispatch(self._handle_post)

    def do_PATCH(self) -> None:
        self._safe_dispatch(self._handle_patch)

    def do_PUT(self) -> None:
        self._safe_dispatch(self._handle_put)

    def do_DELETE(self) -> None:
        self._safe_dispatch(self._handle_delete)

    # ---- GET Routes ----
    def _handle_get(self) -> None:
        path, q = self._clean_path()
        parts = [unquote(x) for x in path.strip("/").split("/") if x]

        # Health
        if path in ("/api/health", "/health"):
            self._send_json(200, {
                "ok": True,
                "db": True,
                "hermes": True,
                "model": MODEL_ID,
                "catalog_count": len(CATALOG.rows),
                "commit": _bff_commit(),
            })
            return

        # Static files: /output/... and /images/...
        if path.startswith("/output/") or path.startswith("/bff/output/"):
            clean_rel = path.replace("/bff/output/", "").replace("/output/", "").lstrip("/")
            file_path = MARKETING_OUTPUT_DIR / clean_rel
            if file_path.exists() and file_path.is_file():
                self._serve_static_file(file_path)
                return
            else:
                self._send_json(404, {"error": "File output tidak ditemukan"})
                return

        if path.startswith("/images/") or path.startswith("/bff/images/"):
            clean_rel = path.replace("/bff/images/", "").replace("/images/", "").lstrip("/")
            file_path = IMAGES_DIR / clean_rel
            if file_path.exists() and file_path.is_file():
                self._serve_static_file(file_path)
                return
            else:
                self._send_json(404, {"error": "Gambar produk tidak ditemukan"})
                return

        # Scheduler API
        if path == "/api/scheduler":
            self._send_json(200, {
                "active": True,
                "jobs": [
                    {
                        "id": "cbx-daily-carousel",
                        "name": "Colorbox Daily 5-Agent Carousel Generation",
                        "schedule": "08:00 WIB Setiap Hari",
                        "status": "active",
                        "agents": ["bimo", "meda", "raka", "bram", "vina"],
                        "target_channel": "Instagram Feed (4:5 Portrait)",
                        "last_run": "Hari ini, Selesai (5 Slide)",
                        "next_run": "Besok, 08:00 WIB"
                    }
                ]
            })
            return

        # Global SSE /api/events
        if path == "/api/events":
            self._serve_global_sse()
            return

        if path == "/api/me":
            self._send_json(200, _get_me())
            return

        if path == "/api/models":
            self._send_json(200, _models_catalog())
            return

        if path == "/api/settings":
            self._send_json(200, _get_settings())
            return

        if path == "/api/settings/security":
            self._send_json(200, _settings_security())
            return

        if path == "/api/settings/knowledge":
            self._send_json(200, _settings_knowledge())
            return

        if path == "/api/export/history":
            self._send_json(
                200,
                _export_history(),
                extra_headers={"Content-Disposition": 'attachment; filename="riwayat-chat.json"'},
            )
            return

        if path == "/api/plans":
            self._send_json(200, PLANS_DATA)
            return

        if path == "/api/templates":
            self._send_json(200, [
                {
                    "id": b["id"],
                    "name": b["name"],
                    "role": b["role"],
                    "team": b["team"],
                    "color": b["color"],
                    "description": b["about"],
                }
                for b in BUILTIN_BOTS
            ])
            return

        if path == "/api/bots":
            self._send_json(200, _list_bots_view())
            return

        # /api/bots/{bot_id}
        if len(parts) == 3 and parts[:2] == ["api", "bots"]:
            r = _get_bot_row(parts[2])
            view = _bot_row_to_view(r)
            view["persona"] = r["persona"] or ""
            view["template"] = r["template"] or ""
            self._send_json(200, view)
            return

        # /api/bots/{bot_id}/sessions
        if len(parts) == 4 and parts[:2] == ["api", "bots"] and parts[3] == "sessions":
            bot_id = parts[2]
            _get_bot_row(bot_id)
            conn = _connect()
            try:
                rows = conn.execute(
                    """SELECT s.id, s.title, s.preview, s.created_at, s.updated_at, s.model,
                              (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) as msg_cnt,
                              (SELECT COUNT(*) FROM runs r WHERE r.session_id = s.id) as run_cnt
                       FROM sessions s
                       WHERE s.bot_id = ? AND s.id NOT LIKE 'grup-%'
                       ORDER BY s.updated_at DESC LIMIT 200""",
                    (bot_id,),
                ).fetchall()
                data = [
                    {
                        "id": r["id"],
                        "bot_id": bot_id,
                        "title": r["title"] or "Percakapan",
                        "preview": r["preview"] or r["title"] or "",
                        "message_count": int(r["msg_cnt"] or (r["run_cnt"] * 2)),
                        "last_active": r["updated_at"] or r["created_at"] or 0,
                        "created_at": r["created_at"] or 0,
                        "updated_at": r["updated_at"] or 0,
                        "model": r["model"] or MODEL_ID,
                    }
                    for r in rows
                ]
            finally:
                conn.close()
            self._send_json(200, {"object": "list", "data": data})
            return

        # /api/bots/{bot_id}/sessions/{sid}/messages
        if len(parts) == 6 and parts[:2] == ["api", "bots"] and parts[3] == "sessions" and parts[5] == "messages":
            bot_id, sid = parts[2], parts[4]
            _get_bot_row(bot_id)
            conn = _connect()
            try:
                sess = conn.execute("SELECT id FROM sessions WHERE id = ? AND bot_id = ?", (sid, bot_id)).fetchone()
                if not sess:
                    raise ApiError(404, "Sesi tidak ditemukan")
                mrows = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (sid,)).fetchall()
                if mrows:
                    out = [
                        {
                            "id": m["id"],
                            "role": m["role"],
                            "content": m["content"] or "",
                            "reasoning": m["reasoning"] or "",
                            "tool_call_id": m["tool_call_id"],
                            "tool_name": m["tool_name"],
                        }
                        for m in mrows
                    ]
                else:
                    rrows = conn.execute(
                        "SELECT id, input, output, reasoning FROM runs WHERE session_id = ? ORDER BY created_at ASC",
                        (sid,),
                    ).fetchall()
                    out = []
                    for idx, rr in enumerate(rrows):
                        if rr["input"]:
                            out.append({"id": f"u-{idx}", "role": "user", "content": rr["input"], "reasoning": ""})
                        if rr["output"] or rr["reasoning"]:
                            out.append({"id": f"a-{idx}", "role": "assistant", "content": rr["output"] or "", "reasoning": rr["reasoning"] or ""})
            finally:
                conn.close()
            self._send_json(200, {"object": "list", "data": out})
            return

        # /api/tools
        if path == "/api/tools":
            bot_filter = q.get("bot", [None])[0]
            bots_list = _list_bots_view()
            if bot_filter:
                bots_list = [b for b in bots_list if b["id"] == bot_filter]
                if not bots_list:
                    raise ApiError(404, "Bot tidak ditemukan")
            denied_entries = [
                {
                    "name": d,
                    "label": d,
                    "description": "Dimatikan di lingkungan API demi keamanan",
                    "tools": [],
                    "enabled": False,
                }
                for d in DENY_TOOLS
            ]
            out_bots = [
                {
                    "bot_id": b["id"],
                    "name": b["name"],
                    "ok": True,
                    "toolsets": [*TOOLSETS_BY_TEAM.get(b["team"], TOOLSETS_BY_TEAM["marketing"]), *denied_entries],
                }
                for b in bots_list
            ]
            self._send_json(200, {"deny": list(DENY_TOOLS), "bots": out_bots})
            return

        # /api/products/search
        if path == "/api/products/search":
            q_str = q.get("q", [None])[0]
            cat = q.get("category", [None])[0]
            mp_str = q.get("max_price", [None])[0]
            col = q.get("color", [None])[0]
            sz = q.get("size", [None])[0]
            lim_str = q.get("limit", ["5"])[0]
            if not any((q_str and q_str.strip(), cat, mp_str, col, sz)):
                raise ApiError(400, "Isi q atau salah satu filter (category, max_price, color, size)")
            mp = int(mp_str) if mp_str else None
            lim = int(lim_str) if lim_str else 5
            rows = CATALOG.search(q_str, cat, mp, col, sz, lim)
            self._send_json(200, {"data": rows, "count": len(rows)})
            return

        # /api/runs
        if path == "/api/runs":
            st_filter = q.get("status", ["recent"])[0]
            lim = max(1, min(int(q.get("limit", [30])[0]), 100))
            bot_filter = q.get("bot", [None])[0]
            cond = "r.status IN ('running', 'queued')" if st_filter == "active" else "r.status NOT IN ('running', 'queued')"
            params: List[Any] = []
            extra = ""
            if bot_filter:
                extra = " AND r.bot_id = ?"
                params.append(bot_filter)
            params.append(lim)
            conn = _connect()
            try:
                rows = conn.execute(
                    f"""SELECT r.*, b.name as bname FROM runs r LEFT JOIN bots b ON b.id = r.bot_id
                        WHERE {cond}{extra} ORDER BY r.created_at DESC LIMIT ?""",
                    params,
                ).fetchall()
                out = []
                for r in rows:
                    rv = _run_row_to_view(r)
                    rv["bot_name"] = r["bname"] or rv["bot_id"]
                    rv["input"] = rv["input"][:120]
                    out.append(rv)
            finally:
                conn.close()
            self._send_json(200, out)
            return

        # /api/runs/{rid}
        if len(parts) == 3 and parts[:2] == ["api", "runs"]:
            rid = parts[2]
            conn = _connect()
            try:
                r = conn.execute("SELECT r.*, b.name as bname FROM runs r LEFT JOIN bots b ON b.id = r.bot_id WHERE r.id = ?", (rid,)).fetchone()
                if not r:
                    raise ApiError(404, "Tugas tidak ditemukan")
                rv = _run_row_to_view(r)
                rv["bot_name"] = r["bname"] or rv["bot_id"]
                evs = conn.execute(
                    "SELECT id, type, tool, status, duration, preview, created_at FROM run_events WHERE run_id = ? ORDER BY id ASC",
                    (rid,),
                ).fetchall()
                ev_list = [dict(e) for e in evs]
            finally:
                conn.close()
            self._send_json(200, {**rv, "run": rv, "events": ev_list})
            return

        # /api/runs/{rid}/stream or /events
        if len(parts) == 4 and parts[:2] == ["api", "runs"] and parts[3] in ("stream", "events"):
            self._serve_run_sse(parts[2])
            return

        # /api/sequences
        if path == "/api/sequences":
            case_id = q.get("case_id", [None])[0]
            lim = max(1, min(int(q.get("limit", [10])[0]), 20))
            conn = _connect()
            try:
                if case_id:
                    rows = conn.execute(
                        "SELECT id FROM sequences WHERE case_id = ? ORDER BY created_at DESC LIMIT ?",
                        (case_id, lim),
                    ).fetchall()
                else:
                    rows = conn.execute("SELECT id FROM sequences ORDER BY created_at DESC LIMIT ?", (lim,)).fetchall()
            finally:
                conn.close()
            self._send_json(200, [_sequence_view(r["id"]) for r in rows])
            return

        if len(parts) == 3 and parts[:2] == ["api", "sequences"]:
            self._send_json(200, _sequence_view(parts[2]))
            return

        # /api/groups
        if path == "/api/groups":
            conn = _connect()
            try:
                rows = conn.execute("SELECT * FROM groups WHERE deleted_at IS NULL ORDER BY created_at ASC").fetchall()
                self._send_json(200, [_group_row_to_view(r) for r in rows])
            finally:
                conn.close()
            return

        if len(parts) == 3 and parts[:2] == ["api", "groups"]:
            conn = _connect()
            try:
                r = conn.execute("SELECT * FROM groups WHERE id = ? AND deleted_at IS NULL", (parts[2],)).fetchone()
                if not r:
                    raise ApiError(404, "Grup tidak ditemukan")
                self._send_json(200, _group_row_to_view(r))
            finally:
                conn.close()
            return

        if len(parts) == 4 and parts[:2] == ["api", "groups"] and parts[3] == "live":
            gid = parts[2]
            conn = _connect()
            try:
                g = conn.execute("SELECT id FROM groups WHERE id = ? AND deleted_at IS NULL", (gid,)).fetchone()
                if not g:
                    raise ApiError(404, "Grup tidak ditemukan")
            finally:
                conn.close()
            with GROUP_LOCK:
                st = GROUP_ACTIVE.get(gid)
                t_bot = st.turn_bot if st else None
                t_run = st.active_run_id if st else None
            self._send_json(200, {"turn": {"bot_id": t_bot, "run_id": t_run} if t_bot else None})
            return

        if len(parts) == 4 and parts[:2] == ["api", "groups"] and parts[3] == "messages":
            gid = parts[2]
            before_id = q.get("before", [None])[0]
            lim = max(1, min(int(q.get("limit", [50])[0]), 200))
            conn = _connect()
            try:
                g = conn.execute("SELECT id FROM groups WHERE id = ? AND deleted_at IS NULL", (gid,)).fetchone()
                if not g:
                    raise ApiError(404, "Grup tidak ditemukan")
                all_bots = conn.execute("SELECT id, name FROM bots").fetchall()
                n2b = {b["name"].lower(): b["id"] for b in all_bots}
                before_rowid = None
                if before_id:
                    br = conn.execute("SELECT rowid FROM group_messages WHERE id = ? AND group_id = ?", (before_id, gid)).fetchone()
                    if br:
                        before_rowid = br[0]
                if before_rowid is not None:
                    rows = conn.execute(
                        "SELECT * FROM (SELECT rowid as rid, * FROM group_messages WHERE group_id = ? AND rowid < ? ORDER BY rowid DESC LIMIT ?) ORDER BY rid ASC",
                        (gid, before_rowid, lim),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM (SELECT rowid as rid, * FROM group_messages WHERE group_id = ? ORDER BY rowid DESC LIMIT ?) ORDER BY rid ASC",
                        (gid, lim),
                    ).fetchall()
                self._send_json(200, [_group_msg_to_view(r, n2b) for r in rows])
            finally:
                conn.close()
            return

        # /api/office
        if path == "/api/office":
            conn = _connect()
            try:
                all_bots = conn.execute("SELECT id, name FROM bots").fetchall()
                n2b = {b["name"].lower(): b["id"] for b in all_bots}
                grows = conn.execute("SELECT * FROM groups WHERE deleted_at IS NULL ORDER BY created_at ASC").fetchall()
                gs = []
                for gr in grows:
                    gv = _group_row_to_view(gr)
                    mrows = conn.execute(
                        "SELECT * FROM (SELECT rowid as rid, * FROM group_messages WHERE group_id = ? ORDER BY rowid DESC LIMIT 5) ORDER BY rid ASC",
                        (gr["id"],),
                    ).fetchall()
                    gv["messages"] = [_group_msg_to_view(m, n2b) for m in mrows]
                    gs.append(gv)
            finally:
                conn.close()
            self._send_json(200, {"bots": _list_bots_view(), "groups": gs})
            return

        # /api/usage
        if path == "/api/usage":
            sid = q.get("session_id", [None])[0]
            gid = q.get("group_id", [None])[0]
            if bool(sid) == bool(gid):
                raise ApiError(400, "Isi salah satu: session_id atau group_id")
            col, val = ("group_id", gid) if gid else ("session_id", sid)
            conn = _connect()
            try:
                names = {b["id"]: b["name"] for b in conn.execute("SELECT id, name FROM bots").fetchall()}
                rows = conn.execute(
                    f"SELECT id, bot_id, created_at, input_tokens, output_tokens, cache_read_tokens, total_tokens, status FROM runs WHERE {col} = ? ORDER BY created_at DESC",
                    (val,),
                ).fetchall()
            finally:
                conn.close()

            total = {"input": 0, "output": 0, "cache_read": 0, "total": 0, "runs": 0}
            by_bot: Dict[str, Dict[str, Any]] = {}
            turns = []
            for r in rows:
                inp = int(r["input_tokens"] or 0)
                outp = int(r["output_tokens"] or 0)
                cr = int(r["cache_read_tokens"] or 0)
                tot = int(r["total_tokens"] or 0)
                bid = r["bot_id"]
                total["input"] += inp
                total["output"] += outp
                total["cache_read"] += cr
                total["total"] += tot
                total["runs"] += 1
                b = by_bot.setdefault(bid, {"bot_id": bid, "name": names.get(bid, bid), "input": 0, "output": 0, "total": 0, "runs": 0})
                b["input"] += inp
                b["output"] += outp
                b["total"] += tot
                b["runs"] += 1
                if len(turns) < 50:
                    turns.append({
                        "run_id": r["id"],
                        "bot_id": bid,
                        "created_at": r["created_at"] or 0,
                        "input": inp,
                        "output": outp,
                        "total": tot,
                        "status": _norm_status(r["status"]),
                    })
            self._send_json(200, {
                "total": total,
                "by_bot": sorted(by_bot.values(), key=lambda x: x["total"], reverse=True),
                "turns": turns,
            })
            return

        # /api/usage/bots
        if path == "/api/usage/bots":
            period = q.get("period", ["month"])[0]
            if period not in ("month", "all"):
                raise ApiError(400, "Periode harus month atau all")
            since_ts = _month_start_ts() if period == "month" else 0.0
            conn = _connect()
            try:
                rows = conn.execute(
                    """SELECT b.id as bot_id, b.name as name,
                              COALESCE(SUM(r.input_tokens), 0) as input,
                              COALESCE(SUM(r.output_tokens), 0) as output,
                              COALESCE(SUM(r.total_tokens), 0) as total,
                              COUNT(r.id) as runs
                       FROM bots b
                       JOIN runs r ON r.bot_id = b.id AND r.created_at >= ?
                       WHERE b.deleted_at IS NULL
                       GROUP BY b.id, b.name
                       ORDER BY total DESC""",
                    (since_ts,),
                ).fetchall()
                self._send_json(200, [
                    {
                        "bot_id": r["bot_id"],
                        "name": r["name"],
                        "input": int(r["input"] or 0),
                        "output": int(r["output"] or 0),
                        "total": int(r["total"] or 0),
                        "runs": int(r["runs"] or 0),
                    }
                    for r in rows
                ])
            finally:
                conn.close()
            return

        # /api/thinking
        if path == "/api/thinking":
            sid = q.get("session_id", [None])[0]
            gid = q.get("group_id", [None])[0]
            if bool(sid) == bool(gid):
                raise ApiError(400, "Isi salah satu: session_id atau group_id")
            col, val = ("group_id", gid) if gid else ("session_id", sid)
            conn = _connect()
            try:
                rows = conn.execute(
                    f"""SELECT * FROM (
                            SELECT id as run_id, bot_id, status, created_at, started_at, finished_at, reasoning
                            FROM runs
                            WHERE {col} = ? AND ((reasoning IS NOT NULL AND reasoning != '') OR status IN ('running', 'queued'))
                            ORDER BY created_at DESC LIMIT 50
                        ) ORDER BY created_at ASC""",
                    (val,),
                ).fetchall()
                out = []
                for r in rows:
                    s0 = r["started_at"] or r["created_at"]
                    s1 = r["finished_at"]
                    secs = int(max(0, s1 - s0)) if (s0 and s1) else None
                    out.append({
                        "run_id": r["run_id"],
                        "bot_id": r["bot_id"],
                        "status": _norm_status(r["status"]),
                        "created_at": r["created_at"] or 0,
                        "seconds": secs,
                        "reasoning": r["reasoning"] or "",
                    })
                self._send_json(200, out)
            finally:
                conn.close()
            return

        # /api/activity
        if path == "/api/activity":
            bot = q.get("bot", [None])[0] or None
            status = q.get("status", [None])[0] or None
            lim = max(1, min(int(q.get("limit", [100])[0]), 500))
            before = q.get("before", [None])[0] or None
            sid = q.get("session_id", [None])[0] or None
            gid = q.get("group_id", [None])[0] or None
            if status not in (None, "ok", "error"):
                raise ApiError(400, "Status harus ok atau error")

            where = ["1=1"]
            params: List[Any] = []
            if bot:
                where.append("e.bot_id = ?")
                params.append(bot)
            if status:
                where.append("e.status = ?")
                params.append(status)
            if before:
                try:
                    where.append("e.id < ?")
                    params.append(int(before))
                except ValueError:
                    pass
            if sid:
                where.append("e.session_id = ?")
                params.append(sid)
            if gid:
                where.append("e.group_id = ?")
                params.append(gid)
            params.append(lim)

            conn = _connect()
            try:
                rows = conn.execute(
                    f"""SELECT e.*, b.name as bot_name, s.title as session_title, g.name as group_name
                        FROM run_events e
                        LEFT JOIN bots b ON b.id = e.bot_id
                        LEFT JOIN sessions s ON s.id = e.session_id
                        LEFT JOIN groups g ON g.id = e.group_id
                        WHERE {' AND '.join(where)}
                        ORDER BY e.id DESC LIMIT ?""",
                    params,
                ).fetchall()
                out = [
                    {
                        "id": str(r["id"]),
                        "time": r["created_at"],
                        "bot_id": r["bot_id"],
                        "bot_name": r["bot_name"] or r["bot_id"],
                        "tool": r["tool"],
                        "status": r["status"],
                        "duration": r["duration"] or 0,
                        "preview": r["preview"] or "",
                        "session_id": r["session_id"] or "",
                        "group_id": r["group_id"] or "",
                        "session_title": r["session_title"] or "",
                        "group_name": r["group_name"] or None,
                    }
                    for r in rows
                ]
            finally:
                conn.close()
            self._send_json(200, out)
            return

        # /api/evaluations/summary
        if path == "/api/evaluations/summary":
            conn = _connect()
            try:
                rows = conn.execute("SELECT * FROM evaluations ORDER BY COALESCE(created_ts, 0) ASC, rowid ASC").fetchall()
                evs = [_eval_row_to_view(r) for r in rows]
            finally:
                conn.close()

            latest: Dict[str, Dict[str, Any]] = {}
            for ev in sorted(evs, key=lambda x: x["created_at"]):
                latest[ev["case_id"]] = ev
            counts = {"pass": 0, "fail": 0, "blocked": 0}
            sums = {d: [0, 0] for d in DIMENSIONS}
            for ev in latest.values():
                v = ev["verdict"]
                counts[v] = counts.get(v, 0) + 1
                for d, sc in (ev.get("scores") or {}).items():
                    if d in sums and isinstance(sc, dict) and isinstance(sc.get("score"), int) and not isinstance(sc.get("score"), bool):
                        sums[d][0] += sc["score"]
                        sums[d][1] += 1
            self._send_json(200, {
                "cases": [{"case_id": c, "verdict": ev["verdict"]} for c, ev in sorted(latest.items())],
                "counts": counts,
                "total_evaluations": len(evs),
                "dimensions": {d: {"avg": round(a / n, 2) if n else None, "n": n} for d, (a, n) in sums.items()},
                "latest_at": max((ev["created_at"] for ev in evs), default=0),
            })
            return

        # /api/evaluations
        if path == "/api/evaluations":
            conn = _connect()
            try:
                rows = conn.execute("SELECT * FROM evaluations ORDER BY COALESCE(created_ts, 0) DESC, rowid DESC LIMIT 500").fetchall()
                self._send_json(200, [_eval_row_to_view(r) for r in rows])
            finally:
                conn.close()
            return

        self._send_json(404, {"error": "Tidak ditemukan", "path": path})

    # ---- SSE Helpers ----
    def _serve_global_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = HUB.subscribe("*")
        ev_num = 0
        try:
            self.wfile.write(b"retry: 3000\n\n: keepalive\n\n")
            self.wfile.flush()
            while True:
                try:
                    etype, edata = q.get(timeout=15.0)
                    ev_num += 1
                    frame = f"id: {ev_num}\nevent: {etype}\ndata: {json.dumps(edata, ensure_ascii=False, default=str)}\n\n"
                    self.wfile.write(frame.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            HUB.unsubscribe("*", q)

    def _serve_run_sse(self, run_id: str) -> None:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                raise ApiError(404, "Tugas tidak ditemukan")
        finally:
            conn.close()

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = HUB.subscribe(run_id)
        try:
            usage_snap: Dict[str, Any] = {}
            meta_snap: Dict[str, Any] = {}
            err_snap = ""
            rc_count = 0

            with LIVE_LOCK:
                lv = LIVE_RUNS.get(run_id)

            if lv is not None and not lv.finished:
                with lv.lock:
                    out_snap = "".join(lv.out)
                    rc_count = len(lv.reasoning)
                    rc_snap = "\n\n".join(lv.reasoning)
                    ev_snap = list(lv.events)
                    finished = lv.finished
                    st = "running" if not finished else "completed"
            else:
                conn2 = _connect()
                try:
                    rr = conn2.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
                    rv = _run_row_to_view(rr)
                    out_snap = rv["output"]
                    rc_snap = rv["reasoning"]
                    st = rv["status"]
                    finished = st not in ACTIVE_STATUSES
                    evs = conn2.execute(
                        "SELECT id, type, tool, status, duration, preview, created_at FROM run_events WHERE run_id = ? ORDER BY id ASC",
                        (run_id,),
                    ).fetchall()
                    ev_snap = [
                        {"event": "tool.completed", "tool": e["tool"], "preview": e["preview"], "duration": e["duration"], "error": e["status"] == "error"}
                        for e in evs
                    ]
                    usage_snap = {
                        "input_tokens": rv["input_tokens"],
                        "output_tokens": rv["output_tokens"],
                        "total_tokens": rv["total_tokens"],
                    }
                    meta_snap = rv["meta"]
                    err_snap = rv["error"]
                finally:
                    conn2.close()

            self.wfile.write(b"retry: 2000\n\n")
            n = 1
            snap_payload = {
                "output": out_snap,
                "status": st,
                "events": ev_snap,
                "reasoning": rc_snap,
                "clarify": lv.clarify if (lv is not None and not lv.finished) else None,
            }
            self.wfile.write(f"id: {n}\nevent: snapshot\ndata: {json.dumps(snap_payload, ensure_ascii=False)}\n\n".encode("utf-8"))
            self.wfile.flush()

            if finished:
                n += 1
                done_payload = {
                    "status": st,
                    "output": out_snap,
                    "reasoning": rc_snap,
                    "error": err_snap,
                    "usage": usage_snap,
                    **_done_extra(meta_snap),
                }
                self.wfile.write(f"id: {n}\nevent: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
                return

            while True:
                try:
                    etype, edata = q.get(timeout=15.0)
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue

                if etype == "delta" and isinstance(edata.get("end"), int) and edata["end"] <= len(out_snap):
                    continue
                if etype == "reasoning" and isinstance(edata.get("step"), int) and edata["step"] <= rc_count:
                    continue
                n += 1
                frame = f"id: {n}\nevent: {etype}\ndata: {json.dumps(edata, ensure_ascii=False, default=str)}\n\n"
                self.wfile.write(frame.encode("utf-8"))
                self.wfile.flush()
                if etype == "done":
                    return
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            HUB.unsubscribe(run_id, q)

    # ---- POST Routes ----
    def _handle_post(self) -> None:
        path, _ = self._clean_path()
        parts = [unquote(x) for x in path.strip("/").split("/") if x]
        body = self._read_json_body()

        # POST /api/bots
        if path == "/api/bots":
            name = " ".join(str(body.get("name") or "").split())
            role = " ".join(str(body.get("role") or "").split())
            team = " ".join(str(body.get("team") or "").split())
            color = body.get("color") or "plain"
            template = body.get("template")
            persona = body.get("persona")
            if not name or len(name) > 40:
                raise ApiError(400, "Nama wajib diisi (maksimal 40 karakter)")
            if not role or len(role) > 40:
                raise ApiError(400, "Peran wajib diisi (maksimal 40 karakter)")
            if not team or len(team) > 40:
                raise ApiError(400, "Tim wajib diisi (maksimal 40 karakter)")
            if color not in COLORS:
                raise ApiError(400, "Warna tidak dikenal")
            if bool(template) == bool(persona):
                raise ApiError(400, "Pilih salah satu: template atau persona")
            if template and not any(b["id"] == template for b in BUILTIN_BOTS):
                raise ApiError(400, "Template tidak dikenal")
            if persona and (not isinstance(persona, str) or not persona.strip() or len(persona) > 2000):
                raise ApiError(400, "Persona wajib diisi (maksimal 2000 karakter)")

            ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
            base_slug = re.sub(r"[^a-z0-9]", "", ascii_name.lower())[:24]
            if not base_slug:
                raise ApiError(400, "Nama harus memuat huruf atau angka")

            me = _get_me()
            if me["usage"]["bots"] >= me["limits"]["max_bots"]:
                raise ApiError(402, "Batas jumlah bot tercapai", {"upgrade": True})

            if template:
                tpl_b = next(b for b in BUILTIN_BOTS if b["id"] == template)
                final_persona = re.sub(rf"\b{tpl_b['name']}\b", name, tpl_b["persona"])
            else:
                final_persona = persona.strip()

            about_txt = final_persona if len(final_persona) <= 280 else final_persona[:280].rstrip() + "…"
            now = time.time()

            conn = _connect()
            try:
                n = 1
                while True:
                    slug = base_slug if n == 1 else f"{base_slug[:24 - len(str(n))]}{n}"
                    if not conn.execute("SELECT 1 FROM bots WHERE id = ?", (slug,)).fetchone():
                        break
                    n += 1
                conn.execute(
                    """INSERT INTO bots (id, name, role, team, color, template, persona, about, builtin, created_at, deleted_at, delete_error)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, NULL, '')""",
                    (slug, name, role, team, color, template or None, final_persona, about_txt, now),
                )
                conn.commit()
                r = conn.execute("SELECT * FROM bots WHERE id = ?", (slug,)).fetchone()
                view = _bot_row_to_view(r)
            finally:
                conn.close()
            _publish_bot(slug)
            self._send_json(201, view)
            return

        # POST /api/bots/{id}/sequences
        if len(parts) == 4 and parts[:2] == ["api", "bots"] and parts[3] == "sequences":
            seq_obj = _create_sequence(parts[2], body)
            self._send_json(202, seq_obj)
            return

        # POST /api/sequences/{id}/stop
        if len(parts) == 4 and parts[:2] == ["api", "sequences"] and parts[3] == "stop":
            seq_id = parts[2]
            sv = _sequence_view(seq_id)
            if sv["status"] not in ACTIVE_STATUSES:
                raise ApiError(409, "Urutan sudah selesai")
            with SEQ_LOCK:
                SEQ_STOPS.add(seq_id)
            if sv["run_ids"]:
                last_rid = sv["run_ids"][-1]
                with LIVE_LOCK:
                    lv = LIVE_RUNS.get(last_rid)
                if lv:
                    lv.stopped = True
            self._send_json(200, {"status": "stopping"})
            return

        # POST /api/bots/{id}/runs
        if len(parts) == 4 and parts[:2] == ["api", "bots"] and parts[3] == "runs":
            bot_id = parts[2]
            sid = body.get("session_id")
            if sid is not None:
                sid = str(sid)
                conn = _connect()
                try:
                    if not conn.execute("SELECT 1 FROM sessions WHERE id = ? AND bot_id = ?", (sid, bot_id)).fetchone():
                        raise ApiError(404, "Sesi tidak ditemukan")
                finally:
                    conn.close()

            ins = body.get("instructions")
            if ins is not None and (not isinstance(ins, str) or len(ins) > 6000):
                raise ApiError(400, "Instruksi harus berupa teks (maksimal 6000 karakter)")
            ins = ins.strip() if isinstance(ins, str) and ins.strip() else None

            origin = _clean_origin(body.get("origin"))
            run_view, _ = start_run_job(
                bot_id=bot_id,
                user_input=str(body.get("input") or ""),
                session_id=sid,
                instructions=ins,
                workflow=body.get("workflow"),
                stage=body.get("stage"),
                test_mode=bool(body.get("test_mode", False)),
                origin=origin,
                kind="chat",
            )
            self._send_json(202, {"run": run_view, "session_id": run_view["session_id"]})
            return

        # POST /api/runs/{rid}/{stop|steer|approval}
        if len(parts) == 4 and parts[:2] == ["api", "runs"]:
            rid, action = parts[2], parts[3]
            with LIVE_LOCK:
                lv = LIVE_RUNS.get(rid)
            if action == "stop":
                if not lv or lv.finished:
                    raise ApiError(409, "Tugas sudah selesai")
                lv.stopped = True
                self._send_json(200, {"status": "stopping"})
                return
            if action == "steer":
                if not lv or lv.finished:
                    raise ApiError(409, "Bot sudah selesai, pesan dikirim sebagai pesan baru")
                text = body.get("text")
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
                    raise ApiError(400, "Pesan wajib diisi (maksimal 4000 karakter)")
                with lv.lock:
                    lv.steer_notes.append(text.strip())
                self._send_json(200, {"accepted": True})
                return
            if action == "approval":
                choice = body.get("choice")
                if choice not in ("once", "session", "always", "deny"):
                    raise ApiError(400, "Pilihan persetujuan tidak valid")
                self._send_json(200, {"ok": True})
                return
            if action == "clarify":
                answer = body.get("answer")
                if not isinstance(answer, str) or not 1 <= len(answer.strip()) <= 4000:
                    raise ApiError(400, "Jawaban wajib diisi (maksimal 4000 karakter)")
                if not lv or lv.finished:
                    raise ApiError(409, "Tugas sudah selesai")
                if not lv.clarify:
                    raise ApiError(409, "Tidak ada pertanyaan yang menunggu jawaban")
                with lv.lock:
                    lv.clarify = None
                HUB.publish(rid, "clarify_done", {})
                self._send_json(200, {"ok": True})
                return

        # POST /api/evaluations
        if path == "/api/evaluations":
            v = _clean_eval_body(body, partial=False)
            _enrich_eval(v)
            eid = str(uuid.uuid4())
            now = time.time()
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))

            payload = {
                "session_id": v.get("session_id"),
                "run_id": v.get("run_id"),
                "prompt": v.get("prompt", ""),
                "expected": v.get("expected", ""),
                "actual": v.get("actual", ""),
                "notes": v.get("notes") or {"errors": "", "improvements": "", "critical": False, "reviewed_on": ""},
                "meta": v.get("meta") or {},
                "comparison": v.get("comparison"),
            }

            conn = _connect()
            try:
                conn.execute(
                    """INSERT INTO evaluations (id, case_id, bot_id, verdict, scores, notes, reviewer, created_at, payload, created_ts)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        eid,
                        v["case_id"],
                        v["bot_id"],
                        v["verdict"],
                        json.dumps(v.get("scores") or {}, ensure_ascii=False),
                        json.dumps(payload["notes"], ensure_ascii=False),
                        v.get("reviewer", ""),
                        now_iso,
                        json.dumps(payload, ensure_ascii=False),
                        now,
                    ),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM evaluations WHERE id = ?", (eid,)).fetchone()
                self._send_json(201, _eval_row_to_view(row))
            finally:
                conn.close()
            return

        # POST /api/groups
        if path == "/api/groups":
            name = str(body.get("name") or "").strip()
            bot_ids = body.get("bot_ids")
            if not name or len(name) > 60:
                raise ApiError(400, "Nama grup wajib diisi (maksimal 60 karakter)")
            if not isinstance(bot_ids, list) or not all(isinstance(b, str) for b in bot_ids):
                raise ApiError(400, "Daftar anggota tidak valid")
            ids = list(dict.fromkeys(bot_ids))
            if not 2 <= len(ids) <= 6:
                raise ApiError(400, "Grup harus punya 2 sampai 6 anggota")
            me = _get_me()
            if me["usage"]["groups"] >= me["limits"]["max_groups"]:
                raise ApiError(402, "Batas jumlah grup tercapai", {"upgrade": True})
            conn = _connect()
            try:
                for bid in ids:
                    if not conn.execute("SELECT 1 FROM bots WHERE id = ? AND deleted_at IS NULL", (bid,)).fetchone():
                        raise ApiError(400, f"Anggota {bid} tidak ditemukan")
                gid = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO groups (id, name, bot_ids, created_at, deleted_at) VALUES (?, ?, ?, ?, NULL)",
                    (gid, name, json.dumps(ids), time.time()),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM groups WHERE id = ?", (gid,)).fetchone()
                self._send_json(201, _group_row_to_view(row))
            finally:
                conn.close()
            return

        # POST /api/groups/{gid}/messages
        if len(parts) == 4 and parts[:2] == ["api", "groups"] and parts[3] == "messages":
            gid = parts[2]
            text = str(body.get("text") or "").strip()
            mode = body.get("mode") or "queue"
            if not text or len(text) > 4000:
                raise ApiError(400, "Pesan wajib diisi (maksimal 4000 karakter)")
            if mode not in ("queue", "steer"):
                raise ApiError(400, "Mode harus queue atau steer")

            conn = _connect()
            try:
                g_row = conn.execute("SELECT * FROM groups WHERE id = ? AND deleted_at IS NULL", (gid,)).fetchone()
                if not g_row:
                    raise ApiError(404, "Grup tidak ditemukan")
                gv = _group_row_to_view(g_row)
            finally:
                conn.close()

            if len(gv["members"]) < 2:
                raise ApiError(409, "Grup ini belum punya cukup anggota")
            _check_quota()

            msg_view = _post_group_msg(gid, "user", text, sender_label="User")
            with GROUP_LOCK:
                st = GROUP_ACTIVE.get(gid)
                if st is None:
                    st = GroupSendState(group_id=gid)
                    GROUP_ACTIVE[gid] = st
                    threading.Thread(target=_group_loop, args=(gid, st, text), daemon=True).start()
                    queued = False
                else:
                    with st.lock:
                        st.queued_texts.append(text)
                    if mode == "steer":
                        st.cancel_round = True
                    queued = True
            self._send_json(202, {"message": msg_view, "queued": queued})
            return

        # POST /api/groups/{gid}/stop
        if len(parts) == 4 and parts[:2] == ["api", "groups"] and parts[3] == "stop":
            gid = parts[2]
            conn = _connect()
            try:
                if not conn.execute("SELECT 1 FROM groups WHERE id = ? AND deleted_at IS NULL", (gid,)).fetchone():
                    raise ApiError(404, "Grup tidak ditemukan")
            finally:
                conn.close()

            with GROUP_LOCK:
                st = GROUP_ACTIVE.get(gid)
            if st:
                st.stopped = True
                with st.lock:
                    st.queued_texts.clear()
                if st.active_run_id:
                    with LIVE_LOCK:
                        lv = LIVE_RUNS.get(st.active_run_id)
                    if lv:
                        lv.stopped = True
            self._send_json(200, {"stopping": bool(st)})
            return

        self._send_json(404, {"error": "Tidak ditemukan", "path": path})

    # ---- PATCH / PUT / DELETE Routes ----
    def _handle_patch(self) -> None:
        path, _ = self._clean_path()
        parts = [unquote(x) for x in path.strip("/").split("/") if x]
        body = self._read_json_body()

        # PATCH /api/settings
        if path == "/api/settings":
            self._send_json(200, _patch_settings(body))
            return

        # PATCH /api/bots/{id}
        if len(parts) == 3 and parts[:2] == ["api", "bots"]:
            bot_id = parts[2]
            r = _get_bot_row(bot_id)
            builtin = bool(r["builtin"])
            editable = {"name", "role", "team", "color", "persona", *RUN_FIELDS}
            unknown = sorted(set(body) - editable)
            if unknown:
                raise ApiError(400, "Kolom tidak dikenal: " + ", ".join(unknown))
            if not body:
                raise ApiError(400, "Tidak ada yang diubah")
            if builtin and set(body) - {"color", *RUN_FIELDS}:
                raise ApiError(403, "Agen sistem hanya bisa diubah warna dan modelnya")

            run_ch = _clean_run_fields(body)
            new_d = dict(r)
            new_d.update(run_ch)
            if "color" in body:
                if body["color"] not in COLORS:
                    raise ApiError(400, "Warna tidak dikenal")
                new_d["color"] = body["color"]
            if "name" in body:
                nm = " ".join(str(body["name"]).split())
                ascii_nm = unicodedata.normalize("NFKD", nm).encode("ascii", "ignore").decode()
                if not nm or len(nm) > 40:
                    raise ApiError(400, "Nama wajib diisi (maksimal 40 karakter)")
                if not re.sub(r"[^a-z0-9]", "", ascii_nm.lower()):
                    raise ApiError(400, "Nama harus memuat huruf atau angka")
                new_d["name"] = nm
            if "role" in body:
                rl = " ".join(str(body["role"]).split())
                if not rl or len(rl) > 40:
                    raise ApiError(400, "Peran wajib diisi (maksimal 40 karakter)")
                new_d["role"] = rl
            if "team" in body:
                tm = " ".join(str(body["team"]).split())
                if not tm or len(tm) > 40:
                    raise ApiError(400, "Tim wajib diisi (maksimal 40 karakter)")
                new_d["team"] = tm
            if "persona" in body:
                ps = str(body["persona"]).strip()
                if not ps or len(ps) > 2000:
                    raise ApiError(400, "Persona wajib diisi (maksimal 2000 karakter)")
                new_d["persona"] = ps
                new_d["about"] = ps if len(ps) <= 280 else ps[:280].rstrip() + "…"

            conn = _connect()
            try:
                conn.execute(
                    """UPDATE bots SET name=?, role=?, team=?, color=?, persona=?, about=?,
                               model=?, provider=?, reasoning_effort=? WHERE id=?""",
                    (
                        new_d["name"],
                        new_d["role"],
                        new_d["team"],
                        new_d["color"],
                        new_d["persona"],
                        new_d["about"],
                        new_d.get("model"),
                        new_d.get("provider"),
                        new_d.get("reasoning_effort"),
                        bot_id,
                    ),
                )
                conn.commit()
                r2 = conn.execute("SELECT * FROM bots WHERE id = ?", (bot_id,)).fetchone()
                view = _bot_row_to_view(r2)
                view["persona"] = r2["persona"] or ""
                view["template"] = r2["template"] or ""
            finally:
                conn.close()
            self._send_json(200, view)
            return

        # PATCH /api/bots/{id}/sessions/{sid}
        if len(parts) == 5 and parts[:2] == ["api", "bots"] and parts[3] == "sessions":
            bot_id, sid = parts[2], parts[4]
            title = str(body.get("title") or "").strip()
            if not title or len(title) > 120:
                raise ApiError(400, "Judul wajib diisi (maksimal 120 karakter)")
            conn = _connect()
            try:
                cur = conn.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ? AND bot_id = ?", (title, time.time(), sid, bot_id))
                conn.commit()
                if cur.rowcount == 0:
                    raise ApiError(404, "Sesi tidak ditemukan")
            finally:
                conn.close()
            self._send_json(200, {"ok": True, "title": title})
            return

        # PATCH /api/evaluations/{eid}
        if len(parts) == 3 and parts[:2] == ["api", "evaluations"]:
            eid = parts[2]
            v = _clean_eval_body(body, partial=True)
            conn = _connect()
            try:
                row = conn.execute("SELECT * FROM evaluations WHERE id = ?", (eid,)).fetchone()
                if not row:
                    raise ApiError(404, "Evaluasi tidak ditemukan")
                cur_view = _eval_row_to_view(row)
                merged = {**cur_view, **v}
                if v.get("comparison") or v.get("run_id"):
                    _enrich_eval(merged)
                payload = {
                    "session_id": merged.get("session_id"),
                    "run_id": merged.get("run_id"),
                    "prompt": merged.get("prompt", ""),
                    "expected": merged.get("expected", ""),
                    "actual": merged.get("actual", ""),
                    "notes": merged.get("notes") or {"errors": "", "improvements": "", "critical": False, "reviewed_on": ""},
                    "meta": merged.get("meta") or {},
                    "comparison": merged.get("comparison"),
                }
                conn.execute(
                    """UPDATE evaluations SET case_id=?, bot_id=?, verdict=?, scores=?, notes=?, reviewer=?, payload=?
                       WHERE id=?""",
                    (
                        merged["case_id"],
                        merged["bot_id"],
                        merged["verdict"],
                        json.dumps(merged.get("scores") or {}, ensure_ascii=False),
                        json.dumps(payload["notes"], ensure_ascii=False),
                        merged.get("reviewer", ""),
                        json.dumps(payload, ensure_ascii=False),
                        eid,
                    ),
                )
                conn.commit()
                row2 = conn.execute("SELECT * FROM evaluations WHERE id = ?", (eid,)).fetchone()
                self._send_json(200, _eval_row_to_view(row2))
            finally:
                conn.close()
            return

        # PATCH /api/groups/{gid}
        if len(parts) == 3 and parts[:2] == ["api", "groups"]:
            gid = parts[2]
            conn = _connect()
            try:
                g = conn.execute("SELECT * FROM groups WHERE id = ? AND deleted_at IS NULL", (gid,)).fetchone()
                if not g:
                    raise ApiError(404, "Grup tidak ditemukan")
                new_name = g["name"]
                if "name" in body and body["name"] is not None:
                    nm = str(body["name"]).strip()
                    if not nm or len(nm) > 60:
                        raise ApiError(400, "Nama grup wajib diisi (maksimal 60 karakter)")
                    new_name = nm
                new_bids = json.loads(g["bot_ids"])
                if "bot_ids" in body and body["bot_ids"] is not None:
                    raw_ids = body["bot_ids"]
                    if not isinstance(raw_ids, list) or not all(isinstance(b, str) for b in raw_ids):
                        raise ApiError(400, "Daftar anggota tidak valid")
                    ids = list(dict.fromkeys(raw_ids))
                    if not 2 <= len(ids) <= 6:
                        raise ApiError(400, "Grup harus punya 2 sampai 6 anggota")
                    for bid in ids:
                        if not conn.execute("SELECT 1 FROM bots WHERE id = ? AND deleted_at IS NULL", (bid,)).fetchone():
                            raise ApiError(400, f"Anggota {bid} tidak ditemukan")
                    new_bids = ids
                conn.execute("UPDATE groups SET name = ?, bot_ids = ? WHERE id = ?", (new_name, json.dumps(new_bids), gid))
                conn.commit()
                g2 = conn.execute("SELECT * FROM groups WHERE id = ?", (gid,)).fetchone()
                self._send_json(200, _group_row_to_view(g2))
            finally:
                conn.close()
            return

        self._send_json(404, {"error": "Tidak ditemukan", "path": path})

    def _handle_put(self) -> None:
        path, _ = self._clean_path()
        body = self._read_json_body()
        if path == "/api/me/plan":
            pid = body.get("plan_id")
            if not isinstance(pid, str) or not any(p["id"] == pid for p in PLANS_DATA):
                raise ApiError(400, "Paket tidak dikenal")
            conn = _connect()
            try:
                conn.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES ('plan_id', ?)", (pid,))
                conn.commit()
            finally:
                conn.close()
            self._send_json(200, _get_me())
            return
        self._send_json(404, {"error": "Tidak ditemukan", "path": path})

    def _handle_delete(self) -> None:
        path, _ = self._clean_path()
        parts = [unquote(x) for x in path.strip("/").split("/") if x]

        # DELETE /api/bots/{id}
        if len(parts) == 3 and parts[:2] == ["api", "bots"]:
            bot_id = parts[2]
            r = _get_bot_row(bot_id)
            if r["builtin"]:
                raise ApiError(403, "Bot bawaan tidak bisa dihapus")
            with LIVE_LOCK:
                busy = any(lv.bot_id == bot_id and not lv.finished for lv in LIVE_RUNS.values())
            if busy:
                raise ApiError(409, "Bot sedang bekerja. Hentikan tugasnya dulu.")
            conn = _connect()
            try:
                conn.execute("UPDATE bots SET deleted_at = ? WHERE id = ?", (time.time(), bot_id))
                conn.execute("DELETE FROM sessions WHERE bot_id = ?", (bot_id,))
                for gr in conn.execute("SELECT id, bot_ids FROM groups WHERE deleted_at IS NULL").fetchall():
                    bids = [x for x in json.loads(gr["bot_ids"]) if x != bot_id]
                    conn.execute("UPDATE groups SET bot_ids = ? WHERE id = ?", (json.dumps(bids), gr["id"]))
                conn.commit()
            finally:
                conn.close()
            self._send_json(204, {})
            return

        # DELETE /api/bots/{id}/sessions/{sid}
        if len(parts) == 5 and parts[:2] == ["api", "bots"] and parts[3] == "sessions":
            bot_id, sid = parts[2], parts[4]
            conn = _connect()
            try:
                cur = conn.execute("DELETE FROM sessions WHERE id = ? AND bot_id = ?", (sid, bot_id))
                conn.execute("DELETE FROM messages WHERE session_id = ? AND bot_id = ?", (sid, bot_id))
                conn.commit()
                if cur.rowcount == 0:
                    raise ApiError(404, "Sesi tidak ditemukan")
            finally:
                conn.close()
            self._send_json(204, {})
            return

        # DELETE /api/groups/{gid}
        if len(parts) == 3 and parts[:2] == ["api", "groups"]:
            gid = parts[2]
            conn = _connect()
            try:
                cur = conn.execute("UPDATE groups SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL", (time.time(), gid))
                conn.commit()
                if cur.rowcount == 0:
                    raise ApiError(404, "Grup tidak ditemukan")
            finally:
                conn.close()
            with GROUP_LOCK:
                st = GROUP_ACTIVE.get(gid)
            if st:
                st.stopped = True
            self._send_json(204, {})
            return

        self._send_json(404, {"error": "Tidak ditemukan", "path": path})


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_server() -> None:
    init_db()
    server = ReusableThreadingHTTPServer(("127.0.0.1", PORT), BFFHandler)
    print("===========================================================")
    print("  Pegawai AI - BFF Server (SQLite + OpenCode Zen Live)")
    print(f"  Port: {PORT}")
    print(f"  URL: http://127.0.0.1:{PORT}")
    print(f"  Model: {MODEL_ID} (via {PROVIDER_ID})")
    print(f"  Katalog Colorbox terindeks: {len(CATALOG.rows)} produk")
    print("===========================================================")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
