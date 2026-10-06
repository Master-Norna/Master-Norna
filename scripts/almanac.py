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


def fields(d):
    """落款模板可用的占位符。"""
    return {"year": year(d), "season": season(d), "month": month(d)}


SEASONS_EN = {"春": "Spring", "夏": "Summer", "秋": "Autumn", "冬": "Winter"}


def season_en(d):
    """英文时令标签，如 Autumn 2025（冬季跨年时记在入冬那一年）。"""
    name = season(d)
    y = d.year - (1 if name == "冬" and (d.month, d.day) < (2, 4) else 0)
    return f"{SEASONS_EN[name]} {y}"
