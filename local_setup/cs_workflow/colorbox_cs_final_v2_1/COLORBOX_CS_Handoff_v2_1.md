# Colorbox CS Handoff v2.1

**Date:** 2026-11-09  
**Status:** Ready for facilitator-led demo and Engineering/CS review; not ready for customer pilot. No external handoff, ticket, or approval has been completed.  
**Package owner:** CS validation workstream

## 1. What is being handed off

A tested Colorbox CS instruction/knowledge package for a controlled pilot, plus actual backend and UI evidence.

- Instructions: `COLORBOX_CS_Instructions_v2_1.md`
- Knowledge: `COLORBOX_CS_Knowledge_v2.json` (11 records)
- Sources: `COLORBOX_CS_Source_Register_v1.csv`
- Fixtures: `COLORBOX_CS_Dummy_Scenarios_v2.json`
- Corpus: `COLORBOX_CS_Test_Corpus_v2.json`
- Runner: `run_colorbox_cs_v2_tests.py`
- Evaluator: `evaluate_colorbox_cs_v2.py`
- Results: `COLORBOX_CS_Test_Results_v2_1.csv`
- Report: `COLORBOX_CS_Validation_Report_v2_1.md`
- Issues: `COLORBOX_CS_Issue_Log_v2_1.md`
- Before/after: `COLORBOX_CS_Before_After_v2_1.md`
- Retests: `COLORBOX_CS_Critical_Retest_v2_1.md`
- Frontend feedback: `COLORBOX_CS_Frontend_Feedback_v2_1.md`
- Demo conversations and expected/actual records: `COLORBOX_CS_Demo_Scenarios_v2_1.md`
- Business readiness decision: `COLORBOX_CS_Business_Readiness_v2_1.md` (demo-ready only; complete workflow not ready; CS sign-off pending)
- Evidence folders: `evidence/run_20261109_v2_1`, `evidence/run_20261109_v2_1_retest_v03`, `evidence/run_20261109_v2_0_before`, `evidence/ui_20261109_v06`
- Final UI demo evidence: `evidence/ui_demos_20261109` (three actual submissions, prompts, result JSON, screenshots)

## 2. Backend work required

### B-01 retrieval engine

Implement the production retrieval path over approved knowledge. The current tests inject candidates from a keyword/IDF shim; they do not prove retrieval quality.

Acceptance:

- Given the 9-turn corpus, returns all required knowledge IDs and no unapproved record.
- Unknown-policy cases retrieve the `unknown_*` record for limitation language.
- Returns stable ordering with scores and a trace for audit.
- Does not retrieve the unrelated PT AI Top Trends FAQ or SOP.

### B-08/N-01/N-09 JSON contract

Return strict JSON matching the schema. Reject or repair invalid output before it reaches the client; do not rely on the evaluator's control-character repair.

Acceptance:

- 10/10 repeated runs parse with `json.loads` without repair.
- Missing required keys, invalid enums, null URL/date when a register row exists, and `handoff_status != recommendation_only` are rejected with a clear error.
- No unescaped newlines inside string values.

### Provider and SOP isolation

- Resolve the active provider server-side; do not trust a hardcoded client `provider`.
- Suppress the shared department SOP when the request carries the exact `STANDAR OPERASIONAL PROSEDUR` marker, or better, select the correct SOP by tenant/department.
- Keep an audit record of which SOP and instruction version was used.

### Persistence/audit

- Store run id, timestamp, provider, model, prompt hash, instruction/knowledge version, latency, token count, raw response, and validation result.
- Do not store secrets or unnecessary personal data.

## 3. CS work required

1. Approve the P0-P3 rules as test rules, not Colorbox SLAs.
2. Approve or reject the Indonesia market assumption.
3. Approve the source register and resolve gaps:
   - FAQ answer text (B-02)
   - product detail HTTP 429 and size chart transcription (B-03)
   - shipping fee/ETA/Click & Collect terms (B-04)
   - refund processing time/method (B-05)
4. Confirm the account-deletion process is genuinely unknown in public sources, or supply an approved source.
5. Confirm the size-exchange policy is genuinely unverified, or supply an approved source.
6. Define the human-review queue and owner for P1/P0 cases.
7. Sign off the customer-draft tone and the "internal draft only" rule.

## 4. Frontend work required

See `COLORBOX_CS_Frontend_Feedback_v2_1.md`. Minimum pilot fixes:

- Remove the wrong-brand `PT AI TOP TRENDS` / `SOP-CS-AITT` / `<15 detik` display.
- Use the active provider from health/config.
- Add a persistent conversation/thread or clearly support embedded history.
- Raise/configure the 180 s timeout and show progress.
- Validate JSON/schema and show a clear error state.
- Surface priority, escalation, human-review, simulation, and source count.

## 5. Acceptance criteria for pilot

- 9/9 corpus turns HTTP 200 and strict-valid JSON on two consecutive runs.
- 144/144 rubric, with no critical safety/grounding failure.
- Retrieval trace shows only approved Colorbox records.
- UI run shows Colorbox branding/SOP, no wrong SLA, and a clean customer draft.
- CS signs off all open blockers or explicitly accepts them for a supervised pilot.
- Run id and evidence are stored for every request.

## 6. Known limitations to disclose

- Retrieval is a test-harness shim, not a production engine.
- No live order, carrier, inventory, CRM, payment, or account access.
- No customer reply is sent; every output is an internal draft.
- Escalation output is a recommendation only; no live queue, ticket, owner, or assignment exists.
- Source coverage is incomplete; unknown policies remain unknown.
- One strict-JSON formatting failure occurred on first pass and passed on retest; this is not a closed defect.
- UI multi-agent, P0, and >3-turn conversations were not tested.

## 7. Next actions

1. Backend: implement B-01 and the JSON/schema gate; return a run id and validation result.
2. Frontend: fix F-01/F-02/F-04; then F-03/F-08.
3. Operations: define and implement human-review routing, queue, owner, and audit for escalation.
4. CS: approve rules/sources and close B-02 to B-07.
5. Validation: rerun the full corpus twice on the implemented retrieval path; add a P0 case and a 5-turn case.
6. Package: use the demo records and UI screenshots for the facilitator-led review; the ZIP is for local/shared-drive handoff because chat rejects ZIP attachments.
