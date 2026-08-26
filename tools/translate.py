#!/usr/bin/env python3
"""Переводит страницы сайта при сборке и кладёт их в `/en/…`.

    python3 tools/translate.py --list          # что пойдёт в перевод, что нет
    python3 tools/translate.py --dry           # прогнать, ничего не покупая
    python3 tools/translate.py ksh/index.md    # одну страницу
    python3 tools/translate.py                 # всё

## Что переводится, а что нет

Переводится **наше**. Не переводится то, что само перевод:

* «[Тантралока](../ksh/ta/)» и «[Тантрасара](../ksh/tantrasara/)» по-русски —
  работа Габриэля Pradīpaka, перенесённая ради поиска;
* Parātrīśikāvivaraṇa и разбор Pratyabhijñāhṛdayam переведены **с его
  английского**.

Гнать это машиной обратно в английский значит выдать третье колено пересказа
вместо его собственного текста, который на одну ссылку дальше. Такие страницы
получают не перевод, а строку со ссылкой на источник (см. `SOURCE`).

Śivastotrāvalī — исключение и переводится: её русский сделан прямо с санскрита,
и по-английски её нет нигде. Но живёт она в `ru/*.json`, поэтому переводится не
здесь, а своим конвейером.

## Отчего страница режется на куски

Целую страницу модель переписывает: сбивает front matter, съедает вставки
Jekyll, «поправляет» таблицы. Кусок между пустыми строками — единица, которую
она возвращает целой, и та же единица, которой режет текст поисковый указатель.

Заголовок страницы (`title:`) переводится отдельно: это не проза, а строка в
кавычках, и вернуть её надо ровно строкой.

## Отчего запросы идут разом

Кусков на сайте почти шесть тысяч. По одному запросу за раз это часы ожидания
на пустом месте: время уходит не на счёт, а на дорогу до сервера и обратно.
Поэтому сперва собирается список всего, что предстоит купить, из него
выбрасываются повторы (одна и та же шапка стоит на четырёх десятках страниц), и
оставшееся забирается в несколько потоков. Собирается страница уже из готового
кеша, по порядку и без сети.

## Ссылки внутри

Ссылка на страницу, у которой английский двойник есть, ведёт к двойнику; на ту,
у которой нет, — остаётся русской. Это честно: страница и правда русская, и
подменять её нечем. Оттого перевод идёт в два прохода — сперва становится
известен состав английского дерева, потом правятся ссылки.
"""
import argparse
import concurrent.futures
import os
import re
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from common.translate import Cache, translate

OUT = os.path.join(ROOT, 'en')
LANG = 'English'
CODE = 'en'

# Разделы, чей русский сам перевод. Их страницы не переводятся; вместо этого
# на них стоит ссылка на источник.
SOURCE = {
    'ksh/pv/': 'https://www.sanskrit-trikashaivism.com/en/node/793',
    'ksh/ta/': 'https://www.sanskrit-trikashaivism.com/en/node/581',
    'ksh/tantrasara/': 'https://www.sanskrit-trikashaivism.com/en/'
                       'tantrasara-introduction-trika-scriptures-non-dual-shaivism-of-kashmir/919',
    'ksh/ph/': 'https://www.sanskrit-trikashaivism.com/en/'
               'pratyabhijnahrdayam-commentary-introduction-trika-scriptures-non-dual-shaivism-of-kashmir/543',
}

# Страницы этих разделов — сам перенесённый перевод. Заглавная страница раздела
# и словарь написаны здесь и переводятся.
ROUND = ('ksh/pv/s', 'ksh/ta/ch', 'ksh/tantrasara/ch', 'ksh/ph/s', 'ksh/ph/begin')

# Что не идёт в перевод вовсе: служебное, не страницы.
SKIP = ('_sitecheck/', 'sitesearch/', 'tools/', '.claude/', 'en/',
        'search-index/', 'search/', 'dance/search.md')

CYR = re.compile(r'[А-Яа-яЁё]')
# Санскритская помета — та же, что маскируется при переводе. Здесь она нужна,
# чтобы сличить её последовательность до и после.
MARK = re.compile(r'\([A-Za-zĀ-ſḀ-ỿ\'\-\s.…|]+\)')
FM = re.compile(r'\A---\n(.*?)\n---\n', re.S)
TITLE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.M)
FENCE = re.compile(r'\A```')
LINK = re.compile(r'\]\((/[^)]*)\)')


