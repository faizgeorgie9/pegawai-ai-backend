import os
import sys
import json
import base64
import urllib.request
import urllib.error
import ssl
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
        res = call_opencode_image_generation(prompt, model=model)
        if res:
            return res
    return None

def call_gemini_image_generation(prompt: str) -> bytes | None:
    """Compatibility wrapper redirecting image generation to openai/gpt-image-2 via OpenCode Zen."""
    return call_opencode_image_gen(prompt, model=DEFAULT_IMAGE_MODEL)

def call_gemini_generate(prompt: str, system_instruction: str = "", model: str = "deepseek-v4.1-flash") -> str:
    """Generates text via OpenCode Zen API (unified model endpoint)."""
    if call_opencode_chat:
        try:
            txt, _ = call_opencode_chat(prompt, system_prompt=system_instruction, model=model)
            if txt:
                return txt
        except Exception as e:
            print(f"[OpenCode Text Gen Error]: {e}")
    return ""


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

def get_swatches_for_product(prod: dict, count: int = 5, day_theme: int = 1) -> list[tuple[int, int, int]]:
    c_name = str(prod.get("color", "")).upper()
    palette = []
    for k, rgb in COLOR_MAP.items():
        if k in c_name:
            palette.append(rgb)
            break
            
    # Distinct fallback swatches based on day theme
    if day_theme == 2:
        # Autumn Earthy (Dark Brown, Olive, Ecru, Light Grey, Terracotta)
        defaults = [(62, 39, 35), (98, 114, 84), (236, 229, 216), (189, 195, 199), (214, 98, 77)]
    elif day_theme == 3:
        # Edgy Chic (Dark Red, Jet Black, Lilac, Off White, Coral)
        defaults = [(138, 28, 44), (25, 25, 28), (209, 196, 233), (246, 243, 236), (235, 78, 98)]
    else:
        # Day 1: Urban Y2K Denim & Pop (Dark Blue, Washed Black, Coral, Off White, Ecru)
        defaults = [(28, 43, 69), (25, 25, 28), (235, 78, 98), (246, 243, 236), (236, 229, 216)]
        
    for d in defaults:
        if d not in palette and len(palette) < count:
            palette.append(d)
    return palette[:count]


