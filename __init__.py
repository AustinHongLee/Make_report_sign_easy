"""
🖋️ handfont - 模擬手寫風格的中文字與符號渲染工具

本模組提供：
- 單字圖像產出（含抖動、模糊、顏色變化等筆跡模擬）
- 多字串拼接圖像產出（可直接嵌入報表、GUI 或 PDF）
"""

from handfont.builder import generate_text_image
from handfont.utils import get_image_filename, sanitize_filename_char

__all__ = [
    'generate_text_image',
    'get_image_filename',
    'sanitize_filename_char'
]