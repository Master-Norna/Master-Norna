"""笔意与时令画，移植自「言」src/03-brush.js、src/12-season.js。

一笔是一串二次曲线（起点、控制点、终点、控制点、终点……），照「起笔顿、行笔匀、收笔出锋」的笔形铺成一片面。
时令画是 300 × 340 的格子里贴右下角长出来的一件：春柳、夏荷、秋苇、冬梅，只用一色，浓淡靠 fill-opacity。
"""
import math


def _f(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


def stroke(points, width, tail=0.0, head=0.78):
    """一笔。points 是 x0 y0 cx cy x1 y1 [cx cy x2 y2 …]；width 最粗处；tail 收笔处的粗细比（0 出锋，0.6 以上是顿笔收住）。"""
    samples = []
    for i in range(0, len(points) - 4, 4):
        x0, y0, cx, cy, x1, y1 = points[i:i + 6]
        for k in range(1 if i else 0, 13):
            t = k / 12
            u = 1 - t
            samples.append((u * u * x0 + 2 * u * t * cx + t * t * x1, u * u * y0 + 2 * u * t * cy + t * t * y1))
    lengths = [0.0]
    for (ax, ay), (bx, by) in zip(samples, samples[1:]):
        lengths.append(lengths[-1] + math.hypot(bx - ax, by - ay))
    total = lengths[-1] or 1

    def shape(t):
        if t < .16:
            return head + (1 - head) * t / .16
        return 1 if t < .62 else 1 - (1 - tail) * (t - .62) / .38

    left, right = [], []
    for i, (x, y) in enumerate(samples):
        ax, ay = samples[max(0, i - 1)]
        bx, by = samples[min(len(samples) - 1, i + 1)]
        ln = math.hypot(bx - ax, by - ay) or 1
        half = width * shape(lengths[i] / total) / 2
        nx, ny = -(by - ay) / ln, (bx - ax) / ln
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    # 起笔是个圆头：从右边绕回左边时往笔尖反方向鼓出去一点
    (sx, sy), (tx, ty) = samples[0], samples[1]
    back = math.hypot(tx - sx, ty - sy) or 1
    bulge = (sx - (tx - sx) / back * width * .55, sy - (ty - sy) / back * width * .55)
    line = "".join(f"L{_f(x)} {_f(y)}" for x, y in left[1:] + right[::-1])
    return f'<path d="M{_f(left[0][0])} {_f(left[0][1])}{line}Q{_f(bulge[0])} {_f(bulge[1])} {_f(left[0][0])} {_f(left[0][1])}Z"/>'


def _bezier(p, t):
    u = 1 - t
    return u * u * p[0] + 2 * u * t * p[2] + t * t * p[4], u * u * p[1] + 2 * u * t * p[3] + t * t * p[5]


def spring():
    """春 · 柳：一枝从右边探进来，垂下四缕；叶是缕上一串细笔，两边交错、朝下斜出。"""
    s = stroke([300, 18, 252, 4, 196, 34], 3, tail=.4, head=.5)
    for i, (x, y, sway, ln) in enumerate([(276, 12, 40, 250), (246, 12, 22, 300), (220, 22, -6, 236), (204, 32, 12, 160)]):
        end, ctrl = (x - sway * .4, y + ln), (x - sway, y + ln * .45)
        p = [x, y, *ctrl, *end]
        s += stroke(p, 1.3, tail=0, head=.6)
        for k in range(1, 9):
            t = k / 9 + (i % 2) * .04
            if t > .96:
                break
            px, py = _bezier(p, t)
            side = 1 if k % 2 else -1
            size = 11 + 7 * math.sin(math.pi * t) - (k % 3) * 2
            s += stroke([px, py, px + side * size * .3, py + size * .4, px + side * size * .24, py + size], 2.5, tail=0, head=.3)
    return s


def summer():
    """夏 · 荷：一张侧着的叶——淡染一片，前沿一道浓些的叶边，叶脉散向叶缘；一茎落到底，旁边一茎擎着未开的苞。"""
    cx, cy, rx, ry, tilt = 188, 196, 102, 38, math.radians(-10)

    def rim(deg):
        a = math.radians(deg)
        x, y = math.cos(a) * rx, math.sin(a) * ry
        return cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)

    s = f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" transform="rotate(-10 {cx} {cy})" fill-opacity=".3"/>'
    s += stroke([c for d in (10, 50, 90, 130, 170) for c in rim(d)], 2.2, tail=0, head=.2)
    hx, hy = cx + 6, cy + 16
    for i in range(9):
        ex, ey = rim(-178 + i * 22)
        s += stroke([hx, hy, (hx + ex) / 2, (hy + ey) / 2 + 4, ex, ey], 1.1, tail=0, head=.5)
    s += stroke([hx, hy, 214, 270, 204, 340], 3, tail=.7, head=.5)
    s += stroke([104, 340, 98, 280, 74, 236], 2, tail=.8, head=.6)
    s += stroke([74, 238, 56, 216, 70, 186], 8, tail=0, head=.4) + stroke([76, 238, 92, 214, 72, 186], 6.5, tail=0, head=.4)
    return s


