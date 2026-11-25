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

# ==============================================================================
# STRICT SAFETY BOUNDARIES (1080 x 1350 px Feed Portrait Standard)
# Zero offside, zero clipping, zero overflow guaranteed
# ==============================================================================
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350
SAFE_LEFT = 70
SAFE_RIGHT = 1010
SAFE_WIDTH = SAFE_RIGHT - SAFE_LEFT  # Exactly 940 px
SAFE_TOP = 50
SAFE_BOTTOM = 1300

FONT_SERIF_BOLD = "C:/Windows/Fonts/georgiab.ttf"
FONT_SERIF_REG = "C:/Windows/Fonts/georgia.ttf"
FONT_SANS_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SANS_REG = "C:/Windows/Fonts/segoeui.ttf"
FONT_DISPLAY_BOLD = "C:/Windows/Fonts/arialbd.ttf"

def get_text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    """Returns (width, height) of text using textbbox."""
    if not text:
        return (0, 0)
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int, max_lines: int = None) -> list[str]:
    """
    Wraps text cleanly into multiple lines so that no line exceeds max_w.
    If max_lines is set, safely clips the last line with '...'.
    """
    words = text.split()
    if not words:
        return []
    lines = []
    cur_line = []
    for w in words:
        test_line = " ".join(cur_line + [w])
        w_px, _ = get_text_size(draw, test_line, font)
        if w_px <= max_w:
            cur_line.append(w)
        else:
            if cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                lines.append(w)
                cur_line = []
    if cur_line:
        lines.append(" ".join(cur_line))

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last_line = lines[-1]
        while len(last_line) > 3:
            w_px, _ = get_text_size(draw, last_line + "...", font)
            if w_px <= max_w:
                lines[-1] = last_line + "..."
                break
            last_line = last_line[:-1]
    return lines

def draw_safe_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_w: int,
    font_path: str,
    font_size: int,
    fill: tuple,
    line_spacing: int = 6,
    max_lines: int = 2,
    auto_shrink: bool = True,
    min_size: int = 14
) -> int:
    """
    Renders text safely within [x, y, x + max_w].
    - Clamps max_w to prevent exceeding SAFE_RIGHT (1010).
    - Wraps text across lines up to max_lines.
    - If text still overflows, decrements font size until it fits.
    - Returns the bottom Y coordinate of the rendered block.
    """
    if not text:
        return y

    # Clamp max_w so x + max_w never exceeds SAFE_RIGHT
    if x + max_w > SAFE_RIGHT:
        max_w = SAFE_RIGHT - x

    cur_size = font_size
    while cur_size >= min_size:
        try:
            f = ImageFont.truetype(font_path, cur_size)
        except Exception:
            f = ImageFont.load_default()
            draw.text((x, y), text, fill=fill, font=f)
            return y + 20

        lines = wrap_text(draw, text, f, max_w, max_lines=max_lines)
        if len(lines) <= max_lines and all(get_text_size(draw, l, f)[0] <= max_w for l in lines):
            cur_y = y
            for l in lines:
                draw.text((x, cur_y), l, fill=fill, font=f)
                _, lh = get_text_size(draw, l, f)
                cur_y += lh + line_spacing
            return cur_y

        if not auto_shrink:
            break
        cur_size -= 2

    # Fallback with min_size and clean truncation
    try:
        f = ImageFont.truetype(font_path, min_size)
    except Exception:
        f = ImageFont.load_default()
    lines = wrap_text(draw, text, f, max_w, max_lines=max_lines)
    cur_y = y
    for l in lines:
        draw.text((x, cur_y), l, fill=fill, font=f)
        _, lh = get_text_size(draw, l, f)
        cur_y += lh + line_spacing
    return cur_y

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
    Guarantees placement strictly stays within canvas bounds without stretching.
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

