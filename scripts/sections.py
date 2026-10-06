"""透明背景的小标题、自述正文（各出浅/深两版），以及作品卡片。"""
import ink
import seals
from glyphs import num

WIDTH = 840


def title(fonts, text, note, theme):
    """■ 自述 ———————————— 注语"""
    c = ink.THEMES[theme]
    serif = fonts["serif"]
    if is_latin(text):  # 英文标题用宋体（楷书的西文字母不好看），字距收紧
        head = fonts["serif_semibold"].run(text, 24, 40, 25, spacing=1.5)
    else:
        head = fonts["brush"].run(text, 24, 42, 30, spacing=14)
    parts = [f'<rect class="a" style="animation:fade .4s .1s forwards" x="4" y="27" width="8" height="8" fill="{c["seal"]}"/>',
             f'<defs><clipPath id="tc"><rect class="fx" style="transform-origin:left;transform:scaleX(0);'
             f'animation:growx .9s .2s forwards" x="20" y="4" width="{num(head.width + 12)}" height="52"/></clipPath></defs>',
             f'<path clip-path="url(#tc)" d="{head.d}" fill="{c["text"]}"/>']
    x1, x2 = 24 + head.width + 14, WIDTH - 4
    if note:
        n = serif.run(note, WIDTH - 4, 36, 12.5, spacing=1 if is_latin(note) else 3.4, anchor="end")
        x2 = WIDTH - 4 - n.width - 18
        parts.append(f'<path class="a" style="animation:fade 1s 1.2s forwards" d="{n.d}" fill="{c["muted"]}"/>')
    length = num(x2 - x1)
    parts.insert(3, f'<line x1="{num(x1)}" y1="31" x2="{num(x2)}" y2="31" stroke="{c["line"]}" stroke-dasharray="{length}" '
                    f'stroke-dashoffset="{length}" style="animation:draw 1.4s .5s cubic-bezier(.3,.7,.2,1) forwards"/>')
    return ink.svg(WIDTH, 60, "".join(parts), label=text)


def is_latin(text):
    return sum(ch.isascii() for ch in text) > len(text) / 2


def intro(fonts, lines, theme):
    """自述正文：每行像被笔刷从左到右刷出来。"""
    c = ink.THEMES[theme]
    serif = fonts["serif"]
    clips, paths = [], []
    for i, line in enumerate(lines):
        base = 30 + i * 36
        r = serif.run(line, 4, base, 17)
        clips.append(f'<clipPath id="l{i}"><rect class="fx" style="transform-origin:left;transform:scaleX(0);'
                     f'animation:growx 1.4s {num(.3 + .6 * i)}s cubic-bezier(.4,.2,.2,1) forwards" '
                     f'x="0" y="{base - 22}" width="{num(r.width + 8)}" height="32"/></clipPath>')
        paths.append(f'<path clip-path="url(#l{i})" d="{r.d}" fill="{c["text"]}"/>')
    return ink.svg(WIDTH, 24 + 36 * len(lines), f'<defs>{"".join(clips)}</defs>{"".join(paths)}', label="".join(lines))


def wrap(font, text, size, width):
    """按字宽折行（英文单词不拆开）。"""
    lines, cur = [], ""
    tokens, word = [], ""
    for ch in text:
        if ch.isascii() and not ch.isspace():
            word += ch
            continue
        if word:
            tokens.append(word)
            word = ""
        tokens.append(ch)
    if word:
        tokens.append(word)
    for tok in tokens:
        if cur and font.measure(cur + tok, size) > width:
            lines.append(cur.rstrip())
            cur = tok.lstrip()
        else:
            cur += tok
    return lines + [cur] if cur else lines


CARD_W, CARD_H = 412, 150


def _card_frame(seed, fill, stroke, dashed=False):
    g_defs, g_rect = ink.grain("grain", 2, 2, CARD_W - 4, CARD_H - 4, seed)
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    frame = f'<rect x="1" y="1" width="{CARD_W - 2}" height="{CARD_H - 2}" rx="3" fill="{fill}" stroke="{stroke}"{dash}/>{g_rect}'
    if not dashed:
        frame += f'<rect x="7" y="7" width="{CARD_W - 14}" height="{CARD_H - 14}" rx="2" fill="none" stroke="{stroke}" stroke-width=".6"/>'
    return g_defs, frame


def card(fonts, p, index, seed):
    """作品卡片：印章 + 名称 + 一句话介绍 + 标签。"""
    serif, serif_sb = fonts["serif"], fonts["serif_semibold"]
    g_defs, frame = _card_frame(seed + index, ink.PAPER, ink.EDGE)
    # 印章：文字浮现时呼吸，写完钤印（同「言」）；各卡片错开一点
    seal_css, seal = seals.animated(fonts["serif_medium"], p.get("seal") or p["name"][:4], 27, 27, 50,
                                    style=p.get("seal_style", "line"), prefix="sc", total=3.4,
                                    intervals=[(.1, 1.6)], delay=.15 * index, seed=seed + index)
    name = serif_sb.run(p["name"], 98.7, 56.5, 21, spacing=2.5)
    desc_lines = wrap(serif, p.get("desc", ""), 14, CARD_W - 98.7 - 26)[:2]
    top, pitch = (84, 20) if len(desc_lines) > 1 else (88, 22)  # 两行时整体上提，给标签留出空
    desc = "".join(serif.run(line, 98.7, top + pitch * i, 14).d for i, line in enumerate(desc_lines))
    tags = serif_sb.run(" · ".join(p.get("tags", [])), 98.5, 130.5, 11, spacing=2)
    body = (f"<defs>{g_defs}</defs>{frame}{seal}"
            f'<path class="a" style="animation:rise .8s .55s forwards" d="{name.d}" fill="{ink.INK}"/>'
            f'<path class="a" style="animation:fade 1s .8s forwards" d="{desc}" fill="{ink.MUTED}"/>'
            f'<path class="a" style="animation:fade 1s 1s forwards" d="{tags.d}" fill="{ink.VERMILION}"/>')
    return ink.svg(CARD_W, CARD_H, body, seal_css, label=f'{p["name"]}: {p.get("desc", "")}')


def empty_card(fonts, cfg, seed):
    """虚位以待：作品数为奇数时补齐网格。"""
    g_defs, frame = _card_frame(seed + 99, ink.PAPER_EMPTY, ink.EDGE_EMPTY, dashed=True)
    latin = is_latin(cfg["title"])
    head = fonts["serif_semibold"].run(cfg["title"], CARD_W / 2, 79, 26, spacing=3 if latin else 5, anchor="middle")
    sub = fonts["serif"].run(cfg["subtitle"], CARD_W / 2, 106, 11.5, spacing=1 if latin else 2.8, anchor="middle")
    body = (f"<defs>{g_defs}</defs>{frame}"
            f'<path class="a" style="animation:fade 1.4s .6s forwards" d="{head.d}" fill="{ink.MUTED}"/>'
            f'<path class="a" style="animation:fade 1.4s .9s forwards" d="{sub.d}" fill="{ink.MUTED}" fill-opacity=".8"/>')
    return ink.svg(CARD_W, CARD_H, body, label=cfg["title"])