def autumn():
    """秋 · 苇：三茎从底边斜出、梢头各垂一穗（几笔细丝往左下散开，越往下越长）；一片叶从茎腰扫出去。"""
    stalks = [(262, 340, 250, 214, 172, 56, 3.2, 11, 54), (286, 340, 284, 236, 238, 96, 2.6, 9, 44),
              (238, 340, 222, 270, 160, 176, 2.1, 7, 34)]
    s = ""
    for x0, y0, cx, cy, x1, y1, w, n, ln in stalks:
        p = [x0, y0, cx, cy, x1, y1]
        s += stroke(p, w, tail=.15, head=.6)
        for i in range(n):
            hx, hy = _bezier(p, 1 - i / n * .3)
            ll = ln * (.45 + i / n * .55)
            lean = 7 if i % 3 == 1 else -5 if i % 3 == 2 else 0
            s += stroke([hx, hy, hx - ll * .5 + lean, hy + ll * .12, hx - ll * .68 + lean * 1.6, hy + ll * .82], 1.25, tail=0, head=.55)
    lx, ly = _bezier([262, 340, 250, 214, 172, 56], .4)
    return s + stroke([lx, ly, lx - 46, ly - 30, lx - 92, ly + 14], 5, tail=0, head=.3)


def winter():
    """冬 · 梅：老枝从右下折上来、转一个弯，几根细枝挺出去；花五瓣一朵，有的还是苞。"""
    s = stroke([300, 300, 252, 286, 224, 236, 202, 196, 150, 176], 6.5, tail=.3, head=.6)
    s += stroke([226, 240, 232, 174, 216, 104], 2.8, tail=.1, head=.7)
    s += stroke([172, 182, 130, 180, 86, 152], 2.2, tail=.1, head=.7)
    s += stroke([220, 150, 242, 128, 254, 98], 1.5, tail=.1, head=.7)

    def bloom(x, y, r):
        petals = "".join(f'<circle cx="{_f(x + math.cos(math.radians(i * 72 - 90)) * r)}" '
                         f'cy="{_f(y + math.sin(math.radians(i * 72 - 90)) * r)}" r="{_f(r * .66)}" fill-opacity=".5"/>'
                         for i in range(5))
        return petals + f'<circle cx="{x}" cy="{y}" r="{_f(r * .32)}"/>'

    s += bloom(214, 100, 7.5) + bloom(86, 150, 6.5) + bloom(150, 174, 6) + bloom(254, 94, 5)
    return s + '<circle cx="118" cy="170" r="2.8"/><circle cx="234" cy="146" r="2.6"/><circle cx="196" cy="212" r="2.4"/>'


SEASON_MARKS = {"春": spring, "夏": summer, "秋": autumn, "冬": winter}
