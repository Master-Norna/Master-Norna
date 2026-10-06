"""竖排打字机：从右往左、逐字书写，墨点光标，多句轮播。

全部是 CSS @keyframes：所有元素共用一个总周期 T、同一个起始延迟，无限循环，
因此在 GitHub README 的 <img> 里也能播放（<img> 内不执行脚本）。
"""
import ink
from glyphs import num

JU = set("。！？.!?")          # 句：朱圈
DOU = set("，、；：,;:")        # 读：朱点
ROTATE = set("「」『』《》〈〉（）()—…～-")  # 竖排时转 90°
QUOTES = {"“": "「", "”": "」", "‘": "『", "’": "』"}
BLINK = .5  # 墨点闪烁半周期（秒）
EASE = "cubic-bezier(.45,.05,.55,.95)"


def parse(sentence):
    """拆成竖排单元：{"ch": 字或 None(空格), "mark": None | "ju" | "dou"}。"""
    cells = []
    for ch in sentence:
        ch = QUOTES.get(ch, ch)
        if ch in JU or ch in DOU:
            if cells:
                cells[-1]["mark"] = "ju" if ch in JU else "dou"
        elif ch in " 　":
            cells.append({"ch": None, "mark": None})
        elif not ch.isspace():
            cells.append({"ch": ch, "mark": None})
    return cells


def layout(cells, per_column):
    """分列：每列最多 per_column 字，逢句读另起一列。"""
    cols, col = [], []
    for cell in cells:
        col.append(cell)
        if len(col) == per_column or cell["mark"]:
            cols.append(col)
            col = []
    return cols + [col] if col else cols


class Keyframes:
    """收集 (时间, {属性}) 并输出 @keyframes，时间换算成总周期的百分比。"""

    def __init__(self, name, total):
        self.name, self.total, self.frames = name, total, {}

    def at(self, t, **props):
        pct = round(min(max(t / self.total * 100, 0), 100), 3)
        self.frames.setdefault(pct, {}).update(props)
        return self

    def css(self):
        body = "".join(f"{p:g}%{{" + ";".join(f"{k.replace('_', '-')}:{v}" for k, v in props.items()) + "}"
                       for p, props in sorted(self.frames.items()))
        return f"@keyframes {self.name}{{{body}}}"


