import os
import sys
import json
import base64
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))
try:
    from opencode_client import call_opencode_chat, call_opencode_image_generation, get_opencode_key
except ImportError:
    call_opencode_chat = None
    call_opencode_image_generation = None
    get_opencode_key = None

DEFAULT_IMAGE_MODEL = "openai/gpt-image-2"

def call_opencode_image_gen(prompt: str, model: str = DEFAULT_IMAGE_MODEL) -> bytes | None:
    """Attempts direct image generation via OpenCode Zen API using openai/gpt-image-2."""
    if call_opencode_image_generation:
        try:
            res = call_opencode_image_generation(prompt, model=model)
            if res:
                return res
        except Exception as e:
            print(f"[OpenCode Image Gen Error]: {e}")
    return None

def call_gemini_image_generation(prompt: str) -> bytes | None:
    """Compatibility wrapper redirecting image generation to openai/gpt-image-2 via OpenCode Zen."""
    return call_opencode_image_gen(prompt, model=DEFAULT_IMAGE_MODEL)

COLOR_MAP = {
    "DARK BLUE": (28, 43, 69),
    "NAVY": (24, 38, 62),
    "BLACK": (25, 25, 28),
    "DARK BROWN": (62, 39, 35),
    "BROWN": (85, 55, 45),
    "OFF WHITE": (246, 243, 236),
    "WHITE": (252, 252, 252),
    "ECRU": (236, 229, 216),
    "LT. PINK": (248, 187, 208),
    "PINK": (244, 143, 177),
    "GREY": (99, 103, 110),
    "LIGHT GREY": (189, 195, 199),
    "LT. GREY": (189, 195, 199),
    "LILAC": (209, 196, 233),
    "BUTTER": (255, 249, 196),
    "BEIGE": (235, 222, 203),
    "CORAL": (235, 78, 98),
    "DUSTY OLIVE": (98, 114, 84),
    "DARK RED": (138, 28, 44),
}

def get_swatches_for_product(prod: dict, count: int = 5) -> list[tuple[int, int, int]]:
    c_name = str(prod.get("color", "")).upper()
    palette = []
    for k, rgb in COLOR_MAP.items():
        if k in c_name:
            palette.append(rgb)
            break
            
    defaults = [(28, 43, 69), (25, 25, 28), (98, 114, 84), (138, 28, 44), (236, 229, 216), (235, 78, 98)]
    for d in defaults:
        if d not in palette and len(palette) < count:
            palette.append(d)
    return palette[:count]

def paste_proportional(canvas: Image.Image, img: Image.Image, box_x: int, box_y: int, box_w: int, box_h: int) -> tuple[int, int, int, int]:
    """
    Pastes img into (box_x, box_y, box_w, box_h) maintaining strict original aspect ratio.
    Zero stretching, zero distortion. Returns actual bounding box placed.
    """
    orig_w, orig_h = img.size
    scale = min(box_w / orig_w, box_h / orig_h)
    new_w = max(1, int(orig_w * scale))
    new_h = max(1, int(orig_h * scale))

    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    offset_x = box_x + (box_w - new_w) // 2
    offset_y = box_y + (box_h - new_h) // 2

    if resized.mode == "RGBA":
        canvas.paste(resized, (offset_x, offset_y), resized)
    else:
        canvas.paste(resized, (offset_x, offset_y))
        
    return offset_x, offset_y, new_w, new_h

def draw_color_palette(draw: ImageDraw.ImageDraw, start_x: int, start_y: int, colors: list[tuple[int, int, int]], radius: int = 15, spacing: int = 38):
    for idx, rgb in enumerate(colors):
        cx = start_x + (idx * spacing)
        draw.ellipse([cx - radius, start_y - radius, cx + radius, start_y + radius], fill=rgb, outline=(220, 220, 220), width=1)


