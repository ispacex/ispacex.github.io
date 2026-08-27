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
получают не перевод, а страницу со ссылкой на подлинник (см. `SECTION`,
`source()` и `stub()`).

Ссылка при этом **не сочиняется**: она уже стоит на каждой такой странице, и
здесь у неё меняется только язык.

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

# Слово из двух алфавитов ловит `check-scripts.py` — та же проверка, что стоит
# на сайте с давних пор. Здесь она нужна раньше: перевод рождает такие слова
# сам. «урас» модель наполовину переложила латиницей и вернула «уras» —
# кириллическая «у», латинское «ras». На странице это выглядит словом, а
# поиском не находится ни по одному написанию.
import importlib.util as _il

_spec = _il.spec_from_file_location('chk', os.path.join(HERE, 'check-scripts.py'))
_chk = _il.module_from_spec(_spec)
_spec.loader.exec_module(_chk)


def mixed(text):
    """Слова, в которых сошлись два алфавита. Пусто — значит чисто."""
    return [m.group(0) for m in _chk.WORD.finditer(text) if _chk.strangers(m.group(0))]

OUT = os.path.join(ROOT, 'en')
LANG = 'English'
CODE = 'en'

# Разделы, чей русский сам перевод. Их страницы не переводятся; вместо этого
# каждая получает свою английскую страницу со ссылкой на подлинник.
#
# `name` — имя раздела: оно в IAST и одинаково на обоих языках. `home` — весь
# раздел у источника. `made` — чей русский лежит на этих страницах: `his` —
# собственный русский Габриэля, перенесённый без изменений; `here` — сделанный
# для этого сайта с его английского. Разница видна читателю и потому написана
# на странице разными словами.
#
# Адреса заглавных сверены по заголовку страницы у источника, а не выписаны на
# глаз: выписанный на глаз уже был неверен — у Parātrīśikāvivaraṇa здесь стоял
# узел 793, а это «строфы 1–2, часть 4», а не введение.
SECTION = {
    'ksh/pv/': ('Parātrīśikāvivaraṇa',
                'https://www.sanskrit-trikashaivism.com/en/node/540', 'here'),
    'ksh/ta/': ('Tantrāloka',
                'https://www.sanskrit-trikashaivism.com/en/node/581', 'his'),
    'ksh/tantrasara/': ('Tantrasāra',
                        'https://www.sanskrit-trikashaivism.com/en/node/919', 'his'),
    'ksh/ph/': ('Pratyabhijñāhṛdayam',
                'https://www.sanskrit-trikashaivism.com/en/node/543', 'here'),
}

# Ссылка на подлинник не сочиняется. Она уже стоит на каждой из этих страниц —
# в хлебных крошках («Эта часть у источника») или в подписи под текстом, — и
# берётся оттуда; здесь у неё меняется только язык.
#
# Так можно потому, что узел у Габриэля **один на оба языка**: `/ru/node/869` и
# `/en/node/869` — две версии одной и той же девятой главы. Значит перевод
# адреса не может привести не на ту страницу. Считать адрес по номеру главы,
# наоборот, нельзя: номера узлов идут с пропусками (869, 871, 873, 878…), и
# арифметика попала бы в соседний текст, ничем не выдав ошибки.
SRC = re.compile(r'https://www\.sanskrit-trikashaivism\.com/(ru|en)/(?:[^)"\s]+/)?(\d+)(#[^)"\s]*)?')


def source(text):
    """Английский подлинник этой страницы у Габриэля. Ссылки нет — None."""
    m = SRC.search(text)
    if not m:
        return None
    lang, node, frag = m.groups()
    if lang == 'en':
        return m.group(0)
    return 'https://www.sanskrit-trikashaivism.com/en/node/%s%s' % (node, frag or '')


def section(rel):
    """(префикс раздела, имя, заглавная у источника, чей русский)."""
    for pref, row in SECTION.items():
        if rel.startswith(pref):
            return (pref,) + row
    return None, None, None, None

