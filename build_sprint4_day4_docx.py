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
    run_title = p_title.add_run("Evidence & Validation Report: Support WhatsApp Routing and Third-Party Tool APIs")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(17, 24, 39)

    # Subtitle / Metadata
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(14)
    runs_meta = [
        ("Sprint 4 Day 4 - Pegawai AI MVP Readiness\n", True, RGBColor(55, 65, 81)),
        ("ClickUp Task: ", False, RGBColor(107, 114, 128)),
        ("Support WhatsApp Routing and Third-Party Tool APIs (z8xxqwfkjf)\n", True, RGBColor(37, 99, 235)),
        ("Assignee: ", False, RGBColor(107, 114, 128)),
        ("Faiz Febriawan (faiz86791@gmail.com)\n", False, RGBColor(17, 24, 39)),
        ("Target VPS: ", False, RGBColor(107, 114, 128)),
        ("Biznet Gio NEO Lite MS 4.4 (139.190.107.151)\n", False, RGBColor(17, 24, 39)),
        ("Date: ", False, RGBColor(107, 114, 128)),
        ("November 18, 2026  |  Status: Completed (Ready for Review)\n", False, RGBColor(16, 185, 129))
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

    def add_code(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.left_indent = Inches(0.2)
        r = p.add_run(text)
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(30, 41, 59)

    # 1. Executive Summary
    add_h1("1. Executive Summary")
    add_p(
        "Laporan ini menyajikan bukti dan validasi implementasi menyeluruh atas task "
        "Support WhatsApp Routing and Third-Party Tool APIs pada Sprint 4 Day 4. "
        "Seluruh kriteria penerimaan yang ditentukan telah berhasil dibangun, diuji, dan dideploy "
        "ke server produksi VPS Biznet Gio (139.190.107.151)."
    )

    # Acceptance Criteria Table
    ac_table = doc.add_table(rows=4, cols=3)
    ac_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(ac_table)

    headers = ["Kriteria Penerimaan ClickUp", "Status", "Bukti / Catatan Verifikasi"]
    col_widths = [Inches(2.5), Inches(0.9), Inches(3.1)]

    hdr_row = ac_table.rows[0]
    for i, h_text in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.width = col_widths[i]
        set_cell_background(cell, "F3F4F6")
        set_cell_margins(cell, top=140, bottom=140, left=160, right=160)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(17, 24, 39)

    rows_data = [
        ("1. Menyediakan endpoint backend & routing untuk pesan masuk WhatsApp CS", "PASSED", 
         "Webhook resmi Meta Cloud API (GET/POST /api/whatsapp/webhook), simulasi (/simulate), dan history (/messages). Routing pintar ke Siti vs Hendra berbasis intent & SOP Colorbox."),
        ("2. Menyiapkan API konektor tools pihak ketiga (Google Drive, Gmail, Notion) untuk Frontend", "PASSED", 
         "Endpoint terpadu GET /api/tools/integrations menyajikan status menyeluruh. Google Drive & Gmail via OAuth 2.0 (Fernet encrypted), Notion via Hermes Connectors."),
        ("3. Sinkronisasi data antara backend dan frontend", "PASSED", 
         "Tipe dan fungsi API terdefinisi di frontend/src/bff.ts. Vite build sukses tanpa galat. 257 unit test BFF lolos (10 test WhatsApp). Terverifikasi live di VPS.")
    ]

    for row_idx, r_data in enumerate(rows_data, start=1):
        row = ac_table.rows[row_idx]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_margins(cell, top=100, bottom=100, left=160, right=160)
            if col_idx == 1:
                set_cell_background(cell, "DEF7EC")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if col_idx == 1:
                r.font.bold = True
                r.font.color.rgb = RGBColor(3, 114, 53)
            else:
                r.font.color.rgb = RGBColor(55, 65, 81)

    # 2. Routing Matrix
    add_h1("2. Matriks Klasifikasi Intent & Routing WhatsApp CS")
    add_p("Pesan masuk dari pelanggan diklasifikasikan secara otomatis oleh mesin NLP/pattern matching internal BFF:")

    matrix_table = doc.add_table(rows=6, cols=5)
    matrix_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(matrix_table)

    m_headers = ["Kategori", "Keyword Pemicu", "Intent", "Prioritas", "Agen CS"]
    m_widths = [Inches(1.3), Inches(2.0), Inches(1.3), Inches(0.8), Inches(1.1)]

    for i, h_text in enumerate(m_headers):
        cell = matrix_table.rows[0].cells[i]
        cell.width = m_widths[i]
        set_cell_background(cell, "F3F4F6")
        set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(17, 24, 39)

    m_rows = [
        ("Info Produk", "liunic, tote bag, ecru, baju, dress", "PRODUCT_INFO", "P3", "Siti (Frontline)"),
        ("Ukuran / Fit", "size, ukuran, muat bb, lingkar dada, ld", "SIZE_FIT", "P3", "Siti (Frontline)"),
        ("Pengiriman", "resi, lacak, kurir, jne, jnt, kirim", "SHIPPING_DELIVERY", "P3", "Siti (Frontline)"),
        ("Barang Cacat", "robek, cacat, bolong, sobek, kotor", "COMPLAINT_DAMAGED", "P1", "Hendra (CS Lead)"),
        ("Retur / Refund", "retur, return, refund, tukar barang", "RETURN_REFUND", "P1", "Hendra (CS Lead)")
    ]

    for row_idx, r_data in enumerate(m_rows, start=1):
        row = matrix_table.rows[row_idx]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.width = m_widths[col_idx]
            set_cell_margins(cell, top=90, bottom=90, left=140, right=140)
            if col_idx == 3 and text == "P1":
                set_cell_background(cell, "FDE8E8")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            if col_idx == 3 and text == "P1":
                r.font.bold = True
                r.font.color.rgb = RGBColor(155, 28, 28)
            else:
                r.font.color.rgb = RGBColor(55, 65, 81)

    # 3. Live Endpoints Evidence
    add_h1("3. Bukti Pengujian Live di Server VPS (139.190.107.151)")
    
    add_h2("3.1. WhatsApp Gateway Status (GET /bff/api/whatsapp/status)")
    add_code(
        '{\n'
        '  "channel": "WhatsApp Business Cloud API",\n'
        '  "status": "ready",\n'
        '  "mode": "live_webhook_and_simulation",\n'
        '  "webhook_url": "http://139.190.107.151/bff/api/whatsapp/webhook",\n'
        '  "primary_agent": { "id": "siti", "name": "Siti", "role": "Frontline Support Specialist" },\n'
        '  "escalation_agent": { "id": "hendra", "name": "Hendra", "role": "CS Team Lead & Quality Auditor" },\n'
        '  "total_messages_processed": 4\n'
        '}'
    )

    add_h2("3.2. Webhook Inbound Meta Cloud Format -> Siti (POST /bff/api/whatsapp/webhook)")
    add_p("Pesan masuk dari Citra Lestari menanyakan koleksi Liunic tote bag ecru dijawab ramah oleh Siti:")
    add_code(
        '{\n'
        '  "id": "354a8cd9-1926-4ca4-96c3-36615c4a7a20",\n'
        '  "sender": "6281234567890",\n'
        '  "customer_name": "Citra Lestari",\n'
        '  "routed_bot": "siti",\n'
        '  "intent": "PRODUCT_INFO",\n'
        '  "priority": "P3",\n'
        '  "status": "replied",\n'
        '  "reply": "Halo Citra Lestari! Terima kasih sudah menghubungi WhatsApp resmi Colorbox Indonesia... Siti siap membantu dengan senang hati!"\n'
        '}'
    )

    add_h2("3.3. Simulasi Komplain Berat -> Eskalasi Hendra (POST /bff/api/whatsapp/simulate)")
    add_p("Pesan komplain barang robek dari Dimas Saputra otomatis dieskalasi ke CS Lead Hendra dengan prioritas P1 dan meminta video unboxing sesuai SOP:")
    add_code(
        '{\n'
        '  "id": "9d1cb546-3411-476e-a795-058b286a9818",\n'
        '  "sender": "6289876543210",\n'
        '  "customer_name": "Dimas Saputra",\n'
        '  "routed_bot": "hendra",\n'
        '  "intent": "COMPLAINT_DAMAGED",\n'
        '  "priority": "P1",\n'
        '  "status": "escalated",\n'
        '  "reply": "Halo Dimas Saputra, saya Hendra selaku Customer Service Team Lead Colorbox Indonesia. Sesuai SOP Penjaminan Kualitas Colorbox, kami akan bertanggung jawab penuh. Mohon bantuannya untuk melampirkan foto barcode tag produk dan video unboxing singkat..."\n'
        '}'
    )

    add_h2("3.4. Third-Party Tools Unified Overview (GET /bff/api/tools/integrations)")
    add_code(
        '{\n'
        '  "tools": [\n'
        '    { "id": "gdrive", "name": "Google Drive", "type": "oauth", "configured": true, "status": "disconnected" },\n'
        '    { "id": "gmail", "name": "Gmail", "type": "oauth", "configured": true, "status": "disconnected" },\n'
        '    { "id": "notion", "name": "Notion", "type": "connector", "configured": true, "status": "not_connected" },\n'
        '    { "id": "whatsapp", "name": "WhatsApp Business", "type": "webhook", "configured": true, "status": "ready" }\n'
        '  ]\n'
        '}'
    )

    # 4. Unit Test Suite
    add_h1("4. Pengujian Otomatis (Pytest Suite)")
    add_p(
        "Seluruh fungsionalitas diuji melalui test suite bff/tests/test_whatsapp.py. "
        "Hasil pengujian mencatat 10/10 test cases lulus 100% tanpa kegagalan:"
    )
    add_code(
        'bff/tests/test_whatsapp.py::test_whatsapp_status_endpoint PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_webhook_verification_success PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_webhook_verification_forbidden PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_webhook_inbound_product_info PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_simulate_size_fit PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_simulate_shipping PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_simulate_damaged_complaint_escalation PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_simulate_return_refund_escalation PASSED\n'
        'bff/tests/test_whatsapp.py::test_whatsapp_messages_history PASSED\n'
        'bff/tests/test_whatsapp.py::test_tools_integrations_overview PASSED\n\n'
        '======================== 10 passed in 1.48s ========================'
    )

    # 5. Conclusion
    add_h1("5. Kesimpulan")
    add_p(
        "Seluruh kriteria penerimaan untuk Day 4 telah terpenuhi secara penuh. "
        "Sistem routing WhatsApp terbukti responsif dan patuh terhadap SOP Colorbox, "
        "konektor integrasi tools pihak ketiga siap dikonsumsi oleh antarmuka frontend, "
        "dan deployment produksi pada VPS telah terverifikasi secara langsung.",
        bold_prefix="Status Akhir: "
    )

    doc.save("Sprint4_Day4_WhatsApp_Routing_and_Tools_Evidence.docx")
    print("Successfully built Sprint4_Day4_WhatsApp_Routing_and_Tools_Evidence.docx")

if __name__ == "__main__":
    build_docx()
