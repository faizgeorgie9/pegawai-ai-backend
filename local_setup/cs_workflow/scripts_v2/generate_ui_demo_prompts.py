import json
from pathlib import Path

import run_colorbox_cs_v2_tests as r

HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence" / "ui_demos_20261109"
OUT.mkdir(parents=True, exist_ok=True)


def load_run_response(case_id, turn_id):
    path = HERE / "evidence" / "run_20261109_v2_1" / f"{case_id}_{turn_id}_response.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["parsed_output"]["customer_reply_draft"]


def main():
    instructions = r.INSTRUCTIONS_PATH.read_text(encoding="utf-8")
    knowledge = r.load_json(r.KNOWLEDGE_PATH)
    sources = r.load_sources()
    fixtures = r.load_json(r.FIXTURE_PATH)
    corpus = r.load_json(r.CORPUS_PATH)
    records = knowledge["records"]
    run_date = "2026-11-09"

    cases = {case["test_id"]: case for case in corpus["cases"]}

    demos = [
        {
            "demo_id": "DEMO-A",
            "label": "Normal grounded inquiry: price, stock and fit",
            "test_id": "CB-CS-V01",
            "turn_id": "T1",
            "history": [],
        },
        {
            "demo_id": "DEMO-B",
            "label": "Contextual complaint: damaged item, refund, then corrected item",
            "test_id": "CB-CS-V02",
            "turn_id": "T3",
            "history": [
                {"speaker": "customer", "text": cases["CB-CS-V02"]["turns"][0]["customer_input"]},
                {"speaker": "assistant", "text": load_run_response("CB-CS-V02", "T1")},
                {"speaker": "customer", "text": cases["CB-CS-V02"]["turns"][1]["customer_input"]},
                {"speaker": "assistant", "text": load_run_response("CB-CS-V02", "T2")},
            ],
        },
        {
            "demo_id": "DEMO-C",
            "label": "Simulated order/refund plus fictional 30-day policy conflict",
            "test_id": "CB-CS-V03",
            "turn_id": "T2",
            "history": [
                {"speaker": "customer", "text": cases["CB-CS-V03"]["turns"][0]["customer_input"]},
                {"speaker": "assistant", "text": load_run_response("CB-CS-V03", "T1")},
            ],
        },
    ]

    manifest = []
    for demo in demos:
        case = cases[demo["test_id"]]
        turn = next(item for item in case["turns"] if item["turn_id"] == demo["turn_id"])
        retrieved = r.retrieve(turn["customer_input"], records)
        simulation = r.select_fixtures(fixtures, turn.get("simulation_ids", []))
        prompt = r.build_prompt(
            instructions,
            retrieved,
            sources,
            simulation,
            demo["history"],
            turn["customer_input"],
            run_date,
        )
        prompt_path = OUT / f"{demo['demo_id']}_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        manifest.append(
            {
                "demo_id": demo["demo_id"],
                "label": demo["label"],
                "test_id": demo["test_id"],
                "turn_id": demo["turn_id"],
                "customer_input": turn["customer_input"],
                "history": demo["history"],
                "simulation_ids": turn.get("simulation_ids", []),
                "retrieved_ids": [record["id"] for _, record in retrieved],
                "expected": turn["expected"],
                "prompt_file": str(prompt_path),
                "prompt_chars": len(prompt),
            }
        )
        print(f"{demo['demo_id']} {demo['test_id']} {demo['turn_id']}: {len(prompt)} chars, "
              f"fixtures={len(simulation)} retrieved={[record['id'] for _, record in retrieved]}")

    (OUT / "demo_manifest_expected.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
