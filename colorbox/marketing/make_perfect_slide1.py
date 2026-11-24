from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

def generate_perfect_fur_flatlay():
    # Load user ref image 2
    ref = Image.open('C:/Users/IVANAGITA/.gemini/antigravity/brain/289c4273-5463-4a74-9663-80a73fc092a8/.user_uploaded/media_1795503832892_9e641f00.jpg').convert('RGB')
    w, h = ref.size
    
    # Upscale ref to 1080x1620 (high-res 4:5 friendly)
    target_w, target_h = 1080, 1620
    ref_hi = ref.resize((target_w, target_h), Image.Resampling.LANCZOS)
    arr = np.array(ref_hi).astype(float)
    
    # Load real colorbox graphic artwork
    cbx = Image.open('d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images/cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg')
    # High res crop of the print:
    # 85, 195, 470, 765
    art_crop = cbx.crop((85, 195, 470, 765)).convert('RGBA')
    
    # Detect shirt pixels on high-res
    gray = np.mean(arr, axis=2)
    # Shirt is between y: 350 and 1350
    y_grid = np.arange(target_h)[:, None]
    shirt_mask = (gray < 85) & (y_grid > 320) & (y_grid < 1340)
    
    # Clean up mask (smooth edges)
    mask_img = Image.fromarray((shirt_mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=3))
    mask_arr = np.array(mask_img).astype(float) / 255.0
    
    # Shading factor from original fabric folds and leaf shadows
    shading = (gray / 42.0)
    shading = np.clip(shading, 0.45, 1.25)
    
    # Colorbox Light Pink base: (246, 215, 222)
    pink_base = np.array([246.0, 215.0, 222.0])
    
    # Sunlit areas on the shirt get warm golden tint:
    sun_tint = np.array([255.0, 235.0, 215.0])
    
    # Composite the pink shirt with folds and shadows
    for c in range(3):
        pink_channel = pink_base[c] * shading
        arr[:, :, c] = (1.0 - mask_arr) * arr[:, :, c] + mask_arr * np.clip(pink_channel, 0, 255)
        
    result_img = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    
    # Now place the authentic Miami Beach artwork onto the chest
    # Calculate chest position on 1080x1620:
    # Center X: around 540, Y: around 680..1120
    aw, ah = 440, 610
    art_resized = art_crop.resize((aw, ah), Image.Resampling.LANCZOS)
    
    # Blend artwork seamlessly onto the pink cotton:
    # Multiply blend mode for screen-printed effect
    art_np = np.array(art_resized).astype(float)
    # Background of art is pink (245, 215, 220), graphics are darker colors
    # We blend so white/light areas match shirt, dark inks stay rich
    shirt_patch = np.array(result_img.crop((320, 560, 320 + aw, 560 + ah))).astype(float)
    
    # Screenprint transfer:
    art_gray = np.mean(art_np[:, :, :3], axis=2) / 255.0
    # Blend:
    for c in range(3):
        ink = (art_np[:, :, c] / 235.0) * shirt_patch[:, :, c]
        shirt_patch[:, :, c] = np.clip(ink, 0, 255)
        
    result_img.paste(Image.fromarray(shirt_patch.astype(np.uint8)), (320, 560))
    
    # Crop to exact Instagram 4:5 ratio: 1080x1350
    # Ref is 1080x1620, let's crop centered vertically (y: 135 to 1485)
    slide_1 = result_img.crop((0, 135, 1080, 1485))
    
    out_path = 'd:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing/perfect_slide_1_fur.png'
    slide_1.save(out_path)
    print('Perfect slide 1 fur flatlay created:', slide_1.size)

if __name__ == '__main__':
    generate_perfect_fur_flatlay()
