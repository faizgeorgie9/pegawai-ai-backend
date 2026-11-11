"""Knowledge bundles per team and the per-run instruction builder (decision: the BFF retrieves before the run).
Files under bff/knowledge are owned by Ivana and Mansi and are read as they are, never edited."""
import csv
import hashlib
import json
import re
from pathlib import Path

from .errors import ApiError

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
COLORBOX_DIR = KNOWLEDGE_DIR / "colorbox"
CS_DIR = KNOWLEDGE_DIR / "cs-v2.1"

INSTRUCTIONS_VERSION = "cs-2.1"
CS_INSTRUCTIONS = CS_DIR / "COLORBOX_CS_Instructions_v2_1.md"
CS_KNOWLEDGE = CS_DIR / "COLORBOX_CS_Knowledge_v2.json"
CS_REGISTER = CS_DIR / "COLORBOX_CS_Source_Register_v1.csv"
CS_FIXTURES = CS_DIR / "COLORBOX_CS_Dummy_Scenarios_v2.json"

# Marketing bundle: file -> Hub source ids (from the "Cakupan Penggunaan Dokumen" column of colorbox/source-register.md).
MARKETING_FILES = {"brand-profile.md": ["SRC-01"], "brand-guidelines.md": ["SRC-01", "SRC-07"],
                   "content-pillars.md": ["SRC-06", "SRC-07"], "content-research.md": ["SRC-06", "SRC-08"]}
# Hub CS files: never injected into CS runs (spec decision 2); listed so a test can assert that.
HUB_CS_ONLY = ("business-policies.md", "product-size-reference.md", "customer-faq.md", "customer-inquiry-patterns.md")
HUB_ACCESSED = "2026-11-09"
SIM_CLASS = "Dummy / Simulated Data"

TEAM_WORKFLOW = {"marketing": "marketing", "customer_support": "cs"}
PRODUCT_NOTE = ("Data katalog publik (Colorbox Collection, SRC-02 Hub) yang diamati 9 November 2026. Harga dan pilihan "
                "bisa berubah dan stok TIDAK diketahui. Jangan menjanjikan ketersediaan. Jika bertentangan dengan "
                "catatan pengetahuan, sebutkan konflik itu dan rekomendasikan tinjauan manusia.")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hub_sources() -> dict[str, dict]:
    """Rows of the Hub source inventory table: code -> {url, classification}."""
    out = {}
    for line in (COLORBOX_DIR / "source-register.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*\*\*(SRC-\d+)\*\*\s*\|(.+)\|\s*$", line)
        if m:
            cells = [c.strip() for c in m.group(2).split("|")]
            link = re.search(r"\]\((https?://[^)\s]+)\)", cells[1])
            out[m.group(1)] = {"url": link.group(1) if link else None, "classification": cells[2]}
    return out


def cs_register() -> dict[str, dict]:
    with CS_REGISTER.open(encoding="utf-8", newline="") as f:
        return {r["source_id"]: r for r in csv.DictReader(f)}


def cs_knowledge() -> dict:
    return json.loads(CS_KNOWLEDGE.read_text(encoding="utf-8"))


def knowledge_version() -> str:
    return str(cs_knowledge()["knowledge_version"])


def marketing_hashes() -> dict[str, str]:
    """First 12 hex chars of each Marketing file's sha256, for the audit trail."""
    return {n: _sha((COLORBOX_DIR / n).read_bytes())[:12] for n in MARKETING_FILES}


def marketing_bundle() -> list[dict]:
    src = hub_sources()
    out = []
    for name, ids in MARKETING_FILES.items():
        text = (COLORBOX_DIR / name).read_text(encoding="utf-8")
        title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), name)
        first = src.get(ids[0], {})
        out.append({"id": name, "title": title, "text": text, "classification": first.get("classification"),
                    "source_id": ids[0], "url": first.get("url"), "accessed_date": HUB_ACCESSED})
    return out


def cs_bundle() -> dict:
    """instructions v2.1 + the knowledge records + the source register (the only CS-authorized evidence)."""
    k, reg = cs_knowledge(), cs_register()
    refs = []
    for r in k["records"]:
        sid = (r.get("source_ids") or [None])[0]
        row = reg.get(sid, {}) if sid else {}
        refs.append({"id": r["id"], "title": r["kind"], "classification": r["status"], "source_id": sid,
                     "url": row.get("url"), "accessed_date": row.get("accessed_date")})
    return {"instructions": CS_INSTRUCTIONS.read_text(encoding="utf-8"), "records": k["records"], "register": reg,
            "register_csv": CS_REGISTER.read_text(encoding="utf-8"), "refs": refs,
            "knowledge_version": str(k["knowledge_version"])}


