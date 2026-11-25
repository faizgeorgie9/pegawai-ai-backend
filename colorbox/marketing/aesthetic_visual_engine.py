import os
import sys
import base64
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = ROOT_DIR / "backend" / "colorbox" / "colorbox-knowledge" / "images"
if not IMAGES_DIR.exists():
    IMAGES_DIR = ROOT_DIR / "colorbox" / "colorbox-knowledge" / "images"

def img_to_b64(path):
    if not path or not os.path.exists(path):
        return ""
    mime = "image/png" if str(path).lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")

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

    p_name = prod.get("name", "").lower()
    pid = prod.get("id", "").lower()
    img_files = list(Path(images_dir).glob("*.jpg")) + list(Path(images_dir).glob("*.png"))
    
    # Direct match on tokens
    tokens = [t for t in p_name.replace("-", " ").split() if len(t) > 3]
    best_match = None
    best_score = 0
    for f in img_files:
        fn = f.name.lower()
        score = sum(1 for t in tokens if t in fn)
        if pid and pid in fn:
            score += 5
        if score > best_score:
            best_score = score
            best_match = str(f)
            
    if best_match:
        return best_match
    
    # Fallback to first available image
    return str(img_files[0]) if img_files else ""

def render_aesthetic_carousel(
    theme_title: str,
    headline: str,
    subtitle: str,
    products_info: list[dict],
    output_dir: str,
    images_dir: str = str(IMAGES_DIR),
    day_num: int = 1
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir)

    p1 = products_info[0] if len(products_info) > 0 else {}
    p2 = products_info[1] if len(products_info) > 1 else {}
    p3 = products_info[2] if len(products_info) > 2 else {}

    p1_name = p1.get("name", "Colorbox Hero Piece")
    p1_color = p1.get("color", "Classic")
    p1_price = p1.get("price", "Rp 299.900")
    p1_img_b64 = img_to_b64(find_product_image(p1, images_dir, "front"))
    p1_det_b64 = img_to_b64(find_product_image(p1, images_dir, "detail")) or p1_img_b64

    p2_name = p2.get("name", "Pairing Piece")
    p2_color = p2.get("color", "Neutral")
    p2_price = p2.get("price", "Rp 199.900")
    p2_img_b64 = img_to_b64(find_product_image(p2, images_dir, "front"))

    p3_name = p3.get("name", "Daily Accessory")
    p3_img_b64 = img_to_b64(find_product_image(p3, images_dir, "front"))

    generated_slides = []

    # HTML TEMPLATES FOR 5 EDITORIAL PINTEREST SLIDES (1080 x 1350 px)
    # ZERO-TEXT ON IMAGE (Clean, high-fashion aesthetic)
    
    # -------------------------------------------------------------
    # SLIDE 1: SPLIT EDITORIAL / HERO IMPACT
    # -------------------------------------------------------------
    html_s1 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #F9F7F4;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, serif;
    position: relative;
  }}
  .hero-canvas {{
    width: 100%; height: 100%; position: relative;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 60px 70px;
  }}
  .brand-pill {{
    display: flex; align-items: center; justify-content: space-between;
  }}
  .brand-name {{
    font-size: 24px; font-weight: 800; letter-spacing: 4px; color: #1A1A1A; text-transform: uppercase;
  }}
  .tag-capsule {{
    font-size: 15px; font-weight: 600; letter-spacing: 2px; color: #8C827A; text-transform: uppercase;
  }}
  .center-stage {{
    width: 940px; height: 980px; position: relative;
    border-radius: 28px; overflow: hidden;
    background: #ffffff;
    box-shadow: 0 20px 50px rgba(0,0,0,0.06);
    display: flex; align-items: center; justify-content: center;
  }}
  .center-img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center;
  }}
  .aesthetic-bottom {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0;
  }}
  .curated-label {{
    font-family: "Georgia", serif; font-style: italic; font-size: 26px; color: #4A4440;
  }}
  .subtle-tag {{
    font-size: 14px; font-weight: 700; color: #E05342; letter-spacing: 2px;
  }}
</style>
</head>
<body>
  <div class="hero-canvas">
    <div class="brand-pill">
      <span class="brand-name">COLORBOX</span>
      <span class="tag-capsule">OOTD LOOKBOOK // 01</span>
    </div>
    <div class="center-stage">
      <img class="center-img" src="{p1_img_b64}" />
    </div>
    <div class="aesthetic-bottom">
      <span class="curated-label">Never Just One Thing</span>
      <span class="subtle-tag">#NEVERJUSTONETHING</span>
    </div>
  </div>