def pages():
    """Страницы сайта: (путь, переводить ли, почему нет)."""
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in sorted(files):
            if not f.endswith('.md'):
                continue
            rel = os.path.relpath(os.path.join(base, f), ROOT)
            if rel.startswith(SKIP):
                continue
            text = open(os.path.join(ROOT, rel), encoding='utf-8').read()
            if not CYR.search(text):
                out.append((rel, False, 'не по-русски'))
            elif rel.startswith(ROUND):
                out.append((rel, False, 'сама перевод'))
            else:
                out.append((rel, True, ''))
    return out


def twin(rel):
    """Адрес английского двойника: `ksh/index.md` -> `/en/ksh/`."""
    url = '/' + rel[:-len('.md')]
    if url.endswith('/index'):
        url = url[:-len('index')]
    return '/en' + url


def blocks(body):
    """Куски между пустыми строками, как их режет поисковый указатель."""
    return re.split(r'\n\s*\n', body)


def relink(text, have):
    """Ссылки внутрь сайта — на английские двойники, где они есть."""
    def one(m):
        url = m.group(1)
        return '](%s)' % ('/en' + url if url in have else url)
    return LINK.sub(one, text)


def wanted(rel):
    """Куски страницы, которые пойдут в перевод. Порядок значим."""
    src = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    m = FM.match(src)
    head, body = (m.group(1), src[m.end():]) if m else ('', src)
    title = TITLE.search(head)
    out = [title.group(1)] if title else []
    for b in blocks(body):
        if b.strip() and CYR.search(b) and not FENCE.match(b.strip()):
            out.append(b)
    return out


def warm(texts, cache, workers=8):
    """Покупает всё, чего в кеше нет, — в несколько потоков.

    Кеш до и после — единственное, что связывает потоки, и пишут они в него
    под замком. Сборка страницы после этого идёт по кешу и сети не касается:
    так порядок кусков на странице не зависит от того, в каком порядке
    отвечал сервер.
    """
    from common.translate import ask, fingerprint, mask
    need = {}
    for t in texts:
        masked, _parts = mask(t)
        if not re.search(r'[^\W\d_]', re.sub(r'⟦\d+⟧', '', masked), re.U):
            continue
        # Ключ — у кеша, тот же, что берёт `translate()` при сборке. Пока
        # здесь стояло своё имя языка, закупка и сборка считали разные ключи, и
        # всё покупалось дважды.
        fp = fingerprint(masked, cache.lang)
        if cache.get(fp) is None:
            need[fp] = masked
    if not need:
        return 0
    lock = threading.Lock()
    done = [0]

    def one(item):
        fp, masked = item
        got = ask(masked, LANG)
        with lock:
            cache.put(fp, got)
            done[0] += 1
            if done[0] % 100 == 0:
                cache.save()
                print('   куплено %d из %d' % (done[0], len(need)), flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, list(need.items())))
    cache.save()
    return len(need)


def do(rel, cache, stats, dry=False):
    """Переводит страницу. Кусок, испортивший подстрочник, остаётся русским.

    Модель не только теряет — она **добавляет**: там, где в русском стояло
    тире, в английском появляется пояснение в скобках. На рукописной странице
    скобка это скобка, и вреда нет. На странице писания из скобок строится
    подстрочник: `(Devanāgarī and IAST)` встало бы мелким шрифтом над соседним
    словом, будто это санскрит. Двадцать страниц гимнов получили такую скобку с
    первого же прогона.

    Поэтому там, где подстрочник есть, последовательность помет сличается до и
    после. Разошлась — кусок остаётся русским: правило то же, что с метками, и
    по той же причине. Испорченное место чинить нечем, а по-русски оно хотя бы
    не врёт.
    """
    src = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    ruby = 'pv-tr' in src or 'pv-pair' in src
    m = FM.match(src)
    head, body = (m.group(1), src[m.end():]) if m else ('', src)

    title = TITLE.search(head)
    if title and dry:
        en_title = title.group(1)
    elif title:
        en_title = translate(title.group(1), LANG, cache, stats) or title.group(1)
    else:
        en_title = None

    done = []
    for b in blocks(body):
        if not b.strip() or not CYR.search(b) or FENCE.match(b.strip()):
            done.append(b)
            continue
        if dry:
            stats['would'] = stats.get('would', 0) + 1
            done.append(b)
            continue
        got = translate(b, LANG, cache, stats)
        if got is not None and ruby and MARK.findall(got) != MARK.findall(b):
            stats['marks'] = stats.get('marks', 0) + 1
            got = None
        done.append(got if got is not None else b)
    return en_title, '\n\n'.join(done)


