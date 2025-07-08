import os
import random
# 使用相對匯入避免在未安裝套件時產生錯誤
from .config import SPECIAL_RENDER_OVERRIDES


def get_image_filename(ch):
    """
    ✅ 給定單一字元，產生對應圖片檔名
    空白鍵、特殊符號皆處理
    """
    if ch == ' ':
        return 'ink_style_SPACE_v1.png'
    return f"ink_style_{'U%04X' % ord(ch) if ch in SPECIAL_RENDER_OVERRIDES else ch}_v1.png"


def sanitize_filename_char(c):
    """
    ✅ 防止字元不合法作為檔名（如 : / \ ? * 等）
    若屬於特殊符號也會轉為 UXXXX 編碼
    """
    return f'U{ord(c):04X}' if c in SPECIAL_RENDER_OVERRIDES or c in '<>:"/\\|?*' else c


def get_spacing(ch):
    """
    ✅ 根據不同字元類型取得預設間距
    """
    if ch == ' ':
        return 500
    if ch in SPECIAL_RENDER_OVERRIDES: # 特殊符號
        return SPECIAL_RENDER_OVERRIDES[ch].get("spacing", -5)
    if '\u4e00' <= ch <= '\u9fff':  # 中文
        return 5
    if ch.isdigit() or ch.isalpha(): # 英文或數字
        return -60
    return 10


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
