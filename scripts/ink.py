"""纸、墨、印 —— 各组件共用的配色、滤镜与图形。

风格：干净的米色纸 + 极细的 feTurbulence 纸纹（不做旧、不加云纹，浅色主题下才不显脏）；墨色有浓淡；印章边缘略有磨损。
滤镜一律 filterUnits="userSpaceOnUse"，纹理固定在画布上，动画时不会跟着元素「游动」。
"""
import math

from glyphs import num

# 配色取自「言」styles/00-base.css：纸 --paper / --paper-2，线 --line，墨 --ink / --ink-2 / --ink-3，朱 --accent
# GRAIN 为纸纹颗粒 (r, g, b, 浓度, 偏移)：浅纸撒淡褐，暗纸撒极淡的白（同「言」暗色的 --grain）
LIGHT = dict(PAPER="#fbfaf6", PAPER_EMPTY="#f3f0e8", EDGE="#ded8ca", EDGE_EMPTY="#d3ccbc",
             INK="#292724", INK_LIGHT="#625e57", MUTED="#8a847a", VERMILION="#9b5540", GRAIN=(.45, .38, .27, .22, .08))
DARK = dict(PAPER="#201f1c", PAPER_EMPTY="#282622", EDGE="#403c35", EDGE_EMPTY="#4a453d",
            INK="#e8e3d8", INK_LIGHT="#b7b0a4", MUTED="#8f887e", VERMILION="#c47a5f", GRAIN=(1, 1, 1, .1, .04))
PAPER = PAPER_EMPTY = EDGE = EDGE_EMPTY = INK = INK_LIGHT = MUTED = VERMILION = GRAIN = None


def use(palette):
    """切换纸墨配色：各组件运行时读 ink.PAPER 等，切过之后生成的就是这一套。"""
    globals().update(palette)


use(LIGHT)

# GitHub 浅色 / 深色主题下，透明背景组件（标题、自述）的配色；深色取「言」的暗色主题
THEMES = {
    "light": {"text": "#292724", "muted": "#625e57", "line": "#ded8ca", "seal": "#9b5540"},
    "dark": {"text": "#e8e3d8", "muted": "#b7b0a4", "line": "#403c35", "seal": "#c47a5f"},
}

BASE_CSS = """
.a{opacity:0;animation-fill-mode:forwards;animation-timing-function:cubic-bezier(.2,.7,.2,1)}
.fx{transform-box:fill-box}
@keyframes fade{to{opacity:1}}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes growx{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes stamp{0%{opacity:0;transform:scale(1.7) rotate(-4deg)}60%{opacity:.95;transform:scale(.94) rotate(-4deg)}100%{opacity:.95;transform:scale(1) rotate(-4deg)}}
@keyframes draw{to{stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;opacity:1!important;stroke-dashoffset:0!important}*:not(.w){transform:none!important}}
"""


def svg(w, h, body, css="", label=""):
    title = f"<title>{label}</title>" if label else ""
    aria = f' role="img" aria-label="{label}"' if label else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(w)}" height="{num(h)}" viewBox="0 0 {num(w)} {num(h)}"{aria}>'
            f"{title}<style>{BASE_CSS}{css}</style>{body}</svg>\n")


def lerp_color(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def grain(fid, x, y, w, h, seed):
    """极淡的纸纹：只有细颗粒。返回 (defs, 覆盖层)。"""
    box = f'x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"'
    r, g, b, a, off = GRAIN
    defs = f"""<filter id="{fid}" filterUnits="userSpaceOnUse" {box} color-interpolation-filters="sRGB">
<feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="{seed}" result="n"/>
<feColorMatrix in="n" type="matrix" values="0 0 0 0 {r}  0 0 0 0 {g}  0 0 0 0 {b}  {a} 0 0 0 -{off}" result="dots"/>
<feComposite in="dots" in2="SourceGraphic" operator="in"/>
</filter>"""
    return defs, f'<rect {box} fill="#000" filter="url(#{fid})"/>'


def ink_filter(fid, x, y, w, h, seed):
    """墨：边缘轻微洇开，笔画里有颗粒状的浓淡。"""
    box = f'x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"'
    return f"""<filter id="{fid}" filterUnits="userSpaceOnUse" {box} color-interpolation-filters="sRGB">
<feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="2" seed="{seed + 10}" result="warp"/>
<feDisplacementMap in="SourceGraphic" in2="warp" scale="1.6" xChannelSelector="R" yChannelSelector="G" result="rough"/>
<feGaussianBlur in="rough" stdDeviation=".8" result="bleed"/>
<feComponentTransfer in="bleed" result="halo"><feFuncA type="linear" slope=".3"/></feComponentTransfer>
<feTurbulence type="fractalNoise" baseFrequency=".8 .5" numOctaves="2" seed="{seed + 11}" result="grain"/>
<feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.4 0 0 0 -.05" result="grainAlpha"/>
<feComposite in="rough" in2="grainAlpha" operator="in" result="body"/>
<feMerge><feMergeNode in="halo"/><feMergeNode in="body"/></feMerge>
</filter>"""


def seal_filter(fid, x, y, w, h, seed, light=False):
    """印章做旧：边缘毛口 + 印泥不匀处零星脱落。light=True 时（细框印）只做毛口和少量缺口。"""
    box = f'x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"'
    return f"""<filter id="{fid}" filterUnits="userSpaceOnUse" {box} color-interpolation-filters="sRGB">
<feTurbulence type="fractalNoise" baseFrequency=".18" numOctaves="2" seed="{seed + 20}" result="warp"/>
<feDisplacementMap in="SourceGraphic" in2="warp" scale="{1.1 if light else 1.8}" xChannelSelector="R" yChannelSelector="G" result="rough"/>
<feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="2" seed="{seed + 21}" result="c"/>
<feColorMatrix in="c" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  12 0 0 0 -2.7" result="chips"/>
<feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="2" seed="{seed + 22}" result="s"/>
<feColorMatrix in="s" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  12 0 0 0 -3.1" result="specks"/>
<feComposite in="rough" in2="chips" operator="in" result="chipped"/>
{'' if light else '<feComposite in="chipped" in2="specks" operator="in"/>'}
</filter>"""


def blob(rng, r, points=11):
    """不规则的墨点轮廓（闭合二次贝塞尔），以原点为中心。"""
    pts = []
    for k in range(points):
        a = 2 * math.pi * k / points + rng.uniform(-.15, .15)
        rr = r * rng.uniform(.82, 1.1)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    mids = [((x0 + x1) / 2, (y0 + y1) / 2) for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])]
    d = f"M{num(mids[-1][0])} {num(mids[-1][1])}"
    for (px, py), (mx, my) in zip(pts, mids):
        d += f"Q{num(px)} {num(py)} {num(mx)} {num(my)}"
    return d + "Z"
