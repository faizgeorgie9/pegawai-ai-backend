from pathlib import Path
import re
import zipfile
from docx import Document

root = Path(r"C:\Users\MI\.openmausbot\task-workspaces\5ccb6477-64f6-40a1-8d2f-9fa4ba5eb8f3\c36ce5b6-ee46-4765-9873-218ffad05481")
handover = root / "sprint5_review_handover"
local = Path(r"C:\Users\MI\Documents\pegawai-ai-backend\local_setup\sprint5_review_handover")
extracted = (root / "MASTER_CATALOG_EXTRACTED_v1.txt").read_text(encoding="utf-8").splitlines()

roles = {
    "CS-01": "Omnichannel Customer Service",
    "MKT-01": "Marketing Strategist",
    "MKT-02": "SEO Specialist",
    "MKT-03": "Digital Ads Specialist",
    "MKT-04": "Email Marketing Specialist",
    "MKT-05": "Lead Generation Specialist",
    "MKT-06": "Sales Assistant",
    "MKT-07": "Marketing Performance Analyst",
}
base_names = {
    "CS-01": "CS-01_Omnichannel_Customer_Service_template",
    "MKT-01": "MKT-01_Marketing_Strategist_template",
    "MKT-02": "MKT-02_SEO_Specialist_template",
    "MKT-03": "MKT-03_Digital_Ads_Specialist_template",
    "MKT-04": "MKT-04_Email_Marketing_Specialist_template",
    "MKT-05": "MKT-05_Lead_Generation_Specialist_template",
    "MKT-06": "MKT-06_Sales_Assistant_template",
    "MKT-07": "MKT-07_Marketing_Performance_Analyst_template",
}

required = [
    "Divisi:",
    "Deskripsi Singkat:",
    "Job Description:",
    "1. Scope of Work & Boundaries (Ruang Lingkup & Batasan)",
    "2. Persona, Language & Tone of Voice (Karakter & Gaya Komunikasi)",
    "3. Triggers & Use Cases (Pemicu & Skenario Penggunaan)",
    "4. Modular Skills & Capabilities (Keterampilan Modular)",
    "5. SOP & Task Execution Pattern (Alur Kerja Eksekusi SOP)",
    "6. Operating Rules & Prohibitions (Prinsip Kerja & Larangan Ketat)",
    "7. Tools, Integrations & Permissions (Alat, Integrasi & Hak Akses)",
    "8. Knowledge Base & Memory Needs (Kebutuhan Basis Data & Memori)",
    "9. Input & Expected Output Standards (Standar Input & Output)",
    "10. Approval & Escalation Rules (Tingkat Otorisasi & Eskalasi)",
    "11. Model Recommendation & KPIs (Rekomendasi Model LLM & Metrik Sukses)",
    "In Scope (Tanggung Jawab Utama)",
    "Out of Scope (Bukan Tanggung Jawab)",
    "Cross-Department Collaboration (Kolaborasi Lintas Peran)",
    "Menerima Input dari",
    "Menyerahkan Hasil ke",
    "Karakter Profesional",
    "Communication Style",
    "Formality Level",
    "Preferred Language & Dialect",
    "Response Length & Formatting Rules",
    "User Prompt Triggers",
    "Concrete Task Scenarios",
    "Skenario A (Rutin/Harian)",
    "Skenario B (Insidental/Kampanye)",
    "Skenario C (Pivoting/Optimasi)",
    "Core Skills",
    "Supporting Skills",
    "Optional / Advanced Skills",
    "Understand:",
    "Analyze:",
    "Clarify:",
    "Plan:",
    "Execute:",
    "Verify:",
    "Report:",
    "Follow Up:",
    "Prinsip Operasional",
    "Penanganan Data Kurang/Ambigu",
    "Strict Prohibitions (Larangan Keras)",
    "Alat / Layanan",
    "Fungsi Utama",
    "Level Akses (Read / Write / Execute / Approval)",
    "Dokumen Wajib dari Klien",
    "Arsitektur Memori 5 Layer",
    "Layer 1 (Session)",
    "Layer 2 (Employee)",
    "Layer 3 (Customer/Tenant)",
    "Layer 4 (Project)",
    "Layer 5 (Long-Term)",
    "Input yang Diperlukan",
    "Standar Format Deliverable",
    "Header, Matrix/Table, Body, Actionable Next Steps",
    "Level 1 (Autonomous)",
    "Level 2 (Approval Required)",
    "Level 3 (Restricted / Human Only)",
    "Protokol Eskalasi",
    "Kategori Model",
    "Reasoning Effort",
    "Key Performance Indicators (KPI)",
    "KPI 1: Kelengkapan & Kualitas Deliverable (%)",
    "KPI 2: Kepatuhan Brand & Anti-Halusinasi (100%)",
    "KPI 3: Ketepatan Waktu Perencanaan (SLA)",
    "TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md",
]
stale = [
    "not available; depth standard referenced but not verified",
    "depth standard unverified",
    "Depth standard PDF | Blocked",
    "Catalog JD baseline (source blocked)",
    "HTTP 403",
    "Version: v1.1",
]

