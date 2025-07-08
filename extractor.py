from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen


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
        steps = 10
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


def extract_paths(font_path, char):
    font = TTFont(font_path)
    glyphSet = font.getGlyphSet()
    cmap = font.getBestCmap()
    glyph_name = cmap.get(ord(char))
    if glyph_name is None:
        raise ValueError(f"⚠️ 字符「{char}」在該字體中找不到 glyph")

    glyph = font["glyf"][glyph_name]
    pen = PointListPen(glyphSet)

    if glyph.isComposite():
        for comp in glyph.components:
            tp = TransformPen(pen, (
                getattr(comp, "xScale", 1.0), getattr(comp, "xyScale", 0.0),
                getattr(comp, "yxScale", 0.0), getattr(comp, "yScale", 1.0),
                getattr(comp, "x", 0), getattr(comp, "y", 0)
            ))
            glyphSet[comp.glyphName].draw(tp)
    else:
        glyphSet[glyph_name].draw(pen)

    if pen.current_path:
        pen.paths.append(pen.current_path)

    return pen.paths
