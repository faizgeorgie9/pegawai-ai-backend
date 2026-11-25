import os
import sys
import base64
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

_CUR = Path(__file__).resolve().parent

def _find_knowledge_subdir(subdir: str) -> Path | None:
    for base in [
        _CUR / "colorbox" / "colorbox-knowledge",
        _CUR / "backend" / "colorbox" / "colorbox-knowledge",
        _CUR.parent / "colorbox-knowledge",
        _CUR.parent / "colorbox" / "colorbox-knowledge",
        _CUR.parent / "backend" / "colorbox" / "colorbox-knowledge",
        _CUR.parent.parent / "colorbox" / "colorbox-knowledge",
        _CUR.parent.parent / "backend" / "colorbox" / "colorbox-knowledge",
        Path("colorbox/colorbox-knowledge").resolve(),
        Path("backend/colorbox/colorbox-knowledge").resolve(),
    ]:
        cand = base / subdir
        if cand.exists():
            return cand
    return None

IMAGES_DIR = _find_knowledge_subdir("images") or _find_knowledge_subdir("IMAGES")
BACKGROUND_DIR = _find_knowledge_subdir("background")
GRAPHICS_DIR = _find_knowledge_subdir("graphics")

def img_to_b64(path):
    if not path or not os.path.exists(path):
        return ""
    mime = "image/png" if str(path).lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")

def remove_studio_background_to_b64(path: str) -> str:
    """
    Removes uniform light/studio background connected to image borders using
    flood-fill + morphological edge feathering, returning a transparent PNG data URI.
    Preserves interior highlights/white inner garments not connected to the border.
    """
    if not path or not os.path.exists(path):
        return ""
    try:
        import io
        import numpy as np
        from PIL import Image, ImageFilter
        from scipy import ndimage

        im = Image.open(path).convert("RGBA")
        arr = np.array(im, dtype=np.float32)
        rgb = arr[:, :, :3]
        h, w = rgb.shape[:2]

        # Sample border pixels (top, left, right) to estimate studio backdrop color
        border_pixels = np.concatenate([
            rgb[0, :, :],
            rgb[1, :, :],
            rgb[:, 0, :],
            rgb[:, -1, :],
        ], axis=0)
        bg_color = np.median(border_pixels, axis=0)

        # Studio backdrop is neutral (low chroma) and bright/grey, including soft floor shadows
        dist = np.linalg.norm(rgb - bg_color, axis=2)
        chroma = np.max(rgb, axis=2) - np.min(rgb, axis=2)
        luma = np.mean(rgb, axis=2)
        is_bg_candidate = (dist < 46.0) | ((chroma < 20.0) & (luma > 180.0))

        # Keep only background regions connected to the outer border (4-connectivity)
        # so white inner shirts / buttons inside the model are preserved!
        border_seed = np.zeros((h, w), dtype=bool)
        border_seed[0, :] = is_bg_candidate[0, :]
        border_seed[-1, :] = is_bg_candidate[-1, :]
        border_seed[:, 0] = is_bg_candidate[:, 0]
        border_seed[:, -1] = is_bg_candidate[:, -1]

        bg_mask = ndimage.binary_propagation(border_seed, mask=is_bg_candidate)

        # Slightly expand mask by 1px to eat white studio fringe, then feather alpha
        bg_mask_dilated = ndimage.binary_dilation(bg_mask, iterations=1)
        alpha = np.where(bg_mask_dilated, 0.0, 255.0).astype(np.uint8)
        alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=1.2))

        out_arr = np.array(im)
        out_arr[:, :, 3] = np.array(alpha_img)
        out_im = Image.fromarray(out_arr, mode="RGBA")

        buf = io.BytesIO()
        out_im.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"[Remove Studio BG Warning]: {e}")
        return img_to_b64(path)

