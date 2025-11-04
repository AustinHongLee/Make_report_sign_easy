"""
🧪 demo.py - 測試 handfont 模組效果

此腳本用於手動執行測試，會：
1. 呼叫 handfont.generate_text_image() 渲染輸入文字
2. 將結果存成 PNG 圖片於桌面或指定資料夾
"""

import os
import argparse

# 以相對路徑匯入模組，方便直接以 `python -m 包名.demo` 執行
from . import generate_text_image, sanitize_filename_char
from . import auto_update
from .config import OUTPUT_DIR

def run_demo(texts, output_dir, font_path=None, size=None):
    if not texts:
        texts = [
        "Hello世界",
        "管線XG32-1200A",
        "！請檢查此區",
        "UU00c885759",
        ]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for text in texts:
        image = generate_text_image(text, font_path=font_path, size=size)
        if image:
            safe_name = ''.join([sanitize_filename_char(c) for c in text])
            out_path = os.path.join(output_dir, f"demo_{safe_name}.png")
            image.save(out_path)
            print(f"✅ 渲染完成：{out_path}")
        else:
            print(f"⚠️ 無法產生圖像：{text}")

def main():
    auto_update.check_for_update()
    parser = argparse.ArgumentParser(description="Render sample texts to images")
    parser.add_argument("texts", nargs="*", help="Texts to render")
    parser.add_argument("-o", "--output-dir", default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("-f", "--font", dest="font_path", help="Custom font path")
    parser.add_argument("-s", "--size", type=int, help="Image size")
    args = parser.parse_args()
    run_demo(args.texts, args.output_dir, args.font_path, args.size)

if __name__ == "__main__":
    main()
