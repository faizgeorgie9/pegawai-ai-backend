import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import markdown

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
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

def build_docx():
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Title
    p_t = doc.add_paragraph()
    r_sub = p_t.add_run("PROGRAM PENGEMBANGAN PEGAWAI AI — TASK 2 DELIVERABLE\n")
    r_sub.font.bold = True
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = RGBColor(90, 105, 120)

    r_title = p_t.add_run("HERMES AGENT: SETUP GUIDE & SMOKE TEST EVIDENCE")
    r_title.font.bold = True
    r_title.font.size = Pt(18)
    r_title.font.color.rgb = RGBColor(27, 54, 93)

    # Metadata Box
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_table, color="D0D7DE", sz="6", val="single")

    meta_data = [
        ("Kandidat & Versi", "Candidate A: Hermes Agent v0.22.2 (Nous Research)"),
        ("Tanggal Eksekusi", "23 Oktober 2026"),
        ("Pelaksana Evaluasi", "Candidate A Researcher"),
        ("Status Smoke Test", "PASSED & VERIFIED (Seluruh Uji Coba Berhasil)"),
        ("Status Keamanan", "ZERO SECRET LEAK (Menggunakan Safe Config & .env.example)"),
    ]

    for i, (label, val) in enumerate(meta_data):
        row = meta_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width, c1.width = Inches(2.2), Inches(4.3)
        set_cell_background(c0, "F3F4F6")
        set_cell_margins(c0, top=60, bottom=60, left=100, right=100)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(label)
        r0.font.bold = True
        r0.font.size = Pt(9.5)

        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c1, top=60, bottom=60, left=100, right=100)
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(val)
        r1.font.size = Pt(9.5)
        if "PASSED" in val or "ZERO" in val:
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(20, 120, 40)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    def add_h(text, size=13):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.bold = True
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(27, 54, 93)

    def add_b(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.bold = True
        p.add_run(text)

    add_h("1. Rangkaian Hasil Pengujian Smoke Test (Evidence-Backed)")
    add_b("Perintah: hermes.exe -z 'Say hello and confirm you are working.' --provider copilot --model gpt-4o\nOutput: 'Hello! I am working and ready to assist.' (Exit Code: 0)", "Test Case 1 (Basic Inference): ")
    add_b("Perintah: hermes.exe -z 'Create a file named smoke_test_output.txt...' --provider copilot --model gpt-4o\nOutput: Berkas smoke_test_output.txt berhasil dibuat dengan isi persis sesuai prompt.", "Test Case 2 (Tool File Creation): ")
    add_b("Perintah: hermes.exe -z 'Read smoke_test_output.txt and count words...' --usage-file smoke_test_usage.json\nOutput: 'The file contains 7 words.' dan tercatat telemetri 22.444 total tokens, 2 API calls.", "Test Case 3 (Observability & Word Count): ")

    add_h("2. Kendala Teknis & Batasan yang Diungkap (Disclosed Limitations)")
    add_b("Hermes mewajibkan model dengan context window >= 64,000 tokens. Saat diuji dengan model gpt-4o-mini (12k context), Hermes menolak eksekusi. Solusi: Gunakan model gpt-4o atau claude-3.5-sonnet.", "Context Window Minimum (64k): ")
    add_b("Pada instalasi awal Windows native, operasi Move-Item terhambat permission berkas .git. Masalah terselesaikan 100% dengan perintah 'git reset --hard HEAD'.", "File Permission Windows: ")

    add_h("3. Status Kriteria Penerimaan (Acceptance Criteria)")
    t_ac = doc.add_table(rows=6, cols=3)
    t_ac.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_ac, color="E1E4E8", sz="4", val="single")

    ac_headers = ["Kriteria Penerimaan", "Status", "Bukti Pelaksanaan"]
    for j, h in enumerate(ac_headers):
        c = t_ac.rows[0].cells[j]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, top=60, bottom=60, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.0)
        r.font.color.rgb = RGBColor(255, 255, 255)

    ac_rows = [
        ("A basic task produces verified output", "TERPENUHI (PASSED)", "3 kasus uji berhasil mengeksekusi inferensi & tool."),
        ("Commands, versions, & config reproduce setup", "TERPENUHI (PASSED)", "Tersedia Hermes_Agent_Setup_Guide.md yang lengkap."),
        ("No secrets are committed", "TERPENUHI (PASSED)", "Menggunakan config.example.yaml & .env.example."),
        ("Errors, limitations, & risks disclosed", "TERPENUHI (PASSED)", "Batasan context window 64k & permission Windows dicatat."),
        ("Lead accepts guide and results", "READY FOR REVIEW", "Daily update template tersedia untuk komentar task."),
    ]

    widths = [Inches(2.5), Inches(1.8), Inches(2.2)]
    for i, r_data in enumerate(ac_rows, start=1):
        row = t_ac.rows[i]
        bg = "FFFFFF" if i % 2 == 1 else "F9FAFB"
        for j, val in enumerate(r_data):
            c = row.cells[j]
            c.width = widths[j]
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if j == 1:
                r.font.bold = True
                r.font.color.rgb = RGBColor(20, 120, 40)

    doc.save("D:\\ai_developer\\project6\\task 2\\Hermes_Agent_Task2_Report.docx")
    print("Task 2 DOCX generated.")

if __name__ == "__main__":
    build_docx()
