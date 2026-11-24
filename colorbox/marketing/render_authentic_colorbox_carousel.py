import os
import shutil
import base64
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

print("=== RENDERING 100% AUTHENTIC COLORBOX GRAPHIC TEE CAROUSEL ===")

ROOT_DIR = Path(r"d:\Users\IVANAGITA\aitoptrends\hermes")
KB_IMAGES = ROOT_DIR / "backend" / "colorbox" / "colorbox-knowledge" / "images"

OUTPUT_DIRS = [
    Path(r"d:\Users\IVANAGITA\aitoptrends\karyawan ai\output_graphic_tee"),
    ROOT_DIR / "colorbox" / "marketing" / "output" / "carousel_graphic_tee",
    ROOT_DIR / "colorbox" / "marketing" / "output" / "carousel_latest",
    ROOT_DIR / "backend" / "colorbox" / "marketing" / "output" / "carousel_latest",
    ROOT_DIR / "frontend" / "frontend" / "public" / "output" / "carousel_latest"
]

for d in OUTPUT_DIRS:
    d.mkdir(parents=True, exist_ok=True)

# Aesthetic Palette (Colorbox Pastel Peach & Clean Ivory)
BG_CANVAS = (253, 248, 245)
CARD_BG = (255, 255, 255)
TEXT_DARK = (45, 35, 40)
TEXT_MUTED = (140, 125, 130)
ACCENT_PINK = (244, 114, 150)
ACCENT_LILAC = (186, 160, 215)
BORDER_PASTEL = (240, 230, 232)

font_brand = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 44)
font_slide_tag = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
font_caption = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 24)

def create_base_canvas(w=1080, h=1350):
    return Image.new("RGB", (w, h), BG_CANVAS)

def add_header_footer(canvas, slide_num, total=5, tag="GIRLY CHIC"):
    draw = ImageDraw.Draw(canvas)
    draw.text((70, 48), "COLORBOX", fill=TEXT_DARK, font=font_brand)
    draw.text((360, 58), f"|  {tag}", fill=TEXT_MUTED, font=font_slide_tag)
    
    counter_text = f"0{slide_num} / 0{total}"
    draw.rounded_rectangle([860, 48, 1010, 92], radius=22, fill=(255, 255, 255), outline=BORDER_PASTEL, width=2)
    draw.text((885, 54), counter_text, fill=ACCENT_PINK, font=font_slide_tag)
    
    draw.line([70, 1265, 1010, 1265], fill=BORDER_PASTEL, width=1)
    draw.text((70, 1285), "@colorbox_id", fill=TEXT_MUTED, font=font_sub)
    draw.text((850, 1285), "#NeverJustOneThing", fill=ACCENT_PINK, font=font_sub)

# Authentic asset paths
tee_detail = KB_IMAGES / "cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg"
tee_front = KB_IMAGES / "cbx-21a-oversize-graphic-tee-lt-pink-front.jpg"
tee_full = KB_IMAGES / "cbx-21c-oversize-graphic-tee-lt-pink-full.jpg"
jacket_front = KB_IMAGES / "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg"
jacket_detail = KB_IMAGES / "cbx-12c-double-breasted-crop-jacket-lt-grey-detail.jpg"
denim_img = KB_IMAGES / "cbx-02-high-waist-barrel-denim-black.jpg"
tote_img = KB_IMAGES / "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg"

# =========================================================================
# SLIDE 1: STATEMENT PIECE (Authentic Graphic Tee Detail, No Model)
# =========================================================================
print("Rendering Slide 1: Real Graphic Artwork Detail (Zero People)...")
s1 = create_base_canvas()
d1 = ImageDraw.Draw(s1)
d1.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)

if tee_detail.exists():
    im1 = Image.open(tee_detail).convert("RGB")
    # Crop to focus on the graphic artwork & pink fabric
    w, h = im1.size
    # Focus on the Miami Beach artwork
    im1_crop = im1.crop((0, int(h * 0.12), w, int(h * 0.95)))
    im1_fit = im1_crop.resize((940, 940), Image.Resampling.LANCZOS)
    s1.paste(im1_fit, (70, 145))

