import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

output_dir = r"hermes\colorbox\marketing\output\carousel_campus_rebel"
images_dir = r"hermes\colorbox\colorbox-knowledge\images"
os.makedirs(output_dir, exist_ok=True)

# Color Palette (Colorbox Aesthetic: Clean, Warm, Trendy)
BG_COLOR = (246, 244, 240)       # #F6F4F0 Warm Cream
CARD_BG = (255, 255, 255)        # Pure White
TEXT_DARK = (28, 28, 30)         # Deep Charcoal #1C1C1E
TEXT_MUTED = (110, 110, 115)     # Warm Muted Grey
ACCENT_CORAL = (235, 78, 98)     # Colorbox Coral #EB4E62
ACCENT_LIGHT = (254, 237, 240)   # Soft Pink tint
ACCENT_NAVY = (27, 43, 75)       # Sophisticated Navy
BORDER_COLOR = (226, 222, 214)   # Subtle Border
TAG_BG = (238, 234, 227)

# Fonts
font_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 64)
font_subtitle = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 34)
font_card_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 46)
font_body = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 30)
font_body_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 32)
font_small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
font_badge = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 28)
font_price = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 40)
font_price_small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 28)

def draw_header(draw, title_text, slide_number):
    # Top branding bar
    draw.rectangle([0, 0, 1080, 120], fill=(255, 255, 255))
    draw.line([0, 120, 1080, 120], fill=BORDER_COLOR, width=2)
    
    # Brand logo text
    draw.text((60, 42), "COLORBOX", fill=TEXT_DARK, font=font_body_bold)
    draw.text((230, 45), "|   CAMPUS LOOKBOOK", fill=TEXT_MUTED, font=font_body)
    
    # Slide pagination badge
    pill_w = 160
    pill_x = 1080 - 60 - pill_w
    draw.rounded_rectangle([pill_x, 35, pill_x + pill_w, 85], radius=25, fill=TAG_BG)
    draw.text((pill_x + 25, 45), f"SLIDE {slide_number}/5", fill=TEXT_DARK, font=font_badge)

def draw_footer(draw, slide_number, cta_text="GESER UNTUK SPILL LOOK  ➔"):
    # Bottom bar (Feed style - clean, full bleed)
    draw.line([60, 1240, 1020, 1240], fill=BORDER_COLOR, width=2)
    
    # Progress dots
    start_x = 60
    for i in range(1, 6):
        col = ACCENT_CORAL if i == slide_number else BORDER_COLOR
        rad = 8 if i == slide_number else 6
        draw.ellipse([start_x, 1275 - rad, start_x + rad*2, 1275 + rad], fill=col)
        start_x += 26
        
    # Swipe CTA
    bbox = draw.textbbox((0, 0), cta_text, font=font_badge)
    text_w = bbox[2] - bbox[0]
    draw.text((1080 - 60 - text_w, 1260), cta_text, fill=ACCENT_CORAL, font=font_badge)

def draw_product_badge(draw, x, y, name, price, strike_price=None):
    w, h = 420, 110
    draw.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    # Tag label
    draw.text((x + 20, y + 16), name[:28], fill=TEXT_DARK, font=font_small)
    # Price
    draw.text((x + 20, y + 52), price, fill=ACCENT_CORAL, font=font_body_bold)
    if strike_price:
        bbox = draw.textbbox((0, 0), price, font=font_body_bold)
        pw = bbox[2] - bbox[0]
        draw.text((x + 20 + pw + 15, y + 56), strike_price, fill=TEXT_MUTED, font=font_small)
        # strike line
        s_bbox = draw.textbbox((0, 0), strike_price, font=font_small)
        sw = s_bbox[2] - s_bbox[0]
        draw.line([x + 35 + pw, y + 70, x + 35 + pw + sw, y + 70], fill=TEXT_MUTED, width=2)

print("Starting generation of 5 Final Rendered Carousel Slides...")

# ==============================================================================
# SLIDE 1: COVER HERO
# ==============================================================================
s1 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
d1 = ImageDraw.Draw(s1)
draw_header(d1, "CAMPUS LOOKBOOK", 1)

# Category Badge
d1.rounded_rectangle([60, 160, 420, 215], radius=28, fill=ACCENT_LIGHT)
d1.text((85, 172), "🎓 CAMPUS OOTD FORMULA", fill=ACCENT_CORAL, font=font_badge)

# Main Hook Headline
d1.text((60, 240), "Kelas Jam 8 Pagi,\nTetap Slay Tanpa Pusing.", fill=TEXT_DARK, font=font_title, spacing=14)
d1.text((60, 400), "Formula 3-item praktis buat kamu yang anti-ribet tapi mau tetap on-point.", fill=TEXT_MUTED, font=font_subtitle)

