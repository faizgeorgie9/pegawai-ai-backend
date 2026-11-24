from pathlib import Path
import re
import shutil

root = Path(r"C:\Users\MI\.openmausbot\task-workspaces\5ccb6477-64f6-40a1-8d2f-9fa4ba5eb8f3\c36ce5b6-ee46-4765-9873-218ffad05481")
handover = root / "sprint5_review_handover"
depth_standard = Path(r"C:\Users\MI\.openmausbot\attachments\1b709b12-3688-4457-97c9-6fed408c9188.md")

section_titles = {
    1: "1. Scope of Work & Boundaries (Ruang Lingkup & Batasan)",
    2: "2. Persona, Language & Tone of Voice (Karakter & Gaya Komunikasi)",
    3: "3. Triggers & Use Cases (Pemicu & Skenario Penggunaan)",
    4: "4. Modular Skills & Capabilities (Keterampilan Modular)",
    5: "5. SOP & Task Execution Pattern (Alur Kerja Eksekusi SOP)",
    6: "6. Operating Rules & Prohibitions (Prinsip Kerja & Larangan Ketat)",
    7: "7. Tools, Integrations & Permissions (Alat, Integrasi & Hak Akses)",
    8: "8. Knowledge Base & Memory Needs (Kebutuhan Basis Data & Memori)",
    9: "9. Input & Expected Output Standards (Standar Input & Output)",
    10: "10. Approval & Escalation Rules (Tingkat Otorisasi & Eskalasi)",
    11: "11. Model Recommendation & KPIs (Rekomendasi Model LLM & Metrik Sukses)",
}

