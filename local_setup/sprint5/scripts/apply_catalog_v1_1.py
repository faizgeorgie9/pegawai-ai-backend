from pathlib import Path
import re

root = Path(r"C:\Users\MI\.openmausbot\task-workspaces\5ccb6477-64f6-40a1-8d2f-9fa4ba5eb8f3\c36ce5b6-ee46-4765-9873-218ffad05481")
catalog_attachment = Path(r"C:\Users\MI\.openmausbot\attachments\c9cf124a-f3ae-4783-8edb-67c8ff3d2144.docx")
handover = root / "sprint5_review_handover"
local_handover = Path(r"C:\Users\MI\Documents\pegawai-ai-backend\local_setup\sprint5_review_handover")

entries = {
    "CS-01": {
        "file": "CS-01_Omnichannel_Customer_Service_template_v1.md",
        "heading": "CS-01  |  Omnichannel Customer Service",
        "short": "Deskripsi singkat: Menangani interaksi pelanggan melalui kanal komunikasi yang terhubung dan memberikan bantuan sepanjang perjalanan pelanggan.",
        "duties": [
            "Menjawab pertanyaan produk, harga, ketersediaan, kebijakan, dan FAQ serta membantu pelanggan memilih produk.",
            "Membantu memeriksa status pesanan dan pengiriman, serta menangani pertanyaan terkait transaksi.",
            "Menangani keluhan, permintaan retur atau refund sesuai kebijakan, memperbarui konteks layanan, dan mengeskalasi kasus yang membutuhkan keputusan manusia.",
        ],
        "section": "02. Customer Service & Experience",
        "crosswalk": "Catalog duty 1 maps to sections 3, 4, 8 and 9; live product, price, stock, policy and FAQ claims remain limited to approved sources. Catalog duty 2 maps to sections 1, 4, 7 and 10 and remains blocked for live status until an authoritative read-only source is configured. Catalog duty 3 maps to sections 1, 3, 5, 6, 8 and 10 and is implemented as internal drafts plus recommendation-only escalation until a named human owner is assigned. Reviewer decision: confirm whether the catalog division label 'Customer Service & Experience' should replace the template's 'Customer Service & Operations'.",
    },
    "MKT-01": {
        "file": "MKT-01_Marketing_Strategist_template_v1.md",
        "heading": "MKT-01  |  Marketing Strategist",
        "short": "Deskripsi singkat: Menyusun strategi pemasaran berdasarkan pasar, pelanggan, kompetitor, dan tujuan bisnis.",
        "duties": [
            "Melakukan riset pasar, kompetitor, tren, dan target audience.",
            "Menentukan positioning, value proposition, channel, dan pendekatan pemasaran.",
            "Menyusun rencana marketing dan rekomendasi campaign yang selaras dengan target bisnis.",
        ],
        "section": "03. Marketing & Sales",
        "crosswalk": "Catalog duty 1 maps to sections 3, 4, 7, 8 and 9 and is covered by the Aldi research module. Catalog duty 2 maps to sections 4, 5 and 9. Catalog duty 3 maps to sections 3, 5, 9, 10 and 11. Reviewer decision: confirm the synthesis mapping MKT-01 = Aldi + Bram + Meda/Bimo; the catalog supplies duties, not the Karyawan.AI source mapping.",
    },
    "MKT-02": {
        "file": "MKT-02_SEO_Specialist_template_v1.md",
        "heading": "MKT-02  |  SEO Specialist",
        "short": "Deskripsi singkat: Meningkatkan visibilitas organik website melalui riset, evaluasi, dan optimasi SEO.",
        "duties": [
            "Melakukan keyword research, search intent analysis, dan analisis kompetitor.",
            "Melakukan SEO audit serta memberikan rekomendasi optimasi halaman, struktur, dan internal linking.",
            "Menyusun prioritas keyword dan strategi peningkatan visibilitas serta performa pencarian.",
        ],
        "section": "03. Marketing & Sales",
        "crosswalk": "Catalog duty 1 maps to sections 3, 4, 5 and 9. Catalog duty 2 maps to sections 3, 4, 5, 9 and 10. Catalog duty 3 maps to sections 5, 9 and 11. All three fit the exact Rifqy dossier adaptation; the no-live-data rule remains active because the catalog does not grant API access.",
    },
    "MKT-03": {
        "file": "MKT-03_Digital_Ads_Specialist_template_v1.md",
        "heading": "MKT-03  |  Digital Ads Specialist",
        "short": "Deskripsi singkat: Merencanakan, memantau, dan mengevaluasi kampanye iklan berbayar untuk mencapai target pemasaran.",
        "duties": [
            "Menyusun strategi dan struktur campaign pada platform seperti Meta Ads dan Google Ads.",
            "Memantau performa iklan, audiens, materi kreatif, dan penggunaan anggaran.",
            "Menganalisis hasil serta memberikan rekomendasi optimasi campaign, targeting, dan budget.",
        ],
        "section": "03. Marketing & Sales",
        "crosswalk": "Catalog duty 1 maps to sections 1, 4, 5, 7 and 9. The template currently configures only Meta Ads; Google Ads is named in the catalog but is not connected in the supplied tools and remains a reviewer decision. Catalog duty 2 maps to sections 4, 5, 7, 9 and 11. Catalog duty 3 maps to sections 5, 9 and 11. PAUSED-only creation and explicit activation approval remain active.",
    },
    "MKT-04": {
        "file": "MKT-04_Email_Marketing_Specialist_template_v1.md",
        "heading": "MKT-04  |  Email Marketing Specialist",
        "short": "Deskripsi singkat: Mengelola komunikasi pemasaran melalui email untuk membangun hubungan, engagement, dan konversi.",
        "duties": [
            "Menyusun newsletter, email campaign, dan rangkaian email otomatis.",
            "Mengelola segmentasi audiens, mailing list, dan personalisasi pesan.",
            "Menganalisis deliverability, open rate, click-through rate, dan konversi untuk meningkatkan performa.",
        ],
        "section": "03. Marketing & Sales",
        "crosswalk": "Catalog duty 1 maps to sections 3, 4, 5 and 9, but the template implements draft sequences only; sending and automation require an ESP and human approval. Catalog duty 2 maps to sections 4, 8 and 9; the template currently forbids contact/PII and list access, so segment rules must be supplied as non-PII briefs until approved. Catalog duty 3 maps to sections 7, 9 and 11; no ESP analytics tool is connected, so the role can analyze user-supplied reports only. Reviewer decision: confirm whether the draft-only boundary is accepted as the operating scope.",
    },
    "MKT-05": {
        "file": "MKT-05_Lead_Generation_Specialist_template_v1.md",
        "heading": "MKT-05  |  Lead Generation Specialist",
        "short": "Deskripsi singkat: Mencari dan menyiapkan database calon pelanggan yang relevan bagi kegiatan penjualan.",
        "duties": [
            "Mengidentifikasi sumber dan menemukan prospek sesuai profil pelanggan ideal.",
            "Mengumpulkan serta melengkapi informasi kontak dan profil calon pelanggan dari sumber yang diizinkan.",
            "Menilai, mengelompokkan, dan memprioritaskan kualitas prospek sebelum diserahkan kepada tim sales.",
        ],
        "section": "03. Marketing & Sales — lanjutan",
        "crosswalk": "Catalog duty 1 maps to sections 3, 4, 5, 8 and 9. Catalog duty 2 maps to sections 4 and 9 but conflicts with the template's no-recipient-PII rule; the catalog says contact information may be collected from permitted sources, while the template only drafts source criteria and does not store contact data. Catalog duty 3 maps to sections 4, 5, 9 and 10. Reviewer decision: resolve the PII boundary before approving this role.",
    },
    "MKT-06": {
        "file": "MKT-06_Sales_Assistant_template_v1.md",
        "heading": "MKT-06  |  Sales Assistant",
        "short": "Deskripsi singkat: Mendukung proses penjualan dengan menghubungi prospek, mengelola tindak lanjut, dan menyiapkan kebutuhan penawaran.",
        "duties": [
            "Membuat dan mengirim pesan pendekatan serta melakukan follow-up melalui kanal yang diizinkan.",
            "Membantu kualifikasi prospek, menjadwalkan pertemuan, dan memperbarui CRM atau sales pipeline.",
            "Menyiapkan draft penawaran, proposal, ringkasan kebutuhan pelanggan, dan tindak lanjut penjualan.",
        ],
        "section": "03. Marketing & Sales — lanjutan",
        "crosswalk": "Catalog duty 1 maps to sections 1, 3, 5 and 9. The template narrows this to pre-sale conversations from approved lead lists and one reply per turn; provider choice is still pending. Catalog duty 2 maps to sections 4, 5 and 9; CRM update and meeting scheduling are not connected in the current template and remain reviewer/backend decisions. Catalog duty 3 maps to sections 4, 5 and 9 as drafts only. Reviewer decision: confirm the pre-sale boundary and whether CRM/scheduling access will be granted.",
    },
    "MKT-07": {
        "file": "MKT-07_Marketing_Performance_Analyst_template_v1.md",
        "heading": "MKT-07  |  Marketing Performance Analyst",
        "short": "Deskripsi singkat: Mengolah data pemasaran menjadi laporan dan insight untuk mengevaluasi efektivitas aktivitas marketing.",
        "duties": [
            "Menganalisis performa channel, campaign, traffic, leads, dan conversion rate.",
            "Mengukur metrik seperti biaya akuisisi, efektivitas anggaran, dan marketing ROI jika datanya tersedia.",
            "Menyusun dashboard, laporan berkala, serta rekomendasi berbasis data untuk tim marketing.",
        ],
        "section": "03. Marketing & Sales — lanjutan",
        "crosswalk": "Catalog duty 1 maps to sections 3, 4, 5, 9 and 11. Catalog duty 2 maps to sections 5, 7, 9 and 11 and preserves the catalog's 'if the data is available' limit. Catalog duty 3 maps to sections 5, 7, 9 and 11; reports may be saved as new dated files through the configured drive tool. No ad-entity writes are granted.",
    },
}


