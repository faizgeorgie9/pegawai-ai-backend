r"""
Generator Dokumen Individual 4 Pegawai AI (Content & Creative)
Menghasilkan:
1. File Word (.docx) berstandar eksekutif per bot.
2. File Web (.html dan .mhtml) bergaya antarmuka modern Karyawan.ai per bot.
Tujuan penyimpanan:
- D:/Users/IVANAGITA/aitoptrends/karyawan ai/
- backend/docs-kaf/sprint5/
- frontend/docs-kaf/sprint5/
- C:/Users/IVANAGITA/.gemini/antigravity/brain/289c4273-5463-4a74-9663-80a73fc092a8/ (Artifact Dir)
"""

import os
import re
import html
import shutil
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

ROOT_DIR = Path(r"D:\Users\IVANAGITA\aitoptrends\hermes")
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
KARYAWAN_AI_DIR = Path(r"D:\Users\IVANAGITA\aitoptrends\karyawan ai")
ARTIFACT_DIR = Path(r"C:\Users\IVANAGITA\.gemini\antigravity\brain\289c4273-5463-4a74-9663-80a73fc092a8")

SRC_DOCS_DIR = BACKEND_DIR / "docs-kaf" / "sprint5"

BOTS_CONFIG = [
    {
        "code": "CRE-01",
        "short_name": "Content Strategist",
        "full_name": "Content Strategist & Omnichannel Distribution Lead",
        "handle": "@contentstrategist",
        "initials": "CS",
        "color_hex": "6366F1",  # Indigo
        "color_rgb": (99, 102, 241),
        "tagline": "Merancang strategi pilar konten, riset audiens Gen Z, kurasi produk resmi Colorbox, menyusun kalender editorial, serta mengelola adaptasi format dan penjadwalan distribusi multi-kanal.",
        "consolidation": "CRE-01 Content Strategist + CRE-08 Content Distribution Specialist",
        "src_file": SRC_DOCS_DIR / "01_CONTENT_STRATEGIST.md",
        "docx_name": "CRE-01_Content_Strategist.docx",
        "html_name": "Karyawan AI — CRE-01 - Content Strategist.html",
        "mhtml_name": "Karyawan AI — CRE-01 - Content Strategist.mhtml",
        "in_scope": "Strategi pilar konten, persona mapping, riset tren, omnichannel calendar, creative brief, multi-platform adaptation, antrean scheduler, agregasi performa distribusi.",
        "out_scope": "Tidak menulis naskah detail per kata (ke Copywriter), tidak mendesain grafis (ke Graphic Designer), tidak mengedit video (ke Video Creator), tidak mengelola budget ads.",
        "inputs": "Brief kampanye, tujuan bisnis, pilar gaya Colorbox (Urban/Romantic/Chic), katalog produk resmi (product-catalog.md).",
        "outputs": "Matriks pilar konten, kalender editorial mingguan, creative brief terstruktur, antrean tayang scheduler (Buffer/Meta/WA).",
        "model": "Claude 3.5 Sonnet / GPT-4o (Reasoning: Balanced)",
        "kpi": "Ketepatan waktu kalender (100%), kepatuhan pilar konten (>95%), efektivitas brief (revisi <10%), zero unsupported claim (100%)."
    },
    {
        "code": "CRE-02",
        "short_name": "Content & Copywriter",
        "full_name": "Creative Content & Copywriter (Storytelling, Educational & Conversion Copy)",
        "handle": "@copywriter",
        "initials": "CC",
        "color_hex": "E11D48",  # Rose
        "color_rgb": (225, 29, 72),
        "tagline": "Menghasilkan naskah tulisan persuasif, caption Instagram/TikTok #NeverJustOneThing, hook viral 3 detik, on-screen text minimalis, dan spoken script video berdaya konversi tinggi.",
        "consolidation": "CRE-02 Content Writer + CRE-03 Copywriter",
        "src_file": SRC_DOCS_DIR / "02_CONTENT_AND_COPYWRITER.md",
        "docx_name": "CRE-02_Content_and_Copywriter.docx",
        "html_name": "Karyawan AI — CRE-02 - Content & Copywriter.html",
        "mhtml_name": "Karyawan AI — CRE-02 - Content & Copywriter.mhtml",
        "in_scope": "Caption Instagram & TikTok, teks slide carousel 5 slide, hook 3 detik pembuka, spoken script video 15-60s, artikel blog/panduan gaya, optimasi SEO on-page, A/B angle copy.",
        "out_scope": "Tidak menentukan pilar konten makro (ke Strategist), tidak mendesain visual (ke Graphic Designer), tidak memotong video (ke Video Creator), tidak mempublikasikan langsung tanpa izin.",
        "inputs": "Creative brief dari Strategist, informasi produk resmi Colorbox terverifikasi, target persona Gen Z, batasan karakter kanal.",
        "outputs": "Paket naskah carousel 5 slide, caption lengkap tagar #NeverJustOneThing, headline promosi A/B, spoken script video berdurasi 15-60 detik.",
        "model": "Claude 3.5 Sonnet / GPT-4o (Reasoning: Balanced Creative)",
        "kpi": "Hook retention rate (>65%), akurasi fakta katalog (100%), kepatuhan tone brand (100%), kelengkapan CTA (100%)."
    },
    {
        "code": "CRE-03",
        "short_name": "Graphic & Motion Designer",
        "full_name": "Graphic & Motion Designer (Static Feeds, Carousels, Motion Graphics & Visual Prompts)",
        "handle": "@motiondesigner",
        "initials": "GM",
        "color_hex": "0284C7",  # Sky
        "color_rgb": (2, 132, 199),
        "tagline": "Merancang feed carousel 4:5 Portrait (1080x1350 px), wireframe tata letak safe zone, banner promosi, tipografi kinetik, transisi gerak, dan Master AI Visual Prompts fotorealistik.",
        "consolidation": "CRE-04 Graphic Designer + CRE-06 Motion Graphics Specialist",
        "src_file": SRC_DOCS_DIR / "03_GRAPHIC_AND_MOTION_DESIGNER.md",
        "docx_name": "CRE-03_Graphic_and_Motion_Designer.docx",
        "html_name": "Karyawan AI — CRE-03 - Graphic & Motion Designer.html",
        "mhtml_name": "Karyawan AI — CRE-03 - Graphic & Motion Designer.mhtml",
        "in_scope": "Feed carousel Instagram 4:5 Portrait, wireframe kanvas & safe zone, banner digital e-commerce, infografik size guide, kinetic typography, efek transisi gerak, Master AI Visual Prompts.",
        "out_scope": "Tidak menulis naskah panjang (ke Copywriter), tidak shooting live-action video (ke Video Creator), tidak merilis materi tanpa approval desainer manusia.",
        "inputs": "Naskah copy & hook dari Copywriter, foto produk asli Colorbox dari folder images/, palet warna brand, spesifikasi kanvas platform.",
        "outputs": "5 Diagram wireframe kanvas lengkap, spec sheet desain Canva/Figma, 5 Master AI Visual Prompts (FLUX/Midjourney), panduan aset kinetic typography.",
        "model": "GPT-4o Multimodal / Claude 3.5 Sonnet + OpenCode Zen (Visual Rendering)",
        "kpi": "Kepatuhan safe-zone (100%), integritas rasio aspek foto asli (100%), kesiapan produksi visual (>95%), kepuasan estetika visual (>90%)."
    },
    {
        "code": "CRE-04",
        "short_name": "Video & UGC Creator",
        "full_name": "Video & UGC Creator (Short-Form Reels/TikTok/Shorts, UGC Directing & Audio Strategy)",
        "handle": "@videougc",
        "initials": "VU",
        "color_hex": "059669",  # Emerald
        "color_rgb": (5, 150, 105),
        "tagline": "Mengembangkan konsep video vertikal 9:16 (Reels/TikTok/Shorts), naskah percakapan natural, panduan talent UGC styling demo, kurasi audio viral/SFX, dan optimasi hook visual 3 detik.",
        "consolidation": "CRE-05 Video Creator + CRE-07 UGC Specialist",
        "src_file": SRC_DOCS_DIR / "04_VIDEO_AND_UGC_CREATOR.md",
        "docx_name": "CRE-04_Video_and_UGC_Creator.docx",
        "html_name": "Karyawan AI — CRE-04 - Video & UGC Creator.html",
        "mhtml_name": "Karyawan AI — CRE-04 - Video & UGC Creator.mhtml",
        "in_scope": "Konsep video vertikal 9:16 (15-60 detik), video storyboard & shot list, spoken dialogue natural, panduan talent UGC try-on, kurasi musik trending/SFX, visual hook 3 detik.",
        "out_scope": "Tidak menentukan strategi pilar makro (ke Strategist), tidak mendesain aset vektor statis (ke Graphic Designer), tidak mengklaim pengalaman fiktif sebagai review riil.",
        "inputs": "Creative brief & fokus pilar gaya, spoken script dari Copywriter, aset foto produk Colorbox resmi, referensi tren video/audio TikTok.",
        "outputs": "Storyboard video 9:16 lengkap per detik, talent briefing doc untuk UGC creator, audio & sound effect recommendation, caption & sound tagar.",
        "model": "Claude 3.5 Sonnet / GPT-4o (Reasoning: Creative Pacing)",
        "kpi": "Hook rate 3 detik pertama (>60%), retensi tontonan video (>45%), kejelasan instruksi talent (revisi <10%), kepatuhan klaim autentik (100%)."
    }
]