def get_product_pov_map(prod: dict, images_dir=IMAGES_DIR) -> dict[str, str]:
    """
    Discovers all available POV angles ('front', 'back', 'detail', 'side') for a product
    so each carousel slide uses the most appropriate POV instead of repeating one angle.
    """
    povs: dict[str, str] = {}
    if not prod or not images_dir:
        return povs
    angles = prod.get("angles", {})
    if isinstance(angles, dict):
        for ang in ("front", "back", "detail", "side"):
            fn = angles.get(ang)
            if fn:
                cand = Path(images_dir) / fn
                if cand.exists():
                    povs[ang] = str(cand)

    # Scan images_dir if any angle is missing
    pid = str(prod.get("id") or "").lower()
    p_name = str(prod.get("name") or "").lower()
    tokens = [t for t in p_name.replace("-", " ").split() if len(t) > 3]
    img_files = list(Path(images_dir).glob("*.jpg")) + list(Path(images_dir).glob("*.png"))
    for ang in ("front", "back", "detail", "side"):
        if ang in povs:
            continue
        best_path = ""
        best_score = 0
        for f in img_files:
            fn = f.name.lower()
            hits = sum(1 for t in tokens if t in fn)
            if pid and pid in fn:
                hits += 5
            if hits == 0:
                continue
            ang_match = (
                (ang in fn)
                or (ang == "front" and "-a-" in fn)
                or (ang == "back" and "-b-" in fn)
                or (ang == "detail" and ("-c-" in fn or "close" in fn or "texture" in fn))
            )
            if ang_match:
                score = hits + 10
                if score > best_score:
                    best_score = score
                    best_path = str(f)
        if best_path:
            povs[ang] = best_path
    return povs

def select_accent_color(prod: dict) -> tuple[str, str]:
    """Selects dynamic --accent-dynamic from sistem-desain-carousel-modular.md based on product color/mood."""
    color = str(prod.get("color") or "").upper()
    name = str(prod.get("name") or "").lower()
    if any(k in color for k in ["BROWN", "CORAL", "RED", "TERRACOTTA"]) or "denim" in name:
        return "#B85A3A", "Terracotta"
    if any(k in color for k in ["NAVY", "BLUE", "DENIM"]):
        return "#1F5CE6", "Cobalt"
    if any(k in color for k in ["OLIVE", "GREEN", "FOREST"]):
        return "#2E473B", "Forest"
    if any(k in color for k in ["PINK", "LILAC", "ECRU", "WHITE"]):
        return "#F3C6CF", "Blush"
    return "#B85A3A", "Terracotta"

def select_background_asset(prod: dict, bg_dir: Path | None = BACKGROUND_DIR) -> tuple[str, str]:
    """Selects a matching [SLOT_BG_ASSET] from Folder Aset Background based on product category & color."""
    if not bg_dir or not bg_dir.exists():
        return "", ""
    cat = str(prod.get("category") or "").lower()
    color = str(prod.get("color") or "").upper()
    name = str(prod.get("name") or "").lower()

    # Priority preference list based on silhouette contrast & mood
    if "denim" in name or "jacket" in name or "outerwear" in cat:
        prefs = ["aesthetic-street.jpg", "street.jpg", "monochrome-strairs.jpg", "cafee.jpg", "minimalist.jpg"]
    elif any(k in color for k in ["BLACK", "DARK NAVY", "DARK BROWN"]):
        prefs = ["white-clean.jpg", "minimalist.jpg", "cafee.jpg", "aesthetic-street.jpg"]
    elif any(k in color for k in ["ECRU", "OFF WHITE", "WHITE"]):
        prefs = ["doores.jpg", "blue-street.jpg", "infront-of-grocerys.jpg", "street.jpg"]
    else:
        prefs = ["minimalist.jpg", "cafee.jpg", "mall.jpg", "white-clean.jpg"]

    for p_fn in prefs:
        cand = bg_dir / p_fn
        if cand.exists():
            return str(cand), p_fn
    all_bgs = sorted(list(bg_dir.glob("*.jpg")) + list(bg_dir.glob("*.png")))
    if all_bgs:
        return str(all_bgs[0]), all_bgs[0].name
    return "", ""

