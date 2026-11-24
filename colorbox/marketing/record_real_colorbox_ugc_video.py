import base64
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

print("=== RECORDING UGC VIDEO WITH REAL COLORBOX MODEL ASSETS ===")

ROOT_DIR = Path(r"d:\Users\IVANAGITA\aitoptrends\hermes")
KB_IMAGES = ROOT_DIR / "backend" / "colorbox" / "colorbox-knowledge" / "images"

OUTPUT_DIRS = [
    Path(r"d:\Users\IVANAGITA\aitoptrends\karyawan ai\output_graphic_tee"),
    ROOT_DIR / "colorbox" / "marketing" / "output" / "carousel_graphic_tee",
    ROOT_DIR / "colorbox" / "marketing" / "output" / "carousel_latest",
    ROOT_DIR / "backend" / "colorbox" / "marketing" / "output" / "carousel_latest",
    ROOT_DIR / "frontend" / "frontend" / "public" / "output" / "carousel_latest"
]

def img_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

tee_model_b64 = img_to_b64(KB_IMAGES / "cbx-21a-oversize-graphic-tee-lt-pink-front.jpg")
jacket_model_b64 = img_to_b64(KB_IMAGES / "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg")
tee_detail_b64 = img_to_b64(KB_IMAGES / "cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg")

html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  body {{
    width: 720px;
    height: 1280px;
    background: #181416;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    overflow: hidden;
    color: white;
    position: relative;
  }}

  .stage {{
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  /* Scene 1: Real Model in Pink Graphic Tee */
  .scene-1 {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #FFE4EC 0%, #FFF3F6 100%);
    animation: fadeOutScene1 0.6s ease forwards 3.3s;
  }}

  .model-card {{
    width: 580px;
    height: 850px;
    background: white;
    border-radius: 36px;
    box-shadow: 0 25px 60px rgba(244, 114, 150, 0.25);
    overflow: hidden;
    position: relative;
    transform: scale(0.94);
    animation: zoomHero 3.2s ease forwards;
  }}

  .model-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}

  .badge-tag {{
    position: absolute;
    top: 24px;
    left: 24px;
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(8px);
    color: #F47296;
    padding: 10px 22px;
    border-radius: 20px;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  }}

  .rating-tag {{
    position: absolute;
    bottom: 24px;
    right: 24px;
    background: #F47296;
    color: white;
    padding: 10px 22px;
    border-radius: 20px;
    font-size: 20px;
    font-weight: 800;
  }}

  /* Scene 2: Layered with Double Breasted Crop Jacket */
  .scene-2 {{
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #F5EFF9 0%, #FFF0F5 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    opacity: 0;
    animation: fadeInScene2 0.6s ease forwards 3.3s;
  }}

  .layer-card {{
    width: 580px;
    height: 850px;
    background: white;
    border-radius: 36px;
    box-shadow: 0 25px 60px rgba(186, 160, 215, 0.25);
    overflow: hidden;
    position: relative;
    animation: pulseGrid 3.2s ease forwards 3.3s;
  }}

  /* UI Overlay */
  .ui-overlay {{
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 10;
  }}

  .top-bar {{
    position: absolute;
    top: 45px;
    left: 40px;
    right: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}

  .user-pill {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(0,0,0,0.55);
    backdrop-filter: blur(10px);
    padding: 8px 18px;
    border-radius: 24px;
  }}

  .avatar {{
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: #F47296;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 16px;
  }}

  .username {{
    font-size: 20px;
    font-weight: 700;
  }}

  .follow-btn {{
    background: #F47296;
    color: white;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 15px;
    font-weight: 700;
  }}

  .actions-col {{
    position: absolute;
    right: 32px;
    bottom: 180px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 28px;
  }}

  .action-item {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }}

  .action-icon {{
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background: rgba(0,0,0,0.45);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
  }}

  .action-label {{
    font-size: 16px;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0,0,0,0.6);
  }}

  .bottom-info {{
    position: absolute;
    bottom: 45px;
    left: 40px;
    right: 120px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}

  .caption-title {{
    font-size: 25px;
    font-weight: 800;
    color: #1A1A1A;
    background: rgba(255,255,255,0.9);
    padding: 8px 18px;
    border-radius: 14px;
    width: fit-content;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }}

  .caption-desc {{
    font-size: 19px;
    font-weight: 600;
    color: #FFFFFF;
    text-shadow: 0 2px 8px rgba(0,0,0,0.85);
    line-height: 1.4;
  }}

  .music-tag {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 17px;
    color: #FFFFFF;
    background: rgba(0,0,0,0.5);
    padding: 6px 14px;
    border-radius: 18px;
    width: fit-content;
  }}

  @keyframes zoomHero {{
    0% {{ transform: scale(0.94); }}
    100% {{ transform: scale(1.02); }}
  }}

  @keyframes fadeOutScene1 {{
    0% {{ opacity: 1; }}
    100% {{ opacity: 0; pointer-events: none; }}
  }}

  @keyframes fadeInScene2 {{
    0% {{ opacity: 0; transform: scale(0.95); }}
    100% {{ opacity: 1; transform: scale(1); }}
  }}

  @keyframes pulseGrid {{
    0% {{ transform: scale(0.95); }}
    100% {{ transform: scale(1.03); }}
  }}
