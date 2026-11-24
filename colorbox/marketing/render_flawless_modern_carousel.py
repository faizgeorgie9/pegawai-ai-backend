import os
import base64
from playwright.sync_api import sync_playwright

BASE_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing"
OUT_DIR = "d:/Users/IVANAGITA/aitoptrends/karyawan ai/output_graphic_tee"
os.makedirs(OUT_DIR, exist_ok=True)

CBX_IMG_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images"
USER_UPLOAD_DIR = "C:/Users/IVANAGITA/.gemini/antigravity/brain/289c4273-5463-4a74-9663-80a73fc092a8/.user_uploaded"

def img_to_b64(path):
    with open(path, "rb") as f:
        mime = "image/png" if path.endswith(".png") else "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")

print("Encoding assets to base64...")
b64_fur_bg = img_to_b64(f"{BASE_DIR}/render_modern/test_fur_bg.png")
b64_clean_tee = img_to_b64(f"{BASE_DIR}/clean_folded_tee.png")
b64_tee_front = img_to_b64(f"{CBX_IMG_DIR}/cbx-21a-oversize-graphic-tee-lt-pink-front.jpg")
b64_tee_full = img_to_b64(f"{CBX_IMG_DIR}/cbx-21c-oversize-graphic-tee-lt-pink-full.jpg")
b64_jacket = img_to_b64(f"{CBX_IMG_DIR}/cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg")
b64_denim = img_to_b64(f"{CBX_IMG_DIR}/cbx-02-high-waist-barrel-denim-black.jpg")
b64_skirt = img_to_b64(f"{CBX_IMG_DIR}/cbx-17a-jeans-overlap-micro-skirt-dark-navy-front.jpg")
b64_sling = img_to_b64(f"{CBX_IMG_DIR}/cbx-19a-denim-sling-bag-denim-front.jpg")

# User reference authentic photoshoot images
b64_user_callout = img_to_b64(f"{USER_UPLOAD_DIR}/media_1795504141514_8405a635.jpg")
b64_user_ceramic = img_to_b64(f"{USER_UPLOAD_DIR}/media_1795504154172_021f554c.png")
b64_user_split = img_to_b64(f"{USER_UPLOAD_DIR}/media_1795504189114_398a90a2.jpg")

print("All assets encoded!")

