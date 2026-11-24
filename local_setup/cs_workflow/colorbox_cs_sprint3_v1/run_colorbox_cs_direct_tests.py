import json
import csv
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENDPOINT = "http://127.0.0.1:8080/api/v1/agent/execute"
KNOWLEDGE_PATH = HERE / "COLORBOX_CS_Knowledge_v1.json"
INSTRUCTIONS_PATH = HERE / "COLORBOX_CS_Instructions_v1_2.md"
SOURCE_REGISTER_PATH = HERE / "COLORBOX_CS_Source_Register_v1.csv"
FIXTURE_PATH = HERE / "COLORBOX_CS_Dummy_Scenarios_v1.json"
CORPUS_PATH = HERE / "COLORBOX_CS_Test_Corpus_v1.json"


def load_json(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def load_sources():
    with SOURCE_REGISTER_PATH.open(encoding="utf-8-sig", newline="") as source:
        return {row["source_id"]: row for row in csv.DictReader(source)}


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
            body = {"error": "HTTP error; response body was not JSON"}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        status = 0
        body = {"error": f"{type(error).__name__}: {error}"}
    return status, body, round(time.monotonic() - started, 2)


def build_prompt(test, instructions, records, fixtures, sources, run_date):
    knowledge = [records[record_id] for record_id in test["knowledge_ids"]]
    source_ids = {
        source_id
        for record in knowledge
        for source_id in record.get("source_ids", [])
    }
    source_rows = [sources[source_id] for source_id in sorted(source_ids) if source_id in sources]
    simulation = [
        item
        for collection in (
            fixtures.get("simulated_orders", []),
            fixtures.get("simulated_returns", []),
            fixtures.get("simulated_policies", []),
            fixtures.get("explicit_unknowns", []),
        )
        for item in collection
        if item.get("scenario_id") in test.get("simulation_ids", [])
    ]
    return (
        "STANDAR OPERASIONAL PROSEDUR — Colorbox CS test v1\n"
        "This is an isolated test of CS requirements, not a real customer case. "
        "Treat the provided records as the only evidence. Do not claim a live lookup. "
        "Return valid JSON only, matching the required output shape in the instructions.\n\n"
        f"Test date: {run_date}\n\n"
        "[CS INSTRUCTIONS]\n"
        f"{instructions}\n\n"
        "[SELECTED APPROVED KNOWLEDGE RECORDS]\n"
        f"{json.dumps(knowledge, ensure_ascii=False, indent=2)}\n\n"
        "[SOURCE REGISTER — cite exact URLs and accessed dates]\n"
        f"{json.dumps(source_rows, ensure_ascii=False, indent=2)}\n\n"
        "[SIMULATION FIXTURES — FABRICATED; NOT LIVE DATA]\n"
        f"{json.dumps(simulation, ensure_ascii=False, indent=2)}\n\n"
        "[SAME-CONVERSATION HISTORY]\n"
        f"{json.dumps(test.get('conversation', []), ensure_ascii=False, indent=2)}\n\n"
        "[CURRENT CUSTOMER INPUT]\n"
        f"{test['customer_input']}\n\n"
        "[END OF CUSTOMER INPUT]"
    )


def main():
    knowledge_doc = load_json(KNOWLEDGE_PATH)
    fixtures = load_json(FIXTURE_PATH)
    corpus = load_json(CORPUS_PATH)
    sources = load_sources()
    instructions = INSTRUCTIONS_PATH.read_text(encoding="utf-8")
    run_tag = os.environ.get("COLORBOX_CS_RUN_TAG", "run_20261107_v1_2")
    evidence_dir = HERE / "evidence" / run_tag
    requested_ids = {
        test_id.strip()
        for test_id in os.environ.get("COLORBOX_CS_TEST_IDS", "").split(",")
        if test_id.strip()
    }
    tests = corpus["tests"]
    if requested_ids:
        tests = [test for test in tests if test["test_id"] in requested_ids]
        found_ids = {test["test_id"] for test in tests}
        missing_ids = requested_ids - found_ids
        if missing_ids:
            raise ValueError(f"Unknown test ID(s): {', '.join(sorted(missing_ids))}")
    if not tests:
        raise ValueError("No direct test cases selected")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    records = {record["id"]: record for record in knowledge_doc["records"]}
    run_date = datetime.now(timezone.utc).astimezone().date().isoformat()
    summary = {
        "package": "Colorbox CS Sprint 3",
        "test_corpus_version": corpus["corpus_version"],
        "instruction_version": "1.2",
        "knowledge_version": knowledge_doc["knowledge_version"],
        "run_date": run_date,
        "endpoint": ENDPOINT,
        "execution_mode": "direct shared-backend API request; no UI",
        "retrieval_mode": "manual test-case selection and prompt injection; no retrieval engine",
        "expected_fixtures_are_model_output": False,
        "cases": [],
    }

    for test in tests:
        prompt = build_prompt(test, instructions, records, fixtures, sources, run_date)
        payload = {
            "customer_id": f"colorbox_test_{test['test_id']}",
            "department": "customer_support",
            "prompt": prompt,
            "agent_mode": "single",
            "multi_agent": False,
            "provider": "opencode-go",
            "model": "deepseek-v4.1-flash",
            "timeout_seconds": 300,
        }
        request_record = {
            "test_id": test["test_id"],
            "coverage": test["coverage"],
            "expected": test["expected"],
            "retrieval_mode": summary["retrieval_mode"],
            "payload": payload,
        }
        (evidence_dir / f"{test['test_id']}_request.json").write_text(
            json.dumps(request_record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        status, body, elapsed = call_backend(payload)
        response_record = {
            "test_id": test["test_id"],
            "http_status": status,
            "elapsed_seconds": elapsed,
            "body": body,
        }
        (evidence_dir / f"{test['test_id']}_response.json").write_text(
            json.dumps(response_record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        executed = body.get("executed") or {}
        case_summary = {
            "test_id": test["test_id"],
            "coverage": test["coverage"],
            "http_status": status,
            "status": body.get("status", "transport_error" if status == 0 else "unknown"),
            "provider": executed.get("provider", body.get("provider")),
            "model": executed.get("model", body.get("model")),
            "fallback_applied": executed.get("fallback_applied", body.get("fallback_applied")),
            "elapsed_seconds": elapsed,
            "output_present": bool(body.get("output")),
            "error": body.get("error"),
        }
        summary["cases"].append(case_summary)
        print(
            f"{test['test_id']}: http={status} status={case_summary['status']} "
            f"provider={case_summary['provider']} model={case_summary['model']} "
            f"fallback={case_summary['fallback_applied']} elapsed={elapsed}s",
            flush=True,
        )

    summary["all_http_200_success"] = all(
        case["http_status"] == 200 and case["status"] == "success"
        for case in summary["cases"]
    )
    (evidence_dir / "direct_test_runs_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
