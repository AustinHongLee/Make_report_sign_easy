"""HandFont 主要設定檔
==========================
此檔案集中管理所有可調參數，並附上安全範圍建議與簡易說明。
使用者可依需求微調，或透過 ``print_config_help()`` 迅速檢視每個
參數的用途與建議值。
"""

import os
import sys
import json

# === 📁 模組根目錄（可相容打包後的 __file__）===
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS  # PyInstaller 專用變數
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === 📂 輸出資料夾 ===
# demo.py 會將產生的圖片輸出到此資料夾
OUTPUT_DIR = os.path.join(BASE_DIR, "demo_output")

# ==============================
# 🔤 字體與輸出大小設定
# ==============================

# 使用的 TrueType 字體（支援中文）：建議為細體或筆跡風格字體
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'ChenYuluoyan-2.0-Thin.ttf')

# === 外部字型路由表（支援社群貢獻）===
ROUTER_PATH = os.path.join(BASE_DIR, 'font_routes_template.json')

if os.path.exists(ROUTER_PATH):
    with open(ROUTER_PATH, 'r', encoding='utf-8') as f:
        FONT_ROUTER = json.load(f)
else:
    FONT_ROUTER = {}
    
for ch, path in FONT_ROUTER.items():
    abs_path = os.path.join(BASE_DIR, path) if not os.path.isabs(path) else path
    if not os.path.exists(abs_path):
        print(f"⚠️ 字「{ch}」對應的字型不存在：{abs_path}")
    FONT_ROUTER[ch] = abs_path  # ← 這句才是關鍵，把絕對路徑寫回去
# 單一字圖像輸出尺寸（正方形），單位：像素
# - 常見值：256 ~ 1024
# - 建議：512（平衡細節與效能）
IMAGE_SIZE = 512

# 字元圖片輸出時的放大倍數（用於抗鋸齒處理）
# - 若值為 2，則先以 1024 渲染再縮小為 512
UPSCALE_FACTOR = 2


# ==============================
# ✏️ 字形動態變形設定（書寫模擬）
# ==============================

# 筆劃顫抖程度（數值越大越顫抖）
# - 建議值：0（完全靜止）~ 15（非常亂）
# - 推薦值：10~12，模擬自然手寫浮動
PERTURB = 12

# 參數隨機浮動範圍，數值越高每個字的變形差異越大
# 建議值：0 ~ 5
PERTURB_JITTER = 2

# 傾斜角度（deg）
# - 負數向左傾、正數向右傾
# - 建議範圍：-20° ~ +20°
# - 推薦值：+15 ~ +20（略右傾是常見書寫習慣）
SHEAR_ANGLE = 20

# 傾斜角度的隨機浮動範圍
# 建議值：0° ~ 10°
SHEAR_JITTER = 3

# 模糊半徑（模擬墨水微暈染）
# - 建議值：1 ~ 5（過高會模糊得太重）
# - 推薦值：3，模擬實體紙張吸墨
BLUR_RADIUS = 3


# ==============================
# 🎨 墨水與筆劃樣式設定
# ==============================

# 筆跡主色（RGB）
# 常見風格建議：
#   💙 Royal Blue：     (65, 105, 225)  ← 推薦
#   🖤 Carbon Black：    (30, 30, 30)
#   ❤️ Scarlet Red：     (200, 50, 50)
#   💚 Dark Green：      (0, 128, 64)
#   🩵 Cornflower Blue： (100, 149, 237)
COLOR_BASE = (65, 105, 225)

# 墨水顏色波動範圍 ±N（用於製造不均感）
# - 建議：10 ~ 60
# - 數值越高，越有手寫墨水深淺差異
COLOR_VARIATION = 20

# 筆劃透明度變化範圍（模擬起筆淡、收筆濃）
# - 最小值越小，筆觸尾端會更淡
# - 推薦範圍：120 ~ 255
ALPHA_RANGE = (160, 255)

# 中段墨水球大小（模擬停筆、重壓時的墨水聚集）
# - 數值越大 → 墨球越大、風格越「潦草、隨性」
# - 建議：
#   - 工整風格：(3, 5)
#   - 日常手寫：(5, 10) ✅
#   - 草寫風格：(8, 15)
BLOB_SIZE_RANGE = (3, 6)

# 筆尾斷墨點（模擬筆水不足產生的墨點）
# - 數值越大 → 斷墨點越粗
# - 建議：
#   - 嚴謹風格：(1.5, 3)
#   - 實用自然：(2.5, 5) ✅
#   - 草寫潦草：(4, 6)
PARTIAL_DOT_RADIUS = (1.5, 4)

# 筆劃線寬（用於線條層）
# - 建議：1 ~ 3
LINE_WIDTH = 1

# 文字間距額外調整量（正值增加間距，負值減少）
# - 建議：-100 ~ 100
CHAR_SPACING_OFFSET = 0

# === 字型群組預設調整量 ===
# 各類字元的縮放倍率與垂直位移，可在 GUI 或 custom_config.json 中覆寫
DIGIT_SCALE = 0.8
DIGIT_OFFSET_Y = 0.0
ALPHA_SCALE = 1.0
ALPHA_OFFSET_Y = 0.0
CJK_SCALE = 1.0
CJK_OFFSET_Y = 0.0
SPECIAL_SCALE = 1.0
SPECIAL_OFFSET_Y = 0.0

# === 🗃️ 外部參數覆寫 ===
CUSTOM_CONFIG_PATH = os.path.join(BASE_DIR, "custom_config.json")
if os.path.exists(CUSTOM_CONFIG_PATH):
    import json
    with open(CUSTOM_CONFIG_PATH, "r", encoding="utf-8") as f:
        user_conf = json.load(f)
        globals().update(user_conf)