# Страницы этих разделов — сам перенесённый перевод. Заглавная страница раздела
# и словарь написаны здесь и переводятся.
ROUND = ('ksh/pv/s', 'ksh/ta/ch', 'ksh/tantrasara/ch', 'ksh/ph/s', 'ksh/ph/begin')

# Что не идёт в перевод вовсе: служебное, не страницы.
SKIP = ('_sitecheck/', 'sitesearch/', 'tools/', '.claude/', 'en/',
        'search-index/', 'search/', 'dance/search.md', 'CLAUDE.md')

# Двойник, написанный руками. Страница поиска машине не отдаётся (она наполовину
# из <script>, и переводить в ней надо не прозу, а обещания движку), но
# английская пара у неё есть — en/search/index.md, и правится она там же.
#
# Названа она здесь затем, чтобы ссылки с английских страниц вели к ней, а не на
# русский поиск, и чтобы переключатель языка на самом поиске знал, куда вести.
# Сама страница помечена `byhand: true` — по этой пометке её обходит
# tools/check-i18n.py, который сличает перевод с исходником построчно.
# Иначе выходило бы обидное: перевод в указателе есть и по языку отбирается, а
# прийти за ним читателю некуда — тридцать шесть английских страниц отправляют
# его на русский поиск, где английских находок нет по построению.
BYHAND = ('/search/',)

# Что во front matter принадлежит переводу, а не странице: заголовок он
# переводит, язык объявляет, обратный адрес считает. Всё остальное — своё у
# страницы, и до двойника обязано доехать.
OURS = ('title', 'lang', 'ru')

# А это не доедет никогда. `permalink` — это адрес: доехав, он заставил бы обе
# страницы просить один и тот же, и Jekyll отдал бы его одной из двух, молча.
NEVER = ('permalink',)

# Поля, в которых лежит проза, а не признак: их переводим, а не переносим.
# `description` читает `{% seo %}` — он уезжает в выдачу поисковика и в карточку
# ссылки, то есть остаётся русским ровно там, где виден чаще самой страницы.
PROSE = ('description',)

# Строка front matter вида `имя: значение`. Продолжений и вложенности здесь не
# бывает: front matter на этом сайте плоский (проверено по всем страницам).
FMLINE = re.compile(r'^([A-Za-z_][\w-]*):\s*(.*)$')

CYR = re.compile(r'[А-Яа-яЁё]')
# Санскритская помета — та же, что маскируется при переводе. Здесь она нужна,
# чтобы сличить её последовательность до и после.
MARK = re.compile(r'\([A-Za-zĀ-ſḀ-ỿ\'\-\s.…|]+\)')
FM = re.compile(r'\A---\n(.*?)\n---\n', re.S)
TITLE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.M)
FENCE = re.compile(r'\A```')
LINK = re.compile(r'\]\((/[^)]*)\)')
# Ссылка бывает и разметкой Markdown, и готовым тегом: перечни глав на
# заглавных страницах разделов написаны прямо на HTML. Пока правилось только
# первое, английская страница «Pratyabhijñāhṛdayam» уводила читателя в русские
# афоризмы, хотя английские двойники у них были.
HREF = re.compile(r'href="(/[^"]*)"')


def pages():
    """Страницы сайта: (путь, что с ней делать, пояснение).

    Три состояния, а не два: `ours` — перевести, `source` — не переводить, а
    поставить ссылку на подлинник, `no` — не трогать вовсе.
    """
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
                out.append((rel, 'no', 'не по-русски'))
            elif rel.startswith(ROUND):
                out.append((rel, 'source', 'сама перевод — ссылка на подлинник'))
            else:
                out.append((rel, 'ours', ''))
    return out


def title_of(rel):
    """Заголовок страницы из front matter. Нет — None."""
    src = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    m = FM.match(src)
    if not m:
        return None
    t = TITLE.search(m.group(1))
    return t.group(1) if t else None


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
    """Ссылки внутрь сайта — на английские двойники, где они есть.

    Якорь отделяется и возвращается на место: `/ksh/ta/ch9/#v9.5` — та же
    страница, что `/ksh/ta/ch9/`, и без этого она бы не узналась.
    """
    def swap(url):
        base, sep, frag = url.partition('#')
        return ('/en' + base + sep + frag) if base in have else url

    text = LINK.sub(lambda m: '](%s)' % swap(m.group(1)), text)
    return HREF.sub(lambda m: 'href="%s"' % swap(m.group(1)), text)


