import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO_DIR = HERE / "evidence" / "ui_demos_20261109"


def parse_result(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    text = data["result_text"]
    start = text.find("{")
    end = text.rfind("}")
    parsed = json.loads(text[start : end + 1])
    return data, parsed


for path in sorted(DEMO_DIR.glob("DEMO-*_result.json")):
    data, parsed = parse_result(path)
    print("=" * 80)
    print(f"{data['demo_id']}  latency={data['latency']}  tokens={data['tokens']}  provider={data['provider']}")
    print(f"primary={parsed['primary_intent']} secondary={parsed['secondary_intents']} priority={parsed['priority']}")
    print(f"escalation={parsed['escalation']}")
    print(f"clarifying={parsed['clarifying_question']}")
    print(f"simulation={parsed['simulation']}")
    print(f"knowledge={[(k.get('knowledge_id'), k.get('source_url'), k.get('accessed_date')) for k in parsed.get('knowledge_refs', [])]}")
    print(f"summary_issue={parsed['ticket_summary'].get('issue')}")
    print(f"summary_verified={parsed['ticket_summary'].get('publicly_verified_facts')}")
    print(f"summary_unknowns={parsed['ticket_summary'].get('unknowns')}")
    print("DRAFT:")
    print(parsed["customer_reply_draft"])