def select_graphic_asset(preferred_names: list[str], graphics_dir: Path | None = GRAPHICS_DIR) -> str:
    """Selects a graphic overlay asset from Folder Graphics."""
    if not graphics_dir or not graphics_dir.exists():
        return ""
    for fn in preferred_names:
        cand = graphics_dir / fn
        if cand.exists():
            return str(cand)
    all_g = sorted(list(graphics_dir.glob("*.png")) + list(graphics_dir.glob("*.jpg")))
    return str(all_g[0]) if all_g else ""

def find_product_image(prod, images_dir=IMAGES_DIR, prefer_angle="front"):
    if not prod:
        return ""
    angles = prod.get("angles", {})
    if isinstance(angles, dict) and angles.get(prefer_angle):
        candidate = Path(images_dir) / angles[prefer_angle]
        if candidate.exists():
            return str(candidate)
        for ang in ["front", "detail", "back", "side"]:
            if angles.get(ang):
                c = Path(images_dir) / angles[ang]
                if c.exists():
                    return str(c)

    p_name = str(prod.get("name") or "").lower()
    pid = str(prod.get("id") or "").lower()
    img_files = list(Path(images_dir).glob("*.jpg")) + list(Path(images_dir).glob("*.png"))
    
    # Direct match on tokens with prefer_angle boost
    tokens = [t for t in p_name.replace("-", " ").split() if len(t) > 3]
    pa = (prefer_angle or "").lower()
    best_match = None
    best_score = -1
    for f in img_files:
        fn = f.name.lower()
        token_hits = sum(1 for t in tokens if t in fn)
        if not token_hits and pid not in fn:
            continue
        score = token_hits
        if pid and pid in fn:
            score += 5
        if pa:
            if pa in fn:
                score += 10
            elif pa == "detail" and any(k in fn for k in ["detail", "-c-", "close", "texture"]):
                score += 10
            elif pa == "front" and any(k in fn for k in ["front", "-a-"]):
                score += 10
            elif pa == "back" and any(k in fn for k in ["back", "-b-"]):
                score += 10
            elif pa == "side" and any(k in fn for k in ["side", "profile"]):
                score += 10
        if score > best_score:
            best_score = score
            best_match = str(f)
            
    if best_match and best_score > 0:
        return best_match
    
    # Fallback to angle matching alone or first available image
    if img_files:
        if pa:
            for f in img_files:
                fn = f.name.lower()
                if pa in fn or (pa == "detail" and "-c-" in fn) or (pa == "front" and "-a-" in fn):
                    return str(f)
        return str(img_files[0])
    return ""

