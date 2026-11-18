import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # blank layout

    # Color definitions
    C_BG_DARK = RGBColor(15, 23, 42)      # Slate 900
    C_BG_LIGHT = RGBColor(248, 250, 252)  # Slate 50
    C_CARD_BG = RGBColor(255, 255, 255)   # White
    C_CARD_BORDER = RGBColor(226, 232, 240) # Slate 200
    C_TEXT_DARK = RGBColor(15, 23, 42)    # Slate 900
    C_TEXT_BODY = RGBColor(51, 65, 85)    # Slate 700
    C_TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500
    C_BRAND = RGBColor(14, 165, 233)      # Sky 500
    C_BRAND_GREEN = RGBColor(16, 185, 129)# Emerald 500
    C_ACCENT_BLUE = RGBColor(37, 99, 235) # Blue 600
    C_TAG_BG = RGBColor(241, 245, 249)    # Slate 100

    def add_bg(slide, dark=False):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG_DARK if dark else C_BG_LIGHT
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="PERSIAPAN & DEPLOYMENT VPS"):
        # Category Tag
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8), Inches(0.35))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_bottom = tf_tag.margin_right = 0
        p_tag = tf_tag.paragraphs[0]
        r_tag = p_tag.add_run()
        r_tag.text = category_text.upper()
        r_tag.font.name = "Arial"
        r_tag.font.size = Pt(10)
        r_tag.font.bold = True
        r_tag.font.color.rgb = C_BRAND

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_bottom = tf_title.margin_right = 0
        p_title = tf_title.paragraphs[0]
        r_title = p_title.add_run()
        r_title.text = title_text
        r_title.font.name = "Arial"
        r_title.font.size = Pt(22)
        r_title.font.bold = True
        r_title.font.color.rgb = C_TEXT_DARK

    def add_card(slide, left, top, width, height, bg_color=C_CARD_BG, border_color=C_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # ==========================================
    # SLIDE 1: Title Slide (Dark Theme)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    add_bg(s1, dark=True)

    # Accent decorative box
    dec = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(0.15), Inches(4.2))
    dec.fill.solid()
    dec.fill.fore_color.rgb = C_BRAND
    dec.line.fill.background()

    # Title box
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(11.2), Inches(4.2))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p1 = tf.paragraphs[0]
    r = p1.add_run()
    r.text = "LAPORAN PERSIAPAN & DEPLOYMENT VPS"
    r.font.name = "Arial"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = C_BRAND

    p2 = tf.add_paragraph()
    p2.space_before = Pt(12)
    r2 = p2.add_run()
    r2.text = "Infrastruktur Cloud, Hermes Core v0.23+, Multi-Agent &\nIntegrasi WhatsApp CS Pegawai AI"
    r2.font.name = "Arial"
    r2.font.size = Pt(28)
    r2.font.bold = True
    r2.font.color.rgb = RGBColor(255, 255, 255)

    p3 = tf.add_paragraph()
    p3.space_before = Pt(20)
    r3 = p3.add_run()
    r3.text = "Transisi Sukses dari Lingkungan Lokal ke Server Cloud Produksi (Biznet Gio 139.190.107.151)"
    r3.font.name = "Arial"
    r3.font.size = Pt(14)
    r3.font.color.rgb = RGBColor(203, 213, 225)

    p4 = tf.add_paragraph()
    p4.space_before = Pt(36)
    r4 = p4.add_run()
    r4.text = "Presenter: "
    r4.font.bold = True
    r4.font.color.rgb = C_BRAND
    r4_val = p4.add_run()
    r4_val.text = "Faiz Febriawan  |  "
    r4_val.font.color.rgb = RGBColor(241, 245, 249)
    r4_tgt = p4.add_run()
    r4_tgt.text = "Target: "
    r4_tgt.font.bold = True
    r4_tgt.font.color.rgb = C_BRAND
    r4_tgt_val = p4.add_run()
    r4_tgt_val.text = "Lead & Mentor  |  "
    r4_tgt_val.font.color.rgb = RGBColor(241, 245, 249)
    r4_dt = p4.add_run()
    r4_dt.text = "Periode: "
    r4_dt.font.bold = True
    r4_dt.font.color.rgb = C_BRAND
    r4_dt_val = p4.add_run()
    r4_dt_val.text = "Sprint 4 MVP Readiness (November 2026)"
    r4_dt_val.font.color.rgb = RGBColor(241, 245, 249)
    for run in [r4, r4_val, r4_tgt, r4_tgt_val, r4_dt, r4_dt_val]:
        run.font.name = "Arial"
        run.font.size = Pt(12)

    # ==========================================
    # SLIDE 2: Executive Summary (Problem -> Action -> Result)
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_bg(s2)
    add_header(s2, "Executive Summary: Mengapa VPS & Apa yang Dihasilkan?")

    col_w = Inches(3.7)
    gap = Inches(0.3)
    card_top = Inches(1.8)
    card_h = Inches(5.0)

    # Card 1: Problem / Kebutuhan
    add_card(s2, Inches(0.8), card_top, col_w, card_h)
    tb1 = s2.shapes.add_textbox(Inches(1.0), card_top + Inches(0.2), col_w - Inches(0.4), card_h - Inches(0.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "1. Kebutuhan & Tantangan"
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = RGBColor(225, 29, 72) # Rose

    bullets1 = [
        "Localhost Tidak Bisa Kolaborasi: Selama ini aplikasi berjalan di laptop lokal pengembang, membatasi tim QA, mentor, dan stakeholders untuk menguji langsung.",
        "Ketergantungan Perangkat: Jika laptop mati atau koneksi putus, bot AI dan webhook berhenti berjalan.",
        "Integrasi Eksternal: Webhook WhatsApp Business (Meta) membutuhkan IP publik / URL cloud yang aktif 24/7 dan dapat menerima lalu lintas pesan secara stabil."
    ]
    for b in bullets1:
        p = tf1.add_paragraph()
        p.space_before = Pt(10)
        title, desc = b.split(": ", 1)
        r_b = p.add_run()
        r_b.text = "• " + title + ": "
        r_b.font.bold = True
        r_b.font.size = Pt(11)
        r_b.font.color.rgb = C_TEXT_DARK
        r_d = p.add_run()
        r_d.text = desc
        r_d.font.size = Pt(10.5)
        r_d.font.color.rgb = C_TEXT_BODY

    # Card 2: Solusi & Eksekusi
    add_card(s2, Inches(0.8) + col_w + gap, card_top, col_w, card_h)
    tb2 = s2.shapes.add_textbox(Inches(1.0) + col_w + gap, card_top + Inches(0.2), col_w - Inches(0.4), card_h - Inches(0.4))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "2. Eksekusi yang Dilakukan"
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_ACCENT_BLUE

    bullets2 = [
        "Provisi Server VPS: Mengonfigurasi Biznet Gio NEO Lite MS 4.4 (Ubuntu 22.04 LTS, 4 vCPU, 4GB RAM).",
        "Multi-Service Systemd: Memasang Hermes Agent Core v0.23+ dan FastAPI BFF sebagai background daemon otomatis.",
        "Nginx Reverse Proxy: Mengarahkan lalu lintas port 80 ke frontend statis Vite dan proxy /bff/ ke backend dengan injeksi header keamanan API.",
        "Cloud Database: Menghubungkan migrasi PostgreSQL ke Neon Serverless Cloud dengan connection pooling terproteksi."
    ]
    for b in bullets2:
        p = tf2.add_paragraph()
        p.space_before = Pt(10)
        title, desc = b.split(": ", 1)
        r_b = p.add_run()
        r_b.text = "• " + title + ": "
        r_b.font.bold = True
        r_b.font.size = Pt(11)
        r_b.font.color.rgb = C_TEXT_DARK
        r_d = p.add_run()
        r_d.text = desc
        r_d.font.size = Pt(10.5)
        r_d.font.color.rgb = C_TEXT_BODY

    # Card 3: Hasil Nyata
    add_card(s2, Inches(0.8) + (col_w + gap)*2, card_top, col_w, card_h)
    tb3 = s2.shapes.add_textbox(Inches(1.0) + (col_w + gap)*2, card_top + Inches(0.2), col_w - Inches(0.4), card_h - Inches(0.4))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "3. Dampak & Hasil Nyata"
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_BRAND_GREEN

    bullets3 = [
        "Server Aktif 24/7: Web App dan API live di http://139.190.107.151/ dapat diakses siapa saja kapan saja tanpa laptop pengembang.",
        "7 Agen AI Berjalan Serentak: 5 bot marketing resmi (Bimo, Meda, Raka, Bram, Vina) + 2 bot CS (Siti, Hendra).",
        "WhatsApp Gateway Siap: Mampu menerima webhook resmi Meta dan memiliki Web Simulator interaktif (/wa-tester.html).",
        "Performa Sangat Ringan: Pemakaian RAM stabil di 5-7%, CPU Load < 0.4, swap 0%."
    ]
    for b in bullets3:
        p = tf3.add_paragraph()
        p.space_before = Pt(10)
        title, desc = b.split(": ", 1)
        r_b = p.add_run()
        r_b.text = "• " + title + ": "
        r_b.font.bold = True
        r_b.font.size = Pt(11)
        r_b.font.color.rgb = C_TEXT_DARK
        r_d = p.add_run()
        r_d.text = desc
        r_d.font.size = Pt(10.5)
        r_d.font.color.rgb = C_TEXT_BODY

    # ==========================================
    # SLIDE 3: Arsitektur Sistem Produksi di VPS
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_bg(s3)
    add_header(s3, "Arsitektur Sistem: Integrasi Nginx, BFF, Hermes, dan Database")

    # 4 Architecture layer cards horizontally
    layer_w = Inches(11.7)
    
    # Layer 1: Client / Ingress
    add_card(s3, Inches(0.8), Inches(1.7), layer_w, Inches(1.1))
    tb_l1 = s3.shapes.add_textbox(Inches(1.0), Inches(1.75), layer_w - Inches(0.4), Inches(1.0))
    tf_l1 = tb_l1.text_frame
    tf_l1.word_wrap = True
    p = tf_l1.paragraphs[0]
    p.text = "1. INGRESS & REVERSE PROXY LAYER (Nginx Port 80)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_ACCENT_BLUE
    p_desc = tf_l1.add_paragraph()
    p_desc.text = "Nginx bertindak sebagai gerbang tunggal di IP 139.190.107.151. Melayani static assets Vite Frontend (/var/www/pegawai-ai) dan mem-proxy request /bff/ ke port 8090 dengan otomatis menginjeksi header autentikasi X-Pegawai-AI-Key."
    p_desc.font.size = Pt(10.5)
    p_desc.font.color.rgb = C_TEXT_BODY

    # Layer 2: BFF FastAPI
    add_card(s3, Inches(0.8), Inches(3.0), layer_w, Inches(1.2))
    tb_l2 = s3.shapes.add_textbox(Inches(1.0), Inches(3.05), layer_w - Inches(0.4), Inches(1.1))
    tf_l2 = tb_l2.text_frame
    tf_l2.word_wrap = True
    p = tf_l2.paragraphs[0]
    p.text = "2. BACKEND FOR FRONTEND (FastAPI Daemon - Port 8090)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_BRAND_GREEN
    p_desc = tf_l2.add_paragraph()
    p_desc.text = "Dikelola oleh systemd (pegawai-ai-bff.service). Menangani REST API, Server-Sent Events (SSE) streaming respons agen, manajemen jadwal eksekusi (Scheduler), tracking biaya token USD, serta Webhook WhatsApp & konektor tools pihak ketiga."
    p_desc.font.size = Pt(10.5)
    p_desc.font.color.rgb = C_TEXT_BODY

    # Layer 3: Hermes Agent Runtime
    add_card(s3, Inches(0.8), Inches(4.4), layer_w, Inches(1.2))
    tb_l3 = s3.shapes.add_textbox(Inches(1.0), Inches(4.45), layer_w - Inches(0.4), Inches(1.1))
    tf_l3 = tb_l3.text_frame
    tf_l3.word_wrap = True
    p = tf_l3.paragraphs[0]
    p.text = "3. AI AGENT RUNTIME CORE (Hermes Gateway - Port 8642)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(147, 51, 234) # Purple
    p_desc = tf_l3.add_paragraph()
    p_desc.text = "Dikelola oleh systemd (hermes-gateway.service). Menjalankan engine multi-agent v0.23+ dengan model penalaran DeepSeek V4.1 Flash via OpenCode provider. Mengisolasi 7 profil agen lengkap dengan SOUL.md, config.yaml, dan memory context."
    p_desc.font.size = Pt(10.5)
    p_desc.font.color.rgb = C_TEXT_BODY

    # Layer 4: Storage & Cloud Database
    add_card(s3, Inches(0.8), Inches(5.8), layer_w, Inches(1.1))
    tb_l4 = s3.shapes.add_textbox(Inches(1.0), Inches(5.85), layer_w - Inches(0.4), Inches(1.0))
    tf_l4 = tb_l4.text_frame
    tf_l4.word_wrap = True
    p = tf_l4.paragraphs[0]
    p.text = "4. DATA & PERSISTENCE LAYER (Neon Cloud PostgreSQL)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(234, 88, 12) # Orange
    p_desc = tf_l4.add_paragraph()
    p_desc.text = "Penyimpanan relasional terpusat dengan 19 skrip migrasi aktif (termasuk 019_whatsapp_messages.sql). Menggunakan AsyncConnectionPool dengan parameter daur ulang koneksi (max_idle=300) dan proteksi SSL terenkripsi."
    p_desc.font.size = Pt(10.5)
    p_desc.font.color.rgb = C_TEXT_BODY

    # ==========================================
    # SLIDE 4: Detail Provisi & Otomasi Deployment
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_bg(s4)
    add_header(s4, "Detail Provisi: Otomasi Setup & Zero-Downtime Daemon")

    card_w2 = Inches(5.7)
    card_h2 = Inches(5.0)

    # Left: Provisi OS & Dependensi
    add_card(s4, Inches(0.8), Inches(1.8), card_w2, card_h2)
    tb_p1 = s4.shapes.add_textbox(Inches(1.0), Inches(2.0), card_w2 - Inches(0.4), card_h2 - Inches(0.4))
    tf_p1 = tb_p1.text_frame
    tf_p1.word_wrap = True
    p = tf_p1.paragraphs[0]
    p.text = "Provisi Lingkungan & Runtime"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_TEXT_DARK

    steps1 = [
        "Sistem Operasi: Ubuntu 22.04 LTS dipasang di Biznet Gio Cloud NEO Lite MS 4.4.",
        "Package Manager Modern (uv): Menggunakan uv v0.13+ untuk instalasi Python 3.14 dan resolusi dependensi hermes & BFF secara deterministik.",
        "Hermes Core v0.23.0+: Berhasil terpasang versi vgit.27e3893 (2026.9.24) dengan OpenAI SDK v2.54.0.",
        "Frontend Vite Compilation: Build aset statis di lokal (HTML, CSS, JS bundle 666 KB) diupload langsung ke /var/www/pegawai-ai.",
        "Kunci Akses Aman: Kredensial sensitif disimpan pada file .env terisolasi di server VPS dan tidak pernah dicommit ke git publik."
    ]
    for s in steps1:
        p = tf_p1.add_paragraph()
        p.space_before = Pt(8)
        k, v = s.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "✔ " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(10.5)
        r_k.font.color.rgb = C_BRAND_GREEN
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = C_TEXT_BODY

    # Right: Systemd Services & Nginx
    add_card(s4, Inches(6.8), Inches(1.8), card_w2, card_h2)
    tb_p2 = s4.shapes.add_textbox(Inches(7.0), Inches(2.0), card_w2 - Inches(0.4), card_h2 - Inches(0.4))
    tf_p2 = tb_p2.text_frame
    tf_p2.word_wrap = True
    p = tf_p2.paragraphs[0]
    p.text = "Ketahanan Layanan (Systemd & Nginx)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_TEXT_DARK

    steps2 = [
        "hermes-gateway.service: Menjalankan daemon Hermes multi-profile di port 8642. Dikonfigurasi Restart=always dengan jeda 3 detik.",
        "pegawai-ai-bff.service: Menjalankan Uvicorn FastAPI di port 8090. Mengawasi koneksi database, healthcheck, dan routing WhatsApp.",
        "Nginx API Header Injection: Setiap panggilan dari browser ke /bff/ otomatis diinjeksi header X-Pegawai-AI-Key di level web server, mengamankan endpoint privat.",
        "Otomasi Skrip Deployment: Disediakan skrip Python berulang (redeploy_vps.py) yang mengupload perubahan, merefresh migrasi DB, dan merestart service secara instan.",
        "Pemulihan Mandiri (Self-Healing): Jika server reboot atau service crash, systemd otomatis menyalakan ulang seluruh komponen dalam hitungan detik."
    ]
    for s in steps2:
        p = tf_p2.add_paragraph()
        p.space_before = Pt(8)
        k, v = s.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "✔ " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(10.5)
        r_k.font.color.rgb = C_ACCENT_BLUE
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = C_TEXT_BODY

    # ==========================================
    # SLIDE 5: Konfigurasi 7 Bot Colorbox Resmi
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_bg(s5)
    add_header(s5, "Konfigurasi Multi-Agent: 5 Bot Marketing R&D & 2 Bot CS")

    # Left: 5 Marketing Bots
    add_card(s5, Inches(0.8), Inches(1.8), card_w2, card_h2)
    tb_m = s5.shapes.add_textbox(Inches(1.0), Inches(2.0), card_w2 - Inches(0.4), card_h2 - Inches(0.4))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    p = tf_m.paragraphs[0]
    p.text = "5 Bot Tim Pemasaran (Marketing R&D)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_BRAND

    m_bots = [
        ("Bimo (Lead Strategist)", "Menyusun strategi kampanye, roadmap konten, dan alokasi anggaran pemasaran Colorbox."),
        ("Meda (Social Media Lead)", "Mengelola interaksi audiens, tren viral TikTok/Reels, dan jadwal posting terpadu."),
        ("Raka (Copywriter & Content)", "Menulis naskah persuasif formula AIDA, caption Instagram Gen-Z, dan script video."),
        ("Bram (SEO & Performance)", "Riset kata kunci, optimasi SEO e-commerce, tracking CTR, dan evaluasi metrik konversi."),
        ("Vina (Creative & Visual Designer)", "Menyusun panduan visual lookbook, estetika pastel/earthy, dan prompt AI desain.")
    ]
    for name, desc in m_bots:
        p = tf_m.add_paragraph()
        p.space_before = Pt(8)
        r_n = p.add_run()
        r_n.text = "• " + name + ": "
        r_n.font.bold = True
        r_n.font.size = Pt(10.5)
        r_n.font.color.rgb = C_TEXT_DARK
        r_d = p.add_run()
        r_d.text = desc
        r_d.font.size = Pt(9.5)
        r_d.font.color.rgb = C_TEXT_BODY

    # Right: 2 CS Bots & Knowledge Grounding
    add_card(s5, Inches(6.8), Inches(1.8), card_w2, card_h2)
    tb_cs = s5.shapes.add_textbox(Inches(7.0), Inches(2.0), card_w2 - Inches(0.4), card_h2 - Inches(0.4))
    tf_cs = tb_cs.text_frame
    tf_cs.word_wrap = True
    p = tf_cs.paragraphs[0]
    p.text = "2 Bot Customer Service (CS Resmi)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_BRAND_GREEN

    cs_bots = [
        ("Siti (Frontline Support Specialist)", "Menjawab pesan WhatsApp pelanggan seputar info produk, ketersediaan stok, panduan ukuran (size chart), dan resi dengan gaya bahasa ramah ('Halo Kak... 💕')."),
        ("Hendra (CS Team Lead & Quality Auditor)", "Menangani eskalasi komplain P1 (barang robek, cacat produksi, sengketa retur/refund). Berwibawa, tegas, dan menjamin investigasi 1x24 jam.")
    ]
    for name, desc in cs_bots:
        p = tf_cs.add_paragraph()
        p.space_before = Pt(8)
        r_n = p.add_run()
        r_n.text = "• " + name + ": "
        r_n.font.bold = True
        r_n.font.size = Pt(10.5)
        r_n.font.color.rgb = C_TEXT_DARK
        r_d = p.add_run()
        r_d.text = desc
        r_d.font.size = Pt(9.5)
        r_d.font.color.rgb = C_TEXT_BODY

    p_kg = tf_cs.add_paragraph()
    p_kg.space_before = Pt(14)
    p_kg.text = "Grounding Pengetahuan Resmi Colorbox:"
    p_kg.font.bold = True
    p_kg.font.size = Pt(12)
    p_kg.font.color.rgb = C_TEXT_DARK

    rules = [
        "Kebijakan Retur 7 Hari: Wajib maksimal 7 hari kalender sejak produk diterima.",
        "Syarat Klaim Komplain: Wajib melampirkan video unboxing utuh dan barcode tag terpasang.",
        "Zero Hallucination: Agen dilarang menjanjikan garansi fiktif di luar dokumen kebijakan resmi."
    ]
    for r_text in rules:
        p = tf_cs.add_paragraph()
        p.space_before = Pt(4)
        k, v = r_text.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "✔ " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(9.5)
        r_k.font.color.rgb = RGBColor(16, 185, 129)
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(9)
        r_v.font.color.rgb = C_TEXT_BODY

    # ==========================================
    # SLIDE 6: Integrasi WhatsApp CS & Web Simulator
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_bg(s6)
    add_header(s6, "Integrasi WhatsApp: Webhook Meta Cloud API & Simulator Interaktif")

    # 3 Cards horizontal
    card_w3 = Inches(3.7)
    card_h3 = Inches(5.0)

    # Col 1: Webhook Architecture
    add_card(s6, Inches(0.8), Inches(1.8), card_w3, card_h3)
    tb_w1 = s6.shapes.add_textbox(Inches(1.0), Inches(2.0), card_w3 - Inches(0.4), card_h3 - Inches(0.4))
    tf_w1 = tb_w1.text_frame
    tf_w1.word_wrap = True
    p = tf_w1.paragraphs[0]
    p.text = "1. Webhook Meta Cloud API"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_ACCENT_BLUE

    w1_items = [
        "Verifikasi Token (GET): Endpoint /api/whatsapp/webhook memverifikasi hub.challenge dan hub.verify_token sesuai standar keamanan Meta.",
        "Inbound Receiver (POST): Menerima format resmi JSON Meta saat pengguna WhatsApp mengirimkan pesan ke nomor bisnis.",
        "Audit Logging DB: Seluruh pesan masuk dan balasan dicatat otomatis di tabel PostgreSQL whatsapp_messages lengkap dengan metadata intent dan waktu."
    ]
    for it in w1_items:
        p = tf_w1.add_paragraph()
        p.space_before = Pt(10)
        k, v = it.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "• " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(10.5)
        r_k.font.color.rgb = C_TEXT_DARK
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = C_TEXT_BODY

    # Col 2: Routing Engine
    add_card(s6, Inches(0.8) + card_w3 + gap, Inches(1.8), card_w3, card_h3)
    tb_w2 = s6.shapes.add_textbox(Inches(1.0) + card_w3 + gap, Inches(2.0), card_w3 - Inches(0.4), card_h3 - Inches(0.4))
    tf_w2 = tb_w2.text_frame
    tf_w2.word_wrap = True
    p = tf_w2.paragraphs[0]
    p.text = "2. Routing Engine Cerdas"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_BRAND_GREEN

    w2_items = [
        "Frontline Inquiries (P3): Pertanyaan stok barang, panduan size chart (XS-XL), info warna, dan resi pengiriman otomatis diarahkan ke Siti.",
        "Komplain Berat & Kerusakan (P1): Kata kunci seperti robek, cacat, reject, atau somasi otomatis dialihkan ke Hendra (CS Lead).",
        "Retur & Refund (P1): Pelanggan yang menuntut uang kembali ditangani secara empatik dan dipandu syarat video unboxing serta tag barcode utuh."
    ]
    for it in w2_items:
        p = tf_w2.add_paragraph()
        p.space_before = Pt(10)
        k, v = it.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "• " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(10.5)
        r_k.font.color.rgb = C_TEXT_DARK
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = C_TEXT_BODY

    # Col 3: Live Simulator
    add_card(s6, Inches(0.8) + (card_w3 + gap)*2, Inches(1.8), card_w3, card_h3)
    tb_w3 = s6.shapes.add_textbox(Inches(1.0) + (card_w3 + gap)*2, Inches(2.0), card_w3 - Inches(0.4), card_h3 - Inches(0.4))
    tf_w3 = tb_w3.text_frame
    tf_w3.word_wrap = True
    p = tf_w3.paragraphs[0]
    p.text = "3. Simulator Web Interaktif"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = RGBColor(147, 51, 234)

    w3_items = [
        "Tersedia Langsung di VPS: Dapat diakses mentor dan lead di http://139.190.107.151/wa-tester.html.",
        "Antarmuka WhatsApp Web: Menampilkan gelembung chat hijau/putih, centang biru, dan status online.",
        "Tombol Skenario Cepat: Disediakan tombol uji coba instan untuk menguji rute Siti vs eskalasi Hendra dalam satu klik.",
        "Badge Bot Real-time: Setiap pesan menampilkan badge nama agen yang menjawab, perannya, dan level prioritasnya."
    ]
    for it in w3_items:
        p = tf_w3.add_paragraph()
        p.space_before = Pt(10)
        k, v = it.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "• " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(10.5)
        r_k.font.color.rgb = C_TEXT_DARK
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = C_TEXT_BODY

    # ==========================================
    # SLIDE 7: Integrasi Tools Pihak Ketiga & Solusi Bug 503
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_bg(s7)
    add_header(s7, "Konektor Tools & Pemecahan Masalah (Troubleshooting)")

    # Top Card: Third-party Tools
    add_card(s7, Inches(0.8), Inches(1.8), layer_w, Inches(2.2))
    tb_t1 = s7.shapes.add_textbox(Inches(1.0), Inches(1.9), layer_w - Inches(0.4), Inches(2.0))
    tf_t1 = tb_t1.text_frame
    tf_t1.word_wrap = True
    p = tf_t1.paragraphs[0]
    p.text = "1. Konektor Aplikasi & Endpoint Terpadu (/api/tools/integrations)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_ACCENT_BLUE

    t_items = [
        "Google Drive & Gmail: Otentikasi OAuth 2.0 dengan enkripsi token simetris Fernet (CONNECTIONS_KEY) di database Neon Cloud.",
        "Notion Connector: Terintegrasi melalui Hermes Nous Portal (/api/connections/notion/status & /start) untuk membaca basis pengetahuan tim.",
        "54 Aplikasi Eksternal: Seluruh katalog aplikasi (Canva, Slack, Shopify, Jira, dll) kini aktif dan dapat dijelajahi di halaman /#/aplikasi."
    ]
    for it in t_items:
        p = tf_t1.add_paragraph()
        p.space_before = Pt(6)
        k, v = it.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "✔ " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(10.5)
        r_k.font.color.rgb = C_BRAND_GREEN
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = C_TEXT_BODY

    # Bottom Card: Troubleshooting Bug 503
    add_card(s7, Inches(0.8), Inches(4.2), layer_w, Inches(2.6))
    tb_t2 = s7.shapes.add_textbox(Inches(1.0), Inches(4.3), layer_w - Inches(0.4), Inches(2.4))
    tf_t2 = tb_t2.text_frame
    tf_t2.word_wrap = True
    p = tf_t2.paragraphs[0]
    p.text = "2. Analisis & Solusi Galat 503 ('Daftar aplikasi belum bisa dimuat')"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RGBColor(225, 29, 72)

    bug_items = [
        "Akar Masalah (Root Cause): Pada service pegawai-ai-bff, urutan PATH mendahulukan /home/ubuntu/.local/bin/hermes yang merupakan shell script pembungkus lama. Script tersebut memanggil python3 tanpa modul hermes_cli.cli, sehingga eksekusi CLI gagal menghasilkan daftar konektor (code 1).",
        "Solusi Permanen (Resolution): Membuat symlink resmi dari /usr/local/bin/hermes ke /home/ubuntu/.local/bin/hermes, sehingga environment service selalu menggunakan runtime Hermes v0.23+ yang valid.",
        "Hasil Validasi: Panggilan GET /api/apps/catalog langsung merespons HTTP 200 OK dengan 10 kategori dan 54 aplikasi termuat sempurna tanpa error."
    ]
    for it in bug_items:
        p = tf_t2.add_paragraph()
        p.space_before = Pt(6)
        k, v = it.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "• " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(10.5)
        r_k.font.color.rgb = C_TEXT_DARK
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = C_TEXT_BODY

    # ==========================================
    # SLIDE 8: Bukti Stabilitas, Pengujian & Metrik VPS
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_bg(s8)
    add_header(s8, "Metrik Performa & Bukti Validasi Pengujian (Proof of Stability)")

    # 4 Metric Cards
    m_w = Inches(2.7)
    m_h = Inches(1.8)
    m_top = Inches(1.8)
    m_gap = Inches(0.3)

    metrics = [
        ("257 Tests", "Pytest Suite 100% Passed", "Seluruh test case BFF & 10 unit test WhatsApp lulus tanpa galat.", C_BRAND_GREEN),
        ("5.2% RAM", "Konsumsi Memori Sangat Hemat", "Dari 4GB RAM tersedia, hanya terpakai ~210MB saat melayani request.", C_ACCENT_BLUE),
        ("0.36 Load", "CPU Load Rata-Rata Rendah", "4 vCPU Biznet Gio beroperasi optimal dan sangat responsif.", RGBColor(147, 51, 234)),
        ("0 Downtime", "Systemd Self-Healing", "Service otomatis pulih seketika jika terjadi reboot atau reload.", RGBColor(234, 88, 12))
    ]

    for i, (val, title, desc, color) in enumerate(metrics):
        l = Inches(0.8) + i * (m_w + m_gap)
        add_card(s8, l, m_top, m_w, m_h)
        tb_m = s8.shapes.add_textbox(l + Inches(0.15), m_top + Inches(0.1), m_w - Inches(0.3), m_h - Inches(0.2))
        tf_m = tb_m.text_frame
        tf_m.word_wrap = True
        p = tf_m.paragraphs[0]
        p.text = val
        p.font.name = "Arial"
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = color
        
        p2 = tf_m.add_paragraph()
        p2.text = title
        p2.font.bold = True
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = C_TEXT_DARK

        p3 = tf_m.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(9)
        p3.font.color.rgb = C_TEXT_MUTED

    # Bottom Summary Table
    add_card(s8, Inches(0.8), Inches(3.9), layer_w, Inches(2.9))
    tb_bt = s8.shapes.add_textbox(Inches(1.0), Inches(4.0), layer_w - Inches(0.4), Inches(2.7))
    tf_bt = tb_bt.text_frame
    tf_bt.word_wrap = True
    p = tf_bt.paragraphs[0]
    p.text = "Rangkuman Validasi Endpoint Langsung (Live Endpoint Evidence)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_TEXT_DARK

    rows_ev = [
        ("GET / (Nginx Frontend)", "HTTP 200 OK", "Aplikasi web Pegawai AI tampil utuh melayani dashboard, navigasi tim, chat, dan tools."),
        ("GET /bff/api/whatsapp/status", "HTTP 200 OK", "Status ready, bot primer Siti dan bot eskalasi Hendra terdaftar aktif."),
        ("GET /bff/api/whatsapp/webhook", "HTTP 200 OK", "Handshake Meta echo token challenge sukses merespons plaintext challenge."),
        ("POST /bff/api/whatsapp/simulate", "HTTP 200 OK", "Routing presisi: Pertanyaan umum ke Siti (P3), komplain robek ke Hendra (P1)."),
        ("GET /bff/api/apps/catalog", "HTTP 200 OK", "Katalog 54 tools eksternal sukses termuat sempurna."),
        ("Neon Cloud PostgreSQL Sync", "Connected", "Pool koneksi terenkripsi SSL aktif menampung log riwayat chat dan konfigurasi.")
    ]
    for ep, status, notes in rows_ev:
        p = tf_bt.add_paragraph()
        p.space_before = Pt(3)
        r_ep = p.add_run()
        r_ep.text = "• " + ep + " [" + status + "]: "
        r_ep.font.bold = True
        r_ep.font.size = Pt(10)
        r_ep.font.color.rgb = C_BRAND_GREEN if status == "HTTP 200 OK" or status == "Connected" else C_ACCENT_BLUE
        r_n = p.add_run()
        r_n.text = notes
        r_n.font.size = Pt(9.5)
        r_n.font.color.rgb = C_TEXT_BODY

    # ==========================================
    # SLIDE 9: Kesimpulan & Rencana Selanjutnya (Next Steps)
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    add_bg(s9)
    add_header(s9, "Kesimpulan & Rencana Kerja Selanjutnya (Next Steps)")

    add_card(s9, Inches(0.8), Inches(1.8), card_w2, card_h2)
    tb_c1 = s9.shapes.add_textbox(Inches(1.0), Inches(2.0), card_w2 - Inches(0.4), card_h2 - Inches(0.4))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    p = tf_c1.paragraphs[0]
    p.text = "Kesimpulan Pencapaian"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_BRAND_GREEN

    concls = [
        "Infrastruktur Cloud Siap: VPS Biznet Gio NEO Lite MS 4.4 terbukti tangguh, efisien, dan siap menjadi tumpuan utama sistem Pegawai AI.",
        "Multi-Agent Beroperasi Penuh: 5 Agen Marketing R&D dan 2 Agen Customer Service aktif berjalan secara serentak.",
        "Integrasi WhatsApp Terverifikasi: Webhook Meta Cloud API dan Web Simulator interaktif siap diuji langsung oleh stakeholder.",
        "Kualitas Kode Terjaga: Seluruh deliverable Sprint 4 Day 1 s.d. Day 4 telah diverifikasi lolos unit test dan tercatat lengkap di ClickUp."
    ]
    for c in concls:
        p = tf_c1.add_paragraph()
        p.space_before = Pt(12)
        k, v = c.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "✔ " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(11)
        r_k.font.color.rgb = C_TEXT_DARK
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10.5)
        r_v.font.color.rgb = C_TEXT_BODY

    add_card(s9, Inches(6.8), Inches(1.8), card_w2, card_h2)
    tb_c2 = s9.shapes.add_textbox(Inches(7.0), Inches(2.0), card_w2 - Inches(0.4), card_h2 - Inches(0.4))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    p = tf_c2.paragraphs[0]
    p.text = "Rencana Kerja Selanjutnya (Next Actions)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_ACCENT_BLUE

    plans = [
        "Aktivasi Nomor WhatsApp Asli: Memasukkan Phone Number ID dan Token Meta dari tim manajemen untuk menerima chat langsung dari pengguna WhatsApp nyata.",
        "Pemasangan Domain & HTTPS SSL: Memasang sertifikat SSL resmi (Let's Encrypt / Cloudflare) agar URL Webhook memenuhi standar ketat Meta WhatsApp.",
        "Penyelesaian Sprint 4 Day 5: Melakukan pengujian integrasi menyeluruh (End-to-End Testing) dan stabilisasi antarmuka frontend.",
        "Uji Coba Pengguna Terbatas (UAT): Mengundang tim internal Colorbox untuk berinteraksi langsung dengan bot di lingkungan VPS."
    ]
    for pl in plans:
        p = tf_c2.add_paragraph()
        p.space_before = Pt(12)
        k, v = pl.split(": ", 1)
        r_k = p.add_run()
        r_k.text = "➔ " + k + ": "
        r_k.font.bold = True
        r_k.font.size = Pt(11)
        r_k.font.color.rgb = C_BRAND
        r_v = p.add_run()
        r_v.text = v
        r_v.font.size = Pt(10.5)
        r_v.font.color.rgb = C_TEXT_BODY

    # Save presentation
    filename = "Pegawai_AI_VPS_Preparation_and_Deployment_Presentation.pptx"
    prs.save(filename)
    print(f"Presentation saved successfully as '{filename}'!")

if __name__ == "__main__":
    create_deck()
