from pathlib import Path

root = Path(r"C:\Users\MI\.openmausbot\task-workspaces\5ccb6477-64f6-40a1-8d2f-9fa4ba5eb8f3\c36ce5b6-ee46-4765-9873-218ffad05481")
handover = root / "sprint5_review_handover"


def change(text, old, new):
    if old not in text:
        raise SystemExit("missing source text: " + old[:120])
    return text.replace(old, new, 1)


packet = (handover / "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_1.md").read_text(encoding="utf-8")
packet = packet.replace("v1.1", "v1.2").replace("v1_1", "v1_2")
packet = change(
    packet,
    "**Status:** Drafted for Marketing/Ops review; no final role sign-off recorded",
    "**Status:** v1.2 depth standard applied; drafted for Marketing/Ops review; no final role sign-off recorded",
)
packet = change(
    packet,
    "| Eleven required sections in each template | Complete | Every role has all 11 required sections; section numbering inconsistency found earlier was fixed. |",
    "| Eleven required sections and mandatory subfields | Complete | Every role has the exact bilingual section headings and required subfields from the supplied depth standard. |",
)
packet = change(
    packet,
    "| Depth standard PDF | Blocked | `Task Pegawai AI Template & Profile.pdf` was not found; depth standard is unverified beyond CS-01 pattern. |",
    "| Depth standard content | Supplied | Content supplied 2026-11-24 as `TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md`; all required components and subfields applied in v1.2. The original PDF file is not stored in this workspace. |",
)
old_sections = """1. Scope of Work & Boundaries
2. Persona/Language/Tone
3. Triggers & Use Cases
4. Modular Skills & Capabilities
5. SOP & Task Execution Pattern
6. Operating Rules & Prohibitions
7. Tools/Integrations/Permissions
8. Knowledge Base & Memory Needs
9. Input & Expected Output Standards
10. Approval & Escalation Rules
11. Model Recommendation & KPIs"""
new_sections = """1. Scope of Work & Boundaries (Ruang Lingkup & Batasan)
2. Persona, Language & Tone of Voice (Karakter & Gaya Komunikasi)
3. Triggers & Use Cases (Pemicu & Skenario Penggunaan)
4. Modular Skills & Capabilities (Keterampilan Modular)
5. SOP & Task Execution Pattern (Alur Kerja Eksekusi SOP)
6. Operating Rules & Prohibitions (Prinsip Kerja & Larangan Ketat)
7. Tools, Integrations & Permissions (Alat, Integrasi & Hak Akses)
8. Knowledge Base & Memory Needs (Kebutuhan Basis Data & Memori)
9. Input & Expected Output Standards (Standar Input & Output)
10. Approval & Escalation Rules (Tingkat Otorisasi & Eskalasi)
11. Model Recommendation & KPIs (Rekomendasi Model LLM & Metrik Sukses)"""
packet = change(packet, old_sections, new_sections)
compliance = """
### 3.1 Supplied depth-standard compliance

The supplied standard defines required header metadata and exact subfields inside all 11 sections. The v1.2 templates apply all of them:

- Header: `# [KODE-ROLE] | [NAMA JABATAN]`, `## Divisi: ...`, `Deskripsi Singkat`, and `Job Description`.
- Section 1: In Scope, Out of Scope, Cross-Department Collaboration, Menerima Input dari, and Menyerahkan Hasil ke.
- Section 2: Karakter Profesional, Communication Style, Formality Level, Preferred Language & Dialect, and Response Length & Formatting Rules.
- Section 3: User Prompt Triggers, Concrete Task Scenarios, and scenarios A/B/C.
- Section 4: Core Skills, Supporting Skills, and Optional / Advanced Skills.
- Section 5: the exact eight-step cycle from Understand through Follow Up.
- Section 6: Prinsip Operasional, Penanganan Data Kurang/Ambigu, and Strict Prohibitions (Larangan Keras).
- Section 7: tool matrix with `Alat / Layanan`, `Fungsi Utama`, and `Level Akses (Read / Write / Execute / Approval)`.
- Section 8: required KB documents and all five memory layers.
- Section 9: `Input yang Diperlukan` and `Standar Format Deliverable` with Header, Matrix/Table, Body, and Actionable Next Steps.
- Section 10: Level 1, Level 2, Level 3, and Protokol Eskalasi.
- Section 11: Kategori Model, Reasoning Effort, and the three named KPI measures.

"""
packet = change(packet, "## 4. 8-role by 11-section coverage matrix", compliance + "## 4. 8-role by 11-section coverage matrix")
packet = change(
    packet,
    "Section 0 is now `Catalog JD baseline (catalog supplied 2026-11-22)` in all eight v1.2 templates. Exact catalog duty text is present; cross-check against the 11 sections remains pending. The matrix above covers only the 11 required sections.",
    "Section 0 is `Catalog JD baseline (catalog supplied 2026-11-22)` in all eight v1.2 templates. Exact catalog duty text is present; cross-check against the 11 sections remains pending. The v1.2 exact-subfield check is complete for all eight templates. The matrix above covers only the 11 required sections.",
)
packet = change(
    packet,
    "| RD-13 | Supply or waive `Task Pegawai AI Template & Profile.pdf`. | Keep depth-standard verification open until supplied. | PM | Pending |",
    "| RD-13 | Supply or waive `Task Pegawai AI Template & Profile.pdf`. | Content supplied 2026-11-24; depth standard applied to all eight v1.2 templates. Original PDF file is not stored here. | PM | Closed — content supplied |",
)
packet = change(
    packet,
    "| SRC-S-04 | `Task Pegawai AI Template & Profile.pdf` | Not found | Depth standard referenced by CS-01 |",
    "| SRC-S-03 | `TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md` | Supplied 2026-11-24 | Exact 11-component and subfield standard applied to all v1.2 templates |",
)
packet = change(
    packet,
    "- Do not mark any role signed off until RD-01 and the role-specific pending decisions are resolved.",
    "- Do not mark any role signed off until RD-01 and the role-specific pending decisions are resolved; RD-13 is closed for depth-standard structure, not for business approval.",
)
packet = change(
    packet,
    "| PM | Final archive decision | ____________________ | __________ |",
    "| PM | Final archive decision | ____________________ | __________ |\n\n## 11. Depth-standard verification\n\n- Eight v1.2 Markdown files and eight v1.2 DOCX files were generated.\n- All 11 exact bilingual section headings are present in every template.\n- All mandatory subfields, tool-table columns, five memory layers, eight SOP stages, and three KPI labels are present in every template.\n- `TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md` is included in the handover package as the source standard.\n- Verification output is recorded by `verify_v1_2.py`.",
)
(handover / "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_2.md").write_text(packet, encoding="utf-8")

