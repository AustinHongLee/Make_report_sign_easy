import os
import sys
from ..builder import generate_text_image
from ..config import IMAGE_SIZE
from PIL import Image
from ..utils import sanitize_filename_char


# 可支援：python preview_fonts.py 李宗鴻
target_text = sys.argv[1] if len(sys.argv) > 1 else "7"
safe_text = "".join(sanitize_filename_char(ch) for ch in target_text)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "..", "fonts")
OUTPUT_BASE = os.path.join(BASE_DIR, "..", "previews", safe_text)
os.makedirs(OUTPUT_BASE, exist_ok=True)

for font_file in os.listdir(FONT_DIR):
    if not font_file.lower().endswith(".ttf"):
        continue

    font_path = os.path.join(FONT_DIR, font_file)
    
    for ch in target_text:
        try:
            img = generate_text_image(ch, font_path=font_path, size=IMAGE_SIZE, ignore_router=True)
            if img:
                safe_ch = sanitize_filename_char(ch)
                output_path = os.path.join(OUTPUT_BASE, f"{safe_ch}_{font_file}.png")
                img.save(output_path)
                print(f"✅ 渲染成功：{ch} - {font_file}")
            else:
                print(f"⚠️ 渲染失敗：{ch} - {font_file}")
        except Exception as e:
            print(f"❌ 錯誤於 {ch} - {font_file}：{e}")