def bundle_for_team(team: str) -> dict:
    """The bundle a bot's team gets. A team without a bundle (custom teams) gets none."""
    wf = TEAM_WORKFLOW.get(team)
    if wf == "marketing":
        return {"workflow": "marketing", "files": marketing_bundle()}
    if wf == "cs":
        return {"workflow": "cs", **cs_bundle()}
    return {}


def fixtures() -> list[dict]:
    """SIM-* scenarios flattened: [{scenario_id, kind, data}]."""
    d = json.loads(CS_FIXTURES.read_text(encoding="utf-8"))
    return [{"scenario_id": s["scenario_id"], "kind": kind, "data": s}
            for kind, items in d.items() if isinstance(items, list) for s in items if "scenario_id" in s]


def _rp(n: int) -> str:
    return "Rp " + f"{n:,}".replace(",", ".")


def _product_lines(products: list[dict]) -> str:
    out = []
    for p in products:
        price = _rp(p["price"]) + (f" (sebelumnya {_rp(p['price_original'])})" if p["price_original"] else "")
        out.append(f"- {p['name']} | {p['category']} | {price} | warna: {', '.join(p['colors'])} | "
                   f"ukuran: {', '.join(p['sizes'])} | {p['url']} | diamati {p['accessed_date']}")
    return "\n".join(out)


def build_context(team: str, workflow: str, base: str | None, products: list[dict],
                  test_mode: bool = False) -> tuple[str, list[dict], dict]:
    """(instructions, context_refs, meta) for a run with `workflow`. `base` is the client's own instruction (marketing only)."""
    if TEAM_WORKFLOW.get(team) != workflow:
        raise ApiError(400, "Workflow tidak cocok dengan tim bot ini")
    b = bundle_for_team(team)
    refs: list[dict] = []
    meta = {"workflow": workflow}
    fence = "`" * 3
    if workflow == "cs":
        parts = [b["instructions"].strip(),
                 "# DATA PENGETAHUAN YANG DIIZINKAN UNTUK PERMINTAAN INI\n\n## Knowledge records (JSON)\n"
                 + fence + "json\n" + json.dumps(b["records"], ensure_ascii=False, indent=1) + "\n" + fence
                 + "\n\n## Source register (CSV)\n" + fence + "csv\n" + b["register_csv"].strip() + "\n" + fence]
        refs += b["refs"]
        meta.update(instructions_version=INSTRUCTIONS_VERSION, knowledge_version=b["knowledge_version"])
    else:
        parts = [base.strip()] if base and base.strip() else []
        parts.append("# KONTEKS BISNIS COLORBOX (pengetahuan resmi untuk permintaan ini)\n\n"
                     + "\n\n".join(f"## {f['id']} ({f['classification']})\n{f['text'].strip()}" for f in b["files"]))
        refs += [{k: v for k, v in f.items() if k != "text"} for f in b["files"]]
        meta.update(knowledge_files=marketing_hashes())
    if products:
        parts.append(f"# DATA PRODUK (maksimal 5, hasil pencarian katalog)\n{PRODUCT_NOTE}\n{_product_lines(products)}")
    refs = [{"type": "knowledge", **r} for r in refs]
    refs += [{"type": "product", "id": str(p["id"]), "title": p["name"], "classification": "Public Data",
              "source_id": p["source"], "url": p["url"], "accessed_date": p["accessed_date"]} for p in products]
    if workflow == "cs" and test_mode:
        fx = fixtures()
        parts.append("# SIMULASI (mode uji): FIXTURE FIKTIF, BUKAN DATA COLORBOX\nSemua SIM-* di bawah ini fiktif. Isi "
                     "simulation.is_simulated=true dan scenario_ids. Jangan menyebutnya hasil pencarian sistem Colorbox.\n"
                     + fence + "json\n" + json.dumps([f["data"] for f in fx], ensure_ascii=False, indent=1) + "\n" + fence)
        refs += [{"type": "fixture", "id": f["scenario_id"], "title": f["kind"], "classification": SIM_CLASS,
                  "source_id": None, "url": None, "accessed_date": None} for f in fx]
    return "\n\n".join(p for p in parts if p), refs, meta


def prompt_hash(instructions: str | None, input_: str) -> str:
    return _sha(((instructions or "") + "\n" + input_).encode("utf-8"))