d1.text((100, 1115), "SUNSET CLUB GRAPHIC TEE", fill=TEXT_DARK, font=font_caption)
d1.text((100, 1165), "Oversized cotton tee with vintage Miami Beach sunset print", fill=TEXT_MUTED, font=font_sub)
d1.rounded_rectangle([790, 1120, 975, 1175], radius=20, fill=(254, 240, 245))
d1.text((820, 1133), "Rp 99.900", fill=ACCENT_PINK, font=font_slide_tag)
add_header_footer(s1, 1, 5, "THE STATEMENT TEE")

# =========================================================================
# SLIDE 2: MIX & MATCH WITH CROP JACKET (Garment Only Flatlay)
# =========================================================================
print("Rendering Slide 2: Real Graphic Tee + Crop Jacket Pairing...")
s2 = create_base_canvas()
d2 = ImageDraw.Draw(s2)
d2.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)

if tee_detail.exists() and jacket_detail.exists():
    # Left card: Tee Artwork
    im_tee = Image.open(tee_detail).convert("RGB").crop((0, int(h * 0.15), w, int(h * 0.85))).resize((450, 940), Image.Resampling.LANCZOS)
    # Right card: Jacket Structure
    im_jkt = Image.open(jacket_detail).convert("RGB").resize((450, 940), Image.Resampling.LANCZOS)
    
    s2.paste(im_tee, (75, 145))
    s2.paste(im_jkt, (555, 145))
    
    # Washi tape and sticky labels
    d2.rectangle([160, 135, 300, 155], fill=(255, 215, 230))
    d2.rectangle([640, 135, 780, 155], fill=(230, 225, 245))

d2.text((100, 1115), "STYLE PAIRING: TEE + CROP JACKET", fill=TEXT_DARK, font=font_caption)
d2.text((100, 1165), "Vintage sunset graphic meets tailored light grey corduroy texture", fill=TEXT_MUTED, font=font_sub)
d2.rounded_rectangle([800, 1120, 975, 1175], radius=20, fill=(245, 240, 255))
d2.text((825, 1133), "PERFECT DUO", fill=ACCENT_LILAC, font=font_slide_tag)
add_header_footer(s2, 2, 5, "STYLING FORMULA")

# =========================================================================
# SLIDE 3: COMPLETE OUTFIT GRID (Zero People)
# =========================================================================
print("Rendering Slide 3: Full Head-to-Toe Outfit Grid...")
s3 = create_base_canvas()
d3 = ImageDraw.Draw(s3)
d3.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)

# Multi-piece flatlay composition
if tee_detail.exists() and jacket_detail.exists() and denim_img.exists() and tote_img.exists():
    im_t = Image.open(tee_detail).convert("RGB").resize((440, 450), Image.Resampling.LANCZOS)
    im_j = Image.open(jacket_detail).convert("RGB").resize((440, 450), Image.Resampling.LANCZOS)
    im_d = Image.open(denim_img).convert("RGB").resize((440, 450), Image.Resampling.LANCZOS)
    im_b = Image.open(tote_img).convert("RGB").resize((440, 450), Image.Resampling.LANCZOS)
    
    s3.paste(im_t, (85, 160))
    s3.paste(im_j, (555, 160))
    s3.paste(im_d, (85, 635))
    s3.paste(im_b, (555, 635))
    
    # Sub labels
    d3.text((100, 170), "1. GRAPHIC TEE", fill=(255, 255, 255), font=font_slide_tag)
    d3.text((570, 170), "2. CROP JACKET", fill=(255, 255, 255), font=font_slide_tag)
    d3.text((100, 645), "3. BARREL DENIM", fill=(255, 255, 255), font=font_slide_tag)
    d3.text((570, 645), "4. LIUNIC TOTE", fill=(255, 255, 255), font=font_slide_tag)

d3.text((100, 1115), "HEAD-TO-TOE OOTD FORMULA", fill=TEXT_DARK, font=font_caption)
d3.text((100, 1165), "Tee + Cropped Jacket + Barrel Denim + Doodle Tote", fill=TEXT_MUTED, font=font_sub)
d3.rounded_rectangle([790, 1120, 975, 1175], radius=20, fill=(254, 240, 245))
d3.text((815, 1133), "FULL LOOK", fill=ACCENT_PINK, font=font_slide_tag)
add_header_footer(s3, 3, 5, "OUTFIT GRID")

