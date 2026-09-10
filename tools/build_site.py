#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 volumes/*.md 编译成 docs/ 下的静态阅读站（GitHub Pages）。

用法:  python3 tools/build_site.py
输出:  docs/index.html, docs/v/NNN.html, docs/.nojekyll

volumes/NNN.md 的结构固定为：
    # 《大般若波罗蜜多经》第 N 卷 · 白话解读
    <空行>
    段落
    段落
    ...
所以这里不需要完整的 markdown 解析器，只做标题 + 段落。
"""

import html
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "volumes")
OUT = os.path.join(ROOT, "docs")

SITE = "《大般若波罗蜜多经》白话解读"
DANA = "https://openclaw-live-demo.netlify.app/dana.html"
REPO = "https://github.com/eddie-fqh/mahaprajnaparamita-vernacular"
LINKEDIN = "https://www.linkedin.com/in/eddie-fu-qihang"
LICENSE = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
BASE = "https://eddie-fqh.github.io/mahaprajnaparamita-vernacular"

CSS = """
:root{
  --paper:#faf8f3; --paper-2:#f3efe6; --ink:#1f1b16; --ink-2:#4a4239;
  --ink-3:#8a8073; --line:#ddd5c7; --accent:#7a5c3a;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"Songti SC","Source Han Serif SC","Noto Serif CJK SC",
              "STSong",Georgia,"Times New Roman",serif;
  font-size:18px; line-height:2.05; letter-spacing:.01em;
}
.wrap{max-width:38em; margin:0 auto; padding:0 22px 80px}
a{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--line)}
a:hover{border-bottom-color:var(--accent)}
header{padding:56px 0 8px}
h1{font-size:26px; line-height:1.6; margin:0 0 6px; font-weight:600}
.sub{color:var(--ink-3); font-size:15px; line-height:1.9; margin:0}
.rule{height:1px; background:var(--line); margin:34px 0}
p{margin:0 0 1.35em; text-align:justify}
.lede{font-size:17px; color:var(--ink-2)}
h2{font-size:19px; font-weight:600; margin:44px 0 14px}
.note{font-size:15px; color:var(--ink-3); line-height:1.95}
.grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(3.4em,1fr));
  gap:6px; margin:16px 0 6px}
