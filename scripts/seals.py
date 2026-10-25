"""印章：静态图形 + 一次性的钤印动作（从大而斜落下，回弹后定住）。

样式 style：
  line     言式细框朱文：细边框、宋体朱字（默认）
  outline  粗框朱文
  solid    白文：朱底镂字
"""
import ink
from glyphs import num


def shape(font, text, x, y, size, style="line", color=None, paper=None):
    """印章本体（静态图形）。1 字居中；2 字竖排；3、4 字两列，右起竖读。color / paper 缺省取当前配色。"""
    color, paper = color or ink.VERMILION, paper or ink.PAPER
    n = len(text)
    if not 1 <= n <= 4:
        raise ValueError(f"印文「{text}」需 1–4 字")
    cells = {
        1: [(0, 0, 1, 1)],
        2: [(0, 0, 1, .5), (0, .5, 1, .5)],
        3: [(.5, 0, .5, 1), (0, 0, .5, .5), (0, .5, .5, .5)],
        4: [(.5, 0, .5, .5), (.5, .5, .5, .5), (0, 0, .5, .5), (0, .5, .5, .5)],
    }[n]
    pad = size * {"solid": .12, "outline": .17, "line": .16}[style]
    inner = size - 2 * pad
    single = {"solid": .74, "outline": .74, "line": .62}[style]
    if text.isascii():  # 西文大写字母只占字面框的七成高，放大一些才和汉字印一样饱满
        single *= 1.3
    paths = []
    for ch, (u, v, uw, vh) in zip(text, cells):
        cx, cy = x + pad + (u + uw / 2) * inner, y + pad + (v + vh / 2) * inner
        paths.append(font.centered(ch, cx, cy, min(uw, vh) * inner * (.98 if n > 1 else single)).d)
    d = "".join(paths)
    if style == "solid":
        return (f'<rect x="{num(x)}" y="{num(y)}" width="{num(size)}" height="{num(size)}" rx="{num(size * .07)}" fill="{color}"/>'
                f'<path d="{d}" fill="{paper}"/>')
    sw = size * (.055 if style == "outline" else .035)
    rx = size * (.07 if style == "outline" else .1)
    return (f'<rect x="{num(x + sw / 2)}" y="{num(y + sw / 2)}" width="{num(size - sw)}" height="{num(size - sw)}" '
            f'rx="{num(rx)}" fill="none" stroke="{color}" stroke-width="{num(sw)}"/><path d="{d}" fill="{color}"/>')


def stamped(font, text, x, y, size, *, style, prefix, delay=0.0, seed=7, color=None):
    """在 delay 秒时钤一次印，之后静置（略斜 4°）。"""
    fid = f"{prefix}-age"
    margin = size * .4 + 6  # 落印时放大到 1.7 倍，滤镜区域要留够
    filt = ink.seal_filter(fid, x - margin, y - margin, size + 2 * margin, size + 2 * margin, seed, light=style == "line")
    return (f'<defs>{filt}</defs><g filter="url(#{fid})"><g class="a fx" style="transform-origin:center;'
            f'animation:stamp .55s {num(delay)}s cubic-bezier(.2,.8,.2,1) forwards">'
            + shape(font, text, x, y, size, style, color) + "</g></g>")