def write(rel, en_title, body, have):
    dest = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    head = '---\n'
    if en_title:
        head += 'title: "%s"\n' % en_title.replace('"', "'")
    head += 'lang: en\n'
    # Из поиска по сайту перевод пока исключён, и это временно.
    #
    # Указатель не знает языков: он собирает всё подряд, и появление 97
    # английских двойников раздуло его со 141 страницы до 239, а русскому
    # читателю стало выдавать вперемешку два языка — каждую находку дважды, на
    # двух языках. Русский поиск — то, чем сайт пользуются каждый день;
    # английские страницы появились час назад. Портить первое ради второго
    # нельзя.
    #
    # Настоящее решение —языковая пометка у страницы в указателе и отбор по
    # языку читателя. Оно делается в общем движке поиска (`sitesearch`), и как
    # только доедет — эту строку надо снять, а не оставить навсегда.
    head += 'search: false\n'
    # Обратный путь. Стоит первой строкой, чтобы читатель, попавший сюда из
    # поиска, сразу видел, что оригинал русский и он рядом.
    head += 'ru: %s\n---\n\n' % ('/' + rel[:-len('.md')].removesuffix('/index') + '/').replace('//', '/')
    open(dest, 'w', encoding='utf-8').write(head + relink(body, have).rstrip() + '\n')


def roster(todo):
    """Список переведённых страниц — в `_data/i18n.yml`, для макета.

    Макету надо знать две вещи: есть ли у русской страницы английский двойник
    (тогда на ней стоит переключатель и `hreflang`) и наоборот. У английской
    страницы обратный адрес лежит во front matter (`ru:`), а русская о своём
    двойнике сама знать не может — оттуда и список.
    """
    path = os.path.join(ROOT, '_data', 'i18n.yml')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    urls = sorted(twin(rel)[len('/en'):] for rel in todo)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Собирается `tools/translate.py`. Руками не править.\n')
        f.write('#\n# Адреса русских страниц, у которых есть английский двойник в /en/.\n')
        f.write('en:\n')
        for u in urls:
            f.write('  - "%s"\n' % u)
    return len(urls)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('only', nargs='*', help='только эти страницы')
    ap.add_argument('--list', action='store_true', help='что пойдёт в перевод')
    ap.add_argument('--dry', action='store_true', help='прогнать, ничего не покупая')
    ap.add_argument('--workers', type=int, default=8, help='сколько запросов разом')
    args = ap.parse_args()

    rows = pages()
    if args.list:
        yes = [r for r in rows if r[1]]
        no = [r for r in rows if not r[1]]
        print('переводим: %d' % len(yes))
        print('не переводим: %d' % len(no))
        for rel, _, why in no:
            print('   %-40s %s' % (rel, why))
        return 0

    todo = [r[0] for r in rows if r[1]]
    if args.only:
        todo = [r for r in todo if r in args.only]
        if not todo:
            sys.exit('таких страниц в переводе нет: %s' % ' '.join(args.only))
    have = {twin(r)[len('/en'):] for r in todo}

    cache, stats = Cache(CODE), {}

    if not args.dry:
        texts = [t for rel in todo for t in wanted(rel)]
        print('кусков %d, покупаем недостающие…' % len(texts), flush=True)
        print('куплено: %d' % warm(texts, cache, args.workers))

    for n, rel in enumerate(todo, 1):
        en_title, body = do(rel, cache, stats, args.dry)
        if not args.dry:
            write(rel, en_title, body, have)
        if n % 20 == 0 or n == len(todo):
            print('%3d/%d  %s' % (n, len(todo), stats), flush=True)
    cache.save()
    if not args.dry:
        print('в _data/i18n.yml: %d страниц' % roster(todo))
    print('готово: %s' % stats)
    if stats.get('lost'):
        print('вернулись без меток и остались по-русски: %d' % stats['lost'])
    if stats.get('marks'):
        print('испортили бы подстрочник и остались по-русски: %d' % stats['marks'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
