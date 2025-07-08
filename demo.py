"""
🧪 demo.py - 測試 handfont 模組效果

此腳本用於手動執行測試，會：
1. 呼叫 handfont.generate_text_image() 渲染輸入文字
2. 將結果存成 PNG 圖片於桌面或指定資料夾
"""

import os
from handfont import generate_text_image, sanitize_filename_char
from handfont.config import OUTPUT_DIR

def run_demo():
    sample_texts = [
        "Hello世界",
        "管線XG32-1200A",
        "！請檢查此區",
        "UU00c885759",
    ]

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for text in sample_texts:
        image = generate_text_image(text)
        if image:
            safe_name = ''.join([sanitize_filename_char(c) for c in text])
            out_path = os.path.join(OUTPUT_DIR, f"demo_{safe_name}.png")
            image.save(out_path)
            print(f"✅ 渲染完成：{out_path}")
        else:
            print(f"⚠️ 無法產生圖像：{text}")

if __name__ == "__main__":
    run_demo()