</style>
</head>
<body>
  <div class="stage">
    <!-- Scene 1: Real Female Model in Sunset Pink Graphic Tee -->
    <div class="scene-1">
      <div class="model-card">
        <img class="model-img" src="data:image/jpeg;base64,{tee_model_b64}" />
        <div class="badge-tag">SUNSET CLUB TEE 🌸</div>
        <div class="rating-tag">Rp 99.900</div>
      </div>
    </div>

    <!-- Scene 2: Layered Styling with Crop Jacket -->
    <div class="scene-2">
      <div class="layer-card">
        <img class="model-img" src="data:image/jpeg;base64,{jacket_model_b64}" />
        <div class="badge-tag">LAYER WITH CROP JACKET ✨</div>
        <div class="rating-tag">Rp 329.900</div>
      </div>
    </div>
  </div>

  <!-- Reels UI Overlay -->
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
        <span class="action-label">21.5K</span>
      </div>
      <div class="action-item">
        <div class="action-icon">💬</div>
        <span class="action-label">628</span>
      </div>
      <div class="action-item">
        <div class="action-icon">🔖</div>
        <span class="action-label">1.8K</span>
      </div>
      <div class="action-item">
        <div class="action-icon">↗</div>
        <span class="action-label">Share</span>
      </div>
    </div>

    <div class="bottom-info">
      <div class="caption-title">Miami Beach Tee + Crop Jacket 💖</div>
      <div class="caption-desc">Spill OOTD cewek kue yang chic & ga ngebosenin! Graphic tee manis di-layer outer crop grey = auto elevated 🌸✨ #ColorboxBabes #OOTD</div>
      <div class="music-tag">♫ Colorbox Vibes - Sunset Club Chill</div>
    </div>
  </div>
</body>
</html>
"""

temp_html = Path("temp_real_ugc_video_record.html")
temp_html.write_text(html_content, encoding="utf-8")

rec_dir = Path("video_recording_scratch_real")
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
    time.sleep(6.8)
    page.close()
    context.close()
    browser.close()

vids = list(rec_dir.glob("*.webm")) + list(rec_dir.glob("*.mp4"))
print(f"Recorded videos: {vids}")

if vids:
    recorded_file = vids[-1]
    print(f"Using recorded file: {recorded_file} ({recorded_file.stat().st_size} bytes)")
    for d in OUTPUT_DIRS:
        shutil.copy(str(recorded_file), str(d / "ugc_video.webm"))
        shutil.copy(str(recorded_file), str(d / "ugc_video.mp4"))
        shutil.copy(str(recorded_file), str(d / "ugc_video_graphic_tee.mp4"))
    print("=== REAL UGC VIDEO SAVED TO ALL OUTPUT DIRS ===")
