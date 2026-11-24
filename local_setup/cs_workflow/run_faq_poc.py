"""
S2-03A CS FAQ Proof-of-Concept runner (Intern 3).

Sends a small synthetic FAQ question set to Intern 1's shared backend
(POST /api/v1/agent/execute, department=customer_support).

Honesty notes:
- Knowledge is injected manually per question (no retrieval engine).
- Responses are real model output; nothing is fabricated here.
- If a request fails, the failure is saved as evidence, not skipped.
"""

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://127.0.0.1:8080/api/v1/agent/execute"
HERE = Path(__file__).parent
KB_PATH = HERE / "faq_knowledge_base.md"
Q_PATH = HERE / "faq_test_questions.json"
EV = HERE / "evidence"
EV.mkdir(exist_ok=True)

HEADERS = {
    "Content-Type": "application/json",
    "X-Pegawai-AI-Key": "dev-pegawai-ai-2026",
    "X-Department": "customer_support",
}


def load_kb_entries():
    """Parse '## Fn — title' blocks from the synthetic KB."""
    text = KB_PATH.read_text(encoding="utf-8")
    entries = {}
    current = None
    buf = []
    for line in text.splitlines():
        if line.startswith("## F"):
            if current:
                entries[current] = "\n".join(buf).strip()
            head = line[3:].strip()
            current = head.split("—")[0].strip()
            buf = [head]
        elif current is not None:
            if line.startswith("## ") and not line.startswith("## F"):
                entries[current] = "\n".join(buf).strip()
                current = None
                buf = []
            else:
                buf.append(line)
    if current:
        entries[current] = "\n".join(buf).strip()
    return entries


def build_prompt(question, ids, kb):
    blocks = []
    for kid in ids:
        blocks.append(kb.get(kid, f"[{kid} NOT FOUND]"))
    return (
        "PERTANYAAN PELANGGAN:\n"
        f"{question}\n\n"
        "KNOWLEDGE BASE RESMI (satu-satunya sumber kebenaran; jangan menambah fakta "
        "di luar ini, jangan mengarang kebijakan, harga, atau janji):\n"
        + "\n\n".join(blocks)
        + "\n\nJika informasi yang diminta tidak ada di knowledge base, nyatakan bahwa "
        "hal itu perlu ditinjau staf manusia. Jangan menjanjikan hasil."
    )


def call(payload, timeout=240):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE, data=data, headers=HEADERS, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8")
            return r.status, json.loads(body), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", "replace")}, time.time() - t0
    except Exception as e:
        return None, {"error": repr(e)}, time.time() - t0


def main():
    ids = sys.argv[1:]
    kb = load_kb_entries()
    qs = json.loads(Q_PATH.read_text(encoding="utf-8"))["questions"]
    if ids:
        qs = [q for q in qs if q["id"] in ids]

    summary = []
    for q in qs:
        prompt = build_prompt(q["question"], q["knowledge_ids"], kb)
        payload = {
            "customer_id": q["customer_id"],
            "department": "customer_support",
            "prompt": prompt,
            "agent_mode": "auto",
            "provider": "opencode-go",
            "model": "deepseek-v4.1-flash",
            "timeout_seconds": 240,
        }
        (EV / f"{q['id']}_request.json").write_text(
            json.dumps({"meta": q, "payload": payload}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        status, resp, elapsed = call(payload)
        (EV / f"{q['id']}_response.json").write_text(
            json.dumps({"http_status": status, "elapsed_s": round(elapsed, 2), "body": resp},
                       indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        ok = status == 200 and isinstance(resp, dict) and resp.get("status") == "success"
        out = (resp or {}).get("output") or ""
        summary.append({
            "id": q["id"],
            "type": q["type"],
            "http_status": status,
            "ok": ok,
            "elapsed_s": round(elapsed, 2),
            "provider": (resp or {}).get("executed", {}).get("provider"),
            "model": (resp or {}).get("executed", {}).get("model"),
            "output_chars": len(out),
            "error": None if ok else str((resp or {}).get("error"))[:300],
        })
        print(f"{q['id']}: http={status} ok={ok} {elapsed:.1f}s out={len(out)}ch", flush=True)

    (EV / "runs_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
