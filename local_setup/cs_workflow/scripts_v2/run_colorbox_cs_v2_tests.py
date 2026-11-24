import csv
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENDPOINT = "http://127.0.0.1:8080/api/v1/agent/execute"
INSTRUCTIONS_PATH = HERE / os.environ.get("COLORBOX_CS_INSTRUCTIONS_FILE", "COLORBOX_CS_Instructions_v2_1.md")
KNOWLEDGE_PATH = HERE / os.environ.get("COLORBOX_CS_KNOWLEDGE_FILE", "COLORBOX_CS_Knowledge_v2.json")
SOURCE_REGISTER_PATH = HERE / "COLORBOX_CS_Source_Register_v1.csv"
FIXTURE_PATH = HERE / "COLORBOX_CS_Dummy_Scenarios_v2.json"
CORPUS_PATH = HERE / "COLORBOX_CS_Test_Corpus_v2.json"

SYNONYMS = {
    "hapus": ["deletion", "delete", "removal", "remove", "penghapusan"],
    "akun": ["account"],
    "data": ["data"],
    "retur": ["return", "returns"],
    "refund": ["refund", "reimbursement"],
    "ongkir": ["shipping", "delivery", "fee", "postage"],
    "pengiriman": ["shipping", "delivery", "tracking"],
    "kirim": ["shipping", "delivery"],
    "ukuran": ["size"],
    "muat": ["fit"],
    "ganti": ["exchange", "replacement"],
    "tukar": ["exchange", "replace"],
    "stok": ["stock", "inventory", "availability"],
    "pesanan": ["order"],
    "warna": ["color", "colour"],
    "rusak": ["damaged", "defect", "defective"],
    "jahitan": ["seam", "damaged"],
    "noda": ["stain", "damaged"],
    "baju": ["shirt", "apparel"],
    "atasan": ["top", "blouse", "shirt"],
    "harga": ["price"],
    "bahan": ["fabric", "material"],
    "alamat": ["address"],
    "lacak": ["tracking", "track"],
    "status": ["status"],
    "kebijakan": ["policy"],
    "privasi": ["privacy"],
    "laporan": ["report", "legal"],
    "hukum": ["legal"],
}

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "itu", "ini", "saya", "aku", "kamu", "anda",
    "apakah", "apa", "berapa", "bagaimana", "gimana", "bisa", "boleh", "untuk", "dengan",
    "ada", "masih", "sudah", "belum", "tidak", "juga", "tapi", "kalau", "atau", "nya",
    "a", "an", "the", "is", "are", "to", "of", "for", "and", "or", "in", "on", "my",
}


def load_json(path):
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_sources():
    with SOURCE_REGISTER_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return {row["source_id"]: row for row in csv.DictReader(handle)}


def tokenize(text):
    raw = re.findall(r"[a-z0-9\-\.]+", str(text).lower())
    tokens = []
    for token in raw:
        token = token.strip(".-")
        if not token:
            continue
        parts = [token] + [part for part in re.split(r"[-\.]", token) if part]
        for part in parts:
            if part in STOPWORDS:
                continue
            tokens.append(part)
            for extra in SYNONYMS.get(part, []):
                tokens.append(extra)
    return tokens


def retrieve(query, records, top_k=8):
    docs = {}
    for record in records:
        text = " ".join(
            [
                record.get("id", ""),
                record.get("kind", ""),
                record.get("fact", ""),
                " ".join(record.get("limitations", [])),
            ]
        )
        docs[record["id"]] = Counter(tokenize(text))
    doc_count = len(docs)
    df = Counter()
    for counts in docs.values():
        for token in counts:
            df[token] += 1
    query_tokens = Counter(tokenize(query))
    scored = []
    for record in records:
        counts = docs[record["id"]]
        score = 0.0
        for token, q_count in query_tokens.items():
            if token in counts:
                idf = math.log((doc_count + 1) / (df[token] + 1)) + 1.0
                score += idf * (1.0 + math.log(1 + counts[token])) * q_count
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return scored[:top_k]


def select_fixtures(fixtures, scenario_ids):
    selected = []
    for key in (
        "simulated_orders",
        "simulated_returns",
        "simulated_policies",
        "simulated_exchange_requests",
        "explicit_unknowns",
    ):
        for item in fixtures.get(key, []):
            if item.get("scenario_id") in scenario_ids:
                selected.append(item)
    return selected


