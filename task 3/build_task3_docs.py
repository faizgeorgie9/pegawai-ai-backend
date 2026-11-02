import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=70, bottom=70, left=90, right=90):
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

    p_t = doc.add_paragraph()
    r_sub = p_t.add_run("PROGRAM PENGEMBANGAN PEGAWAI AI — DAY 3 EXPLORATION\n")
    r_sub.font.bold = True
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = RGBColor(90, 105, 120)

    r_title = p_t.add_run("HERMES AGENT: FEATURE EXPLORATION & INITIAL COST ANALYSIS")
    r_title.font.bold = True
    r_title.font.size = Pt(17)
    r_title.font.color.rgb = RGBColor(27, 54, 93)

    # 1. Feature Table
    p1 = doc.add_paragraph()
    p1.paragraph_format.space_before = Pt(12)
    p1.paragraph_format.space_after = Pt(4)
    r1 = p1.add_run("1. Matriks Pengujian Fitur Inti (Evidence-Backed)")
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = RGBColor(27, 54, 93)

    t1 = doc.add_table(rows=11, cols=4)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t1, color="E1E4E8", sz="4", val="single")

    headers1 = ["Fitur Diuji", "Hasil", "Kategori", "Bukti & Catatan Teknis"]
    for j, h in enumerate(headers1):
        c = t1.rows[0].cells[j]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, top=60, bottom=60, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.0)
        r.font.color.rgb = RGBColor(255, 255, 255)

    data1 = [
        ("Multi-step Execution & File Tool", "PASS", "Native", "Membuat employee_profile.json, hitung cost/lead: $5.00."),
        ("Persistent Context & Memory", "PASS", "Native", "Sesi tersimpan di SQLite, sukses resume mengingat budget $500."),
        ("LLM / Provider Switching", "PASS", "Native", "Mendukung OpenAI, Copilot, Anthropic, Ollama, & Fallback Chain."),
        ("Error Handling & Monitoring", "PASS", "Native", "Log detail di agent.log (latensi 2.8s, cache 99%, token log)."),
        ("Scheduling & Restart Behavior", "PASS", "Native", "Gateway daemon aktif (PID 15632) dan auto-start Windows Task."),
        ("Human Approval Guardrails", "PASS", "Native", "Prompt konfirmasi aktif default untuk perintah berisiko tinggi."),
        ("Skills & Custom Persona", "PASS", "Native", "51 skills modular, SOUL.md, dan AGENTS.md terintegrasi."),
        ("Browser Operations (Web)", "PASS", "Native", "Toolset browser-use & web scraper siap pakai."),
        ("Visual Computer Use (CUA)", "PARTIAL", "Third-Party", "Toolset computer-use ada, butuh display aktif & OS driver."),
        ("Multi-Tenant Data Isolation", "BLOCKED", "Custom Code", "Aslinya single-user/database tunggal, butuh Docker wrapper."),
    ]

    widths1 = [Inches(2.0), Inches(0.9), Inches(1.1), Inches(2.5)]
    for i, row_data in enumerate(data1, start=1):
        row = t1.rows[i]
        bg = "FFFFFF" if i % 2 == 1 else "F9FAFB"
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = widths1[j]
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if j == 1:
                r.font.bold = True
                if val == "PASS":
                    r.font.color.rgb = RGBColor(20, 120, 40)
                elif val == "PARTIAL":
                    r.font.color.rgb = RGBColor(180, 110, 20)
                else:
                    r.font.color.rgb = RGBColor(180, 30, 30)

    # 2. Cost Table
    p2 = doc.add_paragraph()
    p2.paragraph_format.space_before = Pt(16)
    p2.paragraph_format.space_after = Pt(4)
    r2 = p2.add_run("2. Analisis Biaya Operasional Awal (5 Kategori)")
    r2.font.bold = True
    r2.font.size = Pt(12)
    r2.font.color.rgb = RGBColor(27, 54, 93)

    t2 = doc.add_table(rows=6, cols=4)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t2, color="E1E4E8", sz="4", val="single")

    headers2 = ["Kategori Biaya", "Rincian Asumsi", "Estimasi Biaya", "Status Data"]
    for j, h in enumerate(headers2):
        c = t2.rows[0].cells[j]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, top=60, bottom=60, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.0)
        r.font.color.rgb = RGBColor(255, 255, 255)

    data2 = [
        ("1. Software License", "Lisensi MIT Nous Research, bebas royalti", "$0.00 / bulan", "SOURCED"),
        ("2. LLM / API Usage", "1.000 task @ ~30k tokens gpt-4o (~$0.08/task)", "~$80.00 / bulan", "ESTIMATE"),
        ("3. Infrastructure Hosting", "Cloud VPS 4 vCPU, 8GB RAM untuk Docker runner", "~$48.00 / bulan", "ESTIMATE"),
        ("4. Optional Managed Services", "Web Search API (Tavily/Serper 1.000 query)", "~$10.00 / bulan", "ESTIMATE"),
        ("5. Local GPU Alternative", "Model lokal (Ollama Llama-70B), $0 API, butuh GPU", "$0 API ($150 GPU)", "PROVISIONAL"),
    ]

    widths2 = [Inches(1.8), Inches(2.5), Inches(1.2), Inches(1.0)]
    for i, row_data in enumerate(data2, start=1):
        row = t2.rows[i]
        bg = "FFFFFF" if i % 2 == 1 else "F9FAFB"
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = widths2[j]
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if j in (0, 2):
                r.font.bold = True

    # Summary
    p_sum = doc.add_paragraph()
    p_sum.paragraph_format.space_before = Pt(8)
    r_sum = p_sum.add_run("Total Proyeksi Biaya Operasional Awal: ~$138.00 / bulan (Kapasitas 1.000 task Pegawai AI).")
    r_sum.font.bold = True
    r_sum.font.size = Pt(10)
    r_sum.font.color.rgb = RGBColor(27, 54, 93)

    output_path = "D:\\ai_developer\\project6\\task 3\\Hermes_Agent_Day3_Report.docx"
    doc.save(output_path)
    print("Day 3 DOCX generated.")

if __name__ == "__main__":
    build_docx()