def looks(en, ru):
    """Похоже ли это на перевод строки, а не на разговор с моделью.

    Проза, вернувшаяся не тем, чем была, видна глазами: абзац на странице
    читают. Строка front matter не видна нигде — её читает механика, и потому
    сличать её приходится здесь.

    Четыре признака, и каждый нашёлся на сайте: пусто или метки не вернулись
    (заголовок страницы пожертвований — модель приписала к нему `⟦0⟧`, которого
    в исходнике не было); перевод в несколько строк; кириллица (модель
    пересказывает исходник, цитируя его); длина не по чину (два заголовка глав
    «Натьяшастры» уехали на сайт целым абзацем «I need the source text to
    translate…»). Пятый — числа: номер главы в заголовке не украшение, по нему
    читатель сверяет, туда ли попал, и по нему же главы выстраиваются в палитре.
    """
    if not en or not en.strip():
        return False
    if '\n' in en.strip():
        return False
    if CYR.search(en):
        return False
    if len(en) > 2 * len(ru) + 24:
        return False
    return re.findall(r'\d+', en) == re.findall(r'\d+', ru)


def phrase(ru, cache, stats):
    """Строка front matter по-английски: заголовок, описание. Не вышло — None.

    Спрашивается дважды. Первый раз — общим наказом, тем же, каким переводится
    проза: его ответы уже куплены, и переспрашивать все полторы сотни заголовков
    ради трёх испорченных незачем. Ответ, на строку не похожий, отвергается, и
    тогда — второй раз, назвав вещь своим именем (`kind='title'`): «это
    заголовок страницы, а не просьба к тебе». Купится при этом только то, что и
    правда испорчено.
    """
    got = translate(ru, LANG, cache, stats)
    if looks(got, ru):
        return got
    stats['reask'] = stats.get('reask', 0) + 1
    got = translate(ru, LANG, cache, stats, kind='title')
    return got if looks(got, ru) else None


def wanted(rel):
    """Куски страницы, которые пойдут в перевод. Порядок значим."""
    src = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    m = FM.match(src)
    head, body = (m.group(1), src[m.end():]) if m else ('', src)
    title = TITLE.search(head)
    out = [title.group(1)] if title else []
    for line in head.split('\n'):
        f = FMLINE.match(line)
        if f and f.group(1) in PROSE:
            out.append(f.group(2).strip().strip('"'))
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
        en_title = phrase(title.group(1), cache, stats)
        if en_title is None:
            stats['titles'] = stats.get('titles', 0) + 1
            en_title = title.group(1)
    else:
        en_title = None

    # Что страница объявила о себе сверх заголовка: `layout`, `search`, всё
    # прочее. Раньше сюда не смотрели вовсе — шапка двойника собиралась с нуля,
    # и объявленное молча пропадало. Так английская страница пожертвований
    # потеряла `layout: donate`, а с ним и кнопки копирования крипто-адресов:
    # адреса остались на ней текстом, и скопировать их стало нечем.
    extra = []
    for line in head.split('\n'):
        f = FMLINE.match(line)
        if not f:
            continue
        name, value = f.group(1), f.group(2)
        if name in OURS or name in NEVER:
            continue
        if name in PROSE:
            ru = value.strip().strip('"')
            if not dry and CYR.search(ru):
                got = phrase(ru, cache, stats)
                if got is None:
                    stats['fields'] = stats.get('fields', 0) + 1
                value = '"%s"' % (got or ru).replace('"', "'")
            extra.append('%s: %s' % (name, value))
            continue
        extra.append(line)

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
        if got is not None and mixed(got) and not mixed(b):
            stats['mixed'] = stats.get('mixed', 0) + 1
            got = None
        # Непарная звёздочка не портит абзац — она портит **всё, что ниже**:
        # полужирное начинается и не кончается до конца страницы. Сличается
        # чётность до и после, а не сама чётность: кое-где звёздочка непарна и
        # по-русски, и перевод там ни при чём.
        if got is not None and got.count('**') % 2 != b.count('**') % 2:
            stats['bold'] = stats.get('bold', 0) + 1
            got = None
        done.append(got if got is not None else b)
    return en_title, extra, '\n\n'.join(done)