</body></html>"""

    # -------------------------------------------------------------
    # SLIDE 2: DETAIL ZOOM & TEXTURE CALLOUTS
    # -------------------------------------------------------------
    html_s2 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, serif;
    position: relative;
  }}
  .container {{
    width: 100%; height: 100%; padding: 60px 70px;
    display: flex; flex-direction: column; justify-content: space-between;
  }}
  .header {{
    display: flex; justify-content: space-between; align-items: center;
  }}
  .title-script {{
    font-family: "Georgia", serif; font-style: italic; font-size: 34px; color: #1F1D1D;
  }}
  .stage-grid {{
    width: 940px; height: 1040px; display: flex; gap: 24px; position: relative;
  }}
  .main-shot {{
    flex: 1.2; height: 100%; border-radius: 24px; overflow: hidden;
    background: #FAF8F5; box-shadow: 0 16px 40px rgba(0,0,0,0.05);
  }}
  .main-shot img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center;
  }}
  .detail-col {{
    flex: 0.9; display: flex; flex-direction: column; gap: 24px; height: 100%;
  }}
  .detail-box {{
    flex: 1; border-radius: 20px; overflow: hidden; background: #FAF8F5;
    box-shadow: 0 12px 30px rgba(0,0,0,0.04); position: relative;
  }}
  .detail-box img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center;
  }}
  .callout-badge {{
    position: absolute; bottom: 20px; left: 20px;
    background: rgba(255,255,255,0.92); backdrop-filter: blur(8px);
    padding: 8px 16px; border-radius: 12px; font-size: 14px; font-weight: 700; color: #2B2625;
    letter-spacing: 1px;
  }}
  .footer-sub {{
    font-size: 14px; color: #9E9690; letter-spacing: 2px; text-transform: uppercase;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="title-script">Focus on Details</span>
      <span class="footer-sub">Craftsmanship & Texture</span>
    </div>
    <div class="stage-grid">
      <div class="main-shot">
        <img src="{p1_img_b64}" />
      </div>
      <div class="detail-col">
        <div class="detail-box">
          <img src="{p1_det_b64}" />
          <div class="callout-badge">FIT & TAILORING</div>
        </div>
        <div class="detail-box">
          <img src="{p1_det_b64}" style="transform: scale(1.35);" />
          <div class="callout-badge">WEAVE & TEXTURE</div>
        </div>
      </div>
    </div>
    <div class="footer-sub">
      COLORBOX OFFICIAL ARCHIVE // {p1_color.upper()}
    </div>
  </div>
</body></html>"""

    # -------------------------------------------------------------
    # SLIDE 3: MIX & MATCH STYLING FORMULA
    # -------------------------------------------------------------
    html_s3 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #F7F5F0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, serif;
  }}
  .container {{
    width: 100%; height: 100%; padding: 60px 70px;
    display: flex; flex-direction: column; justify-content: space-between;
  }}
  .header {{
    display: flex; justify-content: space-between; align-items: baseline;
  }}
  .hero-script {{
    font-family: "Georgia", serif; font-style: italic; font-size: 38px; color: #1A1A1A;
  }}
  .sub-tag {{
    font-size: 14px; font-weight: 700; letter-spacing: 3px; color: #A69E96; text-transform: uppercase;
  }}
  .duo-stage {{
    width: 940px; height: 1030px; display: flex; gap: 28px;
  }}
  .duo-card {{
    flex: 1; height: 100%; border-radius: 26px; overflow: hidden;
    background: #ffffff; box-shadow: 0 18px 45px rgba(0,0,0,0.06);
    display: flex; flex-direction: column;
  }}
  .duo-img-box {{
    flex: 1; width: 100%; position: relative; overflow: hidden;
  }}
  .duo-img-box img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center;
  }}
  .duo-caption {{
    padding: 24px 28px; background: #ffffff;
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid rgba(0,0,0,0.04);
  }}
  .duo-name {{
    font-size: 17px; font-weight: 700; color: #1F1D1D; text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .duo-role {{
    font-size: 13px; font-weight: 600; color: #8F8781;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="hero-script">The Styling Formula</span>
      <span class="sub-tag">Harmonious Pairing</span>
    </div>
    <div class="duo-stage">
      <div class="duo-card">
        <div class="duo-img-box">
          <img src="{p1_img_b64}" />
        </div>
        <div class="duo-caption">
          <span class="duo-name">Key Piece</span>
          <span class="duo-role">{p1_color}</span>
        </div>
      </div>
      <div class="duo-card">
        <div class="duo-img-box">
          <img src="{p2_img_b64 or p1_det_b64}" />
        </div>
        <div class="duo-caption">
          <span class="duo-name">Coordination</span>
          <span class="duo-role">{p2_color}</span>
        </div>
      </div>
    </div>
    <div style="font-size: 14px; color: #A69E96; letter-spacing: 1.5px; text-transform: uppercase;">
      Colorbox Collection · Designed for Self-Expression
    </div>
  </div>
</body></html>"""

    # -------------------------------------------------------------
    # SLIDE 4: AESTHETIC PINTEREST FLATLAY / ACCESSORIES
    # -------------------------------------------------------------
    html_s4 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #F5EFEB;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, serif;
    position: relative;
  }}
  .container {{
    width: 100%; height: 100%; padding: 60px 70px;
    display: flex; flex-direction: column; justify-content: space-between;
  }}
  .top-row {{
    display: flex; justify-content: space-between; align-items: baseline;
  }}
  .title-script {{
    font-family: "Georgia", serif; font-style: italic; font-size: 36px; color: #2E2825;
  }}
  .flatlay-board {{
    width: 940px; height: 1040px; position: relative;
    border-radius: 30px; overflow: hidden;
    background: #FAF8F5;
    box-shadow: 0 20px 50px rgba(0,0,0,0.06);
    display: flex; flex-direction: column; padding: 40px; gap: 30px;
  }}
  .flatlay-top {{
    flex: 1.3; width: 100%; display: flex; gap: 24px;
  }}
  .flatlay-bottom {{
    flex: 1; width: 100%; display: flex; gap: 24px;
  }}
  .photo-frame {{
    flex: 1; height: 100%; border-radius: 20px; overflow: hidden;
    background: #FFFFFF; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
  }}
  .photo-frame img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center;
  }}
  .footer-row {{
    display: flex; justify-content: space-between; font-size: 14px;
    color: #9C9189; letter-spacing: 2px; text-transform: uppercase;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="top-row">
      <span class="title-script">Everyday Essentials</span>
      <span style="font-size:14px; letter-spacing:2px; font-weight:700; color:#857B74;">OOTD PALETTE</span>
    </div>
    <div class="flatlay-board">
      <div class="flatlay-top">
        <div class="photo-frame">
          <img src="{p1_img_b64}" />
        </div>
        <div class="photo-frame">
          <img src="{p2_img_b64 or p1_det_b64}" />
        </div>
      </div>
      <div class="flatlay-bottom">
        <div class="photo-frame">
          <img src="{p3_img_b64 or p1_det_b64}" />
        </div>
        <div class="photo-frame" style="display:flex; align-items:center; justify-content:center; background:#F4EEE8; padding:30px;">
          <div style="text-align:center;">
            <div style="font-family:'Georgia',serif; font-style:italic; font-size:28px; color:#3B3430; margin-bottom:8px;">Effortless Chic</div>
            <div style="font-size:13px; font-weight:700; letter-spacing:2px; color:#A69B92;">#NEVERJUSTONETHING</div>
          </div>
        </div>
      </div>
    </div>
    <div class="footer-row">
      <span>Colorbox Wardrobe</span>
      <span>Daily In-Situ Lookbook</span>
    </div>
  </div>
</body></html>"""

    # -------------------------------------------------------------
    # SLIDE 5: WARDROBE CAPSULE / OUTRO
    # -------------------------------------------------------------
    html_s5 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #F9F7F4;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, serif;
  }}
  .container {{
    width: 100%; height: 100%; padding: 70px;
    display: flex; flex-direction: column; justify-content: space-between;
    align-items: center; text-align: center;
  }}
  .top-brand {{
    font-size: 26px; font-weight: 800; letter-spacing: 5px; color: #1A1A1A;
  }}
  .center-capsule {{
    width: 900px; display: flex; flex-direction: column; align-items: center; gap: 36px;
  }}
  .capsule-headline {{
    font-family: "Georgia", serif; font-size: 48px; color: #1F1D1D; line-height: 1.2;
  }}
  .trio-row {{
    display: flex; gap: 24px; width: 100%; justify-content: center;
  }}
  .trio-thumb {{
    width: 260px; height: 350px; border-radius: 20px; overflow: hidden;
    background: #ffffff; box-shadow: 0 14px 35px rgba(0,0,0,0.06);
  }}
  .trio-thumb img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center;
  }}
  .outro-cta {{
    font-family: "Georgia", serif; font-style: italic; font-size: 28px; color: #706863;
  }}
  .link-pill {{
    background: #1A1A1A; color: #ffffff; padding: 14px 36px;
    border-radius: 30px; font-size: 16px; font-weight: 700; letter-spacing: 2px;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="top-brand">COLORBOX</div>
    <div class="center-capsule">
      <div class="capsule-headline">Never Just One Thing</div>
      <div class="trio-row">
        <div class="trio-thumb"><img src="{p1_img_b64}" /></div>
        <div class="trio-thumb"><img src="{p2_img_b64 or p1_det_b64}" /></div>
        <div class="trio-thumb"><img src="{p3_img_b64 or p1_img_b64}" /></div>
      </div>
      <div class="outro-cta">Find your favorite fit at colorbox.co.id</div>
    </div>
    <div class="link-pill">LINK IN BIO @COLORBOX_ID</div>
  </div>
</body></html>"""

    # RENDER VIA PLAYWRIGHT
    slides_html = [
        ("slide_1_cover_hero.png", html_s1),
        ("slide_2_hero_top.png", html_s2),
        ("slide_3_bottom_pairing.png", html_s3),
        ("slide_4_accessories_flatlay.png", html_s4),
        ("slide_5_outro_cta.png", html_s5),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for sname, shtml in slides_html:
            spath = out_path / sname
            page = browser.new_page(viewport={"width": 1080, "height": 1350})
            page.set_content(shtml)
            page.screenshot(path=str(spath))
            page.close()
            generated_slides.append(str(spath))
        browser.close()

    # Mirror slide_4 to slide_4_accessories_layering.png
    shutil.copyfile(str(out_path / "slide_4_accessories_flatlay.png"), str(out_path / "slide_4_accessories_layering.png"))

    # Generate interactive HTML preview
    preview_path = out_path / "carousel_preview.html"
    preview_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Colorbox Editorial Lookbook — {p1_name}</title>
<style>
  body {{ margin:0; background:#121214; color:#fff; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display:flex; flex-direction:column; align-items:center; padding:40px 20px; }}
  h1 {{ font-size:24px; font-weight:700; margin-bottom:8px; text-align:center; }}
  p {{ color:#888; font-size:14px; margin-bottom:30px; text-align:center; }}
  .carousel-wrap {{ display:flex; gap:20px; overflow-x:auto; max-width:100%; padding-bottom:20px; }}
  .slide-card {{ flex:0 0 340px; background:#1c1c20; border-radius:18px; overflow:hidden; box-shadow:0 12px 30px rgba(0,0,0,0.5); }}
  .slide-card img {{ width:100%; height:425px; object-fit:cover; display:block; }}
  .caption {{ padding:14px; font-size:13px; font-weight:600; color:#ccc; }}
</style>
</head>
<body>
  <h1>{p1_name} ({p1_color})</h1>
  <p>Editorial Lookbook Feed Carousel (4:5 Portrait) · Zero-Text on Visual Standard</p>
  <div class="carousel-wrap">
    <div class="slide-card"><img src="slide_1_cover_hero.png"><div class="caption">Slide 1: Hero Cover Impact</div></div>
    <div class="slide-card"><img src="slide_2_hero_top.png"><div class="caption">Slide 2: Craftsmanship & Detail Zoom</div></div>
    <div class="slide-card"><img src="slide_3_bottom_pairing.png"><div class="caption">Slide 3: Mix & Match Styling Formula</div></div>
    <div class="slide-card"><img src="slide_4_accessories_flatlay.png"><div class="caption">Slide 4: Aesthetic Flatlay & In-Situ</div></div>
    <div class="slide-card"><img src="slide_5_outro_cta.png"><div class="caption">Slide 5: Capsule Wardrobe Outro</div></div>
  </div>
</body></html>"""
    preview_path.write_text(preview_html, encoding="utf-8")

    return {
        "success": True,
        "slides": generated_slides,
        "html_preview": str(preview_path)
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