# Main Hero Visual Card (Composite of real product photos)
hero_box = [60, 480, 1020, 1130]
d1.rounded_rectangle(hero_box, radius=24, fill=CARD_BG, outline=BORDER_COLOR, width=2)

# Insert Hero Product Images side-by-side
img_shirt_path = os.path.join(images_dir, "cbx-01-contrast-stitch-chambray-shirt.jpg")
img_denim_path = os.path.join(images_dir, "cbx-02-high-waist-barrel-denim-black.jpg")
img_tote_path = os.path.join(images_dir, "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg")

if os.path.exists(img_denim_path) and os.path.exists(img_shirt_path):
    # Left: Shirt
    im_s = Image.open(img_shirt_path).convert("RGB")
    im_s = im_s.resize((440, 600), Image.Resampling.LANCZOS)
    s1.paste(im_s, (80, 505))
    
    # Right: Denim
    im_d = Image.open(img_denim_path).convert("RGB")
    im_d = im_d.resize((440, 600), Image.Resampling.LANCZOS)
    s1.paste(im_d, (560, 505))

# Floating Total Price Chip
d1.rounded_rectangle([320, 1110, 760, 1180], radius=35, fill=TEXT_DARK)
d1.text((350, 1125), "✨ TOTAL OUTFIT: Rp 629.700", fill=(255, 255, 255), font=font_price_small)

draw_footer(d1, 1, "GESER UNTUK SPILL LOOK  ➔")
s1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
s1.save(s1_path, "PNG", quality=95)
print(f"[OK] Slide 1 generated -> {s1_path}")

# ==============================================================================
# SLIDE 2: HERO TOP BREAKDOWN
# ==============================================================================
s2 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
d2 = ImageDraw.Draw(s2)
draw_header(d2, "ITEM BREAKDOWN", 2)

# Step Badge & Name
d2.rounded_rectangle([60, 160, 380, 215], radius=28, fill=TAG_BG)
d2.text((85, 172), "STEP 1: THE COMFY BASE", fill=TEXT_DARK, font=font_badge)

d2.text((60, 235), "Contrast Stitch Chambray", fill=TEXT_DARK, font=font_card_title)
d2.text((60, 290), "Atasan santai bernuansa denim dengan aksen jahitan kontras putih.", fill=TEXT_MUTED, font=font_body)

# Product Card with Real Photo
photo_box = [60, 360, 620, 1140]
d2.rounded_rectangle(photo_box, radius=24, fill=CARD_BG, outline=BORDER_COLOR, width=2)
if os.path.exists(img_shirt_path):
    im_s = Image.open(img_shirt_path).convert("RGB")
    im_s = im_s.resize((520, 740), Image.Resampling.LANCZOS)
    s2.paste(im_s, (80, 380))

