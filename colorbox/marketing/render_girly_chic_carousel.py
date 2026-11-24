import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

print("=== BUILDING COLORBOX COLORFUL GRAPHIC TEE CAROUSEL (GIRLY & CHIC) ===")

ROOT_DIR = Path(r"d:\Users\IVANAGITA\aitoptrends\hermes")
BRAIN_DIR = Path(r"C:\Users\IVANAGITA\.gemini\antigravity\brain\289c4273-5463-4a74-9663-80a73fc092a8")
KB_IMAGES = ROOT_DIR / "backend" / "colorbox" / "colorbox-knowledge" / "images"

OUTPUT_DIRS = [
    Path(r"d:\Users\IVANAGITA\aitoptrends\karyawan ai\output_graphic_tee"),
    ROOT_DIR / "colorbox" / "marketing" / "output" / "carousel_graphic_tee",
    ROOT_DIR / "colorbox" / "marketing" / "output" / "carousel_latest",
    ROOT_DIR / "backend" / "colorbox" / "marketing" / "output" / "carousel_latest",
    ROOT_DIR / "frontend" / "frontend" / "public" / "output" / "carousel_latest",
    BRAIN_DIR / "output_graphic_tee"
]

for d in OUTPUT_DIRS:
    d.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# COLOR PALETTE (Colorbox Girly Chic: Pastel Peach, Soft Cream, Warm Rose)
# -------------------------------------------------------------------------
BG_CREAM = (253, 248, 245)      # Warm Pastel Peach/Cream
CARD_BG = (255, 255, 255)       # Pure White
TEXT_DARK = (45, 35, 40)        # Soft Espresso Charcoal
TEXT_MUTED = (140, 125, 130)    # Soft Rose Muted
ACCENT_PINK = (244, 114, 150)   # Cute Girly Pink
ACCENT_LILAC = (186, 160, 215)  # Aesthetic Lilac
BORDER_PASTEL = (240, 230, 232) # Soft Border

# Typography
try:
    font_brand = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 44)
    font_slide_tag = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
    font_caption = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
    font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 24)
except Exception:
    font_brand = ImageFont.load_default()
    font_slide_tag = ImageFont.load_default()
    font_caption = ImageFont.load_default()
    font_sub = ImageFont.load_default()

def create_base_canvas(w=1080, h=1350):
    return Image.new("RGB", (w, h), BG_CREAM)

def add_header_footer(canvas, slide_num, total=5, tag="GIRLY CHIC"):
    draw = ImageDraw.Draw(canvas)
    # Header minimal
    draw.text((70, 48), "COLORBOX", fill=TEXT_DARK, font=font_brand)
    draw.text((360, 58), f"|  {tag}", fill=TEXT_MUTED, font=font_slide_tag)
    
    # Pill slide counter
    counter_text = f"0{slide_num} / 0{total}"
    draw.rounded_rectangle([860, 48, 1010, 92], radius=22, fill=(255, 255, 255), outline=BORDER_PASTEL, width=2)
    draw.text((885, 54), counter_text, fill=ACCENT_PINK, font=font_slide_tag)
    
    # Footer minimal watermark
    draw.line([70, 1265, 1010, 1265], fill=BORDER_PASTEL, width=1)
    draw.text((70, 1285), "@colorbox_id", fill=TEXT_MUTED, font=font_sub)
    draw.text((850, 1285), "#NeverJustOneThing", fill=ACCENT_PINK, font=font_sub)

