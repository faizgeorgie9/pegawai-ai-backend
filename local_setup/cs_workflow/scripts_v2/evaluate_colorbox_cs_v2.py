import csv
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUN_TAG = "run_20261109_v2_1"
BEFORE_TAG = "run_20261109_v2_0_before"
KNOWLEDGE_PATH = HERE / "COLORBOX_CS_Knowledge_v2.json"
SOURCE_REGISTER_PATH = HERE / "COLORBOX_CS_Source_Register_v1.csv"
SCHEMA_KEYS = [
    "primary_intent",
    "secondary_intents",
    "classification_confidence",
    "priority",
    "customer_reply_draft",
    "ticket_summary",
    "knowledge_refs",
    "clarifying_question",
    "escalation",
    "human_review_required",
    "simulation",
]
INTERNAL_LABEL_PATTERN = re.compile(
    r"\b(draft|internal|sop|handoff|recommendation|eskalasi|escalation|knowledge_ref|"
    r"standar operasional prosedur)\b",
    re.IGNORECASE,
)


def repair_json_control_chars(text):
    """Escape literal control characters that appear inside JSON strings."""
    output = []
    in_string = False
    escaped = False
    for char in text:
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
    return "".join(output)


def recover_json(raw_text):
    if not isinstance(raw_text, str):
        return None
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\\s*", "", cleaned)
        cleaned = re.sub(r"\\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        return None
    candidate = cleaned[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        try:
            return json.loads(repair_json_control_chars(candidate))
        except json.JSONDecodeError:
            return None


def load_json(path):
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_sources():
    with SOURCE_REGISTER_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return {row["source_id"]: row for row in csv.DictReader(handle)}


def contains_any(text, alternatives):
    lowered = text.casefold()
    return any(str(alt).casefold() in lowered for alt in alternatives)


def all_groups_present(text, groups):
    missing = []
    for group in groups:
        if not contains_any(text, group):
            missing.append(" | ".join(group))
    return not missing, missing


def any_term_present(text, groups):
    flat = [term for group in groups for term in group]
    return contains_any(text, flat)


def ref_valid(ref, records, sources):
    knowledge_id = ref.get("knowledge_id")
    record = records.get(knowledge_id)
    if record is None:
        return False, f"unknown knowledge_id {knowledge_id}"
    url = ref.get("source_url") or ref.get("url") or ""
    accessed = ref.get("accessed_date") or ref.get("accessed") or ""
    source_ids = record.get("source_ids", [])
    if not source_ids:
        if url:
            return False, f"{knowledge_id} has no public source but a URL was cited"
        return True, "no-source record cited without URL"
    allowed = [
        sources[source_id]
        for source_id in source_ids
        if source_id in sources
    ]
    if not url:
        return False, f"{knowledge_id} requires a source URL"
    for source in allowed:
        if url.strip() == source["url"].strip() and accessed.strip() == source["accessed_date"].strip():
            return True, f"matched {source['source_id']}"
    return False, f"URL/date does not match source register for {knowledge_id}"


def assess_turn(request, response, records, sources):
    expected = request["expected"]
    body = response.get("raw_body") or {}
    parsed = response.get("parsed_output")
    checks = {}
    details = {}

    checks["http_200"] = response.get("http_status") == 200
    checks["valid_json"] = isinstance(parsed, dict)
    if not isinstance(parsed, dict):
        parsed = recover_json(body.get("output"))
        checks["json_recovered"] = isinstance(parsed, dict)
        if not isinstance(parsed, dict):
            return checks, details, None, parsed

    checks["schema_complete"] = all(key in parsed for key in SCHEMA_KEYS)
    draft = str(parsed.get("customer_reply_draft") or "")
    all_text = json.dumps(parsed, ensure_ascii=False)

    primary = str(parsed.get("primary_intent") or "").upper()
    secondary = [str(item).upper() for item in (parsed.get("secondary_intents") or [])]
    checks["primary_intent"] = primary in expected["accepted_primary_intents"]
    checks["secondary_intents"] = all(
        required in secondary for required in expected["required_secondary"]
    )
    checks["priority"] = str(parsed.get("priority") or "").upper() == expected["priority"]

    escalation = parsed.get("escalation") or {}
    checks["escalation_recommended"] = bool(escalation.get("recommended")) == expected[
        "escalation_recommended"
    ]
    checks["escalation_reason"] = any_term_present(
        str(escalation.get("reason") or ""), expected["escalation_reason_terms"]
    )
    checks["human_review"] = bool(parsed.get("human_review_required")) == expected[
        "escalation_recommended"
    ]
    checks["handoff_recommendation_only"] = str(
        escalation.get("handoff_status") or ""
    ) == "recommendation_only"

    refs = parsed.get("knowledge_refs") or []
    ref_results = [ref_valid(ref, records, sources) for ref in refs]
    details["reference_results"] = [message for _, message in ref_results]
    all_refs_valid = all(valid for valid, _ in ref_results)
    if expected["citation_required"]:
        checks["citations"] = bool(refs) and all_refs_valid
    else:
        checks["citations"] = all_refs_valid
    cited_ids = {str(ref.get("knowledge_id")) for ref in refs if ref.get("knowledge_id")}
    expected_ids = expected.get("expected_knowledge_ids", [])
    checks["expected_knowledge_any"] = (not expected_ids) or bool(cited_ids & set(expected_ids))
    details["cited_ids"] = sorted(cited_ids)

    checks["must_include"], missing_groups = all_groups_present(
        draft, expected["must_include_any"]
    )
    details["missing_include_groups"] = missing_groups
    forbidden = [term for term in expected["must_not_include"] if term.casefold() in draft.casefold()]
    timeline_terms = [
        term for term in ["14 hari", "30 hari"] if term in expected["must_not_include"]
    ]
    verified_text = json.dumps(
        (parsed.get("ticket_summary") or {}).get("publicly_verified_facts", []),
        ensure_ascii=False,
    )
    timeline_leaks = [term for term in timeline_terms if term in verified_text.casefold()]
    checks["must_not_include"] = not forbidden and not timeline_leaks
    details["forbidden_found"] = forbidden + [term + " (anywhere)" for term in timeline_leaks]

    simulation = parsed.get("simulation") or {}
    if expected["simulation_required"]:
        checks["simulation_label"] = bool(simulation.get("is_simulated")) and bool(
            simulation.get("scenario_ids")
        )
    else:
        checks["simulation_label"] = not bool(simulation.get("is_simulated"))
    details["scenario_ids"] = simulation.get("scenario_ids")

    question = str(parsed.get("clarifying_question") or "").strip()
    checks["clarifying_question"] = (not expected["clarifying_required"]) or bool(question)

    summary_text = json.dumps(parsed.get("ticket_summary") or {}, ensure_ascii=False)
    checks["summary_terms"], missing_summary = all_groups_present(
        summary_text, expected["summary_terms"]
    )
    details["missing_summary_groups"] = missing_summary

    words = re.findall(r"\b[\w'-]+\b", draft)
    checks["draft_length"] = 15 <= len(words) <= 250
    checks["draft_clean"] = not INTERNAL_LABEL_PATTERN.search(draft)
    checks["draft_polite"] = contains_any(
        draft, ["terima kasih", "mohon", "kami", "halo", "selamat"]
    )
    allowed_uppercase = {"DEMO", "CBX", "SIM", "IDR", "XL", "XXL", "CS", "SOP", "P1", "P2", "P3"}
    shouting = [
        word
        for word in re.findall(r"(?<![\w-])([A-Z]{4,})(?![\w-])", draft)
        if word not in allowed_uppercase
    ]
    checks["no_shouting"] = len(shouting) <= 1
    details["draft_word_count"] = len(words)

    accuracy = 2 if checks["must_include"] and checks["must_not_include"] else (
        1 if checks["must_include"] or checks["must_not_include"] else 0
    )
    relevance_count = sum(
        1
        for group in expected["summary_terms"]
        if contains_any(summary_text, group)
    )
    relevance = 2 if relevance_count == len(expected["summary_terms"]) else (1 if relevance_count else 0)
    grounding = 2 if checks["citations"] and checks["expected_knowledge_any"] else (
        1 if checks["citations"] or checks["expected_knowledge_any"] else 0
    )
    clarity = 2 if checks["draft_length"] and checks["draft_clean"] else (
        1 if checks["draft_length"] or checks["draft_clean"] else 0
    )
    if not checks["valid_json"]:
        clarity = min(clarity, 1)
    tone = 2 if checks["draft_clean"] and checks["draft_polite"] and checks["no_shouting"] else (
        1 if checks["draft_clean"] else 0
    )
    classification = 2 if checks["primary_intent"] and checks["secondary_intents"] else (
        1 if checks["primary_intent"] else 0
    )
    priority = 2 if checks["priority"] else 0
    escalation_score = 2 if (
        checks["escalation_recommended"]
        and checks["escalation_reason"]
        and checks["human_review"]
        and checks["handoff_recommendation_only"]
    ) else (1 if checks["escalation_recommended"] else 0)

    rubric = {
        "accuracy": accuracy,
        "relevance": relevance,
        "grounding": grounding,
        "clarity": clarity,
        "tone": tone,
        "classification": classification,
        "priority": priority,
        "escalation": escalation_score,
    }
    critical_fail = (
        not checks["must_not_include"]
        or not checks["simulation_label"]
        or not checks["citations"]
        or not checks["valid_json"]
    )
    return checks, details, rubric, parsed


def evaluate_run(run_tag):
    evidence_dir = HERE / "evidence" / run_tag
    knowledge = load_json(KNOWLEDGE_PATH)
    records = {record["id"]: record for record in knowledge["records"]}
    sources = load_sources()
    corpus = load_json(HERE / "COLORBOX_CS_Test_Corpus_v2.json")
    expectations = {
        (case["test_id"], turn["turn_id"]): turn["expected"]
        for case in corpus["cases"]
        for turn in case["turns"]
    }
    turns = []
    for request_path in sorted(evidence_dir.glob("*_request.json")):
        request = load_json(request_path)
        response_path = request_path.with_name(
            request_path.name.replace("_request.json", "_response.json")
        )
        if not response_path.exists():
            continue
        response = load_json(response_path)
        expected = expectations.get((request["test_id"], request["turn_id"]), request["expected"])
        request = dict(request, expected=expected)
        checks, details, rubric, parsed = assess_turn(request, response, records, sources)
        turns.append(
            {
                "test_id": request["test_id"],
                "turn_id": request["turn_id"],
                "retrieved_ids": request["retrieval"]["retrieved_ids"],
                "response_elapsed_seconds": response.get("elapsed_seconds"),
                "checks": checks,
                "details": details,
                "rubric": rubric,
                "rubric_total": sum(rubric.values()) if rubric else 0,
                "parsed_output": parsed,
            }
        )
    return turns


def before_case_assessment():
    evidence_dir = HERE / "evidence" / BEFORE_TAG
    response_path = evidence_dir / "CB-CS-V06_T1_response.json"
    if not response_path.exists():
        return None
    response = load_json(response_path)
    parsed = response.get("parsed_output") or {}
    draft = str(parsed.get("customer_reply_draft") or "")
    summary = json.dumps(parsed.get("ticket_summary") or {}, ensure_ascii=False)
    refs = parsed.get("knowledge_refs") or []
    return {
        "response_file": str(response_path),
        "elapsed_seconds": response.get("elapsed_seconds"),
        "http_status": response.get("http_status"),
        "mentions_14_days": "14 hari" in draft.casefold(),
        "mentions_30_days": "30 hari" in draft.casefold(),
        "labels_timeline_publicly_verified": "publicly_verified" in summary.casefold()
        and ("14" in summary or "30" in summary),
        "attributes_timeline_to_instructions": "section 8" in summary.casefold(),
        "no_citable_source": not refs,
        "repeats_legal_threat": contains_any(
            draft, ["pihak berwenang", "media sosial", "melaporkan"]
        ),
        "mislabeled_simulation": bool((parsed.get("simulation") or {}).get("is_simulated")),
        "draft": draft,
        "knowledge_refs": refs,
    }


def write_report(run_tag, turns, before):
    report_path = HERE / "COLORBOX_CS_V2_Evaluation_Report.md"
    total = sum(turn["rubric_total"] for turn in turns)
    maximum = 16 * len(turns)
    critical = [
        turn
        for turn in turns
        if not turn["checks"].get("must_not_include", True)
        or not turn["checks"].get("simulation_label", True)
        or not turn["checks"].get("citations", True)
    ]
    lines = [
        "# Colorbox CS v2.1 â€” Actual-Run Evaluation",
        "",
        f"- Run: `{run_tag}`",
        f"- Turns evaluated: {len(turns)}",
        f"- Aggregate rubric: {total}/{maximum} ({total / maximum * 100:.1f}%)" if maximum else "- No turns",
        f"- Turns with a critical safety/grounding failure: {len(critical)}",
        "- Rubric: 8 dimensions Ã— 0â€“2 per turn (accuracy, relevance, grounding, clarity, tone, classification, priority, escalation).",
        "- Retrieval caveat: candidate records were selected by a documented keyword shim in the CS test harness; the Backend retrieval engine is not implemented (B-01).",
        "",
        "## Per-turn results",
        "",
        "| Case | Turn | HTTP | JSON | Rubric | Accuracy | Grounding | Escalation | Retrieved candidates |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for turn in turns:
        checks = turn["checks"]
        rubric = turn["rubric"] or {}
        lines.append(
            f"| {turn['test_id']} | {turn['turn_id']} | {checks.get('http_200')} | "
            f"{checks.get('valid_json')} | {turn['rubric_total']}/16 | "
            f"{rubric.get('accuracy', 0)} | {rubric.get('grounding', 0)} | "
            f"{rubric.get('escalation', 0)} | {', '.join(turn['retrieved_ids'])} |"
        )
    lines += ["", "## Failed checks", ""]
    any_failure = False
    for turn in turns:
        failures = [name for name, value in turn["checks"].items() if value is False]
        if failures:
            any_failure = True
            lines.append(f"- **{turn['test_id']} {turn['turn_id']}**: {', '.join(failures)}")
            if turn["details"].get("missing_include_groups"):
                lines.append(
                    f"  - Missing required content: {turn['details']['missing_include_groups']}"
                )
            if turn["details"].get("forbidden_found"):
                lines.append(f"  - Forbidden content: {turn['details']['forbidden_found']}")
            if turn["details"].get("missing_summary_groups"):
                lines.append(
                    f"  - Missing summary content: {turn['details']['missing_summary_groups']}"
                )
            bad_refs = [
                message
                for message in turn["details"].get("reference_results", [])
                if not message.startswith("matched") and not message.startswith("no-source")
            ]
            if bad_refs:
                lines.append(f"  - Reference problems: {bad_refs}")
    if not any_failure:
        lines.append("- None.")
    lines += ["", "## Before/after â€” account deletion (V06)", ""]
    if before:
        lines += [
            "The v2.0 run is the before case; the v2.1 run is the after case.",
            "",
            "| Defect | v2.0 before | v2.1 after |",
            "|---|---|---|",
            f"| Repeats 14-working-day timeline | {before['mentions_14_days']} | "
            f"{any('14 hari' in str(t['parsed_output'].get('customer_reply_draft', '')).casefold() for t in turns if t['test_id'] == 'CB-CS-V06')} |",
            f"| Repeats 30-day timeline | {before['mentions_30_days']} | "
            f"{any('30 hari' in str(t['parsed_output'].get('customer_reply_draft', '')).casefold() for t in turns if t['test_id'] == 'CB-CS-V06')} |",
            f"| Labels unsourced timeline as publicly verified | {before['labels_timeline_publicly_verified']} | "
            f"{any(t['checks'].get('must_not_include') is False for t in turns if t['test_id'] == 'CB-CS-V06')} |",
            f"| Repeats legal threat / social-media threat in reply | {before['repeats_legal_threat']} | "
            f"{any(str(t['parsed_output'].get('customer_reply_draft', '')).casefold().find('media sosial') >= 0 for t in turns if t['test_id'] == 'CB-CS-V06')} |",
            f"| Mislabels a non-simulated case as simulated | {before['mislabeled_simulation']} | "
            f"{any((t['parsed_output'].get('simulation') or {}).get('is_simulated') for t in turns if t['test_id'] == 'CB-CS-V06')} |",
            "",
            "v2.0 draft excerpt:",
            "",
            "> " + before["draft"].replace("\n", " ")[:900],
        ]
    else:
        lines.append("- Before-case evidence not found.")
    lines += [
        "",
        "## Interpretation limits",
        "",
        "- Scores test instruction-following and drafting against the supplied knowledge; they do not validate a production retrieval engine, live order data, or live stock.",
        "- Tone and clarity are partly heuristic; the accompanying validation report records the manual review of each draft.",
        "- The test harness injects retrieved candidates; a production system must still implement and evaluate retrieval.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    turns = evaluate_run(RUN_TAG)
    before = before_case_assessment()
    output = {
        "run_tag": RUN_TAG,
        "before_tag": BEFORE_TAG,
        "turns": turns,
        "before_case": before,
    }
    (HERE / "COLORBOX_CS_V2_Evaluation_Details.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_path = write_report(RUN_TAG, turns, before)
    total = sum(turn["rubric_total"] for turn in turns)
    print(f"turns={len(turns)} total={total}/{16 * len(turns)} report={report_path.name}")
    for turn in turns:
        failed = [name for name, value in turn["checks"].items() if value is False]
        print(f"{turn['test_id']} {turn['turn_id']}: {turn['rubric_total']}/16 failed={failed}")


if __name__ == "__main__":
    main()

