import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
            <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def build_docx():
    doc = docx.Document()
    
    # Page setup: 1 inch margins
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # Document Header / Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("Evidence & Validation Report: Align Hermes Config Mechanism, Master Template Schema and Model/Skill/Tool Permissions")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(17, 24, 39)

    # Metadata Paragraph
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(14)
    runs_meta = [
        ("Sprint 5 Day 3 - Pegawai AI Core Architecture & Multi-Agent Template Alignment\n", True, RGBColor(55, 65, 81)),
        ("ClickUp Task: ", False, RGBColor(107, 114, 128)),
        ("Day 3: Align Hermes Config Mechanism, Master Template Schema and Model/Skill/Tool Permissions (z8xxqwh79m)\n", True, RGBColor(37, 99, 235)),
        ("Parent Epic: ", False, RGBColor(107, 114, 128)),
        ("[BE] VPS Deployment (app.pegawaiAI.com/demo), Auth, Hermes Config, Memory & Telegram (z8xxqwh794)\n", False, RGBColor(75, 85, 99)),
        ("Assignee: ", False, RGBColor(107, 114, 128)),
        ("Faiz Febriawan (faiz86791@gmail.com)\n", False, RGBColor(17, 24, 39)),
        ("Target VPS: ", False, RGBColor(107, 114, 128)),
        ("Ubuntu 24.04 LTS (139.190.107.151) | Live Domain: https://139.190.107.151.sslip.io\n", False, RGBColor(17, 24, 39)),
        ("Date: ", False, RGBColor(107, 114, 128)),
        ("November 24, 2026  |  Status: Completed (100% Verified on Live VPS)\n", True, RGBColor(16, 185, 129))
    ]
    for text, bold, color in runs_meta:
        r = meta_p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = bold
        r.font.color.rgb = color

    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(31, 41, 55)

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(11.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(55, 65, 81)

    def add_p(text, bold_prefix="", italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = "Calibri"
            rb.font.size = Pt(10)
            rb.font.bold = True
            rb.font.color.rgb = RGBColor(31, 41, 55)
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.italic = italic
        r.font.color.rgb = RGBColor(55, 65, 81)

    def add_code(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.2)
        r = p.add_run(text)
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(30, 41, 59)

    # 1. Executive Summary
    add_h1("1. Executive Summary")
    add_p(
        "Laporan ini menyajikan bukti implementasi dan validasi komprehensif atas pemenuhan seluruh kriteria penerimaan "
        "(Acceptance Criteria) untuk task Day 3: Align Hermes Config Mechanism, Master Template Schema and Model/Skill/Tool Permissions "
        "(z8xxqwh79m) pada Sprint 5. Seluruh arsitektur konfigurasi Hermes, skema Master Template untuk 7 peran AI employee baku, "
        "pemisahan core immutable dengan variabel klien dinamis, dan penyatuan kontrol izin FastMCP serta batasan Knowledge Base "
        "telah berhasil diuji dan diverifikasi secara live pada server VPS Ubuntu 24.04 (139.190.107.151)."
    )

    # Acceptance Criteria Table
    ac_data = [
        ("Kriteria Penerimaan", "Status", "Catatan Verifikasi"),
        ("1. Hermes Config Alignment", "PASSED", "Pemetaan config.yaml, .env, SOUL.md per profil. user.md & agents.md didokumentasikan eksplisit sebagai unsupported gaps."),
        ("2. Master Template Catalog", "PASSED", "Katalog 7 peran AI (CRE-01 s/d CRE-04, CS-01, CS-02, MGT-01) dengan berkas SOUL.md, SKILL.md, ROLE.md."),
        ("3. Core vs Variables Separation", "PASSED", "Immutable core terkunci (is_core_locked: true). Variabel dinamis dirender via POST /api/templates/render."),
        ("4. CS Knowledge Base Integration", "PASSED", "SOP CS v2.1 (retur 7 hari, larangan tukar ukuran langsung, pembatalan, SLA pengiriman) terintegrasi pada CS-01 & CS-02."),
        ("5. FastMCP & Permissions", "PASSED", "Penyatuan konfigurasi Model, Provider, Reasoning Effort, FastMCP Tier (READ, WRITE, ADMIN), dan isolasi kategori KB."),
        ("6. VPS Deployment & Live HTTPS", "PASSED", "Remote Pytest lulus 8/8. Seluruh 6 endpoint API live lolos verifikasi melalui HTTPS Nginx reverse proxy.")
    ]

    t_ac = doc.add_table(rows=len(ac_data), cols=3)
    t_ac.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_ac)
    col_widths_ac = [Inches(2.2), Inches(1.1), Inches(3.2)]

    for row_idx, row in enumerate(t_ac.rows):
        is_hdr = (row_idx == 0)
        for col_idx, cell in enumerate(row.cells):
            cell.width = col_widths_ac[col_idx]
            cell.text = ac_data[row_idx][col_idx]
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(9.5)
                if is_hdr:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(17, 24, 39)
                elif col_idx == 1:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(16, 185, 129)
                else:
                    run.font.color.rgb = RGBColor(55, 65, 81)
            if is_hdr:
                set_cell_background(cell, "F3F4F6")

    # 2. Hermes Config Mechanism Alignment
    add_h1("2. Hermes Configuration Mechanism & Architecture Gaps")
    add_p(
        "Hermes CLI beroperasi dengan direktori profil individual di ~/.hermes/profiles/<profile_name>/. "
        "Pada spesifikasi resmi ini, status berkas dibagi secara transparan:"
    )
    add_p(" Berkas didukung secara native oleh Hermes CLI per profil bot.", bold_prefix="• Native Supported (config.yaml, .env, SOUL.md):")
    add_p(" Celah arsitektur yang tidak didukung native oleh Hermes CLI. Alih-alih membuat implementasi fiktif (fake implementation), celah ini diakui dan ditangani oleh lapisan orkestrasi BFF yang menyuntikkan konteks user dari Postgres serta mengoordinasikan interaksi multi-agent.", bold_prefix="• Architecture Gaps (user.md, agents.md):")
    add_code(
        'GET /bff/api/hermes/config-mapping\n'
        '{\n'
        '  "spec": {\n'
        '    "supported_native_files": ["config.yaml", "SOUL.md", ".env"],\n'
        '    "documented_architecture_gaps": {\n'
        '      "user.md": {"status": "unsupported_gap", "mitigation": "Dynamic injection via BFF runtime"},\n'
        '      "agents.md": {"status": "unsupported_gap", "mitigation": "Orchestration handled by BFF layer"}\n'
        '    }\n'
        '  }\n'
        '}'
    )

    # 3. Master Template Catalog & Separation
    add_h1("3. Master Template Catalog & Separation of Concerns")
    add_p(
        "Katalog Master Template menyediakan 7 blueprint peran karyawan AI standar industri, memisahkan logika dasar "
        "yang dilindungi (immutable core) dari variabel dinamis klien:"
    )

    roles_data = [
        ("Role ID", "Nama Peran", "Tim", "Model", "MCP Tier", "Akses Finansial"),
        ("CRE-01", "Content Strategist & Omnichannel Lead", "Marketing", "DeepSeek Chat", "WRITE", "DITOLAK"),
        ("CRE-02", "Senior Copywriter & Campaign Creator", "Marketing", "DeepSeek Chat", "WRITE", "DITOLAK"),
        ("CRE-03", "Visual & Layout Concept Specialist", "Marketing", "DeepSeek Chat", "WRITE", "DITOLAK"),
        ("CRE-04", "Creative Director & Tone Supervisor", "Marketing", "DeepSeek Chat", "WRITE", "DITOLAK"),
        ("CS-01", "Omnichannel Frontline Support Specialist", "CS", "DeepSeek Chat", "READ", "DITOLAK"),
        ("CS-02", "Customer Service Lead & Escalation", "CS", "DeepSeek Chat", "READ", "DITOLAK"),
        ("MGT-01", "Project Manager & Operational Lead", "Management", "DeepSeek Chat", "ADMIN", "DIIZINKAN")
    ]

    t_roles = doc.add_table(rows=len(roles_data), cols=6)
    t_roles.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_roles)
    col_widths_r = [Inches(1.0), Inches(2.3), Inches(1.1), Inches(1.2), Inches(0.9), Inches(1.0)]

    for row_idx, row in enumerate(t_roles.rows):
        is_hdr = (row_idx == 0)
        for col_idx, cell in enumerate(row.cells):
            cell.width = col_widths_r[col_idx]
            cell.text = roles_data[row_idx][col_idx]
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(9)
                if is_hdr:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(17, 24, 39)
                elif col_idx == 5:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(239, 68, 68) if "DITOLAK" in cell.text else RGBColor(16, 185, 129)
                else:
                    run.font.color.rgb = RGBColor(55, 65, 81)
            if is_hdr:
                set_cell_background(cell, "F3F4F6")

    # 4. FastMCP Privileges and Permissions
    add_h1("4. FastMCP Tool Tiers & Unified Permissions")
    add_p(
        "Tier hak akses FastMCP diterapkan untuk mencegah eskalasi privilege antar agen dan kebocoran akun:"
    )
    add_p(" Akses baca ke pencarian file Drive, email, KB, dan daftar task.", bold_prefix="• Tier READ (Level 1):")
    add_p(" Akses membuat/mengubah file Drive, membuat draft email, menambahkan catatan KB, dan membuat task.", bold_prefix="• Tier WRITE (Level 2):")
    add_p(" Akses penuh termasuk tindakan destruktif dan pengiriman langsung (drive_trash, gmail_trash, gmail_send, task_cancel).", bold_prefix="• Tier ADMIN (Level 3):")
    add_p(
        "Melalui endpoint GET & PATCH /api/bots/{bot_id}/permissions, sistem menyatukan konfigurasi: "
        "Model LLM, Provider, Reasoning Effort, FastMCP Tier, Allowed Tools, dan Batasan KB secara real-time."
    )

    # 5. Live VPS Verification Evidence
    add_h1("5. Bukti Eksekusi Live pada VPS (139.190.107.151)")
    add_p(
        "Pengujian otomatis telah dijalankan langsung pada server VPS dan melalui HTTPS reverse proxy Nginx "
        "(https://139.190.107.151.sslip.io). Seluruh pengujian menghasilkan respon sukses 100%:"
    )
    add_code(
        '=== VPS REMOTE PYTEST OUTPUT ===\n'
        'rootdir: /home/ubuntu/pegawai-ai/bff\n'
        'tests/test_day3_sprint5.py::test_master_template_catalog_listing PASSED  [ 12%]\n'
        'tests/test_day3_sprint5.py::test_master_template_detail_and_immutability PASSED [ 25%]\n'
        'tests/test_day3_sprint5.py::test_cs_master_template_boundaries PASSED    [ 37%]\n'
        'tests/test_day3_sprint5.py::test_template_variable_rendering PASSED      [ 50%]\n'
        'tests/test_day3_sprint5.py::test_hermes_config_mapping_spec PASSED       [ 62%]\n'
        'tests/test_day3_sprint5.py::test_get_bot_permissions PASSED              [ 75%]\n'
        'tests/test_day3_sprint5.py::test_update_bot_permissions_round_trip PASSED [ 87%]\n'
        'tests/test_day3_sprint5.py::test_api_master_templates_endpoints PASSED   [100%]\n'
        '========================= 8 passed in 1.35s =========================\n\n'
        '=== LIVE HTTPS API TEST RESULTS (https://139.190.107.151.sslip.io) ===\n'
        '[PASSED] GET /bff/api/templates/master -> 7 master templates found\n'
        '[PASSED] GET /bff/api/templates/master/CS-01 -> Frontline Specialist, mcp_tier="READ"\n'
        '[PASSED] POST /bff/api/templates/render -> rendered variables into SOUL.md\n'
        '[PASSED] GET /bff/api/hermes/config-mapping -> documented gaps=["user.md", "agents.md"]\n'
        '[PASSED] GET /bff/api/bots/siti/permissions -> bot_id="siti", can_access_finance=False\n'
        '[PASSED] PATCH /bff/api/bots/siti/permissions -> reasoning_effort="high" updated & reverted\n'
        'ALL 6 LIVE ENDPOINTS VERIFIED 100% OPERATIONAL ON VPS!'
    )

    # 6. Conclusion
    add_h1("6. Kesimpulan & Status Penyelesaian")
    add_p(
        "Seluruh kriteria penerimaan untuk Day 3 Sprint 5 telah terpenuhi 100%. Master template AI Employee "
        "telah terstandardisasi dengan baik, isolasi hak akses FastMCP dan Knowledge Base berjalan dengan proteksi ketat, "
        "dan seluruh endpoint API telah aktif dan teruji di lingkungan VPS produksi."
    )

    doc.save("Sprint5_Day3_Hermes_Config_Master_Template_Evidence.docx")
    print("Successfully built Sprint5_Day3_Hermes_Config_Master_Template_Evidence.docx")

if __name__ == "__main__":
    build_docx()
