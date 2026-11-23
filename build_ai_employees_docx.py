"""
Generator Buku Panduan & Profiling Pegawai AI (Divisi Content & Creative)
Menghasilkan dokumen Word (.docx) berstandar eksekutif, rapi, dan mudah dipahami
oleh pengguna non-IT (pemilik bisnis, brand manager, marketer).
"""

import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

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

def add_header_footer(doc):
    for sec in doc.sections:
        # Header
        header = sec.header
        p_hdr = header.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_hdr = p_hdr.add_run("AI Top Trends — Profiling 4 Pegawai AI (Content & Creative)")
        r_hdr.font.name = "Calibri"
        r_hdr.font.size = Pt(8.5)
        r_hdr.font.color.rgb = RGBColor(148, 163, 184)
        
        # Footer
        footer = sec.footer
        p_ftr = footer.paragraphs[0]
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_ftr = p_ftr.add_run("Dokumen Panduan Pengguna Non-IT | Versi 2.0 | Rahasia & Hak Cipta PT AI Top Trends")
        r_ftr.font.name = "Calibri"
        r_ftr.font.size = Pt(8.5)
        r_ftr.font.color.rgb = RGBColor(148, 163, 184)

def add_callout(doc, title, text, bg_hex="F1F5F9", border_color="0284C7"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=160, bottom=160, left=200, right=200)
    
    # Left border only
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
    r_title.font.size = Pt(11)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    r_text = p.add_run(text)
    r_text.font.name = "Calibri"
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = RGBColor(51, 65, 85)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

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

def add_heading_1(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138) # Navy Blue
    return h

