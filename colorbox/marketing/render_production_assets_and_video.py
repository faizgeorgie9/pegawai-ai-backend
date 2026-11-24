import os
import base64
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\backend\colorbox\marketing")
OUT_DIR = Path(r"d:\Users\IVANAGITA\aitoptrends\karyawan ai\output_graphic_tee")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CBX_IMG_DIR = Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\backend\colorbox\colorbox-knowledge\images")
USER_UPLOAD_DIR = Path(r"C:\Users\IVANAGITA\.gemini\antigravity\brain\289c4273-5463-4a74-9663-80a73fc092a8\.user_uploaded")

def img_to_b64(path):
    with open(path, "rb") as f:
        mime = "image/png" if str(path).endswith(".png") else "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")

print("Encoding assets...")
b64_clean_tee = img_to_b64(BASE_DIR / "clean_folded_tee.png")
b64_tee_front = img_to_b64(CBX_IMG_DIR / "cbx-21a-oversize-graphic-tee-lt-pink-front.jpg")
b64_skirt = img_to_b64(BASE_DIR / "skirt_cutout.png")
b64_jacket = img_to_b64(CBX_IMG_DIR / "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg")
b64_denim = img_to_b64(CBX_IMG_DIR / "cbx-02-high-waist-barrel-denim-black.jpg")
b64_tee_full = img_to_b64(CBX_IMG_DIR / "cbx-21c-oversize-graphic-tee-lt-pink-full.jpg")