def render_aesthetic_carousel(
    theme_title: str,
    headline: str,
    subtitle: str,
    products_info: list[dict],
    output_dir: str,
    images_dir: str = str(IMAGES_DIR),
    day_num: int = 1,
    num_slides: int = 3
) -> dict:
    """
    Renders 1-3 modular 1080x1350 px (4:5) Instagram Carousel slides following
    the updated sistem-desain-carousel-modular.md:
    - Model photos have studio background REMOVED and are composited directly
      onto [SLOT_BG_ASSET] (full-bleed, NO white-box collage).
    - 1-3 slides only, NO CTA slide.
    - Minimized text: 1-4 words editorial micro-copy only.
    - Distinct POV per slide (front, detail, back/second-angle).
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir)

    for old_slide in out_path.glob("slide_*.png"):
        try:
            old_slide.unlink()
        except Exception:
            pass

    p1 = products_info[0] if len(products_info) > 0 else {}
    p1_name = p1.get("name", "Hero Collection")
    p1_color = p1.get("color", "Classic")

    p1_povs = get_product_pov_map(p1, images_dir)
    p1_front = p1_povs.get("front") or find_product_image(p1, images_dir, "front")
    p1_back = p1_povs.get("back") or p1_povs.get("side") or p1_front
    p1_detail = p1_povs.get("detail") or p1_back or p1_front

    # Remove studio background for in-situ model compositing!
    p1_front_cutout_b64 = remove_studio_background_to_b64(p1_front)
    p1_back_cutout_b64 = remove_studio_background_to_b64(p1_back) or p1_front_cutout_b64
    p1_detail_b64 = img_to_b64(p1_detail) or p1_front_cutout_b64

    bg_path, bg_name = select_background_asset(p1)
    bg_b64 = img_to_b64(bg_path)
    accent_hex, accent_name = select_accent_color(p1)

    effective_slides = max(1, min(int(num_slides or 3), 3))

    # Minimalist micro-copy (1-4 words max, zero clutter, zero CTA)
    micro_s1 = "structured, <i>effortless.</i>"
    micro_s2 = "contrast stitch" if "contrast" in p1_name.lower() else "detail"
    micro_s3 = "everyday layer"

    base_css = f"""
      @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;1,500&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{
        width: 1080px; height: 1350px; overflow: hidden;
        background: #F4EFEA;
        font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
        position: relative;
      }}
      .bg-full {{
        position: absolute; inset: 0; width: 100%; height: 100%;
        object-fit: cover; object-position: center; z-index: 0;
        filter: contrast(0.96) brightness(0.95);
      }}
      .model-cutout {{
        position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
        height: 92%; width: auto; max-width: 106%;
        object-fit: contain; z-index: 2;
        filter: drop-shadow(0 18px 36px rgba(20, 14, 12, 0.28));
      }}
      .detail-full {{
        position: absolute; inset: 0; width: 100%; height: 100%;
        object-fit: cover; object-position: center; z-index: 1;
      }}
      .micro-copy {{
        position: absolute; z-index: 5;
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 46px; font-weight: 500; letter-spacing: -0.01em;
        color: #FAF7F2;
        text-shadow: 0 3px 18px rgba(0, 0, 0, 0.55);
      }}
      .micro-copy i {{ font-style: italic; }}
      .micro-pill {{
        position: absolute; z-index: 5;
        background: rgba(244, 239, 234, 0.88);
        color: #231916;
        border: 1px solid rgba(35, 25, 22, 0.45);
        border-radius: 999px;
        padding: 8px 18px;
        font-size: 18px; font-weight: 500; letter-spacing: 0.04em;
        text-transform: lowercase;
      }}
      .bracket {{
        position: absolute; z-index: 4;
        width: 44px; height: 44px;
        border-color: #F4D03F; border-style: solid; border-width: 0;
      }}
    """

    html_s1 = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}</style></head>
<body>
  <img class="bg-full" src="{bg_b64}" />
  <img class="model-cutout" src="{p1_front_cutout_b64}" />
  <div class="micro-copy" style="top: 72px; left: 68px;">{micro_s1}</div>
</body></html>"""

    html_s2 = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}</style></head>
<body>
  <img class="detail-full" src="{p1_detail_b64}" />
  <div class="bracket" style="top: 320px; left: 260px; border-top-width: 3px; border-left-width: 3px;"></div>
  <div class="bracket" style="top: 320px; right: 260px; border-top-width: 3px; border-right-width: 3px;"></div>
  <div class="bracket" style="bottom: 320px; left: 260px; border-bottom-width: 3px; border-left-width: 3px;"></div>
  <div class="bracket" style="bottom: 320px; right: 260px; border-bottom-width: 3px; border-right-width: 3px;"></div>
  <div class="micro-pill" style="bottom: 72px; left: 68px;">{micro_s2}</div>
