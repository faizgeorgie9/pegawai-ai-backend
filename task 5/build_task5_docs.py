import os
import re
import markdown
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=70, bottom=70, left=100, right=100):
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

def set_table_borders(table, color="D0D7DE", sz="4", val="single"):
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

def build_docx(md_path, docx_path):
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Document Header Title
    p_t = doc.add_paragraph()
    r_sub = p_t.add_run("PROGRAM PENGEMBANGAN PEGAWAI AI — SUBTASK S1-05A\n")
    r_sub.font.bold = True
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = RGBColor(90, 105, 120)

    r_title = p_t.add_run("HERMES AGENT: FINDINGS & SHORTLIST PRESENTATION\n")
    r_title.font.bold = True
    r_title.font.size = Pt(16)
    r_title.font.color.rgb = RGBColor(27, 54, 93)

    r_desc = p_t.add_run("Laporan Sidang Kelayakan & Keputusan Shortlist Kandidat A untuk Sprint 2")
    r_desc.font.size = Pt(11)
    r_desc.font.italic = True
    r_desc.font.color.rgb = RGBColor(70, 80, 95)

    # Metadata Table
    meta_table = doc.add_table(rows=6, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_table, color="D0D7DE", sz="6", val="single")

    meta_data = [
        ("Kandidat AI Agent", "Kandidat A: Hermes Agent (Nous Research v0.22.2)"),
        ("Keputusan Akhir Lead", "CONDITIONAL (Lolos Bersyarat ke Sprint 2)"),
        ("Penyaji (Presenter)", "Hermes Agent Researcher"),
        ("Evaluator / Sign-off", "R&D Lead"),
        ("Syarat Utama Lolos", "Isolasi Docker per-tenant & integrasi DeepSeek V3 via OpenRouter"),
        ("Basis Bukti", "Task 1 (Validasi), Task 2 (Smoke Test), Task 3 (Checklist), Task 4 (Kit)"),
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
        if "CONDITIONAL" in val:
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(200, 110, 20)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_code_block = False
    code_content = []

    for line in lines:
        sline = line.strip()

        # Handle fenced code block
        if sline.startswith("```"):
            if in_code_block:
                in_code_block = False
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.left_indent = Inches(0.2)
                r = p.add_run("\n".join(code_content))
                r.font.name = "Consolas"
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(40, 50, 60)
                code_content = []
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_content.append(line.rstrip("\r\n"))
            continue

        if sline.startswith("# DOKUMEN PRESENTASI") or sline.startswith("## Evaluasi Kelayakan") or sline.startswith("**Kode Subtask:**"):
            continue

        if sline.startswith("---") or sline == "":
            continue

        # Headings
        if sline.startswith("## "):
            h_text = sline.replace("## ", "").strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(h_text)
            r.font.bold = True
            r.font.size = Pt(13)
            r.font.color.rgb = RGBColor(27, 54, 93)
        elif sline.startswith("### "):
            h_text = sline.replace("### ", "").strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(h_text)
            r.font.bold = True
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(41, 74, 110)
        elif sline.startswith("- [ ] ") or sline.startswith("- [x] ") or sline.startswith("[✓] ") or sline.startswith("[ ] "):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            prefix = "[✓] " if (sline.startswith("- [x] ") or sline.startswith("[✓] ")) else "[ ] "
            r_pre = p.add_run(prefix)
            r_pre.font.bold = True
            p.add_run(sline[4:] if sline.startswith("[") else sline[6:])
        elif sline.startswith("- "):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.add_run(sline[2:])
        elif re.match(r"^\d+\.\s", sline):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0.2)
            p.add_run(sline)
        elif sline.startswith("|") and sline.endswith("|"):
            pass
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(4)
            p.add_run(sline)

    doc.save(docx_path)
    print(f"DOCX created: {docx_path}")

