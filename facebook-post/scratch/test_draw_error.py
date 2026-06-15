import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tiktok_service import draw_text_wrapped

# Create dummy image and draw context
img = Image.new("RGBA", (1080, 1920), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# Try loading font or use default
try:
    font = ImageFont.truetype("Prompt-Bold.ttf", 60)
except Exception:
    font = ImageFont.load_default()

text = "ราคาดิ่งลึกที่สุดในรอบปี!\nจ่ายเพียง 219.- (จากราคาปกติ 599.-)"
print("Testing with text:", repr(text))
try:
    draw_text_wrapped(draw, text, font, (0, 0, 0, 255), 920, 220)
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