def baseline_block(entry):
    bullets = "\n".join("- " + duty for duty in entry["duties"])
    return (
        "Source: `AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx`, section `"
        + entry["section"]
        + "`, supplied by the user as a local DOCX on 2026-11-22. The text below is copied verbatim from that file. The ClickUp Doc copy was not opened for this update.\n\n"
        + "Catalog JD baseline (verbatim):\n\n"
        + entry["heading"]
        + "\n\n"
        + entry["short"]
        + "\n\nJob description:\n\n"
        + bullets
        + "\n\nCross-check: "
        + entry["crosswalk"]
        + "\n"
    )

for code, entry in entries.items():
    src = root / entry["file"]
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"^Version: v1\b", "Version: v1.1", text, count=1, flags=re.MULTILINE)
    baseline_line = (
        "- Baseline: extends the catalog Job Description for "
        + code
        + " in *AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx*. The exact catalog text is reproduced in section 0 from the DOCX supplied by the user on 2026-11-22."
    )
    text = re.sub(r"^- Baseline:.*$", baseline_line, text, count=1, flags=re.MULTILINE)
    text = re.sub(
        r"^## 0\. Catalog JD baseline \(source blocked\)$",
        "## 0. Catalog JD baseline (catalog supplied 2026-11-22)",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"(## 0\. Catalog JD baseline[^\n]*\n\n)[\s\S]*?(?=\n---\n)",
        lambda m: m.group(1) + baseline_block(entry),
        text,
        count=1,
    )
    open_item = (
        "1. Catalog JD baseline for "
        + code
        + " is now pasted in section 0 from the supplied catalog DOCX; reviewer cross-check against sections 1–11 remains pending."
    )
    text = re.sub(
        r"^\d+\. (?:The )?Catalog JD paragraph for " + re.escape(code) + r".*$",
        open_item,
        text,
        flags=re.MULTILINE,
    )
    text = text.replace(
        "| Catalog JD Doc `2kzn5r6w-5998` | baseline duties | Blocked — HTTP 403 |",
        "| Catalog JD baseline | baseline duties | Supplied as local DOCX 2026-11-22; cross-check pending |",
    )
    text = text.replace(
        "The catalog JD paragraph for MKT-02 is a Blocker until pasted (section 0).",
        "The catalog JD baseline for MKT-02 is now pasted in section 0; reviewer cross-check remains pending.",
    )
    text = text.replace(
        "The catalog JD paragraph for MKT-01 (section 0) — Blocker until pasted (Doc `2kzn5r6w-5998`, HTTP 403).",
        "The catalog JD baseline for MKT-01 is now pasted in section 0 from the supplied catalog DOCX; reviewer cross-check remains pending.",
    )
    dst = root / entry["file"].replace("_v1.md", "_v1_1.md")
    dst.write_text(text, encoding="utf-8")