def write(rel, en_title, extra, body, have):
    dest = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    head = '---\n'
    if en_title:
        head += 'title: "%s"\n' % en_title.replace('"', "'")
    # `lang` — не только для <html lang>. Его же читает поисковый указатель:
    # страница, назвавшая язык, попадает в выдачу только тому, кто читает на
    # этом языке. Пока движок языков не знал, перевод из поиска исключался
    # целиком (`search: false`), иначе русскому читателю каждая находка
    # выдавалась дважды, на двух языках. Теперь исключать нечего: обе выдачи
    # одноязычны, и перевод наконец ищется — на своих страницах.
    head += 'lang: en\n'
    # Обратный путь. Считается тем же `twin()`, что и путь туда, — своя
    # арифметика здесь однажды уже соврала: `index.md` она обращала в
    # «/index/», и переключатель с английской главной вёл в 404. Адрес
    # страницы и адрес её двойника — одно знание, и живёт оно в одном месте.
    head += 'ru: %s\n' % twin(rel)[len('/en'):]
    # Своё у страницы — следом, чтобы сверху стояло сказанное переводом, а под
    # ним перенесённое как есть.
    for line in extra:
        head += line + '\n'
    head += '---\n\n'
    open(dest, 'w', encoding='utf-8').write(head + relink(body, have).rstrip() + '\n')


# Что стоит на английской странице вместо перевода. Текста два, потому что
# происхождение русского разное, и читателю эта разница важна: в одном случае
# русское здесь — работа Габриэля, в другом — наша работа по его английскому.
WHOSE = {
    'his': ("The Russian on this page is **Gabriel Pradīpaka's own translation**, kept "
            "here unchanged so that a stanza can be found by any word in it. Rather than "
            "run his work through a machine and back into English, here is his own English:"),
    'here': ("The Russian on this page was made **for this site, out of Gabriel Pradīpaka's "
             "English**. Translating it back would hand you a third-hand retelling of a text "
             "whose original is one link away:"),
}


def stub(rel, en_title):
    """Английская страница взамен непереведённой: чей текст и куда за подлинником.

    Ссылка ведёт **на эту же часть**, а не на раздел вообще: она взята с самой
    страницы (`source()`), и заглавная раздела остаётся лишь на случай, когда
    ссылки на странице почему-то нет.
    """
    pref, name, home, whose = section(rel)
    text = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    src = source(text) or home
    ru_url = twin(rel)[len('/en'):]
    en_home = '/en/' + pref
    head = ('---\n'
            'title: "%s"\n'
            'lang: en\n'
            # Своего текста у такой страницы нет — искать в ней нечего.
            'search: false\n'
            'source: %s\n'
            'ru: %s\n'
            '---\n\n') % ((en_title or name).replace('"', "'"), src, ru_url)
    body = (
        '<p class="pv-crumbs nosearch" markdown="1">[Kashmir Shaivism](/en/ksh/) · '
        '[%(name)s](%(home)s) · [Glossary](%(home)sglossary/)</p>\n\n'
        '# %(title)s\n\n'
        '> **Not translated here, and on purpose.** %(whose)s\n'
        '>\n'
        '> **[Read this part in the author\'s own English](%(src)s)**\n'
        '>\n'
        '> The Russian page you were heading for is [still here](%(ru)s) — the Sanskrit '
        'on it is the same Sanskrit.\n'
    ) % {'name': name, 'home': en_home, 'title': en_title or name,
         'whose': WHOSE[whose], 'src': src, 'ru': ru_url}
    dest = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, 'w', encoding='utf-8').write(head + body)


