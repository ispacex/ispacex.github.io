#!/usr/bin/env python3
"""Проверка: страница зовётся тем же адресом, каким её зовут ссылки.

    ./tools/build-local.sh             # сначала собрать
    python3 tools/check-address.py     # потом проверить

У страницы, лежащей файлом, а не каталогом, `page.url` отдаёт имя файла:
`/dance/ns-ch5.html`. Ссылки сайта пишутся иначе — без расширения, все 228 до
одной. Расходились так 79 страниц: главы «Натьяшастры», словарь танца, поиск по
строфам и их английские двойники (VS-52).

Видно это было не сразу, потому что оба адреса отдаются. Но из `page.url`
строятся `canonical` и `og:url`, и сайт объявлял поисковику своим адресом тот,
которым сам себя не зовёт ни разу: `hreflang`, поставленный в VS-49, называл
адреса, для поисковика неканонические, а такие связки он не учитывает. Оттуда
же берут адрес три поисковых указателя и палитра ⌘K — и вели на `.html`, тогда
как меню и ссылки в тексте вели без него.

## Почему проверяются указатели, а не сам `canonical`

`canonical` в локальной сборке не увидеть: гема `jekyll-seo-tag` в контейнере
нет, и `{% seo %}` не выдаёт ничего (как и тема — см. `tools/build-local.sh`).
Указатели строит Jekyll из того же `page.url`, тем же выражением, и это
единственный свидетель адреса, который в локальной сборке есть. На живом сайте
то же место смотрится глазами:

    curl -s https://ispacex.github.io/dance/ns-ch5 | grep canonical

## Что считается поломкой

Адрес с `.html`, у которого исходник — Markdown. Такую страницу сайт зовёт без
расширения всегда, и разночтения тут быть не может.

Страницы, написанные прямо в HTML, — читалки книги Мархая (`/ship/tables.html`
и ещё три) — так и зовутся, с расширением: у них имя файла и есть адрес, и
ссылки на них пишутся ровно так же. Поломкой это не считается: расхождения нет.
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, '_sitecheck')


def sources():
    return set(subprocess.check_output(
        ['git', '-C', ROOT, 'ls-files', '*.md'], text=True).split())


def indexes():
    """Указатели собранного сайта: поисковые (их пять) и указатель палитры."""
    found = sorted(glob.glob(os.path.join(SITE, '**', 'search-index.json'),
                             recursive=True))
    nav = os.path.join(SITE, 'nav-index.json')
    if os.path.exists(nav):
        found.append(nav)
    return found


def main():
    if not os.path.isdir(SITE):
        print('нет _sitecheck/ — сначала ./tools/build-local.sh')
        return 1

    src = sources()
    bad, seen, files = {}, 0, 0
    for path in indexes():
        files += 1
        with open(path, encoding='utf-8') as fh:
            pages = json.load(fh).get('pages', [])
        where = os.path.relpath(path, SITE)
        for page in pages:
            url = page.get('url', '')
            seen += 1
            if not url.endswith('.html'):
                continue
            if url.lstrip('/')[:-5] + '.md' not in src:
                continue    # исходник и правда .html — так и зовётся
            bad.setdefault(url, set()).add(where)

    if bad:
        for url in sorted(bad)[:20]:
            print('%s: адрес с .html, а страница написана в Markdown (%s)'
                  % (url, ', '.join(sorted(bad[url]))))
        if len(bad) > 20:
            print('… и ещё %d' % (len(bad) - 20))
        print('')
        print('адресов, которых сайт своими ссылками не пишет: %d' % len(bad))
        return 1

    print('адрес страницы — тот же, каким её зовут ссылки: '
          'просмотрено %d записей в %d указателях' % (seen, files))
    return 0


if __name__ == '__main__':
    sys.exit(main())
