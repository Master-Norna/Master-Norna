"""干支纪年与时令（按「节」近似划分，误差一两天，够落款用）。"""
GAN, ZHI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
# 四立：(月, 日) 为节气的大致日期
SEASONS = [((2, 4), "春"), ((5, 6), "夏"), ((8, 8), "秋"), ((11, 7), "冬")]
MONTHS = [((1, 6), "季冬"), ((2, 4), "孟春"), ((3, 6), "仲春"), ((4, 5), "季春"),
          ((5, 6), "孟夏"), ((6, 6), "仲夏"), ((7, 7), "季夏"), ((8, 8), "孟秋"),
          ((9, 8), "仲秋"), ((10, 8), "季秋"), ((11, 7), "孟冬"), ((12, 7), "仲冬")]


def year(d):
    """干支年，以立春为岁首。"""
    y = d.year - (1 if (d.month, d.day) < (2, 4) else 0)
    return GAN[(y - 4) % 10] + ZHI[(y - 4) % 12]


def _pick(d, table, before_first):
    name = before_first
    for start, n in table:
        if (d.month, d.day) >= start:
            name = n
    return name


def season(d):
    return _pick(d, SEASONS, "冬")


def month(d):
    return _pick(d, MONTHS, "仲冬")


# 二十四节气交节的日子（逐年差一两天，取常见的那天；同「言」src/12-season.js）
TERMS = [((1, 5), "小寒"), ((1, 20), "大寒"), ((2, 4), "立春"), ((2, 19), "雨水"), ((3, 5), "惊蛰"), ((3, 20), "春分"),
         ((4, 4), "清明"), ((4, 20), "谷雨"), ((5, 5), "立夏"), ((5, 21), "小满"), ((6, 5), "芒种"), ((6, 21), "夏至"),
         ((7, 7), "小暑"), ((7, 22), "大暑"), ((8, 7), "立秋"), ((8, 23), "处暑"), ((9, 7), "白露"), ((9, 23), "秋分"),
         ((10, 8), "寒露"), ((10, 23), "霜降"), ((11, 7), "立冬"), ((11, 22), "小雪"), ((12, 7), "大雪"), ((12, 21), "冬至")]


def term(d):
    """当下所在的节气（一月五日前还在去年的冬至）。"""
    return _pick(d, TERMS, "冬至")


def fields(d):
    """落款模板可用的占位符。"""
    return {"year": year(d), "season": season(d), "month": month(d), "term": term(d)}


SEASONS_EN = {"春": "Spring", "夏": "Summer", "秋": "Autumn", "冬": "Winter"}


def season_en(d):
    """英文时令标签，如 Autumn 2025（冬季跨年时记在入冬那一年）。"""
    name = season(d)
    y = d.year - (1 if name == "冬" and (d.month, d.day) < (2, 4) else 0)
    return f"{SEASONS_EN[name]} {y}"