handoff = (handover / "SPRINT5_BE_FE_HANDOVER_v1_1.md").read_text(encoding="utf-8")
handoff = handoff.replace("v1.1", "v1.2").replace("v1_1", "v1_2")
handoff = change(
    handoff,
    "| BE-13 | Supply or explicitly waive `Task Pegawai AI Template & Profile.pdf`. | PM / All 8 roles | Depth standard verified against the PDF or waiver recorded in the shared document. | Pending |",
    "| BE-13 | Apply the supplied 11-component depth standard. | PM / All 8 roles | Content supplied 2026-11-24; exact headings and subfields present in all eight v1.2 templates; source standard included in package. Original PDF file is not stored here. | Closed |",
)
handoff = change(
    handoff,
    "| BE-14 | Confirm the temporary WhatsApp API provider. | Backend / Ops | Decision recorded: Hermes/Baileys demo number or hosted provider such as Fonnte/Wablas/Wati; no credentials in chat or documents. | Pending |",
    "| BE-14 | Confirm the temporary WhatsApp API provider. | Backend / Ops | Decision recorded: Hermes/Baileys demo number or hosted provider such as Fonnte/Wablas/Wati; no credentials in chat or documents. | Pending |\n| BE-15 | Implement the v1.2 profile schema fields. | All 8 roles | Backend schema stores exact bilingual section labels, required subfields, five memory layers, tool access values, escalation levels, and the three named KPI measures. | Pending |",
)
handoff = change(
    handoff,
    "| FE-01 | Role template reviewer for eight roles. | Lists CS-01 and MKT-01–MKT-07; opens the Markdown/DOCX version; shows version `v1.2`. | Pending |",
    "| FE-01 | Role template reviewer for eight roles. | Lists CS-01 and MKT-01–MKT-07; opens the Markdown/DOCX version; shows version `v1.2`. | Pending |",
)
handoff = change(
    handoff,
    "| FE-02 | 11-section viewer plus Section 0. | All required sections visible in order; catalog-supplied and cross-check-pending states cannot be mistaken for approved content. | Pending |",
    "| FE-02 | 11-section and subfield viewer plus Section 0. | Exact bilingual headings, mandatory subfields, five memory layers, eight SOP stages, and three KPI labels are visible in order; catalog-supplied and cross-check-pending states cannot be mistaken for approved content. | Pending |",
)
handoff = change(
    handoff,
    "- [ ] All eight role DOCX files open and show the required 11 sections plus Section 0.",
    "- [ ] All eight role DOCX files open and show the required 11 sections, exact mandatory subfields, and Section 0.",
)
handoff = change(
    handoff,
    "- [ ] RD-01 through RD-13 resolved or explicitly accepted as open conditions.",
    "- [ ] RD-01 through RD-13 resolved or explicitly accepted as open conditions; RD-13 is closed for structure only.",
)
handoff = change(
    handoff,
    "8. Payload hygiene gate: no credentials, customer data, internal IDs, or calendar dates in ClickUp task fields.",
    "8. Payload hygiene gate: no credentials, customer data, internal IDs, or calendar dates in ClickUp task fields.\n9. Depth-standard gate: v1.2 profile schema preserves the supplied 11-section structure and every mandatory subfield; reviewer sign-off remains separate.",
)
(handover / "SPRINT5_BE_FE_HANDOVER_v1_2.md").write_text(handoff, encoding="utf-8")

