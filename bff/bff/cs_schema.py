"""Pydantic model of the Colorbox CS v2.1 structured output (instructions section 11, invariants in sections 4 and 12).
Hermes /v1/runs has no JSON mode (checked in gateway/platforms/api_server_runs.py and api_server.py), so the BFF
extracts the JSON from the answer, validates it here and retries once."""
import json
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

Intent = Literal["PRODUCT_INFO", "PRODUCT_AVAILABILITY", "SIZE_FIT", "SHIPPING_DELIVERY", "CLICK_COLLECT", "ORDER_PROCESS",
                 "ORDER_STATUS", "COMPLAINT_DAMAGED", "COMPLAINT_WRONG_ITEM", "COMPLAINT_LATE_MISSING", "RETURN_REFUND",
                 "PAYMENT", "WEBSITE_TECHNICAL", "OTHER", "AMBIGUOUS"]


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
    """The JSON object of an answer: the whole text, a fenced block, or the outermost {...}. ValueError when none parses."""
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


def validate_cs(text: str) -> tuple[dict | None, dict]:
    """(structured object or None, validation) where validation = {status: valid|invalid, errors: [...]}."""
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
