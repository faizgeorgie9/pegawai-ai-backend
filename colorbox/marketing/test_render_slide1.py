import os
import base64
from playwright.sync_api import sync_playwright

BASE_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing"
OUT_DIR = "d:/Users/IVANAGITA/aitoptrends/karyawan ai/output_graphic_tee"
CBX_IMG_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images"

def img_to_b64(path):
    with open(path, "rb") as f:
        mime = "image/png" if path.endswith(".png") else "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")

b64_fur = img_to_b64(f"{BASE_DIR}/render_modern/test_fur_bg.png")
b64_tee_detail = img_to_b64(f"{CBX_IMG_DIR}/cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg")

html_slide_1 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background-image: url('{b64_fur}');
    background-size: cover;
    background-position: center;
    position: relative;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  
  .header-brand {{
    position: absolute; top: 60px; left: 0; right: 0;
    text-align: center; z-index: 20;
  }}
  .brand-sub {{
    font-size: 13px; font-weight: 700; letter-spacing: 5px;
    color: #8c7365; text-transform: uppercase; margin-bottom: 6px;
  }}
  .brand-title {{
    font-size: 22px; font-weight: 800; letter-spacing: 3px;
    color: #4a3429; text-transform: uppercase;
  }}
  
  .tee-container {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-1.5deg);
    width: 650px;
    height: auto;
    z-index: 10;
  }}
  .tee-container img {{
    width: 100%; height: auto; display: block;
    border-radius: 18px;
    filter: drop-shadow(0 25px 35px rgba(50, 30, 20, 0.35))
            drop-shadow(0 10px 15px rgba(50, 30, 20, 0.2));
  }}
  
  .prop-glasses {{
    position: absolute;
    top: 360px; left: 60px;
    width: 180px; height: 85px;
    z-index: 15;
    transform: rotate(-18deg);
    filter: drop-shadow(0 15px 18px rgba(60, 40, 30, 0.35));
  }}
  
  .prop-vase {{
    position: absolute;
    bottom: 120px; right: 70px;
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
    <img src="{b64_tee_detail}" alt="Colorbox Graphic Tee Pink">
  </div>

  <div class="prop-glasses">
    <svg viewBox="0 0 170 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="45" cy="40" r="32" stroke="#d4af37" stroke-width="3.5" fill="rgba(255,255,255,0.2)"/>
      <circle cx="45" cy="40" r="31" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <circle cx="125" cy="40" r="32" stroke="#d4af37" stroke-width="3.5" fill="rgba(255,255,255,0.2)"/>
      <circle cx="125" cy="40" r="31" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <path d="M77 38 C 85 30, 95 30, 103 38" stroke="#d4af37" stroke-width="4" stroke-linecap="round"/>
      <path d="M13 38 L 2 30" stroke="#d4af37" stroke-width="3.5"/>
      <path d="M157 38 L 168 30" stroke="#d4af37" stroke-width="3.5"/>
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
      <rect x="75" y="130" width="50" height="110" rx="16" fill="rgba(255,255,255,0.4)" stroke="rgba(255,255,255,0.8)" stroke-width="2.5"/>
      <rect x="88" y="112" width="24" height="20" rx="4" fill="rgba(255,255,255,0.4)" stroke="rgba(255,255,255,0.8)" stroke-width="2.5"/>
      <line x1="86" y1="112" x2="114" y2="112" stroke="rgba(255,255,255,0.9)" stroke-width="3"/>
      <line x1="78" y1="180" x2="122" y2="180" stroke="rgba(255,255,255,0.6)" stroke-width="2"/>
    </svg>
  </div>

  <div class="bottom-tag">NATURAL COTTON • OVERSIZED FIT • MIAMI SUNSET</div>
</body>
</html>"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
    page.set_content(html_slide_1, wait_until="networkidle")
    page.wait_for_timeout(1000)
    dest = os.path.join(OUT_DIR, "slide_1_cover_hero.png")
    page.screenshot(path=dest)
    browser.close()
    print("Test slide 1 rendered to:", dest)
