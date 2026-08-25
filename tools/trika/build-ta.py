#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""«Тантралока» из собрания IAST — в страницы Jekyll под /ksh/ta/.

Кладёт на сайт **только санскрит** в транслитерации: 37 глав, 5849 строф. Ни
перевода, ни комментария — переводы у источника принадлежат Габриэлю Pradīpaka,
и дублировать их мы не станем (VS-13). Смысл этих страниц один: найти строфу.
От каждой главы стоит ссылка туда, где её читают с переводом.

    python3 tools/trika/build-ta.py            # собрать ksh/ta/
    python3 tools/trika/build-ta.py --check    # только сверить, ничего не писать

Источник — файл собрания `Tantrāloka.rtf` (см. /ksh/scriptures/). Он лежит вне
репозитория; путь задаётся --src, по умолчанию берётся из ~/Downloads.

Разметка страницы повторяет /ksh/pv/ (класс `pv-iast`), и не только ради вида:
указатель поиска собирает Jekyll, а он режет содержимое на абзацы по пустой
строке. Поэтому строфа — ровно один абзац исходника, и попадание указывает на
строфу, а не на главу в триста строф. Якорь берётся из номера в конце строфы;
собирает указатель `ksh/ta/search-index.json`.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'ksh', 'ta')
SRC = os.path.expanduser(
    '~/Downloads/Trika_Scriptures_IAST_transliteration/Tantrāloka/Tantrāloka.rtf')
NODE = 'https://www.sanskrit-trikashaivism.com/%s/node/%d'

HEAD = re.compile(r'^Āhnika\s+(\d+)\s*[–—-]\s*(.+)$')
NUM = re.compile(r'\|\|(\d+)\.(\d+)\|\|[\s\]]*$')
# «Atha śrītantrāloke saptadaśamāhnikam|» — открывающая строка главы. Порядковое
# числительное стоит то отдельным словом, то приросшим к предыдущему через
# авагра́ху: «śrītantrāloke'ṣṭāviṁśamāhnikam». Поэтому между началом и концом
# строки — что угодно, лишь бы недлинное.
OPENING = re.compile(r'^Atha śrītantrāloke.{0,40}māhnikam\|$')
CLOSING = re.compile(r'\|\|\s*$')

# Глава → страницы источника. Русский перевод у Габриэля доведён до 16-й главы
# включительно; дальше страницы есть, но перевода на них нет (VS-13, проверено
# tools/trika/ta-ru-scan.py). Ссылка ведёт на первую страницу главы: у длинных
# глав источник делит её на части, и они связаны между собой.
SOURCE = {
    1: 582, 2: 857, 3: 858, 4: 860, 5: 862, 6: 863, 7: 865, 8: 866, 9: 869,
    10: 871, 11: 873, 12: 874, 13: 875, 14: 878, 15: 879, 16: 883, 17: 885,
    18: 886, 19: 887, 20: 888, 21: 889, 22: 890, 23: 891, 24: 892, 25: 893,
    26: 894, 27: 895, 28: 896, 29: 899, 30: 901, 31: 902, 32: 903, 33: 904,
    34: 905, 35: 906, 36: 907, 37: 908,
}
RUSSIAN_THROUGH = 16


def read(path):
    """Текст собрания: .rtf разворачивается textutil, .txt берётся как есть."""
    if path.endswith('.rtf'):
        return subprocess.run(['textutil', '-convert', 'txt', '-stdout', path],
                              check=True, capture_output=True).stdout.decode('utf-8')
    return open(path, encoding='utf-8').read()


def parse(text):
    """Собрание → главы: номер, имя, открывающая строка, строфы, колофон.

    Строфа кончается номером вида ||17.3||, и до него может идти сколько
    угодно строк — обычно две. Всё, что не строфа: заголовок главы, её
    открывающая строка «Atha śrītantrāloke...» и колофон, кончающийся на ||
    без номера.
    """
    chapters, cur, buf = [], None, []
    for raw in text.split('\n'):
        line = raw.strip()
        if not line or line == 'Tantrāloka' or line.startswith('http'):
            continue
        m = HEAD.match(line)
        if m:
            cur = {'no': int(m.group(1)), 'name': m.group(2).strip(),
                   'opening': None, 'stanzas': [], 'closing': None}
            chapters.append(cur)
            buf = []
            continue
        if cur is None:
            raise SystemExit('строка до первого заголовка главы: %r' % line)
        if OPENING.match(line) and not buf:
            cur['opening'] = line
            continue
        buf.append(line)
        m = NUM.search(line)
        if m:
            cur['stanzas'].append((int(m.group(1)), int(m.group(2)), buf))
            buf = []
        elif CLOSING.search(line):
            cur['closing'] = ' '.join(buf)
            buf = []
    if buf:
        raise SystemExit('хвост без номера строфы: %r' % buf[:2])
    return chapters


