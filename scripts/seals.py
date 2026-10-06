"""印章：样式与「言」同款的动态 —— 书写时呼吸、外扩涟漪，写完一下钤上去。

样式 style：
  line     言式细框朱文：细边框、宋体朱字（默认）
  outline  粗框朱文
  solid    白文：朱底镂字
"""
import ink
from glyphs import num
from writer import Keyframes

# 与「言」styles/90-motion-responsive.css 的 sealBreathe / sealBloom / sealStamp 对应
DIM = {"opacity": .28, "rot": -8, "scale": .86, "tint": 0}
BRIGHT = {"opacity": 1, "rot": -1, "scale": 1.16, "tint": .22}
STAMP = [(0, 0, -14, 2.6), (.48, 1, -3, .86), (.72, None, -4.5, 1.08), (1, "rest", -4, 1)]  # (进度, 不透明度, 角度, 缩放)
STAMP_TIME = .55
BREATH = 1.5
BLOOM_SCALE = 1.9  # 「言」里是 2.7；这里印章大得多，放小一点
EASE_IO, EASE_OUT = "ease-in-out", "cubic-bezier(.2,.8,.2,1)"


def shape(font, text, x, y, size, style="line", color=ink.VERMILION, paper=ink.PAPER):
    """印章本体（静态图形）。1 字居中；2 字竖排；3、4 字两列，右起竖读。"""
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


def _tf(rot, scale):
    return f"rotate({rot:g}deg) scale({scale:g})"


def animated(font, text, x, y, size, *, style, prefix, total, intervals, delay=0.0, infinite=False,
             rest=.88, color=ink.VERMILION, seed=7):
    """带「言」式动态的印章。

    intervals：[(t0, t1)] 书写区间（秒，相对动画起点）。区间内呼吸 + 涟漪，t1 时钤印，其后静置。
    返回 (css, svg)。
    """
    seal_kf, tint_kf = Keyframes(f"{prefix}-s", total), Keyframes(f"{prefix}-t", total)
    rings = [Keyframes(f"{prefix}-r{i}", total) for i in range(2)]
    eps = .001

    def put(t, state, ease=EASE_IO):
        seal_kf.at(t, opacity=state["opacity"], transform=_tf(state["rot"], state["scale"]), animation_timing_function=ease)
        tint_kf.at(t, opacity=state["tint"], animation_timing_function=ease)

    def bloom(ring, t, period):
        ring.at(t, opacity=.75, transform=_tf(-4, 1), animation_timing_function="ease-out")
        ring.at(t + .8 * period, opacity=0, transform=_tf(-4, BLOOM_SCALE))
        ring.at(t + .8 * period + eps, opacity=0, transform=_tf(-4, 1))

    rest_state = {"opacity": rest, "rot": -4, "scale": 1, "tint": 0}
    for ring in rings:
        ring.at(0, opacity=0, transform=_tf(-4, 1))
    for t0, t1 in intervals:
        n = max(1, round((t1 - t0) / BREATH))
        p = (t1 - t0) / n  # 呼吸周期微调到正好填满书写区间
        for k in range(n):
            put(t0 + k * p, DIM)
            put(t0 + (k + .5) * p, BRIGHT)
            bloom(rings[0], t0 + k * p, p)
            if t0 + (k + 1 / 3) * p + .8 * p < t1:
                bloom(rings[1], t0 + (k + 1 / 3) * p, p)
        put(t1, DIM)
        for frac, op, rot, scale in STAMP:  # 钤印：从大而斜落下，回弹后定住
            t = t1 + eps + frac * STAMP_TIME
            state = {"opacity": rest if op == "rest" else op, "rot": rot, "scale": scale, "tint": 0}
            if op is None:
                state["opacity"] = 1
            put(t, state, EASE_OUT)
        bloom(rings[0], t1 + .12, 1.0)  # 落印后的一圈余韵
    first_t0 = intervals[0][0]
    if first_t0 > 0:
        put(0, DIM)
    # 收尾显式写到 100%：缺省的话，CSS 会把末段补间到元素自身的默认值（色块会变成满色）
    end = intervals[-1][1] + STAMP_TIME
    put(end + eps, rest_state, EASE_OUT)
    put(total, rest_state)
    for ring in rings:
        ring.at(total, opacity=0, transform=_tf(-4, 1))

    cls = prefix
    count = "infinite" if infinite else "1"
    css = (f".{cls}{{transform-box:fill-box;transform-origin:center;animation-duration:{num(total)}s;"
           f"animation-delay:{num(delay)}s;animation-iteration-count:{count};animation-fill-mode:both;"
           f"animation-timing-function:linear}}"
           f"@media (prefers-reduced-motion:reduce){{.{cls}.ring,.{cls}.tint{{opacity:0!important}}}}"
           + seal_kf.css() + tint_kf.css() + "".join(r.css() for r in rings))

    sw = max(1.2, size * .03)
    ring_rect = (f'x="{num(x)}" y="{num(y)}" width="{num(size)}" height="{num(size)}" rx="{num(size * .1)}" '
                 f'fill="none" stroke="{color}" stroke-width="{num(sw)}"')
    margin = size * (BLOOM_SCALE - 1) / 2 + 6
    fid = f"{prefix}-age"
    filt = ink.seal_filter(fid, x - margin, y - margin, size + 2 * margin, size + 2 * margin, seed, light=style == "line")
    body = (f'<defs>{filt}</defs><g filter="url(#{fid})">'
            + "".join(f'<rect class="{cls} ring" style="animation-name:{prefix}-r{i}" {ring_rect}/>' for i in range(2))
            + f'<g class="{cls}" style="animation-name:{prefix}-s">'
              f'<rect class="{cls} tint" style="animation-name:{prefix}-t" x="{num(x)}" y="{num(y)}" width="{num(size)}" '
              f'height="{num(size)}" rx="{num(size * .1)}" fill="{color}"/>'
            + shape(font, text, x, y, size, style, color) + "</g></g>")
    return css, body
