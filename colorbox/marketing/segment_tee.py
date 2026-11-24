from PIL import Image, ImageDraw, ImageFilter
import numpy as np

def segment_pink_tee():
    im = Image.open('d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images/cbx-21a-oversize-graphic-tee-lt-pink-front.jpg').convert('RGBA')
    w, h = im.size
    arr = np.array(im)
    r = arr[:, :, 0].astype(float)
    g = arr[:, :, 1].astype(float)
    b = arr[:, :, 2].astype(float)
    
    # In cbx-21a:
    # T-shirt is between y: 280 (shoulders) and y: 720 (bottom hem)
    # The shirt color: pinkish (R is highest, R - G is 15..45, R - B is 10..35)
    # Black pants below y: 715 are very dark (R < 80, G < 80, B < 80)
    # Skin (arms/neck) has higher R-G (R-G > 45 or G < 140)
    
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Main shirt bounding box: y from 280 to 715, x from 50 to 460
    # Let's define the precise contour of the t-shirt:
    # Collar: (265, 335) down to (335, 345) and up to (375, 310)
    # Right shoulder: (375, 310) to (440, 360)
    # Right sleeve: (440, 360) down to (455, 500) and in to (390, 520)
    # Left shoulder: (265, 335) to (180, 320) to (140, 360)
    # Left sleeve: (140, 360) down to (52, 530) and in to (100, 550)
    # Torso: y: 520 to 715, x: 140 to 430
    
    # We can trace the exact polygon of the shirt!
    # Let's inspect coordinates of collar, sleeves, hems
    tee_polygon = [
        # Collar curve (closed at back of collar so it looks like ghost mannequin)
        (265, 332), (285, 342), (325, 346), (355, 335), (372, 312),
        # Right shoulder
        (405, 335), (438, 365),
        # Right sleeve outer
        (448, 410), (455, 460), (458, 500),
        # Right sleeve cuff
        (445, 505), (410, 515), (382, 520),
        # Right armpit / side seam
        (385, 495), (388, 540), (405, 600), (425, 670), (428, 715),
        # Bottom hem
        (380, 716), (320, 718), (260, 718), (200, 716), (142, 714),
        # Left side seam
        (150, 670), (160, 600), (155, 540), (148, 490),
        # Left sleeve cuff
        (125, 505), (90, 520), (52, 530),
        # Left sleeve outer
        (65, 480), (88, 430), (120, 380), (140, 355),
        # Left shoulder
        (175, 325), (220, 328), (265, 332)
    ]
    
    mask_img = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.polygon(tee_polygon, fill=255)
    
    # Smooth edges with antialiasing / slight blur
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=0.8))
    
    # Cut out the t-shirt
    im.putalpha(mask_img)
    
    # Crop tightly to the t-shirt bounding box
    bbox = (50, 305, 465, 720)
    tee_isolated = im.crop(bbox)
    tee_isolated.save('d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing/tee_isolated_ghost.png')
    print('Tee isolated successfully, size:', tee_isolated.size)

if __name__ == '__main__':
    segment_pink_tee()