def check(chapters):
    """Разбор сошёлся с собранием — или не собирать вовсе."""
    bad = []
    if len(chapters) != 37:
        bad.append('глав %d, а не 37' % len(chapters))
    for ch in chapters:
        for i, (c, s, _) in enumerate(ch['stanzas'], 1):
            if c != ch['no']:
                bad.append('в главе %d строфа помечена %d.%d' % (ch['no'], c, s))
                break
        nums = [s for _, s, _ in ch['stanzas']]
        if nums != sorted(nums):
            bad.append('в главе %d строфы не по порядку' % ch['no'])
        if not nums:
            bad.append('в главе %d нет строф' % ch['no'])
    return bad


def stanzas_word(n):
    """«1 строфа», «332 строфы», «5849 строф» — по последним цифрам числа."""
    if 11 <= n % 100 <= 14:
        return 'строф'
    return {1: 'строфа', 2: 'строфы', 3: 'строфы', 4: 'строфы'}.get(n % 10, 'строф')


def esc(line):
    """Строка санскрита внутри HTML: экранируется только то, что ломает разметку."""
    return line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def stanza_html(c, s, lines):
    """Строфа — один абзац исходника, чтобы указатель поиска взял её целиком.

    Номер стоит ссылкой на самого себя: это и якорь, и способ сослаться на
    строфу. Класса `nosearch` на нём нет намеренно — он выбрасывает из
    указателя весь абзац, а выбросить надо было бы одно число.
    """
    body = '<br />\n'.join(esc(l) for l in lines)
    return ('<p class="ta-st" id="v%d.%d"><a class="ta-num" href="#v%d.%d">%d.%d</a> '
            '<span class="pv-iast">%s</span></p>' % (c, s, c, s, c, s, body))


def chapter_page(ch, prev, nxt):
    ru = ch['no'] <= RUSSIAN_THROUGH
    src = NODE % ('ru' if ru else 'en', SOURCE[ch['no']])
    where = ('перевод главы у источника' if ru
             else 'английский перевод у источника — русского там нет')

    out = ['---',
           'title: "Тантралока, глава %d — %s"' % (ch['no'], ch['name']),
           '# Текст этих страниц попадает в поиск через ksh/ta/search-index.json:',
           '# он собирает строфу целиком и ставит на неё якорь. Указателю по сайту',
           '# нечего добавить, а текст в двух указателях — это он же дважды.',
           'search: false',
           '---',
           '']
    crumbs = ['[КШ](/ksh/)', '[Тантралока](/ksh/ta/)', '[Поиск по сайту](/search/)']
    out.append('<p class="pv-crumbs nosearch" markdown="1">%s</p>' % ' · '.join(crumbs))
    out.append('')
    out.append('# Глава %d — %s' % (ch['no'], ch['name']))
    out.append('')
    out.append('<p class="ta-meta nosearch" markdown="1">%d %s · только санскрит '
               'в транслитерации IAST · [%s](%s)</p>'
               % (len(ch['stanzas']), stanzas_word(len(ch['stanzas'])), where, src))
    out.append('')

    pager = []
    pager.append('[← %s](%s)' % (
        ('Глава %d — %s' % (prev['no'], prev['name'])) if prev else 'Тантралока',
        ('/ksh/ta/ch%d/' % prev['no']) if prev else '/ksh/ta/'))
    if nxt:
        pager.append('[Глава %d — %s →](/ksh/ta/ch%d/)' % (nxt['no'], nxt['name'], nxt['no']))
    out.append('<p class="pv-pager nosearch" markdown="1">%s</p>' % ' · '.join(pager))
    out.append('')

    if ch['opening']:
        out.append('<p class="ta-open pv-iast">%s</p>' % esc(ch['opening']))
        out.append('')
    for c, s, lines in ch['stanzas']:
        out.append(stanza_html(c, s, lines))
        out.append('')
    if ch['closing']:
        out.append('<p class="ta-open pv-iast">%s</p>' % esc(ch['closing']))
        out.append('')

    out.append('<p class="pv-pager nosearch" markdown="1">%s</p>' % ' · '.join(pager))
    out.append('')
    return '\n'.join(out)


def index_page(chapters):
    total = sum(len(ch['stanzas']) for ch in chapters)
    rows = []
    for ch in chapters:
        ru = ch['no'] <= RUSSIAN_THROUGH
        src = NODE % ('ru' if ru else 'en', SOURCE[ch['no']])
        rows.append('| [%d](/ksh/ta/ch%d/) | [%s](/ksh/ta/ch%d/) | %d | [%s](%s) |'
                    % (ch['no'], ch['no'], ch['name'], ch['no'], len(ch['stanzas']),
                       'русский' if ru else 'английский', src))

    page = PAGE.replace('@ROWS@', '\n'.join(rows))
    return page.replace('@TOTAL@', '{:,}'.format(total).replace(',', ' '))


