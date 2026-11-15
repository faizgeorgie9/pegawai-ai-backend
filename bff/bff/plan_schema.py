"""The multi-day content plan a group's project manager ends a message with: one fenced JSON block (instructions in
groups._instructions). Parsed and validated here; anything invalid is not a plan and the message stays plain text."""
import json
import re
from datetime import date

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

MAX_DAYS = 14
_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class PlanDay(BaseModel):
    date: date
    theme: str = Field(min_length=1, max_length=120)
    products: list[str] = Field(default=[], max_length=10)
    brief: str = Field(min_length=1, max_length=2000)
    time: str = "09:00"

    @field_validator("theme", "brief")
    @classmethod
    def _text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("tidak boleh kosong")
        return v

    @field_validator("products")
    @classmethod
    def _products(cls, v: list[str]) -> list[str]:
        if any(not isinstance(p, str) or not 1 <= len(p.strip()) <= 120 for p in v):
            raise ValueError("produk harus berupa teks (maksimal 120 karakter)")
        return [p.strip() for p in v]

    @field_validator("time")
    @classmethod
    def _time(cls, v: str) -> str:
        if not _HHMM.match(v):
            raise ValueError("jam harus berformat HH:MM")
        return v


class Plan(BaseModel):
    title: str = Field(default="Rencana konten", max_length=120)
    days: list[PlanDay] = Field(min_length=1, max_length=MAX_DAYS)

    @model_validator(mode="after")
    def _days(self):
        dates = [d.date for d in self.days]
        if len(set(dates)) != len(dates):
            raise ValueError("tanggal tidak boleh dobel")
        if dates != sorted(dates):
            raise ValueError("tanggal harus berurutan")
        return self


def extract(text: str) -> dict | None:
    """The last fenced JSON block of `text` as {"plan": {...}}'s inner object, or None."""
    for block in reversed(_FENCE.findall(text or "")):
        try:
            d = json.loads(block)
        except ValueError:
            continue
        if isinstance(d, dict) and isinstance(d.get("plan"), dict):
            return d["plan"]
    return None


def parse(text: str) -> tuple[dict | None, list[str]]:
    """(plan as plain dict with ISO dates, errors). (None, []) when the text has no plan block; (None, errors) when invalid."""
    raw = extract(text)
    if raw is None:
        return None, []
    try:
        p = Plan.model_validate(raw)
    except ValidationError as e:
        return None, [f"{'.'.join(str(x) for x in err['loc']) or 'root'}: {err['msg']}" for err in e.errors()]
    return p.model_dump(mode="json"), []


def strip(text: str) -> str:
    """The message without its plan block (what a reader sees above the card)."""
    return _FENCE.sub("", text or "").strip()
