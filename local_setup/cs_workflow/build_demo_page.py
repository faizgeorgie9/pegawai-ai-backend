import json, re, html
from pathlib import Path

BASE = Path(r"C:\Users\MI\Documents\pegawai-ai-backend\local_setup\cs_workflow")
EV = BASE / "evidence"
OUT = BASE / "CS_FAQ_Demo_Day3.html"

kb_text = (BASE / "faq_knowledge_base.md").read_text(encoding="utf-8")


def kb_entry(fid):
    m = re.search(rf"^## {fid} â€” ([^\n]+)\n(.*?)(?=\n## |\n---)", kb_text, re.S | re.M)
    if not m:
        return fid, ""
    body = re.sub(r"\n{2,}", "\n", m.group(2).strip())
    return m.group(1).strip(), body


CASES = {
    "Q1": {
        "tab": "Q1 Â· Standard",
        "label": "Standard policy question",
        "verdict_kind": "ok",
        "verdict_title": "Correct â€” grounded in F2 and F8",
        "verdict_body": "Every figure matches the injected entries: Rp1.499.000/month, 5 users, 3.000 credits, API included, prices exclude VAT, no activation fee. No invented extras.",
        "reviewer": "All figures match F2/F8. The only weak point is the closing offer, which is vague rather than wrong.",
    },
    "Q4": {
        "tab": "Q4 Â· Refund",
        "label": "Sensitive â€” refund request",
        "verdict_kind": "bad",
        "verdict_title": "Defect â€” wrong escalation level",
        "verdict_body": "The SOP requires any refund request to go to a human (PERLU_ESKALASI_MANAJEMEN). The QA agent returned BUTUH_MONITORING. The customer draft itself is compliant â€” this is a routing failure, not a wording failure.",
        "reviewer": "Draft states both conditions as cumulative and makes no approval, denial or promise. The escalation status is the defect.",
    },
    "Q8": {
        "tab": "Q8 Â· Deletion",
        "label": "Missing information â€” delete all data",
        "verdict_kind": "warn",
        "verdict_title": "Known gap â€” omits the F6 timelines",
        "verdict_body": "The draft correctly avoids claiming deletion happened and asks for identity verification first. But it drops both timings from F6: review within 14 working days, backups removed within 30 days.",
        "reviewer": "Safe on the big claim (no fake deletion), incomplete on the detail. As written it sets a false expectation about backups.",
    },
}


def md(s):
    t = html.escape(s or "")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t


def parse(q):
    body = json.load(open(EV / f"{q}_response.json", encoding="utf-8"))["body"]
    out = body.get("output") or ""
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)
    m1 = re.search(r"===BAGIAN_1[^=]*===(.*?)(?:===BAGIAN_2|$)", out, re.S)
    m2 = re.search(r"===BAGIAN_2[^=]*===(.*)$", out, re.S)
    score = re.search(r"SKOR_QA[:\s]*([0-9]{1,3})", out, re.I)
    esc = re.search(r"STATUS_ESKALASI[:\s]*([A-Z_ ]+)", out)
    return {
        "draft": (m1.group(1).strip() if m1 else out).strip(),
        "qa": (m2.group(1).strip() if m2 else ""),
        "score": score.group(1) if score else "â€”",
        "esc": (esc.group(1).strip() if esc else "â€”"),
        "tokens": body.get("token_usage") or {},
        "model": body.get("model"),
        "provider": body.get("provider"),
        "fallback": body.get("fallback_applied"),
    }


meta = {r["id"]: r for r in json.loads((EV / "runs_summary.json").read_text(encoding="utf-8"))}

ESC_CLASS = {"AMAT_AMAN": "ok", "BUTUH_MONITORING": "warn", "PERLU_ESKALASI_MANAJEMEN": "bad"}

