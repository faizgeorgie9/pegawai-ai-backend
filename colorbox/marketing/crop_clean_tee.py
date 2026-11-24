from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# Load cbx-21b
cbx = Image.open('d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/colorbox-knowledge/images/cbx-21b-oversize-graphic-tee-lt-pink-detail.jpg')
w, h = cbx.size
# Crop from y: 150 to h-40 to completely remove the chin/neck, keeping the clean crewneck collar and full print!
clean_tee = cbx.crop((20, 150, w - 20, h - 30))
clean_tee.save('d:/Users/IVANAGITA/aitoptrends/hermes/backend/colorbox/marketing/clean_folded_tee.png')
print('Clean folded tee cropped, size:', clean_tee.size)
