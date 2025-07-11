from PIL import Image
import os
import random

# 使用相對路徑引用同一套件內的模組，避免在直接執行時找不到 handfont 套件
from . import config
from .extractor import extract_paths
from .transform import perturb, shear, flip_y
from .utils import get_spacing, sanitize_filename_char

# 1. 從我們重新命名的檔案中，匯入兩位專家畫師的繪圖能力
from .draw_cjk import render_cjk_char
from .draw_hollow import render_hollow_char

# 2. 定義需要由「空心專家」處理的字元列表
HOLLOW_CHARS = "O0ABDPAQRGabdeopqg869"

def generate_text_image(text, font_path=None, size=None, ignore_router=False):
    # 保持數字相關設定最新
    if hasattr(config, "sync_digit_overrides"):
        config.sync_digit_overrides()
    if font_path is None:
        font_path = config.FONT_PATH
    if size is None:
        size = config.IMAGE_SIZE
    """
    給定文字與字體路徑，回傳 PIL.Image。
    此版本包含智慧分派邏輯。
    """
    images = []
    spacings = []

    for ch in text:
        try:
            if ch == ' ':
                spacing = get_spacing(ch, size)
                # 為了避免拼接問題，空白也產生一個透明圖像
                images.append(Image.new("RGBA", (spacing, 1)))
                spacings.append(0)
                continue

            # 通用前置作業：提取路徑和變形
            # 若有特殊指定用字型，就改用該字型
            font_used = font_path if ignore_router else config.FONT_ROUTER.get(ch, font_path)
            paths = extract_paths(font_used, ch)
            # 依據設定值加入少量隨機變形，模擬手寫差異
            perturb_amount = config.PERTURB + random.uniform(-config.PERTURB_JITTER, config.PERTURB_JITTER)
            shear_amount = config.SHEAR_ANGLE + random.uniform(-config.SHEAR_JITTER, config.SHEAR_JITTER)
            paths = flip_y(shear(perturb(paths, perturb_amount), shear_amount))

            # ⭐ --- 智慧分派邏輯 --- ⭐
            char_img = None
            if ch in HOLLOW_CHARS:
                # 任務分派給「空心專家」
                char_img = render_hollow_char(paths, size, current_char=ch)
            else:
                # 其他所有字元 (包含中文字和簡單符號) 都交給比較穩定的「書法家」
                char_img = render_cjk_char(paths, size, current_char=ch)
            
            if char_img:
                images.append(char_img)
                spacings.append(get_spacing(ch))

        except Exception as e:
            print(f"⚠️ 字「{ch}」產生失敗：{e}")

    if not images:
        return None

    # 拼接所有小圖到大畫布上 (維持不變)
    total_width = sum(im.width for im in images) + sum(spacings[:-1]) # 最後一個 spacing 不計
    if not images: return None # 防呆
    max_height = max(im.height for im in images if im)

    canvas = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))

    x = 0
    for i, im in enumerate(images):
        y_offset = (max_height - im.height) // 2
        canvas.paste(im, (x, y_offset), im)
        if i < len(spacings) -1:
            x += im.width + spacings[i]

    return canvas

def save_text_image(text, font_path=None, output_path=None, size=None):
    img = generate_text_image(text, font_path or config.FONT_PATH, size or config.IMAGE_SIZE)
    if img:
        if output_path:
            img.save(output_path)
            print(f"✅ 已儲存圖片：{output_path}")
        else:
            print("⚠️ 請指定輸出路徑")
    else:
        print("❌ 無圖片產出")