# ==============================================================================
# DOCX STYLING HELPERS
# ==============================================================================

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
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

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
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

def format_cell(cell, text, bold=False, color=(51, 65, 85), font_size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT, bg_hex=None):
    if bg_hex:
        set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(*color)
    return run

def add_header_footer(doc, bot_title):
    for sec in doc.sections:
        header = sec.header
        p_hdr = header.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_hdr = p_hdr.add_run(f"Karyawan AI — {bot_title}")
        r_hdr.font.name = "Calibri"
        r_hdr.font.size = Pt(8.5)
        r_hdr.font.color.rgb = RGBColor(148, 163, 184)
        
        footer = sec.footer
        p_ftr = footer.paragraphs[0]
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_ftr = p_ftr.add_run("Dokumen Profiling Pegawai AI — Versi 2.0 (Konsolidasi) | Hak Cipta AI Top Trends")
        r_ftr.font.name = "Calibri"
        r_ftr.font.size = Pt(8.5)
        r_ftr.font.color.rgb = RGBColor(148, 163, 184)

def add_callout(doc, title, text, bg_hex="F8FAFC", border_color="6366F1"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    r_title = p.add_run(f"{title}\n")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(10.5)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    r_text = p.add_run(text)
    r_text.font.name = "Calibri"
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = RGBColor(51, 65, 85)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ==============================================================================
# BUILD INDIVIDUAL DOCX FOR A BOT
# ==============================================================================

def build_bot_docx(bot_cfg):
    doc = docx.Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.8)
    sec.bottom_margin = Inches(0.8)
    sec.left_margin = Inches(0.9)
    sec.right_margin = Inches(0.9)
    
    add_header_footer(doc, f"{bot_cfg['code']} {bot_cfg['short_name']}")
    
    # 1. Header & Title Block
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(2)
    r_meta = p_meta.add_run(f"KARYAWAN AI • DIVISI 04. CONTENT & CREATIVE • HANDLE: {bot_cfg['handle']}")
    r_meta.font.name = "Calibri"
    r_meta.font.size = Pt(9)
    r_meta.font.bold = True
    r_meta.font.color.rgb = RGBColor(*bot_cfg["color_rgb"])
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(2)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run(f"{bot_cfg['code']} | {bot_cfg['short_name']}")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run(f"Spesifikasi Jabatan & Panduan Operasional AI Employee — {bot_cfg['full_name']}")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = RGBColor(71, 85, 105)
    
    # Callout: Executive Summary
    add_callout(
        doc,
        f"🎯 Ringkasan Eksekutif ({bot_cfg['code']})",
        f"{bot_cfg['tagline']}\n\nStatus Integrasi: {bot_cfg['consolidation']}",
        bg_hex="F8FAFC",
        border_color=bot_cfg["color_hex"]
    )
    
    # Quick Specs Table
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    tbl = doc.add_table(rows=7, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)
    
    specs = [
        ("Identitas & Handle", f"{bot_cfg['code']} {bot_cfg['short_name']} ({bot_cfg['handle']})"),
        ("Cakupan Konsolidasi", bot_cfg["consolidation"]),
        ("Tugas Utama (In Scope)", bot_cfg["in_scope"]),
        ("Batasan (Out of Scope)", bot_cfg["out_scope"]),
        ("Masukan Diperlukan (Inputs)", bot_cfg["inputs"]),
        ("Standar Keluaran (Outputs)", bot_cfg["outputs"]),
        ("Rekomendasi AI & Target KPI", f"{bot_cfg['model']}\nKPI: {bot_cfg['kpi']}")
    ]
    
    col_widths = [Inches(2.2), Inches(4.5)]
    for r_idx, (k, v) in enumerate(specs):
        bg = "F1F5F9" if r_idx % 2 == 0 else "FFFFFF"
        cell_k = tbl.cell(r_idx, 0)
        cell_v = tbl.cell(r_idx, 1)
        format_cell(cell_k, k, bold=True, color=(15, 23, 42), font_size=9, bg_hex="E2E8F0")
        format_cell(cell_v, v, bold=False, color=(51, 65, 85), font_size=9, bg_hex=bg)
        cell_k.width = col_widths[0]
        cell_v.width = col_widths[1]
        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Parse source markdown and append all 11 components cleanly!
    src_text = bot_cfg["src_file"].read_text(encoding="utf-8")
    lines = src_text.splitlines()
    
    in_header = True
    in_table = False
    table_rows = []
    
    for line in lines:
        l_strip = line.strip()
        
        # Skip top markdown header since we designed an executive title
        if l_strip.startswith("# CRE-") or l_strip.startswith("## Divisi:"):
            continue
        if l_strip.startswith("> **") or l_strip.startswith("---"):
            continue
        if l_strip.startswith("### Deskripsi Singkat") or l_strip.startswith("### Job Description"):
            in_header = False
            
        # Headings
        if l_strip.startswith("## "):
            h_text = l_strip.replace("## ", "").strip()
            p_h = doc.add_paragraph()
            p_h.paragraph_format.space_before = Pt(14)
            p_h.paragraph_format.space_after = Pt(4)
            p_h.paragraph_format.keep_with_next = True
            r = p_h.add_run(h_text)
            r.font.name = "Calibri"
            r.font.size = Pt(13)
            r.font.bold = True
            r.font.color.rgb = RGBColor(15, 23, 42)
            continue
            
        if l_strip.startswith("### "):
            h_text = l_strip.replace("### ", "").strip()
            p_h = doc.add_paragraph()
            p_h.paragraph_format.space_before = Pt(10)
            p_h.paragraph_format.space_after = Pt(2)
            p_h.paragraph_format.keep_with_next = True
            r = p_h.add_run(h_text)
            r.font.name = "Calibri"
            r.font.size = Pt(11)
            r.font.bold = True
            r.font.color.rgb = RGBColor(*bot_cfg["color_rgb"])
            continue

        if l_strip.startswith("#### "):
            h_text = l_strip.replace("#### ", "").strip()
            p_h = doc.add_paragraph()
            p_h.paragraph_format.space_before = Pt(8)
            p_h.paragraph_format.space_after = Pt(2)
            p_h.paragraph_format.keep_with_next = True
            r = p_h.add_run(h_text)
            r.font.name = "Calibri"
            r.font.size = Pt(10)
            r.font.bold = True
            r.font.color.rgb = RGBColor(71, 85, 105)
            continue
            
        # Tables in markdown
        if l_strip.startswith("|") and l_strip.endswith("|"):
            cells = [c.strip() for c in l_strip.split("|")[1:-1]]
            if all(set(c) <= set("-: ") for c in cells):
                continue  # separator line
            table_rows.append(cells)
            in_table = True
            continue
        else:
            if in_table and table_rows:
                # Render markdown table to docx table
                cols_count = max(len(r) for r in table_rows)
                tbl_md = doc.add_table(rows=len(table_rows), cols=cols_count)
                tbl_md.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl_md)
                for r_i, row_data in enumerate(table_rows):
                    for c_i, cell_text in enumerate(row_data):
                        cell = tbl_md.cell(r_i, c_i)
                        is_hdr = (r_i == 0)
                        bg = "E2E8F0" if is_hdr else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                        format_cell(cell, cell_text.replace("**", ""), bold=is_hdr, font_size=8.5, bg_hex=bg)
                doc.add_paragraph().paragraph_format.space_after = Pt(6)
                table_rows = []
                in_table = False
                
        # Bullet list
        if l_strip.startswith("* ") or l_strip.startswith("- "):
            item_text = l_strip[2:].strip()
            p_b = doc.add_paragraph(style="List Bullet")
            p_b.paragraph_format.space_before = Pt(1)
            p_b.paragraph_format.space_after = Pt(1)
            p_b.paragraph_format.line_spacing = 1.15
            
            # Simple bold handler
            parts = re.split(r'(\*\*.*?\*\*)', item_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p_b.add_run(part[2:-2])
                    r.font.name = "Calibri"
                    r.font.size = Pt(9.5)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 23, 42)
                else:
                    r = p_b.add_run(part)
                    r.font.name = "Calibri"
                    r.font.size = Pt(9.5)
                    r.font.color.rgb = RGBColor(51, 65, 85)
            continue
            
        # Numbered list
        m_num = re.match(r'^(\d+\.)\s+(.*)', l_strip)
        if m_num:
            num_prefix = m_num.group(1)
            item_text = m_num.group(2)
            p_n = doc.add_paragraph()
            p_n.paragraph_format.left_indent = Inches(0.25)
            p_n.paragraph_format.space_before = Pt(1)
            p_n.paragraph_format.space_after = Pt(1)
            p_n.paragraph_format.line_spacing = 1.15
            r_num = p_n.add_run(f"{num_prefix} ")
            r_num.font.name = "Calibri"
            r_num.font.size = Pt(9.5)
            r_num.font.bold = True
            r_num.font.color.rgb = RGBColor(*bot_cfg["color_rgb"])
            
            parts = re.split(r'(\*\*.*?\*\*)', item_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p_n.add_run(part[2:-2])
                    r.font.name = "Calibri"
                    r.font.size = Pt(9.5)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 23, 42)
                else:
                    r = p_n.add_run(part)
                    r.font.name = "Calibri"
                    r.font.size = Pt(9.5)
                    r.font.color.rgb = RGBColor(51, 65, 85)
            continue
            
        # Regular paragraph
        if l_strip:
            p_reg = doc.add_paragraph()
            p_reg.paragraph_format.space_before = Pt(2)
            p_reg.paragraph_format.space_after = Pt(3)
            p_reg.paragraph_format.line_spacing = 1.15
            parts = re.split(r'(\*\*.*?\*\*)', l_strip)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p_reg.add_run(part[2:-2])
                    r.font.name = "Calibri"
                    r.font.size = Pt(9.5)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 23, 42)
                else:
                    r = p_reg.add_run(part)
                    r.font.name = "Calibri"
                    r.font.size = Pt(9.5)
                    r.font.color.rgb = RGBColor(51, 65, 85)

    return doc