SLIDES = {
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
    background-image: url('{b64_fur_bg}');
    background-size: cover;
    background-position: center;
    position: relative;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  
  .header-brand {{
    position: absolute; top: 70px; left: 0; right: 0;
    text-align: center; z-index: 20;
  }}
  .brand-sub {{
    font-size: 13px; font-weight: 700; letter-spacing: 6px;
    color: #8c7365; text-transform: uppercase; margin-bottom: 6px;
  }}
  .brand-title {{
    font-size: 24px; font-weight: 800; letter-spacing: 3px;
    color: #4a3429; text-transform: uppercase;
  }}
  
  /* The Pristine Flatlay Folded Tee */
  .tee-container {{
    position: absolute;
    top: 51%; left: 50%;
    transform: translate(-50%, -50%) rotate(-1.5deg);
    width: 630px;
    height: auto;
    z-index: 10;
  }}
  .tee-container img {{
    width: 100%; height: auto; display: block;
    border-radius: 20px;
    filter: drop-shadow(0 28px 40px rgba(50, 30, 20, 0.32))
            drop-shadow(0 10px 18px rgba(50, 30, 20, 0.2));
  }}
  
  /* Prop 1: Retro Wireframe Glasses */
  .prop-glasses {{
    position: absolute;
    top: 350px; left: 70px;
    width: 180px; height: 85px;
    z-index: 15;
    transform: rotate(-18deg);
    filter: drop-shadow(0 15px 18px rgba(60, 40, 30, 0.35));
  }}
  
  /* Prop 2: Delicate Glass Vase with Dried Flowers */
  .prop-vase {{
    position: absolute;
    bottom: 120px; right: 80px;
    width: 200px; height: 260px;
    z-index: 15;
    filter: drop-shadow(0 20px 25px rgba(60, 40, 30, 0.3));
  }}
  
  .bottom-tag {{
    position: absolute; bottom: 55px; left: 0; right: 0;
    text-align: center; font-size: 13px; letter-spacing: 5px;
    color: #8c7365; text-transform: uppercase; font-weight: 700;
  }}
</style>
</head>
<body>
  <div class="header-brand">
    <div class="brand-sub">COLORBOX • SUMMER DROP</div>
    <div class="brand-title">MIAMI SUNSET CLUB • GRAPHIC TEE</div>
  </div>

  <div class="tee-container">
    <img src="{b64_clean_tee}" alt="Colorbox Graphic Tee Pink">
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
  
  /* Top Half: Cinematic Lifestyle On-Model */
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
    background: linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, transparent 40%, rgba(0,0,0,0.6) 100%);
  }}
  .top-title-box {{
    position: absolute; bottom: 35px; left: 50px; z-index: 10;
  }}
  .top-script {{
    font-family: "Georgia", serif; font-style: italic; font-size: 58px;
    color: #ffffff; text-shadow: 0 4px 18px rgba(0,0,0,0.5);
    line-height: 1.1; margin-bottom: 4px;
  }}
  .top-subtext {{
    font-size: 16px; font-weight: 700; letter-spacing: 3px;
    color: #f7e6dc; text-transform: uppercase;
  }}
  
  /* Bottom Half: Clean Pinterest Moodboard Grid */
  .bottom-section {{
    width: 1080px; height: 710px; position: relative;
    padding: 30px 60px;
    display: flex; flex-direction: column; justify-content: center;
  }}
  
  .moodboard-canvas {{
    position: relative; width: 960px; height: 630px; margin: 0 auto;
  }}
  
  .item-tee {{
    position: absolute; top: 20px; left: 40px; width: 330px; height: auto;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.09));
  }}
  .item-tee img {{ width: 100%; height: auto; display: block; border-radius: 14px; }}
  
  .item-bottom {{
    position: absolute; bottom: 20px; left: 45px; width: 320px; height: auto;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.09));
  }}
  .item-bottom img {{ width: 100%; height: auto; display: block; border-radius: 14px; }}
  
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
  .item-bag img {{ width: 100%; height: auto; display: block; border-radius: 14px; }}
  
  .item-shoes {{
    position: absolute; bottom: 40px; right: 70px; width: 170px;
    filter: drop-shadow(0 12px 20px rgba(0,0,0,0.12));
  }}
</style>
</head>
<body>
  <div class="top-section">
    <img src="{b64_tee_front}" alt="Model in Pink Tee">
    <div class="top-gradient"></div>
    <div class="top-title-box">
      <div class="top-script">Jakarta* Styled.</div>
      <div class="top-subtext">COLORBOX EDITORIAL LOOKBOOK • 26J</div>
    </div>
  </div>

  <div class="bottom-section">
    <div class="moodboard-canvas">
      <div class="item-tee">
        <img src="{b64_clean_tee}" alt="Pink Tee">
      </div>
      
      <div class="item-bottom">
        <img src="{b64_skirt}" alt="Denim Skirt">
      </div>
      
      <div class="item-bag">
        <img src="{b64_sling}" alt="Denim Sling Bag">
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
    border: 3px solid #fed330;
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
    background: rgba(255,255,255,0.88); backdrop-filter: blur(8px);
    padding: 8px 18px; border-radius: 6px;
    font-size: 13px; font-weight: 700; letter-spacing: 2px;
    color: #2d2d34; border-left: 3px solid #fed330;
  }}
