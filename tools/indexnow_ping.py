#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 docs/sitemap.xml 里的 URL 提交给 IndexNow（Bing / Yandex / Seznam / Naver）。

为什么需要它：这个站没有外链，搜索引擎不会自己爬过来。
IndexNow 不需要站长后台验证，只要 docs/<key>.txt 能被访问到就行，
而那个 key 文件由 build_site.py 生成。

用法：
    python3 tools/build_site.py && python3 tools/indexnow_ping.py

新写完几卷之后跑一次就够了，不用每天跑。
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, "docs", "sitemap.xml")

HOST = "eddie-fqh.github.io"
BASE = "https://eddie-fqh.github.io/mahaprajnaparamita-vernacular"
KEY = "dd2d5cf90de74098be6c7833ffbb9e31d19f559274f64068b813a4286115becb"

ENDPOINT = "https://api.indexnow.org/indexnow"


def main():
    if not os.path.exists(SITEMAP):
        sys.exit("找不到 docs/sitemap.xml —— 先跑 python3 tools/build_site.py")

    with open(SITEMAP, encoding="utf-8") as f:
        urls = re.findall(r"<loc>(.*?)</loc>", f.read())

    if not urls:
        sys.exit("sitemap 里没有 URL")

    payload = json.dumps(
        {
            "host": HOST,
            "key": KEY,
            "keyLocation": "%s/%s.txt" % (BASE, KEY),
            "urlList": urls,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        # 403 SiteVerificationNotCompleted 通常是 key 文件刚部署，等几分钟再跑。
        sys.exit("IndexNow 失败 %s: %s" % (e.code, body))

    print("已提交 %d 条 URL -> IndexNow (%s %s)" % (len(urls), resp.status, resp.reason))


if __name__ == "__main__":
    main()
