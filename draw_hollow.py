from PIL import Image, ImageDraw, ImageFilter
import random
from handfont.config import (
    COLOR_BASE, COLOR_VARIATION, ALPHA_RANGE,
    BLOB_SIZE_RANGE, PARTIAL_DOT_RADIUS, LINE_WIDTH,
    SPECIAL_RENDER_OVERRIDES
)

# 👉 工具
def with_alpha(rgb, alpha):
    return (rgb[0], rgb[1], rgb[2], alpha)

def varied_color(base, variation=0, alpha=255):
    return tuple(
        min(255, max(0, base[i] + random.randint(-variation, variation))) for i in range(3)
    ) + (alpha,)


# === 單層繪製邏輯 ===
def draw_solid_fill_layer(paths, size, scale, ox, oy, min_x, min_y, current_char=None):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)

    # 判斷是否為可能需要「挖洞」的封閉字元（鎖定英文字母和數字）
    is_hollow_char = current_char and current_char.isalnum()

    # 並且路徑數大於1（單一路徑不可能有洞）
    if is_hollow_char and len(paths) > 1:
        # ⭐【更穩健的挖洞邏輯】
        # 1. 先將所有路徑都畫上填滿的顏色
        for path in paths:
            poly = [((x - min_x) * scale + ox, (y - min_y) * scale + oy) for x, y in path]
            if len(poly) >= 3:
                draw.polygon(poly, fill=255) # 全部填滿白色

        # 2. 然後，將除了第一個路徑之外的所有路徑，用黑色(0)再畫一次，實現「挖洞」
        for inner_path in paths[1:]:
            poly = [((x - min_x) * scale + ox, (y - min_y) * scale + oy) for x, y in inner_path]
            if len(poly) >= 3:
                draw.polygon(poly, fill=0) # 用黑色把內洞挖掉
    else:
        # 對於中文字、簡單符號、或只有單一路徑的字元，全部填滿即可
        for path in paths:
            poly = [((x - min_x) * scale + ox, (y - min_y) * scale + oy) for x, y in path]
            if len(poly) >= 3:
                draw.polygon(poly, fill=255)
    
    final_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    alpha = SPECIAL_RENDER_OVERRIDES.get(current_char, {}).get("alpha", 255)
    color_layer = Image.new("RGBA", (size, size), varied_color(COLOR_BASE, COLOR_VARIATION, alpha))
    final_layer.paste(color_layer, mask=mask)
    return final_layer


def draw_partial_fill_layer(paths, size, scale, ox, oy, min_x, min_y):
    from handfont.config import PARTIAL_DOT_PROBABILITY
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for path in paths:
        for (x, y) in path[::max(1, len(path)//6)]:
            if random.random() < PARTIAL_DOT_PROBABILITY:
                px = (x - min_x) * scale + ox
                py = (y - min_y) * scale + oy
                r = random.uniform(*PARTIAL_DOT_RADIUS)
                draw.ellipse((px - r, py - r, px + r, py + r),
                             fill=varied_color(COLOR_BASE, COLOR_VARIATION, random.randint(*ALPHA_RANGE)))
    return layer


def draw_stroke_alpha_layer(paths, size, scale, ox, oy, min_x, min_y):
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for path in paths:
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i+1]
            p1 = ((x1 - min_x) * scale + ox, (y1 - min_y) * scale + oy)
            p2 = ((x2 - min_x) * scale + ox, (y2 - min_y) * scale + oy)
            alpha = int(255 * (1 - abs(i / len(path) - 0.5) * 2))
            draw.line(p1 + p2, fill=with_alpha(COLOR_BASE, alpha), width=LINE_WIDTH)
    return layer


def draw_stroke_blob_layer(paths, size, scale, ox, oy, min_x, min_y):
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for path in paths:
        for i in range(len(path)//3, 2*len(path)//3, max(1, len(path)//15)):
            x, y = path[i]
            px = (x - min_x) * scale + ox
            py = (y - min_y) * scale + oy
            r = random.randint(*BLOB_SIZE_RANGE)
            draw.ellipse((px - r, py - r, px + r, py + r),
                         fill=varied_color(COLOR_BASE, COLOR_VARIATION, random.randint(*ALPHA_RANGE)))
    return layer


# === ⭐ 主函式改名 ⭐ ===
def render_hollow_char(paths, size=512, current_char=None):
    all_x = [x for path in paths for x, y in path]
    all_y = [y for path in paths for x, y in path]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    scale_ratio = SPECIAL_RENDER_OVERRIDES.get(current_char, {}).get("scale", 1.0)
    offset_y_ratio = SPECIAL_RENDER_OVERRIDES.get(current_char, {}).get("offset_y", 0.0)

    if max_x == min_x or max_y == min_y:
        scale = 0
    else:
        scale = 0.9 * size / max(max_x - min_x, max_y - min_y) * scale_ratio
        
    ox = (size - (max_x - min_x) * scale) / 2
    oy = (size - (max_y - min_y) * scale) / 2 + size * offset_y_ratio

    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for func in [
        draw_solid_fill_layer,
        draw_partial_fill_layer,
        draw_stroke_blob_layer,
        draw_stroke_alpha_layer
    ]:
        kwargs = { "paths": paths, "size": size, "scale": scale, "ox": ox, "oy": oy, "min_x": min_x, "min_y": min_y }
        if func == draw_solid_fill_layer:
            kwargs["current_char"] = current_char
        layer = func(**kwargs)
        base = Image.alpha_composite(base, layer)

    if current_char in 'abcdefghijklmnopqrstuvwxyz':
        shrink = 0.6
        y_offset_ratio = 0.2
        new_size = int(size * shrink)
        image = base.filter(ImageFilter.GaussianBlur(3)).resize((new_size, new_size), Image.LANCZOS)
        padded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        padded.paste(image, ((size - new_size) // 2, int(size * y_offset_ratio)))
        return padded

    from handfont.config import BLUR_AMOUNT
    return base.filter(ImageFilter.GaussianBlur(BLUR_AMOUNT))