</body></html>"""

    html_s3 = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}</style></head>
<body>
  <img class="bg-full" src="{bg_b64}" />
  <img class="model-cutout" src="{p1_back_cutout_b64}" />
  <div class="micro-copy" style="top: 72px; left: 68px;">{micro_s3}</div>
</body></html>"""

    all_slides = [
        ("slide_1_cover_hero.png", html_s1, "Slide 1: In-Situ Front POV (Removed BG)"),
        ("slide_2_hero_top.png", html_s2, "Slide 2: Macro Detail POV"),
        ("slide_3_bottom_pairing.png", html_s3, "Slide 3: In-Situ Second Angle POV (Removed BG)"),
    ]
    slides_to_render = all_slides[:effective_slides]

    generated_slides = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for sname, shtml, _ in slides_to_render:
            spath = out_path / sname
            page = browser.new_page(viewport={"width": 1080, "height": 1350})
            page.set_content(shtml)
            page.screenshot(path=str(spath))
            page.close()
            generated_slides.append(str(spath))
        browser.close()

    slide_cards_html = "\n".join([
        f'    <div class="slide-card"><img src="{sname}"><div class="caption">{stitle}</div></div>'
        for sname, _, stitle in slides_to_render
    ])

    preview_path = out_path / "carousel_preview.html"
    preview_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Colorbox In-Situ Lookbook — {p1_name}</title>
