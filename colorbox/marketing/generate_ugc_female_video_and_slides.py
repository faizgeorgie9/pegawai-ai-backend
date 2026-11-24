import os
import shutil
import base64
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

print("=== 1. POLISHING SLIDES (CLEAN TYPOGRAPHY, NO TOFU GLYPHS) ===")

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

BG_CREAM = (253, 248, 245)
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
    return Image.new("RGB", (w, h), BG_CREAM)

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

ai_tee_path = BRAIN_DIR / "slide_1_hero_pink_tee_1795499426687.jpg"
ai_jacket_path = BRAIN_DIR / "slide_2_mix_match_jacket_1795499443707.jpg"
ai_grid_path = BRAIN_DIR / "slide_3_full_outfit_grid_1795499442332.jpg"
model_jacket_path = KB_IMAGES / "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg"

# SLIDE 1
s1 = create_base_canvas()
if ai_tee_path.exists():
    im1_fit = Image.open(ai_tee_path).convert("RGB").resize((940, 940), Image.Resampling.LANCZOS)
    d1 = ImageDraw.Draw(s1)
    d1.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
    s1.paste(im1_fit, (70, 145))
    d1.text((100, 1115), "PINK OBSESSION TEE", fill=TEXT_DARK, font=font_caption)
    d1.text((100, 1165), "Oversized fit with soft cherry blossom artwork", fill=TEXT_MUTED, font=font_sub)
    d1.rounded_rectangle([790, 1120, 975, 1175], radius=20, fill=(254, 240, 245))
    d1.text((815, 1133), "MUST-HAVE", fill=ACCENT_PINK, font=font_slide_tag)
add_header_footer(s1, 1, 5, "THE STATEMENT TEE")

# SLIDE 2
s2 = create_base_canvas()
if ai_jacket_path.exists():
    im2_fit = Image.open(ai_jacket_path).convert("RGB").resize((940, 940), Image.Resampling.LANCZOS)
    d2 = ImageDraw.Draw(s2)
    d2.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
    s2.paste(im2_fit, (70, 145))
    d2.text((100, 1115), "STYLE PAIRING: TEE + CROP JACKET", fill=TEXT_DARK, font=font_caption)
    d2.text((100, 1165), "Soft pink graphic meets tailored grey structure", fill=TEXT_MUTED, font=font_sub)
    d2.rounded_rectangle([800, 1120, 975, 1175], radius=20, fill=(245, 240, 255))
    d2.text((825, 1133), "PERFECT DUO", fill=ACCENT_LILAC, font=font_slide_tag)
add_header_footer(s2, 2, 5, "STYLING FORMULA")

# SLIDE 3
s3 = create_base_canvas()
if ai_grid_path.exists():
    im3_fit = Image.open(ai_grid_path).convert("RGB").resize((860, 960), Image.Resampling.LANCZOS)
    d3 = ImageDraw.Draw(s3)
    d3.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
    px = (1080 - 860) // 2
    s3.paste(im3_fit, (px, 145))
    d3.text((100, 1125), "HEAD-TO-TOE OOTD GRID", fill=TEXT_DARK, font=font_caption)
    d3.text((100, 1170), "Tee + Cropped Jacket + Barrel Denim + Doodle Tote", fill=TEXT_MUTED, font=font_sub)
    d3.rounded_rectangle([790, 1125, 975, 1175], radius=20, fill=(254, 240, 245))
    d3.text((815, 1135), "FULL LOOK", fill=ACCENT_PINK, font=font_slide_tag)
add_header_footer(s3, 3, 5, "OUTFIT GRID")

# SLIDE 4
s4 = create_base_canvas()
d4 = ImageDraw.Draw(s4)
d4.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
if model_jacket_path.exists():
    im_m_fit = Image.open(model_jacket_path).convert("RGB").resize((660, 950), Image.Resampling.LANCZOS)
    px = (1080 - 660) // 2
    s4.paste(im_m_fit, (px, 145))
d4.rectangle([px + 40, 135, px + 180, 155], fill=(255, 230, 200, 180))
d4.rectangle([px + 480, 135, px + 620, 155], fill=(255, 215, 230, 180))
d4.text((100, 1115), "THE FIT CHECK (ON MODEL)", fill=TEXT_DARK, font=font_caption)
d4.text((100, 1165), "Effortless Gen-Z chic for campus, hangout, or weekend coffee run", fill=TEXT_MUTED, font=font_sub)
d4.rounded_rectangle([800, 1120, 975, 1175], radius=20, fill=(254, 240, 245))
d4.text((830, 1133), "10/10 FIT", fill=ACCENT_PINK, font=font_slide_tag)
add_header_footer(s4, 4, 5, "ON-MODEL TRY-ON")

