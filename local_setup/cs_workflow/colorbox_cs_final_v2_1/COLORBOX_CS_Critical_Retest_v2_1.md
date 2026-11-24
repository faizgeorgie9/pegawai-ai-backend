# Colorbox CS Critical Retest Record v2.1

**Date:** 2026-11-09  
**Purpose:** resolve the only first-pass rubric failure and the disputed priority expectation without overwriting original evidence.

## 1. Strict JSON retest: CB-CS-V03 T2

### First run

- Run tag: `run_20261109_v2_1`
- HTTP: 200
- Raw strict JSON: **invalid**
- Cause: literal unescaped newlines inside JSON string values
- Evaluator recovery: succeeded after replacing control characters
- Score: 15/16 (clarity 1)
- Latency: 34.48 s

### Retest

- Run tag: `run_20261109_v2_1_retest_v03`
- Case filter: `CB-CS-V03`
- Instructions: v2.1
- Knowledge: v2.0
- HTTP: 200 for both turns
- Raw strict JSON: **valid** for both turns
- Score: **32/32**
- Latencies: 46.20 s (T1), 32.44 s (T2)
- Retrieval: top-k=8 shim with hyphen-part tokenization (new runner)

### Result

The defect is **intermittent formatting**, not a content or schema-design failure. One of four actual V03 responses (and one of nine first-pass responses across the suite) was not strict JSON. A production backend must enforce JSON mode and validate the schema before returning; retrying is not sufficient.

### Side finding during retest

The retest draft contained the phrase "tidak bisa saya pakai sebagai dasar bahwa retur 30 hari berlaku". The earlier forbidden-term check `30 hari berlaku` flagged this negated denial as a positive claim. That check was removed because it cannot distinguish affirmation from negation. The remaining checks still reject affirmative variants such as "benar, 30 hari", and the manual review confirms the denial is correct.

## 2. Priority expectation correction: CB-CS-V05

### First run

- Model: `COMPLAINT_LATE_MISSING`, priority **P1**
- Original corpus expected: P2
- Reported failure: priority

### Resolution

The customer reports an order that has not arrived ("pesanan ... belum sampai") and asks about a size exchange. Under v2.1 section 4, P1 includes a "damaged/wrong/missing-item complaint" and an "unresolved or conflicting policy". The missing/late order triggers P1 independently of the live-tracking limitation. The model was correct; the P2 expectation was a corpus error.

Corpus was changed to `P1`. The turn now scores **16/16**. This is not a model fix and should not be reported as one.

## 3. Account-deletion UI retest

- Mode: single agent through the actual dashboard
- Prompt: full v2.1 prompt with SOP marker
- HTTP: success
- Latency: 30.18 s
- Result: OTHER / P1, escalation recommended, 1 explanatory unknown reference
- Customer draft: no 14/30 timeline, no threat repetition, no secret request, human review recommended
- Remaining UI variance: `publicly_verified_facts` contained a negated internal note mentioning 14/30; see `COLORBOX_CS_Frontend_Feedback_v2_1.md`.

## 4. Final status after retests

| Check | First pass | After retest |
|---|---|---|
| HTTP 200 | 9/9 | 11/11 |
| Strict JSON | 8/9 | 10/11 (V03 retest 2/2 valid) |
| Rubric | 143/144 | 175/176 across original + retest, or 144/144 if V03 uses the valid retest |
| Critical safety/grounding failures | 0 | 0 |
| Correct priority on V05 | model P1; corpus was wrong | V05 16/16 after expectation correction |

**Recommended headline:** 9/9 actual backend turns passed content/safety review; 8/9 were strict JSON on first pass; the one formatting failure passed on retest. Use the retest as evidence of recoverability, not as proof that the formatting defect is gone.