.grid a,.grid span{
  display:block; text-align:center; padding:9px 0; font-size:15px;
  border:1px solid var(--line); border-radius:3px; background:#fff;
  font-variant-numeric:tabular-nums;
}
.grid span{color:#c7bfb1; background:var(--paper-2); border-style:dashed}
.grid a{color:var(--ink-2)}
.grid a:hover{border-color:var(--accent); color:var(--accent)}
.start{display:inline-block; margin-top:10px; padding:12px 22px;
  border:1px solid var(--accent); border-radius:3px; color:var(--accent)}
nav.pager{display:flex; justify-content:space-between; gap:14px;
  margin:52px 0 0; font-size:16px}
nav.pager a,nav.pager span{flex:1; padding:14px 12px; border:1px solid var(--line);
  border-radius:3px; background:#fff; text-align:center}
nav.pager span{color:#c7bfb1; background:transparent; border-style:dashed}
footer{margin-top:56px; padding-top:26px; border-top:1px solid var(--line);
  font-size:14px; color:var(--ink-3); line-height:2}
footer a{color:var(--ink-3)}
.dana{margin-top:14px; font-size:14px; color:var(--ink-3)}
@media (max-width:600px){
  body{font-size:17px; line-height:1.98}
  .wrap{padding:0 18px 60px}
  header{padding:38px 0 6px}
  h1{font-size:22px}
}
"""


def esc(s):
    return html.escape(s, quote=False)


def page(title, body, desc, canonical):
    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:url" content="{canonical}">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>
"""


FOOTER_VOL = f"""<footer>
<p style="margin:0">
  <a href="../index.html">← 全部卷目</a> ·
  <a href="{REPO}">GitHub 原始文本</a> ·
  <a href="{LICENSE}">CC BY-NC-SA 4.0</a>
</p>
<p class="dana" style="margin:14px 0 0">
  经文永远免费，没有付费墙。<br>
  如果这笔钱不会影响你的生活，可以<a href="{DANA}">随喜供养</a>——
  它只影响推进速度，不影响它是否存在。<br>
  比钱更有用的：指出错误，或者转给一个可能需要它的人。
</p>
</footer>"""


def read_volume(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    lines = [ln.rstrip() for ln in raw.split("\n")]
    title = ""
    body = []
    for ln in lines:
        if not title and ln.startswith("# "):
            title = ln[2:].strip()
            continue
        if ln.strip():
            body.append(ln.strip())
    return title, body


def build():
    nums = sorted(
        int(m.group(1))
        for m in (re.fullmatch(r"(\d{3})\.md", n) for n in os.listdir(SRC))
        if m
    )
    have = set(nums)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "v"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    # ---- volume pages ----
    for i, n in enumerate(nums):
        title, paras = read_volume(os.path.join(SRC, "%03d.md" % n))
        title = title or "《大般若波罗蜜多经》第 %d 卷 · 白话解读" % n
        prev_n = nums[i - 1] if i > 0 else None
        next_n = nums[i + 1] if i < len(nums) - 1 else None

        pager = ['<nav class="pager">']
        pager.append(
            '<a href="%03d.html">← 第 %d 卷</a>' % (prev_n, prev_n)
            if prev_n else "<span>已是最前</span>"
        )
        pager.append(
            '<a href="%03d.html">第 %d 卷 →</a>' % (next_n, next_n)
            if next_n else "<span>已是最后</span>"
        )
        pager.append("</nav>")

        body = [
            "<header>",
            "<h1>%s</h1>" % esc(title),
            '<p class="sub">第 %d 卷 / 共 600 卷 · 已完成 %d 卷</p>' % (n, len(nums)),
            "</header>",
            '<div class="rule"></div>',
        ]
        body += ["<p>%s</p>" % esc(p) for p in paras]
        body += pager
        body.append(FOOTER_VOL)

        desc = (paras[0][:110] + "…") if paras else title
        out = page(
            title, "\n".join(body), desc, "%s/v/%03d.html" % (BASE, n)
        )
        with open(os.path.join(OUT, "v", "%03d.html" % n), "w", encoding="utf-8") as f:
            f.write(out)

    # ---- index ----
    grid = []
    for n in range(1, 601):
        if n in have:
            grid.append('<a href="v/%03d.html">%d</a>' % (n, n))
        else:
            grid.append("<span>%d</span>" % n)

    missing = [n for n in range(1, 601) if n not in have]
    words = sum(
        len(open(os.path.join(SRC, "%03d.md" % n), encoding="utf-8").read())
        for n in nums
    )

    idx = f"""<header>
<h1>{SITE}</h1>
<p class="sub">玄奘译 600 卷 · 逐卷现代白话解读 · 已完成 {len(nums)} 卷，约 {words // 10000} 万字</p>
</header>
<div class="rule"></div>

<p class="lede">《大般若波罗蜜多经》是汉传佛教篇幅最大的一部经，也是读的人最少的一部经。
原因很简单：太长、太重复、文言太密。绝大多数人翻开第一卷就放下了。</p>

<p class="lede">这里是一次很笨的尝试——<strong>一卷一卷，用今天的话把它讲一遍。</strong>
每一卷可以独立读，也可以顺着读。</p>

<p><a class="start" href="v/050.html">从第 50 卷开始读 →</a></p>
<p class="note">（前面几十卷是铺垫，第 50 卷进入正题。想从头也可以直接点下面的卷号。）</p>

<h2>是什么，不是什么</h2>
<p class="note"><strong>是</strong>：逐卷的白话解读稿。保留原经的义理骨架和推进顺序，用现代口语讲出来。<br>
<strong>不是</strong>：不是逐字直译，不是学术译本，不是原文替代品。遇到义理关口会停下来打比方——
这些比喻是解读者加的，不是经文里的。<br>
真正想深入，请回到玄奘原译。这份稿子的作用是让你有能力读下去，而不是替你读。</p>

<h2>全部卷目</h2>
<p class="note">灰色虚线 = 尚未完成，共缺 {len(missing)} 卷，陆续补。</p>
<div class="grid">
{chr(10).join(grid)}
</div>

<h2>关于文本</h2>
<p class="note">这些稿子最初是为语音讲解写的口播稿，所以语气是讲给人听的，不是写给人看的。
原始文件里「般若」曾被写成「波惹」（为了让语音合成读对 <em>prajñā</em> 的音），本站已全部还原。</p>
<p class="note">如果你发现义理讲错了、比喻不当、或者哪一卷读不通，
欢迎到 <a href="{REPO}/issues">GitHub 开 issue</a>。<strong>指出错误是对这件事最大的帮助。</strong></p>

<footer>
<p style="margin:0">
  付启航 Eddie · <a href="{LINKEDIN}">LinkedIn</a> ·
  <a href="{REPO}">GitHub</a> ·
  原经公有领域，本解读 <a href="{LICENSE}">CC BY-NC-SA 4.0</a>，
  可自由转载印制朗读，<strong>不要用于付费产品</strong>。
</p>
<p class="dana" style="margin:14px 0 0">
  经文永远免费，没有付费墙，这一点不会变。<br>
  供养只影响推进速度，不影响它是否存在——不给钱，剩下的 {len(missing)} 卷也会写完，只是慢一点。<br>
  所以只在这句话成立时再考虑：<strong>这笔钱不会影响你的生活。</strong>
  零花钱可以，生活费不行。手头紧的人请直接跳过，去读经。<br>
  <a href="{DANA}">→ 供养通道</a>
</p>
</footer>"""

    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(SITE, idx, "玄奘译《大般若波罗蜜多经》600 卷的逐卷现代白话解读，已完成 %d 卷，全文免费公开。" % len(nums), BASE + "/"))

    # ---- sitemap (为了能被搜到) ----
    urls = ["%s/" % BASE] + ["%s/v/%03d.html" % (BASE, n) for n in nums]
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            f.write("  <url><loc>%s</loc></url>\n" % u)
        f.write("</urlset>\n")

    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE)

    print("built %d volume pages -> docs/  (missing %d)" % (len(nums), len(missing)))


if __name__ == "__main__":
    build()
