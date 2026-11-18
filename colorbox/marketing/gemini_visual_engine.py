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
    "DARK NAVY": (18, 28, 48),
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
    "DENIM": (65, 95, 135),
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

def resolve_product_angles(prod: dict, images_dir: str) -> dict[str, str]:
    """
    Resolves multi-angle images (front, back, detail, side) for a given product dict.
    Returns a dictionary of absolute file paths keyed by angle name.
    """
    angles = {}
    prod_angles = prod.get("angles", {})
    if isinstance(prod_angles, dict):
        for k, fname in prod_angles.items():
            fp = os.path.join(images_dir, fname)
            if os.path.exists(fp):
                angles[k] = fp
                
    # Fallback to image_file
    main_file = prod.get("image_file", "")
    if main_file:
        fp = os.path.join(images_dir, main_file)
        if os.path.exists(fp):
            if "front" not in angles:
                angles["front"] = fp

    # Also inspect images_dir by product prefix (e.g. cbx-11a -> 11b, 11c)
    if "front" in angles and ("back" not in angles or "detail" not in angles):
        front_name = os.path.basename(angles["front"])
        m = re.match(r"(cbx-\d+)[a-z]-(.+)", front_name)
        if m:
            prefix = m.group(1)
            for f in os.listdir(images_dir):
                if f.startswith(prefix) and f.endswith(".jpg"):
                    full_p = os.path.join(images_dir, f)
                    if "back" in f or "-b-" in f:
                        angles.setdefault("back", full_p)
                    elif "detail" in f or "-c-" in f:
                        angles.setdefault("detail", full_p)
                    elif "side" in f:
                        angles.setdefault("side", full_p)
                    elif "top-down" in f:
                        angles.setdefault("top_down", full_p)

    # Defaults if missing
    front_p = angles.get("front")
    if not front_p and main_file:
        fp = os.path.join(images_dir, main_file)
        if os.path.exists(fp):
            front_p = fp
            angles["front"] = front_p

    if front_p:
        angles.setdefault("detail", front_p)
        angles.setdefault("back", front_p)
        angles.setdefault("side", angles.get("back", front_p))

    return angles


