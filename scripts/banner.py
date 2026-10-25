"""横幅：一张素纸。左侧照「言」的欢迎页排：小印 + 眉批（落款），名号，一行小字；右侧竖排打字机（多句轮播）。"""
import random

import ink
import seals
import writer
from glyphs import num

W, H = 840, 300

def build(cfg, fonts, colophon_text, seed):
    serif, serif_md, brush = fonts["serif"], fonts["serif_medium"], fonts["brush"]
    rng = random.Random(seed)
    defs, body, css = [], [], []

    # ---- 纸、边框、纸纹 ----
    g_defs, g_rect = ink.grain("grain", 2, 2, W - 4, H - 4, seed)
    defs.append(g_defs)
    body.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="3" fill="{ink.PAPER}" stroke="{ink.EDGE}"/>{g_rect}')

    # ---- 左：小印 + 眉批「MASTER-NORNA · 金陵·丙午秋」（点为淡点，同「言」的「对谈 · 寒露」）----
    x0 = 84
    body.append(seals.stamped(serif_md, cfg["seal"], x0, 78, 28, style=cfg.get("seal_style", "line"),
                              prefix="sl", delay=.2, seed=seed))
    x, brow = x0 + 28 + 14, []
    for i, text in enumerate([cfg["eyebrow"], colophon_text]):
        for j, seg in enumerate(text.replace("•", "·").replace("・", "·").split("·")):
            if i or j:
                brow.append(f'<circle cx="{num(x + 7)}" cy="{num(92)}" r="1.3" fill="{ink.MUTED}" fill-opacity=".6"/>')
                x += 14
            seg = seg.strip()
            if seg:
                r = serif.run(seg, x, 96, 11.5, spacing=2.2 if seg.isascii() else 1.8)
                brow.append(f'<path d="{r.d}" fill="{ink.MUTED}"/>')
                x += r.width
    body.append(f'<g class="a" style="animation:fade 1s .4s forwards">{"".join(brow)}</g>')

    # ---- 名号（「.」用朱）与一行小字 ----
    x, size, parts = x0 - 1.5, 58, []
    for i, seg in enumerate(cfg["title"].split(".")):
        if i:
            dot = serif_md.run(".", x, 172, size)
            parts.append(f'<path d="{dot.d}" fill="{ink.VERMILION}"/>')
            x += dot.width + 3.5
        if seg:
            r = serif_md.run(seg, x, 172, size, spacing=3.5)  # 字距 .06em，同「言」的 h1
            parts.append(f'<path d="{r.d}" fill="{ink.INK}"/>')
            x += r.width + 3.5
    body.append(f'<g class="a" style="animation:rise 1s .6s forwards">{"".join(parts)}</g>')
    sub = serif.run(cfg["subtitle"], x0, 212, 13.5, spacing=2.6)
    body.append(f'<path class="a" style="animation:fade 1s 1s forwards" d="{sub.d}" fill="{ink.INK_LIGHT}"/>')

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
