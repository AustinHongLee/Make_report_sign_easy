from PIL import Image
import os
import random as rnd
import re
from contextlib import contextmanager, nullcontext

# 使用相對路徑引用同一套件內的模組，避免在直接執行時找不到 handfont 套件
from . import config
from .extractor import extract_paths, _load_font
from .transform import perturb, shear, flip_y
from .utils import get_spacing
from .core.models import RenderProfile

# 1. 從我們重新命名的檔案中，匯入兩位專家畫師的繪圖能力
from .draw_cjk import render_cjk_char
from .draw_hollow import render_hollow_char

# 2. 定義需要由「空心專家」處理的字元列表
HOLLOW_CHARS = "O0ABDPAQRGabdeopqg869"


@contextmanager
def _apply_random_config(random_per=10):
    """Temporarily jitter config parameters within their safe ranges.

    Parameters
    ----------
    random_per : float
        Percentage of the allowed range used for jitter. Default is 10.
    """
    original = {}
    for key, (_, rng) in getattr(config, 'PARAM_INFO', {}).items():
        if not hasattr(config, key):
            continue
        val = getattr(config, key)
        numbers = re.findall(r'-?\d+\.?\d*', rng)
        if len(numbers) != 2:
            continue
        low, high = map(float, numbers)
        if isinstance(val, (int, float)):
            delta = (high - low) * (random_per / 100)
            new_val = val + rnd.uniform(-delta, delta)
            new_val = max(low, min(high, new_val))
            if isinstance(val, int):
                new_val = int(round(new_val))
            original[key] = val
            setattr(config, key, new_val)
        elif isinstance(val, tuple) and len(val) == 2:
            delta = (high - low) * (random_per / 100)
            new_vals = []
            for v in val:
                nv = v + rnd.uniform(-delta, delta)
                nv = max(low, min(high, nv))
                if isinstance(v, int):
                    nv = int(round(nv))
                new_vals.append(nv)
            original[key] = val
            setattr(config, key, tuple(new_vals))
    try:
        yield
    finally:
        for k, v in original.items():
            setattr(config, k, v)


@contextmanager
def _apply_overrides(overrides: dict | None):
    """Temporarily override selected config attributes.

    Parameters
    ----------
    overrides : dict | None
        Mapping of config attribute name to temporary value, e.g.
        {"LINE_WIDTH": 1, "BLUR_AMOUNT": 0}.
    """
    if not overrides:
        yield
        return
    original = {}
    try:
        for key, val in overrides.items():
            if hasattr(config, key):
                original[key] = getattr(config, key)
                setattr(config, key, val)
        yield
    finally:
        for k, v in original.items():
            setattr(config, k, v)


def generate_text_image(text, font_path=None, size=None, ignore_router=False,
                        clear_cache=False, random=False, random_per=10,
                        overrides: dict | None = None,
                        profile: RenderProfile | None = None):
    # 保持數字相關設定最新
    if hasattr(config, "sync_digit_overrides"):
        config.sync_digit_overrides()
    if profile is not None:
        profile_overrides = profile.to_config_overrides()
        if overrides:
            profile_overrides.update(overrides)
        overrides = profile_overrides
        if font_path is None:
            font_path = profile.font_path
        if size is None:
            size = profile.image_size
    if font_path is None:
        font_path = config.FONT_PATH
    if size is None:
        size = config.IMAGE_SIZE
    """
    給定文字與字體路徑，回傳 PIL.Image。
    此版本包含智慧分派邏輯。

    Parameters
    ----------
    text : str
        要渲染的文字
    font_path : str, optional
        字體檔路徑，預設為 ``config.FONT_PATH``
    size : int, optional
        圖片尺寸，預設為 ``config.IMAGE_SIZE``
    ignore_router : bool, optional
        不使用字元路由表時設為 ``True``
    clear_cache : bool, optional
        渲染後是否清除字型快取
    random : bool, optional
        若為 ``True``，將在渲染過程中暫時隨機化配置參數，
        讓每次產生的字形略有不同
    random_per : float, optional
        隨機化幅度 (百分比)，預設為 10
    """
    images = []
    spacings = []

    with _apply_overrides(overrides):
        for ch in text:
            ctx = _apply_random_config(random_per) if random else nullcontext()
            with ctx:
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
                    try:
                        paths = extract_paths(font_used, ch)
                    except Exception as e1:
                        # 若路由字型缺字，嘗試 fallback 至預設字型
                        fallback_font = config.FONT_PATH
                        if not ignore_router and font_used != fallback_font:
                            try:
                                paths = extract_paths(fallback_font, ch)
                                font_used = fallback_font
                                print(f"ℹ️ '{ch}' 使用預設字型 fallback：{os.path.basename(fallback_font)}")
                            except Exception:
                                raise e1
                        else:
                            raise
                    # 依據設定值加入少量隨機變形，模擬手寫差異
                    perturb_amount = config.PERTURB + rnd.uniform(-config.PERTURB_JITTER, config.PERTURB_JITTER)
                    shear_amount = config.SHEAR_ANGLE + rnd.uniform(-config.SHEAR_JITTER, config.SHEAR_JITTER)
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
    total_width = sum(im.width for im in images) + sum(spacings[:-1])  # 最後一個 spacing 不計
    if not images:
        return None  # 防呆
    max_height = max(im.height for im in images if im)

    canvas = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))

    x = 0
    for i, im in enumerate(images):
        y_offset = (max_height - im.height) // 2
        canvas.paste(im, (x, y_offset), im)
        if i < len(spacings) - 1:
            x += im.width + spacings[i]

    if clear_cache:
        _load_font.cache_clear()

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
