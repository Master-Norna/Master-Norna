"""读取 config.yml，从 google/fonts 取字体，生成 assets/ 下的全部 SVG，并更新 README 的作品区。

用法：python scripts/build.py
  - 设了 GITHUB_TOKEN（Actions 里自动有）时，「墨痕」用真实提交记录；否则用示意数据。
  - BUILD_DATE=2026-02-04 可指定日期（默认北京时间今天），用于预览落款。
"""
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
    import fontTools  # noqa: F401
except ModuleNotFoundError as e:
    sys.exit(f"缺少依赖 {e.name}。当前用的 Python 是：{sys.executable}\n"
             f"请运行：\"{sys.executable}\" -m pip install -r scripts/requirements.txt")

import almanac
import banner
import inktrace
import sections
from glyphs import Font

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
GOOGLE_FONTS = "https://raw.githubusercontent.com/google/fonts/main/"


def fetch_font(rel, font_dir):
    path = font_dir / Path(rel).name
    if not path.exists():
        print(f"下载字体 {rel}")
        font_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".part")
        with urllib.request.urlopen(GOOGLE_FONTS + urllib.parse.quote(rel), timeout=180) as r, open(tmp, "wb") as f:
            f.write(r.read())
        tmp.replace(path)
    return str(path)


def today():
    if os.environ.get("BUILD_DATE"):
        return date.fromisoformat(os.environ["BUILD_DATE"])
    return datetime.now(timezone(timedelta(hours=8))).date()


written = set()


def write(name, text):
    out = ASSETS / name
    out.parent.mkdir(parents=True, exist_ok=True)
    old = out.read_text(encoding="utf-8") if out.exists() else None
    if old != text:
        out.write_text(text, encoding="utf-8", newline="\n")
    written.add(name)
    print(f"{'更新' if old != text else '未变'} assets/{name}  ({len(text.encode()) / 1024:.0f} KB)")


def works_block(works, has_empty, empty_alt):
    lines = []
    for p in works:
        img = f'<img src="assets/card-{p["id"]}.svg" width="49%" alt="{p["name"]}">'
        lines.append(f'<a href="{p["url"]}">{img}</a>' if p.get("url") else img)
    if has_empty:
        lines.append(f'<img src="assets/card-empty.svg" width="49%" alt="{empty_alt}">')
    return "\n".join(lines)


def update_readme(block):
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    new, n = re.subn(r"(<!-- works:start -->\n).*?(\n<!-- works:end -->)",
                     lambda m: m.group(1) + block + m.group(2), text, flags=re.S)
    if n == 0:
        print("README.md 里没找到 <!-- works:start --> / <!-- works:end -->，跳过作品区")
    elif new != text:
        readme.write_text(new, encoding="utf-8", newline="\n")
        print("更新 README.md 作品区")


def main():
    cfg = yaml.safe_load((ROOT / "config.yml").read_text(encoding="utf-8"))
    font_dir = ROOT / cfg["fonts"].get("dir", "fonts")
    serif_path = fetch_font(cfg["fonts"]["serif"], font_dir)
    fonts = {
        "serif": Font(serif_path, 400),
        "serif_medium": Font(serif_path, 500),
        "serif_semibold": Font(serif_path, 600),
        "serif_bold": Font(serif_path, 700),
        "brush": Font(fetch_font(cfg["fonts"]["brush"], font_dir)),
    }
    seed = cfg.get("seed", 7)
    day = today()

    b = cfg["banner"]
    write("banner.svg", banner.build(b, fonts, b.get("colophon", "").format(**almanac.fields(day)), seed))

    for sid, s in cfg["sections"].items():
        for theme in ("light", "dark"):
            write(f"title-{sid}-{theme}.svg", sections.title(fonts, s["title"], s.get("note", ""), theme))
    for theme in ("light", "dark"):
        write(f"intro-{theme}.svg", sections.intro(fonts, cfg["intro"], theme))

    works = cfg.get("works") or []
    for i, p in enumerate(works):
        write(f"card-{p['id']}.svg", sections.card(fonts, p, i, seed))
    has_empty = len(works) % 2 == 1
    if has_empty:
        write("card-empty.svg", sections.empty_card(fonts, cfg["empty_card"], seed))
    update_readme(works_block(works, has_empty, cfg["empty_card"]["title"]))

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    days = None
    if token:
        try:
            days = inktrace.fetch(cfg["profile"]["login"], token)
        except Exception as e:  # 网络或权限问题：保留上一次的 ink.svg，不拿示意数据覆盖
            print(f"取提交记录失败，保留现有 assets/ink.svg：{e}")
            written.add("ink.svg")
    else:
        print("未设置 GITHUB_TOKEN：墨痕使用示意数据（Actions 里会自动用真实提交记录）")
        days = inktrace.mock(day, seed)
    if days:
        it = cfg.get("inktrace", {})
        write("ink.svg", inktrace.build(fonts, days, seed, it.get("highlight", 2), it.get("labels", "en")))

    # 清理不再使用的卡片（比如从 config 里删掉的作品）
    for old in ASSETS.glob("card-*.svg"):
        if old.name not in written:
            old.unlink()
            print(f"删除 assets/{old.name}")


if __name__ == "__main__":
    sys.exit(main())