crosswalk_lines = [
    "# Sprint 5 Catalog JD Baseline Crosswalk v1",
    "",
    "**Source received:** `AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx`, supplied by the user on 2026-11-22 (Jakarta time).",
    "**Purpose:** verify that each role template contains the exact catalog duty statement and record where each catalog duty maps into the 11-section template.",
    "**Status:** catalog baseline supplied; reviewer cross-check pending. This document does not grant role sign-off.",
    "",
    "## Review rule",
    "",
    "The catalog is the baseline duty statement. It does not override the role template's explicit boundaries, approval gates or tool permissions. Where a catalog duty is broader than the implemented operating scope, the difference is recorded below and remains a reviewer decision.",
    "",
]
for code, entry in entries.items():
    crosswalk_lines += [
        "## " + entry["heading"],
        "",
        "**Catalog section:** " + entry["section"],
        "",
        "**Verbatim catalog text:**",
        "",
        entry["short"],
        "",
        "Job description:",
        "",
    ]
    crosswalk_lines += ["- " + duty for duty in entry["duties"]]
    crosswalk_lines += ["", "**Cross-check:** " + entry["crosswalk"], ""]
crosswalk_lines += [
    "## Sign-off",
    "",
    "| Reviewer | Decision | Name | Date |",
    "|---|---|---|---|",
    "| Marketing | Accept / Revisions / Reject | ____________________ | __________ |",
    "| Ops | Accept / Revisions / Reject | ____________________ | __________ |",
    "| PM | Archive decision | ____________________ | __________ |",
]
(root / "sprint5_review_handover" / "SPRINT5_CATALOG_BASELINE_CROSSWALK_v1.md").write_text("\n".join(crosswalk_lines) + "\n", encoding="utf-8")