<style>
  body {{ margin:0; background:#121214; color:#fff; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display:flex; flex-direction:column; align-items:center; padding:40px 20px; }}
  h1 {{ font-size:24px; font-weight:700; margin-bottom:8px; text-align:center; }}
  p {{ color:#aaa; font-size:14px; margin-bottom:30px; text-align:center; }}
  .carousel-wrap {{ display:flex; gap:20px; overflow-x:auto; max-width:100%; padding-bottom:20px; }}
  .slide-card {{ flex:0 0 340px; background:#1c1c20; border-radius:18px; overflow:hidden; box-shadow:0 12px 30px rgba(0,0,0,0.5); }}
  .slide-card img {{ width:100%; height:425px; object-fit:cover; display:block; }}
  .caption {{ padding:14px; font-size:13px; font-weight:600; color:#ccc; }}
</style>
</head>
<body>
  <h1>{p1_name} ({p1_color})</h1>
  <p>In-Situ Cutout Lookbook (BG Removed) · Background: {bg_name} · {effective_slides} Slides · Minimal Micro-Copy</p>
  <div class="carousel-wrap">
{slide_cards_html}
  </div>
</body></html>"""
    preview_path.write_text(preview_html, encoding="utf-8")

    return {
        "success": True,
        "slides": generated_slides,
        "html_preview": str(preview_path),
        "bg_asset": bg_name,
        "accent": f"{accent_name} ({accent_hex})",
        "povs_used": list(p1_povs.keys()),
    }

def render_dynamic_ugc_video(
    hero_product: dict,
    secondary_product: dict,
    output_dir: str,
    images_dir: str = str(IMAGES_DIR),
    theme_title: str = None
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir)

    p1 = hero_product or {}
    p2 = secondary_product or {}

    p1_name = p1.get("name", "Colorbox Piece")
    p1_price = p1.get("price", "Rp 299.900")
    p1_color = p1.get("color", "Classic")
    p1_img_b64 = img_to_b64(find_product_image(p1, images_dir, "front"))

    p2_name = p2.get("name", "Layer Piece")
    p2_price = p2.get("price", "Rp 199.900")
    p2_color = p2.get("color", "Chic")
    p2_img_b64 = img_to_b64(find_product_image(p2, images_dir, "front")) or p1_img_b64

    # HTML 9:16 VERTICAL VIDEO ANIMATION (720 x 1280 px)
    html_video = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  body {{
    width: 720px; height: 1280px; background: #121012;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow: hidden; color: white; position: relative;
  }}
  .stage {{
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  }}
  .scene-1 {{
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: linear-gradient(135deg, #F9F0EE 0%, #FAF6F3 100%);
    animation: fadeOutScene1 0.6s ease forwards 3.3s;
  }}
  .model-card {{
    width: 580px; height: 850px; background: white; border-radius: 36px;
    box-shadow: 0 25px 60px rgba(0,0,0,0.12); overflow: hidden; position: relative;
    transform: scale(0.95); animation: zoomHero 3.2s ease forwards;
  }}
  .model-img {{ width: 100%; height: 100%; object-fit: cover; object-position: center; }}
  .badge-tag {{
    position: absolute; top: 24px; left: 24px;
    background: rgba(255,255,255,0.95); backdrop-filter: blur(8px);
    color: #E05342; padding: 10px 22px; border-radius: 20px;
    font-size: 19px; font-weight: 800; letter-spacing: 0.5px;
  }}
  .price-tag {{
    position: absolute; bottom: 24px; right: 24px;
    background: #E05342; color: white; padding: 10px 22px;
    border-radius: 20px; font-size: 20px; font-weight: 800;
  }}
  .scene-2 {{
    position: absolute; inset: 0; background: linear-gradient(135deg, #F4F1EA 0%, #FAF8F5 100%);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    opacity: 0; animation: fadeInScene2 0.6s ease forwards 3.3s;
  }}
  .layer-card {{
    width: 580px; height: 850px; background: white; border-radius: 36px;
    box-shadow: 0 25px 60px rgba(0,0,0,0.12); overflow: hidden; position: relative;
    animation: pulseGrid 3.2s ease forwards 3.3s;
  }}
  .ui-overlay {{ position: absolute; inset: 0; pointer-events: none; z-index: 10; }}
  .top-bar {{
    position: absolute; top: 45px; left: 40px; right: 40px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .user-pill {{
    display: flex; align-items: center; gap: 12px;
    background: rgba(0,0,0,0.55); backdrop-filter: blur(10px);
    padding: 8px 18px; border-radius: 24px;
  }}
  .avatar {{
    width: 38px; height: 38px; border-radius: 50%; background: #E05342;
    display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 16px;
  }}
  .username {{ font-size: 20px; font-weight: 700; }}
  .follow-btn {{
    background: #E05342; color: white; border-radius: 14px;
    padding: 4px 12px; font-size: 15px; font-weight: 700;
  }}
  .actions-col {{
    position: absolute; right: 32px; bottom: 180px;
    display: flex; flex-direction: column; align-items: center; gap: 28px;
  }}
  .action-item {{ display: flex; flex-direction: column; align-items: center; gap: 6px; }}
  .action-icon {{
    width: 58px; height: 58px; border-radius: 50%; background: rgba(0,0,0,0.45);
    backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; font-size: 28px;
  }}
  .action-label {{ font-size: 16px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.6); }}
  .bottom-info {{
    position: absolute; bottom: 45px; left: 40px; right: 120px;
    display: flex; flex-direction: column; gap: 12px;
  }}
  .caption-title {{
    font-size: 23px; font-weight: 800; color: #1A1A1A; background: rgba(255,255,255,0.92);
    padding: 8px 18px; border-radius: 14px; width: fit-content;
  }}
  .caption-desc {{
    font-size: 18px; font-weight: 600; color: #FFFFFF; text-shadow: 0 2px 8px rgba(0,0,0,0.85); line-height: 1.4;
  }}
  .music-tag {{
    display: flex; align-items: center; gap: 8px; font-size: 16px; color: #FFFFFF;
    background: rgba(0,0,0,0.5); padding: 6px 14px; border-radius: 18px; width: fit-content;
  }}
  @keyframes zoomHero {{ 0% {{ transform: scale(0.95); }} 100% {{ transform: scale(1.02); }} }}
  @keyframes fadeOutScene1 {{ 0% {{ opacity: 1; }} 100% {{ opacity: 0; pointer-events: none; }} }}
  @keyframes fadeInScene2 {{ 0% {{ opacity: 0; transform: scale(0.95); }} 100% {{ opacity: 1; transform: scale(1); }} }}
  @keyframes pulseGrid {{ 0% {{ transform: scale(0.95); }} 100% {{ transform: scale(1.03); }} }}
</style>
</head>
<body>
  <div class="stage">
    <div class="scene-1">
      <div class="model-card">
        <img class="model-img" src="{p1_img_b64}" />
        <div class="badge-tag">{p1_name[:24].upper()} ✨</div>
        <div class="price-tag">{p1_price}</div>
      </div>
    </div>
    <div class="scene-2">
      <div class="layer-card">
        <img class="model-img" src="{p2_img_b64}" />
        <div class="badge-tag">PAIR WITH {p2_name[:18].upper()} 💖</div>
        <div class="price-tag">{p2_price}</div>
      </div>
    </div>
  </div>

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
        <span class="action-label">24.8K</span>
      </div>
      <div class="action-item">
        <div class="action-icon">💬</div>
        <span class="action-label">742</span>
      </div>
      <div class="action-item">
        <div class="action-icon">🔖</div>
        <span class="action-label">2.1K</span>
      </div>
      <div class="action-item">
        <div class="action-icon">↗</div>
        <span class="action-label">Share</span>
      </div>
    </div>

    <div class="bottom-info">
      <div class="caption-title">{p1_name[:30]} OOTD ✨</div>
      <div class="caption-desc">Spill styling fit {p1_name} ({p1_color}) buat ngampus & hangout! Padukan sama {p2_name} biar look makin standout 🌸 #NeverJustOneThing #ColorboxBabes</div>
      <div class="music-tag">♫ Colorbox Original Audio • Trending Beats</div>
    </div>
  </div>
</body></html>"""

    temp_html = out_path / "temp_dynamic_video.html"
    temp_html.write_text(html_video, encoding="utf-8")

    rec_dir = out_path / "temp_rec"
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
        time.sleep(6.5)
        page.close()
        context.close()
        browser.close()

    vids = list(rec_dir.glob("*.webm")) + list(rec_dir.glob("*.mp4"))
    target_mp4 = out_path / "ugc_video.mp4"
    target_webm = out_path / "ugc_video.webm"
    if vids:
        src_vid = vids[-1]
        shutil.copyfile(str(src_vid), str(target_webm))
        shutil.copyfile(str(src_vid), str(target_mp4))
        # Also sync to graphic tee alias so backward-compat works
        shutil.copyfile(str(src_vid), str(out_path / "ugc_video_graphic_tee.mp4"))

    # Cleanup temp recording dir
    shutil.rmtree(str(rec_dir), ignore_errors=True)
    if temp_html.exists():
        temp_html.unlink()

    return str(target_mp4)

if __name__ == "__main__":
    print("Testing aesthetic_visual_engine...")
    test_prod = {
        "name": "Double Pocket Flared Denim Pants",
        "color": "LT. GREY",
        "price": "Rp 299.900",
        "category": "Bottoms / Denim",
        "angles": {"front": "cbx-05-double-pocket-flared-denim-grey.jpg"}
    }
    test_second = {
        "name": "Double Breasted Crop Jacket",
        "color": "LT. GREY",
        "price": "Rp 329.900",
        "angles": {"front": "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg"}
    }
    test_third = {
        "name": "Denim Sling Bag",
        "color": "DENIM",
        "price": "Rp 129.900",
        "angles": {"front": "cbx-19a-denim-sling-bag-denim-front.jpg"}
    }
    out = "backend/colorbox/marketing/output/carousel_latest"
    res = render_aesthetic_carousel("Editorial Denim Lookbook", test_prod["name"], "Colorbox", [test_prod, test_second, test_third], out)
    print("Carousel result:", res)
    vid_res = render_dynamic_ugc_video(test_prod, test_second, out)
    print("Video result:", vid_res)
