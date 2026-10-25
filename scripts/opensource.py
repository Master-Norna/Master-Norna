"""开源：合并进别人仓库的 PR（只算已合并的，还在审、关掉的不计）。

build：上面两个数（已合并 / 项目），下面列出合并最多的几个项目，右侧一粒朱点一个 PR。
trail：行迹 —— 最近合并的几条，细竖线串起朱点，标题一行、下面一行淡字「日期 仓库」。
"""
from datetime import date, datetime

import github
import ink
from glyphs import num

W = 840
X0, COL_W = 44, 364          # 左列起点、每列宽（两列间隔 24）
ROW_TOP, ROW_PITCH = 150, 30
MAX_DOTS = 5                 # 每个项目最多画几粒朱点

CSS = """
.d{opacity:0;transform-box:fill-box;transform-origin:center;animation:soak .9s cubic-bezier(.25,.6,.3,1) forwards}
@keyframes soak{0%{opacity:0;transform:scale(.3)}30%{opacity:1}100%{opacity:1;transform:scale(1)}}
"""

QUERY = """query($q:String!,$after:String){search(type:ISSUE,first:100,query:$q,after:$after){
pageInfo{hasNextPage endCursor}
nodes{...on PullRequest{title mergedAt repository{nameWithOwner stargazerCount isPrivate}}}}}"""


def fetch(login, token):
    """取合并进别人仓库（不含自己名下）的全部 PR，返回 [(仓库, 星数, 合并日期, 标题)]。"""
    prs, after = [], None
    for _ in range(10):  # 最多 1000 条
        data = github.graphql(QUERY, {"q": f"is:pr is:merged author:{login} -user:{login}", "after": after}, token)["search"]
        for n in data["nodes"]:
            repo = n.get("repository")
            if repo and not repo["isPrivate"] and n.get("mergedAt"):
                merged = datetime.fromisoformat(n["mergedAt"].replace("Z", "+00:00")).date()
                prs.append((repo["nameWithOwner"], repo["stargazerCount"], merged, n["title"]))
        if not data["pageInfo"]["hasNextPage"]:
            break
        after = data["pageInfo"]["endCursor"]
    return prs


def mock():
    """没有 token 时的示意数据（本地预览用）。"""
    sample = [("ink-lab/brush", 12800, 3), ("paper-co/fiber", 4200, 2), ("seal/stamp", 930, 2),
              ("scroll/mount", 2100, 1), ("inkstone/grind", 640, 1), ("ink-lab/wash", 310, 1)]
    repos = [(repo, stars) for repo, stars, n in sample for _ in range(n)]
    return [(repo, stars, date(2026, 10, 24 - i), f"fix: an example pull request #{i}") for i, (repo, stars) in enumerate(repos)]


def stars_text(n):
    return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "k" if n >= 1000 else str(n)


def fit(font, text, size, width):
    """放不下就截断加省略号。"""
    if font.measure(text, size) <= width:
        return text
    while text and font.measure(text + "…", size) > width:
        text = text[:-1]
    return text + "…"