# ==============================================================================
# ARCHETYPE 1 (DAY 1): ATELIER HAUTE-MINIMALIST EDITORIAL
# ==============================================================================
def _render_archetype_1(
    theme_title: str,
    headline: str,
    subtitle: str,
    p1: dict,
    p2: dict,
    p3: dict,
    p1_angles: dict,
    p2_angles: dict,
    p3_angles: dict,
    output_dir: str
) -> list[str]:
    """
    Day 1 Style: Refined warm studio ecru, Georgia serif display, asymmetric collage,
    haute lookbook layout with zero canned boxes.
    """
    BG_COLOR = (247, 245, 240)       # Warm Studio Ecru
    CARD_BG = (255, 255, 255)        # Pure White
    TEXT_DARK = (24, 24, 28)         # Charcoal Black
    TEXT_MUTED = (120, 115, 110)     # Muted Taupe
    ACCENT_COLOR = (225, 83, 66)     # Colorbox Coral
    BORDER_HAIRLINE = (228, 224, 216)

    try:
        font_serif_xl = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 54)
        font_serif_lg = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 40)
        font_serif_italic = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 26)
        font_sans_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
        font_sans_med = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
        font_sans_sm = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    except Exception:
        font_serif_xl = ImageFont.load_default()
        font_serif_lg = font_serif_xl
        font_serif_italic = font_serif_xl
        font_sans_bold = font_serif_xl
        font_sans_med = font_serif_xl
        font_sans_sm = font_serif_xl

    slides = []

    p1_name = p1.get("name", "Tailored Piece").upper()
    p2_name = p2.get("name", "Complementary Bottom").upper()
    p3_name = p3.get("name", "Accessory Accent").upper()

    # SLIDE 1: BESPOKE HERO COVER
    s1 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)
    
    # Minimalist Header
    d1.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_sans_bold)
    d1.text((250, 52), "|   ATELIER EDITORIAL", fill=TEXT_MUTED, font=font_sans_med)
    d1.text((820, 52), "SS/26 EDITION", fill=ACCENT_COLOR, font=font_sans_sm)

    # Headline
    hl_text = (headline or p1_name[:30]).upper()
    d1.text((70, 110), hl_text, fill=TEXT_DARK, font=font_serif_xl)
    concept_str = (theme_title or "Sartorial Precision & Balance").title()
    d1.text((70, 175), f'"{concept_str}"', fill=TEXT_MUTED, font=font_serif_italic)

    # Hero Photo (Full portrait frame)
    d1.rounded_rectangle([70, 230, 1010, 1220], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        im1 = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s1, im1, 90, 250, 900, 940)

    # Palette bar at bottom
    d1.rounded_rectangle([90, 1245, 990, 1305], radius=10, fill=CARD_BG)
    d1.text((120, 1260), "CURATED PALETTE", fill=TEXT_MUTED, font=font_sans_sm)
    draw_color_palette(d1, 680, 1275, get_swatches_for_product(p1, 5))

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    slides.append(p1_path)

    # SLIDE 2: CRAFTSMANSHIP & TEXTURE (Detail Angle)
    s2 = Image.new("RGB", (1080, 1350), color=CARD_BG)
    d2 = ImageDraw.Draw(s2)
    d2.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_sans_bold)
    d2.text((250, 52), "|   CRAFTSMANSHIP & TEXTURE", fill=TEXT_MUTED, font=font_sans_med)
    
    d2.text((70, 110), "MATERIAL WEAVE & DETAIL", fill=TEXT_DARK, font=font_serif_lg)
    d2.text((70, 160), f"Fokus pada presisi jahitan dan tekstur kain {p1.get('color', '')}", fill=TEXT_MUTED, font=font_sans_med)

    # Large Detail Photo Frame
    d2.rounded_rectangle([70, 210, 1010, 1010], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    detail_img = p1_angles.get("detail") or p1_angles.get("front")
    if detail_img:
        im2 = Image.open(detail_img).convert("RGB")
        paste_proportional(s2, im2, 90, 230, 900, 760)

    # Technical Spec Bottom Panel
    d2.rounded_rectangle([70, 1040, 1010, 1280], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    d2.text((100, 1065), "TAILORING SPECIFICATION", fill=ACCENT_COLOR, font=font_sans_bold)
    d2.text((100, 1105), p1_name, fill=TEXT_DARK, font=font_serif_italic)
    d2.text((100, 1145), f"Warna Resmi: {p1.get('color', 'Classic')}  •  Pilihan Ukuran: {p1.get('sizes', 'S - XL')}", fill=TEXT_MUTED, font=font_sans_med)
    d2.text((100, 1185), "Dirancang untuk kenyamanan sepanjang hari dengan potongan presisi khas Colorbox.", fill=TEXT_DARK, font=font_sans_med)

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    slides.append(p2_path)

    # SLIDE 3: COMPLEMENTARY PAIRING (Bottom Front Angle)
    s3 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)
    d3.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_sans_bold)
    d3.text((250, 52), f"|   THE PAIRING FORMULA", fill=TEXT_MUTED, font=font_sans_med)

    d3.text((70, 110), p2_name[:34], fill=TEXT_DARK, font=font_serif_lg)
    d3.text((70, 160), f"Padu-padan ideal bawahan untuk siluet {p1.get('name', 'atasan')} yang proporsional", fill=ACCENT_COLOR, font=font_sans_med)

    d3.rounded_rectangle([70, 210, 1010, 1170], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    bot_img = p2_angles.get("front") or p2_angles.get("detail")
    if bot_img:
        im3 = Image.open(bot_img).convert("RGB")
        paste_proportional(s3, im3, 90, 230, 900, 910)

    d3.text((100, 1210), f"Featured Color: {p2.get('color', 'Neutral')}  •  Sizes: {p2.get('sizes', 'All Sizes')}", fill=TEXT_MUTED, font=font_sans_med)
    draw_color_palette(d3, 800, 1225, get_swatches_for_product(p2, 4))

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    slides.append(p3_path)

    # SLIDE 4: ASYMMETRIC ENSEMBLE COLLAGE (Hero Back/Side + Bottom + Accessory)
    s4 = Image.new("RGB", (1080, 1350), color=CARD_BG)
    d4 = ImageDraw.Draw(s4)
    d4.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_sans_bold)
    d4.text((250, 52), "|   COMPLETE ENSEMBLE", fill=TEXT_MUTED, font=font_sans_med)
    d4.text((70, 105), "HARMONI 360 LOOKBOOK", fill=TEXT_DARK, font=font_serif_lg)

    # Left tall frame: Hero profile / back angle
    d4.rounded_rectangle([70, 170, 540, 1180], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    back_img = p1_angles.get("back") or p1_angles.get("side") or p1_angles.get("front")
    if back_img:
        imb = Image.open(back_img).convert("RGB")
        paste_proportional(s4, imb, 85, 185, 440, 930)
    d4.text((90, 1135), f"{p1_name[:20]} (Profile)", fill=TEXT_DARK, font=font_sans_sm)

    # Right top frame: Complementary bottom
    d4.rounded_rectangle([565, 170, 1010, 660], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    if bot_img:
        imbt = Image.open(bot_img).convert("RGB")
        paste_proportional(s4, imbt, 580, 185, 415, 435)
    d4.text((585, 625), f"{p2_name[:20]}", fill=TEXT_DARK, font=font_sans_sm)

    # Right bottom frame: Accessory or Footwear
    d4.rounded_rectangle([565, 680, 1010, 1180], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    acc_img = p3_angles.get("front") or p3_angles.get("side") or p2_angles.get("front")
    if acc_img:
        ima = Image.open(acc_img).convert("RGB")
        paste_proportional(s4, ima, 580, 695, 415, 435)
    d4.text((585, 1135), f"{p3_name[:20]}", fill=TEXT_DARK, font=font_sans_sm)

    d4.text((70, 1235), "#NeverJustOneThing  •  Authentic Wardrobe Formula", fill=ACCENT_COLOR, font=font_sans_med)

    p4_path = os.path.join(output_dir, "slide_4_accessories_layering.png")
    s4.save(p4_path, "PNG", quality=95)
    # Also save as slide_4_accessories_flatlay.png for legacy compatibility
    s4.save(os.path.join(output_dir, "slide_4_accessories_flatlay.png"), "PNG", quality=95)
    slides.append(p4_path)

    # SLIDE 5: EDITORIAL LOOKBOOK OUTRO
    s5 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d5 = ImageDraw.Draw(s5)
    d5.text((70, 50), "COLORBOX", fill=TEXT_DARK, font=font_sans_bold)
    d5.text((250, 52), "|   LOOKBOOK SIGN-OFF", fill=TEXT_MUTED, font=font_sans_med)

    d5.text((70, 110), "STYLING INSPIRATION", fill=TEXT_DARK, font=font_serif_xl)
    d5.text((70, 175), "Paduan gaya kurasi resmi tim Colorbox Indonesia.", fill=TEXT_MUTED, font=font_serif_italic)

    d5.rounded_rectangle([70, 230, 1010, 1180], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        imf = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s5, imf, 90, 250, 900, 900)

    d5.text((90, 1220), "#NeverJustOneThing", fill=ACCENT_COLOR, font=font_serif_lg)
    d5.text((90, 1270), "Dapatkan di colorbox.co.id & gerai resmi Colorbox seluruh Indonesia", fill=TEXT_MUTED, font=font_sans_med)

    p5_path = os.path.join(output_dir, "slide_5_outro_cta.png")
    s5.save(p5_path, "PNG", quality=95)
    slides.append(p5_path)

    return slides


# ==============================================================================
# ARCHETYPE 2 (DAY 2): ARCHITECTURAL MODERNISM / SWISS GRID
# ==============================================================================
def _render_archetype_2(
    theme_title: str,
    headline: str,
    subtitle: str,
    p1: dict,
    p2: dict,
    p3: dict,
    p1_angles: dict,
    p2_angles: dict,
    p3_angles: dict,
    output_dir: str
) -> list[str]:
    """
    Day 2 Style: Clean architectural concrete grey, black contrast bands, sage green accents,
    strict Swiss grid lines, tri-modular columns. Completely distinct structure.
    """
    BG_COLOR = (238, 240, 242)       # Architectural Concrete Grey
    CARD_BG = (255, 255, 255)        # Pure White
    CONTRAST_BAND = (22, 26, 30)     # Ink Black
    TEXT_DARK = (20, 24, 28)         # Deep Ink
    TEXT_MUTED = (110, 116, 122)     # Studio Slate
    ACCENT_COLOR = (95, 120, 88)     # Sage Green
    BORDER_HAIRLINE = (215, 220, 224)

    try:
        font_sans_xl = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 52)
        font_sans_lg = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
        font_sans_med = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
        font_sans_sm = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
        font_mono = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
    except Exception:
        font_sans_xl = ImageFont.load_default()
        font_sans_lg = font_sans_xl
        font_sans_med = font_sans_xl
        font_sans_sm = font_sans_xl
        font_mono = font_sans_xl

    slides = []

    p1_name = p1.get("name", "Contemporary Essential").upper()
    p2_name = p2.get("name", "Lower Foundation").upper()
    p3_name = p3.get("name", "Accent Footwear").upper()

    # SLIDE 1: ARCHITECTURAL BANNER & PEDESTAL COVER
    s1 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)

    # Top Black Contrast Band
    d1.rectangle([0, 0, 1080, 140], fill=CONTRAST_BAND)
    d1.text((70, 45), "COLORBOX // MODERNIST WARDROBE", fill=(255, 255, 255), font=font_mono)
    d1.text((880, 45), "LOOK 02", fill=ACCENT_COLOR, font=font_mono)

    # Main Visual Pedestal Frame
    d1.rectangle([70, 170, 1010, 1080], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        im1 = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s1, im1, 90, 190, 900, 870)

    # Bottom Information Strip
    d1.rectangle([70, 1110, 1010, 1290], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    d1.rectangle([70, 1110, 85, 1290], fill=ACCENT_COLOR) # Left accent strip
    d1.text((110, 1130), p1_name[:32], fill=TEXT_DARK, font=font_sans_lg)
    d1.text((110, 1180), f"PALETTE: {p1.get('color', 'STUDIO')}  |  CUT: CONTEMPORARY RELAXED", fill=TEXT_MUTED, font=font_sans_sm)
    d1.text((110, 1220), "Konstruksi modular yang adaptif untuk rotasi gaya harian.", fill=ACCENT_COLOR, font=font_sans_med)

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    slides.append(p1_path)

    # SLIDE 2: NUMBERED SPECIFICATION (Left 40% Spec + Right 60% Detail Angle)
    s2 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d2 = ImageDraw.Draw(s2)

    d2.text((70, 45), "COLORBOX // TECHNICAL BREAKDOWN", fill=TEXT_DARK, font=font_mono)
    d2.text((70, 85), "ANATOMI POTONGAN & STRUKTUR", fill=TEXT_DARK, font=font_sans_lg)

    # Left Spec Column
    d2.rectangle([70, 150, 430, 1250], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    d2.text((95, 180), "[01] SILUET", fill=ACCENT_COLOR, font=font_mono)
    d2.text((95, 215), "Relaxed fit dengan", fill=TEXT_DARK, font=font_sans_med)
    d2.text((95, 245), "garis bahu natural.", fill=TEXT_DARK, font=font_sans_med)

    d2.text((95, 330), "[02] TEKSTUR", fill=ACCENT_COLOR, font=font_mono)
    d2.text((95, 365), f"Material {p1.get('color', '')}", fill=TEXT_DARK, font=font_sans_med)
    d2.text((95, 395), "berdensitas sejuk.", fill=TEXT_DARK, font=font_sans_med)

    d2.text((95, 480), "[03] SIZE MATRIX", fill=ACCENT_COLOR, font=font_mono)
    d2.text((95, 515), p1.get('sizes', 'S, M, L, XL'), fill=TEXT_DARK, font=font_sans_med)

    d2.text((95, 620), "[04] COLORWAYS", fill=ACCENT_COLOR, font=font_mono)
    draw_color_palette(d2, 130, 680, get_swatches_for_product(p1, 4), radius=12, spacing=30)

    # Right Large Photo: Detail or Back Angle!
    d2.rectangle([455, 150, 1010, 1250], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    detail_img = p1_angles.get("detail") or p1_angles.get("back") or p1_angles.get("front")
    if detail_img:
        im2 = Image.open(detail_img).convert("RGB")
        paste_proportional(s2, im2, 470, 170, 525, 1060)

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    slides.append(p2_path)

    # SLIDE 3: MODERNIST BOTTOM FOUNDATION
    s3 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)

    d3.text((70, 45), "COLORBOX // LOWER FOUNDATION", fill=TEXT_DARK, font=font_mono)
    d3.text((70, 85), p2_name[:34], fill=TEXT_DARK, font=font_sans_lg)

    # Upper Visual Frame
    d3.rectangle([70, 150, 1010, 1020], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    bot_img = p2_angles.get("front") or p2_angles.get("detail")
    if bot_img:
        im3 = Image.open(bot_img).convert("RGB")
        paste_proportional(s3, im3, 90, 170, 900, 830)

    # Lower Technical Card
    d3.rectangle([70, 1050, 1010, 1270], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    d3.text((100, 1080), f"PASANGAN IDEAL: {p2_name}", fill=ACCENT_COLOR, font=font_mono)
    d3.text((100, 1125), f"Warna: {p2.get('color', 'Neutral')}  •  Potongan terukur untuk keseimbangan volume atas-bawah.", fill=TEXT_DARK, font=font_sans_med)
    d3.text((100, 1175), "Menciptakan siluet ramping & fleksibel untuk mobilitas perkotaan.", fill=TEXT_MUTED, font=font_sans_med)

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    slides.append(p3_path)

    # SLIDE 4: ARCHITECTURAL TRIPTYCH GRID (Top Back + Bottom + Shoes/Bag)
    s4 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d4 = ImageDraw.Draw(s4)

    d4.rectangle([0, 0, 1080, 110], fill=CONTRAST_BAND)
    d4.text((70, 38), "TRIPTYCH STYLING SYSTEM // COMPLETE OUTFIT", fill=(255, 255, 255), font=font_mono)

    col_w = 295
    spacing = 22
    start_x = 70

    # Col 1: Top piece (Profile / Back angle)
    x1 = start_x
    d4.rectangle([x1, 140, x1 + col_w, 1160], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    back_img = p1_angles.get("back") or p1_angles.get("front")
    if back_img:
        imb = Image.open(back_img).convert("RGB")
        paste_proportional(s4, imb, x1 + 10, 155, col_w - 20, 880)
    d4.text((x1 + 15, 1070), "[01] ATASAN", fill=ACCENT_COLOR, font=font_mono)
    d4.text((x1 + 15, 1105), p1_name[:16], fill=TEXT_DARK, font=font_sans_sm)

    # Col 2: Bottom piece
    x2 = x1 + col_w + spacing
    d4.rectangle([x2, 140, x2 + col_w, 1160], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if bot_img:
        imbt = Image.open(bot_img).convert("RGB")
        paste_proportional(s4, imbt, x2 + 10, 155, col_w - 20, 880)
    d4.text((x2 + 15, 1070), "[02] BAWAHAN", fill=ACCENT_COLOR, font=font_mono)
    d4.text((x2 + 15, 1105), p2_name[:16], fill=TEXT_DARK, font=font_sans_sm)

    # Col 3: Accessory or Footwear
    x3 = x2 + col_w + spacing
    d4.rectangle([x3, 140, x3 + col_w, 1160], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    acc_img = p3_angles.get("front") or p3_angles.get("side") or p2_angles.get("front")
    if acc_img:
        ima = Image.open(acc_img).convert("RGB")
        paste_proportional(s4, ima, x3 + 10, 155, col_w - 20, 880)
    d4.text((x3 + 15, 1070), "[03] AKSESORI", fill=ACCENT_COLOR, font=font_mono)
    d4.text((x3 + 15, 1105), p3_name[:16], fill=TEXT_DARK, font=font_sans_sm)

    d4.text((70, 1220), "MODULAR HARMONY • FORM FOLLOWS FUNCTION", fill=TEXT_MUTED, font=font_mono)

    p4_path = os.path.join(output_dir, "slide_4_accessories_layering.png")
    s4.save(p4_path, "PNG", quality=95)
    s4.save(os.path.join(output_dir, "slide_4_accessories_flatlay.png"), "PNG", quality=95)
    slides.append(p4_path)

    # SLIDE 5: MODERNIST INDEX OUTRO
    s5 = Image.new("RGB", (1080, 1350), color=CARD_BG)
    d5 = ImageDraw.Draw(s5)

    d5.rectangle([0, 0, 1080, 140], fill=CONTRAST_BAND)
    d5.text((70, 45), "COLORBOX // COLLECTION INDEX", fill=(255, 255, 255), font=font_mono)
    d5.text((860, 45), "AUTUMN DROP", fill=ACCENT_COLOR, font=font_mono)

    d5.rectangle([70, 180, 1010, 1080], fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        imf = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s5, imf, 90, 200, 900, 860)

    d5.text((70, 1130), "DIRANCANG UNTUK GAYA HIDUP PERKOTAAN", fill=TEXT_DARK, font=font_sans_lg)
    d5.text((70, 1185), "Dapatkan seluruh kurasi di colorbox.co.id & gerai Colorbox terdekat.", fill=TEXT_MUTED, font=font_sans_med)
    d5.text((70, 1235), "#NeverJustOneThing  •  Official Lookbook Standard", fill=ACCENT_COLOR, font=font_mono)

    p5_path = os.path.join(output_dir, "slide_5_outro_cta.png")
    s5.save(p5_path, "PNG", quality=95)
    slides.append(p5_path)

    return slides


# ==============================================================================
# ARCHETYPE 3 (DAY 3): AVANT-GARDE NOCTURNE / DARK CONTEMPORARY
# ==============================================================================
def _render_archetype_3(
    theme_title: str,
    headline: str,
    subtitle: str,
    p1: dict,
    p2: dict,
    p3: dict,
    p1_angles: dict,
    p2_angles: dict,
    p3_angles: dict,
    output_dir: str
) -> list[str]:
    """
    Day 3 Style: Midnight slate background, pure white crisp typography, vivid crimson accents,
    dramatic spotlighting, dynamic offset diagonal collage. High-contrast evening look.
    """
    BG_COLOR = (16, 18, 22)          # Midnight Slate
    CARD_BG = (26, 30, 38)           # Dark Slate Panel
    TEXT_LIGHT = (250, 250, 252)     # Crisp Pure White
    TEXT_MUTED = (148, 163, 184)     # Silver Slate
    ACCENT_COLOR = (225, 29, 72)     # Neon Crimson
    BORDER_HAIRLINE = (45, 52, 64)   # Subtle Dark Border

    try:
        font_display_xl = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 54)
        font_display_lg = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 38)
        font_sans_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
        font_sans_med = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
        font_sans_sm = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    except Exception:
        font_display_xl = ImageFont.load_default()
        font_display_lg = font_display_xl
        font_sans_bold = font_display_xl
        font_sans_med = font_display_xl
        font_sans_sm = font_display_xl

    slides = []

    p1_name = p1.get("name", "Statement Jacket").upper()
    p2_name = p2.get("name", "Contrast Bottom").upper()
    p3_name = p3.get("name", "Night Accessory").upper()

    # SLIDE 1: DRAMATIC SPOTLIGHT COVER
    s1 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)

    # Left Neon Crimson Bar
    d1.rectangle([70, 50, 78, 140], fill=ACCENT_COLOR)
    d1.text((95, 50), "COLORBOX // NOCTURNE DROP", fill=TEXT_LIGHT, font=font_sans_bold)
    d1.text((95, 85), (headline or p1_name[:28]).upper(), fill=TEXT_LIGHT, font=font_display_xl)

    # Spotlight Main Frame
    d1.rectangle([70, 170, 1010, 1180], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        im1 = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s1, im1, 90, 190, 900, 970)

    # Bottom Crimson Tag
    d1.rectangle([70, 1210, 1010, 1290], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    d1.text((100, 1235), "STATEMENT COLLECTION  •  AFTER-HOURS EDITION", fill=ACCENT_COLOR, font=font_sans_bold)
    draw_color_palette(d1, 800, 1250, get_swatches_for_product(p1, 4))

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    slides.append(p1_path)

    # SLIDE 2: HARDWARE & SHEEN TEXTURE FOCUS (Detail Angle)
    s2 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d2 = ImageDraw.Draw(s2)

    d2.text((70, 50), "COLORBOX // TEXTURE & HARDWARE", fill=ACCENT_COLOR, font=font_sans_bold)
    d2.text((70, 90), "FINISH & DETAIL SPECIFICATION", fill=TEXT_LIGHT, font=font_display_lg)

    # Dark Visual Frame
    d2.rectangle([70, 160, 1010, 1010], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    detail_img = p1_angles.get("detail") or p1_angles.get("front")
    if detail_img:
        im2 = Image.open(detail_img).convert("RGB")
        paste_proportional(s2, im2, 90, 180, 900, 810)

    # Bottom Spec Panel
    d2.rectangle([70, 1040, 1010, 1270], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    d2.text((100, 1070), f"{p1_name} ({p1.get('color', 'DARK')})", fill=TEXT_LIGHT, font=font_sans_bold)
    d2.text((100, 1115), "Sentuhan material premium dengan kilau terkontrol dan ritsleting presisi.", fill=TEXT_MUTED, font=font_sans_med)
    d2.text((100, 1165), f"Sizes: {p1.get('sizes', 'S - XL')}  •  Bold silhouette with high-impact presence.", fill=ACCENT_COLOR, font=font_sans_med)

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    slides.append(p2_path)

    # SLIDE 3: NOCTURNE LOWER CONTRAST (Bottom Front Angle)
    s3 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)

    d3.text((70, 50), "COLORBOX // LOWER CONTRAST", fill=ACCENT_COLOR, font=font_sans_bold)
    d3.text((70, 90), p2_name[:34], fill=TEXT_LIGHT, font=font_display_lg)

    d3.rectangle([70, 160, 1010, 1150], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    bot_img = p2_angles.get("front") or p2_angles.get("detail")
    if bot_img:
        im3 = Image.open(bot_img).convert("RGB")
        paste_proportional(s3, im3, 90, 180, 900, 950)

    d3.text((90, 1210), f"Colorway: {p2.get('color', 'Midnight')}  •  Bawahan penyeimbang dengan siluet tegas.", fill=TEXT_MUTED, font=font_sans_med)

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    slides.append(p3_path)

    # SLIDE 4: DYNAMIC OFFSET DUO (Hero Back/Side + Bottom + Accessory)
    s4 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d4 = ImageDraw.Draw(s4)

    d4.text((70, 50), "COLORBOX // NIGHT FORMULA", fill=ACCENT_COLOR, font=font_sans_bold)
    d4.text((70, 90), "COMPLETE NOCTURNE OUTFIT", fill=TEXT_LIGHT, font=font_display_lg)

    # Left tall frame: Hero profile
    d4.rectangle([70, 160, 540, 1180], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    back_img = p1_angles.get("back") or p1_angles.get("side") or p1_angles.get("front")
    if back_img:
        imb = Image.open(back_img).convert("RGB")
        paste_proportional(s4, imb, 85, 175, 440, 950)
    d4.text((90, 1140), f"{p1_name[:18]} (Profile)", fill=TEXT_MUTED, font=font_sans_sm)

    # Right top frame: Bottom
    d4.rectangle([565, 160, 1010, 650], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if bot_img:
        imbt = Image.open(bot_img).convert("RGB")
        paste_proportional(s4, imbt, 580, 175, 415, 430)
    d4.text((585, 615), f"{p2_name[:18]}", fill=TEXT_MUTED, font=font_sans_sm)

    # Right bottom frame: Accessory
    d4.rectangle([565, 680, 1010, 1180], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    acc_img = p3_angles.get("front") or p3_angles.get("side") or p2_angles.get("front")
    if acc_img:
        ima = Image.open(acc_img).convert("RGB")
        paste_proportional(s4, ima, 580, 695, 415, 430)
    d4.text((585, 1140), f"{p3_name[:18]}", fill=TEXT_MUTED, font=font_sans_sm)

    d4.text((70, 1230), "#NeverJustOneThing  •  Night Out Curated Ensemble", fill=ACCENT_COLOR, font=font_sans_bold)

    p4_path = os.path.join(output_dir, "slide_4_accessories_layering.png")
    s4.save(p4_path, "PNG", quality=95)
    s4.save(os.path.join(output_dir, "slide_4_accessories_flatlay.png"), "PNG", quality=95)
    slides.append(p4_path)

    # SLIDE 5: NOCTURNE OUTRO
    s5 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d5 = ImageDraw.Draw(s5)

    d5.text((70, 50), "COLORBOX", fill=TEXT_LIGHT, font=font_sans_bold)
    d5.text((250, 52), "|   NOCTURNE EDITION", fill=ACCENT_COLOR, font=font_sans_med)

    d5.text((70, 110), "STANDOUT AFTER DARK", fill=TEXT_LIGHT, font=font_display_xl)

    d5.rectangle([70, 180, 1010, 1120], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        imf = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s5, imf, 90, 200, 900, 900)

    d5.text((70, 1160), "#NeverJustOneThing", fill=ACCENT_COLOR, font=font_display_lg)
    d5.text((70, 1220), "Belanja koleksi lengkap di colorbox.co.id & seluruh store Colorbox.", fill=TEXT_MUTED, font=font_sans_med)

    p5_path = os.path.join(output_dir, "slide_5_outro_cta.png")
    s5.save(p5_path, "PNG", quality=95)
    slides.append(p5_path)

    return slides


# ==============================================================================
# MAIN EXPORTED ENTRY POINT
# ==============================================================================
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
    1. ZERO rigid templates: Dynamically switches layout archetype by day/mood:
       - Day 1: Haute-Minimalist Atelier (Georgia serif, ivory paper, asymmetric collage)
       - Day 2: Modernist Bauhaus / Swiss Grid (Sans display, architectural grey, tri-modular columns)
       - Day 3: Avant-Garde Nocturne (Dark mode midnight slate, neon crimson, dramatic spotlighting)
    2. Category-Aware Mix & Match: Top piece pairs with Bottom, Bottom pairs with Top, plus Accessory.
    3. Multi-Angle Image Routing:
       - Slide 1: Hero Front
       - Slide 2: Hero Detail (craftsmanship, texture, lapel, weave)
       - Slide 3: Complementary Bottom Front (silhouette foundation)
       - Slide 4: Complete Trio Ensemble (Hero Back/Profile + Bottom + Accessory)
       - Slide 5: Lookbook Outro & Palette
    4. ZERO noise: No 'SLIDE 1/5', no 'SWIPE', no wireframe labels.
    5. Aspect Ratio strictly locked with Lanczos high-fidelity scaling.
    """
    os.makedirs(output_dir, exist_ok=True)

    p1 = products_info[0] if len(products_info) > 0 else {}
    p2 = products_info[1] if len(products_info) > 1 else {}
    p3 = products_info[2] if len(products_info) > 2 else {}

    p1_angles = resolve_product_angles(p1, images_dir)
    p2_angles = resolve_product_angles(p2, images_dir)
    p3_angles = resolve_product_angles(p3, images_dir)

    # Route to distinct Archetype
    if day_num == 2:
        generated_slides = _render_archetype_2(
            theme_title=theme_title,
            headline=headline,
            subtitle=subtitle,
            p1=p1,
            p2=p2,
            p3=p3,
            p1_angles=p1_angles,
            p2_angles=p2_angles,
            p3_angles=p3_angles,
            output_dir=output_dir
        )
    elif day_num == 3:
        generated_slides = _render_archetype_3(
            theme_title=theme_title,
            headline=headline,
            subtitle=subtitle,
            p1=p1,
            p2=p2,
            p3=p3,
            p1_angles=p1_angles,
            p2_angles=p2_angles,
            p3_angles=p3_angles,
            output_dir=output_dir
        )
    else:
        generated_slides = _render_archetype_1(
            theme_title=theme_title,
            headline=headline,
            subtitle=subtitle,
            p1=p1,
            p2=p2,
            p3=p3,
            p1_angles=p1_angles,
            p2_angles=p2_angles,
            p3_angles=p3_angles,
            output_dir=output_dir
        )

    # Interactive HTML Preview
    generate_carousel_preview_html(output_dir, headline or theme_title, subtitle or "Colorbox Campaign", day_num)

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
  <title>Colorbox Bespoke Lookbook — Day {day_num}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0d0f14;
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
    .badge {{ display: inline-block; padding: 4px 14px; background: rgba(244,63,94,0.15); border: 1px solid #f43f5e; border-radius: 20px; font-size: 12px; font-weight: 600; color: #f43f5e; margin-bottom: 10px; }}
    .carousel-container {{
      position: relative;
      width: 100%;
      max-width: 440px;
      aspect-ratio: 4/5;
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.7);
      background: #14171f;
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
    <span class="badge">DAY {day_num} BESPOKE EDITORIAL LOOKBOOK</span>
    <h1>{title}</h1>
    <p>{subtitle} • 1080 × 1350 px (4:5 Feed Portrait)</p>
  </div>
  <div class="carousel-container">
    <div class="slides-wrapper">
      <div class="slide-item"><img src="slide_1_cover_hero.png" alt="Slide 1 - Cover Hero"></div>
      <div class="slide-item"><img src="slide_2_hero_top.png" alt="Slide 2 - Craftsmanship & Detail"></div>
      <div class="slide-item"><img src="slide_3_bottom_pairing.png" alt="Slide 3 - Silhouette Pairing"></div>
      <div class="slide-item"><img src="slide_4_accessories_layering.png" alt="Slide 4 - Complete Ensemble"></div>
      <div class="slide-item"><img src="slide_5_outro_cta.png" alt="Slide 5 - Lookbook Outro"></div>
    </div>
  </div>
  <div class="nav-hints">
    <span>👈 Geser / Swipe horizontal 👉</span>
    <span>5 Slides Ready-to-Post</span>
  </div>
</body>
</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_path
