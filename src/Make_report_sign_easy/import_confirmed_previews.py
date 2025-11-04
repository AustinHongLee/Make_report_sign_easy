import os
import json

# 相對匯入以便直接以模組方式執行
from .config import BASE_DIR
from .safe_char_map import REVERSE_SAFE_CHAR_MAP

ROUTER_PATH = os.path.join(BASE_DIR, "configs", "font_routes_template.json")
CONFIRM_DIR = os.path.join(BASE_DIR, "confirm")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

# 讀取既有 ROUTER
if os.path.exists(ROUTER_PATH):
    with open(ROUTER_PATH, "r", encoding="utf-8") as f:
        font_router = json.load(f)
else:
    font_router = {}

added = 0

for file in os.listdir(CONFIRM_DIR):
    if not file.endswith(".ttf.png"):
        continue

    try:
        safe_char, font_with_ext = file.split("_", 1)
        # 嘗試從 SAFE_CHAR_MAP 反查
        char = REVERSE_SAFE_CHAR_MAP.get(safe_char, None)

        # 若失敗，且格式為 Uxxxx → 嘗試直接轉回原字元
        if char is None and safe_char.startswith("U") and len(safe_char) == 5:
            try:
                char = chr(int(safe_char[1:], 16))
            except:
                char = safe_char  # fallback 用原始名        
        font_name = font_with_ext.replace(".png", "")  # ✅ 去除末尾 .png
        print(f"🔍 處理檔案：{file} → 字：「{char}」, 字型：「{font_name}」")
        font_path = os.path.join("fonts", font_name).replace("\\", "/")

        # 驗證字型檔是否存在
        if not os.path.exists(os.path.join(BASE_DIR, font_path)):
            print(f"⚠️ 找不到對應字型檔：{font_path}")
            continue

        font_router[char] = font_path
        added += 1
        print(f"✅ 新增路由：「{char}」→ {font_path}")

    except Exception as e:
        print(f"❌ 無法解析檔名 {file}：{e}")

# 儲存回 JSON
with open(ROUTER_PATH, "w", encoding="utf-8") as f:
    json.dump(font_router, f, ensure_ascii=False, indent=2)

print(f"🎯 已完成，總共寫入 {added} 筆字型路由")