def build(fonts, prs, rows=6):
    serif, serif_sb = fonts["serif"], fonts["serif_semibold"]
    repos = {}
    for name, stars, *_ in prs:
        r = repos.setdefault(name, {"stars": stars, "merged": 0})
        r["merged"] += 1
    ranked = sorted(repos.items(), key=lambda x: (-x[1]["merged"], -x[1]["stars"]))
    shown = ranked[:rows]

    parts = []
    # ---- 两个数 ----
    stats = [(len(prs), "MERGED PULL REQUESTS"), (len(repos), "PROJECTS")]
    for i, (value, label) in enumerate(stats):
        x = X0 + i * 220
        v = fonts["serif_medium"].run(str(value), x, 72, 38)
        lb = serif.run(label, x + 1, 96, 10.5, spacing=2.6)
        parts.append(f'<g class="a" style="animation:rise .8s {num(.2 + .12 * i)}s forwards">'
                     f'<path d="{v.d}" fill="{ink.VERMILION if i == 0 else ink.INK}"/>'
                     f'<path d="{lb.d}" fill="{ink.MUTED}"/></g>')

    # 右上角图例：● = 一个合并的 PR（不列项目时没有点，也就不要图例）
    if shown:
        t = serif.run("one merged PR", W - X0, 96, 10.5, spacing=1.5, anchor="end")
        parts.append(f'<g class="a" style="animation:fade 1s .6s forwards"><circle cx="{num(W - X0 - t.width - 9)}" cy="92.5" '
                     f'r="3" fill="{ink.VERMILION}"/><path d="{t.d}" fill="{ink.MUTED}"/></g>')

    parts.append(f'<rect class="a fx" style="transform-origin:left;animation:growx 1s .5s forwards,fade .1s .5s forwards" '
                 f'x="{X0}" y="118" width="{W - 2 * X0}" height=".8" fill="{ink.EDGE}"/>')

    # ---- 项目列表：两列，按行交错浮现 ----
    for k, (name, r) in enumerate(shown):
        row, col = k // 2, k % 2
        x, y = X0 + col * (COL_W + 24), ROW_TOP + row * ROW_PITCH
        delay = .8 + .1 * k
        dots, dx = [], x + COL_W
        extra = r["merged"] - MAX_DOTS
        if extra > 0:  # 点太多会挤掉仓库名：只画 MAX_DOTS 粒，余下的写成「+N」
            more = serif.run(f"+{extra}", dx, y, 10.5, spacing=.6, anchor="end")
            dots.append(f'<path class="a" style="animation:fade .6s {num(delay + .6)}s forwards" d="{more.d}" fill="{ink.MUTED}"/>')
            dx -= more.width + 4
        for j in range(min(r["merged"], MAX_DOTS)):
            dx -= 10
            dots.append(f'<circle class="d" style="animation-delay:{num(delay + .3 + .06 * j)}s" cx="{num(dx + 3)}" cy="{y - 4.5}" '
                        f'r="3" fill="{ink.VERMILION}"/>')
        star = serif.run(f"★ {stars_text(r['stars'])}", dx - 8, y, 10.5, spacing=.6, anchor="end")
        owner, repo = name.split("/", 1)
        room = dx - 8 - star.width - 14 - x
        o = serif.run(fit(serif, owner + "/", 13.5, room / 2), x, y, 13.5)
        n = serif_sb.run(fit(serif_sb, repo, 13.5, room - o.width), x + o.width, y, 13.5)
        parts.append(f'<g class="a" style="animation:fade .9s {num(delay)}s forwards">'
                     f'<path d="{o.d}" fill="{ink.MUTED}"/><path d="{n.d}" fill="{ink.INK}"/>'
                     f'<path d="{star.d}" fill="{ink.MUTED}" fill-opacity=".85"/></g>{"".join(dots)}')

    h = ROW_TOP + (len(shown) + 1) // 2 * ROW_PITCH + 6
    return ink.svg(W, h, _paper(h, parts), CSS,
                   label=f"{len(prs)} pull requests merged into {len(repos)} open source projects")


def trail(fonts, prs, rows=4):
    """行迹：最近合并的 rows 条。"""
    serif, serif_sb = fonts["serif"], fonts["serif_semibold"]
    recent = sorted(((d, repo, title) for repo, _, d, title in prs), reverse=True)[:rows]
    top, pitch = 44, 46
    span = max(len(recent) - 1, 0) * pitch
    parts = [f'<rect class="a" style="animation:fade .6s .1s forwards" x="55.6" y="{top - 6}" width=".8" '
             f'height="{span + 12}" fill="{ink.EDGE}"/>']
    for i, (d, repo, title) in enumerate(recent):
        y = top + i * pitch
        t = serif_sb.run(fit(serif_sb, title, 14, W - 80 - X0), 80, y, 14)
        meta = serif.run(f"{d:%Y·%m·%d}   {repo}", 80, y + 19, 11, spacing=1)
        # 朱点描一圈纸色，压在竖线上像断开一截
        parts.append(f'<circle class="a" style="animation:fade .6s {num(.3 + .15 * i)}s forwards" cx="56" cy="{y - 5}" r="4" '
                     f'fill="{ink.VERMILION}" stroke="{ink.PAPER}" stroke-width="2"/>'
                     f'<g class="a" style="animation:fade .9s {num(.35 + .15 * i)}s forwards">'
                     f'<path d="{t.d}" fill="{ink.INK}"/><path d="{meta.d}" fill="{ink.MUTED}"/></g>')
    h = top + span + 40
    return ink.svg(W, h, _paper(h, parts), label="Recently merged: " + "; ".join(f"{t} ({r})" for _, r, t in recent))


def _paper(h, parts):
    g_defs, g_rect = ink.grain("grain", 2, 2, W - 4, h - 4, 7)
    return (f'<defs>{g_defs}</defs><rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="3" fill="{ink.PAPER}" '
            f'stroke="{ink.EDGE}"/>{g_rect}{"".join(parts)}')