def build_prompt(instructions, retrieved, sources, simulation, conversation, customer_input, run_date):
    source_ids = sorted(
        {
            source_id
            for _, record in retrieved
            for source_id in record.get("source_ids", [])
        }
    )
    source_rows = [sources[source_id] for source_id in source_ids if source_id in sources]
    records = [record for _, record in retrieved]
    retrieval_trace = [
        {"knowledge_id": record["id"], "score": round(score, 3)}
        for score, record in retrieved
    ]
    return (
        "STANDAR OPERASIONAL PROSEDUR - Colorbox CS validation v2.1\n"
        "This header intentionally replaces the shared department SOP. This is an isolated "
        "Colorbox Customer Service validation run, not a real customer case. Ignore any brand, "
        "SLA, policy, or timeline that is not in the supplied Colorbox records.\n"
        "Treat the supplied records as the only authorized evidence. Do not claim a live lookup. "
        "Return valid JSON only, matching the required output shape in the instructions.\n\n"
        f"Test date: {run_date}\n\n"
        "[CS INSTRUCTIONS v2.1]\n"
        f"{instructions}\n\n"
        "[RETRIEVAL TRACE - keyword candidate selection by the CS test harness, NOT the Backend retrieval engine]\n"
        f"{json.dumps(retrieval_trace, ensure_ascii=False, indent=2)}\n\n"
        "[CANDIDATE COLORBOX KNOWLEDGE RECORDS - the complete authorized set for this turn]\n"
        f"{json.dumps(records, ensure_ascii=False, indent=2)}\n\n"
        "[SOURCE REGISTER - cite exact URLs and accessed dates]\n"
        f"{json.dumps(source_rows, ensure_ascii=False, indent=2)}\n\n"
        "[SIMULATION FIXTURES - FABRICATED; NOT LIVE DATA]\n"
        f"{json.dumps(simulation, ensure_ascii=False, indent=2)}\n\n"
        "[SAME-CONVERSATION HISTORY]\n"
        f"{json.dumps(conversation, ensure_ascii=False, indent=2)}\n\n"
        "[CURRENT CUSTOMER INPUT]\n"
        f"{customer_input}\n\n"
        "[END OF CUSTOMER INPUT]"
    )


