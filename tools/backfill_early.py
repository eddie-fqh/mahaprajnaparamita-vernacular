#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 ~/Downloads/佛经素材/ 里早期的口播稿回填成 volumes/NNN.md。

这些卷（1-15、24）的白话稿早就写好了，但从来没进过阅读站，
导致站点从第 21 卷开始——任何从第一卷进来的读者都会扑空。

用法: python3 tools/backfill_early.py [--dry-run]
"""

import os
import re
import sys

SRC_DIR = os.path.expanduser("~/Downloads/佛经素材")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "volumes")

# 显式映射：卷号 -> 源文件名。第 8 卷有四个重复下载，取内容最完整的那份。
SOURCES = {
    1:  "大般若经第一卷_口播稿.txt",
    2:  "大般若经第二卷_口播稿.txt",
    3:  "大般若经第三卷_口播稿.txt",
    4:  "大般若经第四卷_口播稿.txt",
    5:  "大般若经第五卷_口播稿.txt",
    6:  "大般若经第六卷_口播稿.txt",
    7:  "大般若经第7卷_口播稿.txt",
    8:  "大般若经第8卷_口播稿 (1).txt",
    9:  "大般若经第9卷_口播稿.txt",
    10: "大般若经第10卷_口播稿.txt",
    11: "大般若经第11卷_口播稿.txt",
    12: "大般若经第12卷_口播稿.txt",
    13: "大般若经第13卷_口播稿.txt",
    14: "大般若经第14卷_口播稿.txt",
    15: "大般若经第15卷_口播稿.txt",
    24: "大般若经第24卷_口播稿.txt",
}

TITLE = "# 《大般若波罗蜜多经》第 {n} 卷 · 白话解读"

# 口播稿里给朗读用的标注，不该出现在阅读版里。
STRIP_LINE = re.compile(r"^\s*[（(\[【]?\s*(?:配图|画面|停顿|语气|BGM|音乐|片头|片尾|字幕)"
                        r"[^\n]*$")
# 「第N卷」之类的裸标题行，如果稿子自带就去掉，标题由模板统一生成。
BARE_TITLE = re.compile(r"^\s*#*\s*《?大般若(波罗蜜多)?经》?\s*第.{1,6}卷.*$")

# 口播稿是给 TTS 用的，「般若」被写成注音「波惹」好让配音读对。
# 阅读版必须读回正字，否则整站只有这几卷是错的。
TTS_FIXES = [("波惹", "般若")]


def to_markdown(n: int, raw: str) -> str:
    paras = []
    for block in raw.replace("\r\n", "\n").split("\n"):
        line = block.strip()
        if not line:
            continue
        if STRIP_LINE.match(line) or BARE_TITLE.match(line):
            continue
        for bad, good in TTS_FIXES:
            line = line.replace(bad, good)
        paras.append(line)
    if not paras:
        raise ValueError(f"第 {n} 卷：清洗后没有正文")
    return TITLE.format(n=n) + "\n\n" + "\n\n".join(paras) + "\n"


def main():
    dry = "--dry-run" in sys.argv
    written, skipped, missing = [], [], []

    for n in sorted(SOURCES):
        src = os.path.join(SRC_DIR, SOURCES[n])
        dst = os.path.join(OUT_DIR, f"{n:03d}.md")

        if not os.path.exists(src):
            missing.append((n, SOURCES[n]))
            continue
        if os.path.exists(dst):
            skipped.append(n)          # 站上已有的卷绝不覆盖
            continue

        md = to_markdown(n, open(src, encoding="utf-8").read())
        if not dry:
            open(dst, "w", encoding="utf-8").write(md)
        written.append((n, len(md)))

    for n, size in written:
        print(f"{'would write' if dry else 'wrote'}  volumes/{n:03d}.md  ({size} chars)")
    if skipped:
        print("skipped (already on site):", ", ".join(str(n) for n in skipped))
    if missing:
        for n, name in missing:
            print(f"MISSING source for vol {n}: {name}")
    print(f"\n{len(written)} volumes backfilled.")


if __name__ == "__main__":
    main()
