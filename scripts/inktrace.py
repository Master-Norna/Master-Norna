"""墨痕：一年的提交记录化作墨点。提交越多，墨点越大越浓；最勤的几天用朱砂；今天画一个朱圈。

墨点像落在宣纸上一样慢慢洇开（不弹跳），从左往右、略带随机地浮现。
"""
import json
import random
import urllib.request
from datetime import date, timedelta

import almanac
import ink
from glyphs import num

W, H = 840, 190
X0, Y0, STEP = 63, 36, 14
# GitHub 的 5 档活跃度 -> (半径, 浓度)
LEVELS = [(1.5, .14), (2.6, .3), (3.4, .5), (4.2, .7), (4.9, .88)]
GQL_LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

CSS = """
.d{opacity:0;transform-box:fill-box;transform-origin:center;animation:soak 1.2s cubic-bezier(.25,.6,.3,1) forwards}
@keyframes soak{0%{opacity:0;transform:scale(.3)}30%{opacity:1}100%{opacity:1;transform:scale(1)}}
.today{opacity:0;transform-box:fill-box;transform-origin:center;animation:fade .8s 2.3s forwards,breathe 2.4s ease-in-out 3s infinite alternate}
@keyframes breathe{to{transform:scale(1.35)}}
"""


def fetch(login, token):
    """用 GraphQL 取过去一年的贡献日历，返回 [(date, count, level)]。"""
    query = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar"
             "{weeks{contributionDays{date contributionCount contributionLevel}}}}}}")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(date.fromisoformat(d["date"]), d["contributionCount"], GQL_LEVEL[d["contributionLevel"]])
            for w in weeks for d in w["contributionDays"]]


def mock(today, seed):
    """没有 token 时的示意数据（本地预览用），与 GitHub 日历同样从 53 周前的周日开始。"""
    rng = random.Random(seed)
    start = today - timedelta(days=(today.weekday() + 1) % 7 + 52 * 7)
    days, d = [], start
    while d <= today:
        busy = rng.random()
        count = 0 if busy < .45 else int(rng.expovariate(.25)) + 1
        level = 0 if count == 0 else min(4, 1 + count // 3)
        days.append((d, count, level))
        d += timedelta(days=1)
    return days


def build(fonts, days, seed, highlight=2, labels_lang="en"):
    serif = fonts["serif"]
    rng = random.Random(seed)
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)  # 所在周的周日
    top = {d for d, c, _ in sorted(days, key=lambda x: -x[1])[:highlight] if c > 0}

    dots, labels = [], []
    today = days[-1]
    last_label_col, last_season = -99, None
    for d, count, level in days:
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        cx, cy = X0 + col * STEP, Y0 + row * STEP
        delay = .3 + col * .034 + row * .012 + rng.uniform(0, .15)
        if d in top:
            dots.append(f'<circle class="d" style="animation-delay:{delay:.2f}s" cx="{cx}" cy="{cy}" r="5.2" fill="{ink.VERMILION}"/>')
        else:
            r, op = LEVELS[level]
            dots.append(f'<circle class="d" style="animation-delay:{delay:.2f}s" cx="{cx}" cy="{cy}" r="{r}" '
                        f'fill="{ink.INK}" fill-opacity="{op}"/>')
        if row == 0 or d == days[0][0]:  # 每列第一天决定时令标签
            name = almanac.season_en(d) if labels_lang == "en" else almanac.year(d) + almanac.season(d)
            if name != last_season:
                if col - last_label_col < (6 if labels_lang == "en" else 4) and labels:
                    labels.pop()  # 太挤：去掉前一个（通常是开头只占一两周的残季）
                labels.append((col, name))
                last_label_col, last_season = col, name

    texts = []
    for i, (col, name) in enumerate(labels):
        r = serif.run(name, X0 - 5 + col * STEP, 161, 12, spacing=2.5 if labels_lang != "en" else 1)
        texts.append(f'<path class="a" style="animation:fade 1s {2.2 + .12 * i:.2f}s forwards" d="{r.d}" fill="{ink.MUTED}"/>')

    tcol, trow = (today[0] - start).days // 7, (today[0].weekday() + 1) % 7
    g_defs, g_rect = ink.grain("grain", 2, 2, W - 4, H - 4, seed)
    body = (f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="3" fill="{ink.PAPER}" stroke="{ink.EDGE}"/>{g_rect}'
            f'<defs>{g_defs}<filter id="bleed" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="3"/>'
            f'<feDisplacementMap in="SourceGraphic" scale="1.8" result="rough"/>'
            f'<feGaussianBlur in="rough" stdDeviation="1.3" result="blur"/>'
            f'<feComponentTransfer in="blur" result="halo"><feFuncA type="linear" slope=".4"/></feComponentTransfer>'
            f'<feMerge><feMergeNode in="halo"/><feMergeNode in="rough"/></feMerge></filter></defs>'
            f'<g filter="url(#bleed)">{"".join(dots)}</g>'
            f'<circle class="today" cx="{X0 + tcol * STEP}" cy="{Y0 + trow * STEP}" r="7.5" fill="none" '
            f'stroke="{ink.VERMILION}" stroke-width="1" stroke-opacity=".6"/>{"".join(texts)}')
    total = sum(c for _, c, _ in days)
    return ink.svg(W, H, body, CSS, label=f"{total} contributions in the last year")
