import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageDraw

IMG_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images"
OUT_ASSETS = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing/assets_cutouts"
os.makedirs(OUT_ASSETS, exist_ok=True)

def extract_tshirt_cbx21b():
    # cbx-21b is the detail macro of the t-shirt
    # Let's inspect cbx-21b and extract it cleanly
    src = os.path.join(IMG_DIR, "cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg")
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    print(f"Loaded cbx-21b: {w}x{h}")
    
    # Save a clean copy
    im.save(os.path.join(OUT_ASSETS, "tee_detail_raw.png"))

def inspect_assets():
    files = [
        "cbx-21a-oversize-graphic-tee-lt-pink-front.jpg",
        "cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg",
        "cbx-21c-oversize-graphic-tee-lt-pink-full.jpg",
        "cbx-21d-oversize-graphic-tee-lt-pink-back.jpg",
        "cbx-12a-double-breasted-crop-jacket-lt-grey-front.jpg",
        "cbx-02-high-waist-barrel-denim-black-front.jpg",
        "cbx-17a-jeans-overlap-micro-skirt-dark-denim-front.jpg",
        "cbx-10-colorbox-x-liunic-tote-bag-ecru-front.jpg",
        "cbx-19a-denim-sling-bag-denim-front.jpg",
    ]
    for f in files:
        p = os.path.join(IMG_DIR, f)
        if os.path.exists(p):
            im = Image.open(p)
            print(f"{f}: {im.size}, aspect={im.size[0]/im.size[1]:.3f}")
        else:
            print(f"MISSING: {f}")

if __name__ == "__main__":
    inspect_assets()
    extract_tshirt_cbx21b()
