#!/usr/bin/env python3
"""Забирает исходные страницы с sanskrit-trikashaivism.com в <конвейер>/src/.

Уже скачанное не перекачивается — сайт чужой, дёргать его лишний раз незачем.
"""
import os, sys, time, urllib.parse, urllib.request

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def fetch(here, src, src_url, prefix='', pause=1.0):
    out = os.path.join(here, 'src')
    os.makedirs(out, exist_ok=True)
    for pid, path in src_url.items():
        dest = os.path.join(out, '%s%s.html' % (prefix, pid))
        if os.path.exists(dest):
            print('%s — уже есть' % pid)
            continue
        url = src + urllib.parse.quote(path, safe='/')
        print('%s — качаю' % pid)
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req) as r:
            open(dest, 'wb').write(r.read())
        time.sleep(pause)
