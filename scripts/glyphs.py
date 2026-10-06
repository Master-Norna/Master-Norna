"""用 fontTools 把文字转成 SVG path —— 生成的 SVG 不依赖访客本地字体。"""
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


def num(v):
    """数字保留一位小数并去掉多余的 0，压缩 path 体积。"""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class Glyph:
    def __init__(self, d, bounds):
        self.d = d
        # (xMin, yMin, xMax, yMax)，SVG 坐标系（y 向下）；空白字形为 None
        self.bounds = bounds


class Run:
    """一行横排文字：path 数据 + 排版宽度（含字距，不含末字之后的字距）。"""

    def __init__(self, d, width):
        self.d, self.width = d, width


class Font:
    _files = {}  # 同一个字体文件只解析一次，不同字重共享

    def __init__(self, path, wght=None):
        if path not in Font._files:
            Font._files[path] = TTFont(path)
        self.tt = Font._files[path]
        self.cmap = self.tt.getBestCmap()
        is_var = "fvar" in self.tt
        self.glyphs = self.tt.getGlyphSet(location={"wght": wght} if is_var and wght else None)
        self.upem = self.tt["head"].unitsPerEm
        os2 = self.tt["OS/2"]
        # 汉字的「字面框」中线，用于竖排时把字放正
        self.em_center = (os2.sTypoAscender + os2.sTypoDescender) / 2

    def _name(self, ch):
        name = self.cmap.get(ord(ch))
        if name is None:
            raise KeyError(f"字体里没有「{ch}」(U+{ord(ch):04X})")
        return name

    def _draw(self, ch, matrix):
        g = self.glyphs[self._name(ch)]
        svg = SVGPathPen(self.glyphs, ntos=num)
        g.draw(TransformPen(svg, matrix))
        bp = BoundsPen(self.glyphs)
        g.draw(TransformPen(bp, matrix))
        return Glyph(svg.getCommands(), bp.bounds)

    def advance(self, ch, size):
        return self.glyphs[self._name(ch)].width * size / self.upem

    def measure(self, text, size, spacing=0):
        return sum(self.advance(ch, size) for ch in text) + spacing * max(len(text) - 1, 0)

    def run(self, text, x, baseline, size, spacing=0, anchor="start"):
        """横排一行。spacing 为字距（px）；anchor 取 start / middle / end。"""
        width = self.measure(text, size, spacing)
        x -= {"start": 0, "middle": width / 2, "end": width}[anchor]
        s = size / self.upem
        svg = SVGPathPen(self.glyphs, ntos=num)
        for ch in text:
            g = self.glyphs[self._name(ch)]
            g.draw(TransformPen(svg, (s, 0, 0, -s, x, baseline)))
            x += g.width * s + spacing
        return Run(svg.getCommands(), width)

    def cell(self, ch, size, rotate=False):
        """把字放进左上角为原点、边长 size 的方格里（居中）。

        rotate=True 时顺时针转 90°，用于竖排里的括号、引号等。
        """
        adv = self.glyphs[self._name(ch)].width
        s = size / self.upem
        # 仿射矩阵 (a, b, c, d, e, f)：x' = a·x + c·y + e，y' = b·x + d·y + f
        a, b, c, d = s, 0, 0, -s
        e, f = size / 2 - adv / 2 * s, size / 2 + self.em_center * s
        if rotate:  # 绕方格中心顺时针 90°：(x, y) -> (size - y, x)
            a, b, c, d, e, f = -b, a, -d, c, size - f, e
        return self._draw(ch, (a, b, c, d, e, f))

    def fit(self, ch, x, y, w, h):
        """把字的墨迹外框拉伸填满矩形 (x, y, w, h) —— 印章字常用的做法。"""
        bp = BoundsPen(self.glyphs)
        self.glyphs[self._name(ch)].draw(bp)
        x0, y0, x1, y1 = bp.bounds
        sx, sy = w / (x1 - x0), h / (y1 - y0)
        return self._draw(ch, (sx, 0, 0, -sy, x - x0 * sx, y + y1 * sy))

    def centered(self, ch, cx, cy, size):
        """按墨迹外框居中放一个字（等比），用于印章里的单字或竖排小字。"""
        bp = BoundsPen(self.glyphs)
        self.glyphs[self._name(ch)].draw(bp)
        x0, y0, x1, y1 = bp.bounds
        s = size / self.upem
        return self._draw(ch, (s, 0, 0, -s, cx - (x0 + x1) / 2 * s, cy + (y0 + y1) / 2 * s))
