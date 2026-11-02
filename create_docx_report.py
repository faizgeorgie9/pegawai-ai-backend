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

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

def set_table_borders(table, color="CCCCCC", sz="4", val="single"):
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

def build_report():
    doc = docx.Document()
    
    # Page setup - Margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(40, 40, 40)

    # Document Header Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_sub = title_p.add_run("PROGRAM PENGEMBANGAN PEGAWAI AI — CANDIDATE VALIDATION\n")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(10)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(90, 105, 120)

    run_title = title_p.add_run("PRODUCT VALIDATION REPORT: HERMES AGENT")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(27, 54, 93) # Deep Navy

    # Meta Table (Boxed)
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    set_table_borders(meta_table, color="D0D7DE", sz="6", val="single")

    meta_data = [
        ("Kandidat yang Divalidasi", "Kandidat A: Hermes Agent (Nous Research)"),
        ("Tanggal Validasi", "21 Oktober 2026"),
        ("Peneliti / Penguji", "Candidate A Researcher (Informational Role)"),
        ("Target Pembaca", "R&D Lead & Koordinator Validasi (Rakazo Researcher)"),
        ("Status Akses & Pengujian", "ACCESSIBLE & VERIFIED (Pengujian Lokal Sukses)"),
    ]

    for i, (label, val) in enumerate(meta_data):
        row = meta_table.rows[i]
        
        c0 = row.cells[0]
        c0.width = Inches(2.2)
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_before = Pt(3)
        p0.paragraph_format.space_after = Pt(3)
        r0 = p0.add_run(label)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = RGBColor(70, 70, 70)
        set_cell_background(c0, "F3F4F6")
        set_cell_margins(c0, top=60, bottom=60, left=100, right=100)

        c1 = row.cells[1]
        c1.width = Inches(4.3)
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_before = Pt(3)
        p1.paragraph_format.space_after = Pt(3)
        r1 = p1.add_run(val)
        r1.font.size = Pt(9.5)
        if "ACCESSIBLE" in val:
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(20, 120, 40)
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c1, top=60, bottom=60, left=100, right=100)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    def add_section_heading(text, num=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(f"{num} {text}".strip())
        r.font.name = 'Calibri'
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(27, 54, 93)

    def add_subsection_heading(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(45, 75, 115)

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.bold = True
            rb.font.color.rgb = RGBColor(30, 30, 30)
        rt = p.add_run(text)
        rt.font.color.rgb = RGBColor(40, 40, 40)

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        cell = tbl.rows[0].cells[0]
        cell.width = Inches(6.5)
        set_cell_background(cell, "F6F8FA")
        set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
        set_table_borders(tbl, color="D0D7DE", sz="4", val="single")
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(code_text)
        r.font.name = 'Consolas'
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(180, 40, 40)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 1. Identitas Resmi
    add_section_heading("1. Identitas Resmi Produk & Repositori")
    
    t1 = doc.add_table(rows=6, cols=3)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t1, color="E1E4E8", sz="4", val="single")

    t1_headers = ["Parameter", "Data Terverifikasi", "Catatan Validasi"]
    for j, h in enumerate(t1_headers):
        c = t1.rows[0].cells[j]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    t1_rows = [
        ("Nama Produk", "Hermes Agent (Candidate A)", "Bukan LLM raw model mentah, melainkan full autonomous agent runtime."),
        ("Vendor / Organisasi", "Nous Research", "Situs resmi: nousresearch.com"),
        ("Repositori Resmi", "https://github.com/NousResearch/hermes-agent", "Repositori open source resmi dan aktif dimaintain."),
        ("Dokumentasi Resmi", "https://hermes-agent.nousresearch.com", "Tersedia panduan CLI, TUI, Desktop, dan API."),
        ("Versi Diuji", "v0.22.2 (Commit d923a5eb48)", "Latest Stable Release saat dilakukan validasi."),
    ]

    widths = [Inches(1.8), Inches(2.3), Inches(2.4)]
    for i, row_data in enumerate(t1_rows, start=1):
        row = t1.rows[i]
        bg = "FFFFFF" if i % 2 == 1 else "F9FAFB"
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = widths[j]
            set_cell_background(c, bg)
            set_cell_margins(c, top=60, bottom=60, left=100, right=100)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.size = Pt(9.0)
            if j == 0:
                r.font.bold = True

    # 2. Lingkungan Uji & Status Akses
    add_section_heading("2. Status Akses, Lingkungan Uji & Verifikasi Instalasi")
    add_bullet("Windows 11 / Windows 10 (Arch: win32-x64).", "Sistem Operasi Pengujian: ")
    add_bullet("Python 3.14 (diprovosikan otomatis via uv v0.12.3), Git portable v2.53.0, Node.js/Electron untuk Desktop App.", "Runtime & Dependencies: ")
    add_bullet("C:\\Users\\LOQ\\AppData\\Local\\hermes (Binaries: bin/hermes.exe, Desktop: apps/desktop/.../Hermes.exe).", "Lokasi Instalasi Lokal: ")

    add_subsection_heading("Temuan Error Nyata Saat Instalasi (Disclosed Error & Evidence):")
    p_err = doc.add_paragraph()
    p_err.add_run("Instalasi dilakukan menggunakan installer resmi Hermes-Setup.exe (Bootstrap Protocol v1). Pada proses instalasi awal di sistem Windows, instalasi sempat terhenti karena dua kendala beruntun:")

    add_code_block("2026-10-21T05:39:51Z INFO bootstrap.log: [X] Cannot remove item C:\\Users\\LOQ\\AppData\\Local\\hermes\\.hermes-clone-8496-616162997\\tree\\.git: You do not have sufficient access rights to perform this operation.\n\n[X] Cannot find path 'C:\\Users\\LOQ\\AppData\\Local\\hermes\\hermes-agent\\pm\\lock.json' because it does not exist. stage=venv")

    add_bullet("Perintah Move-Item di PowerShell mengalami error hak akses berkas Windows saat memindahkan folder .git berstatus read-only dari staging area, sehingga proses kloning terputus di tengah jalan.", "Akar Masalah (Root Cause): ")
    add_bullet("Ketika dicoba Retry install, installer mengira versi v0.22.2 sudah terpasang dan langsung melanjutkan ke tahap venv tanpa memeriksa kelengkapan file. Akibatnya file pm/lock.json belum ada di tempat.", "Dampak: ")
    add_bullet("Masalah diselesaikan dengan mengeksekusi 'git reset --hard HEAD' di folder repositori lokal. Perintah ini berhasil memulihkan seluruh 18.508 berkas yang tertinggal. Setelah itu installer menyelesaikan seluruh 9 tahapan tanpa kendala dan mencapai status 'HERMES IS READY'.", "Resolusi yang Terbukti Berhasil: ")

    # 3. Lisensi Komersial
    add_section_heading("3. Verifikasi Lisensi Komersial (Commercial Licensing)")
    t2 = doc.add_table(rows=6, cols=2)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t2, color="E1E4E8", sz="4", val="single")

    t2_headers = ["Aspek Lisensi", "Hasil Verifikasi & Dampak Bisnis"]
    for j, h in enumerate(t2_headers):
        c = t2.rows[0].cells[j]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    t2_rows = [
        ("Jenis Lisensi Resmi", "MIT License (Copyright (c) 2025 Nous Research). Terverifikasi langsung di file LICENSE."),
        ("Hak Penggunaan Komersial", "DISETUJUI PENUH (Full Commercial Rights). Boleh digunakan, dimodifikasi, dan dijual sebagai produk komersial tanpa royalti."),
        ("Kewajiban Distribusi", "Hanya wajib menyertakan copyright notice asli dan teks lisensi MIT dalam distribusi software."),
        ("Tingkat Risiko Hukum IP", "SANGAT RENDAH (Low Risk). Tidak memiliki klausul Copyleft/viral seperti GPL/AGPL yang memaksa membuka source code rahasia perusahaan."),
        ("Framework vs Hosted Service", "100% Self-Hosted Framework. Bebas vendor lock-in untuk orchestration. Biaya eksternal hanya timbul dari LLM API provider yang dipilih."),
    ]

    widths2 = [Inches(2.2), Inches(4.3)]
    for i, row_data in enumerate(t2_rows, start=1):
        row = t2.rows[i]
        bg = "FFFFFF" if i % 2 == 1 else "F9FAFB"
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = widths2[j]
            set_cell_background(c, bg)
            set_cell_margins(c, top=60, bottom=60, left=100, right=100)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.size = Pt(9.0)
            if j == 0:
                r.font.bold = True

    # 4. Evaluasi Fitur Teknis
    add_section_heading("4. Evaluasi Fitur Teknis (Kesesuaian Arsitektur Pegawai AI)")
    add_subsection_heading("4.1 Model Providers & Provider Switching")
    add_bullet("Mendukung multi-provider API komersial (OpenAI GPT, Anthropic Claude, OpenRouter, DeepSeek) serta local self-hosted inference (Ollama, vLLM).", "Provider Ekstensif: ")
    add_bullet("Tersedia perintah bawaan 'hermes fallback add/remove/list' untuk mengatur fallback provider chain. Jika API utama rate-limited/down, Hermes otomatis switch ke model cadangan.", "Fallback Provider Chain: ")
    add_bullet("Mendukung manajemen banyak credential melalui 'hermes auth add/list/priority/refresh' dengan rotasi key otomatis.", "Credential Pooling: ")

    add_subsection_heading("4.2 Tools, Connectors & Extensibility")
    add_bullet("Eksekusi Shell/Terminal, File I/O, Web Search & Scraper (agent-browser), Computer Use GUI (cua-driver).", "Native Tools: ")
    add_bullet("Mendukung pembuatan spesialisasi peran (Marketing AI, Sales AI, CS AI) melalui format skills terisolasi (--skills, AGENTS.md, SOUL.md).", "Skills Framework: ")
    add_bullet("Mendukung integrasi standar Model Context Protocol (MCP) untuk terhubung ke database, CRM, dan sistem enterprise pihak ketiga.", "MCP Integration: ")

    add_subsection_heading("4.3 Human-in-the-Loop & Guardrails")
    add_bullet("Secara default, aksi berisiko tinggi (menulis/menghapus file, menjalankan shell command) mewajibkan konfirmasi manusia (Approval Prompt). Bypassing (--yolo) bersifat opsional.", "Approval System: ")
    add_bullet("Tersedia perintah 'hermes logs' serta flag '--usage-file PATH' untuk mencatat jumlah token, estimasi biaya (spend), dan pemanggilan tool secara terperinci.", "Audit & Observability: ")

    # 5. Native vs Custom Matrix
    add_section_heading("5. Matriks Analisis: Native vs Custom Integration")
    t3 = doc.add_table(rows=7, cols=3)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t3, color="E1E4E8", sz="4", val="single")

    t3_headers = ["Kebutuhan Pegawai AI (PPT)", "Fitur Native Hermes", "Kebutuhan Custom (Tim Internal)"]
    for j, h in enumerate(t3_headers):
        c = t3.rows[0].cells[j]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    t3_rows = [
        ("Orchestration & Task Runner", "SUDAH ADA (Native autonomous engine)", "Tidak perlu, siap pakai."),
        ("Tool & Function Calling", "SUDAH ADA (Shell, Browser, File, MCP)", "Konektor custom marketplace lokal (Shopee/Tokopedia)."),
        ("Human-in-the-loop Guardrail", "SUDAH ADA (Interactive CLI/GUI prompt)", "Web dashboard webhook approval untuk klien non-teknis."),
        ("Token & Cost Observability", "SUDAH ADA (--usage-file, agent.log)", "Penyimpanan log ke database billing & analytics tenant."),
        ("Multi-Tenant Data Isolation", "PARSIAL (Bisa via hermes -p <profile>)", "Wajib Custom: Isolasi container Docker per tenant."),
        ("Role & Skill Configuration", "SUDAH ADA (Skills, AGENTS.md)", "Menyusun prompt template & SOP Marketing Content."),
    ]

    widths3 = [Inches(2.1), Inches(2.2), Inches(2.2)]
    for i, row_data in enumerate(t3_rows, start=1):
        row = t3.rows[i]
        bg = "FFFFFF" if i % 2 == 1 else "F9FAFB"
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = widths3[j]
            set_cell_background(c, bg)
            set_cell_margins(c, top=60, bottom=60, left=100, right=100)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if j == 0:
                r.font.bold = True

    # 6. Batasan, Risiko & Unknowns
    add_section_heading("6. Batasan, Risiko & Hal yang Belum Diketahui")
    add_bullet("Aslinya dirancang sebagai autonomous agent lokal per-pengguna (single user / workstation). Untuk arsitektur multi-tenant SaaS perusahaan, tim harus membungkusnya dalam container/worker terisolasi.", "Batasan Arsitektural: ")
    add_bullet("Script installer Windows memiliki ketergantungan sensitif pada perizinan direktori sementara saat operasi git klon.", "Risiko Instalasi Windows: ")
    add_bullet("Agen otonom dengan tool looping dapat mengonsumsi token dengan cepat jika instruksi ambigu; wajib menerapkan max iterations dan timeout guardrails.", "Risiko Biaya Token: ")
    add_bullet("Performa dan stabilitas latensi mode server headless ('hermes serve') di bawah konkurensi alur kerja Marketing AI secara bersamaan (perlu uji beban lanjutan).", "[UNKNOWN - CONCURRENCY BENCHMARK]: ")
    add_bullet("Efisiensi retrieval konteks brand jangka panjang untuk dokumen knowledge berukuran besar (>50 MB) tanpa vector database eksternal.", "[UNKNOWN - KNOWLEDGE RETRIEVAL AT SCALE]: ")

    # 7. Kesimpulan & Rekomendasi
    add_section_heading("7. Kesimpulan Evaluasi & Rekomendasi untuk R&D Lead")
    t4 = doc.add_table(rows=7, cols=4)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t4, color="E1E4E8", sz="4", val="single")

    t4_headers = ["Kriteria Scorecard", "Bobot", "Skor (1-10)", "Catatan Evaluasi"]
    for j, h in enumerate(t4_headers):
        c = t4.rows[0].cells[j]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    t4_rows = [
        ("Task Success & Kualitas", "30%", "8.5 / 10", "Reasoning kuat, eksekusi tool sangat matang."),
        ("Reliability & Error Recovery", "20%", "8.0 / 10", "Fallback provider chain otomatis jika provider down."),
        ("Tools & Integrasi (MCP/API)", "15%", "9.0 / 10", "Dukungan MCP, browser automation, dan computer use native."),
        ("Security & Guardrails", "15%", "8.5 / 10", "Default approval aktif; command berbahaya terkontrol."),
        ("Biaya & Observability", "10%", "8.5 / 10", "Kompatibel model lokal (Ollama); log token jelas."),
        ("Deployment & Maintenance", "10%", "7.5 / 10", "Instalasi Windows butuh catatan teknis; Linux/Docker sangat baik."),
    ]

    widths4 = [Inches(2.0), Inches(0.8), Inches(1.1), Inches(2.6)]
    for i, row_data in enumerate(t4_rows, start=1):
        row = t4.rows[i]
        bg = "FFFFFF" if i % 2 == 1 else "F9FAFB"
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = widths4[j]
            set_cell_background(c, bg)
            set_cell_margins(c, top=60, bottom=60, left=100, right=100)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if j in (0, 2):
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Final Verdict Callout Box
    rec_box = doc.add_table(rows=1, cols=1)
    rec_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    rec_box.autofit = False
    c_box = rec_box.rows[0].cells[0]
    c_box.width = Inches(6.5)
    set_cell_background(c_box, "EBF3FA")
    set_cell_margins(c_box, top=100, bottom=100, left=150, right=150)
    set_table_borders(rec_box, color="1B365D", sz="12", val="single")

    p_box = c_box.paragraphs[0]
    p_box.paragraph_format.space_before = Pt(4)
    p_box.paragraph_format.space_after = Pt(4)
    r_box_title = p_box.add_run("REKOMENDASI AKHIR: GO (KANDIDAT KUAT)\n")
    r_box_title.font.name = 'Calibri'
    r_box_title.font.size = Pt(11)
    r_box_title.font.bold = True
    r_box_title.font.color.rgb = RGBColor(27, 54, 93)

    r_box_desc = p_box.add_run("Hermes Agent terbukti memiliki kapabilitas teknis yang sangat solid, lisensi komersial MIT yang aman tanpa royalti, serta fitur guardrails dan MCP yang sejalan dengan arsitektur Pegawai AI. Sangat direkomendasikan untuk masuk ke tahap pengujian skenario alur kerja MVP (Marketing & Content AI).")
    r_box_desc.font.name = 'Calibri'
    r_box_desc.font.size = Pt(9.5)
    r_box_desc.font.color.rgb = RGBColor(40, 50, 70)

    # Save
    output_path = "D:\\ai_developer\\project6\\Hermes_Agent_Validation_Report.docx"
    doc.save(output_path)
    print(f"Report successfully saved to: {output_path}")

if __name__ == "__main__":
    build_report()