# SLIDE 5
s5 = create_base_canvas()
d5 = ImageDraw.Draw(s5)
d5.rounded_rectangle([65, 130, 1015, 1220], radius=32, fill=CARD_BG, outline=BORDER_PASTEL, width=2)
if ai_tee_path.exists() and model_jacket_path.exists():
    im_thumb1 = Image.open(ai_tee_path).convert("RGB").resize((420, 520), Image.Resampling.LANCZOS)
    im_thumb2 = Image.open(model_jacket_path).convert("RGB").resize((420, 520), Image.Resampling.LANCZOS)
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
d5.text((150, 1015), "TEAM PINK TEE", fill=ACCENT_PINK, font=font_caption)

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
    print(f"Polished {name}")

# =========================================================================
# 2. GENERATE UGC FEMALE MODEL VIDEO WITH PLAYWRIGHT
# =========================================================================
print("\n=== 2. RECORDING HIGH-ENERGY UGC VIDEO WITH FEMALE MODEL (CRE-04) ===")

# Prepare base64 images for HTML embedding
def img_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

b64_model = img_to_b64(model_jacket_path)
b64_tee = img_to_b64(ai_tee_path)
b64_grid = img_to_b64(ai_grid_path)

html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  body {{
    width: 720px;
    height: 1280px;
    background: #181416;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    overflow: hidden;
    color: white;
    position: relative;
  }}

  /* Video Stage */
  .stage {{
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  /* Scene 1: Opening Model Hook */
  .scene-1 {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #FFDFEC 0%, #F5E8FF 50%, #FFEFE6 100%);
    animation: fadeOutScene1 0.6s ease forwards 3.2s;
  }}

  .model-card {{
    width: 580px;
    height: 840px;
    background: white;
    border-radius: 36px;
    box-shadow: 0 25px 60px rgba(244, 114, 150, 0.25);
    overflow: hidden;
    position: relative;
    transform: scale(0.92);
    animation: zoomHero 3s ease forwards;
  }}

  .model-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}

  .badge-tag {{
    position: absolute;
    top: 24px;
    left: 24px;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(8px);
    color: #F47296;
    padding: 10px 22px;
    border-radius: 20px;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  }}

  .rating-tag {{
    position: absolute;
    bottom: 24px;
    right: 24px;
    background: #F47296;
    color: white;
    padding: 10px 22px;
    border-radius: 20px;
    font-size: 20px;
    font-weight: 800;
  }}

  /* Scene 2: Product & Outfit Grid Cut */
  .scene-2 {{
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #FFF0F5 0%, #F8F4FF 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    opacity: 0;
    animation: fadeInScene2 0.6s ease forwards 3.2s;
  }}

  .grid-card {{
    width: 580px;
    height: 840px;
    background: white;
    border-radius: 36px;
    box-shadow: 0 25px 60px rgba(186, 160, 215, 0.25);
    overflow: hidden;
    position: relative;
    animation: pulseGrid 3s ease forwards 3.2s;
  }}

  .grid-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}

  /* Reels / TikTok UI Overlay */
  .ui-overlay {{
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 10;
  }}

  .top-bar {{
    position: absolute;
    top: 45px;
    left: 40px;
    right: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}

  .user-pill {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(0,0,0,0.5);
    backdrop-filter: blur(10px);
    padding: 8px 18px;
    border-radius: 24px;
  }}

  .avatar {{
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: #F47296;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 16px;
  }}

  .username {{
    font-size: 20px;
    font-weight: 700;
  }}

  .follow-btn {{
    background: #F47296;
    color: white;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 15px;
    font-weight: 700;
  }}

  /* Right Action Icons */
  .actions-col {{
    position: absolute;
    right: 32px;
    bottom: 180px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 28px;
  }}

  .action-item {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }}

  .action-icon {{
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background: rgba(0,0,0,0.45);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
  }}

  .action-label {{
    font-size: 16px;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0,0,0,0.6);
  }}

  /* Bottom Caption Area */
  .bottom-info {{
    position: absolute;
    bottom: 45px;
    left: 40px;
    right: 120px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}

  .caption-title {{
    font-size: 26px;
    font-weight: 800;
    color: #1A1A1A;
    background: rgba(255,255,255,0.85);
    padding: 8px 16px;
    border-radius: 12px;
    width: fit-content;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }}

  .caption-desc {{
    font-size: 19px;
    font-weight: 600;
    color: #FFFFFF;
    text-shadow: 0 2px 8px rgba(0,0,0,0.8);
    line-height: 1.4;
  }}

  .music-tag {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 17px;
    color: #FFFFFF;
    background: rgba(0,0,0,0.5);
    padding: 6px 14px;
    border-radius: 18px;
    width: fit-content;
  }}

  @keyframes zoomHero {{
    0% {{ transform: scale(0.92); }}
    100% {{ transform: scale(1.02); }}
  }}

  @keyframes fadeOutScene1 {{
    0% {{ opacity: 1; }}
    100% {{ opacity: 0; pointer-events: none; }}
  }}

  @keyframes fadeInScene2 {{
    0% {{ opacity: 0; transform: scale(0.95); }}
    100% {{ opacity: 1; transform: scale(1); }}
  }}

  @keyframes pulseGrid {{
    0% {{ transform: scale(0.95); }}
    100% {{ transform: scale(1.03); }}
  }}