catalog = {}
for code in roles:
    idx = next(i for i, line in enumerate(extracted) if code + "  |  " in line)
    catalog[code] = [
        extracted[idx].split("\t", 2)[2].strip(),
        extracted[idx + 1].split("\t", 2)[2].strip(),
        extracted[idx + 3].split("\t", 2)[2].strip(),
        extracted[idx + 4].split("\t", 2)[2].strip(),
        extracted[idx + 5].split("\t", 2)[2].strip(),
    ]

failures = []
checks = 0
for code, name in roles.items():
    base = base_names[code]
    md_path = root / f"{base}_v1_2.md"
    docx_path = root / f"{base}_v1_2.docx"
    for path in [md_path, docx_path]:
        if not path.exists():
            failures.append(f"missing {path.name}")
            continue
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    doc = Document(docx_path) if docx_path.exists() else None
    doc_text = ""
    if doc:
        doc_text += "\n".join(p.text for p in doc.paragraphs)
        doc_text += "\n" + "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    for label, text, kind in [(f"{code} MD", md, "MD"), (f"{code} DOCX", doc_text, "DOCX")]:
        expected_title = f"# {code} | {name}" if kind == "MD" else f"{code} | {name}"
        if expected_title not in text:
            failures.append(f"{label}: missing exact title")
        checks += 1
        for expected in required:
            checks += 1
            if expected not in text:
                failures.append(f"{label}: missing {expected}")
        for expected in catalog[code]:
            checks += 1
            if expected not in text:
                failures.append(f"{label}: missing catalog line {expected}")
        for bad in stale:
            checks += 1
            if bad in text:
                failures.append(f"{label}: stale {bad}")
        if text.count("Document: shared working document") != 1:
            failures.append(f"{label}: metadata not single")
        if text.count("Version: v1.2") != 1:
            failures.append(f"{label}: version not single")
    if doc:
        tool_tables = [t for t in doc.tables if t.rows and t.rows[0].cells and t.rows[0].cells[0].text == "Alat / Layanan"]
        if len(tool_tables) != 1:
            failures.append(f"{code} DOCX: expected one tool table, found {len(tool_tables)}")
        for table in tool_tables:
            for row in table.rows[1:]:
                access = row.cells[2].text.strip()
                checks += 1
                if access not in {"Read", "Write", "Execute", "Approval"}:
                    failures.append(f"{code} DOCX: invalid access value {access}")

def path_text(path):
    if path.suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    return path.read_text(encoding="utf-8")


for expected, path in [
    ("Sprint 5 Role Template Review Packet v1.2", handover / "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_2.docx"),
    ("Content supplied 2026-11-24", handover / "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_2.docx"),
    ("Sprint 5 Backend/Frontend Handover v1.2", handover / "SPRINT5_BE_FE_HANDOVER_v1_2.docx"),
    ("BE-15", handover / "SPRINT5_BE_FE_HANDOVER_v1_2.docx"),
    ("supplied 2026-11-24", handover / "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_2.csv"),
    ("Sprint 5 Role Template Review v1.2", handover / "shared_page" / "index.html"),
    ("Closed — content supplied", handover / "shared_page" / "index.html"),
]:
    checks += 1
    if not path.exists():
        failures.append(f"missing {path}")
    elif expected not in path_text(path):
        failures.append(f"{path.name}: missing {expected}")

register = (handover / "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_2.csv").read_text(encoding="utf-8")
for bad in ["Task Pegawai AI Template Profile PDF,N/A,all roles,missing,depth standard unverified"]:
    checks += 1
    if bad in register:
        failures.append("source register: stale depth-standard row")

expected_staged = [
    local / "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_2.docx",
    local / "SPRINT5_BE_FE_HANDOVER_v1_2.docx",
    local / "SPRINT5_CATALOG_BASELINE_CROSSWALK_v1.docx",
    local / "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_2.csv",
    local / "SPRINT5_SHARED_DOC_LINKS_v1_2.md",
    local / "SOURCE_AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx",
    local / "TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md",
    local / "shared_page" / "index.html",
]
for path in expected_staged:
    checks += 1
    if not path.exists():
        failures.append(f"missing staged file {path.name}")
for code, base in base_names.items():
    for suffix in [".md", ".docx"]:
        checks += 1
        if not (local / "role_templates_v1_2" / f"{base}_v1_2{suffix}").exists():
            failures.append(f"missing staged template {base}_v1_2{suffix}")

archive = root / "SPRINT5_V1_2_HANDOVER_PACKAGE.zip"
if not archive.exists():
    failures.append("missing v1.2 archive")
else:
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
    expected_zip = [
        "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_2.docx",
        "SPRINT5_BE_FE_HANDOVER_v1_2.docx",
        "SPRINT5_CATALOG_BASELINE_CROSSWALK_v1.docx",
        "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_2.csv",
        "SPRINT5_SHARED_DOC_LINKS_v1_2.md",
        "SOURCE_AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx",
        "TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md",
        "shared_page/index.html",
    ]
    for code, base in base_names.items():
        for suffix in [".md", ".docx"]:
            expected_zip.append(f"role_templates_v1_2/{base}_v1_2{suffix}")
    for expected in expected_zip:
        checks += 1
        if expected not in names:
            failures.append(f"zip missing {expected}")

print("templates checked:", len(roles))
print("format checks:", len(roles) * 2)
print("mandatory labels per format:", len(required))
print("total checks:", checks)
print("failures:", len(failures))
for failure in failures:
    print(failure)
