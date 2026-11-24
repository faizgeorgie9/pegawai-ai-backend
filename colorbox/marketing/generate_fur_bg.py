import os
import math
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

OUTPUT_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing/render_modern"
os.makedirs(OUTPUT_DIR, exist_ok=True)

IMG_DIR = "d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images"

def create_fur_texture(width=1080, height=1350):
    """
    Generate an ultra-realistic high-pile fluffy white/cream fur rug texture
    with golden-hour warmth and directional micro-strands.
    """
    print("Generating fluffy fur rug texture...")
    # Base warm off-white/cream
    base_color = np.array([248, 244, 238], dtype=np.float32)
    
    # Generate fine noise for fur strands
    np.random.seed(42)
    noise = np.random.normal(0, 18, (height, width, 3))
    
    # Create soft directional fibers
    img = Image.fromarray(np.clip(base_color + noise, 0, 255).astype(np.uint8))
    # Motion blur / directional blur to simulate hair/fur pile
    img = img.filter(ImageFilter.GaussianBlur(radius=1.8))
    
    # Add warm golden hour sunlight gradient from top-left
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Diagonal warm sunbeam
    for i in range(120):
        alpha = int(35 * (1.0 - i / 120.0))
        # Warm golden yellow tone
        draw.polygon([(0, i*12), (width, i*12 + 400), (width, 0), (0, 0)], fill=(255, 230, 180, alpha))
        
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    
    # Add realistic palm / monstera leaf shadow cast diagonally
    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    
    # Draw soft organic palm frond silhouettes
    # Stem
    s_draw.line([(0, 200), (900, 1000)], fill=(40, 25, 20, 90), width=35)
    # Palm leaflets
    leaf_angles = [
        ((150, 320), (350, 260), (450, 340)),
        ((250, 410), (550, 310), (620, 420)),
        ((350, 500), (700, 390), (780, 510)),
        ((480, 610), (850, 490), (950, 620)),
        ((600, 720), (980, 600), (1050, 740)),
        ((100, 280), (300, 420), (220, 520)),
        ((220, 380), (420, 540), (340, 650)),
        ((330, 470), (560, 660), (470, 770)),
        ((450, 570), (700, 780), (600, 900)),
        ((580, 690), (850, 910), (730, 1030)),
    ]
    for p1, p2, p3 in leaf_angles:
        s_draw.polygon([p1, p2, p3], fill=(40, 25, 20, 85))
        
    # Heavy blur for natural sunlight penumbra shadow
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=38))
    
    # Composite shadow onto fur
    img = Image.alpha_composite(img, shadow_layer)
    return img

if __name__ == "__main__":
    fur = create_fur_texture(1080, 1350)
    fur.save(os.path.join(OUTPUT_DIR, "test_fur_bg.png"))
    print("Saved test fur bg!")
