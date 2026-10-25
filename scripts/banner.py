"""横幅：一张素纸。左侧照「言」的欢迎页排：小印 + 眉批（落款），名号，一行小字（可再接一排提示字）；
右侧竖排打字机（多句轮播）；纸上淡淡一件当令的画（春柳、夏荷、秋苇、冬梅，同「言」右下角那件）。"""
import random

import brush as brushwork
import ink
import seals
import writer
from glyphs import num

W, H = 840, 300
# 时令画摆放：300 × 340 的画格缩到 SCALE，贴底；middle 在名号与题字之间，corner 贴右下角、与题字叠着
SCALE = .82
MARK_RIGHT = {"middle": 690, "corner": 838}


def build(cfg, fonts, colophon_text, seed, season=None):
    serif, serif_md, brush = fonts["serif"], fonts["serif_medium"], fonts["brush"]
    rng = random.Random(seed)
    defs, body, css = [], [], []

    # ---- 纸、边框、纸纹 ----
    g_defs, g_rect = ink.grain("grain", 2, 2, W - 4, H - 4, seed)
    defs.append(g_defs)
    body.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="3" fill="{ink.PAPER}" stroke="{ink.EDGE}"/>{g_rect}')

    # ---- 当令的一件：只用墨一色、整组压淡，慢慢洇出来 ----
    place = cfg.get("season_mark", "none")
    if season and place in MARK_RIGHT:
        # 淡墨直接调成色、位置用嵌套 <svg> 的视口摆：不用 opacity / transform 属性，
        # 免得「减弱动态效果」时 BASE_CSS 里的 opacity:1、transform:none 把画变浓、挪回原点
        w, h = 300 * SCALE, 340 * SCALE
        tone = ink.lerp_color(ink.PAPER, ink.INK, cfg.get("season_tone", .14))
        defs.append(f'<clipPath id="paper"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="3"/></clipPath>')
        body.append(f'<g clip-path="url(#paper)"><g class="a" style="animation:fade 2.4s .3s forwards" fill="{tone}">'
                    f'<svg x="{num(MARK_RIGHT[place] - w)}" y="{num(H - h)}" width="{num(w)}" height="{num(h)}" viewBox="0 0 300 340">'
                    f'{brushwork.SEASON_MARKS[season]()}</svg></g></g>')

    # 有提示字时整块上提，三四行仍在纸面正中
    tags = cfg.get("tags") or []
    dy = -16 if tags else 0

    # ---- 左：小印 + 眉批「MASTER-NORNA · 金陵·丙午秋」（点为淡点，同「言」的「对谈 · 寒露」）----
    x0 = 84
    body.append(seals.stamped(serif_md, cfg["seal"], x0, 78 + dy, 28, style=cfg.get("seal_style", "line"),
                              prefix="sl", delay=.2, seed=seed))
    x, brow = x0 + 28 + 14, []
    for i, text in enumerate([cfg["eyebrow"], colophon_text]):
        for j, seg in enumerate(text.replace("•", "·").replace("・", "·").split("·")):
            if i or j:
                brow.append(f'<circle cx="{num(x + 7)}" cy="{num(92 + dy)}" r="1.3" fill="{ink.MUTED}" fill-opacity=".6"/>')
                x += 14
            seg = seg.strip()
            if seg:
                r = serif.run(seg, x, 96 + dy, 11.5, spacing=2.2 if seg.isascii() else 1.8)
                brow.append(f'<path d="{r.d}" fill="{ink.MUTED}"/>')
                x += r.width
    body.append(f'<g class="a" style="animation:fade 1s .4s forwards">{"".join(brow)}</g>')

    # ---- 名号（「.」用朱）与一行小字 ----
    x, size, parts = x0 - 1.5, 58, []
    for i, seg in enumerate(cfg["title"].split(".")):
        if i:
            dot = serif_md.run(".", x, 172 + dy, size)
            parts.append(f'<path d="{dot.d}" fill="{ink.VERMILION}"/>')
            x += dot.width + 3.5
        if seg:
            r = serif_md.run(seg, x, 172 + dy, size, spacing=3.5)  # 字距 .06em，同「言」的 h1
            parts.append(f'<path d="{r.d}" fill="{ink.INK}"/>')
            x += r.width + 3.5
    body.append(f'<g class="a" style="animation:rise 1s .6s forwards">{"".join(parts)}</g>')
    sub = serif.run(cfg["subtitle"], x0, 212 + dy, 13.5, spacing=2.6)
    body.append(f'<path class="a" style="animation:fade 1s 1s forwards" d="{sub.d}" fill="{ink.INK_LIGHT}"/>')

    # ---- 提示字：一排淡字，淡朱丝栏相隔（同「言」欢迎页输入框下那一排）----
    x, row = x0, []
    for i, tag in enumerate(tags):
        if i:
            row.append(f'<rect x="{num(x + 13)}" y="{num(242 + dy)}" width="1" height="11" fill="{ink.VERMILION}" fill-opacity=".3"/>')
            x += 27
        r = serif.run(tag, x, 252 + dy, 13, spacing=.5 if tag.isascii() else 1.2)
        row.append(f'<path d="{r.d}" fill="{ink.MUTED}"/>')
        x += r.width
    if row:
        body.append(f'<g class="a" style="animation:fade 1s 1.3s forwards">{"".join(row)}</g>')

    # ---- 右：竖排打字机 ----
    per_column = 4
    for s in cfg["motto"]:
        if len(writer.layout(writer.parse(s), per_column)) > 1:
            raise ValueError(f"banner.motto「{s}」太长：横幅右侧只放得下一列 {per_column} 字")
    w = writer.vertical(brush, cfg["motto"], right=740, top=44, size=46, line_height=53.5,
                        column_width=60, per_column=per_column, timing=cfg["timing"], rng=rng, start=.8, prefix="m")
    css.append(w["css"])
    defs.append(w["defs"])
    defs.append(ink.ink_filter("ink", 694, 28, 100, 256, seed))
    body.append(f'<g filter="url(#ink)">{w["body"]}</g>')

    out = f'<defs>{"".join(defs)}</defs>{"".join(body)}'
    label = f'{cfg["title"]} · {" / ".join(cfg["motto"])}'
    return ink.svg(W, H, out, "".join(css), label)