</style>
</head>
<body>
  <img class="hero-full" src="{b64_tee_full}" alt="Full body Colorbox Pink Tee">

  <svg class="svg-lines" viewBox="0 0 1080 1350">
    <line x1="250" y1="155" x2="390" y2="170" stroke="#fed330" stroke-width="2.5" stroke-dasharray="5,3"/>
    <circle cx="390" cy="170" r="4.5" fill="#fed330"/>
    
    <line x1="270" y1="610" x2="370" y2="480" stroke="#fed330" stroke-width="2.5" stroke-dasharray="5,3"/>
    <circle cx="370" cy="480" r="4.5" fill="#fed330"/>
    
    <line x1="880" y1="560" x2="570" y2="470" stroke="#fed330" stroke-width="2.5" stroke-dasharray="5,3"/>
    <circle cx="570" cy="470" r="4.5" fill="#fed330"/>
    
    <line x1="270" y1="1185" x2="410" y2="760" stroke="#fed330" stroke-width="2.5" stroke-dasharray="5,3"/>
    <circle cx="410" cy="760" r="4.5" fill="#fed330"/>
  </svg>

  <div class="callout-box box-1">
    <img src="{b64_tee_front}">
  </div>

  <div class="callout-box box-2">
    <img src="{b64_clean_tee}">
  </div>

  <div class="callout-box box-3">
    <img src="{b64_tee_front}">
  </div>

  <div class="callout-box box-4">
    <img src="{b64_tee_full}">
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
    background: #0d0a08;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  
  /* Authentic Editorial Ambient Photo from Colorbox */
  .hero-ambient {{
    position: absolute; inset: 0; width: 100%; height: 100%;
    object-fit: cover; object-position: center 20%;
    filter: brightness(0.96) contrast(1.05);
  }}
  
  .vignette {{
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(13,10,8,0.85) 0%, transparent 40%, rgba(13,10,8,0.3) 100%);
    pointer-events: none;
  }}
  
  .top-left-label {{
    position: absolute; top: 60px; left: 60px; z-index: 30;
    color: #e5d2c5; font-size: 13px; font-weight: 700; letter-spacing: 4px;
    text-transform: uppercase;
  }}
  
  .bottom-editorial-box {{
    position: absolute; bottom: 55px; left: 60px; right: 60px; z-index: 30;
    display: flex; justify-content: space-between; align-items: flex-end;
  }}
  .ed-title {{
    font-family: "Georgia", serif; font-size: 42px; color: #ffffff;
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
  <img class="hero-ambient" src="{b64_user_ceramic}" alt="Model in Ceramic Pottery Studio">
  
  <div class="vignette"></div>
  <div class="top-left-label">COLORBOX STUDIO • ATMOSPHERIC EDITORIAL</div>

  <div class="bottom-editorial-box">
    <div>
      <div class="ed-title">Casual Charm in Ambient Light</div>
      <div class="ed-desc">Layered Street Styling • Colorbox Collection</div>
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
    position: absolute; top: 55px; left: 0; right: 0; text-align: center; z-index: 30;
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
    width: 310px; height: auto;
    filter: drop-shadow(0 10px 22px rgba(216, 27, 96, 0.22));
    border: 5px solid #ffffff; border-radius: 14px;
    background: #ffffff;
    transform: rotate(-3deg);
  }}
  .sticker-tee img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  
  .sticker-jacket {{
    width: 290px; height: auto;
    filter: drop-shadow(0 10px 22px rgba(216, 27, 96, 0.22));
    border: 5px solid #ffffff; border-radius: 14px;
    background: #ffffff;
    align-self: flex-end;
    transform: rotate(3deg);
  }}
  .sticker-jacket img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  
  .sticker-denim {{
    width: 270px; height: auto;
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
      <img src="{b64_clean_tee}" alt="Pink Tee">
    </div>
    
    <div class="sticker-jacket">
      <img src="{b64_jacket}" alt="Crop Jacket">
    </div>
    
    <div class="sticker-denim">
      <img src="{b64_denim}" alt="Denim Pants">
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

def render_all():
    print("Launching Playwright to render all 5 slides...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        
        for name, html in SLIDES.items():
            print(f"Rendering {name}...")
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(1000)
            
            dest = os.path.join(OUT_DIR, name)
            page.screenshot(path=dest)
            print(f"Saved: {dest}")
            
            # Sync to all target folders
            for sub in [
                "colorbox/marketing/output/carousel_latest",
                "backend/colorbox/marketing/output/carousel_latest",
                "frontend/frontend/public/output/carousel_latest"
            ]:
                alt_dest = f"d:/Users/IVANAGITA/aitoptrends/hermes/{sub}/{name}"
                os.makedirs(os.path.dirname(alt_dest), exist_ok=True)
                page.screenshot(path=alt_dest)
                
            # Brain artifact folder
            brain_dest = f"C:/Users/IVANAGITA/.gemini/antigravity/brain/289c4273-5463-4a74-9663-80a73fc092a8/output_graphic_tee/{name}"
            os.makedirs(os.path.dirname(brain_dest), exist_ok=True)
            page.screenshot(path=brain_dest)
            
        browser.close()
    print("All 5 slides successfully rendered and synced everywhere!")

if __name__ == "__main__":
    render_all()