# 1. RENDER SLIDE 2 WITH REFINED PINTEREST LAYOUT
html_slide_2 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1350px; overflow: hidden;
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    position: relative;
  }}
  
  .top-section {{
    width: 1080px; height: 650px; position: relative; overflow: hidden;
    background: #2b2320;
  }}
  .top-section img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center 25%;
    filter: brightness(0.96) contrast(1.04);
  }}
  .top-gradient {{
    position: absolute; inset: 0;
    background: linear-gradient(to bottom, rgba(0,0,0,0.25) 0%, transparent 40%, rgba(0,0,0,0.6) 100%);
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
  
  .bottom-section {{
    width: 1080px; height: 700px; position: relative;
    padding: 30px 50px;
    background: #faf8f5;
  }}
  
  .moodboard-canvas {{
    position: relative; width: 980px; height: 640px; margin: 0 auto;
  }}
  
  .item-tee {{
    position: absolute; top: 15px; left: 30px; width: 280px;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.08));
  }}
  .item-tee img {{ width: 100%; height: auto; display: block; border-radius: 14px; }}
  
  .item-skirt {{
    position: absolute; bottom: 25px; left: 30px; width: 280px;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.08));
  }}
  .item-skirt img {{ width: 100%; height: auto; display: block; border-radius: 14px; }}
  
  .item-coffee {{
    position: absolute; top: 30px; left: 390px; width: 140px;
    filter: drop-shadow(0 12px 20px rgba(0,0,0,0.12));
  }}
  
  /* Chic Slouchy Shoulder Bag (Center Bottom) */
  .item-bag {{
    position: absolute; bottom: 25px; left: 340px; width: 250px; height: 260px;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.14));
  }}
  
  .item-sunglasses {{
    position: absolute; top: 35px; right: 40px; width: 220px;
    filter: drop-shadow(0 12px 20px rgba(0,0,0,0.14));
  }}
  
  .item-headphones {{
    position: absolute; top: 170px; right: 50px; width: 190px;
    filter: drop-shadow(0 14px 22px rgba(0,0,0,0.12));
  }}
  
  .item-shoes {{
    position: absolute; bottom: 45px; right: 55px; width: 170px;
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
      <!-- Pink Tee -->
      <div class="item-tee">
        <img src="{b64_clean_tee}" alt="Pink Tee">
      </div>
      
      <!-- Denim Skirt Cutout -->
      <div class="item-skirt">
        <img src="{b64_skirt}" alt="Denim Skirt">
      </div>
      
      <!-- Iced Coffee -->
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
      
      <!-- Slouchy Black Leather Shoulder Bag (Matching Image 5) -->
      <div class="item-bag">
        <svg viewBox="0 0 250 260" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Shoulder Strap -->
          <path d="M85 100 C 85 10, 165 10, 165 100" stroke="#1a1a1a" stroke-width="14" stroke-linecap="round"/>
          <!-- Bag Slouch Body -->
          <path d="M25 150 Q 50 110, 85 100 Q 125 140, 165 100 Q 200 110, 225 150 Q 240 220, 210 245 Q 125 255, 40 245 Q 10 220, 25 150 Z" fill="#141416" stroke="#222225" stroke-width="3"/>
          <!-- Leather Sheen / Glare Highlights -->
          <path d="M50 160 Q 75 145, 95 165" stroke="rgba(255,255,255,0.3)" stroke-width="4" stroke-linecap="round"/>
          <path d="M155 165 Q 175 145, 200 160" stroke="rgba(255,255,255,0.3)" stroke-width="4" stroke-linecap="round"/>
          <path d="M70 200 Q 125 220, 180 200" stroke="rgba(255,255,255,0.2)" stroke-width="3" stroke-linecap="round"/>
        </svg>
      </div>
      
      <!-- Retro Sunglasses -->
      <div class="item-sunglasses">
        <svg viewBox="0 0 220 90" fill="none" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="60" cy="45" rx="48" ry="28" fill="#1e272e" stroke="#000000" stroke-width="4"/>
          <ellipse cx="160" cy="45" rx="48" ry="28" fill="#1e272e" stroke="#000000" stroke-width="4"/>
          <path d="M106 42 Q 110 38, 114 42" stroke="#000000" stroke-width="6" stroke-linecap="round"/>
          <path d="M35 32 Q 55 25, 75 32" stroke="rgba(255,255,255,0.3)" stroke-width="3" stroke-linecap="round"/>
          <path d="M135 32 Q 155 25, 175 32" stroke="rgba(255,255,255,0.3)" stroke-width="3" stroke-linecap="round"/>
        </svg>
      </div>
      
      <!-- Apple AirPods Max -->
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
      
      <!-- Ballet Flats -->
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
</html>"""

# 2. HTML FOR ANIMATED PAPER-DOLL WARDROBE REEL VIDEO (720x1280 px)
html_video = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    background: #fdf5f7;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    position: relative;
  }}

  /* Scene 1: Wardrobe Animation (0s to 3s) */
  .scene-wardrobe {{
    position: absolute; inset: 0;
    display: flex; flex-direction: column; align-items: center;
    padding-top: 60px;
    animation: fadeOutScene 0.8s ease 3.2s forwards;
    z-index: 10;
  }}

  @keyframes fadeOutScene {{
    0% {{ opacity: 1; transform: scale(1); }}
    100% {{ opacity: 0; transform: scale(1.08); pointer-events: none; }}
  }}

  .w-header {{ text-align: center; margin-bottom: 25px; }}
  .w-tag {{ font-size: 13px; font-weight: 800; letter-spacing: 4px; color: #d81b60; text-transform: uppercase; }}
  .w-title {{ font-size: 24px; font-weight: 900; color: #2d2d34; margin-top: 4px; }}

  /* Vintage Wardrobe SVG with 3D Opening Doors */
  .wardrobe-wrap {{
    position: relative; width: 340px; height: 700px;
    perspective: 1000px;
  }}

  .door-left {{
    transform-origin: left center;
    animation: openDoorLeft 1.4s cubic-bezier(0.25, 1, 0.5, 1) 0.6s forwards;
  }}
  .door-right {{
    transform-origin: right center;
    animation: openDoorRight 1.4s cubic-bezier(0.25, 1, 0.5, 1) 0.6s forwards;
  }}

  @keyframes openDoorLeft {{
    0% {{ transform: rotateY(0deg); }}
    100% {{ transform: rotateY(-85deg); }}
  }}
  @keyframes openDoorRight {{
    0% {{ transform: rotateY(0deg); }}
    100% {{ transform: rotateY(85deg); }}
  }}

  /* Flying Paper-Doll Stickers */
  .flying-sticker {{
    position: absolute;
    border: 4px solid #ffffff; border-radius: 12px;
    background: #ffffff;
    box-shadow: 0 12px 28px rgba(216, 27, 96, 0.28);
    opacity: 0;
  }}

  .fly-tee {{
    top: 240px; left: -140px; width: 220px;
    animation: flyOutTee 1.6s cubic-bezier(0.34, 1.56, 0.64, 1) 1.2s forwards;
  }}
  .fly-tee img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}

  @keyframes flyOutTee {{
    0% {{ opacity: 0; transform: scale(0.4) rotate(0deg) translate(200px, 100px); }}
    60% {{ opacity: 1; transform: scale(1.1) rotate(-8deg) translate(0, 0); }}
    100% {{ opacity: 1; transform: scale(1) rotate(-4deg) translate(0, 0); }}
  }}

  .fly-jacket {{
    top: 480px; right: -130px; width: 210px;
    animation: flyOutJacket 1.6s cubic-bezier(0.34, 1.56, 0.64, 1) 1.5s forwards;
  }}
  .fly-jacket img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}

  @keyframes flyOutJacket {{
    0% {{ opacity: 0; transform: scale(0.4) rotate(0deg) translate(-200px, 50px); }}
    60% {{ opacity: 1; transform: scale(1.1) rotate(8deg) translate(0, 0); }}
    100% {{ opacity: 1; transform: scale(1) rotate(4deg) translate(0, 0); }}
  }}

  /* Scene 2: The Fit Check On-Model (2.8s to 6s) */
  .scene-model {{
    position: absolute; inset: 0;
    opacity: 0;
    animation: fadeInModel 0.8s ease 3.0s forwards;
    z-index: 5;
    background: #000000;
  }}

  @keyframes fadeInModel {{
    0% {{ opacity: 0; transform: scale(0.95); }}
    100% {{ opacity: 1; transform: scale(1); }}
  }}

  .scene-model img {{
    width: 100%; height: 100%; object-fit: cover; object-position: center 20%;
  }}

  .model-overlay {{
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 45%, rgba(0,0,0,0.4) 100%);
  }}

  /* Instagram Reels UI Elements */
  .reels-sidebar {{
    position: absolute; right: 20px; bottom: 120px;
    display: flex; flex-direction: column; align-items: center; gap: 24px;
    z-index: 30;
  }}
  .reels-btn {{
    display: flex; flex-direction: column; align-items: center; gap: 4px; color: #ffffff;
    text-shadow: 0 2px 8px rgba(0,0,0,0.6); font-size: 13px; font-weight: 700;
  }}
  .reels-btn svg {{ width: 34px; height: 34px; fill: #ffffff; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5)); }}
  .reels-btn.liked svg {{ fill: #ff4757; }}

  .reels-bottom-info {{
    position: absolute; left: 24px; bottom: 35px; right: 90px;
    z-index: 30; color: #ffffff;
  }}
  .user-badge {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .user-avatar {{
    width: 40px; height: 40px; border-radius: 50%;
    background: #d81b60; display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 16px; border: 2px solid #ffffff;
  }}
  .user-name {{ font-weight: 800; font-size: 15px; letter-spacing: 0.5px; }}
  .user-follow {{
    background: transparent; border: 1.5px solid rgba(255,255,255,0.7);
    color: #ffffff; padding: 3px 12px; border-radius: 12px; font-size: 12px; font-weight: 700;
  }}
  .caption-text {{ font-size: 14px; line-height: 1.45; text-shadow: 0 2px 6px rgba(0,0,0,0.7); margin-bottom: 12px; }}
  .audio-ticker {{ display: flex; align-items: center; gap: 8px; font-size: 12.5px; opacity: 0.9; }}
</style>
</head>
<body>
  <!-- Scene 1: Animated Paper-Doll Wardrobe -->
  <div class="scene-wardrobe">
    <div class="w-header">
      <div class="w-tag">YOUR NEXT OUTFIT IS WAITING</div>
      <div class="w-title">Tinggal Pilih & Mix and Match! ✨</div>
    </div>

    <div class="wardrobe-wrap">
      <!-- Vintage Wardrobe SVG with 3D Doors -->
      <svg viewBox="0 0 340 700" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="15" y="55" width="310" height="630" rx="18" fill="#ffdce5" stroke="#f48fb1" stroke-width="4"/>
        <path d="M15 70 Q 170 15, 325 70 Z" fill="#ffdce5" stroke="#f48fb1" stroke-width="4"/>
        <text x="170" y="52" text-anchor="middle" font-family="-apple-system, sans-serif" font-weight="900" font-size="18" fill="#d81b60" letter-spacing="5">COLORBOX</text>
        
        <!-- Interior of wardrobe (revealed when doors open) -->
        <rect x="25" y="80" width="290" height="590" rx="10" fill="#fff5f8"/>
        <!-- Clothes hanging bar -->
        <line x1="35" y1="120" x2="305" y2="120" stroke="#d81b60" stroke-width="5"/>
        <line x1="80" y1="120" x2="80" y2="150" stroke="#d81b60" stroke-width="2"/>
        <line x1="170" y1="120" x2="170" y2="150" stroke="#d81b60" stroke-width="2"/>
        <line x1="260" y1="120" x2="260" y2="150" stroke="#d81b60" stroke-width="2"/>
        
        <!-- Left Door -->
        <g class="door-left">
          <rect x="25" y="80" width="140" height="590" rx="10" fill="#ffe4ec" stroke="#f48fb1" stroke-width="3"/>
          <rect x="35" y="95" width="120" height="560" rx="6" fill="#ffdce5" stroke="#f8bbd0" stroke-width="1.5"/>
          <rect x="140" y="340" width="16" height="50" rx="4" fill="#f48fb1" stroke="#d81b60" stroke-width="1.5"/>
          <text x="148" y="372" text-anchor="middle" font-weight="900" font-size="12" fill="#ffffff">C</text>
        </g>
        
        <!-- Right Door -->
        <g class="door-right">
          <rect x="175" y="80" width="140" height="590" rx="10" fill="#ffe4ec" stroke="#f48fb1" stroke-width="3"/>
          <rect x="185" y="95" width="120" height="560" rx="6" fill="#ffdce5" stroke="#f8bbd0" stroke-width="1.5"/>
          <rect x="184" y="340" width="16" height="50" rx="4" fill="#f48fb1" stroke="#d81b60" stroke-width="1.5"/>
          <text x="192" y="372" text-anchor="middle" font-weight="900" font-size="12" fill="#ffffff">B</text>
        </g>
        
        <!-- Bottom Legs -->
        <rect x="35" y="682" width="24" height="20" rx="4" fill="#f48fb1"/>
        <rect x="281" y="682" width="24" height="20" rx="4" fill="#f48fb1"/>
      </svg>

      <!-- Flying Sticker 1: Pink Tee -->
      <div class="flying-sticker fly-tee">
        <img src="{b64_clean_tee}">
      </div>

      <!-- Flying Sticker 2: Crop Jacket -->
      <div class="flying-sticker fly-jacket">
        <img src="{b64_jacket}">
      </div>
    </div>
  </div>

  <!-- Scene 2: The Fit Check On-Model -->
  <div class="scene-model">
    <img src="{b64_tee_front}" alt="Fit Check On Model">
    <div class="model-overlay"></div>

    <!-- Reels Sidebar -->
    <div class="reels-sidebar">
      <div class="reels-btn liked">
        <svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        <span>24.8K</span>
      </div>
      <div class="reels-btn">
        <svg viewBox="0 0 24 24"><path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18z"/></svg>
        <span>142</span>
      </div>
      <div class="reels-btn">
        <svg viewBox="0 0 24 24"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/></svg>
        <span>3.8K</span>
      </div>
    </div>

    <!-- Reels Caption & User Info -->
    <div class="reels-bottom-info">
      <div class="user-badge">
        <div class="user-avatar">C</div>
        <div class="user-name">colorbox</div>
        <button class="user-follow">Follow</button>
      </div>
      <div class="caption-text">
        Your next outfit is waiting in the wardrobe. 👀 Tinggal pilih pieces favoritmu, and make it your own! ✨
      </div>
      <div class="audio-ticker">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="#fff"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
        <span>colorbox • Sunset Club Original Audio</span>
      </div>
    </div>
  </div>
</body>
</html>"""

def run_production():
    print("Launching Playwright...")
    with sync_playwright() as p:
        # 1. Render Slide 2
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        print("Rendering Slide 2...")
        page.set_content(html_slide_2, wait_until="networkidle")
        page.wait_for_timeout(1000)
        
        slide_2_path = OUT_DIR / "slide_2_hero_top.png"
        page.screenshot(path=str(slide_2_path))
        print("Saved Slide 2 to:", slide_2_path)
        
        # Sync Slide 2 everywhere
        for sub in [
            "colorbox/marketing/output/carousel_latest",
            "backend/colorbox/marketing/output/carousel_latest",
            "frontend/frontend/public/output/carousel_latest"
        ]:
            alt = Path("d:/Users/IVANAGITA/aitoptrends/hermes") / sub / "slide_2_hero_top.png"
            alt.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(alt))
            
        brain_slide2 = Path(r"C:\Users\IVANAGITA\.gemini\antigravity\brain\289c4273-5463-4a74-9663-80a73fc092a8\output_graphic_tee\slide_2_hero_top.png")
        page.screenshot(path=str(brain_slide2))
        browser.close()

        # 2. Record Animated Paper-Doll Wardrobe UGC Video (720x1280 px)
        video_temp_dir = BASE_DIR / "video_record_temp"
        video_temp_dir.mkdir(parents=True, exist_ok=True)
        
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 720, "height": 1280},
            device_scale_factor=1,
            record_video_dir=str(video_temp_dir),
            record_video_size={"width": 720, "height": 1280}
        )
        vid_page = context.new_page()
        print("Recording UGC Video (6 seconds smooth animation)...")
        vid_page.set_content(html_video, wait_until="networkidle")
        
        # Play the full 6-second animated loop
        time.sleep(6.2)
        
        context.close()
        browser.close()
        
        # Find recorded video in video_temp_dir
        recorded_files = list(video_temp_dir.glob("*.webm"))
        if recorded_files:
            latest_vid = max(recorded_files, key=os.path.getctime)
            print("Video recorded successfully:", latest_vid)
            
            # Save as ugc_video.mp4 and ugc_video.webm in all target directories
            targets = [
                OUT_DIR / "ugc_video.mp4",
                OUT_DIR / "ugc_video.webm",
                OUT_DIR / "ugc_video_graphic_tee.mp4",
                Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\colorbox\marketing\output\carousel_latest\ugc_video.mp4"),
                Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\colorbox\marketing\output\carousel_latest\ugc_video.webm"),
                Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\backend\colorbox\marketing\output\carousel_latest\ugc_video.mp4"),
                Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\backend\colorbox\marketing\output\carousel_latest\ugc_video.webm"),
                Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\frontend\frontend\public\output\carousel_latest\ugc_video.mp4"),
                Path(r"d:\Users\IVANAGITA\aitoptrends\hermes\frontend\frontend\public\output\carousel_latest\ugc_video.webm"),
                Path(r"C:\Users\IVANAGITA\.gemini\antigravity\brain\289c4273-5463-4a74-9663-80a73fc092a8\output_graphic_tee\ugc_video.mp4"),
                Path(r"C:\Users\IVANAGITA\.gemini\antigravity\brain\289c4273-5463-4a74-9663-80a73fc092a8\output_graphic_tee\ugc_video.webm"),
            ]
            for t in targets:
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(latest_vid, t)
                print(f"Synced video to: {t}")
        else:
            print("ERROR: No video recorded!")

    print("Production and video recording complete!")

if __name__ == "__main__":
    run_production()
