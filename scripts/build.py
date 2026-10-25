"""读取 config.yml，从 google/fonts 取字体，生成 assets/ 下的全部 SVG，并更新 README 的作品区。

用法：python scripts/build.py
  - 设了 GITHUB_TOKEN（Actions 里自动有）时，「墨痕」「开源」用真实数据；否则用示意数据。
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
import ink
import inktrace
import opensource
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


def write_themed(stem, make):
    """铺纸的组件出两版：assets/<stem>-light.svg 浅纸、-dark.svg 「言」的暗纸，README 用 <picture> 切换。"""
    for theme, palette in (("light", ink.LIGHT), ("dark", ink.DARK)):
        ink.use(palette)
        write(f"{stem}-{theme}.svg", make())
    ink.use(ink.LIGHT)


def keep_themed(stem):
    """取数失败：两版都保留上一次的，不拿示意数据覆盖，也别被当成旧文件清掉。"""
    written.update({f"{stem}-light.svg", f"{stem}-dark.svg"})


def picture(stem, alt, width="100%"):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{stem}-dark.svg">'
            f'<img src="assets/{stem}-light.svg" width="{width}" alt="{alt}"></picture>')


def works_block(works, has_empty, empty_alt):
    lines = []
    for p in works:
        pic = picture(f'card-{p["id"]}', p["name"], "49%")
        lines.append(f'<a href="{p["url"]}">{pic}</a>' if p.get("url") else pic)
    if has_empty:
        lines.append(picture("card-empty", empty_alt, "49%"))
    return "\n".join(lines)


def update_readme(block):
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    new, n = re.subn(r"(<!-- works:start -->\n).*?(<!-- works:end -->)",
                     lambda m: m.group(1) + block + "\n" + m.group(2), text, flags=re.S)
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
    colophon = b.get("colophon", "").format(**almanac.fields(day))
    write_themed("banner", lambda: banner.build(b, fonts, colophon, seed))

    for sid, s in cfg["sections"].items():
        for theme in ("light", "dark"):
            write(f"title-{sid}-{theme}.svg", sections.title(fonts, s["title"], s.get("note", ""), theme))
    for theme in ("light", "dark"):
        write(f"intro-{theme}.svg", sections.intro(fonts, cfg["intro"], theme))

    works = cfg.get("works") or []
    for i, p in enumerate(works):
        write_themed(f"card-{p['id']}", lambda: sections.card(fonts, p, i, seed))
    has_empty = len(works) % 2 == 1
    if has_empty:
        write_themed("card-empty", lambda: sections.empty_card(fonts, cfg["empty_card"], seed))
    update_readme(works_block(works, has_empty, cfg["empty_card"]["title"]))

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    days = None
    if token:
        try:
            days = inktrace.fetch(cfg["profile"]["login"], token)
        except Exception as e:  # 网络或权限问题：保留上一次的墨痕
            print(f"取提交记录失败，保留现有 assets/ink-*.svg：{e}")
            keep_themed("ink")
    else:
        print("未设置 GITHUB_TOKEN：墨痕、开源使用示意数据（Actions 里会自动用真实记录）")
        days = inktrace.mock(day, seed)
    if days:
        it = cfg.get("inktrace", {})
        write_themed("ink", lambda: inktrace.build(fonts, days, seed, it.get("highlight", 2), it.get("labels", "en")))

    prs = None
    if token:
        try:
            prs = opensource.fetch(cfg["profile"]["login"], token)
        except Exception as e:
            print(f"取 PR 记录失败，保留现有 assets/opensource-*.svg、merged-*.svg：{e}")
            keep_themed("opensource")
            keep_themed("merged")
    else:
        prs = opensource.mock()
    if prs is not None:
        oc = cfg.get("opensource", {})
        write_themed("opensource", lambda: opensource.build(fonts, prs, oc.get("rows", 6)))
        write_themed("merged", lambda: opensource.trail(fonts, prs, oc.get("recent", 4)))

    # 清理不再生成的素材（比如从 config 里删掉的作品、改成明暗两版之前的旧文件）
    for old in ASSETS.glob("*.svg"):
        if old.name not in written:
            old.unlink()
            print(f"删除 assets/{old.name}")


if __name__ == "__main__":
    sys.exit(main())
