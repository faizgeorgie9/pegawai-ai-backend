import os
import time
import json
from playwright.sync_api import sync_playwright

BASE_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing"
OUT_DIR = "d:/Users/IVANAGITA/aitoptrends/karyawan ai/output_graphic_tee"
os.makedirs(OUT_DIR, exist_ok=True)

# Pre-normalized paths with forward slashes
CBX_IMG_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images"
FUR_BG = f"{BASE_DIR}/render_modern/test_fur_bg.png".replace("\\", "/")
TEE_FRONT = f"{CBX_IMG_DIR}/cbx-21a-oversize-graphic-tee-lt-pink-front.jpg".replace("\\", "/")
TEE_DETAIL = f"{CBX_IMG_DIR}/cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg".replace("\\", "/")
TEE_FULL = f"{CBX_IMG_DIR}/cbx-21c-oversize-graphic-tee-lt-pink-full.jpg".replace("\\", "/")
TEE_BACK = f"{CBX_IMG_DIR}/cbx-21d-oversize-graphic-tee-lt-pink-back.jpg".replace("\\", "/")
JACKET_FRONT = f"{CBX_IMG_DIR}/cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg".replace("\\", "/")
DENIM_FRONT = f"{CBX_IMG_DIR}/cbx-02-high-waist-barrel-denim-black.jpg".replace("\\", "/")
SKIRT_FRONT = f"{CBX_IMG_DIR}/cbx-17a-jeans-overlap-micro-skirt-dark-navy-front.jpg".replace("\\", "/")
TOTE_FRONT = f"{CBX_IMG_DIR}/cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg".replace("\\", "/")
SLING_FRONT = f"{CBX_IMG_DIR}/cbx-19a-denim-sling-bag-denim-front.jpg".replace("\\", "/")

