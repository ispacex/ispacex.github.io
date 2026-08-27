#!/usr/bin/env python3
"""Проверка: английская страница говорит по-английски.

    ./tools/build-local.sh        # сначала собрать
    python3 tools/check-lang.py   # потом проверить

Перевод отвергает кусок, который не дался, и оставляет его русским — нарочно:
испорченное чинить нечем, а по-русски оно хотя бы не врёт. Но отвергнутый кусок
не пропадает, он уезжает на страницу, и читатель, пришедший по `/en/`,
упирается в алфавит, которого не знает. Так на английских страницах стояло
2318 русских слов на 39 страницах (VS-51), и знал об этом только счётчик в
прогоне.

Считается по **собранной** странице, а не по исходнику, и на то две причины.
Обвязка страниц `/ksh/` приходит не из `en/*.md`, а из своих конвейеров, и в
исходнике перевода её нет вовсе. А главное — читатель видит собранное.

## Что считается текстом

Всё, что видно глазами. Кроме самого текста страницы это **подписи внутри
тегов**: `placeholder` стоит в поле поиска словаря, `title` всплывает над
ссылкой. Тег маскируется при переводе целиком — иначе модель правит класс и
адрес, — и подписи внутри него до перевода не доходили: поле поиска на
английском словаре предлагало «начните вводить термин, например «чити»», а над
каждой из 1197 ссылок «где в тексте» всплывало «Афоризм 7».

Соседние русские значения — `data-alias="санкоча"`, `data-tts="citi"` —
читателю не видны и трогать их нельзя: по первому фильтр словаря находит
статью, по второму зовётся звуковой файл. Здесь они и не считаются.

## Что по-русски и должно быть таким

Двое, и оба названы поимённо (`ALLOW`, `SKIP`). Что не названо — поломка.

## Указатели

Страницей дело не кончается. Над каждой находкой стоит имя раздела, и берётся
оно не со страницы, а из указателя: над английской страницей стояло
«Кашмирский шиваизм», и в палитре то же имя стояло в каждой строке (VS-44).
Читателю это ровно такое же русское слово на английской странице, только
написанное не в HTML, а в JSON, — поэтому считается здесь же.

Указатели просматриваются все, что собрались: страница с `lang: en` называет
свой раздел по-английски, а осколок (`shards`), подписанный по-русски, обязан
нести второе имя — его выбирает движок, потому что файл один на оба языка
(sitesearch/FORMAT.md).
"""
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, '_sitecheck')
SITE = os.path.join(BUILD, 'en')

HIDDEN = re.compile(r'(?is)<(script|style)\b.*?</\1>')
COMMENT = re.compile(r'(?s)<!--.*?-->')
# Переключатель языка двуязычен нарочно: слово «Русский» на английской
# странице — это ссылка на русскую страницу, а не непереведённый кусок.
LANG = re.compile(r'(?is)<p class="pv-lang[^>]*>.*?</p>')
# Врезка Instagram — разметка самого Instagram, не наша: «Посмотреть эту
# публикацию» написано в ней их скриптом, по языку того, кто вставлял. Мы её
# встраиваем, а не переводим.
GUEST = re.compile(r'(?is)<blockquote class="instagram-media".*?</blockquote>')
TAG = re.compile(r'(?s)<[^>]+>')
# Подписи внутри тега, которые читатель видит.
SHOWN = re.compile(r'\b(?:placeholder|title|alt|aria-label)="([^"]*)"')
WORD = re.compile(r'[А-Яа-яЁё]{2,}')

SKIP = (LANG, GUEST)

# Русское слово, стоящее на английской странице по делу. Ключ — само слово,
# значение — почему оно тут.
ALLOW = {
    'шактипата': 'пример запроса: страница показывает, что кириллица '
                 'находит śaktipāta',
}


def text(page):
    page = HIDDEN.sub(' ', page)
    page = COMMENT.sub(' ', page)
    for pat in SKIP:
        page = pat.sub(' ', page)
    # Подписи внутри тегов — часть текста: их читают, как и всё прочее.
    labels = ' '.join(SHOWN.findall(page))
    return html.unescape(TAG.sub(' ', page)) + ' ' + html.unescape(labels)


def pages():
    for base, _, names in os.walk(SITE):
        for name in sorted(names):
            if name.endswith('.html'):
                yield os.path.join(base, name)


def indexes():
    """Указатели собранного сайта: поисковые (их несколько) и указатель палитры."""
    found = sorted(glob.glob(os.path.join(BUILD, '**', 'search-index.json'),
                             recursive=True))
    nav = os.path.join(BUILD, 'nav-index.json')
    if os.path.exists(nav):
        found.append(nav)
    return found


def sections():
    """Разделы, подписанные по-русски там, где читают по-английски."""
    bad, shards, seen = [], [], 0
    for path in indexes():
        where = os.path.relpath(path, BUILD)
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        for page in data.get('pages') or []:
            seen += 1
            if (page.get('lang') or '')[:2].lower() != 'en':
                continue
            if WORD.search(page.get('section') or ''):
                bad.append('%s: %s — раздел «%s»'
                           % (where, page.get('url'), page['section']))
        # Осколок подписан один раз на оба языка: имя по-русски здесь не
        # поломка, но второе имя к нему обязано быть.
        for shard in data.get('shards') or []:
            seen += 1
            name = shard.get('section') or ''
            if not WORD.search(name):
                continue
            other = (shard.get('named') or {}).get('en')
            if not other or WORD.search(other):
                shards.append('%s: осколок %s — «%s» без английского имени'
                              % (where, shard.get('url'), name))
    # Осколков единицы, страниц сотни: сказать сперва о немногом.
    return shards + bad, seen


def main():
    if not os.path.isdir(SITE):
        print('нет _sitecheck/en/ — сначала ./tools/build-local.sh')
        return 1

    found, seen = [], 0
    for path in pages():
        seen += 1
        with open(path, encoding='utf-8', errors='replace') as fh:
            body = text(fh.read())
        where = os.path.relpath(path, os.path.join(ROOT, '_sitecheck'))
        for m in WORD.finditer(body):
            if m.group(0).lower() in ALLOW:
                continue
            a, b = max(0, m.start() - 40), m.end() + 40
            found.append((where, ' '.join(body[a:b].split())))

    named, records = sections()

    if found or named:
        for where, near in found[:30]:
            print('%s: …%s…' % (where, near))
        if len(found) > 30:
            print('… и ещё %d' % (len(found) - 30))
        for line in named[:20]:
            print(line)
        if len(named) > 20:
            print('… и ещё %d' % (len(named) - 20))
        print('')
        if found:
            pages_hit = len(set(w for w, _ in found))
            print('русских слов на английских страницах: %d на %d страницах'
                  % (len(found), pages_hit))
        if named:
            print('разделов, подписанных по-русски над английским: %d' % len(named))
        return 1

    print('английские страницы говорят по-английски — просмотрено страниц: %d, '
          'записей в указателях: %d' % (seen, records))
    return 0


if __name__ == '__main__':
    sys.exit(main())
