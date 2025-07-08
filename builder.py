from PIL import Image
import os
from handfont.config import IMAGE_SIZE, SPECIAL_RENDER_OVERRIDES
from handfont.extractor import extract_paths
from handfont.transform import perturb, shear, flip_y
from handfont.utils import get_spacing, sanitize_filename_char
from handfont.config import FONT_PATH, IMAGE_SIZE
from handfont.config import FONT_ROUTER

# 1. 從我們重新命名的檔案中，匯入兩位專家畫師的繪圖能力
from handfont.draw_cjk import render_cjk_char
from handfont.draw_hollow import render_hollow_char

# 2. 定義需要由「空心專家」處理的字元列表
HOLLOW_CHARS = "O0ABDPAQRGabdeopqg869"

def generate_text_image(text, font_path=None, size=None, ignore_router=False):
    if font_path is None:
        from handfont.config import FONT_PATH as DEFAULT_FONT
        font_path = DEFAULT_FONT
    if size is None:
        from handfont.config import IMAGE_SIZE as DEFAULT_SIZE
        size = DEFAULT_SIZE
    """
    給定文字與字體路徑，回傳 PIL.Image。
    此版本包含智慧分派邏輯。
    """
    images = []
    spacings = []

    for ch in text:
        try:
            if ch == ' ':
                spacing = get_spacing(ch)
                # 為了避免拼接問題，空白也產生一個透明圖像
                images.append(Image.new("RGBA", (int(size * spacing), 1)))
                spacings.append(0)
                continue

            # 通用前置作業：提取路徑和變形
            # 若有特殊指定用字型，就改用該字型
            font_used = font_path if ignore_router else FONT_ROUTER.get(ch, font_path)
            paths = extract_paths(font_used, ch)
            # ‼️ 注意：這裡的抖動和傾斜參數是固定的，您可以之後改成從 config 讀取
            paths = flip_y(shear(perturb(paths, 12), 20))

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

def save_text_image(text, font_path=FONT_PATH, output_path=None, size=IMAGE_SIZE):
    img = generate_text_image(text, font_path, size)
    if img:
        if output_path:
            img.save(output_path)
            print(f"✅ 已儲存圖片：{output_path}")
        else:
            print("⚠️ 請指定輸出路徑")
    else:
        print("❌ 無圖片產出")