source_path = handover / "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1.csv"
source_text = source_path.read_text(encoding="utf-8")
source_text = source_text.replace(
    "SRC-S-02,Master catalog Doc 2kzn5r6w-5998,2kzn5r6w-5998,all roles,blocked,HTTP 403",
    "SRC-S-02,Master catalog DOCX supplied by user,AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx,all roles,supplied 2026-11-22,cross-check pending; ClickUp copy not opened",
)
(handover / "SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_1.csv").write_text(source_text, encoding="utf-8")

packet = (handover / "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1.md").read_text(encoding="utf-8")
packet = packet.replace("# Sprint 5 Role Template Review Packet v1", "# Sprint 5 Role Template Review Packet v1.1")
packet = packet.replace("| Master catalog JD baselines | Blocked | Catalog Doc `2kzn5r6w-5998` returns HTTP 403; must be pasted into Section 0 before sign-off. |", "| Master catalog JD baselines | Supplied | Local DOCX supplied 2026-11-22; exact duty text pasted into Section 0 of all eight v1.1 templates; reviewer cross-check pending. |")
packet = packet.replace("Section 0, `Catalog JD baseline (source blocked)`, is present in all eight templates but remains blocked for every role until the master catalog is accessible. The matrix above covers only the 11 required sections.", "Section 0 is now `Catalog JD baseline (catalog supplied 2026-11-22)` in all eight v1.1 templates. Exact catalog duty text is present; cross-check against the 11 sections remains pending. The matrix above covers only the 11 required sections.")
packet = packet.replace("| RD-01 | Restore access to master catalog Doc `2kzn5r6w-5998` and paste each role's JD baseline into Section 0. | Block final sign-off until complete. | PM / Backend | Blocked |", "| RD-01 | Verify the supplied catalog baseline and duty cross-check in all eight v1.1 templates. | Source access blocker closed; reviewer confirmation still required before final sign-off. | PM / Marketing / Ops | Cross-check pending |")
packet = packet.replace("| SRC-S-03 | Master catalog Doc `2kzn5r6w-5998` | Blocked HTTP 403 | Catalog JD baselines |", "| SRC-S-03 | Master catalog DOCX supplied by user | Supplied 2026-11-22 | Catalog JD baselines; cross-check pending |")
packet = packet.replace("1. Catalog JD baseline gate: no final sign-off until RD-01 and the role-specific pending decisions are resolved.", "1. Catalog JD baseline gate: exact catalog text is now present; no final sign-off until RD-01 cross-check and the role-specific pending decisions are resolved.")
packet = packet.replace("- [ ] All eight role DOCX files open and show the required 11 sections plus Section 0.", "- [ ] All eight role DOCX files open and show the required 11 sections plus the supplied catalog Section 0.")
(handover / "SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_1.md").write_text(packet, encoding="utf-8")

