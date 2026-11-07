"""Evaluation log for test scenarios: validation plus CRUD. Scores: 9 rubric dimensions, each 1-5 or null with a reason."""
import json
import uuid

from . import db
from .errors import ApiError

DIMENSIONS = ("accuracy", "relevance", "brand", "consistency", "knowledge", "instruction",
              "completeness", "error_handling", "human_review")
VERDICTS = ("pass", "fail", "blocked")
TEXT_LIMITS = {"case_id": 40, "bot_id": 60, "session_id": 80, "run_id": 80, "prompt": 20000,
               "expected": 20000, "actual": 40000, "reviewer": 80}
REQUIRED = ("case_id", "bot_id", "verdict")
_JSON = ("scores", "notes")


def clean_scores(raw) -> dict:
    if not isinstance(raw, dict):
        raise ApiError(400, "Skor harus berupa objek")
    out = {}
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


def clean(body: dict, partial: bool = False) -> dict:
    """Validated column values. partial=True (PATCH) checks only the keys given."""
    out: dict = {}
    for k, limit in TEXT_LIMITS.items():
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
        out["scores"] = clean_scores(body["scores"])
    if "notes" in body:
        n = body["notes"]
        if not isinstance(n, dict) or len(json.dumps(n)) > 20000:
            raise ApiError(400, "Catatan tidak valid")
        out["notes"] = n
    if not partial:
        for k in REQUIRED:
            if not out.get(k):
                raise ApiError(400, f"{k} wajib diisi")
    elif not out:
        raise ApiError(400, "Tidak ada yang diubah")
    return out


def _view(r: dict) -> dict:
    return {**r, "id": str(r["id"])}


def _marks(cols) -> str:
    return ", ".join("%s::jsonb" if c in _JSON else "%s" for c in cols)


def _vals(v: dict) -> list:
    return [json.dumps(x) if k in _JSON else x for k, x in v.items()]


async def list_all(uid: str) -> list[dict]:
    rows = await db.q("select * from evaluations where user_id = %s order by created_at desc limit 500", uid)
    return [_view(r) for r in rows]


async def create(uid: str, body: dict) -> dict:
    v = clean(body)
    eid = str(uuid.uuid4())
    cols = ["id", "user_id", *v]
    await db.ex(f"insert into evaluations ({', '.join(cols)}) values ({_marks(cols)})", eid, uid, *_vals(v))
    return _view(await db.q1("select * from evaluations where id = %s", eid))


async def update(uid: str, eid: str, body: dict) -> dict:
    try:
        uuid.UUID(eid)
    except ValueError:
        raise ApiError(404, "Evaluasi tidak ditemukan")
    v = clean(body, partial=True)
    sets = ", ".join(f"{k} = {m}" for k, m in zip(v, _marks(v).split(", ")))
    row = await db.q(f"update evaluations set {sets} where id = %s and user_id = %s returning *", *_vals(v), eid, uid)
    if not row:
        raise ApiError(404, "Evaluasi tidak ditemukan")
    return _view(row[0])
