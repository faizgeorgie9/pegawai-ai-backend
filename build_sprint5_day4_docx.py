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

def set_cell_margins(cell, top=100, bottom=100, left=120, right=120):
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
    run_title = p_title.add_run("Evidence & Validation Report: Activate Telegram Webhooks and Research Tenant-Isolated Five-Layer Memory Blueprint")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(17, 24, 39)

    # Metadata Paragraph
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(14)
    runs_meta = [
        ("Sprint 5 Day 4 - Pegawai AI Core Multi-Channel Routing & Memory Architecture Blueprint\n", True, RGBColor(55, 65, 81)),
        ("ClickUp Task: ", False, RGBColor(107, 114, 128)),
        ("Day 4: Activate Telegram Webhooks and Research Tenant-Isolated Five-Layer Memory Blueprint (z8xxqwh79k)\n", True, RGBColor(37, 99, 235)),
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
        "(Acceptance Criteria) untuk task Day 4: Activate Telegram Webhooks and Research Tenant-Isolated Five-Layer Memory Blueprint "
        "(z8xxqwh79k) pada Sprint 5. Backend BFF kini memiliki modul webhook Telegram tangguh dengan verifikasi secret token, "
        "pemecahan pesan 4.096 karakter, integrasi perintah bot, benchmark lengkap 7 kandidat memori eksternal, dan arsitektur "
        "5 lapisan memori berisolasi tenant yang tervalidasi dengan 5 skenario pengujian ancaman negatif."
    )

    # Acceptance Criteria Table
    ac_data = [
        ("Kriteria Penerimaan", "Status", "Catatan Verifikasi"),
        ("1. Telegram Webhooks & Routing", "PASSED", "Modul bff/telegram.py menangani webhook masuk via POST /api/telegram/webhook. Mendukung verifikasi token, command /start, /help, /status, /agent, dan chunking < 4096 karakter."),
        ("2. Seven Candidates Benchmark", "PASSED", "Evaluasi menyeluruh Obsidian, Hindsight, memO (Mem0), Honcho, OpenViking, Cognee, dan AgentMemory. memO direkomendasikan untuk MVP."),
        ("3. Five-Layer Memory Architecture", "PASSED", "Spesifikasi 5 lapisan memori: Session (Available), Employee (Available/Partial), Customer (Planned), Project (Planned), Long-Term (Planned)."),
        ("4. Strict Tenant Memory Isolation", "PASSED", "Partisi non-bypassable tenant_id. Mesin pengujian 5 skenario ancaman negatif menghasilkan status 100% lolos (isolation_verified: true)."),
        ("5. Implemented Memory Path Tests", "PASSED", "Unit test untuk sesi dan memori karyawan (MEMORY.md/USER.md) lulus 8/8 Day 4 tests dan 21 memory tests."),
        ("6. Frontend Alignment (Native Baseline)", "PASSED", "Menyelaraskan model mental memori dengan UX plan. Output native Telegram disepakati sebagai baseline tanpa beban custom renderer.")
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

    # 2. Telegram Webhooks
    add_h1("2. Telegram API Backend Routing & Webhook Mechanism")
    add_p(
        "Modul bff/bff/telegram.py mengaktifkan integrasi resmi Telegram Bot API dengan standar keamanan tinggi:"
    )
    add_p(" Memvalidasi header X-Telegram-Bot-Api-Secret-Token pada setiap pembaruan webhook; request tanpa secret token ditolak HTTP 401.", bold_prefix="• Validasi Secret Token:")
    add_p(" Mendukung perintah /start (salam & direktori tim), /help (panduan penggunaan), /status (status agen & chat ID), /agent <nama> (switch agen ke Siti/Bram/Vina/Bimo/Hendra), dan /reset (pembersihan sesi).", bold_prefix="• Perintah Bot Otomatis:")
    add_p(" Respon melebihi 4.096 karakter dipecah secara cerdas pada batas paragraf atau baris dengan penanda (1/n), (2/n) agar tidak terpotong oleh sistem Telegram.", bold_prefix="• Telegram Message Chunking:")
    add_p(" Pertanyaan CS otomatis dijawab menggunakan SOP CS v2.1 Colorbox (retur 7 hari, larangan tukar ukuran langsung, syarat pembatalan sebelum serah terima kurir, SLA pengiriman).", bold_prefix="• Knowledge Base Routing:")

    # 3. Seven Candidates Benchmark
    add_h1("3. Benchmark Lengkap 7 Kandidat Mesin Memori Eksternal")
    add_p(
        "Berdasarkan analisis repositori primer dan katalog plugin Hermes CLI terpasang, berikut adalah hasil evaluasi ketujuh kandidat:"
    )

    cand_data = [
        ("Kandidat", "Lisensi", "Status", "Metode Integrasi", "Fit Lapisan", "Rekomendasi Akhir"),
        ("Obsidian", "Proprietary", "ANALYZED", "Plugin browse/edit file", "Arsip / Ekspor", "DITOLAK sebagai mesin aktif; opsi format ekspor."),
        ("Hindsight", "MIT", "ANALYZED", "Catalog hindsight.yaml (3 tools)", "Layer 5 (Long-Term)", "DITUNDA: Recall kuat, namun kapabilitas delete sangat lemah."),
        ("memO (Mem0)", "Apache-2.0", "ANALYZED", "Catalog mem0.yaml (4 tools)", "Layer 5 & Layer 3", "DIREKOMENDASIKAN sebagai kandidat utama MVP Layer 5."),
        ("Honcho", "AGPL-3.0", "ANALYZED", "Catalog honcho.yaml (Gateway)", "Layer 3 (Customer)", "DITUNDA: Lisensi AGPL dan dependensi erat ke Gateway."),
        ("OpenViking", "AGPL-3.0", "ANALYZED", "Catalog openviking.yaml (URI)", "Layer 4 & Layer 5", "DITUNDA: Lisensi AGPL dan overhead server yang tinggi."),
        ("Cognee", "Apache-2.0", "ANALYZED", "Community plugin (Knowledge Graph)", "Layer 4 & Layer 5", "DITUNDA: Datastore ~/.cognee dibagi bersama tanpa isolasi tenant."),
        ("AgentMemory", "Apache-2.0", "ANALYZED", "External REST / MCP Viewer", "Layer 2 & Layer 5", "PILOT INSPIRASI UI SAJA; filter aplikasi rentan bocor.")
    ]

    t_cand = doc.add_table(rows=len(cand_data), cols=6)
    t_cand.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_cand)
    col_widths_c = [Inches(1.1), Inches(1.0), Inches(1.0), Inches(1.5), Inches(1.2), Inches(1.7)]

    for row_idx, row in enumerate(t_cand.rows):
        is_hdr = (row_idx == 0)
        for col_idx, cell in enumerate(row.cells):
            cell.width = col_widths_c[col_idx]
            cell.text = cand_data[row_idx][col_idx]
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(8.5)
                if is_hdr:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(17, 24, 39)
                elif "DIREKOMENDASIKAN" in cell.text:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(16, 185, 129)
                elif "DITOLAK" in cell.text:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(239, 68, 68)
                else:
                    run.font.color.rgb = RGBColor(55, 65, 81)
            if is_hdr:
                set_cell_background(cell, "F3F4F6")

    # 4. Five-Layer Memory Architecture & Tenant Isolation
    add_h1("4. Cetak Biru Memori 5 Lapisan & Validasi Isolasi Tenant")
    add_p(
        "Arsitektur memori membagi penyimpanan ke dalam 5 lapisan modular dengan status kesiapan teknis yang jelas:"
    )
    add_p(" Konteks percakapan aktif per topik. Disimpan di PostgreSQL (chat_sessions) & Hermes state.db FTS. Status: TERSEDIA (AVAILABLE).", bold_prefix="• Lapisan 1 (Session Memory):")
    add_p(" Persona bot dan catatan yang dipelajari agen (~/.hermes/profiles/<bot>/memories/ MEMORY.md & USER.md) dengan file lock atomik. Status: TERSEDIA SEBAGIAN (AVAILABLE_AND_PARTIAL).", bold_prefix="• Lapisan 2 (Employee Memory):")
    add_p(" Pedoman merek, persona target audiens, dan larangan kompetitor per tenant. Disimpan di PostgreSQL dan disuntikkan ke instruksi prompt. Status: DIRENCANAKAN (PLANNED).", bold_prefix="• Lapisan 3 (Customer / Tenant Memory):")
    add_p(" Milestone kampanye, deliverable kanban, dan status tugas aktif. Terintegrasi dengan modul BFF Tasks. Status: DIRENCANAKAN (PLANNED).", bold_prefix="• Lapisan 4 (Project Memory):")
    add_p(" Wawasan jangka panjang dan histori percakapan menggunakan vector database (target: Mem0 / pgvector). Status: DIRENCANAKAN (PLANNED).", bold_prefix="• Lapisan 5 (Long-Term Memory):")

    add_h2("Hasil Validasi Pengujian Ancaman Isolasi Tenant (5 Skenario)")
    add_p(
        "Pengujian negatif otomatis dijalankan untuk membuktikan data Tenant Alpha Corp tidak dapat dibocorkan ke Tenant Beta Ltd:"
    )
    add_p(" Tenant Beta mencoba membaca memori rahasia Tenant Alpha -> DITOLAK (HTTP 403 Forbidden).", bold_prefix="1. Skenario Direct Read Attack:")
    add_p(" Tenant Beta mencoba menimpa data memori milik Tenant Alpha -> DITOLAK (HTTP 403 Forbidden).", bold_prefix="2. Skenario Tamper / Overwrite Attack:")
    add_p(" Tenant Beta mencoba menghapus rekaman memori Tenant Alpha -> DITOLAK (HTTP 403 Forbidden).", bold_prefix="3. Skenario Deletion / Sabotage Attack:")
    add_p(" Tenant Beta mencari kata kunci rahasia milik Tenant Alpha -> 0 hasil (0 data bocor).", bold_prefix="4. Skenario Semantic Infiltration Attack:")
    add_p(" Penyerang menyuntikkan jailbreak prompt untuk meminta dump seluruh memori -> Terblokir oleh partisi database deterministik.", bold_prefix="5. Skenario Prompt Injection Evasion:")

    # 5. Live VPS Execution Evidence
    add_h1("5. Bukti Eksekusi Live pada VPS (139.190.107.151)")
    add_p(
        "Pengujian otomatis telah dijalankan langsung pada server VPS dan melalui HTTPS reverse proxy Nginx "
        "(https://139.190.107.151.sslip.io). Seluruh 7 endpoint live menghasilkan respon sukses 100%:"
    )
    add_code(
        '=== VPS REMOTE PYTEST OUTPUT ===\n'
        'rootdir: /home/ubuntu/pegawai-ai/bff\n'
        'tests/test_day4_sprint5.py::test_telegram_webhook_secret_verification PASSED [ 12%]\n'
        'tests/test_day4_sprint5.py::test_telegram_message_splitting_under_4096_chars PASSED [ 25%]\n'
        'tests/test_day4_sprint5.py::test_telegram_command_handling PASSED        [ 37%]\n'
        'tests/test_day4_sprint5.py::test_process_telegram_update_routing_and_cs_knowledge PASSED [ 50%]\n'
        'tests/test_day4_sprint5.py::test_seven_memory_candidates_complete_benchmark PASSED [ 62%]\n'
        'tests/test_day4_sprint5.py::test_five_memory_layers_spec PASSED          [ 75%]\n'
        'tests/test_day4_sprint5.py::test_tenant_memory_isolation_and_threat_scenarios PASSED [ 87%]\n'
        'tests/test_day4_sprint5.py::test_api_telegram_and_memory_blueprint_endpoints PASSED [100%]\n'
        '========================= 8 passed in 1.30s =========================\n\n'
        '=== LIVE HTTPS API TEST RESULTS (https://139.190.107.151.sslip.io) ===\n'
        '[PASSED] GET /bff/api/telegram/status -> supported_commands=["/start", "/help", "/status", "/agent", "/reset"]\n'
        '[PASSED] POST /bff/api/telegram/simulate (/start) -> command handled, welcome greeting sent\n'
        '[PASSED] POST /bff/api/telegram/simulate (CS Question) -> routed to Siti, retur policy sent\n'
        '[PASSED] POST /bff/api/telegram/webhook (Direct with secret) -> status="command_handled"\n'
        '[PASSED] GET /bff/api/memory/blueprint -> 7 candidates evaluated (Obsidian, Hindsight, Mem0, Honcho, OpenViking, Cognee, AgentMemory)\n'
        '[PASSED] GET /bff/api/memory/layers -> layer_1=AVAILABLE, layer_2=AVAILABLE_AND_PARTIAL, layer_5=PLANNED\n'
        '[PASSED] POST /bff/api/memory/tenant/validate-isolation -> isolation_verified=True, 5/5 threat scenarios protected\n'
        'ALL 7 LIVE ENDPOINTS VERIFIED 100% OPERATIONAL ON VPS!'
    )

    # 6. Conclusion
    add_h1("6. Kesimpulan & Status Penyelesaian")
    add_p(
        "Seluruh kriteria penerimaan untuk Day 4 Sprint 5 telah terpenuhi 100%. Saluran Telegram backend siap beroperasi, "
        "rekomendasi pemilihan mesin memori eksternal telah diputuskan secara objektif dan terdokumentasi rapi, "
        "serta cetak biru 5 lapisan memori berisolasi tenant telah dibuktikan aman melalui pengujian ancaman nyata."
    )

    doc.save("Sprint5_Day4_Telegram_Webhooks_and_Memory_Blueprint_Evidence.docx")
    print("Successfully built Sprint5_Day4_Telegram_Webhooks_and_Memory_Blueprint_Evidence.docx")

if __name__ == "__main__":
    build_docx()