def roster(todo):
    """Список переведённых страниц — в `_data/i18n.yml`, для макета.

    Макету надо знать две вещи: есть ли у русской страницы английский двойник
    (тогда на ней стоит переключатель и `hreflang`) и наоборот. У английской
    страницы обратный адрес лежит во front matter (`ru:`), а русская о своём
    двойнике сама знать не может — оттуда и список.
    """
    path = os.path.join(ROOT, '_data', 'i18n.yml')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    urls = sorted(set(twin(rel)[len('/en'):] for rel in todo) | set(BYHAND))
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
        for kind, what in (('ours', 'переводим'), ('source', 'ссылка на подлинник'),
                           ('no', 'не трогаем')):
            part = [r for r in rows if r[1] == kind]
            print('%s: %d' % (what, len(part)))
            if kind != 'ours':
                for rel, _k, why in part:
                    print('   %-40s %s' % (rel, why))
        return 0

    todo = [r[0] for r in rows if r[1] == 'ours']
    refs = [r[0] for r in rows if r[1] == 'source']
    if args.only:
        todo = [r for r in todo if r in args.only]
        refs = [r for r in refs if r in args.only]
        if not todo and not refs:
            sys.exit('таких страниц в переводе нет: %s' % ' '.join(args.only))
    # Двойник есть и у страницы-заместителя: иначе ссылка на главу с английской
    # заглавной раздела вела бы прямо в русский текст, ничем не предупредив.
    have = {twin(r)[len('/en'):] for r in todo + refs} | set(BYHAND)

    cache, stats = Cache(CODE), {}

    if not args.dry:
        texts = [t for rel in todo for t in wanted(rel)]
        texts += [t for t in (title_of(r) for r in refs) if t]
        print('кусков %d, покупаем недостающие…' % len(texts), flush=True)
        print('куплено: %d' % warm(texts, cache, args.workers))

    for n, rel in enumerate(todo, 1):
        en_title, extra, body = do(rel, cache, stats, args.dry)
        if not args.dry:
            write(rel, en_title, extra, body, have)
        if n % 20 == 0 or n == len(todo):
            print('%3d/%d  %s' % (n, len(todo), stats), flush=True)

    for rel in refs:
        ru_title = title_of(rel)
        en_title = ru_title
        if ru_title and not args.dry:
            # Заголовок у этих страниц — номер и имя: «глава 9», «афоризм 3»,
            # «строфы 3–4, часть 1». Номер тут не украшение: по нему читатель
            # сверяет, туда ли попал, и по нему же страницы выстраиваются в
            # палитре перехода. Пропал или переменился — заголовок остаётся
            # русским: русский заголовок хуже читается, неверный номер врёт.
            # Правило это теперь общее с переведёнными страницами и живёт в
            # `looks()`: разбор у заголовка один, на какой бы странице он ни
            # стоял.
            got = phrase(ru_title, cache, stats)
            if got:
                en_title = got
            else:
                stats['titles'] = stats.get('titles', 0) + 1
        if not args.dry:
            stub(rel, en_title)
    if refs:
        print('со ссылкой на подлинник: %d' % len(refs))
    cache.save()
    if not args.dry:
        print('в _data/i18n.yml: %d страниц' % roster(todo + refs))
    print('готово: %s' % stats)
    if stats.get('lost'):
        print('вернулись без меток и остались по-русски: %d' % stats['lost'])
    if stats.get('marks'):
        print('испортили бы подстрочник и остались по-русски: %d' % stats['marks'])
    if stats.get('mixed'):
        print('дали слово из двух алфавитов и остались по-русски: %d' % stats['mixed'])
    if stats.get('bold'):
        print('потеряли звёздочку и остались по-русски: %d' % stats['bold'])
    if stats.get('titles'):
        print('заголовок не дался и остался русским: %d' % stats['titles'])
    if stats.get('fields'):
        print('поле front matter не далось и осталось русским: %d' % stats['fields'])
    if stats.get('reask'):
        print('переспрошено заголовком: %d' % stats['reask'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
