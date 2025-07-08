import math
import random


def perturb(paths, amount):
    """
    ✅ 隨機抖動筆劃點位（只針對中段點做偏移）
    """
    return [[
        (
            x + (random.uniform(-amount, amount) if 0.15 < i / len(path) < 0.85 else 0),
            y + (random.uniform(-amount, amount) if 0.15 < i / len(path) < 0.85 else 0)
        )
        for i, (x, y) in enumerate(path)
    ] for path in paths]


def shear(paths, angle_deg):
    """
    ✅ 傾斜處理：可使字體帶有手寫傾斜感
    """
    k = math.tan(math.radians(angle_deg))
    return [[(x + y * k, y) for (x, y) in path] for path in paths]


def flip_y(paths):
    """
    ✅ Y 軸翻轉：字體座標系原點在左下，圖片在左上，需翻轉
    """
    return [[(x, -y) for (x, y) in path] for path in paths]
