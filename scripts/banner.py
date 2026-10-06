"""横幅：卷轴展开，左侧名号，右侧竖排打字机（多句轮播），落款 + 钤印。"""
import random

import ink
import seals
import writer
from glyphs import num

W, H = 840, 300
PAPER_BOX = (32, 16, 776, 268)  # 纸面 x, y, w, h

# 两重远山（手绘曲线）
HILLS = [
    ("M32 284 L32 222 C92 204 128 168 186 180 C246 192 270 146 338 156 C404 166 430 208 498 198 "
     "C566 188 596 136 662 144 C724 152 766 196 808 190 L808 284Z", ".06", "1.3s"),
    ("M32 284 L32 248 C110 236 150 214 226 226 C300 238 344 206 428 214 C512 222 572 242 652 230 "
     "C724 220 768 236 808 232 L808 284Z", ".1", "1.6s"),
]

CSS = """
#reveal rect{transform-box:fill-box;transform-origin:center;animation:growx 1.5s cubic-bezier(.3,.7,.2,1) forwards;transform:scaleX(0)}
.rl{animation:rollL 1.5s cubic-bezier(.3,.7,.2,1) forwards;transform:translateX(388px)}
.rr{animation:rollR 1.5s cubic-bezier(.3,.7,.2,1) forwards;transform:translateX(-388px)}
@keyframes rollL{to{transform:none}}@keyframes rollR{to{transform:none}}
.mist{animation:mist 16s ease-in-out 1.5s infinite alternate}
@keyframes mist{from{transform:translateX(-90px)}to{transform:translateX(160px)}}
.birds{animation:fly 28s linear 4.5s infinite;transform:translateX(-120px)}
@keyframes fly{0%{transform:translate(-120px,0)}50%{transform:translate(440px,-14px)}100%{transform:translate(1000px,6px)}}
.wing{transform-box:fill-box;transform-origin:center;animation:flap .9s ease-in-out infinite alternate}
@keyframes flap{to{transform:scaleY(.45)}}
"""


def rod(x):
    return (f'<rect x="{x}" y="8" width="14" height="284" rx="3" fill="#5b3c28"/>'
            f'<rect x="{x + 2}" y="8" width="3" height="284" fill="#7a5638" opacity=".7"/>'
            f'<rect x="{x - 2}" y="2" width="18" height="10" rx="3" fill="#3a2618"/>'
            f'<rect x="{x - 2}" y="288" width="18" height="10" rx="3" fill="#3a2618"/>')


