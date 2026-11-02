import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import markdown

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
    r_sub = p_t.add_run("PROGRAM PENGEMBANGAN PEGAWAI AI — SUBTASK S1-04A\n")
    r_sub.font.bold = True
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = RGBColor(90, 105, 120)

    r_title = p_t.add_run("AI TOP TRENDS: DUMMY BUSINESS PROFILE & BRAND VOICE (v1.0.0)")
    r_title.font.bold = True
    r_title.font.size = Pt(16)
    r_title.font.color.rgb = RGBColor(27, 54, 93)

    # Metadata Box
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_table, color="D0D7DE", sz="6", val="single")

    meta_data = [
        ("Nama Bisnis Fiktif", "AI Top Trends (Versi Artefak: v1.0.0)"),
        ("Tujuan Standar", "Shared Benchmark Context untuk Hermes, MausBot, Rakazo, & CrewAI"),
        ("Penyusun Dokumen", "Candidate A Researcher (Hermes)"),
        ("Reviewer", "Benchmark Coordinator (Rakazo Researcher) & R&D Lead"),
        ("Status Data", "100% SYNTHETIC & SAFE (Zero Real Customer Data / Zero Secrets)"),
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
        if "SYNTHETIC" in val:
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(20, 120, 40)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    def add_h(text, size=12):
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

    add_h("1. Profil Bisnis Fiktif (AI Top Trends)")
    add_b("Membangun Pekerja Digital yang Menghasilkan Nilai Nyata untuk Bisnis.", "Tagline: ")
    add_b("Edukasi dan implementasi otomatisasi alur kerja pemasaran bagi pelaku usaha.", "Industri: ")
    add_b("Pegawai AI Marketing & Content Specialist (Kalender konten, adaptasi multi-kanal, quality check).", "Produk Unggulan MVP: ")

    add_h("2. Tiga Target Audiens Utama")
    add_b("Pemilik toko online & UMKM lokal (Waktu terbatas, butuh konten cepat dan praktis tanpa jargon teknis).", "Audiens A: ")
    add_b("Kreator Konten & Solo Creator (Mengatasi ide buntu, repurpose 1 ide menjadi skrip video pendek).", "Audiens B: ")
    add_b("Marketer Agensi & Tim Kecil (Standarisasi kalender konten dan persetujuan klien yang teratur).", "Audiens C: ")

    add_h("3. Aturan Brand Voice & Batasan Konten")
    add_b("Otoritatif tapi membumi, berbasis langkah nyata, dilarang memberi janji palsu (autopilot kaya instan).", "Karakter Suara: ")
    add_b("Wajib menyertakan Call to Action (CTA) di akhir setiap konten.", "Kewajiban CTA: ")
    add_b("Agen dilarang mempublikasikan otomatis. Setiap konten berstatus DRAFT_PENDING_APPROVAL.", "Guardrail Human Approval: ")

    add_h("4. Status Kepatuhan Keamanan Data")
    add_b("Zero Real Customer Data: 100% nama perusahaan, produk, dan metrik bersifat sintetis.", "Kerahasiaan Pelanggan: ")
    add_b("Zero Credentials / Secrets: Tidak ada kunci API atau kredensial yang disertakan.", "Keamanan Kredensial: ")
    add_b("Berkas siap dibagikan secara seragam ke tim kandidat B, C, dan D.", "Aksesibilitas Bersama: ")

    doc.save("D:\\ai_developer\\project6\\task 4\\AI_Top_Trends_Profile_v1.0.docx")
    print("DOCX generated.")

def build_html():
    with open("D:\\ai_developer\project6\\task 4\\AI_Top_Trends_Profile_v1.0.md", "r", encoding="utf-8") as f:
        md = f.read()
    html_body = markdown.markdown(md, extensions=['tables', 'fenced_code'])
    full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>S1-04A: Dummy Business Profile & Brand Voice</title>
<style>
  body {{ font-family: 'Calibri', Arial, sans-serif; max-width: 900px; margin: 30px auto; line-height: 1.6; color: #282828; padding: 0 25px; }}
  h1 {{ color: #1B365D; border-bottom: 2px solid #1B365D; padding-bottom: 8px; font-size: 22px; }}
  h2 {{ color: #1B365D; border-bottom: 1px solid #ddd; padding-bottom: 4px; font-size: 17px; margin-top: 25px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13.5px; }}
  th, td {{ border: 1px solid #D0D7DE; padding: 8px 12px; text-align: left; }}
  th {{ background-color: #1B365D; color: white; }}
  tr:nth-child(even) {{ background-color: #F8F9FA; }}
  pre, code {{ background-color: #F6F8FA; font-family: Consolas, monospace; }}
  pre {{ padding: 12px; border: 1px solid #D0D7DE; overflow-x: auto; font-size: 12.5px; }}
  .copy-btn {{ position: fixed; top: 20px; right: 20px; background-color: #1B365D; color: white; border: none; padding: 10px 18px; font-weight: bold; border-radius: 6px; cursor: pointer; }}
</style>
</head>
<body>
<button class="copy-btn" onclick="copyForGDocs()">📋 Copy All to Google Docs</button>
<div id="content">{html_body}</div>
<script>
function copyForGDocs() {{
  const range = document.createRange();
  range.selectNode(document.getElementById('content'));
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  document.execCommand('copy');
  window.getSelection().removeAllRanges();
  alert('Konten profil berhasil di-copy! Anda bisa langsung tekan Ctrl+V di Google Docs.');
}}
</script>
</body>
</html>"""
    with open("D:\\ai_developer\project6\\task 4\\AI_Top_Trends_Profile_v1.0.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print("HTML generated.")

if __name__ == "__main__":
    build_docx()
    build_html()