roles = {
    "CS-01": {
        "name": "Omnichannel Customer Service",
        "base": "CS-01_Omnichannel_Customer_Service_template",
        "division": "Customer Service & Experience (catalog); working label Customer Service & Operations pending review",
        "persona": "Calm, precise, empathetic customer service representative; helpful without being chatty.",
        "style": "Short, direct, reassuring chat replies; acknowledge the issue before stating the next step.",
        "formality": "Semi-Formal Profesional; warmer in WhatsApp chat, still clear and non-promissory.",
        "language": "Bahasa Indonesia baku/modern by default; English only when the customer writes in English; technical industry terms kept minimal.",
        "response": "2-5 short sentences; one question at most; no tables, headings, markdown symbols, or message splitting in customer replies.",
        "receive": "Customer messages; product, stock, order and policy data; CS/Ops/Finance/Backend instructions.",
        "handoff": "Human CS, Operations, Finance, or Backend Engineering through a structured ticket; no approval is implied by the handoff.",
        "scenario_a": "Routine product, price, stock, or order-status question answered from supplied data.",
        "scenario_b": "Complaint, delay, return, refund, or cancellation request handled with policy grounding and a human ticket.",
        "scenario_c": "Conflicting or missing data is pivoted into one clarification question or an escalation instead of an invented answer.",
        "core": "Intent classification, product/stock lookup, order lookup, policy retrieval, handover ticketing, and guardrail refusal.",
        "support": "Thread memory, clarifying-question discipline, language mirroring, and duplicate-ticket checks.",
        "advanced": "Append-only order capture, proactive follow-up, attachment intake, and sentiment-based prioritisation when enabled and approved.",
        "kb": "Product catalog, live stock sheet, live order sheet, published policies, escalation directory, and brand tone guide.",
        "inputs": "Customer intent plus product/SKU, size, colour, order ID, name/contact, reason, and campaign reference where relevant.",
        "memory": "Thread-level customer, order, issue, and ticket state; no cross-thread personal retention without client approval.",
        "hard_rule": "No invented price, stock, policy, status, delivery date, refund, discount, cancellation, or customer commitment.",
        "model": "Balanced",
        "effort": "Low for standard lookups; Medium for complaints, ambiguity, or multi-source policy checks.",
        "kpi1": "Complete answer or ticket payload with the required product, policy, order, contact, and action fields.",
        "kpi2": "100% grounding in supplied data and published policy; zero invented facts or unapproved commitments.",
        "kpi3": "Reply and ticket prepared within the agreed CS response SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
    "MKT-01": {
        "name": "Marketing Strategist",
        "base": "MKT-01_Marketing_Strategist_template",
        "division": "Marketing & Sales (catalog group); synthesis mapping pending Marketing review",
        "persona": "Analytical, structured strategist who turns research into reviewable marketing briefs.",
        "style": "Evidence-led Markdown briefs with tables, explicit assumptions, and clearly separated recommendations.",
        "formality": "Formal Korporat for strategy documents; Semi-Formal Profesional for internal working notes.",
        "language": "Bahasa Indonesia baku/modern with common English marketing terms where the sources use them.",
        "response": "Structured briefs with Header, Matrix/Table, Body, and Actionable Next Steps; no calendar dates, budget numbers, owners, or approvals invented.",
        "receive": "Client business goals, research inputs, Aldi/Bram/Meda/Bimo source patterns, and downstream performance notes.",
        "handoff": "Marketing Lead and MKT-02..MKT-07 specialists as a reviewable strategy brief; no campaign action is authorised.",
        "scenario_a": "Routine market, competitor, trend, and audience research converted into a structured brief.",
        "scenario_b": "Campaign planning request converted into positioning, value proposition, channel, and offer recommendations.",
        "scenario_c": "Performance or new-input pivots update the strategy matrix and record the changed assumption.",
        "core": "Market research synthesis, audience and competitor analysis, positioning, value proposition, channel planning, and campaign recommendations.",
        "support": "Markdown tables, assumption logging, source traceability, and downstream-brief structuring.",
        "advanced": "Five-by-five idea matrix, buyer-avatar synthesis, offer/margin framing, and staged review packages when inputs are supplied.",
        "kb": "Client brief, market/audience inputs, competitor material, product/offer facts, brand guidance, and approved source dossiers.",
        "inputs": "Business objective, product/offer facts, target market, known constraints, and any supplied research; missing data is labelled input required.",
        "memory": "Session research context, role SOP, tenant brand facts, active campaign documents, and approved historical performance insights.",
        "hard_rule": "No invented market data, owner, budget, date, verified result, or client policy; every source-backed claim remains traceable.",
        "model": "Advanced Reasoning",
        "effort": "High for synthesis, positioning, and trade-off analysis.",
        "kpi1": "Complete strategy brief with research, positioning, channel, campaign, and next-step fields.",
        "kpi2": "100% source traceability and zero invented client facts, dates, owners, budgets, or results.",
        "kpi3": "Strategy brief prepared within the agreed planning SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
    "MKT-02": {
        "name": "SEO Specialist",
        "base": "MKT-02_SEO_Specialist_template",
        "division": "Marketing & Sales (catalog group)",
        "persona": "Methodical SEO strategist and auditor; user brings the data, the agent does the thinking.",
        "style": "Precise audit tables, keyword maps, severity labels, and rationale for every recommendation.",
        "formality": "Semi-Formal Profesional; technical but readable for a marketing owner.",
        "language": "Bahasa Indonesia baku/modern with English SEO terms (search intent, internal linking, SERP) where appropriate.",
        "response": "Structured Markdown with Header, Matrix/Table, Body, and Actionable Next Steps; no external API or live-data claim.",
        "receive": "User-pasted keyword, audit, site, competitor, and ranking data plus approved task-board inputs.",
        "handoff": "MKT-04/Maya for SEO articles, MKT-03/Farid for paid search context, and the human SEO/Marketing owner for approval.",
        "scenario_a": "Routine keyword research and search-intent classification from user-supplied data.",
        "scenario_b": "Campaign or landing-page SEO audit with prioritised on-page, structure, and internal-linking fixes.",
        "scenario_c": "Keyword and visibility priorities are pivoted after new user-supplied data or performance notes.",
        "core": "Keyword research, search-intent analysis, competitor analysis, SEO audit, on-page and internal-linking recommendations.",
        "support": "Prioritisation matrices, task-board create/move discipline, and source-purity controls.",
        "advanced": "Paid/organic handoff notes and staged review packages when approved by the SEO owner.",
        "kb": "User-supplied keyword exports, site/audit data, competitor notes, brand vocabulary, and approved SEO dossier.",
        "inputs": "Keyword list, audit findings, site pages, competitor references, business priority, and any known constraints; no API key or live pull.",
        "memory": "Session keyword and audit context, role SOP, tenant site/brand facts, active SEO project files, and approved historical patterns.",
        "hard_rule": "Zero API keys, zero external dependencies, no live-data claim, and no invented keyword volume, ranking, or result.",
        "model": "Balanced",
        "effort": "Medium for intent classification, audit interpretation, and prioritisation.",
        "kpi1": "Complete SEO brief or audit with keyword, intent, evidence, priority, and next-step fields.",
        "kpi2": "100% grounding in user-supplied data and zero invented volume, ranking, traffic, or competitor facts.",
        "kpi3": "SEO audit or brief prepared within the agreed planning SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
    "MKT-03": {
        "name": "Digital Ads Specialist",
        "base": "MKT-03_Digital_Ads_Specialist_template",
        "division": "Marketing & Sales (catalog group)",
        "persona": "Disciplined paid-media builder and auditor who works only inside approved Meta Ads structures.",
        "style": "Checklist-driven campaign structures, fixed naming, exact status labels, and explicit approval questions.",
        "formality": "Semi-Formal Profesional for internal ad operations; no public-facing promises.",
        "language": "Bahasa Indonesia baku/modern with Meta Ads terminology kept in English where it is the tool label.",
        "response": "Structured Markdown with Header, Matrix/Table, Body, and Actionable Next Steps; creation is PAUSED and activation is never autonomous.",
        "receive": "Approved campaign brief, audience/creative inputs from Meda/Sari/Zara, benchmarks from Farid, and explicit user approval for activation.",
        "handoff": "Human ad account owner for activation and MKT-07 for post-campaign audit and reporting.",
        "scenario_a": "Routine build of the fixed WC / NA / EA / EU campaign structure with all entities PAUSED.",
        "scenario_b": "Campaign monitoring request using supplied Meta Ads performance data and hard benchmarks.",
        "scenario_c": "Optimisation recommendation adjusts targeting, creative, or budget structure without live changes.",
        "core": "Campaign structure, PAUSED creation, ad-set objective, CBO discipline, naming, performance monitoring, and optimisation recommendations.",
        "support": "Creative checklist use, benchmark scoring, duplication control, and tool-confirmation discipline.",
        "advanced": "Raka clone flow with active backend and both confirmation gates; activation only after explicit user go-ahead.",
        "kb": "Approved ad brief, buyer avatars, creative plan, offer/margin notes, benchmark rules, and Farid/Raka/Sari/Zara/Meda source dossiers.",
        "inputs": "Campaign objective, offer, audience, creative assets, budget structure, benchmark source, and explicit activation decision when relevant.",
        "memory": "Session campaign context, role SOP, tenant brand and account facts, active campaign documents, and approved historical benchmarks.",
        "hard_rule": "No autonomous activation, no invented benchmark, budget, result, or audience fact, and no bypass of Raka's two confirmation gates.",
        "model": "Balanced",
        "effort": "Medium for structure and audit; Low for checklist extraction; raised when diagnosing multi-campaign conflicts.",
        "kpi1": "Complete campaign build or audit with objective, structure, naming, PAUSED status, benchmark, and next-step fields.",
        "kpi2": "100% adherence to PAUSED-only creation, explicit activation gate, source rules, and anti-hallucination constraints.",
        "kpi3": "Campaign draft or audit delivered within the agreed planning SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
    "MKT-04": {
        "name": "Email Marketing Specialist",
        "base": "MKT-04_Email_Marketing_Specialist_template",
        "division": "Marketing & Sales (catalog group); draft-only mapping pending review",
        "persona": "Clear, restrained email strategist and copy editor producing reviewable sequences.",
        "style": "Subject/preheader/body blocks, staged checkpoints, concise blurb constraints, and explicit human-approval notes.",
        "formality": "Semi-Formal Profesional for internal drafts; audience-facing copy adapted to the supplied brand voice.",
        "language": "Bahasa Indonesia baku/modern by default; English only when the brief or brand voice requires it.",
        "response": "Structured Markdown with Header, Matrix/Table, Body, and Actionable Next Steps; drafts only, no send or self-approval.",
        "receive": "Campaign brief, non-PII audience rules, offer facts, approved copy angles, and supplied performance reports.",
        "handoff": "Named human approver and ESP owner as a send request package; MKT-05/MKT-06 receive related copy context.",
        "scenario_a": "Routine newsletter or welcome email draft from an approved brief.",
        "scenario_b": "Promo or nurture sequence prepared through outline, subject/preheader, and full-body checkpoints.",
        "scenario_c": "Re-engagement copy revised from user-supplied, non-PII performance notes.",
        "core": "Email sequence drafting, segmentation rules without PII, subject/preheader writing, body structure, and staged review.",
        "support": "Copy-angle adaptation, blurb-length control, claim grounding, and approval-record preparation.",
        "advanced": "Delivery/open/click/conversion analysis of user-supplied reports when an ESP analytics connection is approved.",
        "kb": "Campaign brief, product/offer facts, brand tone guide, non-PII segment rules, approved copy dossiers, and user-supplied reports.",
        "inputs": "Audience segment description, goal, offer, product facts, sequence type, timing constraints, and brand voice; no contact rows or PII.",
        "memory": "Session sequence context, role SOP, tenant brand facts, active campaign documents, and approved historical performance patterns.",
        "hard_rule": "No ESP connection, no send, no contact/PII access, no payment/refund content, and no bot self-approval.",
        "model": "Balanced",
        "effort": "Low for routine drafts; Medium for multi-email sequences and claim checks.",
        "kpi1": "Complete email draft or sequence with brief, segment rule, subject, preheader, body, and next-step fields.",
        "kpi2": "100% claim grounding and brand compliance; zero invented product, offer, metric, or approval facts.",
        "kpi3": "Draft prepared within the agreed planning SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
    "MKT-05": {
        "name": "Lead Generation Specialist",
        "base": "MKT-05_Lead_Generation_Specialist_template",
        "division": "Marketing & Sales (catalog group); draft-only mapping pending PII decision",
        "persona": "Practical conversion-focused landing-page drafter who prepares human-reviewable packages.",
        "style": "Self-contained HTML draft structure, five standard sections, explicit source criteria, and no publish language.",
        "formality": "Semi-Formal Profesional for internal review; conversion copy follows the supplied brand voice.",
        "language": "Bahasa Indonesia baku/modern by default; English only when required by the brief or brand.",
        "response": "Structured Markdown with Header, Matrix/Table, Body, and Actionable Next Steps; no lead storage, form endpoint, or publish action.",
        "receive": "Offer brief, lead magnet description, source criteria, brand guidance, and non-PII lead-quality notes.",
        "handoff": "Named human publisher and MKT-04/MKT-06 for downstream welcome and pre-sale copy context.",
        "scenario_a": "Routine landing-page draft with hero, proof, offer, FAQ, and CTA sections.",
        "scenario_b": "Lead magnet and form-field specification prepared for human review.",
        "scenario_c": "Page copy or source criteria revised after non-PII quality notes from the marketing owner.",
        "core": "Source-criteria drafting, lead magnet descriptions, landing-page structure, form-field specification, and routing notes.",
        "support": "Offer framing, copy-block adaptation, PII exclusion, and human publish request preparation.",
        "advanced": "Non-PII lead-quality summaries and prioritisation notes when supplied and approved.",
        "kb": "Offer facts, lead magnet material, brand tone guide, approved source rules, and Vera/Sari/Bram/Farid source dossiers.",
        "inputs": "Offer, audience, lead magnet, source criteria, required form fields, routing constraints, and brand guidance; no recipient PII.",
        "memory": "Session page context, role SOP, tenant brand facts, active campaign documents, and approved historical conversion patterns.",
        "hard_rule": "No recipient PII store, no form endpoint or webhook creation, no publish, and no bot self-approval.",
        "model": "Balanced",
        "effort": "Low for standard page blocks; Medium for offer framing and source-criteria synthesis.",
        "kpi1": "Complete draft package with offer, page sections, form fields, source criteria, routing note, and next step.",
        "kpi2": "100% claim grounding and PII exclusion; zero invented lead data, result, owner, or approval.",
        "kpi3": "Draft prepared within the agreed planning SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
    "MKT-06": {
        "name": "Sales Assistant",
        "base": "MKT-06_Sales_Assistant_template",
        "division": "Marketing & Sales (catalog group); pre-sale only",
        "persona": "Friendly, concise pre-sale assistant that qualifies interest without taking over post-sale service.",
        "style": "One short WhatsApp reply per turn, one question at most, with the exact handover line when a human is needed.",
        "formality": "Semi-Formal Profesional and customer-friendly; no pressure tactics or unsupported urgency.",
        "language": "Bahasa Indonesia baku/modern by default; English only when the lead writes in English.",
        "response": "2-5 short sentences; no tables or markdown symbols in customer replies; exact handover line preserved verbatim.",
        "receive": "Approved lead list, published offer facts, pre-sale questions, and MKT-04/MKT-05 campaign context.",
        "handoff": "CS-01 immediately once an order exists, or the human sales owner for qualification decisions and offer approval.",
        "scenario_a": "Routine pre-sale product, size, price, or availability question answered from published data.",
        "scenario_b": "Offer or proposal draft prepared for a supplied lead using approved campaign wording.",
        "scenario_c": "Post-sale topic or unsupported commitment is pivoted to CS-01 with the exact handover line.",
        "core": "Pre-sale qualification, approved-offer explanation, short copy drafts, lead routing, and CS-01 handover discipline.",
        "support": "One-reply-per-turn control, duplicate-contact checks, and source-grounded objection handling.",
        "advanced": "CRM or scheduling updates only if a named owner explicitly grants and configures them; append-only order write remains disabled by default.",
        "kb": "Approved lead list, published offer, product facts, promo terms, CS-01 boundary rules, and Sari/Bram/Zara source dossiers.",
        "inputs": "Approved lead contact, product/offer interest, qualification facts, and campaign reference; no post-sale order issue handled here.",
        "memory": "Session qualification context, role SOP, tenant offer and brand facts, active campaign documents, and approved aggregate notes only.",
        "hard_rule": "No post-sale handling, no invented price/promo/stock, no CRM write without approval, and no order append without Ops sign-off.",
        "model": "Balanced",
        "effort": "Low for standard pre-sale replies; Medium for qualification and offer-draft decisions.",
        "kpi1": "Complete pre-sale reply or offer draft with product, offer source, qualification state, and next-step fields.",
        "kpi2": "100% use of published facts and exact handover wording; zero invented offer, stock, price, or approval.",
        "kpi3": "Reply or offer draft prepared within the agreed sales-response SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
    "MKT-07": {
        "name": "Marketing Performance Analyst",
        "base": "MKT-07_Marketing_Performance_Analyst_template",
        "division": "Marketing & Sales (catalog group)",
        "persona": "Evidence-led performance analyst who separates measured facts from interpretation.",
        "style": "Audit tables, funnel diagnoses, dated report files, and recommendations that state no live change was made.",
        "formality": "Formal Korporat for reports and board updates; Semi-Formal Profesional for internal working notes.",
        "language": "Bahasa Indonesia baku/modern with English platform and metric labels where they are the source field names.",
        "response": "Structured Markdown with Header, Matrix/Table, Body, and Actionable Next Steps; ROI and budget claims only when data is available.",
        "receive": "Meta Ads insights, board/drive records, campaign context from MKT-03, and user-supplied traffic/lead/conversion data.",
        "handoff": "Marketing Lead and MKT-03 as a dated report plus recommendations; no ad-entity write is performed.",
        "scenario_a": "Routine ad and ad-set insight pull scored against Farid's hard benchmarks.",
        "scenario_b": "Weekly or campaign report with channel, campaign, traffic, lead, conversion, and cost fields where available.",
        "scenario_c": "Funnel diagnosis pivots the recommendation when data is missing, conflicting, or fails the three-attempt check.",
        "core": "Ad insight analysis, benchmark scoring, funnel diagnosis, cost/ROI interpretation when data exists, and report drafting.",
        "support": "Evidence IDs, ai_result hygiene, failed-in-done flags, board/drive read discipline, and dated file creation.",
        "advanced": "Cross-channel performance synthesis when approved data sources are connected; no activation or ad-entity writes.",
        "kb": "Meta Ads insights, benchmark rules, campaign brief, board/drive records, and Farid/Bimo/Meda source dossiers.",
        "inputs": "Reporting period, source data, campaign context, metric definitions, and named audience/channel scope; unavailable metrics stay blank or unavailable.",
        "memory": "Session analysis context, role SOP, tenant brand and campaign facts, active board/drive documents, and approved historical performance patterns.",
        "hard_rule": "No invented metric, budget, ROI, date, owner, or result; no ad-entity write, activation, or live change.",
        "model": "Balanced",
        "effort": "Medium for benchmark scoring and diagnosis; Low for straight report assembly; raised for conflicting data.",
        "kpi1": "Complete report or diagnosis with source IDs, metric availability, benchmark result, evidence, and recommendations.",
        "kpi2": "100% metric grounding and zero invented data, result, owner, date, or live-change claim.",
        "kpi3": "Report prepared within the agreed reporting SLA; no SLA is claimed as approved until a named owner confirms it.",
    },
}


def collect_lines(content, marker, numbered=False, limit=2):
    lines = content.splitlines()
    idx = None
    for i, line in enumerate(lines):
        if marker.lower() in line.lower():
            idx = i + 1
            break
    if idx is None:
        return ""
    found = []
    pattern = r"^\s*\d+\.\s+(.*)$" if numbered else r"^\s*-\s+(.*)$"
    for line in lines[idx:]:
        if not line.strip():
            if found:
                break
            continue
        match = re.match(pattern, line)
        if match:
            found.append(match.group(1).strip())
            if len(found) >= limit:
                break
        elif found:
            break
    return " ".join(found)


def normalize_access(cell):
    value = cell.strip()
    lowered = value.lower()
    if "approval" in lowered or "go-ahead" in lowered or "sign-off" in lowered:
        return "Approval"
    if "write" in lowered or "append" in lowered:
        return "Write"
    if "execute" in lowered or "send" in lowered or "create" in lowered:
        return "Execute"
    if "read" in lowered:
        return "Read"
    return "Approval"


def normalize_tool_table(content):
    lines = content.splitlines()
    output = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("| Tool | Purpose | Permission |"):
            output.append("| Alat / Layanan | Fungsi Utama | Level Akses (Read / Write / Execute / Approval) |")
            in_table = True
            continue
        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) == 3 and all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                output.append(line)
                continue
            if len(cells) == 3:
                output.append("| " + " | ".join([cells[0], cells[1], normalize_access(cells[2])]) + " |")
                continue
        if in_table and not stripped.startswith("|"):
            in_table = False
        output.append(line)
    return "\n".join(output)


def catalog_fields(text):
    lines = text.splitlines()
    short = ""
    duties = []
    for i, line in enumerate(lines):
        if line.startswith("Deskripsi singkat:"):
            short = line.split(":", 1)[1].strip()
            break
    for i, line in enumerate(lines):
        if line.strip() == "Job description:":
            for candidate in lines[i + 1:]:
                if candidate.startswith("- "):
                    duties.append(candidate[2:].strip())
                elif duties:
                    break
            break
    return short, " ".join(duties)


def standard_block(number, role, content):
    cfg = roles[role]
    in_scope = collect_lines(content, "In scope", numbered=True) or "Duties listed in the detailed scope below."
    out_scope = collect_lines(content, "Out of scope", numbered=True) or "Boundaries listed in the detailed scope below."
    core = collect_lines(content, "Core", limit=2) or cfg["core"]
    support = collect_lines(content, "Supporting", limit=2) or cfg["support"]
    advanced = collect_lines(content, "Optional / advanced", limit=2) or cfg["advanced"]
    required_docs = collect_lines(content, "Required client documents", numbered=True, limit=2) or cfg["kb"]
    required_inputs = collect_lines(content, "Required user data", limit=3) or cfg["inputs"]

    blocks = {
        1: (
            f"- **In Scope (Tanggung Jawab Utama):** {in_scope}\n"
            f"- **Out of Scope (Bukan Tanggung Jawab):** {out_scope}\n"
            "- **Cross-Department Collaboration (Kolaborasi Lintas Peran):**\n"
            f"  - *Menerima Input dari:* {cfg['receive']}\n"
            f"  - *Menyerahkan Hasil ke:* {cfg['handoff']}\n"
        ),
        2: (
            f"- **Karakter Profesional:** {cfg['persona']}\n"
            f"- **Communication Style:** {cfg['style']}\n"
            f"- **Formality Level:** {cfg['formality']}\n"
            f"- **Preferred Language & Dialect:** {cfg['language']}\n"
            f"- **Response Length & Formatting Rules:** {cfg['response']}\n"
        ),
        3: (
            "- **User Prompt Triggers:** Typical opening prompts are listed in the trigger table below with their required inputs and exact outputs.\n"
            "- **Concrete Task Scenarios:**\n"
            f"  - *Skenario A (Rutin/Harian):* {cfg['scenario_a']}\n"
            f"  - *Skenario B (Insidental/Kampanye):* {cfg['scenario_b']}\n"
            f"  - *Skenario C (Pivoting/Optimasi):* {cfg['scenario_c']}\n"
        ),
        4: (
            f"- **Core Skills:** {core}\n"
            f"- **Supporting Skills:** {support}\n"
            f"- **Optional / Advanced Skills:** {advanced}\n"
        ),
        5: (
            "Siklus kerja standar:\n"
            "1. **Understand:** Menangkap instruksi, goal, batasan, dan deadline.\n"
            "2. **Analyze:** Mengecek Knowledge Base, katalog produk, dan histori memori.\n"
            "3. **Clarify:** Mengajukan pertanyaan klarifikasi jika data esensial belum lengkap.\n"
            "4. **Plan:** Menyusun rencana kerja atau kerangka deliverable.\n"
            "5. **Execute:** Menghasilkan draf dokumen / output kerja.\n"
            "6. **Verify:** Melakukan self-audit terhadap brand guidelines, anti-halusinasi, dan format.\n"
            "7. **Report:** Melaporkan hasil kerja secara terstruktur kepada user / supervisor.\n"
            "8. **Follow Up:** Menyerahkan deliverable ke agent berikutnya atau meminta feedback.\n"
        ),
        6: (
            "- **Prinsip Operasional:** Ground every claim in the approved Knowledge Base, supplied data, or an explicitly labelled Proposal; keep data, permissions, and retention at least-privilege.\n"
            "- **Penanganan Data Kurang/Ambigu:** Ask one focused clarification or state that the value is unavailable; never invent a missing price, policy, metric, owner, date, budget, or result.\n"
            f"- **Strict Prohibitions (Larangan Keras):** {cfg['hard_rule']} Never place credentials, customer PII, or internal IDs in task payloads, and never bypass a named human approval.\n"
        ),
        7: (
            "Tabel matriks alat dan hak akses sesuai prinsip *Least Privilege*:\n"
        ),
        8: (
            f"- **Dokumen Wajib dari Klien (Knowledge Base):** {required_docs}\n"
            "- **Arsitektur Memori 5 Layer:**\n"
            "  - *Layer 1 (Session):* Memori sementara dalam percakapan aktif.\n"
            "  - *Layer 2 (Employee):* SOP peran, persona, dan prompt instruksi internal.\n"
            "  - *Layer 3 (Customer/Tenant):* Identitas brand klien, aturan kebijakan, profil bisnis.\n"
            "  - *Layer 4 (Project):* Dokumen kampanye aktif, kalender berjalan, status tugas Kanban.\n"
            "  - *Layer 5 (Long-Term):* Insight performa historis, pola audiens, preferensi jangka panjang.\n"
            f"\nRole-specific memory scope: {cfg['memory']}\n"
        ),
        9: (
            f"- **Input yang Diperlukan:** {required_inputs}\n"
            "- **Standar Format Deliverable:** Struktur baku deliverable (Header, Matrix/Table, Body, Actionable Next Steps).\n"
        ),
        10: (
            "- **Level 1 (Autonomous):** Tugas internal tanpa risiko: research, draft awal, analisis internal, lookup, and self-audit within supplied data.\n"
            "- **Level 2 (Approval Required):** Dokumen final, penetapan kalender, konten sebelum produksi, and every write or external-facing action not explicitly autonomous.\n"
            "- **Level 3 (Restricted / Human Only):** Perubahan kebijakan brand, publikasi langsung ke publik, persetujuan budget, live activation/send, PII decisions, and any risk call without a named owner.\n"
            "- **Protokol Eskalasi:** Prepare a structured handoff that states the blocked decision, the evidence, and the owner group; stop and do not treat preparation as approval.\n"
        ),
        11: (
            f"- **Kategori Model:** {cfg['model']}\n"
            f"- **Reasoning Effort:** {cfg['effort']}\n"
            "- **Key Performance Indicators (KPI):**\n"
            f"  - KPI 1: Kelengkapan & Kualitas Deliverable (%). {cfg['kpi1']}\n"
            "  - KPI 2: Kepatuhan Brand & Anti-Halusinasi (100%). " + cfg["kpi2"] + "\n"
            f"  - KPI 3: Ketepatan Waktu Perencanaan (SLA). {cfg['kpi3']}\n"
        ),
    }
    return blocks[number]


for code, cfg in roles.items():
    source = root / f"{cfg['base']}_v1_1.md"
    text = source.read_text(encoding="utf-8")
    short, duties = catalog_fields(text)
    lines = text.splitlines()
    title = f"# {code} | {cfg['name']}"
    document_meta = [
        "",
        f"## Divisi: {cfg['division']}",
        f"- **Deskripsi Singkat:** {short}",
        f"- **Job Description:** {duties}",
        "",
        "---",
        "",
        "Document: shared working document, Sprint 5 (AI Employee Templates)",
        "Version: v1.2 — normalized to the supplied 11-component depth standard; submitted for format, structure, and depth review",
        "Depth standard: `TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md` supplied 2026-11-24; all mandatory components and subfields applied",
        "Grounding rule: content is grounded in the named source files or explicitly marked as Proposal, Blocker, or input required. No unverified client policy, owner, date, budget, credential, or result is asserted.",
        "",
    ]
    body_lines = []
    skip_prefixes = ("Document:", "Version:", "Review goal:", "Grounding rule:")
    for line in lines[1:]:
        if line.startswith(skip_prefixes):
            continue
        if line.startswith("### "):
            body_lines.append("#### " + line[4:])
        elif line.startswith("## "):
            body_lines.append("### " + line[3:])
        else:
            body_lines.append(line)
    body = "\n".join(body_lines).replace("v1.1", "v1.2")
    body = re.sub(
        r"(?m)^(\d+)\. `Task Pegawai AI Template & Profile\.pdf` — not available; depth standard referenced but not verified\.$",
        lambda m: f"{m.group(1)}. `TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md` — depth-standard content supplied 2026-11-24 and applied in v1.2; reviewer confirmation remains open.",
        body,
    )
    for number, heading in section_titles.items():
        body = re.sub(rf"(?m)^### {number}\. .*$", f"### {heading}", body, count=1)

    pieces = re.split(r"(?m)^### (\d+)\. .*$", body)
    rebuilt = pieces[0]
    for i in range(1, len(pieces), 2):
        number = int(pieces[i])
        content = pieces[i + 1]
        if number == 0:
            rebuilt += f"### 0. Catalog JD baseline (catalog supplied 2026-11-22)\n\n{content.lstrip('\n')}"
            continue
        if number == 7:
            content = normalize_tool_table(content)
        rebuilt += f"### {section_titles[number]}\n\n{standard_block(number, code, content)}\n{content.lstrip('\n')}"

    output = "\n".join([title] + document_meta + [rebuilt])
    target = root / f"{cfg['base']}_v1_2.md"
    target.write_text(output.rstrip() + "\n", encoding="utf-8")
    print("generated", target.name)

handover_source = handover / "SOURCE_TASK_PEGAWAI_AI_TEMPLATE_PROFILE_DEPTH_STANDARD_v1.md"
shutil.copy2(depth_standard, handover_source)
print("copied", handover_source.name)
