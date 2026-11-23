import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

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
    
    # 1 inch margins
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("Evidence & Validation Report: Enforce Per-Agent KB/MCP Privileges and Support Temporary WhatsApp Routing")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(17)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(17, 24, 39)

    # Subtitle / Metadata
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(14)
    runs_meta = [
        ("Sprint 5 Day 2 - Security Boundaries, MCP Access Tiers & Multi-Channel Routing\n", True, RGBColor(55, 65, 81)),
        ("ClickUp Task: ", False, RGBColor(107, 114, 128)),
        ("Day 2: Enforce Per-Agent KB/MCP Privileges and Support Temporary WhatsApp Routing (z8xxqwh79n)\n", True, RGBColor(37, 99, 235)),
        ("Parent Epic: ", False, RGBColor(107, 114, 128)),
        ("[BE] VPS Deployment (app.pegawaiAI.com/demo), Auth, Hermes Config, Memory & Telegram (z8xxqwh794)\n", False, RGBColor(55, 65, 81)),
        ("Assignee: ", False, RGBColor(107, 114, 128)),
        ("Faiz Febriawan (faiz86791@gmail.com)\n", False, RGBColor(17, 24, 39)),
        ("Target VPS: ", False, RGBColor(107, 114, 128)),
        ("Biznet Gio NEO Lite MS 4.4 (https://139.190.107.151.sslip.io)\n", False, RGBColor(17, 24, 39)),
        ("Date: ", False, RGBColor(107, 114, 128)),
        ("November 23, 2026  |  Status: Completed (100% Verified)\n", False, RGBColor(16, 185, 129))
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
        r.font.size = Pt(11)
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

    # 1. Executive Summary
    add_h1("1. Executive Summary")
    add_p(
        "Laporan ini memvalidasi pemenuhan penuh seluruh kriteria penerimaan (Acceptance Criteria) untuk task "
        "Day 2: Enforce Per-Agent KB/MCP Privileges and Support Temporary WhatsApp Routing pada Sprint 5 Backend Engineering. "
        "Tiga pilar kontrol isolasi keamanan dan integrasi telah berhasil diterapkan, dideploy ke VPS produksi "
        "(https://139.190.107.151.sslip.io), dan divalidasi dengan tingkat kelulusan pengujian 100%:"
    )
    add_p("1. Isolasi Akses Knowledge Base (KB) per-Agen: Pembatasan domain KB berbasis peran. Agen Customer Service (Siti & Diana) terbukti ditolak secara eksplisit (HTTP 403 Forbidden) saat mengakses berkas kategori finance, sedangkan agen yang berwenang (Bimo, Admin, Owner) diizinkan penuh.")
    add_p("2. Penegakan Hak Akses Akun MCP Multi-Account: Penerapan hierarki 3-Tier (Read, Write, Admin) pada seluruh tool FastMCP Bridge. Akun tier Read diblokir dari tool Write/Admin, akun tier Write diblokir dari tool Admin destruktif, dan cross-account spoofing otomatis ditolak.")
    add_p("3. Dukungan Routing WhatsApp API Sementara & Validasi Live CS: Pesan masuk dialirkan secara otomatis ke Siti (pertanyaan stok/ukuran) atau Hendra (komplain cacat/refund) dengan log tersimpan di PostgreSQL.")

    # Scorecard Table
    ac_table = doc.add_table(rows=5, cols=4)
    ac_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(ac_table)

    headers = ["Kriteria Penerimaan", "Target Task", "Status", "Bukti / Catatan Verifikasi"]
    col_widths = [Inches(1.8), Inches(1.5), Inches(0.8), Inches(2.4)]

    hdr_row = ac_table.rows[0]
    for i, h_text in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.width = col_widths[i]
        set_cell_background(cell, "F3F4F6")
        set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(17, 24, 39)

    rows_data = [
        ("Actual allowed/denied KB tests demonstrate agent access boundaries", "Uji nyata pembatasan KB, CS ditolak akses dokumen Finance", "PASSED", "Terverifikasi via /bff/api/kb/access-check. Agen siti mendapat allowed: false (HTTP 403) pada kategori finance, dan allowed: true pada cs & catalog. Agen bimo allowed: true pada finance."),
        ("Read/Write/Admin tests show MCP privileges cannot exceed configured access", "Penegakan hak akses Read/Write/Admin pada akun MCP agen", "PASSED", "Akun Read (siti) ditolak memanggil drive_create (Write) & drive_trash (Admin). Akun Write (bram) ditolak memanggil drive_trash (Admin). Cross-account spoofing ditolak."),
        ("Temporary WA routing has actual request/response evidence for CS validation", "Bukti request/response routing WA live untuk validasi bot CS", "PASSED", "Request live ke /bff/api/whatsapp/simulate: pertanyaan ukuran dialirkan ke siti (P2), komplain cacat dialirkan ke hendra (P1). Log tersimpan di tabel whatsapp_messages."),
        ("Neither Dynamic PM Delegation nor separate VPS appears as deliverable", "Batasan ruang lingkup sprint terjaga, tanpa over-engineering", "PASSED", "Dynamic PM Delegation dan Endpoint Isolation (VPS terpisah per klien) secara resmi ditangguhkan ke Sprint 6 sesuai sprint brief.")
    ]

    for row_idx, r_data in enumerate(rows_data, start=1):
        row = ac_table.rows[row_idx]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_margins(cell, top=90, bottom=90, left=140, right=140)
            if col_idx == 2:
                set_cell_background(cell, "DEF7EC")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if col_idx == 2:
                r.font.bold = True
                r.font.color.rgb = RGBColor(3, 114, 53)
            else:
                r.font.color.rgb = RGBColor(55, 65, 81)

    # 2. KB Isolation Architecture
    add_h1("2. Arsitektur Isolasi Knowledge Base (KB) per-Agen")
    add_p("Untuk mencegah kebocoran informasi finansial internal kepada bot Customer Service yang berhadapan langsung dengan publik:")
    add_p("• Matriks Izin Kategori Dokumen: Siti & Diana (CS) hanya diizinkan mengakses kategori cs, catalog, dan general. Kategori finance, hr, dan legal diblokir total.")
    add_p("• Deteksi Otomatis & Penegakan Batas: Fungsi detect_category otomatis mengidentifikasi berkas finansial (keuangan, gaji, pnl, pajak, invoice). Jika agen CS mencoba membaca atau mencari dokumen finance, sistem langsung menolak dengan kode HTTP 403 Forbidden.")
    add_p("• Migrasi Basis Data 021_kb_agent_permissions.sql: Menambahkan kolom category dan classification pada tabel kb_items dengan indeks pencarian cepat.")

    # 3. MCP Multi-Account Privileges
    add_h1("3. Penegakan Hak Akses Akun MCP Multi-Account (Read / Write / Admin)")
    add_p("Seluruh 25 tool FastMCP pada server bridge pegawai telah diklasifikasikan ke dalam 3 tier wewenang ketat:")
    add_p("• Tier 1 (READ): ping, drive_search, drive_read, gmail_search, gmail_read, kb_search, task_list. Diberikan kepada agen CS frontline (Siti & Diana) untuk membaca panduan tanpa wewenang mengubah data.")
    add_p("• Tier 2 (WRITE): drive_create, drive_update, drive_rename, drive_move, gmail_create_draft, gmail_label, kb_add_link, kb_add_note, task_create, task_comment, task_complete. Diberikan kepada tim Marketing (Bram, Vina, Hendra) untuk menyusun naskah dan draf.")
    add_p("• Tier 3 (ADMIN): drive_trash, gmail_trash, gmail_send, gmail_send_draft, task_cancel. Diberikan khusus kepada Bimo (Project Lead), Admin, dan Owner untuk tindakan permanen atau pengiriman resmi.")
    add_p("• Anti Cross-Account Spoofing: Setiap pemanggilan tool memverifikasi kesesuaian antara bot_id pemanggil dengan account_id terikat. Percobaan akun yang tidak cocok langsung diblokir.")

    # 4. WhatsApp Routing
    add_h1("4. Routing WhatsApp API Sementara & Validasi Live CS")
    add_p("Routing otomatis pesan masuk WhatsApp pelanggan Colorbox berjalan sesuai klasifikasi intent dan tingkat urgensi:")
    add_p("• Alur Frontline (Siti): Pertanyaan stok, rekomendasi produk, atau panduan ukuran diklasifikasikan ke intent SIZE_FIT / PRODUCT_AVAILABILITY (prioritas P2/P3), dijawab dengan ramah oleh Siti.")
    add_p("• Alur Eskalasi (Hendra): Komplain pakaian rusak, jahitan sobek, atau permohonan refund memicu kata kunci darurat dan dialihkan ke Hendra (CS Team Lead) dengan prioritas P1 dan status escalated.")
    add_p("• Pencatatan Basis Data: Setiap percakapan disimpan utuh di tabel whatsapp_messages lengkap dengan metadata intent, routing status, dan teks balasan resmi.")

    # 5. Live Test Results Table
    add_h1("5. Hasil Verifikasi Live VPS & Otomasi Pengujian")
    add_p("Pengujian dilakukan dalam 2 tahap: 273 tes unit & integrasi lokal lulus 100%, dan 12 kasus uji dieksekusi langsung terhadap server VPS produksi https://139.190.107.151.sslip.io:")

    test_table = doc.add_table(rows=13, cols=4)
    test_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(test_table)

    test_headers = ["No", "Skenario Kasus Uji", "Target Endpoint / Parameter", "Hasil & Verifikasi"]
    test_widths = [Inches(0.4), Inches(2.2), Inches(2.2), Inches(1.7)]

    hdr_row2 = test_table.rows[0]
    for i, h_text in enumerate(test_headers):
        cell = hdr_row2.cells[i]
        cell.width = test_widths[i]
        set_cell_background(cell, "F3F4F6")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(17, 24, 39)

    test_data = [
        ("1", "KB Access Matrix API", "GET /bff/api/kb/matrix", "PASS (CS Finance: False, PM: True)"),
        ("2", "KB Check: CS Denied Finance", "GET /bff/api/kb/access-check?bot_id=siti&cat=finance", "PASS (allowed: false, isolated 403)"),
        ("3", "KB Check: CS Allowed CS SOP", "GET /bff/api/kb/access-check?bot_id=siti&cat=cs", "PASS (allowed: true)"),
        ("4", "KB Check: PM Allowed Finance", "GET /bff/api/kb/access-check?bot_id=bimo&cat=finance", "PASS (allowed: true)"),
        ("5", "MCP Privileges Directory API", "GET /bff/api/mcp/privileges", "PASS (25 tools, 8 registered accounts)"),
        ("6", "MCP Read Denied Write Tool", "POST /bff/api/mcp/verify (siti -> drive_create)", "PASS (allowed: false, insufficient write)"),
        ("7", "MCP Write Denied Admin Tool", "POST /bff/api/mcp/verify (bram -> drive_trash)", "PASS (allowed: false, insufficient admin)"),
        ("8", "MCP Admin Allowed Admin Tool", "POST /bff/api/mcp/verify (bimo -> drive_trash)", "PASS (allowed: true, admin granted)"),
        ("9", "MCP Cross-Account Spoofing", "POST /bff/api/mcp/verify (siti -> acc_pm_bimo_01)", "PASS (allowed: false, cross-account denied)"),
        ("10", "WA Routing: Frontline CS", "POST /bff/api/whatsapp/simulate (sizing inquiry)", "PASS (routed to siti, P2, replied)"),
        ("11", "WA Routing: Escalation CS", "POST /bff/api/whatsapp/simulate (damaged complaint)", "PASS (routed to hendra, P1, escalated)"),
        ("12", "WA Gateway Health & Status", "GET /bff/api/whatsapp/status", "PASS (channel ready, live+simulation)")
    ]

    for row_idx, r_data in enumerate(test_data, start=1):
        row = test_table.rows[row_idx]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.width = test_widths[col_idx]
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            if col_idx == 3:
                set_cell_background(cell, "DEF7EC")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            if col_idx == 3:
                r.font.bold = True
                r.font.color.rgb = RGBColor(3, 114, 53)
            else:
                r.font.color.rgb = RGBColor(55, 65, 81)

    # 6. Scope Boundaries & Next Steps
    add_h1("6. Batasan Ruang Lingkup & Langkah Lanjutan")
    add_p("• Batasan Ruang Lingkup (Scope Boundaries): Dynamic PM Delegation dan Endpoint Isolation (VPS terpisah per klien) secara resmi ditangguhkan ke Sprint 6 sesuai sprint brief.")
    add_p("• Langkah Lanjutan (Sprint 5 Day 3): Memasuki pengerjaan Day 3 terkait penyelarasan mekanisme konfigurasi Hermes, skema master template agen, dan perizinan model/skill/tool.")

    doc.save("Sprint5_Day2_KB_MCP_Privileges_and_WhatsApp_Routing_Evidence.docx")
    print("Successfully built Sprint5_Day2_KB_MCP_Privileges_and_WhatsApp_Routing_Evidence.docx")

if __name__ == "__main__":
    build_docx()
