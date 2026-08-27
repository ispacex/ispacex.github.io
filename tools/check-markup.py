#!/usr/bin/env python3
"""Проверка: звёздочка разметки не доходит до читателя.

    ./tools/build-local.sh          # сначала собрать
    python3 tools/check-markup.py   # потом проверить

Главы «Натьяшастры» набирались с бумаги, и закрывающий маркер выделения то и
дело оказывался по ту сторону пробела: `*раса *изучаются`, `**Натья? **В чём`.
Пару так не закрыть — kramdown честно печатает звёздочки как есть, и читатель
видит их в тексте, а термин остаётся не выделен (VS-50).

Ловится это только на **собранной** странице. По исходнику не видно ничего:
`**Натья **и` и `**Натья** и` отличаются одним пробелом, а на странице первое
даёт звёздочки, второе — полужирное. Ровно так же в `ns-ch24.md` похожий набор
встречается шесть десятков раз, но там пара всё же закрывается и до страницы
не доходит ничего. Считать надо то, что видит читатель.

Порог здесь ноль и исключений не имеет: сейчас на сайте нет ни одной звёздочки
в тексте страницы. Ни одна из них не поставлена нарочно — звёздочка в прозе
этих текстов не значит ничего, и если она появилась, то это разметка, которая
не сработала.

Беда не только в виде. Перевод режет страницу на куски по пустым строкам и
отвергает кусок, в котором звёздочек стало нечётное число (`bold` в прогоне
`tools/translate.py`): непарная звёздочка портит не абзац, а всё, что ниже.
Отвергнутый кусок остаётся русским на английской странице.
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, '_sitecheck')

# Скрипты и стили — не текст: звёздочка там законна (`*/`, `a * b`).
HIDDEN = re.compile(r'(?is)<(script|style)\b.*?</\1>')
COMMENT = re.compile(r'(?s)<!--.*?-->')
TAG = re.compile(r'(?s)<[^>]+>')


def text(page):
    page = HIDDEN.sub(' ', page)
    page = COMMENT.sub(' ', page)
    return html.unescape(TAG.sub(' ', page))


def pages():
    for base, _, names in os.walk(SITE):
        for name in sorted(names):
            if name.endswith('.html'):
                yield os.path.join(base, name)


def main():
    if not os.path.isdir(SITE):
        print('нет _sitecheck/ — сначала ./tools/build-local.sh')
        return 1

    found, seen = [], 0
    for path in pages():
        seen += 1
        with open(path, encoding='utf-8', errors='replace') as fh:
            body = text(fh.read())
        where = os.path.relpath(path, SITE)
        for m in re.finditer(r'\*', body):
            a, b = max(0, m.start() - 50), m.end() + 50
            near = ' '.join(body[a:b].split())
            found.append((where, near))

    if found:
        for where, near in found[:40]:
            print('%s: …%s…' % (where, near))
        if len(found) > 40:
            print('… и ещё %d' % (len(found) - 40))
        print('')
        print('звёздочек разметки в тексте страниц: %d' % len(found))
        return 1

    print('звёздочек разметки в тексте страниц нет — '
          'просмотрено страниц: %d' % seen)
    return 0


if __name__ == '__main__':
    sys.exit(main())