PAGE = """---
title: "Тантралока: санскрит целиком, с поиском по строфам"
---

<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [Писания Трики](/ksh/scriptures/) · [Поиск по сайту](/search/) · [Тантралока у источника](https://www.sanskrit-trikashaivism.com/ru/node/581)</p>

# Тантралока

«Свет тантр» Абхинавагупты (ок. 950–1020) — свод всего учения Трики и самый
обширный труд традиции: **37 глав, @TOTAL@ строф**, больше половины всего
[собрания писаний](/ksh/scriptures/) по объёму.

Здесь лежит **только санскрит** в транслитерации IAST — ни перевода, ни
комментария. Это местная копия ради одного: чтобы строфу можно было найти по
любому слову и сослаться на неё по номеру. Читать с переводом — у источника, и
от каждой главы туда ведёт ссылка.

Перевод — [Габриэля Pradīpaka](https://www.sanskrit-trikashaivism.com/), и
дублировать его мы не станем. По-русски у него готовы **главы 1–16**, и работа
продолжается; главы 17–37 читаются пока только по-английски.

## Найти строфу

<p><input type="search" id="q" placeholder="например: anuttara, kaulika, mātṛkā" autocomplete="off" spellcheck="false" /></p>

<p id="status"></p>

<ul id="results"></ul>

<p class="ta-hint nosearch"><em>Ищет по всем @TOTAL@ строфам; находка ведёт прямо
к строфе, а не в начало главы. Диакритика необязательна: «srngara» найдёт
śṛṅgāra, «matrka» — mātṛkā. Несколько слов — найдутся строфы, где есть все они.
Эти же строфы находит и <a href="/search/">поиск по сайту</a>, вместе со всем
остальным.</em></p>

## Главы

| № | Глава | Строф | У источника |
|---:|---|---:|---|
@ROWS@

## Откуда это

Текст взят из собрания `Trika_Scriptures_IAST_transliteration` — оно снято с
«IAST only»-версий сайта [sanskrit-trikashaivism.com](https://www.sanskrit-trikashaivism.com/en/node/696)
и содержит один санскрит. Что в этом собрании есть и чего нет по-русски —
на странице [«Писания Трики»](/ksh/scriptures/).

Страницы собраны `tools/trika/build-ta.py` и правятся не руками, а им.

<style>
/* Тема подключается удалённо и точки расширения не имеет, поэтому страница
   одевает выдачу сама — так же, как это делает страница поиска по сайту. */
#q{padding:.45em .6em;width:100%;max-width:32em;font-size:1em}
#results{margin:1.2em 0;padding:0;list-style:none}
#results li{margin:0 0 1.2em}
#results .where{font-size:.85em;opacity:.75;margin-bottom:.15em}
#results .snippet{margin:0;padding:0}
#results mark{background:rgba(255,220,120,.35);color:inherit;padding:0 .1em;border-radius:2px}
</style>

<script src="/sitesearch/search.js"></script>
<script>
/* Тот же движок, что и у поиска по сайту, только указатель один — строфы
   «Тантралоки». Раздел в выдаче не повторяем: он тут у всех один. */
SiteSearch.mount({
    input: 'q', status: 'status', results: 'results',
    showSection: false,
    sources: [{ url: '/ksh/ta/search-index.json' }],
});
</script>
"""


def write(path, body, check_only, changed):
    if check_only:
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        if old != body:
            changed.append(os.path.relpath(path, ROOT))
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=SRC, help='файл собрания (.rtf или .txt)')
    ap.add_argument('--check', action='store_true',
                    help='сверить собранное с тем, что лежит, и ничего не писать')
    args = ap.parse_args()

    if not os.path.exists(args.src):
        raise SystemExit('нет файла собрания: %s\nпуть задаётся --src' % args.src)

    chapters = parse(read(args.src))
    bad = check(chapters)
    if bad:
        for b in bad:
            print('разбор разошёлся:', b, file=sys.stderr)
        return 1

    changed = []
    write(os.path.join(OUT, 'index.md'), index_page(chapters), args.check, changed)
    for i, ch in enumerate(chapters):
        write(os.path.join(OUT, 'ch%d' % ch['no'], 'index.md'),
              chapter_page(ch, chapters[i - 1] if i else None,
                           chapters[i + 1] if i + 1 < len(chapters) else None),
              args.check, changed)

    total = sum(len(ch['stanzas']) for ch in chapters)
    if args.check:
        for c in changed:
            print('разошлось:', c)
        print('глав %d, строф %d; расхождений %d' % (len(chapters), total, len(changed)))
        return 1 if changed else 0
    print('глав %d, строф %d — собрано в ksh/ta/' % (len(chapters), total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