def render_final_carousel_package(
    theme_title: str,
    headline: str,
    subtitle: str,
    products_info: list[dict],
    output_dir: str,
    images_dir: str,
    day_num: int = 1
) -> dict:
    """
    Renders 5 final 1080x1350 px Feed Portrait carousel slides adhering strictly
    to the official @colorbox Instagram style:
    1. Vibe: Playful, Y2K-inspired, edgy-casual, scrapbook & collage grid.
    2. Micro-copy on canvas strictly 1-2 words.
    3. ZERO internal template noise (NO 'SLIDE 1/5', NO 'SLIDE 2', NO dots, NO 'SWIPE').
       In Instagram feed, pagination is handled by the app UI; canvas is 100% ready-to-post!
    4. ZERO prices anywhere on image canvas (prices belong in caption/bio).
    5. ZERO rigid technical fabric text on canvas.
    6. Aspect Ratio Preserved: Contain mode scaling with PIL Lanczos, never stretched/gepeng.
    7. Multi-day distinct aesthetics:
       - Day 1: Urban Y2K Denim & Pop Coral
       - Day 2: Warm Earthy Autumn & Dusty Olive / Coffee
       - Day 3: Chic Edgy Night & Crimson Leather / Lilac Pop
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Theme Presets
    if day_num == 2:
        # --- THEME 2: WARM AUTUMN & CAFE CHILL ---
        BG_COLOR = (244, 240, 232)        # Warm Oatmeal Cream
        CARD_BG = (253, 251, 247)         # Soft Ivory
        TEXT_DARK = (44, 30, 24)          # Deep Espresso Charcoal
        TEXT_MUTED = (120, 110, 100)      # Warm Sepia Muted
        ACCENT_PRIMARY = (196, 88, 52)    # Terracotta Warm Coral
        ACCENT_LIGHT = (248, 236, 224)    # Warm peach/cream tint
        BORDER_COLOR = (226, 220, 210)    # Soft Kraft Border
        GRID_COLOR = (236, 230, 220)      # Muted Graph Line
        RETRO_BAR = (212, 198, 178)       # Soft warm craft bar
        TAPE_COLOR = (248, 238, 220)      # Kraft tape
        STYLE_LABEL = "COFFEE RUN."
        SLIDE2_TITLE = "CHECKMATE."
        SLIDE3_TITLE = "CLEAN CUT."
        SLIDE4_TITLE = "WHAT'S INSIDE."
        SLIDE5_TITLE = "MEET YA!"
        DOODLE_TAG = "Daily Brew ☕"
    elif day_num == 3:
        # --- THEME 3: CHIC EDGY NIGHT & LEATHER POP ---
        BG_COLOR = (242, 243, 246)        # Cool Studio Off-White
        CARD_BG = (255, 255, 255)         # Pure Crisp White
        TEXT_DARK = (18, 18, 22)          # Sharp Jet Black
        TEXT_MUTED = (105, 107, 115)      # Slate Grey
        ACCENT_PRIMARY = (168, 32, 54)    # Crimson Berry
        ACCENT_LIGHT = (245, 228, 234)    # Rose tint
        BORDER_COLOR = (220, 222, 228)    # Clean Border
        GRID_COLOR = (232, 234, 240)      # Clean Minimalist Grid
        RETRO_BAR = (188, 192, 212)       # Cool steel lavender bar
        TAPE_COLOR = (235, 238, 245)      # Studio tape
        STYLE_LABEL = "NIGHT DROP."
        SLIDE2_TITLE = "LEATHER VIBE."
        SLIDE3_TITLE = "SILHOUETTE."
        SLIDE4_TITLE = "THE PACK."
        SLIDE5_TITLE = "SPILL IN BIO."
        DOODLE_TAG = "Standout ✨"
    else:
        # --- THEME 1: URBAN Y2K DENIM & POP CORAL ---
        BG_COLOR = (250, 248, 244)        # Soft Warm Paper
        CARD_BG = (255, 255, 255)         # Pure White
        TEXT_DARK = (24, 24, 27)          # Charcoal
        TEXT_MUTED = (113, 113, 122)      # Muted Zinc
        ACCENT_PRIMARY = (235, 78, 98)    # Colorbox Signature Coral
        ACCENT_LIGHT = (254, 237, 240)    # Soft Pink tint
        BORDER_COLOR = (228, 224, 216)    # Warm Border
        GRID_COLOR = (236, 232, 224)      # Fine Scrapbook Grid Line
        RETRO_BAR = (196, 212, 238)       # Win95 Titlebar pastel blue
        TAPE_COLOR = (255, 244, 230)      # Washi tape
        STYLE_LABEL = "JAKARTA STYLED."
        SLIDE2_TITLE = "CHAMBRAY VIBE."
        SLIDE3_TITLE = "FIT CHECK."
        SLIDE4_TITLE = "STARTER PACK."
        SLIDE5_TITLE = "NEXT STOP!"
        DOODLE_TAG = "Next Stop! ✨"

    # Fonts
    font_editorial_lg = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 68)
    font_sans_lg = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 68)
    font_editorial_md = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 46)
    font_sans_md = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 44)
    font_body = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
    font_body_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 28)
    font_doodle = ImageFont.truetype("C:/Windows/Fonts/segoeprb.ttf", 26)
    font_doodle_sm = ImageFont.truetype("C:/Windows/Fonts/segoeprb.ttf", 20)
    font_doodle_lg = ImageFont.truetype("C:/Windows/Fonts/segoeprb.ttf", 34)
    font_badge = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
    font_small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
    font_menu = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)

    def draw_grid(draw, w=1080, h=1350, spacing=55):
        for x in range(spacing, w, spacing):
            draw.line([(x, 0), (x, h)], fill=GRID_COLOR, width=1)
        for y in range(spacing, h, spacing):
            draw.line([(0, y), (w, y)], fill=GRID_COLOR, width=1)

    # BRANDING HEADER (Clean, NO slide numbers, NO 'SLIDE X/5' noise!)
    def draw_clean_header(draw, tag_label="LOOKBOOK"):
        draw.text((60, 48), "COLORBOX", fill=TEXT_DARK, font=font_body_bold)
        draw.text((225, 51), f"|   {tag_label.upper()}", fill=TEXT_MUTED, font=font_body)
        pill_w = 140
        pill_x = 1080 - 60 - pill_w
        draw.rounded_rectangle([pill_x, 42, pill_x + pill_w, 82], radius=20, fill=ACCENT_LIGHT)
        draw.text((pill_x + 22, 50), "BABES ♡", fill=ACCENT_PRIMARY, font=font_badge)

    def draw_washi_tape(draw, x, y, w=110, h=28):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=4, fill=TAPE_COLOR, outline=BORDER_COLOR, width=1)

    def draw_doodle_heart(draw, cx, cy, label="C & B"):
        draw.ellipse([cx - 36, cy - 26, cx + 2, cy + 18], fill=ACCENT_LIGHT, outline=ACCENT_PRIMARY, width=2)
        draw.ellipse([cx - 2, cy - 26, cx + 36, cy + 18], fill=ACCENT_LIGHT, outline=ACCENT_PRIMARY, width=2)
        draw.polygon([(cx - 34, cy + 6), (cx + 34, cy + 6), (cx, cy + 38)], fill=ACCENT_LIGHT)
        draw.line([(cx - 34, cy + 6), (cx, cy + 38)], fill=ACCENT_PRIMARY, width=2)
        draw.line([(cx + 34, cy + 6), (cx, cy + 38)], fill=ACCENT_PRIMARY, width=2)
        bbox = draw.textbbox((0, 0), label, font=font_doodle_sm)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw//2, cy - 8), label, fill=ACCENT_PRIMARY, font=font_doodle_sm)

    def draw_color_palette(draw, start_x, start_y, colors):
        draw.text((start_x, start_y), "COLORWAYS", fill=TEXT_MUTED, font=font_small)
        cur_x = start_x
        y_dot = start_y + 36
        for c in colors:
            draw.ellipse([cur_x - 1, y_dot - 1, cur_x + 35, y_dot + 35], fill=(255, 255, 255), outline=BORDER_COLOR, width=1)
            draw.ellipse([cur_x + 2, y_dot + 2, cur_x + 32, y_dot + 32], fill=c)
            cur_x += 46

    def paste_proportional(canvas, img, box_x, box_y, box_w, box_h):
        """
        Pastes `img` strictly preserving natural aspect ratio (contain mode),
        centering horizontally & vertically so model & garment are never stretched/gepeng.
        """
        orig_w, orig_h = img.size
        ratio = min(box_w / orig_w, box_h / orig_h)
        new_w = max(1, int(orig_w * ratio))
        new_h = max(1, int(orig_h * ratio))
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        pos_x = box_x + (box_w - new_w) // 2
        pos_y = box_y + (box_h - new_h) // 2
        canvas.paste(resized, (pos_x, pos_y))
        return pos_x, pos_y, new_w, new_h

    # Product references
    p1 = products_info[0] if len(products_info) > 0 else {}
    p2 = products_info[1] if len(products_info) > 1 else {}
    p3 = products_info[2] if len(products_info) > 2 else {}

    p1_file = p1.get("image_file", "cbx-01-contrast-stitch-chambray-shirt.jpg")
    p2_file = p2.get("image_file", "cbx-02-high-waist-barrel-denim-black.jpg")
    p3_file = p3.get("image_file", "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg")

    p1_img = os.path.join(images_dir, p1_file)
    p2_img = os.path.join(images_dir, p2_file)
    p3_img = os.path.join(images_dir, p3_file)

    generated_slides = []

    # ==============================================================================
    # SLIDE 1: COVER HERO (EDITORIAL LOOKBOOK / CLEAN FEED READY)
    # ==============================================================================
    s1 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)
    draw_grid(d1)
    draw_clean_header(d1, f"DROP {day_num:02d}")

    # Main Headline (Micro-hook: 1-2 words only)
    words = STYLE_LABEL.split()
    first_w = words[0] if words else "COLORBOX"
    second_w = words[1] if len(words) > 1 else "STYLED."

    d1.text((60, 135), first_w, fill=TEXT_DARK, font=font_editorial_lg)
    bbox_w = d1.textbbox((0, 0), first_w + " ", font=font_editorial_lg)
    fw_w = bbox_w[2] - bbox_w[0]
    d1.text((60 + fw_w, 135), second_w, fill=TEXT_DARK, font=font_sans_lg)
    
    # Chic dot accent
    bbox_tot = d1.textbbox((0, 0), first_w + " " + second_w, font=font_editorial_lg)
    tot_w = bbox_tot[2] - bbox_tot[0]
    d1.ellipse([60 + tot_w + 12, 190, 60 + tot_w + 26, 204], fill=ACCENT_PRIMARY)

    draw_doodle_heart(d1, 960, 175, "C & B")
    d1.text((860, 230), DOODLE_TAG, fill=ACCENT_PRIMARY, font=font_doodle_sm)

    # Hero Card (Spanning down to 1270 px - Clean full-bleed, NO bottom bar noise)
    card_box = [60, 270, 1020, 1270]
    d1.rounded_rectangle(card_box, radius=22, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d1, 140, 255)
    draw_washi_tape(d1, 830, 255)

    if os.path.exists(p1_img) and os.path.exists(p2_img):
        im1 = Image.open(p1_img).convert("RGB")
        im2 = Image.open(p2_img).convert("RGB")
        paste_proportional(s1, im1, 80, 290, 435, 840)
        paste_proportional(s1, im2, 565, 290, 435, 840)
    elif os.path.exists(p1_img):
        im1 = Image.open(p1_img).convert("RGB")
        paste_proportional(s1, im1, 80, 290, 920, 840)

    # Bottom Swatch Bar (Minimal, NO slide numbers, NO 'swipe')
    d1.rounded_rectangle([85, 1160, 995, 1245], radius=16, fill=BG_COLOR)
    d1.text((115, 1180), "COLORWAYS PALETTE", fill=TEXT_DARK, font=font_body_bold)
    draw_color_palette(d1, 620, 1168, get_swatches_for_product(p1, 5, day_num))

    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    generated_slides.append(p1_path)

    # ==============================================================================
    # SLIDE 2: HERO TOP PIECE (CLEAN SCRAPBOOK / RETRO WINDOW)
    # ==============================================================================
    s2 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d2 = ImageDraw.Draw(s2)
    draw_grid(d2)
    draw_clean_header(d2, "TOP PIECE")

    # Retro Window Frame (Clean, down to 1140 px)
    win_box = [80, 135, 1000, 1140]
    d2.rounded_rectangle(win_box, radius=12, fill=(242, 242, 242), outline=BORDER_COLOR, width=2)
    # Title bar
    d2.rounded_rectangle([82, 137, 998, 195], radius=10, fill=RETRO_BAR)
    clean_p1_title = p1.get("name", "Top Piece")[:26]
    d2.text((110, 150), f"🗔  {clean_p1_title}", fill=(25, 30, 50), font=font_body_bold)
    
    # Window controls
    d2.rectangle([900, 146, 925, 178], fill=(225, 225, 225), outline=(150, 150, 150), width=1)
    d2.text((908, 148), "_", fill=TEXT_DARK, font=font_small)
    d2.rectangle([932, 146, 957, 178], fill=(225, 225, 225), outline=(150, 150, 150), width=1)
    d2.text((939, 150), "□", fill=TEXT_DARK, font=font_small)
    d2.rectangle([964, 146, 989, 178], fill=(225, 225, 225), outline=(150, 150, 150), width=1)
    d2.text((971, 150), "✕", fill=TEXT_DARK, font=font_small)

    # Menu bar
    d2.rectangle([82, 196, 998, 235], fill=(248, 248, 248))
    d2.line([82, 235, 998, 235], fill=BORDER_COLOR, width=1)
    d2.text((105, 203), "File    Edit    View    Image    Options", fill=(100, 100, 100), font=font_menu)

    # Canvas area
    d2.rectangle([100, 250, 980, 1120], fill=CARD_BG, outline=BORDER_COLOR, width=1)
    if os.path.exists(p1_img):
        im_top = Image.open(p1_img).convert("RGB")
        paste_proportional(s2, im_top, 105, 255, 870, 850)

    # Bottom Micro-Copy + Swatches (NO slide numbering, NO fake buttons)
    d2.text((80, 1175), SLIDE2_TITLE, fill=TEXT_DARK, font=font_sans_md)
    d2.text((830, 1180), "Cute Vibe ♡", fill=ACCENT_PRIMARY, font=font_doodle)
    draw_color_palette(d2, 450, 1170, get_swatches_for_product(p1, 5, day_num))

    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    generated_slides.append(p2_path)

    # ==============================================================================
    # SLIDE 3: BOTTOM PAIRING / FIT CHECK (POLAROID COLLAGE)
    # ==============================================================================
    s3 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)
    draw_grid(d3)
    draw_clean_header(d3, "BOTTOM PAIRING")

    # Title: Micro-hook (1-2 words)
    d3.text((60, 135), SLIDE3_TITLE, fill=TEXT_DARK, font=font_editorial_lg)
    draw_doodle_heart(d3, 960, 175, "C & B")

    # Polaroid style card
    polaroid_box = [140, 255, 940, 1260]
    d3.rounded_rectangle(polaroid_box, radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d3, 480, 240)

    if os.path.exists(p2_img):
        im_bot = Image.open(p2_img).convert("RGB")
        paste_proportional(s3, im_bot, 160, 275, 760, 830)

    # Polaroid bottom bar: Doodle + Swatches (Clean, ready to post)
    d3.text((180, 1150), "Daily Fit ♡", fill=ACCENT_PRIMARY, font=font_doodle_lg)
    draw_color_palette(d3, 560, 1140, get_swatches_for_product(p2, 5, day_num))

    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    generated_slides.append(p3_path)

    # ==============================================================================
    # SLIDE 4: FLAT-LAY STARTER PACK (GEN-Z ESSENTIALS)
    # ==============================================================================
    s4 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d4 = ImageDraw.Draw(s4)
    draw_grid(d4)
    draw_clean_header(d4, "STARTER PACK")

    # Title: Micro-hook (1-2 words)
    d4.text((60, 135), SLIDE4_TITLE, fill=TEXT_DARK, font=font_editorial_lg)
    d4.text((820, 150), "Essentials ✨", fill=ACCENT_PRIMARY, font=font_doodle)

    # Grid board for flatlay (down to 1270 px)
    board = [60, 255, 1020, 1270]
    d4.rounded_rectangle(board, radius=22, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d4, 120, 240)
    draw_washi_tape(d4, 850, 240)

    # Item 1: Top Cutout (Proportional fit, no stretching)
    if os.path.exists(p1_img):
        im_t = Image.open(p1_img).convert("RGB")
        paste_proportional(s4, im_t, 80, 275, 430, 480)

    # Item 2: Denim / Bottom Cutout (Proportional fit, no stretching)
    if os.path.exists(p2_img):
        im_b = Image.open(p2_img).convert("RGB")
        paste_proportional(s4, im_b, 80, 785, 430, 450)

    # Item 3: Tote Bag / Accessory Cutout (Proportional fit, no stretching)
    if os.path.exists(p3_img):
        im_bag = Image.open(p3_img).convert("RGB")
        paste_proportional(s4, im_bag, 550, 275, 430, 480)

    # Vector lifestyle illustrations in bottom right
    d4.rounded_rectangle([550, 800, 985, 1235], radius=18, fill=BG_COLOR, outline=BORDER_COLOR, width=1)
    d4.text((575, 825), "LIFESTYLE ACCENTS", fill=TEXT_MUTED, font=font_badge)

    # Sunglasses
    d4.ellipse([580, 895, 690, 955], fill=(35, 35, 35), outline=(190, 150, 80), width=3)
    d4.ellipse([730, 895, 840, 955], fill=(35, 35, 35), outline=(190, 150, 80), width=3)
    d4.line([(690, 920), (730, 920)], fill=(190, 150, 80), width=4)
    d4.text((865, 915), "Oval Shades", fill=TEXT_DARK, font=font_small)

    # Iced Coffee
    d4.polygon([(590, 1010), (650, 1010), (640, 1120), (600, 1120)], fill=(205, 150, 100), outline=(140, 140, 140), width=2)
    d4.arc([585, 995, 655, 1020], 180, 360, fill=(140, 140, 140), width=3)
    d4.line([(630, 975), (615, 1040)], fill=ACCENT_PRIMARY, width=4)
    d4.text((675, 1045), "Iced Coffee", fill=TEXT_DARK, font=font_small)

    # Silver Headphones
    d4.arc([760, 1010, 860, 1100], 180, 360, fill=(155, 160, 170), width=5)
    d4.ellipse([750, 1060, 780, 1125], fill=(195, 200, 210), outline=(115, 120, 130), width=2)
    d4.ellipse([840, 1060, 870, 1125], fill=(195, 200, 210), outline=(115, 120, 130), width=2)
    d4.text((885, 1080), "Headphones", fill=TEXT_DARK, font=font_small)

    p4_path = os.path.join(output_dir, "slide_4_accessories_flatlay.png")
    s4.save(p4_path, "PNG", quality=95)
    generated_slides.append(p4_path)

    # ==============================================================================
    # SLIDE 5: OUTRO & MOODBOARD SIGN-OFF (CLEAN FEED READY)
    # ==============================================================================
    s5 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d5 = ImageDraw.Draw(s5)
    draw_grid(d5)
    draw_clean_header(d5, "LOOKBOOK SIGN-OFF")

    # Title: Micro-hook (1-2 words)
    d5.text((60, 135), SLIDE5_TITLE, fill=TEXT_DARK, font=font_editorial_lg)

    # Polaroid photo in center
    pol_box = [180, 255, 900, 1030]
    d5.rounded_rectangle(pol_box, radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d5, 485, 240)

    if os.path.exists(p1_img):
        im_outro = Image.open(p1_img).convert("RGB")
        paste_proportional(s5, im_outro, 200, 275, 680, 640)

    d5.text((230, 940), "#NeverJustOneThing ♡", fill=ACCENT_PRIMARY, font=font_doodle_lg)
    draw_doodle_heart(d5, 830, 965, "C & B")

    # Clean Brand Signature Banner at bottom (NO 'slide 5', NO 'swipe', NO dots!)
    d5.rounded_rectangle([60, 1080, 1020, 1260], radius=22, fill=TEXT_DARK)
    d5.text((100, 1120), "COLORBOX INDONESIA", fill=(255, 255, 255), font=font_body_bold)
    d5.text((100, 1170), "Discover full looks & styling in bio link  •  #NeverJustOneThing", fill=(190, 190, 195), font=font_small)

    p5_path = os.path.join(output_dir, "slide_5_outro_cta.png")
    s5.save(p5_path, "PNG", quality=95)
    generated_slides.append(p5_path)

    preview_html = generate_carousel_preview_html(output_dir, theme_title, headline, day_num=day_num)

    return {
        "slides": generated_slides,
        "output_dir": output_dir,
        "preview_html": preview_html,
        "day_num": day_num
    }


def generate_carousel_preview_html(output_dir: str, title: str, subtitle: str, day_num: int = 1) -> str:
    html_path = os.path.join(output_dir, "carousel_preview.html")
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Colorbox Carousel Live Preview — Day {day_num} ({title})</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background: #0f172a; color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px 20px; }}
    header {{ text-align: center; margin-bottom: 30px; max-width: 600px; }}
    .badge {{ display: inline-block; padding: 6px 14px; border-radius: 999px; background: #eb4e62; color: white; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 12px; }}
    h1 {{ font-size: 26px; margin-bottom: 8px; }}
    p.desc {{ color: #94a3b8; font-size: 15px; line-height: 1.5; }}
    .feed-container {{ width: 100%; max-width: 500px; background: #1e293b; border-radius: 20px; padding: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); border: 1px solid #334155; }}
    .account-bar {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding: 0 4px; }}
    .profile {{ display: flex; align-items: center; gap: 10px; }}
    .avatar {{ width: 36px; height: 36px; border-radius: 50%; background: #eb4e62; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; color: white; }}
    .acc-name {{ font-size: 14px; font-weight: 600; color: white; }}
    .acc-sub {{ font-size: 11px; color: #94a3b8; }}
    .carousel-stage {{ position: relative; width: 100%; aspect-ratio: 4 / 5; border-radius: 12px; overflow: hidden; background: #000; }}
    .slides-wrapper {{ display: flex; width: 500%; height: 100%; transition: transform 0.4s cubic-bezier(0.25, 1, 0.5, 1); }}
    .slide-item {{ width: 20%; height: 100%; position: relative; }}
    .slide-item img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .nav-btn {{ position: absolute; top: 50%; transform: translateY(-50%); width: 40px; height: 40px; border-radius: 50%; background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.2); color: white; font-size: 20px; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 10; transition: all 0.2s; }}
    .nav-btn:hover {{ background: #eb4e62; border-color: #eb4e62; }}
    .prev-btn {{ left: 12px; }}
    .next-btn {{ right: 12px; }}
    .dots-nav {{ display: flex; justify-content: center; gap: 6px; margin-top: 14px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #475569; transition: all 0.2s; cursor: pointer; }}
    .dot.active {{ background: #eb4e62; width: 22px; border-radius: 4px; }}
    .action-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 4px 6px 4px; color: #f8fafc; font-size: 20px; }}
    .action-left {{ display: flex; gap: 16px; }}
    .action-icon {{ cursor: pointer; transition: transform 0.15s; }}
    .action-icon:hover {{ transform: scale(1.15); color: #eb4e62; }}
    .caption-box {{ padding: 6px 4px; font-size: 13px; line-height: 1.5; color: #cbd5e1; }}
    .caption-box b {{ color: white; margin-right: 6px; }}
    .tags {{ color: #38bdf8; font-size: 12px; margin-top: 6px; }}
    footer {{ margin-top: 35px; text-align: center; color: #64748b; font-size: 13px; }}
  </style>
</head>
<body>
  <header>
    <div class="badge">LOOKBOOK FEED 4:5 — COLORBOX AI (DAY {day_num})</div>
    <h1>Colorbox Carousel Live Preview</h1>
    <p class="desc">{title} • {subtitle}<br><span style="color: #cbd5e1; font-size: 13px;">Gaya: Playful, Y2K-inspired, scrapbook street style (@colorbox standard) • 100% Siap Posting</span></p>
  </header>

  <div class="feed-container">
    <div class="account-bar">
      <div class="profile">
        <div class="avatar">CB</div>
        <div>
          <div class="acc-name">colorboxindonesia</div>
          <div class="acc-sub">Sponsored • Never Just One Thing</div>
        </div>
      </div>
      <div style="font-size: 20px; cursor: pointer;">•••</div>
    </div>

    <div class="carousel-stage">
      <button class="nav-btn prev-btn" id="prevBtn" onclick="moveSlide(-1)">&#10094;</button>
      <div class="slides-wrapper" id="slidesWrapper">
        <div class="slide-item"><img src="slide_1_cover_hero.png" alt="Slide 1"></div>
        <div class="slide-item"><img src="slide_2_hero_top.png" alt="Slide 2"></div>
        <div class="slide-item"><img src="slide_3_bottom_pairing.png" alt="Slide 3"></div>
        <div class="slide-item"><img src="slide_4_accessories_flatlay.png" alt="Slide 4"></div>
        <div class="slide-item"><img src="slide_5_outro_cta.png" alt="Slide 5"></div>
      </div>
      <button class="nav-btn next-btn" id="nextBtn" onclick="moveSlide(1)">&#10095;</button>
    </div>

    <div class="dots-nav">
      <div class="dot active" onclick="goToSlide(0)"></div>
      <div class="dot" onclick="goToSlide(1)"></div>
      <div class="dot" onclick="goToSlide(2)"></div>
      <div class="dot" onclick="goToSlide(3)"></div>
      <div class="dot" onclick="goToSlide(4)"></div>
    </div>

    <div class="action-bar">
      <div class="action-left">
        <span class="action-icon">&#9825;</span>
        <span class="action-icon">&#128172;</span>
        <span class="action-icon">&#10148;</span>
      </div>
      <span class="action-icon">&#128278;</span>
    </div>

    <div class="caption-box">
      <p><b>colorboxindonesia</b> {title}: {subtitle}✨ Padu padan resmi Colorbox ini siap bikin kamu tampil standout tapi tetap super comfy seharian! 💖</p>
      <div class="tags">#ColorboxIndonesia #NeverJustOneThing #CampusOOTD #GenZStyle #ColorboxBabes</div>
    </div>
  </div>

  <footer>
    Dirender otomatis oleh 5 AI Agents via Pegawai AI Engine (openai/gpt-image-2 via OpenCode Zen) • Clean & Ready to Post.
  </footer>

  <script>
    let currentSlide = 0;
    const totalSlides = 5;
    const wrapper = document.getElementById("slidesWrapper");
    const dots = document.querySelectorAll(".dot");

    function updateCarousel() {{
      wrapper.style.transform = `translateX(-${{currentSlide * 20}}%)`;
      dots.forEach((d, idx) => {{
        if (idx === currentSlide) d.classList.add("active");
        else d.classList.remove("active");
      }});
    }}

    function moveSlide(dir) {{
      currentSlide = (currentSlide + dir + totalSlides) % totalSlides;
      updateCarousel();
    }}

    function goToSlide(idx) {{
      currentSlide = idx;
      updateCarousel();
    }}
  </script>
</body>
</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_path
