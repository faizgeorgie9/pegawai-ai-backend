import json, re, glob, os
from pathlib import Path

EV = Path(__file__).parent / "evidence"

def strip_ansi(s):
    return re.sub(r"\x1b\[[0-9;]*m", "", s or "")

rows = []
for p in sorted(EV.glob("Q*_response.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    b = d.get("body") or {}
    out = strip_ansi(b.get("output") or "")
    m = re.search(r"===BAGIAN_1[^=]*===(.*?)(?:===BAGIAN_2|$)", out, re.S)
    part1 = (m.group(1).strip() if m else out).strip()
    score = re.search(r"SKOR_QA[:\s]*([0-9]{1,3})", out, re.I)
    esc = re.search(r"STATUS_ESKALASI[:\s]*([A-Z_ ]+)", out)
    tu = b.get("token_usage") or {}
    rows.append({
        "id": p.stem.split("_")[0],
        "http_status": d.get("http_status"),
        "elapsed_s": d.get("elapsed_s"),
        "provider": b.get("provider"),
        "model": b.get("model"),
        "fallback": b.get("fallback_applied"),
        "tokens": tu,
        "score": score.group(1) if score else None,
        "escalation": (esc.group(1).strip() if esc else None),
        "reply": part1,
        "flags": [k for k in ["30 hari", "1 jam", "refund disetujui", "sudah diteruskan",
                              "sudah dieskalasi", "kami akan menghubungi", "dijamin",
                              "pasti", "hari ini juga"] if k.lower() in part1.lower()],
    })

Path(EV / "runs_summary.json").write_text(
    json.dumps([{k: v for k, v in r.items() if k != "reply"} for r in rows],
               indent=2, ensure_ascii=False), encoding="utf-8")

for r in rows:
    print("=" * 100)
    print(f"{r['id']} | http={r['http_status']} | {r['elapsed_s']}s | {r['provider']}/{r['model']} | "
          f"fallback={r['fallback']} | tokens={r['tokens']} | QA={r['score']} | ESC={r['escalation']}")
    print(f"FLAGS: {r['flags']}")
    print("-" * 100)
    print(r["reply"])
    print()