def build_html(md_path, html_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    html_body = markdown.markdown(md, extensions=['tables', 'fenced_code', 'nl2br'])

    full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>S1-05A: Hermes Agent Shortlist Presentation & Findings</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --primary: #1B365D;
    --primary-light: #2E5B9A;
    --warning: #D97706;
    --bg-page: #F8FAFC;
    --bg-card: #FFFFFF;
    --text-main: #1E293B;
    --text-muted: #64748B;
    --border: #E2E8F0;
    --code-bg: #F1F5F9;
  }}

  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--bg-page);
    color: var(--text-main);
    line-height: 1.65;
    margin: 0;
    padding: 40px 20px 80px 20px;
  }}

  .container {{
    max-width: 950px;
    margin: 0 auto;
    background: var(--bg-card);
    padding: 45px 55px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--border);
  }}

  /* Floating Copy Button */
  .copy-banner {{
    position: sticky;
    top: 20px;
    z-index: 999;
    background: rgba(27, 54, 93, 0.95);
    backdrop-filter: blur(8px);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    box-shadow: 0 4px 15px rgba(27, 54, 93, 0.25);
  }}
  .copy-banner span {{
    font-size: 13.5px;
    font-weight: 500;
  }}
  .copy-btn {{
    background-color: #10B981;
    color: white;
    border: none;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .copy-btn:hover {{
    background-color: #059669;
    transform: translateY(-1px);
  }}

  h1 {{
    color: var(--primary);
    font-size: 25px;
    font-weight: 700;
    border-bottom: 2px solid var(--primary);
    padding-bottom: 12px;
    margin-top: 0;
    letter-spacing: -0.5px;
  }}
  h2 {{
    color: var(--primary);
    font-size: 18px;
    font-weight: 600;
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin-top: 36px;
    letter-spacing: -0.3px;
  }}
  h3 {{
    color: var(--primary-light);
    font-size: 15px;
    font-weight: 600;
    margin-top: 22px;
    margin-bottom: 8px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 13.5px;
    border: 1px solid var(--border);
  }}
  th, td {{
    padding: 10px 14px;
    text-align: left;
    border: 1px solid var(--border);
    vertical-align: top;
  }}
  th {{
    background-color: #F8FAFC;
    color: var(--primary);
    font-weight: 600;
  }}
  tr:nth-child(even) td {{
    background-color: #FAFAFA;
  }}

  pre {{
    background-color: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 18px;
    overflow-x: auto;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 12.5px;
    line-height: 1.5;
    color: #0F172A;
  }}
  code {{
    background-color: var(--code-bg);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 12.5px;
    color: #BE185D;
  }}

  ul, ol {{
    padding-left: 24px;
    font-size: 14px;
  }}
  li {{
    margin-bottom: 4px;
  }}

  .badge-conditional {{
    display: inline-block;
    background-color: #FEF3C7;
    color: #B45309;
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12.5px;
    border: 1px solid #FCD34D;
  }}
</style>
</head>
<body>

<div class="container">
  <div class="copy-banner">
    <span>📊 <strong>S1-05A: Hermes Findings & Shortlist Presentation</strong> — Status: CONDITIONAL APPROVED</span>
    <button class="copy-btn" onclick="copyForGDocs()">📋 1-Click Copy to Google Docs / Slides</button>
  </div>

  <div id="content">
    {html_body}
  </div>
</div>

<script>
function copyForGDocs() {{
  const contentEl = document.getElementById('content');
  const range = document.createRange();
  range.selectNode(contentEl);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  try {{
    document.execCommand('copy');
    alert('✅ Berhasil di-copy! Seluruh slide dan laporan sidang shortlist siap di-paste (Ctrl + V) ke Google Docs atau Google Slides dengan tabel dan format rapi.');
  }} catch (err) {{
    alert('Gagal menyalin otomatis. Silakan pilih seluruh teks manual lalu tekan Ctrl + C.');
  }}
  window.getSelection().removeAllRanges();
}}
</script>

</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"HTML created: {html_path}")

if __name__ == "__main__":
    task5_dir = r"d:\ai_developer\project6\task 5"
    md_file = os.path.join(task5_dir, "Hermes_Agent_Shortlist_Presentation_S1-05A.md")
    docx_file = os.path.join(task5_dir, "Hermes_Agent_Shortlist_Presentation_S1-05A.docx")
    html_file = os.path.join(task5_dir, "Hermes_Agent_Shortlist_Presentation_S1-05A.html")

    build_docx(md_file, docx_file)
    build_html(md_file, html_file)