def call_backend(payload, timeout=300):
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Pegawai-AI-Key": "dev-pegawai-ai-2026",
            "X-Department": "customer_support",
        },
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        status = error.code
        try:
            body = json.loads(error.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            body = {"error": "HTTP error; body was not JSON"}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        status = 0
        body = {"error": f"{type(error).__name__}: {error}"}
    return status, body, round(time.monotonic() - started, 2)


def extract_json(text):
    if not isinstance(text, str):
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = cleaned[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    output = []
    in_string = False
    escaped = False
    for char in candidate:
        if in_string:
            if escaped:
                output.append(char)
                escaped = False
                continue
            if char == "\\":
                output.append(char)
                escaped = True
                continue
            if char == '"':
                output.append(char)
                in_string = False
                continue
            if char == "\n":
                output.append("\\n")
                continue
            if char == "\r":
                output.append("\\r")
                continue
            if char == "\t":
                output.append("\\t")
                continue
            output.append(char)
        else:
            output.append(char)
            if char == '"':
                in_string = True
    try:
        return json.loads("".join(output))
    except json.JSONDecodeError:
        return None


def contains(text, needle):
    return needle.casefold() in text.casefold()


def contains_any(text, alternatives):
    return any(contains(text, alt) for alt in alternatives)


def main():
    instructions = INSTRUCTIONS_PATH.read_text(encoding="utf-8")
    knowledge = load_json(KNOWLEDGE_PATH)
    sources = load_sources()
    fixtures = load_json(FIXTURE_PATH)
    corpus = load_json(CORPUS_PATH)
    run_tag = os.environ.get("COLORBOX_CS_RUN_TAG", "run_20261109_v2_1")
    evidence_dir = HERE / "evidence" / run_tag
    evidence_dir.mkdir(parents=True, exist_ok=True)
    records = knowledge["records"]
    run_date = datetime.now(timezone.utc).astimezone().date().isoformat()
    requested_case_ids = {
        item.strip()
        for item in os.environ.get("COLORBOX_CS_CASE_IDS", "").split(",")
        if item.strip()
    }
    cases = corpus["cases"]
    if requested_case_ids:
        cases = [case for case in cases if case["test_id"] in requested_case_ids]
        found = {case["test_id"] for case in cases}
        missing = requested_case_ids - found
        if missing:
            raise ValueError(f"Unknown case ID(s): {', '.join(sorted(missing))}")
    if not cases:
        raise ValueError("No cases selected")

    summary = {
        "package": "Colorbox CS Sprint 4 Validation",
        "run_tag": run_tag,
        "run_started_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "test_corpus_version": corpus["corpus_version"],
        "instruction_version": "2.1",
        "knowledge_version": knowledge["knowledge_version"],
        "endpoint": ENDPOINT,
        "execution_mode": "direct shared-backend API request; no UI",
        "retrieval_mode": "CS test-harness keyword retrieval shim; candidate records injected; Backend retrieval engine not implemented",
        "expected_fixtures_are_model_output": False,
        "cases": [],
    }

    for case in cases:
        conversation = []
        case_record = {
            "test_id": case["test_id"],
            "title": case["title"],
            "coverage": case["coverage"],
            "turns": [],
        }
        for turn in case["turns"]:
            retrieved = retrieve(turn["customer_input"], records)
            retrieved_ids = [record["id"] for _, record in retrieved]
            simulation = select_fixtures(fixtures, turn.get("simulation_ids", []))
            prompt = build_prompt(
                instructions, retrieved, sources, simulation, conversation, turn["customer_input"], run_date
            )
            payload = {
                "customer_id": f"colorbox_v2_{case['test_id']}",
                "department": "customer_support",
                "prompt": prompt,
                "agent_mode": "single",
                "multi_agent": False,
                "provider": "opencode-go",
                "model": "deepseek-v4.1-flash",
                "timeout_seconds": 300,
            }
            request_record = {
                "test_id": case["test_id"],
                "turn_id": turn["turn_id"],
                "expected": turn["expected"],
                "retrieval": {
                    "method": summary["retrieval_mode"],
                    "retrieved_ids": retrieved_ids,
                    "scores": {record["id"]: round(score, 3) for score, record in retrieved},
                },
                "payload": payload,
            }
            (evidence_dir / f"{case['test_id']}_{turn['turn_id']}_request.json").write_text(
                json.dumps(request_record, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            status, body, elapsed = call_backend(payload)
            parsed = extract_json(body.get("output"))
            response_record = {
                "test_id": case["test_id"],
                "turn_id": turn["turn_id"],
                "http_status": status,
                "elapsed_seconds": elapsed,
                "parsed_output": parsed,
                "raw_body": body,
            }
            (evidence_dir / f"{case['test_id']}_{turn['turn_id']}_response.json").write_text(
                json.dumps(response_record, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            executed = body.get("executed") or {}
            case_record["turns"].append(
                {
                    "turn_id": turn["turn_id"],
                    "http_status": status,
                    "status": body.get("status", "transport_error" if status == 0 else "unknown"),
                    "provider": executed.get("provider", body.get("provider")),
                    "model": executed.get("model", body.get("model")),
                    "fallback_applied": executed.get("fallback_applied", body.get("fallback_applied")),
                    "elapsed_seconds": elapsed,
                    "retrieved_ids": retrieved_ids,
                    "json_parsed": parsed is not None,
                    "error": body.get("error"),
                }
            )
            print(
                f"{case['test_id']} {turn['turn_id']}: http={status} json={parsed is not None} "
                f"retrieved={','.join(retrieved_ids)} elapsed={elapsed}s",
                flush=True,
            )
            draft = ""
            if isinstance(parsed, dict):
                draft = parsed.get("customer_reply_draft") or ""
            conversation.append({"speaker": "customer", "text": turn["customer_input"]})
            conversation.append({"speaker": "assistant", "text": draft or str(body.get("output", ""))[:1500]})
        summary["cases"].append(case_record)

    summary["all_http_200_success"] = all(
        turn["http_status"] == 200 for case in summary["cases"] for turn in case["turns"]
    )
    summary["all_json_parsed"] = all(
        turn["json_parsed"] for case in summary["cases"] for turn in case["turns"]
    )
    (evidence_dir / "direct_test_runs_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: summary[k] for k in ("run_tag", "all_http_200_success", "all_json_parsed")}, indent=2))


if __name__ == "__main__":
    main()