be_fe = (handover / "SPRINT5_BE_FE_HANDOVER_v1.md").read_text(encoding="utf-8")
be_fe = be_fe.replace("# Sprint 5 Backend/Frontend Handover v1", "# Sprint 5 Backend/Frontend Handover v1.1")
be_fe = be_fe.replace("| BE-01 | Restore master catalog access and paste the exact JD baseline into Section 0 of each role template. | All 8 roles | Doc `2kzn5r6w-5998` opens; Section 0 in all eight templates matches the catalog text; source ID recorded. | Blocked HTTP 403 |", "| BE-01 | Verify the supplied catalog baseline and duty cross-check in Section 0 of each role template. | All 8 roles | Local DOCX supplied 2026-11-22; Section 0 in all eight v1.1 templates matches the catalog text; crosswalk reviewed. | Supplied; cross-check pending |")
be_fe = be_fe.replace("| FE-02 | 11-section viewer plus Section 0. | All required sections visible in order; blocked/source-badged items cannot be mistaken for approved content. | Pending |", "| FE-02 | 11-section viewer plus Section 0. | All required sections visible in order; catalog-supplied and cross-check-pending states cannot be mistaken for approved content. | Pending |")
be_fe = be_fe.replace("1. Catalog JD baseline gate: no final sign-off until BE-01 is complete.", "1. Catalog JD baseline gate: exact catalog text is present; no final sign-off until BE-01 cross-check is complete.")
be_fe = be_fe.replace("- [ ] All eight role DOCX files open and show 11 sections plus Section 0.", "- [ ] All eight role DOCX files open and show 11 sections plus the supplied catalog Section 0.")
(handover / "SPRINT5_BE_FE_HANDOVER_v1_1.md").write_text(be_fe, encoding="utf-8")

links = (handover / "SPRINT5_SHARED_DOC_LINKS_v1.md").read_text(encoding="utf-8")
links = links.replace("# Sprint 5 Shared Document Links", "# Sprint 5 Shared Document Links v1.1")
links = links.replace("- Status: Ready locally, not published.", "- Status: Updated locally to v1.1; not published.")
links = links.replace("1. `SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1.md/.docx`", "1. `SPRINT5_ROLE_TEMPLATE_REVIEW_PACKET_v1_1.md/.docx`")
links = links.replace("2. `SPRINT5_BE_FE_HANDOVER_v1.md/.docx`", "2. `SPRINT5_BE_FE_HANDOVER_v1_1.md/.docx`")
links = links.replace("3. `SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1.csv`", "3. `SPRINT5_ROLE_TEMPLATE_SOURCE_REGISTER_v1_1.csv`")
links = links.replace("5. `shared_page/index.html`", "5. `shared_page/index.html`\n6. `SPRINT5_CATALOG_BASELINE_CROSSWALK_v1.md/.docx`\n7. `SOURCE_AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx`\n8. `role_templates_v1_1/`")
(handover / "SPRINT5_SHARED_DOC_LINKS_v1_1.md").write_text(links, encoding="utf-8")

(handover / "shared_page" / "SOURCE_AI_Top_Trends_Master_Catalog_30_Pegawai_AI_v1.0.docx").write_bytes(catalog_attachment.read_bytes())

page_path = handover / "shared_page" / "index.html"
page = page_path.read_text(encoding="utf-8")
page = page.replace("<title>Sprint 5 Role Template Review</title>", "<title>Sprint 5 Role Template Review v1.1</title>")
page = page.replace("<h1>Sprint 5 Role Template Review</h1>", "<h1>Sprint 5 Role Template Review v1.1</h1>")
page = page.replace('<div class="card"><strong>Catalog baselines</strong><span class="badge bad">Blocked</span> Master catalog request returned HTTP 403.</div>', '<div class="card"><strong>Catalog baselines</strong><span class="badge warn">Supplied</span> Exact duty text pasted; cross-check pending.</div>')
page = page.replace('<p class="muted">Section 0, the catalog JD baseline, is present in all eight templates but blocked until the master catalog is accessible.</p>', '<p class="muted">Section 0 is now catalog-supplied in all eight v1.1 templates. Exact duty text is present; reviewer cross-check against the 11 sections remains pending.</p>')
page = page.replace("<li>The master catalog JD baseline remains blocked by HTTP 403. The depth-standard PDF was not found.</li>", "<li>The master catalog DOCX was supplied on 2026-11-22 and its exact duty text was pasted into Section 0 of all eight v1.1 templates. The depth-standard PDF was not found; the user will ask the PM for it.</li>")
page = page.replace("<tr><td>RD-01</td><td>Restore catalog access and paste JD baselines into Section 0.</td><td>Block final sign-off until complete.</td><td>PM / Backend</td><td><span class=\"badge bad\">Blocked</span></td></tr>", "<tr><td>RD-01</td><td>Verify the supplied catalog baseline and duty cross-check.</td><td>Source access blocker closed; reviewer confirmation required.</td><td>PM / Marketing / Ops</td><td><span class=\"badge warn\">Cross-check pending</span></td></tr>")
page = page.replace("<li>All eight DOCX files open and show 11 sections plus Section 0.</li>", "<li>All eight v1.1 DOCX files open and show 11 sections plus the supplied catalog Section 0.</li>")
page_path.write_text(page, encoding="utf-8")

print("created v1.1 role templates:", len(entries))
print("created packet, handover, crosswalk, source register and shared links")