register = (handover / "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_1.csv").read_text(encoding="utf-8")
register = register.replace(
    "SRC-S-02,Master catalog DOCX supplied by user,AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx,all roles,supplied 2026-11-22,cross-check pending; ClickUp copy not opened",
    "SRC-S-02,Master catalog DOCX supplied by user,AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx,all roles,supplied 2026-11-22,exact duty text reproduced in Section 0; reviewer cross-check pending",
)
register = register.replace(
    "SRC-S-03,Task Pegawai AI Template Profile PDF,N/A,all roles,missing,depth standard unverified",
    "SRC-S-03,Template Role Detail 11 Mandatory Checklist,TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md,all roles,supplied 2026-11-24,content received as Markdown extraction of Task Pegawai AI Template & Profile; exact structure applied in v1.2",
)
(handover / "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_2.csv").write_text(register, encoding="utf-8")

links = (handover / "SPRINT5_SHARED_DOC_LINKS_v1_1.md").read_text(encoding="utf-8")
links = links.replace("v1.1", "v1.2").replace("v1_1", "v1_2")
links = change(
    links,
    "1. `SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_2.md/.docx`",
    "1. `SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_2.md/.docx`",
)
links = change(
    links,
    "8. `role_templates_v1_2/`",
    "8. `role_templates_v1_2/`\n9. `TEMPLATE_ROLE_DETAIL_11_MANDATORY_CHECKLIST.md` (supplied depth standard)",
)
(handover / "SPRINT5_SHARED_DOC_LINKS_v1_2.md").write_text(links, encoding="utf-8")

page = (handover / "shared_page" / "index.html").read_text(encoding="utf-8")
page = page.replace("v1.1", "v1.2").replace("v1_1", "v1_2")
page = page.replace(
    '<div class="card"><strong>Catalog baselines</strong><span class="badge warn">Supplied</span> Exact duty text pasted; cross-check pending.</div>',
    '<div class="card"><strong>Catalog baselines</strong><span class="badge warn">Supplied</span> Exact duty text pasted; cross-check pending.</div>\n<div class="card"><strong>Depth standard</strong><span class="badge ok">Applied</span> Content supplied 2026-11-24; exact subfields normalized in v1.2.</div>',
)
page = page.replace(
    "The templates are ready for structured Marketing/Ops review, not production configuration. All source assumptions, blocked baselines, and permission gates remain visible for decision.",
    "The v1.2 templates match the supplied 11-component depth standard and are ready for structured Marketing/Ops review, not production configuration. All source assumptions, blocked baselines, and permission gates remain visible for decision.",
)
page = page.replace(
    "<p class=\"muted\">Section 0 is now catalog-supplied in all eight v1.2 templates. Exact duty text is present; reviewer cross-check against the 11 sections remains pending.</p>",
    "<p class=\"muted\">Section 0 is catalog-supplied in all eight v1.2 templates. Exact duty text is present; reviewer cross-check against the 11 sections remains pending. All exact bilingual headings and mandatory subfields from the supplied depth standard are present.</p>",
)
page = page.replace(
    "<li>The master catalog DOCX was supplied on 2026-11-22 and its exact duty text was pasted into Section 0 of all eight v1.2 templates. The depth-standard PDF was not found; the user will ask the PM for it.</li>",
    "<li>The master catalog DOCX was supplied on 2026-11-22 and its exact duty text was pasted into Section 0 of all eight v1.2 templates. The depth-standard content was supplied on 2026-11-24 as a Markdown extraction and applied to every v1.2 template; the original PDF file is not stored here.</li>",
)
page = page.replace(
    "<tr><td>RD-13</td><td>Supply or waive the depth-standard PDF.</td><td>Keep depth verification open until supplied or waived.</td><td>PM</td><td><span class=\"badge warn\">Pending</span></td></tr>",
    "<tr><td>RD-13</td><td>Supply or waive the depth-standard PDF.</td><td>Content supplied 2026-11-24; exact structure applied to all v1.2 templates.</td><td>PM</td><td><span class=\"badge ok\">Closed — content supplied</span></td></tr>",
)
page = page.replace("<li>Restore catalog access and paste JD baselines.</li>", "<li>Verify the supplied catalog baseline and paste JD baselines.</li>")
page = page.replace("<li>11-section viewer plus blocked Section 0.</li>", "<li>11-section and subfield viewer plus supplied Section 0.</li>")
page = page.replace(
    "<li>All eight v1.2 DOCX files open and show 11 sections plus the supplied catalog Section 0.</li>",
    "<li>All eight v1.2 DOCX files open and show 11 exact sections, mandatory subfields, and the supplied catalog Section 0.</li>",
)
(handover / "shared_page" / "index.html").write_text(page, encoding="utf-8")

print("generated v1.2 review packet, handover, register, links, and shared page")