# Right Info Panel
info_x = 660
# Price Card
d2.rounded_rectangle([info_x, 360, 1020, 500], radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
d2.text((info_x + 25, 385), "HARGA RESMI", fill=TEXT_MUTED, font=font_small)
d2.text((info_x + 25, 420), "Rp 140.900", fill=ACCENT_CORAL, font=font_price)
d2.text((info_x + 255, 430), "Rp 299.900", fill=TEXT_MUTED, font=font_price_small)
d2.line([info_x + 255, 445, info_x + 395, 445], fill=TEXT_MUTED, width=2)

# Spec Details Card
d2.rounded_rectangle([info_x, 520, 1020, 840], radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
d2.text((info_x + 25, 545), "SPESIFIKASI & FIT", fill=TEXT_DARK, font=font_body_bold)
d2.text((info_x + 25, 595), "• Warna: DARK BLUE\n• Pilihan Ukuran: S, M, L, XL\n• Siluet: Boxy Relaxed Fit\n• Cutting: Lengan pendek santai\n• Fit: True to size / Layering", fill=TEXT_DARK, font=font_small, spacing=10)

# Why We Love It Card
d2.rounded_rectangle([info_x, 860, 1020, 1140], radius=20, fill=ACCENT_LIGHT, outline=ACCENT_CORAL, width=2)
d2.text((info_x + 25, 885), "💡 KENAPA KITA SUKA:", fill=ACCENT_CORAL, font=font_body_bold)
d2.text((info_x + 25, 935), "Bahan adem untuk kelas ber-AC.\nBisa dipakai kancing penuh\natau dijadikan outer santai di atas\ntank-top/crop tee putih!", fill=TEXT_DARK, font=font_small, spacing=8)

draw_footer(d2, 2, "LANJUT KE STEP 2  ➔")
s2_path = os.path.join(output_dir, "slide_2_hero_top.png")
s2.save(s2_path, "PNG", quality=95)
print(f"[OK] Slide 2 generated -> {s2_path}")

# ==============================================================================
# SLIDE 3: BOTTOM PAIRING & SILHOUETTE
# ==============================================================================
s3 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
d3 = ImageDraw.Draw(s3)
draw_header(d3, "ITEM BREAKDOWN", 3)

# Step Badge & Name
d3.rounded_rectangle([60, 160, 420, 215], radius=28, fill=TAG_BG)
d3.text((85, 172), "STEP 2: BALANCED SILHOUETTE", fill=TEXT_DARK, font=font_badge)

d3.text((60, 235), "High Waist Barrel Denim", fill=TEXT_DARK, font=font_card_title)
d3.text((60, 290), "Potongan melengkung khas kekinian yang bikin postur terlihat jenjang.", fill=TEXT_MUTED, font=font_body)

# Product Card with Real Photo (Left)
photo_box = [60, 360, 620, 1140]
d3.rounded_rectangle(photo_box, radius=24, fill=CARD_BG, outline=BORDER_COLOR, width=2)
if os.path.exists(img_denim_path):
    im_d = Image.open(img_denim_path).convert("RGB")
    im_d = im_d.resize((520, 740), Image.Resampling.LANCZOS)
    s3.paste(im_d, (80, 380))

# Right Info Panel
d3.rounded_rectangle([info_x, 360, 1020, 500], radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
d3.text((info_x + 25, 385), "HARGA RESMI", fill=TEXT_MUTED, font=font_small)
d3.text((info_x + 25, 420), "Rp 329.900", fill=ACCENT_CORAL, font=font_price)
d3.text((info_x + 270, 428), "BESTSELLER", fill=TEXT_MUTED, font=font_badge)

d3.rounded_rectangle([info_x, 520, 1020, 840], radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
d3.text((info_x + 25, 545), "SPESIFIKASI & UKURAN", fill=TEXT_DARK, font=font_body_bold)
d3.text((info_x + 25, 595), "• Warna: BLACK (Washed)\n• Pilihan Ukuran: 26 - 30\n• Size 27: LP 65-68 cm (BB 48-52 kg)\n• Size 28: LP 69-72 cm (BB 53-57 kg)\n• Fit: High Rise & Barrel Cut", fill=TEXT_DARK, font=font_small, spacing=10)

d3.rounded_rectangle([info_x, 860, 1020, 1140], radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
d3.text((info_x + 25, 885), "👖 STYLING SECRET:", fill=TEXT_DARK, font=font_body_bold)
d3.text((info_x + 25, 935), "Potongan barrel leg melengkung\nmemberikan siluet modern tanpa\nterasa ketat di paha saat duduk\nseharian di ruang seminar!", fill=TEXT_MUTED, font=font_small, spacing=8)

draw_footer(d3, 3, "LANJUT KE AKSESORIS  ➔")
s3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
s3.save(s3_path, "PNG", quality=95)
print(f"[OK] Slide 3 generated -> {s3_path}")

# ==============================================================================
# SLIDE 4: FLAT-LAY & ACCESSORIES
# ==============================================================================
s4 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
d4 = ImageDraw.Draw(s4)
draw_header(d4, "CAMPUS ESSENTIALS", 4)

d4.rounded_rectangle([60, 160, 420, 215], radius=28, fill=TAG_BG)
d4.text((85, 172), "STEP 3: ELEVATE WITH ACCENTS", fill=TEXT_DARK, font=font_badge)

d4.text((60, 235), "The Final Touch: Liunic Tote Bag", fill=TEXT_DARK, font=font_card_title)
d4.text((60, 290), "Bawa semua kebutuhan kuliahmu dengan tote bag kolaborasi seni eksklusif.", fill=TEXT_MUTED, font=font_body)

# Left Card: Tote Bag Photo
tote_box = [60, 360, 520, 940]
d4.rounded_rectangle(tote_box, radius=24, fill=CARD_BG, outline=BORDER_COLOR, width=2)
if os.path.exists(img_tote_path):
    im_t = Image.open(img_tote_path).convert("RGB")
    im_t = im_t.resize((420, 540), Image.Resampling.LANCZOS)
    s4.paste(im_t, (80, 380))

# Right Card: Skort / Alternate Option
alt_box = [560, 360, 1020, 940]
d4.rounded_rectangle(alt_box, radius=24, fill=CARD_BG, outline=BORDER_COLOR, width=2)
img_skort_path = os.path.join(images_dir, "cbx-06-regular-fit-tailored-mini-skort-grey.jpg")
if os.path.exists(img_skort_path):
    im_sk = Image.open(img_skort_path).convert("RGB")
    im_sk = im_sk.resize((420, 540), Image.Resampling.LANCZOS)
    s4.paste(im_sk, (580, 380))

# Below Cards: Feature Details
d4.rounded_rectangle([60, 970, 520, 1180], radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
d4.text((85, 990), "Colorbox x Liunic Tote Bag", fill=TEXT_DARK, font=font_body_bold)
d4.text((85, 1030), "Rp 199.900  •  Warna: ECRU", fill=ACCENT_CORAL, font=font_price_small)
d4.text((85, 1075), "Bahan kanvas kokoh, muat laptop 14\",\nbinder kuliah, & tumbler minum.", fill=TEXT_MUTED, font=font_small, spacing=6)

d4.rounded_rectangle([560, 970, 1020, 1180], radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
d4.text((585, 990), "Opsi Bawahan Alternatif", fill=TEXT_DARK, font=font_body_bold)
d4.text((585, 1030), "Tailored Mini Skort - Rp 139.930", fill=ACCENT_CORAL, font=font_price_small)
d4.text((585, 1075), "Pilihan manis buat hari presentasi,\nada celana furing aman di dalam!", fill=TEXT_MUTED, font=font_small, spacing=6)

draw_footer(d4, 4, "RANGKUMAN TOTAL LOOK  ➔")
s4_path = os.path.join(output_dir, "slide_4_accessories_flatlay.png")
s4.save(s4_path, "PNG", quality=95)
print(f"[OK] Slide 4 generated -> {s4_path}")

# ==============================================================================
# SLIDE 5: OUTRO & CALL TO ACTION
# ==============================================================================
s5 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
d5 = ImageDraw.Draw(s5)
draw_header(d5, "LOOK SUMMARY", 5)

# Outro Banner
d5.text((60, 160), "Ready to Rock Your\nCampus Day, Babes?", fill=TEXT_DARK, font=font_title, spacing=14)
d5.text((60, 320), "Simpan postingan ini biar besok pagi nggak bingung lagi pilih baju!", fill=TEXT_MUTED, font=font_subtitle)

# Receipt Style Summary Card
rec_box = [60, 400, 1020, 880]
d5.rounded_rectangle(rec_box, radius=24, fill=CARD_BG, outline=BORDER_COLOR, width=2)

d5.text((100, 435), "REKAP FORMULA OUTFIT RESMI COLORBOX", fill=TEXT_MUTED, font=font_badge)
d5.line([100, 480, 980, 480], fill=BORDER_COLOR, width=2)

# Row 1
d5.text((100, 510), "1. Contrast Stitch Chambray Shirt (Dark Blue)", fill=TEXT_DARK, font=font_body_bold)
d5.text((800, 510), "Rp 140.900", fill=TEXT_DARK, font=font_body_bold)

# Row 2
d5.text((100, 580), "2. High Waist Barrel Denim Pants (Black)", fill=TEXT_DARK, font=font_body_bold)
d5.text((800, 580), "Rp 329.900", fill=TEXT_DARK, font=font_body_bold)

# Row 3
d5.text((100, 650), "3. Colorbox x Liunic Canvas Tote Bag (Ecru)", fill=TEXT_DARK, font=font_body_bold)
d5.text((800, 650), "Rp 199.900", fill=TEXT_DARK, font=font_body_bold)

d5.line([100, 720, 980, 720], fill=BORDER_COLOR, width=2)

# Total
d5.text((100, 755), "TOTAL LENGKAP 3 ITEMS:", fill=TEXT_DARK, font=font_card_title)
d5.text((720, 755), "Rp 670.700", fill=ACCENT_CORAL, font=font_card_title)
d5.text((100, 815), "*Hemat hingga Rp 159.000 berkat potongan diskon kemeja chambray!", fill=TEXT_MUTED, font=font_small)

# Call to Action Card
cta_box = [60, 920, 1020, 1180]
d5.rounded_rectangle(cta_box, radius=24, fill=TEXT_DARK)

d5.text((100, 955), "📌 CARA BELANJA / AMBIL INSPIRASI:", fill=(255, 255, 255), font=font_body_bold)
d5.text((100, 1010), "1. Simpan (Bookmark) postingan ini dengan tap ikon di bawah\n2. Kunjungi Colorbox Store terdekat di kotamu\n3. Belanja online 24/7 di colorbox.co.id (Link di Bio!)", fill=(210, 210, 215), font=font_body, spacing=10)

draw_footer(d5, 5, "TAP LINK DI BIO  •  COLORBOX.CO.ID")
s5_path = os.path.join(output_dir, "slide_5_outro_cta.png")
s5.save(s5_path, "PNG", quality=95)
print(f"[OK] Slide 5 generated -> {s5_path}")

print("All 5 Final Carousel Slides generated successfully!")