# ============ 🪶 渲染控制參數 ============
# 是否開啟每個層（可未來擴充用）
ENABLE_SOLID_FILL = True
ENABLE_PARTIAL_FILL = True
ENABLE_BLOB_LAYER = True
ENABLE_ALPHA_STROKE = True

# 模糊程度（GaussianBlur 半徑）
# 建議範圍：1.5 ~ 3
BLUR_AMOUNT = 1.5

# 墨點出現機率（PartialDot）
# 0.0 = 永不出現，1.0 = 幾乎都出現
PARTIAL_DOT_PROBABILITY = 0.3

# ==============================
# 🔣 特殊符號自定義渲染參數
# ==============================

# 可自定義每個特殊字元的樣式：
#   scale：縮放比例（通常用於縮小英文/標點）
#   offset_y：垂直位移（單位：相對 canvas 高度）
#   alpha：整體透明度（255 為完全不透明）
#   spacing：額外間距（負數為減少空隙）

SPECIAL_RENDER_OVERRIDES = {
    '.':  {'scale': 0.2, 'offset_y': 0.3, 'alpha': 200, 'spacing': -100},
    '/':  {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -100},
    '、': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': 30},
    '-':  {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -50},
    '「': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -50},
    '」': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -50},
    '，': {'scale': 0.2, 'offset_y': 0.3, 'alpha': 255, 'spacing': 30},
    '。': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': 30},
    '《': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -40},
    '》': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -40},
    '（': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -40},
    '）': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -40},
    '：': {'scale': 0.4, 'offset_y': 0.1, 'alpha': 255, 'spacing': -20},
    '！': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -30},
    '？': {'scale': 0.6, 'offset_y': 0.0, 'alpha': 255, 'spacing': -30},
    '\'': {'scale': 0.3, 'offset_y': 0.2, 'alpha': 200, 'spacing': -30},
    '"':  {'scale': 0.4, 'offset_y': -0.3, 'alpha': 200, 'spacing': -200},
}

# 對數字補充設定（數字通常佔據較大字框）
for d in '0123456789':
    SPECIAL_RENDER_OVERRIDES.setdefault(d, {})
    SPECIAL_RENDER_OVERRIDES[d].setdefault('scale', DIGIT_SCALE)
    SPECIAL_RENDER_OVERRIDES[d].setdefault('offset_y', DIGIT_OFFSET_Y)

# 新增：確保後續修改縮放或位移時可即時套用
def sync_digit_overrides():
    """Synchronize digit settings into SPECIAL_RENDER_OVERRIDES."""
    for d in '0123456789':
        SPECIAL_RENDER_OVERRIDES.setdefault(d, {})
        SPECIAL_RENDER_OVERRIDES[d]['scale'] = DIGIT_SCALE
        SPECIAL_RENDER_OVERRIDES[d]['offset_y'] = DIGIT_OFFSET_Y

sync_digit_overrides()


# ==============================
# 📖 參數說明與安全範圍
# ==============================
PARAM_INFO = {
    'IMAGE_SIZE': ('單字輸出尺寸(像素)', '256 ~ 1024'),
    'UPSCALE_FACTOR': ('抗鋸齒放大倍數', '1 ~ 4'),
    'PERTURB': ('筆劃顫抖幅度', '0 ~ 15'),
    'PERTURB_JITTER': ('顫抖幅度隨機值', '0 ~ 5'),
    'SHEAR_ANGLE': ('字體傾斜角度', '-20° ~ +20°'),
    'SHEAR_JITTER': ('傾斜角度隨機值', '0° ~ 10°'),
    'BLUR_RADIUS': ('墨跡模糊半徑', '1 ~ 5'),
    'COLOR_VARIATION': ('墨色亮度波動', '10 ~ 60'),
    'ALPHA_RANGE': ('筆畫透明度範圍', '120 ~ 255'),
    'BLOB_SIZE_RANGE': ('墨球大小範圍', '3 ~ 15'),
    'PARTIAL_DOT_RADIUS': ('斷墨點半徑', '1.5 ~ 6'),
    'LINE_WIDTH': ('線條寬度', '1 ~ 3'),
    'CHAR_SPACING_OFFSET': ('字距調整量', '-100 ~ 100'),
    'DIGIT_SCALE': ('數字縮放倍率', '0.5 ~ 1.5'),
    'DIGIT_OFFSET_Y': ('數字垂直位移', '-0.5 ~ 0.5'),
    'ALPHA_SCALE': ('英文縮放倍率', '0.5 ~ 1.5'),
    'ALPHA_OFFSET_Y': ('英文垂直位移', '-0.5 ~ 0.5'),
    'CJK_SCALE': ('中文縮放倍率', '0.5 ~ 1.5'),
    'CJK_OFFSET_Y': ('中文垂直位移', '-0.5 ~ 0.5'),
    'SPECIAL_SCALE': ('特殊符縮放', '0.5 ~ 1.5'),
    'SPECIAL_OFFSET_Y': ('特殊符位移', '-0.5 ~ 0.5'),
    'BLUR_AMOUNT': ('最終高斯模糊量', '1.5 ~ 3'),
    'PARTIAL_DOT_PROBABILITY': ('斷墨點出現機率', '0.0 ~ 1.0'),
}


def print_config_help():
    """列出主要參數及其目前設定值與建議範圍。"""
    for key, (desc, rng) in PARAM_INFO.items():
        val = globals().get(key)
        print(f"{key:20} = {val:<10}  # {desc} (建議 {rng})")