# ==============================================================================
# BUILD INDIVIDUAL HTML / MHTML FOR A BOT (Karyawan.ai Aesthetic)
# ==============================================================================

def build_bot_html(bot_cfg):
    src_text = bot_cfg["src_file"].read_text(encoding="utf-8")
    
    # Simple markdown to HTML converter for body
    html_lines = []
    lines = src_text.splitlines()
    in_table = False
    table_rows = []
    in_code = False
    code_lines = []
    
    for line in lines:
        l = line.strip()
        
        # Code block
        if l.startswith("```"):
            if in_code:
                in_code = False
                code_content = html.escape("\n".join(code_lines))
                html_lines.append(f'<pre class="code-block"><code>{code_content}</code></pre>')
                code_lines = []
            else:
                in_code = True
                code_lines = []
            continue
            
        if in_code:
            code_lines.append(line)
            continue
            
        # Skip raw top markdown title
        if l.startswith("# CRE-") or l.startswith("## Divisi:"):
            continue
        if l.startswith("> **") or l.startswith("---"):
            continue
            
        # Headings
        if l.startswith("## "):
            html_lines.append(f'<h2 class="section-h2">{html.escape(l[3:].strip())}</h2>')
            continue
        if l.startswith("### "):
            html_lines.append(f'<h3 class="section-h3">{html.escape(l[4:].strip())}</h3>')
            continue
        if l.startswith("#### "):
            html_lines.append(f'<h4 class="section-h4">{html.escape(l[5:].strip())}</h4>')
            continue
            
        # Tables
        if l.startswith("|") and l.endswith("|"):
            cells = [c.strip() for c in l.split("|")[1:-1]]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            table_rows.append(cells)
            in_table = True
            continue
        else:
            if in_table and table_rows:
                html_lines.append('<div class="table-container"><table class="data-table">')
                for r_idx, r in enumerate(table_rows):
                    tag = "th" if r_idx == 0 else "td"
                    html_lines.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in r) + "</tr>")
                html_lines.append('</table></div>')
                table_rows = []
                in_table = False
                
        # Lists
        if l.startswith("* ") or l.startswith("- "):
            content = html.escape(l[2:].strip())
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            html_lines.append(f'<li class="bullet-item">{content}</li>')
            continue
            
        m_num = re.match(r'^(\d+\.)\s+(.*)', l)
        if m_num:
            num = m_num.group(1)
            content = html.escape(m_num.group(2).strip())
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            html_lines.append(f'<div class="numbered-item"><span class="num-badge">{num}</span> <span>{content}</span></div>')
            continue
            
        # Paragraph
        if l:
            content = html.escape(l)
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            html_lines.append(f'<p class="body-p">{content}</p>')

    body_content = "\n".join(html_lines)
    
    html_template = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Karyawan AI — {bot_cfg['code']} {bot_cfg['short_name']}</title>
    <style>
        :root {{
            --primary: #{bot_cfg['color_hex']};
            --slate-900: #0f172a;
            --slate-800: #1e293b;
            --slate-700: #334155;
            --slate-600: #475569;
            --slate-500: #64748b;
            --slate-200: #e2e8f0;
            --slate-100: #f1f5f9;
            --slate-50: #f8fafc;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--slate-50);
            color: var(--slate-700);
            line-height: 1.6;
            padding: 24px;
        }}
        .container {{
            max-width: 1040px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            border: 1px solid var(--slate-200);
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
            overflow: hidden;
        }}
        .header-top {{
            background: linear-gradient(135deg, var(--slate-900) 0%, var(--slate-800) 100%);
            padding: 32px;
            color: white;
            border-bottom: 1px solid var(--slate-800);
        }}
        .breadcrumb {{
            font-size: 13px;
            color: var(--slate-400);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .breadcrumb span {{ color: var(--primary); font-weight: 600; }}
        .profile-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            flex-wrap: wrap;
        }}
        .profile-left {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .avatar {{
            width: 76px;
            height: 76px;
            border-radius: 20px;
            background: linear-gradient(135deg, var(--primary) 0%, #1e1b4b 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 700;
            color: white;
            box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.15);
        }}
        .profile-info h1 {{
            font-size: 26px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }}
        .handle-tag {{
            font-family: monospace;
            background: rgba(255, 255, 255, 0.1);
            color: #38bdf8;
            padding: 3px 10px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 8px;
        }}
        .badges-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .badge {{
            font-size: 11.5px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.08);
            color: #cbd5e1;
            border: 1px solid rgba(255, 255, 255, 0.12);
        }}
        .badge-active {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border-color: rgba(16, 185, 129, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .dot {{ width: 7px; height: 7px; border-radius: 50%; background: #34d399; }}
        .btn-hire {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 22px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
        }}
        .summary-card {{
            margin: 24px 32px;
            padding: 20px;
            border-radius: 12px;
            background: var(--slate-100);
            border-left: 4px solid var(--primary);
        }}
        .summary-card h3 {{
            font-size: 15px;
            color: var(--slate-900);
            margin-bottom: 6px;
        }}
        .summary-card p {{
            font-size: 13.5px;
            color: var(--slate-600);
            line-height: 1.5;
        }}
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin: 0 32px 24px 32px;
        }}
        .card-item {{
            background: white;
            border: 1px solid var(--slate-200);
            border-radius: 12px;
            padding: 16px;
        }}
        .card-item-title {{
            font-size: 12px;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--slate-500);
            margin-bottom: 6px;
        }}
        .card-item-val {{
            font-size: 13px;
            color: var(--slate-900);
            line-height: 1.4;
        }}
        .tabs-nav {{
            display: flex;
            border-bottom: 1px solid var(--slate-200);
            padding: 0 32px;
            background: #ffffff;
            gap: 24px;
        }}
        .tab {{
            padding: 14px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--slate-500);
            border-bottom: 2px solid transparent;
            cursor: pointer;
        }}
        .tab.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
        }}
        .content-area {{
            padding: 32px;
        }}
        .section-h2 {{
            font-size: 19px;
            color: var(--slate-900);
            margin: 28px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--slate-200);
        }}
        .section-h3 {{
            font-size: 15.5px;
            color: var(--primary);
            margin: 20px 0 8px 0;
        }}
        .section-h4 {{
            font-size: 14px;
            color: var(--slate-700);
            margin: 14px 0 6px 0;
        }}
        .body-p {{
            font-size: 14px;
            color: var(--slate-700);
            margin-bottom: 12px;
            line-height: 1.6;
        }}
        .bullet-item {{
            font-size: 13.5px;
            color: var(--slate-700);
            margin-left: 20px;
            margin-bottom: 6px;
        }}
        .numbered-item {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 8px;
            font-size: 13.5px;
        }}
        .num-badge {{
            color: var(--primary);
            font-weight: 700;
            min-width: 22px;
        }}
        .table-container {{
            overflow-x: auto;
            margin: 16px 0 24px 0;
            border-radius: 8px;
            border: 1px solid var(--slate-200);
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }}
        .data-table th {{
            background: var(--slate-100);
            padding: 10px 14px;
            font-weight: 600;
            color: var(--slate-900);
            border-bottom: 1px solid var(--slate-200);
        }}
        .data-table td {{
            padding: 10px 14px;
            border-bottom: 1px solid var(--slate-200);
            color: var(--slate-700);
        }}
        .data-table tr:nth-child(even) {{
            background: #fafafa;
        }}
        .code-block {{
            background: var(--slate-900);
            color: #f8fafc;
            padding: 16px;
            border-radius: 10px;
            font-family: Consolas, Monaco, monospace;
            font-size: 12.5px;
            overflow-x: auto;
            margin: 16px 0;
            line-height: 1.45;
        }}
        .footer {{
            padding: 24px 32px;
            background: var(--slate-100);
            border-top: 1px solid var(--slate-200);
            text-align: center;
            font-size: 12.5px;
            color: var(--slate-500);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Profile Banner -->
        <div class="header-top">
            <div class="breadcrumb">
                Home / Agent / <span>{bot_cfg['handle']}</span>
            </div>
            <div class="profile-row">
                <div class="profile-left">
                    <div class="avatar">{bot_cfg['initials']}</div>
                    <div class="profile-info">
                        <h1>{bot_cfg['code']} | {bot_cfg['short_name']}</h1>
                        <div class="handle-tag">{bot_cfg['handle']}</div>
                        <div class="badges-row">
                            <span class="badge badge-active"><span class="dot"></span> Selalu aktif</span>
                            <span class="badge">Divisi Content & Creative</span>
                            <span class="badge">Konsolidasi 4-Bot</span>
                            <span class="badge">Colorbox Pegawai AI</span>
                        </div>
                    </div>
                </div>
                <div>
                    <button class="btn-hire">Rekrut Pegawai AI</button>
                </div>
            </div>
        </div>

        <!-- Summary Card -->
        <div class="summary-card">
            <h3>Ringkasan Eksekutif & Misi Jabatan</h3>
            <p>{bot_cfg['tagline']}</p>
            <p style="margin-top: 8px; font-weight: 600; color: var(--primary);">Integrasi: {bot_cfg['consolidation']}</p>
        </div>

        <!-- Quick 4 Cards Grid -->
        <div class="grid-cards">
            <div class="card-item">
                <div class="card-item-title">In-Scope (Fokus Utama)</div>
                <div class="card-item-val">{bot_cfg['in_scope']}</div>
            </div>
            <div class="card-item">
                <div class="card-item-title">Out-of-Scope (Batasan)</div>
                <div class="card-item-val">{bot_cfg['out_scope']}</div>
            </div>
            <div class="card-item">
                <div class="card-item-title">Masukan Diperlukan</div>
                <div class="card-item-val">{bot_cfg['inputs']}</div>
            </div>
            <div class="card-item">
                <div class="card-item-title">Hasil Deliverables</div>
                <div class="card-item-val">{bot_cfg['outputs']}</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="tabs-nav">
            <div class="tab active">Job desk & 11 Mandatory Checklist</div>
            <div class="tab">Alur SOP & State Machine</div>
            <div class="tab">Tools & Matriks Otorisasi</div>
        </div>

        <!-- Main Content Area -->
        <div class="content-area">
            {body_content}
        </div>

        <!-- Footer -->
        <div class="footer">
            Dokumen Profiling Resmi Pegawai AI — Versi 2.0 (Arsitektur 4-Bot Konsolidasi) • PT AI Top Trends © 2026
        </div>
    </div>
</body>
</html>
"""
    return html_template

def make_mhtml(html_str, title, location="http://karyawan.ai/agent/"):
    boundary = "----=_NextPart_01DC5EA0.B1234567"
    mhtml = f"""From: <Saved by Blink>
Snapshot-Content-Location: {location}
Subject: {title}
Date: Mon, 23 Nov 2026 18:45:00 +0700
MIME-Version: 1.0
Content-Type: multipart/related;
	type="text/html";
	boundary="{boundary}"

--{boundary}
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: 8bit
Content-Location: {location}

{html_str}

--{boundary}--
"""
    return mhtml

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    print("="*70)
    print("BUILDING INDIVIDUAL BOT DOCS (DOCX, HTML, MHTML)")
    print("="*70)
    
    KARYAWAN_AI_DIR.mkdir(parents=True, exist_ok=True)
    SRC_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    for bot in BOTS_CONFIG:
        print(f"\n[BOT] Processing {bot['code']} | {bot['short_name']}...")
        
        # 1. Build DOCX
        doc = build_bot_docx(bot)
        
        # Save DOCX to all target locations
        karyawan_docx = KARYAWAN_AI_DIR / bot["docx_name"]
        try:
            doc.save(str(karyawan_docx))
            print(f"  [+] Saved DOCX: {karyawan_docx}")
        except PermissionError:
            print(f"  [!] Note: {karyawan_docx.name} sedang dibuka oleh aplikasi lain (Word). Melewati penimpaan file ini.")
        
        backend_docx = SRC_DOCS_DIR / bot["docx_name"]
        try:
            doc.save(str(backend_docx))
            print(f"  [+] Saved DOCX: {backend_docx}")
        except PermissionError:
            pass
        
        frontend_docx = FRONTEND_DIR / "docs-kaf" / "sprint5" / bot["docx_name"]
        frontend_docx.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc.save(str(frontend_docx))
            print(f"  [+] Saved DOCX: {frontend_docx}")
        except PermissionError:
            pass
        
        artifact_docx = ARTIFACT_DIR / bot["docx_name"]
        try:
            doc.save(str(artifact_docx))
            print(f"  [+] Saved DOCX: {artifact_docx}")
        except PermissionError:
            pass
        
        # 2. Build HTML
        html_content = build_bot_html(bot)
        
        karyawan_html = KARYAWAN_AI_DIR / bot["html_name"]
        karyawan_html.write_text(html_content, encoding="utf-8")
        print(f"  [+] Saved HTML: {karyawan_html}")
        
        backend_html = SRC_DOCS_DIR / bot["html_name"]
        backend_html.write_text(html_content, encoding="utf-8")
        print(f"  [+] Saved HTML: {backend_html}")
        
        artifact_html = ARTIFACT_DIR / bot["html_name"]
        artifact_html.write_text(html_content, encoding="utf-8")
        print(f"  [+] Saved HTML: {artifact_html}")
        
        # 3. Build MHTML
        mhtml_content = make_mhtml(html_content, f"Karyawan AI — {bot['code']} {bot['short_name']}", f"http://karyawan.ai/agent/{bot['handle'].replace('@', '')}")
        
        karyawan_mhtml = KARYAWAN_AI_DIR / bot["mhtml_name"]
        karyawan_mhtml.write_text(mhtml_content, encoding="utf-8")
        print(f"  [+] Saved MHTML: {karyawan_mhtml}")
        
        backend_mhtml = SRC_DOCS_DIR / bot["mhtml_name"]
        backend_mhtml.write_text(mhtml_content, encoding="utf-8")
        print(f"  [+] Saved MHTML: {backend_mhtml}")

        artifact_mhtml = ARTIFACT_DIR / bot["mhtml_name"]
        artifact_mhtml.write_text(mhtml_content, encoding="utf-8")
        print(f"  [+] Saved MHTML: {artifact_mhtml}")

    print("\n" + "="*70)
    print("ALL INDIVIDUAL BOT DOCS (DOCX, HTML, MHTML) GENERATED SUCCESSFULLY!")
    print("="*70)

if __name__ == "__main__":
    main()