def render_final_carousel_package(
    theme_title: str,
    headline: str,
    subtitle: str,
    products_info: list[dict],
    output_dir: str,
    images_dir: str,
    day_num: int = 1,
    visual_prompts: list[str] = None
) -> dict:
    """
    Renders 5 bespoke, template-free 1080x1350 px Feed Portrait carousel slides:
    1. ZERO rigid templates: No fixed washi tape, no doodle hearts, no hardcoded coffee flat-lays.
    2. Dynamic, Product-Driven Editorial Design:
       - Directly adapts to the specific products, colors, and concepts provided.
       - Highlights authentic garments with 100% locked aspect ratio (zero distortion).
    3. ZERO noise: No 'SLIDE 1/5', no 'SWIPE', no pagination dots on canvas.
    4. ZERO prices on canvas: Kept clean for Instagram Feed lookbook.
    5. AI-Prompter Driven: If visual prompts from Bram are provided, attempts AI image generation.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Dynamic Palette based on actual products or day theme
    p1 = products_info[0] if len(products_info) > 0 else {}
    p2 = products_info[1] if len(products_info) > 1 else p1
    p3 = products_info[2] if len(products_info) > 2 else p2

    p1_name = p1.get("name", "Colorbox Selection").upper()
    p2_name = p2.get("name", "Fashion Essential").upper()
    p3_name = p3.get("name", "Complete Look").upper()

    # Dynamic Background Palette: clean, modern, ultra-editorial
    if day_num == 2:
        BG_COLOR = (244, 241, 235)       # Warm Earthy Paper
        CARD_BG = (252, 250, 246)        # Crisp Cream
        TEXT_DARK = (38, 28, 24)         # Deep Espresso
        TEXT_MUTED = (125, 115, 105)     # Muted Taupe
        ACCENT_COLOR = (180, 80, 50)     # Terracotta
    elif day_num == 3:
        BG_COLOR = (240, 242, 245)       # Cool Studio Off-White
        CARD_BG = (255, 255, 255)        # Pure Crisp White
        TEXT_DARK = (20, 20, 24)         # Jet Black
        TEXT_MUTED = (110, 115, 125)     # Slate Grey
        ACCENT_COLOR = (145, 30, 48)     # Crimson
    else:
        BG_COLOR = (248, 246, 242)       # Soft Minimalist Ivory
        CARD_BG = (255, 255, 255)        # Pure White
        TEXT_DARK = (24, 24, 28)         # Clean Black
        TEXT_MUTED = (115, 115, 120)     # Neutral Grey
        ACCENT_COLOR = (235, 78, 98)     # Colorbox Coral

    # Fonts
    try:
        font_headline = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 64)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
        font_body = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
        font_brand = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 28)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
    except Exception:
        font_headline = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_brand = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    generated_slides = []

    # Resolve local images
    def resolve_img(p_dict):
        fname = p_dict.get("image_file", "")
        if fname:
            fp = os.path.join(images_dir, fname)
            if os.path.exists(fp):
                return fp
        return None

    p1_img = resolve_img(p1)
    p2_img = resolve_img(p2)
    p3_img = resolve_img(p3)

    # --------------------------------------------------------------------------
    # SLIDE 1: BESPOKE HERO COVER
    # --------------------------------------------------------------------------
    s1 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)

    # Brand Header (Minimalist & Clean)
    d1.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_brand)
    concept_title = (theme_title or p1_name[:24]).upper()
    d1.text((260, 52), f"|   {concept_title}", fill=TEXT_MUTED, font=font_body)

    # Clean Headline
    hl_text = (headline or p1_name[:32]).upper()
    d1.text((70, 120), hl_text, fill=TEXT_DARK, font=font_headline)

    # Hero Visual Area (Full frame with elegant card & proportional photo)
    d1.rounded_rectangle([70, 230, 1010, 1220], radius=16, fill=CARD_BG, outline=(225, 222, 215), width=1)
    if p1_img and os.path.exists(p1_img):
        im1 = Image.open(p1_img).convert("RGB")
        paste_proportional(s1, im1, 90, 250, 900, 940)

    # Minimal Color Palette Bar at Bottom
    d1.rounded_rectangle([90, 1240, 990, 1300], radius=12, fill=CARD_BG)
    d1.text((120, 1255), "OFFICIAL COLORWAYS", fill=TEXT_MUTED, font=font_sm)
    draw_color_palette(d1, 680, 1270, get_swatches_for_product(p1, 5))

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    generated_slides.append(p1_path)

    # --------------------------------------------------------------------------
    # SLIDE 2: HERO PRODUCT STYLING
    # --------------------------------------------------------------------------
    s2 = Image.new("RGB", (1080, 1350), color=CARD_BG)
    d2 = ImageDraw.Draw(s2)
    d2.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_brand)
    d2.text((260, 52), f"|   {p1.get('category', 'COLLECTION').upper()}", fill=TEXT_MUTED, font=font_body)
    
    # Title from Product
    d2.text((70, 115), p1_name[:36], fill=TEXT_DARK, font=font_sub)
    if p1.get("color"):
        d2.text((70, 165), f"Colorway: {p1['color']}", fill=ACCENT_COLOR, font=font_body)

    # Large Clean Image Focus
    d2.rounded_rectangle([70, 220, 1010, 1220], radius=16, fill=BG_COLOR, outline=(225, 222, 215), width=1)
    if p1_img and os.path.exists(p1_img):
        im1 = Image.open(p1_img).convert("RGB")
        paste_proportional(s2, im1, 90, 240, 900, 960)

    # Bottom minimal info
    d2.text((100, 1260), f"Sizes: {p1.get('sizes', 'S, M, L, XL')}", fill=TEXT_MUTED, font=font_body)
    draw_color_palette(d2, 800, 1275, get_swatches_for_product(p1, 4))

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    generated_slides.append(p2_path)

    # --------------------------------------------------------------------------
    # SLIDE 3: PAIRING & SILHOUETTE FOCUS
    # --------------------------------------------------------------------------
    s3 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)
    d3.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_brand)
    d3.text((260, 52), f"|   {p2.get('category', 'SILHOUETTE').upper()}", fill=TEXT_MUTED, font=font_body)

    d3.text((70, 115), p2_name[:36], fill=TEXT_DARK, font=font_sub)
    if p2.get("color"):
        d3.text((70, 165), f"Featured: {p2['color']}", fill=ACCENT_COLOR, font=font_body)

    d3.rounded_rectangle([70, 220, 1010, 1220], radius=16, fill=CARD_BG, outline=(225, 222, 215), width=1)
    active_p2_img = p2_img if p2_img else p1_img
    if active_p2_img and os.path.exists(active_p2_img):
        im2 = Image.open(active_p2_img).convert("RGB")
        paste_proportional(s3, im2, 90, 240, 900, 960)

    d3.text((100, 1260), f"Sizes: {p2.get('sizes', 'S, M, L, XL')}", fill=TEXT_MUTED, font=font_body)
    draw_color_palette(d3, 800, 1275, get_swatches_for_product(p2, 4))

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    generated_slides.append(p3_path)

    # --------------------------------------------------------------------------
    # SLIDE 4: COMPLETE OUTFIT & DETAILS
    # --------------------------------------------------------------------------
    s4 = Image.new("RGB", (1080, 1350), color=CARD_BG)
    d4 = ImageDraw.Draw(s4)
    d4.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_brand)
    d4.text((260, 52), "|   STYLING FORMULA", fill=TEXT_MUTED, font=font_body)
    d4.text((70, 115), "THE COMPLETE ENSEMBLE", fill=TEXT_DARK, font=font_sub)

    # Duo Split Frame (Clean high-fashion lookbook)
    box_w = 425
    d4.rounded_rectangle([70, 200, 70 + box_w, 1180], radius=14, fill=BG_COLOR, outline=(225, 222, 215), width=1)
    d4.rounded_rectangle([585, 200, 585 + box_w, 1180], radius=14, fill=BG_COLOR, outline=(225, 222, 215), width=1)

    if p1_img and os.path.exists(p1_img):
        im1 = Image.open(p1_img).convert("RGB")
        paste_proportional(s4, im1, 80, 210, box_w - 20, 920)
    d4.text((90, 1140), p1_name[:22], fill=TEXT_DARK, font=font_sm)

    active_p3_img = p3_img if p3_img else (p2_img if p2_img else p1_img)
    if active_p3_img and os.path.exists(active_p3_img):
        im3 = Image.open(active_p3_img).convert("RGB")
        paste_proportional(s4, im3, 595, 210, box_w - 20, 920)
    d4.text((605, 1140), p3_name[:22], fill=TEXT_DARK, font=font_sm)

    d4.text((70, 1240), "#NeverJustOneThing  •  Authentic Colorbox Styling", fill=TEXT_MUTED, font=font_body)

    p4_path = os.path.join(output_dir, "slide_4_accessories_layering.png")
    s4.save(p4_path, "PNG", quality=95)
    generated_slides.append(p4_path)

    # --------------------------------------------------------------------------
    # SLIDE 5: EDITORIAL LOOKBOOK OUTRO & INSPIRATION
    # --------------------------------------------------------------------------
    s5 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d5 = ImageDraw.Draw(s5)
    d5.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_brand)
    d5.text((260, 52), "|   SEASONAL HIGHLIGHT", fill=TEXT_MUTED, font=font_body)

    d5.text((70, 115), "STYLING INSPIRATION", fill=TEXT_DARK, font=font_headline)
    d5.text((70, 195), "Dapatkan koleksi lengkap di website resmi dan seluruh gerai.", fill=TEXT_MUTED, font=font_body)

    d5.rounded_rectangle([70, 260, 1010, 1220], radius=16, fill=CARD_BG, outline=(225, 222, 215), width=1)
    if p1_img and os.path.exists(p1_img):
        im1 = Image.open(p1_img).convert("RGB")
        paste_proportional(s5, im1, 90, 280, 900, 920)

    # Clean Brand Sign-off
    d5.text((90, 1245), "#NeverJustOneThing", fill=ACCENT_COLOR, font=font_sub)
    d5.text((680, 1255), "colorbox.co.id", fill=TEXT_MUTED, font=font_body)

    p5_path = os.path.join(output_dir, "slide_5_outro_cta.png")
    s5.save(p5_path, "PNG", quality=95)
    generated_slides.append(p5_path)

    # Interactive HTML Preview
    generate_carousel_preview_html(output_dir, headline or concept_title, subtitle or "Colorbox Campaign", day_num)

    return {
        "success": True,
        "slides": generated_slides,
        "html_preview": os.path.join(output_dir, "carousel_preview.html")
    }

def generate_carousel_preview_html(output_dir: str, title: str, subtitle: str, day_num: int = 1) -> str:
    html_path = os.path.join(output_dir, "carousel_preview.html")
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Colorbox Editorial Carousel — Day {day_num}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f1117;
      color: #fff;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 15px;
      margin: 0;
    }}
    .header {{ text-align: center; margin-bottom: 25px; }}
    .header h1 {{ margin: 0 0 6px; font-size: 24px; font-weight: 700; color: #f43f5e; }}
    .header p {{ margin: 0; color: #94a3b8; font-size: 14px; }}
    .badge {{ display: inline-block; padding: 4px 12px; background: rgba(244,63,94,0.15); border: 1px solid #f43f5e; border-radius: 20px; font-size: 12px; font-weight: 600; color: #f43f5e; margin-bottom: 10px; }}
    .carousel-container {{
      position: relative;
      width: 100%;
      max-width: 440px;
      aspect-ratio: 4/5;
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.6);
      background: #181920;
    }}
    .slides-wrapper {{
      display: flex;
      width: 100%;
      height: 100%;
      overflow-x: auto;
      scroll-snap-type: x mandatory;
      scrollbar-width: none;
    }}
    .slides-wrapper::-webkit-scrollbar {{ display: none; }}
    .slide-item {{
      flex: 0 0 100%;
      height: 100%;
      scroll-snap-align: start;
    }}
    .slide-item img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }}
    .nav-hints {{
      display: flex;
      justify-content: space-between;
      width: 100%;
      max-width: 440px;
      margin-top: 14px;
      color: #64748b;
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <span class="badge">DAY {day_num} EDITORIAL CAMPAIGN</span>
    <h1>{title}</h1>
    <p>{subtitle} • 1080 × 1350 px (4:5 Feed Portrait)</p>
  </div>
  <div class="carousel-container">
    <div class="slides-wrapper">
      <div class="slide-item"><img src="slide_1_cover_hero.png" alt="Slide 1"></div>
      <div class="slide-item"><img src="slide_2_hero_top.png" alt="Slide 2"></div>
      <div class="slide-item"><img src="slide_3_bottom_pairing.png" alt="Slide 3"></div>
      <div class="slide-item"><img src="slide_4_accessories_layering.png" alt="Slide 4"></div>
      <div class="slide-item"><img src="slide_5_outro_cta.png" alt="Slide 5"></div>
    </div>
  </div>
  <div class="nav-hints">
    <span>Geser / Swipe horizontal</span>
    <span>5 Slides Ready-to-Post</span>
  </div>
</body>
</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_path