def draw_color_palette(draw: ImageDraw.ImageDraw, start_x: int, start_y: int, colors: list[tuple[int, int, int]], radius: int = 14, spacing: int = 36):
    for idx, rgb in enumerate(colors):
        cx = start_x + (idx * spacing)
        if cx + radius > SAFE_RIGHT:
            break
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
                
    main_file = prod.get("image_file", "")
    if main_file:
        fp = os.path.join(images_dir, main_file)
        if os.path.exists(fp):
            if "front" not in angles:
                angles["front"] = fp

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
    haute lookbook layout with 100% guarded text boundaries.
    """
    BG_COLOR = (247, 245, 240)       # Warm Studio Ecru
    CARD_BG = (255, 255, 255)        # Pure White
    TEXT_DARK = (24, 24, 28)         # Charcoal Black
    TEXT_MUTED = (120, 115, 110)     # Muted Taupe
    ACCENT_COLOR = (225, 83, 66)     # Colorbox Coral
    BORDER_HAIRLINE = (228, 224, 216)

    slides = []

    p1_name = p1.get("name", "Tailored Piece").upper()
    p2_name = p2.get("name", "Complementary Bottom").upper()
    p3_name = p3.get("name", "Accessory Accent").upper()

    # --------------------------------------------------------------------------
    # SLIDE 1: BESPOKE HERO COVER
    # --------------------------------------------------------------------------
    s1 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)
    
    # Header row
    draw_safe_text(d1, "COLORBOX", SAFE_LEFT, 50, 160, FONT_SANS_BOLD, 26, TEXT_DARK, max_lines=1)
    tag_title = f"|  {theme_title.upper()[:35]}" if theme_title else "|  COLLECTION EDITORIAL"
    draw_safe_text(d1, tag_title, 240, 52, 540, FONT_SANS_REG, 22, TEXT_MUTED, max_lines=1)
    draw_safe_text(d1, "OFFICIAL", 820, 52, 190, FONT_SANS_REG, 18, ACCENT_COLOR, max_lines=1)

    # Headline (Auto-fitting & wrapping)
    hl_text = (headline or p1_name).upper()
    y_hl = draw_safe_text(d1, hl_text, SAFE_LEFT, 100, SAFE_WIDTH, FONT_SERIF_BOLD, 46, TEXT_DARK, line_spacing=4, max_lines=2, min_size=28)

    # Concept Quote
    concept_str = (theme_title or "Sartorial Precision & Balance").title()
    draw_safe_text(d1, f'"{concept_str}"', SAFE_LEFT, y_hl + 4, SAFE_WIDTH, FONT_SERIF_REG, 22, TEXT_MUTED, max_lines=1, min_size=16)

    # Hero Photo (Full portrait frame)
    d1.rounded_rectangle([SAFE_LEFT, 230, SAFE_RIGHT, 1220], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        im1 = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s1, im1, SAFE_LEFT + 20, 245, SAFE_WIDTH - 40, 955)

    # Palette bar at bottom
    d1.rounded_rectangle([SAFE_LEFT + 20, 1245, SAFE_RIGHT - 20, 1305], radius=10, fill=CARD_BG)
    draw_safe_text(d1, "CURATED PALETTE", SAFE_LEFT + 40, 1262, 300, FONT_SANS_REG, 18, TEXT_MUTED, max_lines=1)
    draw_color_palette(d1, 680, 1275, get_swatches_for_product(p1, 5))

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    slides.append(p1_path)

    # --------------------------------------------------------------------------
    # SLIDE 2: CRAFTSMANSHIP & TEXTURE (Detail Angle)
    # --------------------------------------------------------------------------
    s2 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=CARD_BG)
    d2 = ImageDraw.Draw(s2)

    draw_safe_text(d2, "COLORBOX", SAFE_LEFT, 50, 160, FONT_SANS_BOLD, 26, TEXT_DARK, max_lines=1)
    draw_safe_text(d2, "|  CRAFTSMANSHIP & TEXTURE", 240, 52, 700, FONT_SANS_REG, 22, TEXT_MUTED, max_lines=1)
    
    draw_safe_text(d2, "MATERIAL WEAVE & DETAIL", SAFE_LEFT, 105, SAFE_WIDTH, FONT_SERIF_BOLD, 36, TEXT_DARK, max_lines=1)
    draw_safe_text(d2, f"Fokus pada presisi jahitan dan tekstur kain {p1.get('color', '')}", SAFE_LEFT, 155, SAFE_WIDTH, FONT_SANS_REG, 22, TEXT_MUTED, max_lines=1)

    # Large Detail Photo Frame
    d2.rounded_rectangle([SAFE_LEFT, 210, SAFE_RIGHT, 1010], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    detail_img = p1_angles.get("detail") or p1_angles.get("front")
    if detail_img:
        im2 = Image.open(detail_img).convert("RGB")
        paste_proportional(s2, im2, SAFE_LEFT + 20, 225, SAFE_WIDTH - 40, 765)

    # Technical Spec Bottom Panel (Safe wrapping)
    d2.rounded_rectangle([SAFE_LEFT, 1035, SAFE_RIGHT, 1285], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    draw_safe_text(d2, "TAILORING SPECIFICATION", SAFE_LEFT + 30, 1055, SAFE_WIDTH - 60, FONT_SANS_BOLD, 22, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d2, p1_name, SAFE_LEFT + 30, 1092, SAFE_WIDTH - 60, FONT_SERIF_REG, 26, TEXT_DARK, max_lines=1)
    draw_safe_text(d2, f"Warna Resmi: {p1.get('color', 'Classic')}  •  Pilihan Ukuran: {p1.get('sizes', 'S - XL')}", SAFE_LEFT + 30, 1135, SAFE_WIDTH - 60, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=1)
    draw_safe_text(d2, "Dirancang untuk kenyamanan sepanjang hari dengan potongan presisi khas Colorbox.", SAFE_LEFT + 30, 1175, SAFE_WIDTH - 60, FONT_SANS_REG, 20, TEXT_DARK, max_lines=2)

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    slides.append(p2_path)

    # --------------------------------------------------------------------------
    # SLIDE 3: COMPLEMENTARY PAIRING (Bottom Front Angle)
    # --------------------------------------------------------------------------
    s3 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)

    draw_safe_text(d3, "COLORBOX", SAFE_LEFT, 50, 160, FONT_SANS_BOLD, 26, TEXT_DARK, max_lines=1)
    draw_safe_text(d3, "|  THE PAIRING FORMULA", 240, 52, 700, FONT_SANS_REG, 22, TEXT_MUTED, max_lines=1)

    draw_safe_text(d3, p2_name, SAFE_LEFT, 105, SAFE_WIDTH, FONT_SERIF_BOLD, 36, TEXT_DARK, max_lines=1)
    draw_safe_text(d3, f"Padu-padan ideal bawahan untuk siluet seimbang dan proporsional.", SAFE_LEFT, 155, SAFE_WIDTH, FONT_SANS_REG, 22, ACCENT_COLOR, max_lines=1)

    d3.rounded_rectangle([SAFE_LEFT, 210, SAFE_RIGHT, 1170], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    bot_img = p2_angles.get("front") or p2_angles.get("detail")
    if bot_img:
        im3 = Image.open(bot_img).convert("RGB")
        paste_proportional(s3, im3, SAFE_LEFT + 20, 225, SAFE_WIDTH - 40, 925)

    draw_safe_text(d3, f"Featured Color: {p2.get('color', 'Neutral')}  •  Sizes: {p2.get('sizes', 'All Sizes')}", SAFE_LEFT + 30, 1205, 620, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=1)
    draw_color_palette(d3, 760, 1220, get_swatches_for_product(p2, 4))

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    slides.append(p3_path)

    # --------------------------------------------------------------------------
    # SLIDE 4: ASYMMETRIC ENSEMBLE COLLAGE (Hero Profile + Bottom + Accessory)
    # --------------------------------------------------------------------------
    s4 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=CARD_BG)
    d4 = ImageDraw.Draw(s4)

    draw_safe_text(d4, "COLORBOX", SAFE_LEFT, 50, 160, FONT_SANS_BOLD, 26, TEXT_DARK, max_lines=1)
    draw_safe_text(d4, "|  COMPLETE ENSEMBLE", 240, 52, 700, FONT_SANS_REG, 22, TEXT_MUTED, max_lines=1)
    draw_safe_text(d4, "HARMONI 360 LOOKBOOK", SAFE_LEFT, 105, SAFE_WIDTH, FONT_SERIF_BOLD, 36, TEXT_DARK, max_lines=1)

    # Left tall frame: Hero profile / back angle
    d4.rounded_rectangle([SAFE_LEFT, 160, 535, 1180], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    back_img = p1_angles.get("back") or p1_angles.get("side") or p1_angles.get("front")
    if back_img:
        imb = Image.open(back_img).convert("RGB")
        paste_proportional(s4, imb, SAFE_LEFT + 15, 175, 435, 945)
    draw_safe_text(d4, f"{p1_name} (Profile)", SAFE_LEFT + 20, 1135, 425, FONT_SANS_REG, 18, TEXT_DARK, max_lines=1)

    # Right top frame: Complementary bottom
    d4.rounded_rectangle([555, 160, SAFE_RIGHT, 650], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    if bot_img:
        imbt = Image.open(bot_img).convert("RGB")
        paste_proportional(s4, imbt, 570, 175, 425, 425)
    draw_safe_text(d4, p2_name, 570, 615, 425, FONT_SANS_REG, 18, TEXT_DARK, max_lines=1)

    # Right bottom frame: Accessory or Footwear
    d4.rounded_rectangle([555, 675, SAFE_RIGHT, 1180], radius=14, fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    acc_img = p3_angles.get("front") or p3_angles.get("side") or p2_angles.get("front")
    if acc_img:
        ima = Image.open(acc_img).convert("RGB")
        paste_proportional(s4, ima, 570, 690, 425, 435)
    draw_safe_text(d4, p3_name, 570, 1135, 425, FONT_SANS_REG, 18, TEXT_DARK, max_lines=1)

    draw_safe_text(d4, "#NeverJustOneThing  •  Authentic Wardrobe Formula", SAFE_LEFT, 1230, SAFE_WIDTH, FONT_SANS_BOLD, 22, ACCENT_COLOR, max_lines=1)

    p4_path = os.path.join(output_dir, "slide_4_accessories_layering.png")
    s4.save(p4_path, "PNG", quality=95)
    s4.save(os.path.join(output_dir, "slide_4_accessories_flatlay.png"), "PNG", quality=95)
    slides.append(p4_path)

    # --------------------------------------------------------------------------
    # SLIDE 5: EDITORIAL LOOKBOOK OUTRO
    # --------------------------------------------------------------------------
    s5 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d5 = ImageDraw.Draw(s5)

    draw_safe_text(d5, "COLORBOX", SAFE_LEFT, 50, 160, FONT_SANS_BOLD, 26, TEXT_DARK, max_lines=1)
    draw_safe_text(d5, "|  LOOKBOOK SIGN-OFF", 240, 52, 700, FONT_SANS_REG, 22, TEXT_MUTED, max_lines=1)

    draw_safe_text(d5, "STYLING INSPIRATION", SAFE_LEFT, 105, SAFE_WIDTH, FONT_SERIF_BOLD, 42, TEXT_DARK, max_lines=1)
    draw_safe_text(d5, "Paduan gaya kurasi resmi tim Colorbox Indonesia.", SAFE_LEFT, 160, SAFE_WIDTH, FONT_SERIF_REG, 22, TEXT_MUTED, max_lines=1)

    d5.rounded_rectangle([SAFE_LEFT, 215, SAFE_RIGHT, 1180], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        imf = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s5, imf, SAFE_LEFT + 20, 235, SAFE_WIDTH - 40, 925)

    draw_safe_text(d5, "#NeverJustOneThing", SAFE_LEFT + 20, 1215, SAFE_WIDTH - 40, FONT_SERIF_BOLD, 32, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d5, "Dapatkan di colorbox.co.id & gerai resmi Colorbox seluruh Indonesia", SAFE_LEFT + 20, 1260, SAFE_WIDTH - 40, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=1)

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
    strict Swiss grid lines, tri-modular columns with 100% safe margins.
    """
    BG_COLOR = (238, 240, 242)       # Architectural Concrete Grey
    CARD_BG = (255, 255, 255)        # Pure White
    CONTRAST_BAND = (22, 26, 30)     # Ink Black
    TEXT_DARK = (20, 24, 28)         # Deep Ink
    TEXT_MUTED = (110, 116, 122)     # Studio Slate
    ACCENT_COLOR = (95, 120, 88)     # Sage Green
    BORDER_HAIRLINE = (215, 220, 224)

    slides = []

    p1_name = p1.get("name", "Contemporary Essential").upper()
    p2_name = p2.get("name", "Lower Foundation").upper()
    p3_name = p3.get("name", "Accent Footwear").upper()

    # --------------------------------------------------------------------------
    # SLIDE 1: ARCHITECTURAL BANNER & PEDESTAL COVER
    # --------------------------------------------------------------------------
    s1 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)

    # Top Contrast Band
    d1.rectangle([0, 0, CANVAS_WIDTH, 140], fill=CONTRAST_BAND)
    tag_title = f"COLORBOX // {theme_title.upper()[:35]}" if theme_title else "COLORBOX // COLLECTION EDITORIAL"
    draw_safe_text(d1, tag_title, SAFE_LEFT, 45, 750, FONT_DISPLAY_BOLD, 22, (255, 255, 255), max_lines=1)
    draw_safe_text(d1, "CURATED", 870, 45, 140, FONT_DISPLAY_BOLD, 22, ACCENT_COLOR, max_lines=1)

    # Main Visual Pedestal Frame
    d1.rectangle([SAFE_LEFT, 170, SAFE_RIGHT, 1080], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        im1 = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s1, im1, SAFE_LEFT + 20, 190, SAFE_WIDTH - 40, 870)

    # Bottom Information Strip
    d1.rectangle([SAFE_LEFT, 1110, SAFE_RIGHT, 1285], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    d1.rectangle([SAFE_LEFT, 1110, SAFE_LEFT + 12, 1285], fill=ACCENT_COLOR) # Left accent strip

    hl_text = (headline or p1_name).upper()
    draw_safe_text(d1, hl_text, SAFE_LEFT + 30, 1125, SAFE_WIDTH - 50, FONT_SANS_BOLD, 30, TEXT_DARK, max_lines=1, min_size=20)
    draw_safe_text(d1, f"PALETTE: {p1.get('color', 'STUDIO')}  |  CUT: CONTEMPORARY RELAXED", SAFE_LEFT + 30, 1175, SAFE_WIDTH - 50, FONT_SANS_REG, 18, TEXT_MUTED, max_lines=1)
    draw_safe_text(d1, "Konstruksi modular yang adaptif untuk rotasi gaya harian.", SAFE_LEFT + 30, 1215, SAFE_WIDTH - 50, FONT_SANS_REG, 20, ACCENT_COLOR, max_lines=1)

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    slides.append(p1_path)

    # --------------------------------------------------------------------------
    # SLIDE 2: NUMBERED SPECIFICATION (Left 40% Spec + Right 60% Detail Angle)
    # --------------------------------------------------------------------------
    s2 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d2 = ImageDraw.Draw(s2)

    draw_safe_text(d2, "COLORBOX // TECHNICAL BREAKDOWN", SAFE_LEFT, 45, SAFE_WIDTH, FONT_DISPLAY_BOLD, 20, TEXT_DARK, max_lines=1)
    draw_safe_text(d2, "ANATOMI POTONGAN & STRUKTUR", SAFE_LEFT, 85, SAFE_WIDTH, FONT_SANS_BOLD, 34, TEXT_DARK, max_lines=1)

    # Left Spec Column (Width 360 px)
    spec_col_w = 360
    d2.rectangle([SAFE_LEFT, 150, SAFE_LEFT + spec_col_w, 1250], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    
    draw_safe_text(d2, "[01] SILUET", SAFE_LEFT + 25, 180, spec_col_w - 50, FONT_DISPLAY_BOLD, 20, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d2, "Relaxed fit dengan garis bahu natural.", SAFE_LEFT + 25, 215, spec_col_w - 50, FONT_SANS_REG, 20, TEXT_DARK, max_lines=2)

    draw_safe_text(d2, "[02] TEKSTUR", SAFE_LEFT + 25, 330, spec_col_w - 50, FONT_DISPLAY_BOLD, 20, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d2, f"Material {p1.get('color', '')} berdensitas sejuk.", SAFE_LEFT + 25, 365, spec_col_w - 50, FONT_SANS_REG, 20, TEXT_DARK, max_lines=2)

    draw_safe_text(d2, "[03] SIZE MATRIX", SAFE_LEFT + 25, 480, spec_col_w - 50, FONT_DISPLAY_BOLD, 20, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d2, str(p1.get('sizes', 'S, M, L, XL')), SAFE_LEFT + 25, 515, spec_col_w - 50, FONT_SANS_REG, 20, TEXT_DARK, max_lines=2)

    draw_safe_text(d2, "[04] COLORWAYS", SAFE_LEFT + 25, 620, spec_col_w - 50, FONT_DISPLAY_BOLD, 20, ACCENT_COLOR, max_lines=1)
    draw_color_palette(d2, SAFE_LEFT + 55, 680, get_swatches_for_product(p1, 4), radius=12, spacing=30)

    # Right Large Photo: Detail or Back Angle
    right_x = SAFE_LEFT + spec_col_w + 20
    right_w = SAFE_RIGHT - right_x
    d2.rectangle([right_x, 150, SAFE_RIGHT, 1250], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    detail_img = p1_angles.get("detail") or p1_angles.get("back") or p1_angles.get("front")
    if detail_img:
        im2 = Image.open(detail_img).convert("RGB")
        paste_proportional(s2, im2, right_x + 15, 170, right_w - 30, 1060)

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    slides.append(p2_path)

    # --------------------------------------------------------------------------
    # SLIDE 3: MODERNIST BOTTOM FOUNDATION
    # --------------------------------------------------------------------------
    s3 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)

    draw_safe_text(d3, "COLORBOX // LOWER FOUNDATION", SAFE_LEFT, 45, SAFE_WIDTH, FONT_DISPLAY_BOLD, 20, TEXT_DARK, max_lines=1)
    draw_safe_text(d3, p2_name, SAFE_LEFT, 85, SAFE_WIDTH, FONT_SANS_BOLD, 34, TEXT_DARK, max_lines=1)

    d3.rectangle([SAFE_LEFT, 150, SAFE_RIGHT, 1020], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    bot_img = p2_angles.get("front") or p2_angles.get("detail")
    if bot_img:
        im3 = Image.open(bot_img).convert("RGB")
        paste_proportional(s3, im3, SAFE_LEFT + 20, 170, SAFE_WIDTH - 40, 830)

    # Lower Technical Card
    d3.rectangle([SAFE_LEFT, 1050, SAFE_RIGHT, 1270], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    draw_safe_text(d3, f"PASANGAN IDEAL: {p2_name}", SAFE_LEFT + 30, 1075, SAFE_WIDTH - 60, FONT_DISPLAY_BOLD, 20, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d3, f"Warna: {p2.get('color', 'Neutral')}  •  Potongan terukur untuk keseimbangan volume atas-bawah.", SAFE_LEFT + 30, 1118, SAFE_WIDTH - 60, FONT_SANS_REG, 20, TEXT_DARK, max_lines=2)
    draw_safe_text(d3, "Menciptakan siluet ramping & fleksibel untuk mobilitas perkotaan.", SAFE_LEFT + 30, 1175, SAFE_WIDTH - 60, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=2)

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    slides.append(p3_path)

    # --------------------------------------------------------------------------
    # SLIDE 4: ARCHITECTURAL TRIPTYCH GRID (Top Back + Bottom + Shoes/Bag)
    # --------------------------------------------------------------------------
    s4 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d4 = ImageDraw.Draw(s4)

    d4.rectangle([0, 0, CANVAS_WIDTH, 110], fill=CONTRAST_BAND)
    draw_safe_text(d4, "TRIPTYCH STYLING SYSTEM // COMPLETE OUTFIT", SAFE_LEFT, 38, SAFE_WIDTH, FONT_DISPLAY_BOLD, 22, (255, 255, 255), max_lines=1)

    col_w = 295
    spacing = 27
    x1 = SAFE_LEFT
    x2 = x1 + col_w + spacing
    x3 = x2 + col_w + spacing

    # Col 1: Top piece
    d4.rectangle([x1, 140, x1 + col_w, 1160], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    back_img = p1_angles.get("back") or p1_angles.get("front")
    if back_img:
        imb = Image.open(back_img).convert("RGB")
        paste_proportional(s4, imb, x1 + 10, 155, col_w - 20, 880)
    draw_safe_text(d4, "[01] ATASAN", x1 + 15, 1070, col_w - 30, FONT_DISPLAY_BOLD, 18, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d4, p1_name, x1 + 15, 1105, col_w - 30, FONT_SANS_REG, 18, TEXT_DARK, max_lines=1)

    # Col 2: Bottom piece
    d4.rectangle([x2, 140, x2 + col_w, 1160], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if bot_img:
        imbt = Image.open(bot_img).convert("RGB")
        paste_proportional(s4, imbt, x2 + 10, 155, col_w - 20, 880)
    draw_safe_text(d4, "[02] BAWAHAN", x2 + 15, 1070, col_w - 30, FONT_DISPLAY_BOLD, 18, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d4, p2_name, x2 + 15, 1105, col_w - 30, FONT_SANS_REG, 18, TEXT_DARK, max_lines=1)

    # Col 3: Accessory or Footwear
    d4.rectangle([x3, 140, x3 + col_w, 1160], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    acc_img = p3_angles.get("front") or p3_angles.get("side") or p2_angles.get("front")
    if acc_img:
        ima = Image.open(acc_img).convert("RGB")
        paste_proportional(s4, ima, x3 + 10, 155, col_w - 20, 880)
    draw_safe_text(d4, "[03] AKSESORI", x3 + 15, 1070, col_w - 30, FONT_DISPLAY_BOLD, 18, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d4, p3_name, x3 + 15, 1105, col_w - 30, FONT_SANS_REG, 18, TEXT_DARK, max_lines=1)

    draw_safe_text(d4, "MODULAR HARMONY • FORM FOLLOWS FUNCTION", SAFE_LEFT, 1220, SAFE_WIDTH, FONT_DISPLAY_BOLD, 20, TEXT_MUTED, max_lines=1)

    p4_path = os.path.join(output_dir, "slide_4_accessories_layering.png")
    s4.save(p4_path, "PNG", quality=95)
    s4.save(os.path.join(output_dir, "slide_4_accessories_flatlay.png"), "PNG", quality=95)
    slides.append(p4_path)

    # --------------------------------------------------------------------------
    # SLIDE 5: MODERNIST INDEX OUTRO
    # --------------------------------------------------------------------------
    s5 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=CARD_BG)
    d5 = ImageDraw.Draw(s5)

    d5.rectangle([0, 0, CANVAS_WIDTH, 140], fill=CONTRAST_BAND)
    draw_safe_text(d5, "COLORBOX // COLLECTION INDEX", SAFE_LEFT, 45, 750, FONT_DISPLAY_BOLD, 22, (255, 255, 255), max_lines=1)
    draw_safe_text(d5, "AUTUMN DROP", 850, 45, 160, FONT_DISPLAY_BOLD, 22, ACCENT_COLOR, max_lines=1)

    d5.rectangle([SAFE_LEFT, 170, SAFE_RIGHT, 1080], fill=BG_COLOR, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        imf = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s5, imf, SAFE_LEFT + 20, 190, SAFE_WIDTH - 40, 870)

    draw_safe_text(d5, "DIRANCANG UNTUK GAYA HIDUP PERKOTAAN", SAFE_LEFT, 1120, SAFE_WIDTH, FONT_SANS_BOLD, 32, TEXT_DARK, max_lines=1)
    draw_safe_text(d5, "Dapatkan seluruh kurasi di colorbox.co.id & gerai Colorbox terdekat.", SAFE_LEFT, 1175, SAFE_WIDTH, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=1)
    draw_safe_text(d5, "#NeverJustOneThing  •  Official Lookbook Standard", SAFE_LEFT, 1225, SAFE_WIDTH, FONT_DISPLAY_BOLD, 20, ACCENT_COLOR, max_lines=1)

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
    dramatic spotlighting, dynamic offset diagonal collage with strict safety boundaries.
    """
    BG_COLOR = (16, 18, 22)          # Midnight Slate
    CARD_BG = (26, 30, 38)           # Dark Slate Panel
    TEXT_LIGHT = (250, 250, 252)     # Crisp Pure White
    TEXT_MUTED = (148, 163, 184)     # Silver Slate
    ACCENT_COLOR = (225, 29, 72)     # Neon Crimson
    BORDER_HAIRLINE = (45, 52, 64)   # Subtle Dark Border

    slides = []

    p1_name = p1.get("name", "Statement Jacket").upper()
    p2_name = p2.get("name", "Contrast Bottom").upper()
    p3_name = p3.get("name", "Night Accessory").upper()

    # --------------------------------------------------------------------------
    # SLIDE 1: DRAMATIC SPOTLIGHT COVER
    # --------------------------------------------------------------------------
    s1 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)

    # Left Accent Bar
    d1.rectangle([SAFE_LEFT, 45, SAFE_LEFT + 8, 140], fill=ACCENT_COLOR)
    tag_title = f"COLORBOX // {theme_title.upper()[:35]}" if theme_title else "COLORBOX // COLLECTION DROP"
    draw_safe_text(d1, tag_title, SAFE_LEFT + 25, 45, SAFE_WIDTH - 30, FONT_SANS_BOLD, 22, TEXT_LIGHT, max_lines=1)
    
    hl_text = (headline or p1_name).upper()
    draw_safe_text(d1, hl_text, SAFE_LEFT + 25, 80, SAFE_WIDTH - 30, FONT_SANS_BOLD, 44, TEXT_LIGHT, max_lines=2, min_size=26)

    # Spotlight Main Frame
    d1.rectangle([SAFE_LEFT, 170, SAFE_RIGHT, 1180], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        im1 = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s1, im1, SAFE_LEFT + 20, 190, SAFE_WIDTH - 40, 970)

    # Bottom Crimson Tag
    d1.rectangle([SAFE_LEFT, 1210, SAFE_RIGHT, 1290], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    draw_safe_text(d1, "STATEMENT COLLECTION  •  AFTER-HOURS EDITION", SAFE_LEFT + 30, 1235, 680, FONT_SANS_BOLD, 20, ACCENT_COLOR, max_lines=1)
    draw_color_palette(d1, 780, 1250, get_swatches_for_product(p1, 4))

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    slides.append(p1_path)

    # --------------------------------------------------------------------------
    # SLIDE 2: HARDWARE & SHEEN TEXTURE FOCUS (Detail Angle)
    # --------------------------------------------------------------------------
    s2 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d2 = ImageDraw.Draw(s2)

    draw_safe_text(d2, "COLORBOX // TEXTURE & HARDWARE", SAFE_LEFT, 50, SAFE_WIDTH, FONT_SANS_BOLD, 24, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d2, "FINISH & DETAIL SPECIFICATION", SAFE_LEFT, 90, SAFE_WIDTH, FONT_SANS_BOLD, 36, TEXT_LIGHT, max_lines=1)

    # Dark Visual Frame
    d2.rectangle([SAFE_LEFT, 160, SAFE_RIGHT, 1010], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    detail_img = p1_angles.get("detail") or p1_angles.get("front")
    if detail_img:
        im2 = Image.open(detail_img).convert("RGB")
        paste_proportional(s2, im2, SAFE_LEFT + 20, 180, SAFE_WIDTH - 40, 810)

    # Bottom Spec Panel
    d2.rectangle([SAFE_LEFT, 1040, SAFE_RIGHT, 1270], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    draw_safe_text(d2, f"{p1_name} ({p1.get('color', 'DARK')})", SAFE_LEFT + 30, 1065, SAFE_WIDTH - 60, FONT_SANS_BOLD, 24, TEXT_LIGHT, max_lines=1)
    draw_safe_text(d2, "Sentuhan material premium dengan kilau terkontrol dan ritsleting presisi.", SAFE_LEFT + 30, 1110, SAFE_WIDTH - 60, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=2)
    draw_safe_text(d2, f"Sizes: {p1.get('sizes', 'S - XL')}  •  Bold silhouette with high-impact presence.", SAFE_LEFT + 30, 1165, SAFE_WIDTH - 60, FONT_SANS_REG, 20, ACCENT_COLOR, max_lines=2)

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    slides.append(p2_path)

    # --------------------------------------------------------------------------
    # SLIDE 3: NOCTURNE LOWER CONTRAST (Bottom Front Angle)
    # --------------------------------------------------------------------------
    s3 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)

    draw_safe_text(d3, "COLORBOX // LOWER CONTRAST", SAFE_LEFT, 50, SAFE_WIDTH, FONT_SANS_BOLD, 24, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d3, p2_name, SAFE_LEFT, 90, SAFE_WIDTH, FONT_SANS_BOLD, 36, TEXT_LIGHT, max_lines=1)

    d3.rectangle([SAFE_LEFT, 160, SAFE_RIGHT, 1150], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    bot_img = p2_angles.get("front") or p2_angles.get("detail")
    if bot_img:
        im3 = Image.open(bot_img).convert("RGB")
        paste_proportional(s3, im3, SAFE_LEFT + 20, 180, SAFE_WIDTH - 40, 950)

    draw_safe_text(d3, f"Colorway: {p2.get('color', 'Midnight')}  •  Bawahan penyeimbang dengan siluet tegas.", SAFE_LEFT + 20, 1205, SAFE_WIDTH - 40, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=1)

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    slides.append(p3_path)

    # --------------------------------------------------------------------------
    # SLIDE 4: DYNAMIC OFFSET DUO (Hero Profile + Bottom + Accessory)
    # --------------------------------------------------------------------------
    s4 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d4 = ImageDraw.Draw(s4)

    draw_safe_text(d4, "COLORBOX // OUTFIT FORMULA", SAFE_LEFT, 50, SAFE_WIDTH, FONT_SANS_BOLD, 24, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d4, "COMPLETE CURATED ENSEMBLE", SAFE_LEFT, 90, SAFE_WIDTH, FONT_SANS_BOLD, 36, TEXT_LIGHT, max_lines=1)

    # Left tall frame: Hero profile
    d4.rounded_rectangle([SAFE_LEFT, 160, 535, 1180], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    back_img = p1_angles.get("back") or p1_angles.get("side") or p1_angles.get("front")
    if back_img:
        imb = Image.open(back_img).convert("RGB")
        paste_proportional(s4, imb, SAFE_LEFT + 15, 175, 435, 945)
    draw_safe_text(d4, f"{p1_name} (Profile)", SAFE_LEFT + 20, 1135, 425, FONT_SANS_REG, 18, TEXT_MUTED, max_lines=1)

    # Right top frame: Bottom
    d4.rounded_rectangle([555, 160, SAFE_RIGHT, 650], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if bot_img:
        imbt = Image.open(bot_img).convert("RGB")
        paste_proportional(s4, imbt, 570, 175, 425, 425)
    draw_safe_text(d4, p2_name, 570, 615, 425, FONT_SANS_REG, 18, TEXT_MUTED, max_lines=1)

    # Right bottom frame: Accessory
    d4.rounded_rectangle([555, 675, SAFE_RIGHT, 1180], radius=14, fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    acc_img = p3_angles.get("front") or p3_angles.get("side") or p2_angles.get("front")
    if acc_img:
        ima = Image.open(acc_img).convert("RGB")
        paste_proportional(s4, ima, 570, 690, 425, 435)
    draw_safe_text(d4, p3_name, 570, 1135, 425, FONT_SANS_REG, 18, TEXT_MUTED, max_lines=1)

    draw_safe_text(d4, "#NeverJustOneThing  •  Night Out Curated Ensemble", SAFE_LEFT, 1230, SAFE_WIDTH, FONT_SANS_BOLD, 22, ACCENT_COLOR, max_lines=1)

    p4_path = os.path.join(output_dir, "slide_4_accessories_layering.png")
    s4.save(p4_path, "PNG", quality=95)
    s4.save(os.path.join(output_dir, "slide_4_accessories_flatlay.png"), "PNG", quality=95)
    slides.append(p4_path)

    # --------------------------------------------------------------------------
    # SLIDE 5: NOCTURNE OUTRO
    # --------------------------------------------------------------------------
    s5 = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    d5 = ImageDraw.Draw(s5)

    draw_safe_text(d5, "COLORBOX", SAFE_LEFT, 50, 160, FONT_SANS_BOLD, 26, TEXT_LIGHT, max_lines=1)
    tag_sub = f"|  {theme_title.upper()[:35]}" if theme_title else "|  LOOKBOOK FINALE"
    draw_safe_text(d5, tag_sub, 240, 52, 700, FONT_SANS_REG, 22, ACCENT_COLOR, max_lines=1)

    d5_hl = (headline or theme_title or "NEVER JUST ONE THING").upper()
    draw_safe_text(d5, d5_hl, SAFE_LEFT, 105, SAFE_WIDTH, FONT_SANS_BOLD, 42, TEXT_LIGHT, max_lines=1)

    d5.rectangle([SAFE_LEFT, 175, SAFE_RIGHT, 1130], fill=CARD_BG, outline=BORDER_HAIRLINE, width=1)
    if p1_angles.get("front"):
        imf = Image.open(p1_angles["front"]).convert("RGB")
        paste_proportional(s5, imf, SAFE_LEFT + 20, 195, SAFE_WIDTH - 40, 915)

    draw_safe_text(d5, "#NeverJustOneThing", SAFE_LEFT, 1160, SAFE_WIDTH, FONT_SANS_BOLD, 36, ACCENT_COLOR, max_lines=1)
    draw_safe_text(d5, "Belanja koleksi lengkap di colorbox.co.id & seluruh store Colorbox.", SAFE_LEFT, 1215, SAFE_WIDTH, FONT_SANS_REG, 20, TEXT_MUTED, max_lines=1)

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
    visual_prompts: list[str] = None,
    num_slides: int = 3
) -> dict:
    """
    Renders bespoke, template-free 1080x1350 px Feed Portrait carousel slides (default 2 or 3 slides).
    Zero rigid box templates. Clean editorial aesthetic with 100% authentic Colorbox catalog photos.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Use Pinterest Aesthetic Engine (Zero-Text on Visual & Playwright rendering, strictly no rigid box fallback)
    from aesthetic_visual_engine import render_aesthetic_carousel
    res = render_aesthetic_carousel(
        theme_title=theme_title,
        headline=headline,
        subtitle=subtitle,
        products_info=products_info,
        output_dir=output_dir,
        images_dir=images_dir,
        day_num=day_num,
        num_slides=num_slides
    )
    if res and res.get("success"):
        return res

    raise RuntimeError(f"Visual rendering failed: {res.get('error') if isinstance(res, dict) else 'unknown error'}")

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