def add_heading_2(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = RGBColor(14, 116, 144) # Cyan/Dark Teal
    return h

def add_heading_3(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = RGBColor(51, 65, 85)
    return h

def add_p(doc, text, bold_prefix="", space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def add_bullet(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def build_buku_panduan_docx():
    doc = docx.Document()
    
    # 0.8 inch margins for clean spacious layout
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.85)
        sec.right_margin = Inches(0.85)
        
    add_header_footer(doc)
    
    # ================= COVER / TITLE BLOCK =================
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(4)
    run_t = p_title.add_run("Buku Panduan & Profiling 4 Pegawai AI")
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(24)
    run_t.font.bold = True
    run_t.font.color.rgb = RGBColor(30, 58, 138) # Deep Navy
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run("Divisi Content & Creative | Panduan Operasional untuk Pengguna Bisnis & Non-IT")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)
    
    # Metadata badge table
    meta_tbl = doc.add_table(rows=1, cols=4)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_tbl, color="CBD5E1")
    format_cell(meta_tbl.cell(0, 0), "🏢 PT AI Top Trends", bold=True, color=(30, 58, 138), bg_hex="F8FAFC", align=WD_ALIGN_PARAGRAPH.CENTER)
    format_cell(meta_tbl.cell(0, 1), "🎯 Versi 2.0 (4 Pegawai Terpadu)", bold=True, color=(14, 116, 144), bg_hex="F8FAFC", align=WD_ALIGN_PARAGRAPH.CENTER)
    format_cell(meta_tbl.cell(0, 2), "👤 Penanggung Jawab: Ivana", bold=True, color=(15, 23, 42), bg_hex="F8FAFC", align=WD_ALIGN_PARAGRAPH.CENTER)
    format_cell(meta_tbl.cell(0, 3), "📅 November 2026", bold=True, color=(71, 85, 105), bg_hex="F8FAFC", align=WD_ALIGN_PARAGRAPH.CENTER)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    
    # Executive Summary Callout
    add_callout(
        doc,
        "📌 Ringkasan Eksekutif untuk Pemilik Bisnis & Pengguna Non-IT",
        "Dokumen ini dirancang khusus agar Anda—pemilik brand, manajer pemasaran, maupun staf operasional—dapat memahami dan mengoperasikan 4 Pegawai AI divisi Content & Creative dengan sangat mudah tanpa perlu keahlian teknis pemrograman.\n\n"
        "Keempat Pegawai AI ini bekerja layaknya satu tim agensi kreatif digital yang terkoordinasi penuh: mulai dari menyusun pilar strategi, menulis naskah persuasif, merancang visual carousel & motion, hingga menyiapkan storyboard video pendek UGC. Seluruh pekerjaan dijalankan secara otomatis namun tetap 100% aman di bawah kendali Anda melalui Sistem Otorisasi 3 Tingkat.",
        bg_hex="EFF6FF",
        border_color="2563EB"
    )

    # ================= BAB 1 =================
    add_heading_1(doc, "Bab 1: Struktur Tim Kreatif Terpadu & Alur Kerja")
    add_p(doc, "Untuk memastikan pekerjaan berjalan gesit, hemat biaya, dan mudah dimonitor, 8 jabatan kreatif awal disederhanakan menjadi 4 Pegawai AI Utama yang memiliki spesialisasi terpadu:")

    # Table 4 Consolidated Roles
    tbl_roles = doc.add_table(rows=5, cols=4)
    tbl_roles.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_roles)
    
    headers = ["Kode", "Nama Pegawai AI", "Peran yang Digabung", "Fokus Utama bagi Bisnis Anda"]
    for i, h in enumerate(headers):
        format_cell(tbl_roles.cell(0, i), h, bold=True, color=(255, 255, 255), bg_hex="1E3A8A")
        
    roles_data = [
        ("CRE-01", "Content Strategist", "Strategist + Distribution", "Menyusun tema konten bulanan, jadwal tayang, creative brief, dan antrean posting media sosial."),
        ("CRE-02", "Content & Copywriter", "Content Writer + Copywriter", "Menulis naskah slide carousel, caption Instagram/TikTok, headline memikat, teks iklan, dan artikel SEO."),
        ("CRE-03", "Graphic & Motion Designer", "Graphic + Motion Specialist", "Merancang visual carousel 5 slide 4:5, poster promo, banner website, dan animasi teks/logo bergerak."),
        ("CRE-04", "Video & UGC Creator", "Video Creator + UGC Specialist", "Menyusun konsep video pendek 9:16 (TikTok/Reels), naskah storyboard detik-demi-detik, dan panduan rekaman talent HP.")
    ]
    for row_idx, data in enumerate(roles_data, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data):
            bold = (col_idx == 1)
            color = (30, 58, 138) if col_idx == 0 else (15, 23, 42) if col_idx == 1 else (51, 65, 85)
            format_cell(tbl_roles.cell(row_idx, col_idx), val, bold=bold, color=color, bg_hex=bg)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    add_heading_2(doc, "Bagaimana Keempat Pegawai AI Ini Bekerja Bersama?")
    add_p(doc, "Anda tidak perlu mengatur setiap bot satu per satu. Cukup berikan satu instruksi awal (misal: 'Buatkan materi promosi peluncuran kemeja dan celana jeans baru untuk bulan depan'), maka keempat pegawai akan bekerja secara estafet otomatis:")
    add_bullet(doc, " menganalisis katalog produk Anda, menentukan sudut pandang kampanye, dan membuat jadwal tayang kalender serta arahan kreatif.", "1. CRE-01 (Content Strategist)")
    add_bullet(doc, " menerima arahan CRE-01 lalu menulis naskah slide-by-slide lengkap dengan kalimat pembuka (hook) yang bikin penasaran serta caption penjualan.", "2. CRE-02 (Content & Copywriter)")
    add_bullet(doc, " mengambil foto asli baju dari katalog Anda, memadukannya dengan latar belakang estetik, memastikan tulisan tidak terpotong, dan mengekspor gambar beresolusi tinggi.", "3. CRE-03 (Graphic & Motion Designer)")
    add_bullet(doc, " menyusun naskah video pendek 30 detik gaya review jujur (UGC) lengkap dengan panduan ekspresi dan sudut kamera smartphone untuk kreator/talent Anda.", "4. CRE-04 (Video & UGC Creator)")
    add_bullet(doc, " mengumpulkan seluruh hasil visual dan naskah, lalu menyajikan draf siap tayang ke meja review Anda untuk disetujui dalam 1-klik.", "5. Kembali ke CRE-01")

    # ================= BAB 2 =================
    add_heading_1(doc, "Bab 2: Sistem Keamanan & Kendali Bisnis (3 Level Otorisasi)")
    add_p(doc, "Kekhawatiran terbesar pemilik bisnis terhadap AI adalah risiko 'bot memposting hal memalukan atau mengarang harga sendiri'. Di PT AI Top Trends, kami menanamkan Sistem Otorisasi 3 Level untuk menjamin kendali penuh selalu di tangan Anda:")

    tbl_levels = doc.add_table(rows=4, cols=3)
    tbl_levels.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_levels)
    
    lvl_headers = ["Tingkat Otorisasi", "Arti bagi Pemilik Bisnis", "Contoh Tindakan"]
    for i, h in enumerate(lvl_headers):
        format_cell(tbl_levels.cell(0, i), h, bold=True, color=(255, 255, 255), bg_hex="0F172A")
        
    lvl_data = [
        ("🟢 Level 1: Mandiri (Autonomous)", "Bot bekerja otomatis di balik layar. Aman tanpa risiko karena hanya berupa draf internal.", "Membaca katalog, riset tren hashtag, membuat draf naskah, merancang layout gambar kanvas, menyusun storyboard."),
        ("🟡 Level 2: Wajib Persetujuan (Approval Required)", "Bot BERHENTI dan MENUNGGU klik persetujuan Anda di aplikasi sebelum tindakan dilakukan.", "Mengunci kalender konten bulanan, memasukkan postingan ke antrean media sosial, merilis materi promo diskon."),
        ("🔴 Level 3: Khusus Manusia (Human-in-the-Loop)", "Bot DILARANG KERAS mengeksekusi. Hanya boleh dikerjakan oleh pemilik bisnis secara manual.", "Mengubah logo/identitas brand, pernyataan resmi krisis/komplain hukum, pengeluaran uang budget iklan.")
    ]
    for row_idx, data in enumerate(lvl_data, start=1):
        bg = "ECFDF5" if row_idx == 1 else "FEF3C7" if row_idx == 2 else "FEF2F2"
        for col_idx, val in enumerate(data):
            bold = (col_idx == 0)
            color = (5, 150, 105) if (row_idx == 1 and col_idx == 0) else (217, 119, 6) if (row_idx == 2 and col_idx == 0) else (220, 38, 38) if (row_idx == 3 and col_idx == 0) else (15, 23, 42)
            format_cell(tbl_levels.cell(row_idx, col_idx), val, bold=bold, color=color, bg_hex=bg)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ================= BAB 3 =================
    add_heading_1(doc, "Bab 3: Profil Pegawai AI 1 — CRE-01 Content Strategist")
    add_callout(
        doc,
        "🎯 Siapa CRE-01 dalam Bahasa Sederhana?",
        "CRE-01 adalah 'Kepala Perencana & Pengatur Jadwal Konten Anda'. Dialah yang memikirkan konten apa yang cocok tayang hari Senin, topik apa yang ramai di hari Jumat, produk mana yang perlu diangkat, serta memastikan postingan terbit tepat waktu tanpa Anda perlu repot menjadwalkan manual satu per satu.",
        bg_hex="F0FDF4",
        border_color="16A34A"
    )
    
    add_heading_2(doc, "A. Tugas Utama & Apa yang Anda Dapatkan")
    add_bullet(doc, " Membagi tema postingan Anda secara proporsional (misal: 45% Edukasi Tips Berpakaian, 30% Hiburan Relate, 15% Katalog Jualan, 10% Kisah Pelanggan).", "Pilar Konten Terstruktur:")
    add_bullet(doc, " Jadwal tayang lengkap 30 hari berisi tanggal, jam posting terbaik (peak hours), format konten (Carousel/Video), dan produk sorotan.", "Kalender Konten Siap Pakai:")
    add_bullet(doc, " Panduan detail yang diberikan kepada penulis naskah dan desainer agar hasil visualnya tidak melenceng dari identitas brand Anda.", "Creative Brief Terarah:")
    add_bullet(doc, " Menghubungkan postingan ke akun Instagram, TikTok, atau WhatsApp bisnis Anda setelah Anda menyetujuinya.", "Pengatur Antrean Media Sosial:")

    add_heading_2(doc, "B. Batasan Kerja (Apa yang BUKAN Tugasnya)")
    add_bullet(doc, "CRE-01 tidak menulis caption panjang atau mendesain gambar sendiri; tugas tersebut langsung ia delegasikan ke CRE-02 dan CRE-03.")
    add_bullet(doc, "CRE-01 TIDAK BISA memposting langsung ke media sosial Anda tanpa klik 'Setujui' dari Anda (Level 2 Approval).")

    add_heading_2(doc, "C. Contoh Perintah Mudah (Prompt yang Bisa Anda Gunakan)")
    add_callout(
        doc,
        "💬 Contoh Cara Menyuruh CRE-01:",
        "• 'CRE-01, buatkan kalender konten Instagram untuk bulan depan bertema koleksi musim hujan Colorbox.'\n"
        "• 'Tolong riset 3 topik tren fesyen Gen Z yang lagi viral di TikTok dan cocok buat brand kita.'\n"
        "• 'Konten kita minggu lalu sepi. Coba evaluasi jam postingnya dan buatkan jadwal baru yang lebih pas.'",
        bg_hex="F8FAFC",
        border_color="64748B"
    )

    # ================= BAB 4 =================
    add_heading_1(doc, "Bab 4: Profil Pegawai AI 2 — CRE-02 Content & Copywriter")
    add_callout(
        doc,
        "✍️ Siapa CRE-02 dalam Bahasa Sederhana?",
        "CRE-02 adalah 'Penulis Kata-Kata Pemikat & Penjual'. Jika Anda sering pusing memikirkan kata-kata pembuka postingan (hook) yang bikin orang berhenti scrolling, atau bingung menulis caption yang bikin orang mau klik beli, CRE-02 yang akan merangkai kata-katanya secara profesional, asik, dan sesuai gaya bahasa pelanggan Anda.",
        bg_hex="FAF5FF",
        border_color="9333EA"
    )

    add_heading_2(doc, "A. Tugas Utama & Apa yang Anda Dapatkan")
    add_bullet(doc, " Kalimat pembuka 3 detik pertama yang bikin orang penasaran dan tidak langsung men-skip postingan Anda.", "Hook Thumb-Stopping:")
    add_bullet(doc, " Teks narasi dari slide 1 sampai slide 5 yang tersusun rapi, ringkas, dan enak dibaca di layar HP.", "Naskah Slide Carousel:")
    add_bullet(doc, " Caption media sosial lengkap dengan emoji pas, ajakan bertindak (Call to Action), dan hashtag terkurasi.", "Caption Siap Copy-Paste:")
    add_bullet(doc, " Teks iklan untuk Facebook/Instagram Ads berbasis formula psikologi penjualan (AIDA, PAS).", "Naskah Iklan Berbayar:")
    add_bullet(doc, " Artikel panduan gaya atau artikel website yang mudah ditemukan di pencarian Google.", "Artikel Blog Edukasi SEO:")

    add_heading_2(doc, "B. Jaminan Anti-Halusinasi Produk")
    add_p(doc, "CRE-02 memiliki aturan ketat: ia HANYA BOLEH menuliskan nama produk, warna pakaian, dan harga resmi yang benar-benar tercantum di katalog Anda. Ia dilarang keras mengarang diskon fiktif atau menjanjikan klaim yang berlebihan.")

    add_heading_2(doc, "C. Contoh Perintah Mudah")
    add_callout(
        doc,
        "💬 Contoh Cara Menyuruh CRE-02:",
        "• 'CRE-02, tuliskan naskah carousel 5 slide tentang trik padu padan kemeja chambray biar keliatan tinggi.'\n"
        "• 'Buatkan 3 pilihan caption Instagram yang gayanya santai ala anak kulineran buat produk celana denim.'\n"
        "• 'Bikinin copy iklan Meta Ads buat promo payday akhir bulan dengan target mahasiswi.'",
        bg_hex="F8FAFC",
        border_color="64748B"
    )

    # ================= BAB 5 =================
    add_heading_1(doc, "Bab 5: Profil Pegawai AI 3 — CRE-03 Graphic & Motion Designer")
    add_callout(
        doc,
        "🎨 Siapa CRE-03 dalam Bahasa Sederhana?",
        "CRE-03 adalah 'Desainer Visual & Kreator Gambar Bergerak'. Dialah yang mengubah naskah dari CRE-02 dan foto baju dari katalog Anda menjadi gambar carousel Instagram yang estetik, modern, rapi, serta membuat animasi teks atau logo gerak yang memanjakan mata penonton.",
        bg_hex="FFFBEB",
        border_color="D97706"
    )

    add_heading_2(doc, "A. Tugas Utama & Apa yang Anda Dapatkan")
    add_bullet(doc, " Desain 5 slide gambar beresolusi tajam (1080x1350 px) dengan komposisi warna dan tata letak modern.", "Gambar Carousel Instagram:")
    add_bullet(doc, " Desain banner promosi toko untuk Shopee, Tokopedia, website resmi, maupun status WhatsApp.", "Banner Toko Online:")
    add_bullet(doc, " Teks judul yang muncul dengan efek animasi halus, panah gerak penunjuk harga, dan logo bumper 3 detik.", "Animasi Gerak (Motion Graphics):")
    add_bullet(doc, " Tautan halaman web interaktif di mana Anda bisa menggeser slide carousel langsung di browser sebelum memutuskan mengunggahnya.", "Pratinjau Langsung (Live Preview):")

    add_heading_2(doc, "B. Jaminan Kualitas Visual (Bebas Teks Terpotong)")
    add_bullet(doc, "Seluruh tulisan judul dan harga dikunci di zona aman kanvas, sehingga saat tampil di profil Instagram, gambar dan tulisan tidak akan pernah terpotong (Zero Text Clipping).", "Zona Aman 100%:")
    add_bullet(doc, "Warna pakaian pada gambar hasil olahan dijamin identik dengan warna kain baju aslinya (tidak dibuat abu-abu atau berubah warna).", "Warna Produk Asli:")

    add_heading_2(doc, "C. Contoh Perintah Mudah")
    add_callout(
        doc,
        "💬 Contoh Cara Menyuruh CRE-03:",
        "• 'CRE-03, render desain 5 slide carousel Instagram untuk naskah kemeja chambray yang dibuat CRE-02.'\n"
        "• 'Tolong buatkan banner promo gajian ukuran persegi 1:1 dan Story 9:16 dengan warna brand Colorbox.'\n"
        "• 'Buatkan animasi teks judul bergerak 3 detik: \"1 Kemeja, 3 Gaya Ngampus\".'",
        bg_hex="F8FAFC",
        border_color="64748B"
    )

    # ================= BAB 6 =================
    add_heading_1(doc, "Bab 6: Profil Pegawai AI 4 — CRE-04 Video & UGC Creator")
    add_callout(
        doc,
        "📱 Siapa CRE-04 dalam Bahasa Sederhana?",
        "CRE-04 adalah 'Sutradara Video Pendek TikTok & Reels Bergaya Autentik'. Dia tahu persis video seperti apa yang disukai penonton zaman sekarang—bukan iklan kaku TV zaman dulu, melainkan video santai bergaya review jujur (UGC) yang direkam pakai HP, seru, dan terasa seperti rekomendasi teman akrab.",
        bg_hex="FEF2F2",
        border_color="EF4444"
    )

    add_heading_2(doc, "A. Tugas Utama & Apa yang Anda Dapatkan")
    add_bullet(doc, " Naskah video vertikal 15–30 detik yang membagi adegan detik-demi-detik (apa yang dilakukan di kamera, apa yang diucapkan suara).", "Tabel Storyboard Lengkap:")
    add_bullet(doc, " Panduan praktis bagi talent/kreator Anda (cara memegang HP, sudut cermin kamar, ekspresi wajah, dan intonasi suara).", "Panduan Talent Smartphone:")
    add_bullet(doc, " Rekomendasi musik TikTok yang sedang viral dan cocok dengan ritme adegan video Anda.", "Rekomendasi Musik & Audio Tren:")
    add_bullet(doc, " Teks takarir dinamis di layar sehingga orang yang menonton tanpa menyalakan suara HP tetap memahami 100% isi video.", "Takarir Ramah Tanpa Suara:")

    add_heading_2(doc, "B. Standar Kejujuran Konten (Etika UGC)")
    add_p(doc, "CRE-04 memiliki prinsip kejujuran: ia tidak akan menyuruh talent Anda membuat ulasan palsu (misal: mengaku sudah pakai baju 5 tahun padahal baju baru rilis). Semua testimoni diarahkan pada kenyamanan nyata dan keindahan potongan busana.")

    add_heading_2(doc, "C. Contoh Perintah Mudah")
    add_callout(
        doc,
        "💬 Contoh Cara Menyuruh CRE-04:",
        "• 'CRE-04, buatkan storyboard video TikTok 30 detik gaya unboxing & styling kemeja baru.'\n"
        "• 'Bikinin konsep video Reels POV relatable: \"Ketika buru-buru ngampus tapi baju tetap rapi\".'\n"
        "• 'Tolong siapkan panduan talent buat kreator kita yang mau bikin video review celana jeans.'",
        bg_hex="F8FAFC",
        border_color="64748B"
    )

    # ================= BAB 7 =================
    add_heading_1(doc, "Bab 7: Checklist Kesiapan Klien (Panduan Memulai)")
    add_p(doc, "Agar keempat Pegawai AI dapat bekerja dengan hasil maksimal dan 100% akurat sejak hari pertama, berikut file yang perlu Anda siapkan dan unggah ke dalam sistem:")

    tbl_prep = doc.add_table(rows=5, cols=3)
    tbl_prep.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_prep)
    
    prep_headers = ["No", "Dokumen / Data yang Diunggah", "Manfaat bagi Pegawai AI Anda"]
    for i, h in enumerate(prep_headers):
        format_cell(tbl_prep.cell(0, i), h, bold=True, color=(255, 255, 255), bg_hex="1E3A8A")
        
    prep_data = [
        ("1", "Buku Panduan Merek (Brand Guidelines)", "Memastikan warna desain (hex code), gaya font, logo, dan gaya bicara naskah tidak melenceng dari identitas brand Anda."),
        ("2", "Katalog Produk & Daftar Harga Resmi", "Mencegah bot salah menyebut harga atau nama pakaian. Semua foto produk diambil langsung dari katalog resmi ini."),
        ("3", "Daftar Pertanyaan Pelanggan (FAQ)", "Membantu bot memahami kekhawatiran pembeli (misal: ukuran baju, bahan melar/tidak) untuk dijadikan bahan konten edukasi."),
        ("4", "Kalender Acara & Rencana Promo", "Memberi tahu bot kapan ada momen penting (Payday promo, 12.12, Hari Ibu, Liburan) agar kalender konten langsung menyesuaikan.")
    ]
    for row_idx, data in enumerate(prep_data, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data):
            bold = (col_idx == 1)
            format_cell(tbl_prep.cell(row_idx, col_idx), val, bold=bold, color=(15, 23, 42) if bold else (51, 65, 85), bg_hex=bg)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    
    add_callout(
        doc,
        "💡 Tips Emas Berkomunikasi dengan Pegawai AI Anda:",
        "1. Berbicaralah seperti Anda berbicara dengan staf kreatif manusia di kantor: sebutkan produk apa yang ingin dipromosikan dan untuk siapa targetnya.\n"
        "2. Jangan ragu meminta revisi: jika Anda merasa caption kurang santai atau warna poster kurang cerah, katakan saja: 'Tolong buatkan versi yang lebih kasual' atau 'Tolong buat latarnya lebih terang'.\n"
        "3. Pantau status pekerjaan di papan Kanban: Anda bisa melihat kartu tugas berpindah secara rapi dari 'Perencanaan' ➔ 'Menunggu Persetujuan' ➔ 'Selesai'.",
        bg_hex="F0FDF4",
        border_color="16A34A"
    )

    return doc

if __name__ == "__main__":
    doc = build_buku_panduan_docx()
    out_dir_backend = Path("backend/docs-kaf/sprint5")
    out_dir_frontend = Path("frontend/docs-kaf/sprint5")
    out_dir_root = Path(".")
    
    file_name = "Buku_Panduan_dan_Profiling_4_Pegawai_AI_Content_Creative.docx"
    
    out_dir_backend.mkdir(parents=True, exist_ok=True)
    out_dir_frontend.mkdir(parents=True, exist_ok=True)
    
    p1 = out_dir_backend / file_name
    p2 = out_dir_frontend / file_name
    p3 = out_dir_root / file_name
    
    doc.save(str(p1))
    doc.save(str(p2))
    doc.save(str(p3))
    print(f"Berhasil menghasilkan dokumen Word: {p1}")
