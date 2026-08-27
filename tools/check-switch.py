#!/usr/bin/env python3
"""Проверка: с переведённой страницы есть дорога к переводу.

    ./tools/build-local.sh          # сначала собрать
    python3 tools/check-switch.py   # потом проверить

Перевод есть, лежит в `/en/`, из поиска находится — а со страницы до него не
дойти: переключателя в шапке нет. Так на сайте стояли 39 страниц из 191 — все
главы «Натьяшастры», словарь танца и ещё несколько (VS-49).

Ломается это молча и **не там, где написано**. Английская страница знает свой
русский оригинал сама: адрес лежит у неё во front matter (`ru:`). Русская о
двойнике знать не может — она написана раньше перевода, — и смотрит в список
`_data/i18n.yml`, который собирает `tools/translate.py`. Сравнение там строковое
(`contains`), а строки у одного и того же адреса две: в списке лежит `/dance/
ns-ch5` — тот вид, каким адрес пишут ссылки на сайте, — а `page.url` отдаёт имя
файла, `/dance/ns-ch5.html`. Косая черта на конце бывает только у `index.md`,
поэтому у разделов всё сходилось, а у глав — нет. Ровно та же ошибка, что в
VS-46, только на другой поверхности: там ссылка с английской страницы не
узнавала двойника из-за косой черты, здесь русская не узнавала своего.

Проверяется поэтому не правило, а его последствие — на **собранных** страницах:

1. у адреса из списка двойников страница собрана, а `pv-lang` на ней нет;
2. у английской страницы `pv-lang` нет вовсе (обратная дорога);
3. ссылка переключателя ведёт в никуда.

## Чего эта проверка не видит

Локальная сборка идёт без `jekyll-optional-front-matter`, и страницы без front
matter в неё не попадают — сейчас таких одиннадцать (VS-43). Они здесь просто
не проверены: их число печатается отдельно, чтобы «расхождений нет» не читалось
как «просмотрено всё». Ссылка, ведущая на такую страницу, поломкой не считается
— её исходник в репозитории есть.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, '_sitecheck')
ROSTER = os.path.join(ROOT, '_data', 'i18n.yml')

SWITCH = re.compile(r'(?s)<p class="pv-lang[^>]*>.*?</p>')
HREF = re.compile(r'href="([^"]+)"')
ENTRY = re.compile(r'^\s*-\s*"([^"]+)"\s*$')


def roster():
    """Адреса русских страниц, у которых есть английский двойник."""
    with open(ROSTER, encoding='utf-8') as fh:
        return [m.group(1) for m in (ENTRY.match(l) for l in fh) if m]


def sources():
    return set(subprocess.check_output(
        ['git', '-C', ROOT, 'ls-files', '*.md'], text=True).split())


def names(url):
    """Чем этот адрес мог бы быть на диске: `/a/` — `a/index`, `/a` — и то и то.

    Так же его разбирает и GitHub Pages: адрес без расширения он отдаёт файлом
    `.html`, адрес с косой чертой — указателем каталога.
    """
    bare = url.strip('/')
    if not bare:
        return ['index']
    if url.endswith('/'):
        return [bare + '/index']
    return [bare, bare + '/index']


def built(url):
    for name in names(url):
        path = os.path.join(SITE, name + '.html')
        if os.path.exists(path):
            return path
    return None


def written(url, src):
    return any(name + '.md' in src for name in names(url))


def switch(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return SWITCH.search(fh.read())


def main():
    if not os.path.isdir(SITE):
        print('нет _sitecheck/ — сначала ./tools/build-local.sh')
        return 1

    src = sources()
    mute, unbuilt = [], []
    for url in roster():
        path = built(url)
        if path is None:
            unbuilt.append(url)
        elif not switch(path):
            mute.append(url)

    lone, broken = [], []
    for base, _dirs, files in os.walk(SITE):
        for name in sorted(files):
            if not name.endswith('.html'):
                continue
            path = os.path.join(base, name)
            where = os.path.relpath(path, SITE)
            found = switch(path)
            if not found:
                if where.startswith('en' + os.sep):
                    lone.append(where)
                continue
            for href in HREF.findall(found.group(0)):
                if not built(href) and not written(href, src):
                    broken.append((where, href))

    for url in mute[:20]:
        print('%s: двойник есть, переключателя нет' % url)
    for where in lone[:20]:
        print('%s: английская страница без пути назад' % where)
    for where, href in broken[:20]:
        print('%s: переключатель ведёт в никуда — %s' % (where, href))

    print('')
    print('в списке двойников: %d' % len(roster()))
    print('двойник есть, а переключателя нет: %d' % len(mute))
    print('английских страниц без пути назад: %d' % len(lone))
    print('ссылок переключателя в никуда: %d' % len(broken))
    if unbuilt:
        print('не проверено (нет в локальной сборке, VS-43): %d' % len(unbuilt))

    if mute or lone or broken:
        return 1
    print('переключатель стоит везде, где есть на что переключать')
    return 0


if __name__ == '__main__':
    sys.exit(main())
