#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сколько «Тантралоки» переведено у источника на русский.

Обходит русские страницы Tantrāloka на sanskrit-trikashaivism.com и смотрит,
что стоит у каждой строфы: перевод или пометка «Непереведенная ещё».

Считать иначе нельзя, и это проверено дважды:

* Флаг «Русский» стоит у всех страниц и значит лишь, что русский узел заведён.
* Кириллица в теле страницы тоже обманывает. У непереведённой страницы под
  каждой строфой стоит русское «Непереведенная ещё», и чем длиннее глава, тем
  больше кириллицы она набирает: 28-я на этом и попалась — три её страницы по
  150 строф выглядели переведёнными, хотя в них нет ни строки перевода.
* Обратный случай — 29-я глава: пометок нет, а перевод под строфами
  английский. Русский узел с английским телом (так же ведёт себя
  Parātrīśikāvivaraṇa). Поэтому в переведённые идёт только страница, где и
  пометок нет, и кириллицы в области строф — тысячи.

    python3 tools/trika/ta-ru-scan.py            # обойти и напечатать отчёт
    python3 tools/trika/ta-ru-scan.py --json     # то же, машинным видом

Скачанное кладётся в tools/trika/src/ и повторно не качается — сайт чужой,
дёргать его лишний раз незачем. Для новой проверки: --refresh.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
BASE = 'https://www.sanskrit-trikashaivism.com'
INDEX = '/ru/node/581'          # оглавление «Тантралоки» по-русски
PARENT = 297                    # «Тантралока» в общем списке писаний — не глава
VIVEKA = 583                    # Tantrālokaviveka — отдельным узлом
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')

# Кириллицы в области строф у переведённой страницы — десятки тысяч,
# у непереведённой — сотни. Порог стоит посередине, между 189 и 4889.
RU_AT = 2000

CYR = re.compile(r'[А-Яа-яЁё]')
UNTRANSLATED = re.compile(r'Непереведе[нн]?[ыо]?н?ая ещё|Непереведённая ещё')
STANZA = re.compile(r'\|\|\d+(?:-\d+)?\|\|')
SCRIPTS = re.compile(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>')


def fetch(path, name, refresh=False):
    os.makedirs(SRC, exist_ok=True)
    out = os.path.join(SRC, name)
    if os.path.exists(out) and not refresh:
        return open(out, encoding='utf-8', errors='replace').read()
    req = urllib.request.Request(BASE + path, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode('utf-8', 'replace')
    open(out, 'w', encoding='utf-8').write(body)
    time.sleep(1)
    return body


def text(html):
    """Тело страницы словами: без обвязки сайта, скриптов и разметки."""
    i = html.find('id="content"')
    j = html.find('id="footercontent"')
    body = html[i if i >= 0 else 0:j if j > i else len(html)]
    t = SCRIPTS.sub(' ', body)
    t = re.sub(r'(?s)<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t)


def measure(html):
    """Строфы страницы, пометки «Непереведенная ещё» и кириллица при строфах."""
    t = text(html)
    first = STANZA.search(t)
    if not first:
        return {'stanzas': 0, 'untranslated': 0, 'cyrillic': 0}
    end = t.find('Дополнительная информация', first.end())
    tail = t[first.end():end if end > first.end() else len(t)]
    return {'stanzas': len(STANZA.findall(t)),
            'untranslated': len(UNTRANSLATED.findall(tail)),
            'cyrillic': len(CYR.findall(UNTRANSLATED.sub(' ', tail)))}


def chapter_pages(html):
    """Ссылки на страницы глав из оглавления, в порядке появления."""
    seen, out = set(), []
    for path, node in re.findall(r'href="(/ru/tantraloka-[^"]+/(\d+))"', html):
        if node in seen:
            continue
        seen.add(node)
        out.append((int(node), path))
    return out


def label(path, node):
    m = re.search(r'/ru/tantraloka-([^-]+(?:-[a-z]+)?)-trika', path)
    return m.group(1) if m else str(node)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--refresh', action='store_true',
                    help='перекачать, а не брать из tools/trika/src/')
    args = ap.parse_args()

    index = fetch(INDEX, 'ta-ru-581.html', args.refresh)
    pages = [(n, p) for n, p in chapter_pages(index) if n != PARENT]
    pages.sort(key=lambda np: (np[0] == VIVEKA, np[0]))

    rows = []
    for node, path in pages:
        m = measure(fetch(path, 'ta-ru-%d.html' % node, args.refresh))
        russian = m['untranslated'] == 0 and m['cyrillic'] >= RU_AT
        rows.append({'node': node, 'label': label(path, node), 'russian': russian,
                     'url': BASE + path, **m})

    done = [r for r in rows if r['russian']]
    if args.json:
        json.dump({'total': len(rows), 'russian': len(done), 'pages': rows},
                  sys.stdout, ensure_ascii=False, indent=2)
        print()
        return

    for r in rows:
        if r['russian']:
            note = 'русский'
        elif r['untranslated']:
            note = 'нет: «Непереведенная ещё» под каждой строфой'
        elif r['stanzas']:
            note = 'нет: под строфами английский'
        else:
            note = 'нет: строф на странице нет'
        print('%-20s node %-4d строф %4d  %s'
              % (r['label'], r['node'], r['stanzas'], note))
    print()
    print('По-русски %d страниц из %d.' % (len(done), len(rows)))


if __name__ == '__main__':
    main()