</style>
</head>
<body>
  <div class="stage">
    <!-- Scene 1: Female Model Try-on Look -->
    <div class="scene-1">
      <div class="model-card">
        <img class="model-img" src="data:image/jpeg;base64,{b64_model}" />
        <div class="badge-tag">OOTD TRY-ON ✨</div>
        <div class="rating-tag">10/10 FIT 💕</div>
      </div>
    </div>

    <!-- Scene 2: Product Styling Breakdown -->
    <div class="scene-2">
      <div class="grid-card">
        <img class="grid-img" src="data:image/jpeg;base64,{b64_grid}" />
        <div class="badge-tag">PINK CRUSH FORMULA 🌸</div>
        <div class="rating-tag">COLORBOX</div>
      </div>
    </div>
  </div>

  <!-- Reels / UGC Overlay -->
  <div class="ui-overlay">
    <div class="top-bar">
      <div class="user-pill">
        <div class="avatar">C</div>
        <span class="username">colorbox_id</span>
        <span class="follow-btn">Follow</span>
      </div>
      <div style="font-size: 28px; text-shadow:0 2px 4px rgba(0,0,0,0.5);">⋮</div>
    </div>

    <div class="actions-col">
      <div class="action-item">
        <div class="action-icon" style="color: #FF4D6D;">❤️</div>
        <span class="action-label">18.4K</span>
      </div>
      <div class="action-item">
        <div class="action-icon">💬</div>
        <span class="action-label">492</span>
      </div>
      <div class="action-item">
        <div class="action-icon">🔖</div>
        <span class="action-label">1.2K</span>
      </div>
      <div class="action-item">
        <div class="action-icon">↗</div>
        <span class="action-label">Share</span>
      </div>
    </div>

    <div class="bottom-info">
      <div class="caption-title">Pink Tee + Cropped Jacket 💖</div>
      <div class="caption-desc">Spill OOTD cewek kue yang chic & ga ngebosenin! Graphic tee manis di-layer outer crop grey = auto elevated 🌸✨ #ColorboxBabes #OOTD</div>
      <div class="music-tag">♫ Colorbox Vibes - Cherry Blossom Beat</div>
    </div>
  </div>
</body>
</html>
"""

temp_html = Path("temp_ugc_video_record.html")
temp_html.write_text(html_content, encoding="utf-8")

rec_dir = Path("video_recording_scratch")
rec_dir.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        record_video_dir=str(rec_dir),
        record_video_size={"width": 720, "height": 1280},
        viewport={"width": 720, "height": 1280}
    )
    page = context.new_page()
    page.goto(f"file:///{temp_html.resolve().as_posix()}")
    # Let animation play for 6.5 seconds
    time.sleep(6.5)
    page.close()
    context.close()
    browser.close()

# Find recorded video
vids = list(rec_dir.glob("*.webm")) + list(rec_dir.glob("*.mp4"))
print(f"Recorded videos: {vids}")

if vids:
    recorded_file = vids[-1]
    print(f"Using recorded file: {recorded_file} ({recorded_file.stat().st_size} bytes)")
    
    # Copy as both .webm and .mp4 across all destination directories
    for d in OUTPUT_DIRS:
        shutil.copy(str(recorded_file), str(d / "ugc_video.webm"))
        shutil.copy(str(recorded_file), str(d / "ugc_video.mp4"))
        shutil.copy(str(recorded_file), str(d / "ugc_video_graphic_tee.mp4"))
    print("=== UGC FEMALE MODEL VIDEO DISTRIBUTED SUCCESSFULLY ===")