HTML_TEMPLATES = {
    # -------------------------------------------------------------
    # SLIDE 1: AESTHETIC COZY FUR FLATLAY (Asbhoel T-shirt style)
    # -------------------------------------------------------------
    "slide_1_cover_hero.png": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background-image: url('file:///{FUR_BG}');
    background-size: cover;
    background-position: center;
    position: relative;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  
  /* Minimalist Editorial Branding */
  .header-brand {{
    position: absolute; top: 60px; left: 0; right: 0;
    text-align: center; z-index: 20;
  }}
  .brand-sub {{
    font-size: 13px; font-weight: 700; letter-spacing: 5px;
    color: #8c7365; text-transform: uppercase; margin-bottom: 6px;
  }}
  .brand-title {{
    font-size: 20px; font-weight: 800; letter-spacing: 3px;
    color: #4a3429; text-transform: uppercase;
  }}
  
  /* The T-Shirt Centerpiece - 100% Proportional */
  .tee-container {{
    position: absolute;
    top: 52%; left: 50%;
    transform: translate(-50%, -50%) rotate(-1.5deg);
    width: 680px;
    height: auto;
    z-index: 10;
  }}
  .tee-container img {{
    width: 100%; height: auto; display: block;
    border-radius: 14px;
    filter: drop-shadow(0 25px 35px rgba(50, 30, 20, 0.28))
            drop-shadow(0 10px 15px rgba(50, 30, 20, 0.18));
  }}
  
  /* Prop 1: Retro Wireframe Glasses on Left */
  .prop-glasses {{
    position: absolute;
    top: 320px; left: 80px;
    width: 170px; height: 80px;
    z-index: 15;
    transform: rotate(-18deg);
    filter: drop-shadow(0 15px 18px rgba(60, 40, 30, 0.35));
  }}
  
  /* Prop 2: Delicate Glass Vase with Dried Baby's Breath on Right */
  .prop-vase {{
    position: absolute;
    bottom: 120px; right: 80px;
    width: 200px; height: 260px;
    z-index: 15;
    filter: drop-shadow(0 20px 25px rgba(60, 40, 30, 0.3));
  }}
  
  .bottom-tag {{
    position: absolute; bottom: 50px; left: 0; right: 0;
    text-align: center; font-size: 13px; letter-spacing: 4px;
    color: #9e8576; text-transform: uppercase; font-weight: 600;
  }}
</style>
</head>
<body>
  <div class="header-brand">
    <div class="brand-sub">COLORBOX ESSENTIALS</div>
    <div class="brand-title">MIAMI SUNSET CLUB • GRAPHIC TEE</div>
  </div>

  <div class="tee-container">
    <img src="file:///{TEE_DETAIL}" alt="Colorbox Graphic Tee Pink">
  </div>

  <div class="prop-glasses">
    <svg viewBox="0 0 170 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="45" cy="40" r="32" stroke="#d4af37" stroke-width="3" fill="rgba(255,255,255,0.15)"/>
      <circle cx="45" cy="40" r="31" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <circle cx="125" cy="40" r="32" stroke="#d4af37" stroke-width="3" fill="rgba(255,255,255,0.15)"/>
      <circle cx="125" cy="40" r="31" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <path d="M77 38 C 85 30, 95 30, 103 38" stroke="#d4af37" stroke-width="3.5" stroke-linecap="round"/>
      <path d="M13 38 L 2 30" stroke="#d4af37" stroke-width="3"/>
      <path d="M157 38 L 168 30" stroke="#d4af37" stroke-width="3"/>
    </svg>
  </div>

  <div class="prop-vase">
    <svg viewBox="0 0 200 260" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M100 130 Q 80 80, 50 30" stroke="#7a6250" stroke-width="2.5"/>
      <path d="M100 130 Q 110 70, 120 20" stroke="#7a6250" stroke-width="2"/>
      <path d="M100 130 Q 130 90, 160 40" stroke="#7a6250" stroke-width="2"/>
      <circle cx="50" cy="30" r="4.5" fill="#fdfbf7"/>
      <circle cx="42" cy="22" r="3.5" fill="#f7f2ea"/>
      <circle cx="58" cy="36" r="3" fill="#ffffff"/>
      <circle cx="68" cy="50" r="4" fill="#faf6ef"/>
      <circle cx="120" cy="20" r="4.5" fill="#ffffff"/>
      <circle cx="132" cy="28" r="3.5" fill="#fcf9f2"/>
      <circle cx="108" cy="32" r="4" fill="#f7f2ea"/>
      <circle cx="160" cy="40" r="4.5" fill="#ffffff"/>
      <circle cx="170" cy="48" r="3.5" fill="#f5eee3"/>
      <circle cx="148" cy="56" r="4" fill="#fdfbf7"/>
      <rect x="75" y="130" width="50" height="110" rx="16" fill="rgba(255,255,255,0.3)" stroke="rgba(255,255,255,0.7)" stroke-width="2"/>
      <rect x="88" y="112" width="24" height="20" rx="4" fill="rgba(255,255,255,0.3)" stroke="rgba(255,255,255,0.7)" stroke-width="2"/>
      <line x1="86" y1="112" x2="114" y2="112" stroke="rgba(255,255,255,0.8)" stroke-width="3"/>
      <line x1="78" y1="180" x2="122" y2="180" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>
    </svg>
  </div>

  <div class="bottom-tag">NATURAL COTTON • OVERSIZED FIT • MIAMI SUNSET</div>
</body>
</html>""",

    # -------------------------------------------------------------
    # SLIDE 2: SPLIT EDITORIAL + PINTEREST MOODBOARD ("Jakarta* Styled")
    # -------------------------------------------------------------
    "slide_2_hero_top.png": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #faf8f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    position: relative;
  }}
  
  .top-section {{
    width: 1080px; height: 640px; position: relative; overflow: hidden;
    background: #2b2320;
  }}
  .top-section img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center 25%;
    filter: brightness(0.96) contrast(1.04);
  }}
  .top-gradient {{
    position: absolute; inset: 0;
    background: linear-gradient(to bottom, rgba(0,0,0,0.35) 0%, transparent 40%, rgba(0,0,0,0.55) 100%);
  }}
  .top-title-box {{
    position: absolute; bottom: 35px; left: 50px; z-index: 10;
  }}
  .top-script {{
    font-family: "Georgia", serif; font-style: italic; font-size: 56px;
    color: #ffffff; text-shadow: 0 4px 18px rgba(0,0,0,0.5);
    line-height: 1.1; margin-bottom: 4px;
  }}
  .top-subtext {{
    font-size: 16px; font-weight: 700; letter-spacing: 3px;
    color: #f7e6dc; text-transform: uppercase;
  }}
  
  .bottom-section {{
    width: 1080px; height: 710px; position: relative;
    padding: 30px 60px;
    display: flex; flex-direction: column; justify-content: center;
  }}
  
  .moodboard-canvas {{
    position: relative; width: 960px; height: 630px; margin: 0 auto;
  }}
  
  .item-tee {{
    position: absolute; top: 20px; left: 40px; width: 340px; height: auto;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.09));
  }}
  .item-tee img {{ width: 100%; height: auto; display: block; border-radius: 12px; }}
  
  .item-bottom {{
    position: absolute; bottom: 20px; left: 45px; width: 320px; height: auto;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.09));
  }}
  .item-bottom img {{ width: 100%; height: auto; display: block; border-radius: 12px; }}
  
  .item-coffee {{
    position: absolute; top: 110px; left: 420px; width: 130px;
    filter: drop-shadow(0 10px 18px rgba(0,0,0,0.12));
  }}
  
  .item-sunglasses {{
    position: absolute; top: 40px; right: 80px; width: 220px;
    filter: drop-shadow(0 12px 20px rgba(0,0,0,0.14));
  }}
  
  .item-headphones {{
    position: absolute; top: 210px; right: 60px; width: 200px;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.12));
  }}
  
  .item-bag {{
    position: absolute; bottom: 30px; left: 410px; width: 250px; height: auto;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.1));
  }}
  .item-bag img {{ width: 100%; height: auto; display: block; border-radius: 12px; }}
  
  .item-shoes {{
    position: absolute; bottom: 40px; right: 70px; width: 170px;
    filter: drop-shadow(0 12px 20px rgba(0,0,0,0.12));
  }}
</style>
</head>
<body>
  <div class="top-section">
    <img src="file:///{TEE_FRONT}" alt="Model in Pink Tee">
    <div class="top-gradient"></div>
    <div class="top-title-box">
      <div class="top-script">Jakarta* Styled.</div>
      <div class="top-subtext">COLORBOX EDITORIAL LOOKBOOK • 26J</div>
    </div>
  </div>

  <div class="bottom-section">
    <div class="moodboard-canvas">
      <div class="item-tee">
        <img src="file:///{TEE_DETAIL}" alt="Pink Tee">
      </div>
      
      <div class="item-bottom">
        <img src="file:///{SKIRT_FRONT}" alt="Denim Skirt">
      </div>
      
      <div class="item-bag">
        <img src="file:///{SLING_FRONT}" alt="Denim Sling Bag">
      </div>
      
      <div class="item-coffee">
        <svg viewBox="0 0 130 230" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="65" y1="5" x2="65" y2="120" stroke="#1a1a1a" stroke-width="7" stroke-linecap="round"/>
          <ellipse cx="65" cy="55" rx="55" ry="12" fill="rgba(255,255,255,0.7)" stroke="#dcdde1" stroke-width="2"/>
          <path d="M15 55 Q 65 35, 115 55" fill="rgba(255,255,255,0.5)" stroke="#dcdde1" stroke-width="2"/>
          <path d="M18 55 L 32 205 Q 65 215, 98 205 L 112 55 Z" fill="rgba(255,255,255,0.25)" stroke="#dcdde1" stroke-width="2"/>
          <path d="M22 80 L 33 200 Q 65 210, 97 200 L 108 80 Q 65 92, 22 80 Z" fill="#633919"/>
          <rect x="42" y="95" width="26" height="26" rx="4" fill="rgba(255,255,255,0.4)" transform="rotate(12 42 95)"/>
          <rect x="68" y="130" width="28" height="28" rx="4" fill="rgba(255,255,255,0.4)" transform="rotate(-15 68 130)"/>
        </svg>
      </div>
      
      <div class="item-sunglasses">
        <svg viewBox="0 0 220 90" fill="none" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="60" cy="45" rx="48" ry="28" fill="#1e272e" stroke="#000000" stroke-width="4"/>
          <ellipse cx="160" cy="45" rx="48" ry="28" fill="#1e272e" stroke="#000000" stroke-width="4"/>
          <path d="M106 42 Q 110 38, 114 42" stroke="#000000" stroke-width="6" stroke-linecap="round"/>
          <path d="M35 32 Q 55 25, 75 32" stroke="rgba(255,255,255,0.3)" stroke-width="3" stroke-linecap="round"/>
          <path d="M135 32 Q 155 25, 175 32" stroke="rgba(255,255,255,0.3)" stroke-width="3" stroke-linecap="round"/>
        </svg>
      </div>
      
      <div class="item-headphones">
        <svg viewBox="0 0 200 220" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M35 120 C 35 40, 165 40, 165 120" stroke="#d2d7de" stroke-width="12" stroke-linecap="round"/>
          <path d="M48 100 C 48 55, 152 55, 152 100" stroke="#b0b8c4" stroke-width="3" stroke-dasharray="2,3"/>
          <rect x="18" y="110" width="36" height="60" rx="18" fill="#e4e7eb" stroke="#cbd0d8" stroke-width="3"/>
          <rect x="146" y="110" width="36" height="60" rx="18" fill="#e4e7eb" stroke="#cbd0d8" stroke-width="3"/>
          <rect x="30" y="118" width="14" height="44" rx="7" fill="#ffffff"/>
          <rect x="156" y="118" width="14" height="44" rx="7" fill="#ffffff"/>
        </svg>
      </div>
      
      <div class="item-shoes">
        <svg viewBox="0 0 170 90" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 65 Q 40 45, 90 48 Q 140 50, 155 60 Q 140 75, 80 75 Q 30 75, 15 65 Z" fill="#ffffff" stroke="#1e272e" stroke-width="2.5"/>
          <path d="M40 54 L 46 68" stroke="#1e272e" stroke-width="3"/>
          <path d="M60 50 L 68 72" stroke="#1e272e" stroke-width="3.5"/>
          <path d="M85 49 L 90 73" stroke="#1e272e" stroke-width="3"/>
          <path d="M110 52 L 118 70" stroke="#1e272e" stroke-width="3.5"/>
          <path d="M130 56 L 136 66" stroke="#1e272e" stroke-width="3"/>
        </svg>
      </div>
    </div>
  </div>
</body>
</html>""",

    # -------------------------------------------------------------
    # SLIDE 3: ON-MODEL DETAIL ZOOM CALLOUTS (Colorbox Official Style)
    # -------------------------------------------------------------
    "slide_3_bottom_pairing.png": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    position: relative;
    background: #e9e3dc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  
  .hero-full {{
    position: absolute; inset: 0; width: 100%; height: 100%;
    object-fit: cover; object-position: center 30%;
    filter: brightness(0.98) contrast(1.02);
  }}
  
  .callout-box {{
    position: absolute;
    border: 2.5px solid #fed330;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    background: #ffffff;
    overflow: hidden;
    z-index: 20;
  }}
  
  .box-1 {{
    top: 60px; left: 60px; width: 190px; height: 190px;
  }}
  .box-1 img {{
    width: 1080px; height: 1350px;
    position: absolute; top: -60px; left: -240px;
  }}
  
  .box-2 {{
    top: 500px; left: 50px; width: 220px; height: 220px;
  }}
  .box-2 img {{
    width: 1080px; height: 1350px;
    position: absolute; top: -420px; left: -210px;
  }}
  
  .box-3 {{
    top: 460px; right: 50px; width: 200px; height: 200px;
  }}
  .box-3 img {{
    width: 1080px; height: 1350px;
    position: absolute; top: -400px; left: -440px;
  }}
  
  .box-4 {{
    bottom: 80px; left: 60px; width: 210px; height: 210px;
  }}
  .box-4 img {{
    width: 1080px; height: 1350px;
    position: absolute; top: -680px; left: -260px;
  }}
  
  .svg-lines {{
    position: absolute; inset: 0; width: 1080px; height: 1350px;
    z-index: 15; pointer-events: none;
  }}
  
  .timestamp-tag {{
    position: absolute; bottom: 45px; right: 60px; z-index: 25;
    background: rgba(255,255,255,0.85); backdrop-filter: blur(8px);
    padding: 8px 18px; border-radius: 6px;
    font-size: 13px; font-weight: 700; letter-spacing: 2px;
    color: #2d2d34; border-left: 3px solid #fed330;
  }}
</style>
</head>
<body>
  <img class="hero-full" src="file:///{TEE_FULL}" alt="Full body Colorbox Pink Tee">

  <svg class="svg-lines" viewBox="0 0 1080 1350">
    <line x1="250" y1="155" x2="390" y2="170" stroke="#fed330" stroke-width="2" stroke-dasharray="5,3"/>
    <circle cx="390" cy="170" r="4" fill="#fed330"/>
    
    <line x1="270" y1="610" x2="370" y2="480" stroke="#fed330" stroke-width="2" stroke-dasharray="5,3"/>
    <circle cx="370" cy="480" r="4" fill="#fed330"/>
    
    <line x1="880" y1="560" x2="570" y2="470" stroke="#fed330" stroke-width="2" stroke-dasharray="5,3"/>
    <circle cx="570" cy="470" r="4" fill="#fed330"/>
    
    <line x1="270" y1="1185" x2="410" y2="760" stroke="#fed330" stroke-width="2" stroke-dasharray="5,3"/>
    <circle cx="410" cy="760" r="4" fill="#fed330"/>
  </svg>

  <div class="callout-box box-1">
    <img src="file:///{TEE_FRONT}">
  </div>

  <div class="callout-box box-2">
    <img src="file:///{TEE_DETAIL}">
  </div>

  <div class="callout-box box-3">
    <img src="file:///{TEE_FRONT}">
  </div>

  <div class="callout-box box-4">
    <img src="file:///{TEE_FULL}">
  </div>

  <div class="timestamp-tag">4:30 PM, GOLDEN HOUR SUN • COLORBOX</div>
</body>
</html>""",

    # -------------------------------------------------------------
    # SLIDE 4: EDITORIAL AMBIENT LOCATION SHOOT (Ceramic Studio style)
    # -------------------------------------------------------------
    "slide_4_accessories_layering.png": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    position: relative;
    background: #1c1815;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  
  .ambient-bg {{
    position: absolute; inset: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 70% 30%, #3e322a 0%, #1e1713 60%, #0d0a08 100%);
  }}
  
  .plate-wall {{
    position: absolute; inset: 0; width: 100%; height: 100%;
    opacity: 0.18; pointer-events: none;
    background-image: 
      radial-gradient(circle at 100px 150px, #ffffff 40px, transparent 41px),
      radial-gradient(circle at 260px 220px, #e8d0be 55px, transparent 56px),
      radial-gradient(circle at 120px 380px, #d1ccc0 45px, transparent 46px),
      radial-gradient(circle at 920px 180px, #ffffff 60px, transparent 61px),
      radial-gradient(circle at 980px 350px, #e8d0be 40px, transparent 41px),
      radial-gradient(circle at 860px 480px, #d1ccc0 50px, transparent 51px);
  }}
  
  .model-editorial {{
    position: absolute; bottom: 0; left: 50%;
    transform: translateX(-50%);
    width: 820px; height: 1180px;
    overflow: hidden;
  }}
  .model-editorial img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center top;
    border-radius: 20px 20px 0 0;
    box-shadow: 0 -15px 40px rgba(0,0,0,0.6);
  }}
  
  .vignette {{
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(13,10,8,0.85) 0%, transparent 40%, rgba(13,10,8,0.4) 100%);
    pointer-events: none;
  }}
  
  .top-left-label {{
    position: absolute; top: 50px; left: 60px; z-index: 30;
    color: #e5d2c5; font-size: 13px; font-weight: 700; letter-spacing: 4px;
    text-transform: uppercase;
  }}
  
  .bottom-editorial-box {{
    position: absolute; bottom: 50px; left: 60px; right: 60px; z-index: 30;
    display: flex; justify-content: space-between; align-items: flex-end;
  }}
  .ed-title {{
    font-family: "Georgia", serif; font-size: 38px; color: #ffffff;
    font-style: italic; line-height: 1.1; margin-bottom: 6px;
  }}
  .ed-desc {{
    font-size: 13px; font-weight: 600; letter-spacing: 2px; color: #c4b0a2; text-transform: uppercase;
  }}
  .ed-badge {{
    background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3); padding: 8px 18px; border-radius: 20px;
    color: #ffffff; font-size: 12px; font-weight: 800; letter-spacing: 2px;
  }}
</style>
</head>
<body>
  <div class="ambient-bg"></div>
  <div class="plate-wall"></div>
  
  <div class="top-left-label">COLORBOX STUDIO • ATMOSPHERIC EDITORIAL</div>

  <div class="model-editorial">
    <img src="file:///{TEE_FRONT}" alt="Model in Ambient Shoot">
  </div>
  
  <div class="vignette"></div>

  <div class="bottom-editorial-box">
    <div>
      <div class="ed-title">Casual Charm in Ambient Light</div>
      <div class="ed-desc">Light Pink Graphic Tee + Double Breasted Crop Jacket</div>
    </div>
    <div class="ed-badge">LOOK 04</div>
  </div>
</body>
</html>""",

    # -------------------------------------------------------------
    # SLIDE 5: PAPER-DOLL WARDROBE / GHOST MANNEQUIN (Colorbox Video style)
    # -------------------------------------------------------------
    "slide_5_outro_cta.png": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #fdf5f7;
    position: relative;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  
  .wardrobe-header {{
    position: absolute; top: 50px; left: 0; right: 0; text-align: center; z-index: 30;
  }}
  .w-subtitle {{
    font-size: 14px; font-weight: 800; letter-spacing: 4px; color: #d81b60; text-transform: uppercase; margin-bottom: 4px;
  }}
  .w-title {{
    font-size: 26px; font-weight: 900; color: #2d2d34; letter-spacing: 1px;
  }}

  .wardrobe-box {{
    position: absolute; top: 160px; right: 70px;
    width: 440px; height: 920px;
    z-index: 10;
  }}
  
  .sticker-col {{
    position: absolute; top: 170px; left: 70px; width: 440px; height: 920px;
    display: flex; flex-direction: column; justify-content: space-between;
    z-index: 20;
  }}
  
  .sticker-tee {{
    width: 320px; height: auto;
    filter: drop-shadow(0 10px 22px rgba(216, 27, 96, 0.22));
    border: 5px solid #ffffff; border-radius: 14px;
    background: #ffffff;
    transform: rotate(-3deg);
  }}
  .sticker-tee img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  
  .sticker-jacket {{
    width: 300px; height: auto;
    filter: drop-shadow(0 10px 22px rgba(216, 27, 96, 0.22));
    border: 5px solid #ffffff; border-radius: 14px;
    background: #ffffff;
    align-self: flex-end;
    transform: rotate(3deg);
  }}
  .sticker-jacket img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  
  .sticker-denim {{
    width: 280px; height: auto;
    filter: drop-shadow(0 10px 22px rgba(216, 27, 96, 0.22));
    border: 5px solid #ffffff; border-radius: 14px;
    background: #ffffff;
    transform: rotate(-2deg);
  }}
  .sticker-denim img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  
  .star {{
    position: absolute; z-index: 25; pointer-events: none;
  }}
  
  .poll-container {{
    position: absolute; bottom: 60px; left: 70px; right: 70px;
    background: #ffffff; border-radius: 20px;
    box-shadow: 0 10px 30px rgba(216, 27, 96, 0.14);
    border: 2px solid #ffd6e2; padding: 22px 30px;
    display: flex; align-items: center; justify-content: space-between;
    z-index: 30;
  }}
  .poll-question {{
    font-size: 17px; font-weight: 800; color: #2d2d34;
  }}
  .poll-question span {{ color: #d81b60; }}
  .poll-buttons {{ display: flex; gap: 14px; }}
  .btn-poll {{
    padding: 10px 22px; border-radius: 12px; font-size: 13px; font-weight: 800;
    cursor: pointer; text-transform: uppercase; letter-spacing: 1px;
  }}
  .btn-a {{ background: #fdf0f4; color: #d81b60; border: 1.5px solid #f8bbd0; }}
  .btn-b {{ background: #d81b60; color: #ffffff; border: 1.5px solid #d81b60; }}
</style>
</head>
<body>
  <div class="wardrobe-header">
    <div class="w-subtitle">YOUR NEXT OUTFIT IS WAITING</div>
    <div class="w-title">Tinggal Pilih Pieces Favoritmu & Make It Yours! ✨</div>
  </div>

  <div class="sticker-col">
    <div class="sticker-tee">
      <img src="file:///{TEE_DETAIL}" alt="Pink Tee">
    </div>
    
    <div class="sticker-jacket">
      <img src="file:///{JACKET_FRONT}" alt="Crop Jacket">
    </div>
    
    <div class="sticker-denim">
      <img src="file:///{DENIM_FRONT}" alt="Denim Pants">
    </div>
  </div>

  <div class="wardrobe-box">
    <svg viewBox="0 0 440 920" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="25" y="80" width="390" height="800" rx="20" fill="rgba(216,27,96,0.12)" filter="blur(15px)"/>
      <rect x="20" y="70" width="400" height="810" rx="22" fill="#ffdce5" stroke="#f48fb1" stroke-width="4"/>
      <path d="M20 90 Q 220 20, 420 90 Z" fill="#ffdce5" stroke="#f48fb1" stroke-width="4"/>
      <text x="220" y="65" text-anchor="middle" font-family="-apple-system, sans-serif" font-weight="900" font-size="22" fill="#d81b60" letter-spacing="6">COLORBOX</text>
      <rect x="36" y="100" width="176" height="760" rx="14" fill="#fff0f5" stroke="#f48fb1" stroke-width="3"/>
      <rect x="52" y="120" width="144" height="720" rx="8" fill="#ffdce5" stroke="#f8bbd0" stroke-width="2"/>
      <rect x="228" y="100" width="176" height="760" rx="14" fill="#fff0f5" stroke="#f48fb1" stroke-width="3"/>
      <rect x="244" y="120" width="144" height="720" rx="8" fill="#ffdce5" stroke="#f8bbd0" stroke-width="2"/>
      <rect x="180" y="450" width="22" height="60" rx="6" fill="#f48fb1" stroke="#d81b60" stroke-width="2"/>
      <rect x="238" y="450" width="22" height="60" rx="6" fill="#f48fb1" stroke="#d81b60" stroke-width="2"/>
      <text x="191" y="488" text-anchor="middle" font-weight="900" font-size="14" fill="#ffffff">C</text>
      <text x="249" y="488" text-anchor="middle" font-weight="900" font-size="14" fill="#ffffff">B</text>
      <rect x="45" y="876" width="30" height="26" rx="6" fill="#f48fb1"/>
      <rect x="365" y="876" width="30" height="26" rx="6" fill="#f48fb1"/>
    </svg>
  </div>

  <div class="star" style="top: 190px; left: 400px;">
    <svg width="40" height="40" viewBox="0 0 40 40">
      <path d="M20 0 L24 15 L39 20 L24 25 L20 40 L16 25 L1 20 L16 15 Z" fill="#ffd32a"/>
    </svg>
  </div>
  <div class="star" style="top: 520px; left: 30px;">
    <svg width="32" height="32" viewBox="0 0 40 40">
      <path d="M20 0 L24 15 L39 20 L24 25 L20 40 L16 25 L1 20 L16 15 Z" fill="#ff7675"/>
    </svg>
  </div>
  <div class="star" style="top: 760px; right: 40px;">
    <svg width="36" height="36" viewBox="0 0 40 40">
      <path d="M20 0 L24 15 L39 20 L24 25 L20 40 L16 25 L1 20 L16 15 Z" fill="#ffd32a"/>
    </svg>
  </div>

  <div class="poll-container">
    <div class="poll-question">Which piece caught your eye first? <span>👀</span></div>
    <div class="poll-buttons">
      <div class="btn-poll btn-a">A: Pink Graphic Tee</div>
      <div class="btn-poll btn-b">B: Crop Jacket Duo</div>
    </div>
  </div>
</body>
</html>"""
}

def render_carousel_slides():
    print("Starting Playwright to render 5 modern editorial slides...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        
        for filename, html in HTML_TEMPLATES.items():
            print(f"Rendering {filename}...")
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(1000)
            
            dest = os.path.join(OUT_DIR, filename)
            page.screenshot(path=dest)
            print(f"Saved: {dest}")
            
            # Also sync to secondary folders
            for sub in ["colorbox/marketing/output/carousel_latest", "backend/colorbox/marketing/output/carousel_latest", "frontend/frontend/public/output/carousel_latest"]:
                alt_dest = f"d:/Users/IVANAGITA/aitoptrends/hermes/{sub}/{filename}"
                os.makedirs(os.path.dirname(alt_dest), exist_ok=True)
                page.screenshot(path=alt_dest)
            
        browser.close()
    print("All 5 slides successfully rendered and synced!")

if __name__ == "__main__":
    render_carousel_slides()