sections = []
tabs = []
for i, (q, cfg) in enumerate(CASES.items()):
    data = parse(q)
    m = meta[q]
    qtext = json.load(open(BASE / "faq_test_questions.json", encoding="utf-8"))["questions"]
    qdef = next(x for x in qtext if x["id"] == q)
    entries = "".join(
        f'<div class="kb"><div class="kb-id">{fid}</div><div class="kb-title">{html.escape(kb_entry(fid)[0])}</div>'
        f'<div class="kb-body">{md(kb_entry(fid)[1])}</div></div>'
        for fid in qdef["knowledge_ids"]
    )
    active = " active" if i == 0 else ""
    tabs.append(f'<button class="tab{active}" data-t="{q}" onclick="showCase(\'{q}\')">{html.escape(cfg["tab"])}</button>')
    sections.append(f"""
<section class="case{active}" id="case-{q}">
  <div class="meta">
    <span class="pill">case Â· {q}</span>
    <span class="pill">{html.escape(cfg['label'])}</span>
    <span class="pill">latency Â· {m['elapsed_s']} s</span>
    <span class="pill">tokens Â· {data['tokens'].get('total_tokens','â€”')}</span>
    <span class="pill">QA Â· {data['score']}</span>
    <span class="pill {ESC_CLASS.get(data['esc'],'')}">escalation Â· {html.escape(data['esc'])}</span>
  </div>

  <div class="verdict {cfg['verdict_kind']}">
    <div class="vtitle">{html.escape(cfg['verdict_title'])}</div>
    <div class="vbody">{html.escape(cfg['verdict_body'])}</div>
  </div>

  <div class="grid">
    <div class="col">
      <div class="card">
        <div class="card-h">Customer question</div>
        <p class="question">{md(qdef["question"])}</p>
        <div class="expect">Expected: {md(qdef["expected_behaviour"])}</div>
      </div>
      <div class="card">
        <div class="card-h">Knowledge injected <span class="dim">(manual, no retrieval)</span></div>
        {entries}
      </div>
    </div>

    <div class="col">
      <div class="card">
        <div class="card-h">Siti â€” customer-facing draft <span class="dim">(real model output)</span></div>
        <pre class="reply">{md(data["draft"])}</pre>
      </div>
      <div class="card">
        <div class="card-h">Hendra â€” QA review <span class="dim">score {data['score']}</span></div>
        <p class="rnote">{html.escape(cfg['reviewer'])}</p>
        <details><summary>Full QA text</summary><pre class="reply small">{md(data["qa"])}</pre></details>
      </div>
    </div>
  </div>
</section>""")

doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Customer Service FAQ PoC â€” Evidence</title>
<style>
  :root {{
    --ink:#111827; --muted:#5b677a; --line:#e2e8f0; --teal:#0e9488; --navy:#0f172a;
    --ok:#15803d; --okbg:#e7f6eb; --warn:#b45309; --warnbg:#fdf3e2; --bad:#b91c1c; --badbg:#fdecec;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#f2f4f7; color:var(--ink);
         font:15px/1.6 "Segoe UI", system-ui, -apple-system, sans-serif; }}
  .wrap {{ max-width:1280px; margin:0 auto; padding:26px 26px 48px; }}
  header {{ background:linear-gradient(120deg,#0f172a,#16233b 55%,#0f3b3a); color:#fff;
            border-radius:18px; padding:30px 34px; }}
  header h1 {{ margin:0 0 6px; font-size:27px; letter-spacing:-.3px; }}
  header p {{ margin:0; color:#c7d2e0; font-size:14px; }}
  .chips {{ margin-top:16px; display:flex; flex-wrap:wrap; gap:8px; }}
  .chip {{ background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.16);
           padding:5px 11px; border-radius:999px; font-size:12px; color:#e6edf5; }}
  .chip b {{ color:#5ed3c4; font-weight:600; }}
  .tabs {{ display:flex; gap:8px; margin:22px 0 16px; flex-wrap:wrap; }}
  .tab {{ border:1px solid var(--line); background:#fff; color:var(--muted); font:inherit;
          font-size:13.5px; font-weight:600; padding:9px 16px; border-radius:10px; cursor:pointer; }}
  .tab.active {{ border-color:var(--teal); color:var(--teal); background:#ecfaf7; }}
  .case {{ display:none; }}
  .case.active {{ display:block; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:7px; margin-bottom:14px; }}
  .pill {{ background:#fff; border:1px solid var(--line); border-radius:999px;
           padding:4px 11px; font-size:12px; color:var(--muted); }}
  .pill.ok {{ color:var(--ok); border-color:#bfe3c8; background:var(--okbg); }}
  .pill.warn {{ color:var(--warn); border-color:#f0d3a0; background:var(--warnbg); }}
  .pill.bad {{ color:var(--bad); border-color:#f2bcbc; background:var(--badbg); }}
  .verdict {{ border-radius:12px; padding:14px 18px; margin-bottom:16px; border:1px solid; }}
  .verdict.ok {{ background:var(--okbg); border-color:#bfe3c8; }}
  .verdict.warn {{ background:var(--warnbg); border-color:#f0d3a0; }}
  .verdict.bad {{ background:var(--badbg); border-color:#f2bcbc; }}
  .vtitle {{ font-weight:700; font-size:14px; margin-bottom:3px; }}
  .verdict.ok .vtitle {{ color:var(--ok); }} .verdict.warn .vtitle {{ color:var(--warn); }}
  .verdict.bad .vtitle {{ color:var(--bad); }}
  .vbody {{ font-size:13.5px; color:#243044; }}
  .grid {{ display:grid; grid-template-columns:390px minmax(0,1fr); gap:16px; align-items:start; }}
  .col {{ display:flex; flex-direction:column; gap:16px; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px 20px;
           box-shadow:0 1px 2px rgba(15,23,42,.04); }}
  .card-h {{ font-size:11.5px; font-weight:700; letter-spacing:.7px; text-transform:uppercase;
             color:var(--teal); margin-bottom:12px; }}
  .dim {{ color:var(--muted); font-weight:500; text-transform:none; letter-spacing:0; }}
  .question {{ font-size:15px; font-weight:600; margin:0 0 12px; }}
  .expect {{ font-size:12.5px; color:var(--muted); border-top:1px dashed var(--line); padding-top:10px; }}
  .kb {{ border-left:3px solid var(--teal); padding:8px 0 8px 12px; margin-bottom:12px; background:#fafcfc; }}
  .kb-id {{ font-size:11px; font-weight:700; color:var(--teal); }}
  .kb-title {{ font-size:13px; font-weight:600; margin:1px 0 4px; }}
  .kb-body {{ font-size:12.5px; color:#334155; white-space:pre-wrap; }}
  pre.reply {{ margin:0; white-space:pre-wrap; font:13.5px/1.75 "Segoe UI", system-ui, sans-serif;
               color:#1d2838; max-height:430px; overflow:auto; }}
  pre.reply.small {{ font-size:12.5px; color:var(--muted); max-height:300px; }}
  .rnote {{ margin:0 0 10px; font-size:13.5px; }}
  details summary {{ cursor:pointer; font-size:12.5px; color:var(--teal); font-weight:600; }}
  footer {{ margin-top:26px; font-size:12px; color:var(--muted); }}
  @media (max-width:980px) {{ .grid {{ grid-template-columns:1fr; }} }}
  @media print {{ body {{ background:#fff; }} .tabs {{ display:none; }} .case {{ display:block !important; }}
                  .card, header {{ break-inside:avoid; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Customer Service FAQ â€” proof of concept</h1>
    <p>Real model output through Intern 1's backend. Synthetic, authorized knowledge. Drafts only â€” nothing was sent.</p>
    <div class="chips">
      <span class="chip">model <b>deepseek-v4.1-flash</b></span>
      <span class="chip">provider <b>opencode-go</b></span>
      <span class="chip">runs <b>8/8 success</b></span>
      <span class="chip">fallback <b>false</b></span>
      <span class="chip">sprint 2 Â· day 3</span>
    </div>
  </header>

  <div class="tabs">{''.join(tabs)}</div>
  {''.join(sections)}

  <footer>
    Source: <code>cs_workflow/evidence/Q*_request.json</code> and <code>Q*_response.json</code>, generated 2 Nov 2026.
    The question text and knowledge entries are synthetic test data.
  </footer>
</div>
<script>
function showCase(id) {{
  document.querySelectorAll('.case').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById('case-' + id).classList.add('active');
  document.querySelector('.tab[data-t="' + id + '"]').classList.add('active');
}}
</script>
</body>
</html>"""

OUT.write_text(doc, encoding="utf-8")
print("saved", OUT, len(doc), "bytes")