def build(cfg, fonts, colophon_text, seed):
    serif, serif_md, brush = fonts["serif"], fonts["serif_medium"], fonts["brush"]
    rng = random.Random(seed)
    px, py, pw, ph = PAPER_BOX
    defs, body, css = [], [], [CSS]

    # ---- 纸、边框、纸纹 ----
    g_defs, g_rect = ink.grain("grain", px, py, pw, ph, seed)
    defs.append(g_defs)
    body.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="{ink.PAPER}"/>{g_rect}'
                f'<rect x="44" y="28" width="752" height="244" fill="none" stroke="{ink.EDGE}"/>'
                f'<rect x="49" y="33" width="742" height="234" fill="none" stroke="{ink.EDGE}" stroke-width=".6"/>')

    # ---- 朱日、远山、流云、飞鸟 ----
    scene = [f'<circle class="a" style="animation:fade 2s 1.6s forwards" cx="560" cy="150" r="20" '
             f'fill="{ink.VERMILION}" fill-opacity=".5"/>']
    scene += [f'<path class="a" style="animation:rise 2.2s {delay} forwards" d="{d}" fill="{ink.INK}" fill-opacity="{op}"/>'
              for d, op, delay in HILLS]
    scene.append(f'<ellipse class="mist" cx="330" cy="222" rx="170" ry="16" fill="{ink.PAPER}" fill-opacity=".85" filter="url(#soft)"/>')
    wing = f'fill="none" stroke="{ink.INK}" stroke-opacity=".55" stroke-width="1.3" stroke-linecap="round"'
    scene.append(f'<g class="birds"><path class="wing" d="M0 96 q4 -4 8 0 q4 -4 8 0" {wing}/>'
                 f'<path class="wing" d="M26 84 q3 -3 6 0 q3 -3 6 0" {wing}/></g>')
    defs.append('<filter id="soft" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="14"/></filter>')
    body.append(f'<g clip-path="url(#paper)">{"".join(scene)}</g>')

    # ---- 左：英文小标、名号（「.」用朱砂）、朱线、身份 ----
    eyebrow = serif.run(cfg["eyebrow"], 84.5, 108.2, 12.5, spacing=5.6)
    body.append(f'<path class="a" style="animation:fade 1s 1.5s forwards" d="{eyebrow.d}" fill="{ink.MUTED}"/>')
    x, size, parts = 84.5, 64, []
    for i, seg in enumerate(cfg["title"].split(".")):
        if i:
            dot = serif_md.run(".", x, 173, size)
            parts.append(f'<path d="{dot.d}" fill="{ink.VERMILION}"/>')
            x += dot.width
        if seg:
            r = serif_md.run(seg, x, 173, size)
            parts.append(f'<path d="{r.d}" fill="{ink.INK}"/>')
            x += r.width
    body.append(f'<g class="a" style="animation:rise 1s 1.75s forwards">{"".join(parts)}</g>')
    body.append(f'<rect class="a fx" style="transform-origin:left;animation:growx .7s 2.2s forwards,fade .1s 2.2s forwards" '
                f'x="84" y="192" width="40" height="3" fill="{ink.VERMILION}"/>')
    sub = serif.run(cfg["subtitle"], 84.7, 227.6, 15, spacing=3.6)
    body.append(f'<path class="a" style="animation:fade 1s 2.45s forwards" d="{sub.d}" fill="{ink.MUTED}"/>')

    # ---- 右：竖排打字机 ----
    per_column = 4
    for s in cfg["motto"]:
        if len(writer.layout(writer.parse(s), per_column)) > 1:
            raise ValueError(f"banner.motto「{s}」太长：横幅右侧只放得下一列 {per_column} 字")
    w = writer.vertical(brush, cfg["motto"], right=726, top=52, size=46, line_height=53.5,
                        column_width=60, per_column=per_column, timing=cfg["timing"], rng=rng, start=2.0, prefix="m")
    css.append(w["css"])
    defs.append(w["defs"])
    defs.append(ink.ink_filter("ink", 680, 36, 100, 248, seed))
    body.append(f'<g filter="url(#ink)">{w["body"]}</g>')

    # ---- 落款（竖排小字，「·」为朱点）+ 钤印：首句写完后出现 ----
    t_col = w["first_done"] + .2
    col, y = [], 63.5
    for ch in colophon_text:
        if ch in "·•・":
            col.append(f'<circle cx="658" cy="{num(y - 1)}" r="1.6" fill="{ink.VERMILION}"/>')
        elif not ch.isspace():
            col.append(f'<path d="{serif.centered(ch, 658, y, 13).d}" fill="{ink.MUTED}"/>')
        y += 17
    body.append(f'<g class="a" style="animation:fade 1.2s {num(t_col)}s forwards">{"".join(col)}</g>')
    # 印章与题字同步：每写一句，印章呼吸、涟漪外扩；句子写完，一下钤上（同「言」）
    seal_y = min(max(y + 8, 199), 238)
    seal_css, seal = seals.animated(serif_md, cfg["seal"], 635, seal_y, 46, style=cfg.get("seal_style", "line"),
                                    prefix="sl", total=w["total"], intervals=w["intervals"], delay=2.0,
                                    infinite=True, seed=seed)
    css.append(seal_css)
    body.append(seal)

    # 纸面整体用 #reveal 裁切，卷轴展开时由中间向两侧露出
    paper = f'x="{px}" y="{py}" width="{pw}" height="{ph}"'
    defs.insert(0, f'<clipPath id="reveal"><rect {paper}/></clipPath><clipPath id="paper"><rect {paper}/></clipPath>')
    out = (f'<defs>{"".join(defs)}</defs><g clip-path="url(#reveal)">{"".join(body)}</g>'
           f'<g class="rl">{rod(25)}</g><g class="rr">{rod(801)}</g>')
    label = f'{cfg["title"]} · {" / ".join(cfg["motto"])}'
    return ink.svg(W, H, out, "".join(css), label)
