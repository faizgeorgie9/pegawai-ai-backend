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
_JSON = ("scores", "notes", "meta", "comparison")
MODES = ("repeat", "agents")
CONSISTENCY = ("konsisten", "tidak_konsisten")


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


def _text(v, name: str, limit: int, required: bool = False) -> str:
    if not isinstance(v, str):
        raise ApiError(400, f"{name} harus berupa teks")
    v = v.strip()
    if required and not v:
        raise ApiError(400, f"{name} wajib diisi")
    if len(v) > limit:
        raise ApiError(400, f"{name} terlalu panjang (maksimal {limit} karakter)")
    return v


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def clean_comparison(raw) -> dict:
    """Comparison of 2-3 runs: mode 'repeat' (same agent, repeated) or 'agents' (two different agents), plus the consistency verdict."""
    if not isinstance(raw, dict):
        raise ApiError(400, "Perbandingan tidak valid")
    mode = raw.get("mode")
    if mode not in MODES:
        raise ApiError(400, "Mode perbandingan harus repeat atau agents")
    cons = raw.get("consistency")
    if cons not in CONSISTENCY:
        raise ApiError(400, "Pilih Konsisten atau Tidak konsisten")
    runs_in = raw.get("runs")
    if not isinstance(runs_in, list) or not 2 <= len(runs_in) <= 3:
        raise ApiError(400, "Perbandingan butuh 2 sampai 3 run")
    runs = []
    for r in runs_in:
        if not isinstance(r, dict):
            raise ApiError(400, "Run perbandingan tidak valid")
        tokens, meta = r.get("tokens", 0), r.get("meta", {})
        if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
            raise ApiError(400, "Jumlah token run tidak valid")
        if not isinstance(meta, dict) or len(json.dumps(meta)) > 8000:
            raise ApiError(400, "Data versi run tidak valid")
        sid = r.get("session_id")
        runs.append({"run_id": _text(r.get("run_id"), "run_id", TEXT_LIMITS["run_id"], True),
                     "session_id": _text(sid, "session_id", TEXT_LIMITS["session_id"]) if sid is not None else None,
                     "bot_id": _text(r.get("bot_id"), "bot_id", TEXT_LIMITS["bot_id"], True),
                     "output": _text(r.get("output", ""), "output", TEXT_LIMITS["actual"]),
                     "tokens": tokens, "duration": r["duration"] if _num(r.get("duration")) else None, "meta": meta})
    if len({r["run_id"] for r in runs}) != len(runs):
        raise ApiError(400, "Run perbandingan tidak boleh sama")
    bots = {r["bot_id"] for r in runs}
    if mode == "repeat" and len(bots) != 1:
        raise ApiError(400, "Ulang N kali harus memakai satu agen")
    if mode == "agents" and (len(runs) != 2 or len(bots) != 2):
        raise ApiError(400, "Dua agen butuh tepat dua agen berbeda")
    return {"mode": mode, "consistency": cons, "note": _text(raw.get("note", ""), "Catatan konsistensi", 2000), "runs": runs}


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
    if "comparison" in body:
        out["comparison"] = None if body["comparison"] is None else clean_comparison(body["comparison"])
    if "meta" in body:
        m = body["meta"]
        if not isinstance(m, dict) or len(json.dumps(m)) > 8000:
            raise ApiError(400, "Data versi tidak valid")
        out["meta"] = m
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
    return [json.dumps(x) if k in _JSON and x is not None else x for k, x in v.items()]


async def list_all(uid: str) -> list[dict]:
    rows = await db.q("select * from evaluations where user_id = %s order by created_at desc limit 500", uid)
    return [_view(r) for r in rows]


async def enrich(uid: str, v: dict) -> None:
    """Take version snapshot, tokens and time from the stored runs, not from the client. A comparison needs real runs."""
    cmp = v.get("comparison")
    ids = [r["run_id"] for r in cmp["runs"]] if cmp else [v["run_id"]] if v.get("run_id") else []
    good = []
    for i in ids:
        try:
            good.append(str(uuid.UUID(i)))
        except ValueError:
            pass
    rows = await db.q("select r.id, r.bot_id, r.session_id, r.total_tokens, r.meta, r.started_at, r.finished_at, b.team "
                      "from runs r join bots b on b.id = r.bot_id where r.user_id = %s and r.id = any(%s::uuid[])", uid, good)
    found = {str(r["id"]): r for r in rows}
    if not cmp:
        if ids and ids[0] in found:
            v["meta"] = found[ids[0]]["meta"] or {}
        return
    for r in cmp["runs"]:
        row = found.get(r["run_id"])
        if not row:
            raise ApiError(400, f"Run {r['run_id']} tidak ditemukan")
        done = row["finished_at"] and row["started_at"]
        r.update(bot_id=row["bot_id"], session_id=row["session_id"], tokens=row["total_tokens"], meta=row["meta"] or {},
                 duration=round((row["finished_at"] - row["started_at"]).total_seconds(), 1) if done else None)
    if cmp["mode"] == "agents" and len({found[r["run_id"]]["team"] for r in cmp["runs"]}) != 1:
        raise ApiError(400, "Dua agen harus dari tim yang sama")
    first = cmp["runs"][0]
    v["bot_id"], v["run_id"], v["session_id"], v["meta"] = first["bot_id"], first["run_id"], first["session_id"], first["meta"]


def summarize(rows: list[dict]) -> dict:
    """Experiment summary from the latest evaluation of each case: counts per verdict, average per rubric dimension, case list."""
    latest: dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: r["created_at"]):
        latest[r["case_id"]] = r
    counts = {"pass": 0, "fail": 0, "blocked": 0}
    sums = {d: [0, 0] for d in DIMENSIONS}
    for r in latest.values():
        counts[r["verdict"]] += 1
        for d, s in (r.get("scores") or {}).items():
            if d in sums and isinstance(s.get("score"), int):
                sums[d][0] += s["score"]
                sums[d][1] += 1
    return {"cases": [{"case_id": c, "verdict": r["verdict"]} for c, r in sorted(latest.items())],
            "counts": counts, "total_evaluations": len(rows),
            "dimensions": {d: {"avg": round(a / n, 2) if n else None, "n": n} for d, (a, n) in sums.items()},
            "latest_at": max((r["created_at"] for r in rows), default=None)}


async def summary(uid: str) -> dict:
    return summarize(await db.q("select case_id, verdict, scores, created_at from evaluations where user_id = %s", uid))


async def create(uid: str, body: dict) -> dict:
    v = clean(body)
    await enrich(uid, v)
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
    if v.get("comparison") or v.get("run_id"):
        await enrich(uid, v)
    sets = ", ".join(f"{k} = {m}" for k, m in zip(v, _marks(v).split(", ")))
    row = await db.q(f"update evaluations set {sets} where id = %s and user_id = %s returning *", *_vals(v), eid, uid)
    if not row:
        raise ApiError(404, "Evaluasi tidak ditemukan")
    return _view(row[0])