def vertical(font, sentences, *, right, top, size, line_height, column_width, per_column,
             timing, rng, start=0.0, prefix="w"):
    """生成竖排轮播。right 为最右一列中线 x，top 为首字字格上沿 y。

    返回 dict：css、defs（字形）、body（字 + 光标）、columns（最多几列）、first_done（首句写完的时刻，秒）、
    total（总周期）、intervals（每句书写区间）。
    """
    columns = [layout(parse(s), per_column) for s in sentences]

    glyph_ids, glyph_defs = {}, []

    def glyph(ch):
        key = (ch, ch in ROTATE)
        if key not in glyph_ids:
            gid = f"{prefix}g{len(glyph_ids)}"
            g = font.cell(ch, size, rotate=ch in ROTATE)
            glyph_ids[key] = (gid, g)
            glyph_defs.append(f'<path id="{gid}" d="{g.d}"/>')
        return glyph_ids[key]

    # ---- 时间轴 ----
    tm = timing
    schedule, t = [], 0.0
    for cols in columns:
        s = {"gap": t, "chars": []}
        t += tm["gap"]
        for j, col in enumerate(cols):
            if j:
                t += tm["column_pause"] - tm["pause"]
            cx = right - j * column_width
            for r, cell in enumerate(col):
                if cell["ch"] is None:
                    t += tm["stroke"] * .5
                    continue
                gid, g = glyph(cell["ch"])
                y = top + r * line_height
                b = g.bounds or (0, 0, size, size)
                s["chars"].append({"cell": cell, "gid": gid, "x": cx - size / 2, "y": y, "cx": cx,
                                   "top": y + b[1], "bottom": y + b[3], "a": t, "b": t + tm["stroke"]})
                t += tm["stroke"] + tm["pause"]
        s["typed"] = t
        t += tm["hold"]
        s["fade"] = t
        t += tm["fade"]
        s["end"] = t
        schedule.append(s)
    T = t

    # ---- 逐字：自上而下「写」出来（clip-path 擦除），湿墨渐干；笔中墨越写越枯，枯了再蘸 ----
    css, body = [], []
    hidden, shown = "inset(0 0 100% 0)", "inset(0 0 0 0)"
    k = 0
    for si, s in enumerate(schedule):
        load = 1.0
        for c in s["chars"]:
            if load < .62:
                load = 1.0
            color = ink.lerp_color(ink.INK_LIGHT, ink.INK, min(1, load + rng.uniform(-.06, .06)))
            dry = round(rng.uniform(.86, .95), 2)
            load -= rng.uniform(.06, .12)

            kf = Keyframes(f"{prefix}{k}", T)
            kf.at(0, opacity=0, clip_path=hidden)
            kf.at(c["a"], opacity=0, clip_path=hidden, animation_timing_function=EASE)
            kf.at(c["b"], opacity=1, clip_path=shown)
            kf.at(min(c["b"] + tm["dry"], s["fade"]), opacity=dry)
            kf.at(s["fade"], opacity=dry, clip_path=shown)
            kf.at(s["end"], opacity=0, clip_path=shown)
            kf.at(T, opacity=0, clip_path=shown)
            css.append(kf.css())
            first = " w0" if si == 0 else ""
            body.append(f'<g class="w{first}" style="animation-name:{prefix}{k}" '
                        f'transform="translate({num(c["x"])} {num(c["y"])})" fill="{color}"><use href="#{c["gid"]}"/></g>')
            k += 1

            mark = c["cell"]["mark"]
            if mark:  # 朱笔句读，落在字的右下
                mx, my = c["cx"] + size * .46, c["y"] + size * .86
                kf = Keyframes(f"{prefix}{k}", T)
                kf.at(0, opacity=0).at(c["b"], opacity=0).at(c["b"] + .18, opacity=.9)
                kf.at(s["fade"], opacity=.9).at(s["end"], opacity=0).at(T, opacity=0)
                css.append(kf.css())
                shape = (f'<circle cx="{num(mx)}" cy="{num(my)}" r="{num(size * .09)}" fill="none" '
                         f'stroke="{ink.VERMILION}" stroke-width="{num(size * .045)}"/>' if mark == "ju" else
                         f'<circle cx="{num(mx)}" cy="{num(my - size * .06)}" r="{num(size * .055)}" fill="{ink.VERMILION}"/>')
                body.append(f'<g class="w{first}" style="animation-name:{prefix}{k}">{shape}</g>')
                k += 1

    # ---- 墨点光标：书写时贴着笔尖走，停笔时闪烁 ----
    move, blink = Keyframes(f"{prefix}-move", T), Keyframes(f"{prefix}-blink", T)
    eps = .001

    def blink_between(t0, t1):
        on, tt = True, t0
        blink.at(t0, opacity=1)
        while tt + BLINK < t1:
            tt += BLINK
            blink.at(tt - .12, opacity=1 if on else .12).at(tt, opacity=.12 if on else 1)
            on = not on
        blink.at(t1, opacity=1)

    def pos(x, y):
        return f"translate({num(x)}px,{num(y)}px)"

    for s in schedule:
        first, last = s["chars"][0], s["chars"][-1]
        move.at(s["gap"], transform=pos(first["cx"], first["top"]))
        for c in s["chars"]:
            move.at(c["a"], transform=pos(c["cx"], c["top"]), animation_timing_function=EASE)
            move.at(c["b"], transform=pos(c["cx"], c["bottom"]))
        rest = pos(last["cx"], last["bottom"] + size * .2)
        move.at(last["b"] + .25, transform=rest)
        move.at(s["end"] - eps, transform=rest)
        blink_between(s["gap"], first["a"])
        blink.at(last["b"], opacity=1)
        blink_between(last["b"], s["end"])
    css += [move.css(), blink.css()]
    body.append(f'<g class="w wc" style="animation-name:{prefix}-move"><g class="w wc" style="animation-name:{prefix}-blink">'
                f'<path d="{ink.blob(rng, size * .1)}" fill="{ink.INK}"/></g></g>')

    base = (f".w{{animation-duration:{num(T)}s;animation-delay:{num(start)}s;animation-iteration-count:infinite;"
            f"animation-timing-function:linear;animation-fill-mode:both}}"
            # 减弱动态效果时：只静态显示第一句，不显示光标
            f"@media (prefers-reduced-motion:reduce){{.w{{opacity:0!important}}.w0{{opacity:1!important}}}}")
    return {"css": base + "".join(css), "defs": "".join(glyph_defs), "body": "".join(body),
            "columns": max(len(c) for c in columns), "first_done": start + schedule[0]["typed"],
            # 每句的书写区间（落笔前的等待 → 最后一字写完），供印章同步呼吸、钤印
            "total": T, "intervals": [(s["gap"], s["chars"][-1]["b"]) for s in schedule]}
