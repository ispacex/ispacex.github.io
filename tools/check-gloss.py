#!/usr/bin/env python3
"""Проверка: у всплывающего толкования есть что показать.

    ./tools/build-local.sh           # сначала собрать
    python3 tools/check-gloss.py     # потом проверить

Чисто — печатает, сколько просмотрено, и выходит нулём. Иначе показывает
ссылки, которым подсказывать нечем, и выходит единицей.

## Что сличается

Санскритское слово в подстрочнике, у которого есть статья в словаре, — ссылка
туда: `<a class="pv-gl" href="/ksh/pv/glossary/#t-srsti">`. Наведение
показывает толкование на месте, не уводя читателя со страницы (VS-35), и берёт
его из `terms.json`, лежащего рядом со страницей словаря. Ключ подсказка берёт
прямо из адреса ссылки — тот, что стоит после `#t-`.

Значит и ссылка, и файл называют статью одним и тем же ключом, и разойтись они
могут молча: подсказка на такой ссылке просто не появится, а сама ссылка будет
работать по-прежнему — читатель попадёт в словарь и увидит страницу без своей
строки. Ни в браузере, ни в сборке об этом не скажет никто.

Разойтись есть отчего. Ключ статьи выводится из написания (`common/terms.py`,
`slug`), и правится он вместе с ним: `kalā` и `kāla` дают один ключ, и одному
из них ключ задают руками. Ссылки же в подстрочнике расставляет сборка страниц,
а `terms.json` пишет сборка словаря — это два прохода, и между ними страницы
раздела могут остаться от прежнего ключа.

## Что считается поломкой

Три вещи, и все три — про то, что подсказке нечего сказать:

* ссылка ведёт в словарь, у которого нет `terms.json`;
* ключа из адреса ссылки в этом файле нет;
* статья есть, но пустая — без имени или без толкования.

Обратное — статья, на которую не ссылается ни одно слово, — поломкой не
считается и печатается отдельно, к сведению. Словарь на то и словарь: в нём
стоят и те термины, что встречаются только на страницах-обзорах, где
подстрочника нет вовсе.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, '_sitecheck')

# Ссылка в словарь, как её ставит common/page.py: адрес словаря, `#t-` и ключ.
LINK = re.compile(r'<a href="(/[^"#]*/)#t-([^"]+)" class="pv-gl">')


def books(site):
    """Словари сайта: адрес страницы словаря → статьи из его `terms.json`."""
    out = {}
    for here, _dirs, files in os.walk(site):
        if 'terms.json' not in files:
            continue
        url = '/' + os.path.relpath(here, site).replace(os.sep, '/') + '/'
        with open(os.path.join(here, 'terms.json'), encoding='utf-8') as fh:
            out[url] = json.load(fh)
    return out


def pages(site):
    for here, _dirs, files in os.walk(site):
        for name in files:
            if name.endswith('.html'):
                yield os.path.join(here, name)


def main():
    if not os.path.isdir(SITE):
        print('нет _sitecheck/ — сначала ./tools/build-local.sh')
        return 1

    known = books(SITE)
    if not known:
        print('ни одного terms.json в сборке')
        return 1

    seen, used, bad = 0, set(), []
    for path in pages(SITE):
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        where = '/' + os.path.relpath(path, SITE).replace(os.sep, '/')
        for at, key in LINK.findall(html):
            seen += 1
            book = known.get(at)
            if book is None:
                why = 'словаря нет: %sterms.json' % at
            elif key not in book:
                why = 'статьи нет: %s#t-%s' % (at, key)
            elif not (book[key].get('name') and book[key].get('gloss')):
                why = 'статья пустая: %s#t-%s' % (at, key)
            else:
                used.add((at, key))
                continue
            # Одна и та же ссылка стоит на странице десятками; показываем
            # каждую беду один раз, иначе список будет длиннее разговора.
            if (at, key, why) not in [(a, k, w) for a, k, w, _ in bad]:
                bad.append((at, key, why, where))

    for _at, _key, why, where in bad:
        print('%s: %s' % (where, why))

    if bad:
        print('')
        print('ссылок, которым подсказывать нечем: %d' % len(bad))
        return 1

    idle = sum(len(book) for book in known.values()) - len(used)
    print('у каждой ссылки в словарь есть статья — просмотрено ссылок: %d, '
          'словарей: %d' % (seen, len(known)))
    print('статей, на которые не ссылается ни одно слово: %d — это не беда, '
          'словарь шире подстрочника' % idle)
    return 0


if __name__ == '__main__':
    sys.exit(main())
