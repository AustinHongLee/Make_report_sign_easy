from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from functools import lru_cache
import os


@lru_cache(maxsize=16)
def _load_font(path: str) -> TTFont:
    path = os.path.abspath(os.path.normcase(path))
    return TTFont(path)


class PointListPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.paths = []
        self.current_path = []

    def _moveTo(self, pt):
        if self.current_path:
            self.paths.append(self.current_path)
        self.current_path = [pt]

    def _lineTo(self, pt):
        self.current_path.append(pt)

    def _curveToOne(self, pt1, pt2, pt3):
        steps = 20
        last = self._getCurrentPoint()
        for i in range(1, steps + 1):
            t = i / steps
            x = (1 - t)**3 * last[0] + 3*(1 - t)**2*t*pt1[0] + 3*(1 - t)*t**2*pt2[0] + t**3*pt3[0]
            y = (1 - t)**3 * last[1] + 3*(1 - t)**2*t*pt1[1] + 3*(1 - t)*t**2*pt2[1] + t**3*pt3[1]
            self.current_path.append((x, y))

    def _closePath(self):
        if self.current_path:
            self.current_path.append(self.current_path[0])
            self.paths.append(self.current_path)
        self.current_path = []

    def endPath(self):
        self._closePath()


@lru_cache(maxsize=256)
def extract_paths(font_path, char):
    # 正規化路徑避免快取 key 重複
    font_path = os.path.abspath(os.path.normcase(font_path))
    font = _load_font(font_path)
    glyphSet = font.getGlyphSet()
    cmap = font.getBestCmap()
    glyph_name = cmap.get(ord(char))
    if glyph_name is None:
        raise ValueError(f"⚠️ 字符「{char}」在該字體中找不到 glyph")

    glyph = font["glyf"][glyph_name]
    pen = PointListPen(glyphSet)

    if glyph.isComposite():
        for comp in glyph.components:
            # 盡量使用 fontTools 的 transform 矩陣（a, b, c, d, e, f）
            if hasattr(comp, 'transform') and comp.transform is not None:
                # comp.transform 可能是 Transform 或 tuple
                try:
                    m = tuple(comp.transform)
                except Exception:
                    m = (
                        getattr(comp, "xScale", 1.0), getattr(comp, "xyScale", 0.0),
                        getattr(comp, "yxScale", 0.0), getattr(comp, "yScale", 1.0),
                        getattr(comp, "x", 0), getattr(comp, "y", 0)
                    )
            else:
                m = (
                    getattr(comp, "xScale", 1.0), getattr(comp, "xyScale", 0.0),
                    getattr(comp, "yxScale", 0.0), getattr(comp, "yScale", 1.0),
                    getattr(comp, "x", 0), getattr(comp, "y", 0)
                )
            tp = TransformPen(pen, m)
            glyphSet[comp.glyphName].draw(tp)
    else:
        glyphSet[glyph_name].draw(pen)

    if pen.current_path:
        pen.paths.append(pen.current_path)

    return pen.paths
