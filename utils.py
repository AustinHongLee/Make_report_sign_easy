import os
import random
# 使用相對匯入避免在未安裝套件時產生錯誤
from . import config


def get_image_filename(ch):
    """
    ✅ 給定單一字元，產生對應圖片檔名
    空白鍵、特殊符號皆處理
    """
    if ch == ' ':
        return 'ink_style_SPACE_v1.png'
    return f"ink_style_{'U%04X' % ord(ch) if ch in config.SPECIAL_RENDER_OVERRIDES else ch}_v1.png"


def sanitize_filename_char(c):
    """
    ✅ 防止字元不合法作為檔名（如 : / \ ? * 等）
    若屬於特殊符號也會轉為 UXXXX 編碼
    """
    return f'U{ord(c):04X}' if c in config.SPECIAL_RENDER_OVERRIDES or c in '<>:"/\\|?*' else c


def get_spacing(ch, size=None):
    """
    ✅ 根據不同字元類型取得預設間距 (單位: 像素)

    For space characters the width is derived from the target font size.
    """
    if ch == ' ':
        base = int((size or config.IMAGE_SIZE) * 0.5)
    elif ch in config.SPECIAL_RENDER_OVERRIDES:
        base = config.SPECIAL_RENDER_OVERRIDES[ch].get("spacing", -5)
    elif '\u4e00' <= ch <= '\u9fff':
        base = 5
    elif ch.isdigit():
        base = -80
    elif ch.isalpha():
        base = -60
    else:
        base = 10
    return base + config.CHAR_SPACING_OFFSET


def with_alpha(rgb, alpha):
    """
    ✅ 增加 alpha 通道的顏色轉換
    """
    return (rgb[0], rgb[1], rgb[2], alpha)


def varied_color(base, variation=0, alpha=255):
    """
    ✅ 模擬筆壓或墨水深淺的隨機色
    """
    return tuple(
        min(255, max(0, base[i] + random.randint(-variation, variation))) for i in range(3)
    ) + (alpha,)
