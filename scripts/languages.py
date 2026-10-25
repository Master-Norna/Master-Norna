"""语言：写过哪些语言。一个仓库只算它的主语言，按仓库数排。

两处仓库都算：自己名下公开、非 fork 的（own），和合并过 PR 的别人的项目（merged）。
不按代码量排：一个大仓库就能盖过别的，Lean 那样的小仓库会排不上；HTML、CSS 这类陪衬也就挤不进来。
画法是圈点：一个仓库一粒，墨点自己的、朱点合并进的（同「开源」的朱点），点后写总数。
"""
import github
import ink
from glyphs import num

W, X0 = 840, 44
DOTS_X, TOP, PITCH, STEP = X0 + 120, 64, 30, 13
MAX_DOTS = 40  # 一行最多画几粒：再多就按比例缩，后面的数照写实数

OWN = """query($login:String!){user(login:$login){repositories(first:100,ownerAffiliations:OWNER,isFork:false,
privacy:PUBLIC){nodes{primaryLanguage{name}}}}}"""
MERGED = """query($q:String!,$after:String){search(type:ISSUE,first:100,query:$q,after:$after){
pageInfo{hasNextPage endCursor}nodes{...on PullRequest{repository{nameWithOwner isPrivate primaryLanguage{name}}}}}}"""


def fetch(login, token):
    """返回 [(语言, 自己的仓库数, 合并过 PR 的项目数)]，按两者之和从多到少。"""
    count = {}

    def add(lang, key):
        if lang:
            c = count.setdefault(lang["name"], {"own": 0, "merged": 0})
            c[key] += 1

    for r in github.graphql(OWN, {"login": login}, token)["user"]["repositories"]["nodes"]:
        add(r["primaryLanguage"], "own")
    seen, after = set(), None
    for _ in range(10):
        data = github.graphql(MERGED, {"q": f"is:pr is:merged author:{login} -user:{login}", "after": after}, token)["search"]
        for n in data["nodes"]:
            repo = n.get("repository")
            if repo and not repo["isPrivate"] and repo["nameWithOwner"] not in seen:
                seen.add(repo["nameWithOwner"])
                add(repo["primaryLanguage"], "merged")
        if not data["pageInfo"]["hasNextPage"]:
            break
        after = data["pageInfo"]["endCursor"]
    return sorted(((k, v["own"], v["merged"]) for k, v in count.items()), key=lambda x: -(x[1] + x[2]))


def mock():
    """没有 token 时的示意数据（本地预览用）。"""
    return [("Python", 5, 7), ("Rust", 3, 3), ("JavaScript", 1, 0), ("Lean", 1, 0)]


def build(fonts, langs, rows=6):
    serif, serif_sb = fonts["serif"], fonts["serif_semibold"]
    langs = langs[:rows]
    parts = [_legend(serif, [(ink.INK, "own repo"), (ink.VERMILION, "project merged into")], 30)]
    for i, (name, own, merged) in enumerate(langs):
        y = TOP + i * PITCH
        total = own + merged
        shown = min(total, MAX_DOTS)
        own_shown = round(own * shown / total) if total else 0
        n = serif_sb.run(name, X0, y, 13.5)
        parts.append(f'<path class="a" style="animation:fade .9s {num(.4 + .1 * i)}s forwards" d="{n.d}" fill="{ink.INK}"/>')
        for j in range(shown):
            parts.append(f'<circle class="a" style="animation:fade .5s {num(.5 + .1 * i + .04 * j)}s forwards" '
                         f'cx="{DOTS_X + 4 + j * STEP}" cy="{y - 4.5}" r="3.4" fill="{ink.INK if j < own_shown else ink.VERMILION}"/>')
        c = serif.run(str(total), DOTS_X + shown * STEP + 8, y, 12)
        parts.append(f'<path class="a" style="animation:fade .9s {num(.7 + .1 * i)}s forwards" d="{c.d}" fill="{ink.MUTED}"/>')
    h = TOP + (len(langs) - 1) * PITCH + 30
    g_defs, g_rect = ink.grain("grain", 2, 2, W - 4, h - 4, 7)
    body = (f'<defs>{g_defs}</defs><rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="3" fill="{ink.PAPER}" '
            f'stroke="{ink.EDGE}"/>{g_rect}{"".join(parts)}')
    label = "Languages by repository: " + ", ".join(f"{n} {o + m}" for n, o, m in langs)
    return ink.svg(W, h, body, label=label)


def _legend(serif, items, y):
    """右上角图例：[(颜色, 字)…]，从右往左排。"""
    x, out = W - X0, []
    for color, text in reversed(items):
        t = serif.run(text, x, y, 10.5, spacing=1.5, anchor="end")
        x -= t.width + 9
        out.append(f'<circle cx="{num(x)}" cy="{y - 3.5}" r="3" fill="{color}"/><path d="{t.d}" fill="{ink.MUTED}"/>')
        x -= 22
    return f'<g class="a" style="animation:fade 1s .6s forwards">{"".join(out)}</g>'