# =========================================================================
# SLIDE 1: HERO PINK GRAPHIC TEE (Garment Flatlay, Zero People)
# =========================================================================
print("Rendering Slide 1: Pink Graphic Tee Hero Piece...")
s1 = create_base_canvas()
ai_tee_path = BRAIN_DIR / "slide_1_hero_pink_tee_1795499426687.jpg"
if ai_tee_path.exists():
    im1 = Image.open(ai_tee_path).convert("RGB")
    # Resize to fit elegantly with generous framing
    im1_fit = im1.resize((940, 940), Image.Resampling.LANCZOS)
    
    # Decorative polaroid / scrapbook card
    card_box = [65, 130, 1015, 1220]
    d1 = ImageDraw.Draw(s1)
    d1.rounded_rectangle(card_box, radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
    
    # Paste AI image centered
    s1.paste(im1_fit, (70, 145))
    
    # Minimal chic caption banner at bottom of card
    d1.text((100, 1115), "🌸 PINK OBSESSION TEE", fill=TEXT_DARK, font=font_caption)
    d1.text((100, 1165), "Oversized fit with soft cherry blossom artwork", fill=TEXT_MUTED, font=font_sub)
    d1.rounded_rectangle([790, 1120, 975, 1175], radius=20, fill=(254, 240, 245))
    d1.text((815, 1133), "MUST-HAVE", fill=ACCENT_PINK, font=font_slide_tag)

add_header_footer(s1, 1, 5, "THE STATEMENT TEE")

# =========================================================================
# SLIDE 2: MIX & MATCH WITH CROPPED JACKET (Garment Flatlay, Zero People)
# =========================================================================
print("Rendering Slide 2: Mix & Match Styling with Jacket...")
s2 = create_base_canvas()
ai_jacket_path = BRAIN_DIR / "slide_2_mix_match_jacket_1795499443707.jpg"
if ai_jacket_path.exists():
    im2 = Image.open(ai_jacket_path).convert("RGB")
    im2_fit = im2.resize((940, 940), Image.Resampling.LANCZOS)
    
    card_box = [65, 130, 1015, 1220]
    d2 = ImageDraw.Draw(s2)
    d2.rounded_rectangle(card_box, radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
    
    s2.paste(im2_fit, (70, 145))
    
    d2.text((100, 1115), "✨ STYLE PAIRING: TEE + CROP JACKET", fill=TEXT_DARK, font=font_caption)
    d2.text((100, 1165), "Soft pink graphic meets tailored grey structure", fill=TEXT_MUTED, font=font_sub)
    d2.rounded_rectangle([800, 1120, 975, 1175], radius=20, fill=(245, 240, 255))
    d2.text((825, 1133), "PERFECT DUO", fill=ACCENT_LILAC, font=font_slide_tag)

add_header_footer(s2, 2, 5, "STYLING FORMULA")

# =========================================================================
# SLIDE 3: COMPLETE OUTFIT GRID (Full Flatlay, Zero People)
# =========================================================================
print("Rendering Slide 3: Full Head-to-Toe Outfit Grid...")
s3 = create_base_canvas()
ai_grid_path = BRAIN_DIR / "slide_3_full_outfit_grid_1795499442332.jpg"
if ai_grid_path.exists():
    im3 = Image.open(ai_grid_path).convert("RGB")
    # im3 is 896x1200, let's fit it inside 940x1000
    im3_fit = im3.resize((860, 960), Image.Resampling.LANCZOS)
    
    card_box = [65, 130, 1015, 1220]
    d3 = ImageDraw.Draw(s3)
    d3.rounded_rectangle(card_box, radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
    
    px = (1080 - 860) // 2
    s3.paste(im3_fit, (px, 145))
    
    d3.text((100, 1125), "✦ HEAD-TO-TOE OOTD GRID", fill=TEXT_DARK, font=font_caption)
    d3.text((100, 1170), "Tee + Cropped Jacket + Barrel Denim + Doodle Tote", fill=TEXT_MUTED, font=font_sub)
    d3.rounded_rectangle([790, 1125, 975, 1175], radius=20, fill=(254, 240, 245))
    d3.text((815, 1135), "FULL LOOK", fill=ACCENT_PINK, font=font_slide_tag)

add_header_footer(s3, 3, 5, "OUTFIT GRID")

# =========================================================================
# SLIDE 4: ON-MODEL FIT CHECK (Fresh Female Model Appearance!)
# =========================================================================
print("Rendering Slide 4: On-Model Lookbook Reveal (Female Model)...")
s4 = create_base_canvas()
d4 = ImageDraw.Draw(s4)

card_box = [65, 130, 1015, 1220]
d4.rounded_rectangle(card_box, radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)

# Insert real Colorbox female model wearing the jacket & look
model_jacket_path = KB_IMAGES / "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg"
if model_jacket_path.exists():
    im_m = Image.open(model_jacket_path).convert("RGB")
    # Resize and crop nicely
    im_m_fit = im_m.resize((660, 950), Image.Resampling.LANCZOS)
    px = (1080 - 660) // 2
    s4.paste(im_m_fit, (px, 145))

# Polaroid scrapbook tape accents
d4.rectangle([px + 40, 135, px + 180, 155], fill=(255, 230, 200, 180))
d4.rectangle([px + 480, 135, px + 620, 155], fill=(255, 215, 230, 180))

d4.text((100, 1115), "💖 THE FIT CHECK (ON MODEL)", fill=TEXT_DARK, font=font_caption)
d4.text((100, 1165), "Effortless Gen-Z chic for campus, hangout, or weekend coffee run", fill=TEXT_MUTED, font=font_sub)
d4.rounded_rectangle([800, 1120, 975, 1175], radius=20, fill=(254, 240, 245))
d4.text((830, 1133), "10/10 FIT", fill=ACCENT_PINK, font=font_slide_tag)

add_header_footer(s4, 4, 5, "ON-MODEL TRY-ON")

# =========================================================================
# SLIDE 5: LOOKBOOK FINALE / INTERACTIVE CALL TO ACTION
# =========================================================================
print("Rendering Slide 5: Lookbook Finale & Chic Moodboard...")
s5 = create_base_canvas()
d5 = ImageDraw.Draw(s5)

card_box = [65, 130, 1015, 1220]
d5.rounded_rectangle(card_box, radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)

# Mini collage of the look
if ai_tee_path.exists() and model_jacket_path.exists():
    im_thumb1 = Image.open(ai_tee_path).convert("RGB").resize((420, 520), Image.Resampling.LANCZOS)
    im_thumb2 = Image.open(model_jacket_path).convert("RGB").resize((420, 520), Image.Resampling.LANCZOS)
    
    s5.paste(im_thumb1, (100, 200))
    s5.paste(im_thumb2, (560, 200))
    
    d5.rounded_rectangle([100, 735, 520, 785], radius=16, fill=(254, 240, 245))
    d5.text((130, 747), "TEE: Rp 99.900", fill=ACCENT_PINK, font=font_slide_tag)
    
    d5.rounded_rectangle([560, 735, 980, 785], radius=16, fill=(245, 240, 255))
    d5.text((590, 747), "JACKET: Rp 329.900", fill=ACCENT_LILAC, font=font_slide_tag)

# Big chic poll question
d5.text((100, 840), "Which piece is your fave? 💬", fill=TEXT_DARK, font=ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 46))
d5.text((100, 915), "Drop a comment below & tag your bestie to match fits!", fill=TEXT_MUTED, font=font_sub)

# Interactive sticker badges
d5.rounded_rectangle([100, 990, 480, 1070], radius=24, fill=(253, 240, 245), outline=ACCENT_PINK, width=2)
d5.text((130, 1012), "💖 TEAM PINK TEE", fill=ACCENT_PINK, font=font_caption)

d5.rounded_rectangle([540, 990, 980, 1070], radius=24, fill=(245, 240, 255), outline=ACCENT_LILAC, width=2)
d5.text((570, 1012), "✨ TEAM CROP JACKET", fill=ACCENT_LILAC, font=font_caption)

# Save swipe prompt
d5.text((100, 1140), "Available at colorbox.co.id & all Colorbox offline stores", fill=TEXT_MUTED, font=font_sub)

add_header_footer(s5, 5, 5, "COMMUNITY POLL")

# =========================================================================
# SAVE TO ALL FOLDERS
# =========================================================================
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
        target = d / name
        im.save(str(target), format="PNG", quality=95)
    print(f"Saved {name} (1080x1350 px)")

print("=== ALL 5 CHIC SLIDES GENERATED AND SAVED ACROSS REPOSITORIES ===")