# =========================================================================
# SLIDE 4: ON-MODEL REVEAL (Female Model Fit Check)
# =========================================================================
print("Rendering Slide 4: Real Colorbox Female Model Reveal...")
s4 = create_base_canvas()
d4 = ImageDraw.Draw(s4)
d4.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)

if tee_front.exists() and jacket_front.exists():
    im_m1 = Image.open(tee_front).convert("RGB").resize((450, 940), Image.Resampling.LANCZOS)
    im_m2 = Image.open(jacket_front).convert("RGB").resize((450, 940), Image.Resampling.LANCZOS)
    
    s4.paste(im_m1, (75, 145))
    s4.paste(im_m2, (555, 145))
    
    d4.rectangle([160, 135, 300, 155], fill=(255, 215, 230))
    d4.rectangle([640, 135, 780, 155], fill=(230, 225, 245))

d4.text((100, 1115), "THE FIT CHECK (ON MODEL)", fill=TEXT_DARK, font=font_caption)
d4.text((100, 1165), "Real on-model lookbook: Tee OOTD & Layered Cropped Jacket Fit", fill=TEXT_MUTED, font=font_sub)
d4.rounded_rectangle([800, 1120, 975, 1175], radius=20, fill=(254, 240, 245))
d4.text((830, 1133), "10/10 FIT", fill=ACCENT_PINK, font=font_slide_tag)
add_header_footer(s4, 4, 5, "ON-MODEL TRY-ON")

# =========================================================================
# SLIDE 5: LOOKBOOK FINALE & COMMUNITY POLL
# =========================================================================
print("Rendering Slide 5: Lookbook Finale & Community Poll...")
s5 = create_base_canvas()
d5 = ImageDraw.Draw(s5)
d5.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)

if tee_detail.exists() and jacket_front.exists():
    im_thumb1 = Image.open(tee_detail).convert("RGB").crop((0, int(h * 0.12), w, int(h * 0.95))).resize((420, 520), Image.Resampling.LANCZOS)
    im_thumb2 = Image.open(jacket_front).convert("RGB").resize((420, 520), Image.Resampling.LANCZOS)
    
    s5.paste(im_thumb1, (100, 200))
    s5.paste(im_thumb2, (560, 200))
    
    d5.rounded_rectangle([100, 735, 520, 785], radius=16, fill=(254, 240, 245))
    d5.text((130, 747), "TEE: Rp 99.900", fill=ACCENT_PINK, font=font_slide_tag)
    
    d5.rounded_rectangle([560, 735, 980, 785], radius=16, fill=(245, 240, 255))
    d5.text((590, 747), "JACKET: Rp 329.900", fill=ACCENT_LILAC, font=font_slide_tag)

font_poll = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 46)
d5.text((100, 840), "Which piece is your fave?", fill=TEXT_DARK, font=font_poll)
d5.text((100, 915), "Drop a comment below & tag your bestie to match fits!", fill=TEXT_MUTED, font=font_sub)

d5.rounded_rectangle([100, 990, 480, 1070], radius=24, fill=(253, 240, 245), outline=ACCENT_PINK, width=2)
d5.text((140, 1015), "TEAM GRAPHIC TEE", fill=ACCENT_PINK, font=font_caption)

d5.rounded_rectangle([540, 990, 980, 1070], radius=24, fill=(245, 240, 255), outline=ACCENT_LILAC, width=2)
d5.text((570, 1015), "TEAM CROP JACKET", fill=ACCENT_LILAC, font=font_caption)

d5.text((100, 1140), "Available at colorbox.co.id & all Colorbox offline stores", fill=TEXT_MUTED, font=font_sub)
add_header_footer(s5, 5, 5, "COMMUNITY POLL")

slides_map = {
    "slide_1_cover_hero.png": s1,
    "slide_2_hero_top.png": s2,
    "slide_3_bottom_pairing.png": s3,
    "slide_4_accessories_flatlay.png": s4,
    "slide_4_accessories_layering.png": s4,
    "slide_5_outro_cta.png": s5
}

for name, im in slides_map.items():
    for d in OUTPUT_DIRS:
        im.save(str(d / name), format="PNG", quality=95)
    print(f"Saved {name}")

print("=== ALL 5 AUTHENTIC SLIDES GENERATED SUCCESSFULLY ===")
