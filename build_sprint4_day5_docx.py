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
    
    # Margins 1 inch
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # Document Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("Evidence & Stability Report: Stabilize Backend Integrations and Finalize MVP Deployment Documentation")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(17)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(17, 24, 39)

    # Subtitle / Metadata
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(14)
    runs_meta = [
        ("Sprint 4 Day 5 - Pegawai AI MVP Final Backend Release\n", True, RGBColor(55, 65, 81)),
        ("ClickUp Task: ", False, RGBColor(107, 114, 128)),
        ("Stabilize Backend Integrations and Finalize MVP Deployment Documentation (z8xxqwfknf)\n", True, RGBColor(37, 99, 235)),
        ("Parent Epic: ", False, RGBColor(107, 114, 128)),
        ("BE: Hermes Core, VPS, Costing & Backend Integrations (z8xxqwfkga)\n", True, RGBColor(31, 41, 55)),
        ("Assignee: ", False, RGBColor(107, 114, 128)),
        ("Faiz Febriawan (faiz86791@gmail.com)\n", False, RGBColor(17, 24, 39)),
        ("Production Environment: ", False, RGBColor(107, 114, 128)),
        ("Ubuntu 22.04 LTS (https://139.190.107.151.sslip.io/)\n", True, RGBColor(16, 185, 129)),
        ("Date: ", False, RGBColor(107, 114, 128)),
        ("November 18, 2026  |  Final Status: COMPLETED (100% Passed & Verified)\n", True, RGBColor(5, 150, 105))
    ]
    for text, bold, color in runs_meta:
        r = meta_p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
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
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(30, 41, 59)

    # 1. Executive Summary
    add_h1("1. Executive Summary & Kriteria Penerimaan (Acceptance Criteria)")
    add_p(
        "Dokumen ini menyajikan bukti komprehensif atas penyelesaian task final Sprint 4 Day 5 "
        "(Stabilize Backend Integrations and Finalize MVP Deployment Documentation). "
        "Fase ini bertujuan memastikan stabilitas menyeluruh seluruh komponen backend, integrasi tools pihak ketiga, "
        "gateway WhatsApp Customer Service multi-agent, pemenuhan standar Google OAuth 2.0 (HTTPS FQDN), "
        "serta verifikasi performa live pada server produksi VPS Biznet Gio."
    )

    # Acceptance Criteria Table
    ac_table = doc.add_table(rows=6, cols=3)
    ac_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(ac_table)

    headers = ["Kriteria Penerimaan ClickUp", "Status", "Bukti & Catatan Verifikasi"]
    col_widths = [Inches(2.4), Inches(0.9), Inches(3.2)]

    for i, h_text in enumerate(headers):
        cell = ac_table.rows[0].cells[i]
        cell.width = col_widths[i]
        set_cell_background(cell, "F3F4F6")
        set_cell_margins(cell, top=130, bottom=130, left=150, right=150)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(17, 24, 39)

    rows_data = [
        ("1. Validasi routing backend untuk direct WhatsApp CS integration", "PASSED",
         "Meta Cloud API Webhook (GET/POST /bff/api/whatsapp/webhook) tervalidasi. Perutean cerdas: Frontline L1 Siti (P2-P4) vs Eskalasi L2 Hendra (P1). Web simulator dideploy live di /wa-tester.html."),
        ("2. Penyediaan API third-party tools terpadu untuk FE", "PASSED",
         "Endpoint /bff/api/tools/integrations menyajikan status Google Drive, WhatsApp, dan Hermes Connectors. Katalog 54 aplikasi tools aktif di /bff/api/apps/catalog."),
        ("3. Debug & sinkronisasi BE-FE (Google OAuth HTTPS)", "PASSED",
         "Menyelesaikan Error 400 invalid_request Google OAuth dengan memasang domain 139.190.107.151.sslip.io dan sertifikat SSL resmi Let's Encrypt."),
        ("4. Finalisasi dokumentasi deployment live production", "PASSED",
         "Panduan arsitektur VPS, topologi Nginx HTTPS reverse proxy, systemd daemons, database Neon pgvector, dan security headers terangkum lengkap."),
        ("5. Uji stabilitas menyeluruh & regression testing", "PASSED",
         "257 unit test BFF lulus 100% (pytest). 12/12 live regression test terhadap HTTPS VPS berstatus PASS (100% sukses). Utilisasi RAM rendah (18%).")
    ]

    for row_idx, r_data in enumerate(rows_data, start=1):
        row = ac_table.rows[row_idx]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_margins(cell, top=90, bottom=90, left=150, right=150)
            if col_idx == 1:
                set_cell_background(cell, "DEF7EC")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            if col_idx == 1:
                r.font.bold = True
                r.font.color.rgb = RGBColor(3, 114, 53)
            else:
                r.font.color.rgb = RGBColor(55, 65, 81)

    # 2. Key Hardening & Bug Fixes
    add_h1("2. Perbaikan Kritis & Peningkatan Stabilitas Sistem (Hardening)")
    
    add_h2("2.1. Resolusi Google OAuth 2.0 Policy (Error 400: invalid_request)")
    add_p(
        "Sebelumnya, otentikasi Google Drive menghasilkan 'Error 400: invalid_request' karena redirect URI "
        "berupa alamat IP dengan HTTP plain (http://139.190.107.151/...). Kebijakan keamanan Google strictly melarang "
        "alamat IP dan mewajibkan Fully Qualified Domain Name (FQDN) dengan enkripsi HTTPS."
    )
    add_p(
        "Tindakan Perbaikan yang Dilakukan:", bold_prefix="Solusi: "
    )
    add_p("1. Mengalokasikan FQDN resmi: 139.190.107.151.sslip.io yang memetakan langsung ke IP publik VPS.")
    add_p("2. Menerbitkan sertifikat TLS/SSL resmi Let's Encrypt via Certbot & Nginx plugin.")
    add_p("3. Mengaktifkan Nginx HTTP/2 dan redirect otomatis port 80 (HTTP) -> 443 (HTTPS).")
    add_p("4. Mengupdate PUBLIC_BASE_URL=https://139.190.107.151.sslip.io di server BFF.")
    add_p(
        "Hasil: Callback URI terverifikasi kini compliant dengan Google Cloud Console:\n"
        "https://139.190.107.151.sslip.io/bff/api/connections/google/callback",
        italic=True
    )

    add_h2("2.2. Perbaikan Hermes Apps Catalog (503 Service Unavailable)")
    add_p(
        "Halaman Aplikasi frontend sempat menampilkan pesan peringatan 'Daftar aplikasi belum bisa dimuat. Coba lagi sebentar' (HTTP 503). "
        "Investigasi log systemd menunjukkan eksekusi CLI hermes terhambat oleh wrapper usang di /home/ubuntu/.local/bin/hermes "
        "yang memicu error No module named hermes_cli.cli."
    )
    add_p(
        "Solusi: Melakukan symlink ke binary resmi /usr/local/bin/hermes. Endpoint /bff/api/apps/catalog kini "
        "merespons dengan HTTP 200 OK secara instan, menyajikan 54 aplikasi terintegrasi dalam 10 kategori.",
        bold_prefix="Hasil Perbaikan: "
    )

    add_h2("2.3. Deployment Interactive Web WhatsApp Simulator")
    add_p(
        "Untuk memfasilitasi pengujian langsung tanpa ketergantungan nomor WhatsApp fisik, dibuat simulator interaktif "
        "yang dihosting langsung pada web root VPS: https://139.190.107.151.sslip.io/wa-tester.html. "
        "Simulator ini menyimulasikan pengalaman chatting WhatsApp nyata dengan routing otomatis ke agen Siti (tanya produk) "
        "dan eskalasi ke Hendra (keluhan cacat / refund)."
    )

    # 3. Live VPS Regression Test Table
    add_h1("3. Hasil Pengujian Regresi Komprehensif Live VPS (12/12 PASS)")
    add_p(
        "Pengujian otomatis dijalankan secara langsung via script test_vps_day5_stability.py "
        "terhadap domain produksi https://139.190.107.151.sslip.io:"
    )

    test_table = doc.add_table(rows=13, cols=4)
    test_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(test_table)

    t_headers = ["No", "Skenario Pengujian", "Endpoint / Target", "Hasil Uji Live"]
    t_widths = [Inches(0.4), Inches(2.2), Inches(2.5), Inches(1.4)]

    for i, h_text in enumerate(t_headers):
        cell = test_table.rows[0].cells[i]
        cell.width = t_widths[i]
        set_cell_background(cell, "F3F4F6")
        set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(17, 24, 39)

    test_rows = [
        ("1", "Frontend SPA Root (HTTPS)", "GET /", "PASS (HTTP 200, Vite HTML)"),
        ("2", "Backend Healthcheck", "GET /bff/api/health", "PASS (DB & Hermes True)"),
        ("3", "WhatsApp Gateway Status", "GET /bff/api/whatsapp/status", "PASS (Ready, Siti & Hendra)"),
        ("4", "Meta Webhook Handshake", "GET /bff/api/whatsapp/webhook", "PASS (Echo challenge OK)"),
        ("5", "Meta Inbound Message", "POST /bff/api/whatsapp/webhook", "PASS (Routed to Siti, P3)"),
        ("6", "Komplain Kritis Eskalasi", "POST /bff/api/whatsapp/simulate", "PASS (Routed to Hendra, P1)"),
        ("7", "Unified Tools Overview", "GET /bff/api/tools/integrations", "PASS (4 Tools, HTTPS URI)"),
        ("8", "Hermes Apps Catalog", "GET /bff/api/apps/catalog", "PASS (54 Apps, 10 Kategori)"),
        ("9", "Multi-Agent 7 Profiles", "GET /bff/api/bots", "PASS (7 Agen Lengkap Aktif)"),
        ("10", "Token Costing & Limit", "GET /bff/api/usage", "PASS (USD $0.14 / Limit $15)"),
        ("11", "WhatsApp Web Simulator", "GET /wa-tester.html", "PASS (HTTP 200, Live Web UI)"),
        ("12", "Host OS & Systemd Daemons", "SSH (systemctl is-active)", "PASS (BFF, Hermes, Nginx OK)")
    ]

    for row_idx, r_data in enumerate(test_rows, start=1):
        row = test_table.rows[row_idx]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.width = t_widths[col_idx]
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

    # 4. Production Environment Guide
    add_h1("4. Panduan Deployment Lingkungan Produksi (VPS Guide)")
    add_p(
        "Server VPS dikonfigurasi dengan standar produksi yang mengutamakan keamanan dan kemudahan pemeliharaan:"
    )
    add_p("• Host OS: Ubuntu 22.04 LTS (Kernel Linux 5.15), 4 vCPU, 4GB RAM.")
    add_p("• Web Ingress: Nginx reverse proxy dengan SSL/TLS Let's Encrypt terpasang, auto-renew via certbot systemd timer.")
    add_p("• Header Keamanan & Ingress: Nginx otomatis menginjeksi header internal X-Pegawai-AI-Key dan X-Forwarded-Proto https sehingga backend FastAPI terlindungi dari akses liar.")
    add_p("• Database: Neon Serverless PostgreSQL 16 (koneksi SSL terenkripsi, ekstensi pgvector aktif untuk memori agen).")
    add_p("• Daemons: pegawai-ai-bff.service (Port 8090) dan hermes-gateway.service (Port 8080) berjalan di bawah systemd dengan auto-restart on-failure.")

    # 5. Known Limitations & Recommendations
    add_h1("5. Batasan Sistem (Known Limitations) & Rekomendasi Lanjutan")
    add_p(
        "1. Verifikasi Bisnis Meta Cloud API: Integrasi webhook Meta pada backend telah 100% tervalidasi. "
        "Untuk peluncuran komersial ke publik, organisasi Colorbox perlu melengkapi verifikasi bisnis di Meta Business Manager "
        "dan mendaftarkan nomor telepon dedicated yang belum pernah terikat akun WhatsApp reguler."
    )
    add_p(
        "2. Custom Branded Domain: FQDN 139.190.107.151.sslip.io saat ini telah menyelesaikan kendala SSL dan Google OAuth. "
        "Sebagai langkah penyempurnaan branding pasca-MVP, tim DevOps dapat mengarahkan DNS CNAME dari domain perusahaan "
        "(misalnya app.colorbox.co.id) ke server VPS."
    )
    add_p(
        "3. Pemantauan Token Budget: Sistem costing multi-agent saat ini telah berfungsi dengan hard limit $15.00/bulan "
        "dan rate card model Gemini 1.5 Flash. Direkomendasikan melakukan reviu berkala atas limit anggaran seiring peningkatan traffic chat pengguna."
    )

    # 6. Conclusion
    add_h1("6. Kesimpulan & Status Akhir")
    add_p(
        "Sprint 4 Day 5 berhasil ditutup dengan pencapaian sempurna. Seluruh integrasi backend telah stabil, "
        "kendala otentikasi Google OAuth dan katalog tools telah teratasi secara tuntas, simulator WhatsApp live "
        "telah beroperasi, dan seluruh rangkaian pengujian regresi mencapai 100% kelulusan. "
        "Platform Pegawai AI dinyatakan siap dan layak untuk dipresentasikan serta memasuki tahap MVP user testing.",
        bold_prefix="Pernyataan Penyelesaian: "
    )

    output_path = "Sprint4_Day5_Backend_Integrations_and_MVP_Deployment_Evidence.docx"
    doc.save(output_path)
    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    build_docx()
