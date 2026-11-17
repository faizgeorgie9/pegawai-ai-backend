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
    """Generates text via OpenCode Zen API (so all APIs are unified)."""
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
    "BLACK": (33, 33, 33),
    "DARK BROWN": (62, 39, 35),
    "BROWN": (85, 55, 45),
    "OFF WHITE": (245, 242, 235),
    "WHITE": (250, 250, 250),
    "ECRU": (236, 229, 216),
    "LT. PINK": (248, 187, 208),
    "PINK": (244, 143, 177),
    "GREY": (99, 103, 110),
    "LIGHT GREY": (189, 195, 199),
    "LILAC": (209, 196, 233),
    "BUTTER": (255, 249, 196),
    "BEIGE": (235, 222, 203),
    "CORAL": (235, 78, 98),
}

def get_swatches_for_product(prod: dict, count: int = 5) -> list[tuple[int, int, int]]:
    c_name = str(prod.get("color", "")).upper()
    palette = []
    for k, rgb in COLOR_MAP.items():
        if k in c_name:
            palette.append(rgb)
            break
    defaults = [(28, 43, 69), (62, 39, 35), (245, 242, 235), (248, 187, 208), (33, 33, 33), (236, 229, 216)]
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
    images_dir: str
) -> dict:
    """
    Renders 5 final 1080x1350 px Feed Portrait carousel slides adhering strictly
    to the official @colorbox Instagram style:
    1. Vibe: Playful, Y2K-inspired, edgy-casual, scrapbook & collage grid.
    2. Micro-copy on canvas strictly 1-2 words.
    3. ZERO prices anywhere on image canvas (prices only in captions/bio).
    4. ZERO rigid technical fabric text on canvas.
    5. Color Palette Swatches (circular dots) representing colorways.
    6. Layouts: Scrapbook grid, retro Windows 95/Paint UI, flat-lay starter pack, street style duo/polaroid.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    BG_COLOR = (250, 248, 244)        # Soft Warm Ivory / Paper
    CARD_BG = (255, 255, 255)         # Pure White
    TEXT_DARK = (24, 24, 27)          # Charcoal #18181B
    TEXT_MUTED = (113, 113, 122)      # Muted Zinc #71717A
    ACCENT_CORAL = (235, 78, 98)      # Colorbox Coral #EB4E62
    ACCENT_LIGHT = (254, 237, 240)    # Soft Pink tint
    BORDER_COLOR = (228, 224, 216)    # Light Border
    GRID_COLOR = (236, 232, 224)      # Fine Scrapbook Grid Line
    RETRO_BLUE = (196, 212, 238)      # Win95 Titlebar pastel blue
    TAPE_COLOR = (255, 244, 230)      # Washi tape

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

    def draw_header(draw, title_text, slide_number):
        draw.text((60, 42), "COLORBOX", fill=TEXT_DARK, font=font_body_bold)
        draw.text((225, 45), f"|   {title_text.upper()}", fill=TEXT_MUTED, font=font_body)
        pill_w = 160
        pill_x = 1080 - 60 - pill_w
        draw.rounded_rectangle([pill_x, 34, pill_x + pill_w, 80], radius=23, fill=(240, 236, 228))
        draw.text((pill_x + 28, 42), f"SLIDE {slide_number}/5", fill=TEXT_DARK, font=font_badge)

    def draw_footer(draw, slide_number, cta_text="SWIPE ➔"):
        draw.line([60, 1260, 1020, 1260], fill=BORDER_COLOR, width=1)
        start_x = 60
        for i in range(1, 6):
            col = ACCENT_CORAL if i == slide_number else BORDER_COLOR
            rad = 8 if i == slide_number else 5
            draw.ellipse([start_x, 1290 - rad, start_x + rad*2, 1290 + rad], fill=col)
            start_x += 24
        bbox = draw.textbbox((0, 0), cta_text, font=font_badge)
        text_w = bbox[2] - bbox[0]
        draw.text((1080 - 60 - text_w, 1276), cta_text, fill=ACCENT_CORAL, font=font_badge)

    def draw_washi_tape(draw, x, y, w=110, h=28):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=4, fill=TAPE_COLOR, outline=(230, 218, 202), width=1)

    def draw_doodle_heart(draw, cx, cy, label="C & B"):
        draw.ellipse([cx - 36, cy - 26, cx + 2, cy + 18], fill=ACCENT_LIGHT, outline=ACCENT_CORAL, width=2)
        draw.ellipse([cx - 2, cy - 26, cx + 36, cy + 18], fill=ACCENT_LIGHT, outline=ACCENT_CORAL, width=2)
        draw.polygon([(cx - 34, cy + 6), (cx + 34, cy + 6), (cx, cy + 38)], fill=ACCENT_LIGHT)
        draw.line([(cx - 34, cy + 6), (cx, cy + 38)], fill=ACCENT_CORAL, width=2)
        draw.line([(cx + 34, cy + 6), (cx, cy + 38)], fill=ACCENT_CORAL, width=2)
        bbox = draw.textbbox((0, 0), label, font=font_doodle_sm)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw//2, cy - 8), label, fill=ACCENT_CORAL, font=font_doodle_sm)

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
        Pastes `img` into [box_x, box_y, box_x + box_w, box_y + box_h]
        strictly preserving the natural aspect ratio (contain mode),
        centering it horizontally & vertically so model and garment are NEVER stretched/gepeng.
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

    # --- SLIDE 1: COVER HERO (EDITORIAL STREET STYLE) ---
    s1 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d1 = ImageDraw.Draw(s1)
    draw_grid(d1)
    draw_header(d1, "DROP 01", 1)

    # Title: Minimal 1-2 words (JAKARTA STYLED.)
    d1.text((60, 130), "JAKARTA", fill=TEXT_DARK, font=font_editorial_lg)
    bbox_j = d1.textbbox((0, 0), "JAKARTA ", font=font_editorial_lg)
    j_w = bbox_j[2] - bbox_j[0]
    d1.text((60 + j_w, 130), "STYLED.", fill=TEXT_DARK, font=font_sans_lg)
    d1.ellipse([60 + j_w + 295, 185, 60 + j_w + 310, 200], fill=ACCENT_CORAL)

    d1.text((60, 215), "Lookbook Vol. 1  •  Urban Street Style", fill=TEXT_MUTED, font=font_body)
    draw_doodle_heart(d1, 960, 175, "C & B")
    d1.text((870, 230), "Next Stop! ✨", fill=ACCENT_CORAL, font=font_doodle_sm)

    # Hero Card
    card_box = [60, 275, 1020, 1220]
    d1.rounded_rectangle(card_box, radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d1, 140, 260)
    draw_washi_tape(d1, 830, 260)

    if os.path.exists(p1_img) and os.path.exists(p2_img):
        im1 = Image.open(p1_img).convert("RGB")
        im2 = Image.open(p2_img).convert("RGB")
        paste_proportional(s1, im1, 80, 300, 440, 780)
        paste_proportional(s1, im2, 560, 300, 440, 780)
    elif os.path.exists(p1_img):
        im1 = Image.open(p1_img).convert("RGB")
        paste_proportional(s1, im1, 60, 300, 960, 780)

    # Bottom badge
    d1.rounded_rectangle([85, 1110, 995, 1195], radius=16, fill=(250, 248, 244))
    d1.text((115, 1130), "OOTD DUO STREET STYLE", fill=TEXT_DARK, font=font_body_bold)
    d1.text((115, 1162), "Direct Flash Photography • Jakarta Subculture", fill=TEXT_MUTED, font=font_small)
    draw_color_palette(d1, 740, 1120, get_swatches_for_product(p1, 4))

    draw_footer(d1, 1, "SWIPE ➔")
    p1_path = os.path.join(output_dir, "slide_1_cover_hero.png")
    s1.save(p1_path, "PNG", quality=95)
    generated_slides.append(p1_path)

    # --- SLIDE 2: TOP PIECE / LOOK 01 (RETRO WINDOW) ---
    s2 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d2 = ImageDraw.Draw(s2)
    draw_grid(d2)
    draw_header(d2, "LOOK 01", 2)

    # Retro Window Frame (Microsoft Paint / Windows 95)
    win_box = [80, 135, 1000, 1050]
    d2.rounded_rectangle(win_box, radius=8, fill=(240, 240, 240), outline=(130, 130, 130), width=2)
    # Title bar
    d2.rounded_rectangle([82, 137, 998, 195], radius=6, fill=RETRO_BLUE)
    clean_p1_title = p1.get("name", "Chambray Shirt")[:24]
    d2.text((105, 150), f"🗔  LOOK 01 — {clean_p1_title}.bmp", fill=(20, 30, 60), font=font_body_bold)
    
    # Window controls
    d2.rectangle([900, 146, 925, 178], fill=(225, 225, 225), outline=(100, 100, 100), width=1)
    d2.text((908, 148), "_", fill=TEXT_DARK, font=font_small)
    d2.rectangle([932, 146, 957, 178], fill=(225, 225, 225), outline=(100, 100, 100), width=1)
    d2.text((939, 150), "□", fill=TEXT_DARK, font=font_small)
    d2.rectangle([964, 146, 989, 178], fill=(225, 225, 225), outline=(100, 100, 100), width=1)
    d2.text((971, 150), "✕", fill=TEXT_DARK, font=font_small)

    # Menu bar
    d2.rectangle([82, 196, 998, 235], fill=(245, 245, 245))
    d2.line([82, 235, 998, 235], fill=(200, 200, 200), width=1)
    d2.text((105, 203), "File    Edit    View    Image    Options    Help", fill=(80, 80, 80), font=font_menu)

    # Canvas area
    d2.rectangle([100, 250, 980, 1030], fill=CARD_BG, outline=(180, 180, 180), width=1)
    if os.path.exists(p1_img):
        im_top = Image.open(p1_img).convert("RGB")
        paste_proportional(s2, im_top, 100, 250, 880, 780)

    # Bottom Micro-Copy (1-2 Words!) + Color Swatches
    d2.text((80, 1090), "LOOK 01", fill=TEXT_DARK, font=font_sans_md)
    d2.text((80, 1148), "Top Pick  •  Relaxed Silhouette", fill=TEXT_MUTED, font=font_body)
    d2.text((800, 1095), "Super cute! ✨", fill=ACCENT_CORAL, font=font_doodle)
    draw_color_palette(d2, 80, 1185, get_swatches_for_product(p1, 5))

    draw_footer(d2, 2, "SWIPE ➔")
    p2_path = os.path.join(output_dir, "slide_2_hero_top.png")
    s2.save(p2_path, "PNG", quality=95)
    generated_slides.append(p2_path)

    # --- SLIDE 3: BOTTOM PAIRING / FIT CHECK ---
    s3 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d3 = ImageDraw.Draw(s3)
    draw_grid(d3)
    draw_header(d3, "FIT CHECK", 3)

    # Title: FIT CHECK.
    d3.text((60, 130), "FIT", fill=TEXT_DARK, font=font_editorial_lg)
    bbox_f = d3.textbbox((0, 0), "FIT ", font=font_editorial_lg)
    f_w = bbox_f[2] - bbox_f[0]
    d3.text((60 + f_w, 130), "CHECK.", fill=TEXT_DARK, font=font_sans_lg)
    d3.ellipse([60 + f_w + 245, 185, 60 + f_w + 260, 200], fill=ACCENT_CORAL)
    d3.text((60, 215), "Barrel Leg Silhouette  •  High Rise Cut", fill=TEXT_MUTED, font=font_body)

    # Polaroid style card
    polaroid_box = [160, 275, 920, 1140]
    d3.rounded_rectangle(polaroid_box, radius=18, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d3, 480, 260)

    if os.path.exists(p2_img):
        im_bot = Image.open(p2_img).convert("RGB")
        paste_proportional(s3, im_bot, 180, 280, 720, 740)

    # Polaroid bottom bar
    d3.text((220, 1055), "Daily Fit ♡", fill=ACCENT_CORAL, font=font_doodle_lg)
    draw_color_palette(d3, 580, 1045, get_swatches_for_product(p2, 4))

    draw_footer(d3, 3, "SWIPE ➔")
    p3_path = os.path.join(output_dir, "slide_3_bottom_pairing.png")
    s3.save(p3_path, "PNG", quality=95)
    generated_slides.append(p3_path)

    # --- SLIDE 4: FLAT-LAY STARTER PACK ---
    s4 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d4 = ImageDraw.Draw(s4)
    draw_grid(d4)
    draw_header(d4, "STARTER PACK", 4)

    # Title: STARTER PACK.
    d4.text((60, 130), "STARTER", fill=TEXT_DARK, font=font_editorial_lg)
    bbox_s = d4.textbbox((0, 0), "STARTER ", font=font_editorial_lg)
    s_w = bbox_s[2] - bbox_s[0]
    d4.text((60 + s_w, 130), "PACK.", fill=TEXT_DARK, font=font_sans_lg)
    d4.ellipse([60 + s_w + 185, 185, 60 + s_w + 200, 200], fill=ACCENT_CORAL)
    d4.text((60, 215), "What's in My Outfit  •  Jakarta Casual Essentials", fill=TEXT_MUTED, font=font_body)
    d4.text((820, 215), "Essentials ✨", fill=ACCENT_CORAL, font=font_doodle)

    # Grid board for flatlay
    board = [60, 270, 1020, 1220]
    d4.rounded_rectangle(board, radius=20, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d4, 120, 255)
    draw_washi_tape(d4, 850, 255)

    # Item 1: Top Cutout (Proportional fit, no stretching)
    if os.path.exists(p1_img):
        im_t = Image.open(p1_img).convert("RGB")
        paste_proportional(s4, im_t, 80, 290, 420, 460)
        d4.text((105, 765), "01 / Casual Top", fill=TEXT_DARK, font=font_body_bold)

    # Item 2: Denim Cutout (Proportional fit, no stretching)
    if os.path.exists(p2_img):
        im_b = Image.open(p2_img).convert("RGB")
        paste_proportional(s4, im_b, 80, 795, 420, 390)
        d4.text((105, 1195), "02 / Denim Cut", fill=TEXT_DARK, font=font_body_bold)

    # Item 3: Tote Bag Cutout (Proportional fit, no stretching)
    if os.path.exists(p3_img):
        im_bag = Image.open(p3_img).convert("RGB")
        paste_proportional(s4, im_bag, 540, 290, 420, 460)
        d4.text((550, 765), "03 / Tote Bag", fill=TEXT_DARK, font=font_body_bold)

    # Vector lifestyle illustrations in bottom right
    d4.rounded_rectangle([540, 830, 975, 1175], radius=16, fill=(250, 248, 244), outline=BORDER_COLOR, width=1)
    d4.text((565, 850), "LIFESTYLE ACCENTS", fill=TEXT_MUTED, font=font_badge)

    # Sunglasses
    d4.ellipse([570, 910, 680, 970], fill=(40, 40, 40), outline=(200, 160, 90), width=3)
    d4.ellipse([720, 910, 830, 970], fill=(40, 40, 40), outline=(200, 160, 90), width=3)
    d4.line([(680, 935), (720, 935)], fill=(200, 160, 90), width=4)
    d4.text((850, 928), "Oval Shades", fill=TEXT_DARK, font=font_small)

    # Iced Coffee
    d4.polygon([(580, 1020), (640, 1020), (630, 1130), (590, 1130)], fill=(210, 160, 110), outline=(150, 150, 150), width=2)
    d4.arc([575, 1005, 645, 1030], 180, 360, fill=(150, 150, 150), width=3)
    d4.line([(620, 985), (605, 1050)], fill=ACCENT_CORAL, width=4)
    d4.text((660, 1055), "Iced Coffee", fill=TEXT_DARK, font=font_small)

    # Silver Headphones
    d4.arc([750, 1020, 850, 1110], 180, 360, fill=(160, 165, 175), width=5)
    d4.ellipse([740, 1070, 770, 1135], fill=(200, 205, 215), outline=(120, 125, 135), width=2)
    d4.ellipse([830, 1070, 860, 1135], fill=(200, 205, 215), outline=(120, 125, 135), width=2)
    d4.text((875, 1090), "Headphones", fill=TEXT_DARK, font=font_small)

    draw_footer(d4, 4, "SWIPE ➔")
    p4_path = os.path.join(output_dir, "slide_4_accessories_flatlay.png")
    s4.save(p4_path, "PNG", quality=95)
    generated_slides.append(p4_path)

    # --- SLIDE 5: OUTRO & CTA (SPILL DI BIO) ---
    s5 = Image.new("RGB", (1080, 1350), color=BG_COLOR)
    d5 = ImageDraw.Draw(s5)
    draw_grid(d5)
    draw_header(d5, "SPILL DI BIO", 5)

    # Title: SPILL DI BIO.
    d5.text((60, 140), "SPILL DI BIO.", fill=TEXT_DARK, font=font_editorial_lg)
    d5.text((60, 225), "Simpan postingan ini buat inspirasi OOTD kamu besok! ✨", fill=TEXT_MUTED, font=font_body)

    # Polaroid photo in center
    pol_box = [200, 290, 880, 960]
    d5.rounded_rectangle(pol_box, radius=18, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw_washi_tape(d5, 485, 275)

    if os.path.exists(p1_img):
        im_outro = Image.open(p1_img).convert("RGB")
        paste_proportional(s5, im_outro, 220, 310, 640, 550)

    d5.text((250, 885), "#NeverJustOneThing ♡", fill=ACCENT_CORAL, font=font_doodle_lg)
    draw_doodle_heart(d5, 810, 915, "C & B")

    # 3 Action Pills
    pills = [
        ("🔖  SIMPAN LOOK", 60, 1000, 350),
        ("🔗  LINK DI BIO", 380, 1000, 680),
        ("💬  SHARE BESTIE", 710, 1000, 1020),
    ]
    for text, x1, y1, x2 in pills:
        d5.rounded_rectangle([x1, y1, x2, y1 + 75], radius=20, fill=(240, 236, 228), outline=BORDER_COLOR, width=1)
        d5.text((x1 + 35, y1 + 22), text, fill=TEXT_DARK, font=font_body_bold)

    # Bottom brand signature
    d5.rounded_rectangle([60, 1105, 1020, 1225], radius=20, fill=TEXT_DARK)

    d5.text((250, 885), "#NeverJustOneThing ♡", fill=ACCENT_CORAL, font=font_doodle_lg)
    draw_doodle_heart(d5, 810, 915, "C & B")

    # 3 Action Pills
    pills = [
        ("🔖  SIMPAN LOOK", 60, 1000, 350),
        ("🔗  LINK DI BIO", 380, 1000, 680),
        ("💬  SHARE BESTIE", 710, 1000, 1020),
    ]
    for text, x1, y1, x2 in pills:
        d5.rounded_rectangle([x1, y1, x2, y1 + 75], radius=20, fill=(240, 236, 228), outline=BORDER_COLOR, width=1)
        d5.text((x1 + 35, y1 + 22), text, fill=TEXT_DARK, font=font_body_bold)

    # Bottom brand signature
    d5.rounded_rectangle([60, 1105, 1020, 1225], radius=20, fill=TEXT_DARK)
    d5.text((100, 1130), "COLORBOX INDONESIA", fill=(255, 255, 255), font=font_body_bold)
    d5.text((100, 1172), "Available in stores & colorbox.co.id  •  #NeverJustOneThing", fill=(180, 180, 185), font=font_small)

    draw_footer(d5, 5, "TAP LINK IN BIO")
    p5_path = os.path.join(output_dir, "slide_5_outro_cta.png")
    s5.save(p5_path, "PNG", quality=95)
    generated_slides.append(p5_path)

    preview_html = generate_carousel_preview_html(output_dir, theme_title, headline)

    return {
        "slides": generated_slides,
        "output_dir": output_dir,
        "preview_html": preview_html
    }


def generate_carousel_preview_html(output_dir: str, title: str, subtitle: str, total_str: str = "") -> str:
    html_path = os.path.join(output_dir, "carousel_preview.html")
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Colorbox Carousel Live Preview — {title}</title>
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
    <div class="badge">LOOKBOOK FEED 4:5 — COLORBOX AI</div>
    <h1>Colorbox Carousel Live Preview</h1>
    <p class="desc">{title} • {subtitle}<br><span style="color: #cbd5e1; font-size: 13px;">Gaya: Playful, Y2K-inspired, scrapbook street style (@colorbox standard)</span></p>
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
      <p><b>colorboxindonesia</b> {title}: {subtitle}✨ Gak perlu pusing lagi pilih outfit besok pagi, padu padan resmi Colorbox ini siap bikin kamu tampil standout tapi tetap super comfy seharian! 💖</p>
      <div class="tags">#ColorboxIndonesia #NeverJustOneThing #CampusOOTD #GenZStyle #ColorboxBabes</div>
    </div>
  </div>

  <footer>
    Dirender otomatis oleh 5 AI Agents (Bimo, Meda, Raka, Bram, Vina) via Pegawai AI Engine (model: openai/gpt-image-2 via OpenCode Zen).
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
