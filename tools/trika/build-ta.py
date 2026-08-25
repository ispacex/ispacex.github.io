#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""«Тантралока» — в страницы Jekyll под /ksh/ta/.

Санскрит берётся из файла собрания IAST: 37 глав, 5849 строф. Русский перевод —
со страниц источника, где его сделал **Габриэль Pradīpaka**; переведены главы
1–16, и вместе с переводом оттуда переносится деванагари. Главы 17–37 по-русски
у источника не выложены и стоят здесь одной транслитерацией, со ссылкой на
английский перевод.

Ни строки перевода здесь не сделано нами: это перенос, а не перевод. От каждой
главы стоит ссылка на неё же у источника.

    python3 tools/trika/build-ta.py            # собрать ksh/ta/
    python3 tools/trika/build-ta.py --check    # только сверить, ничего не писать

Собрание лежит вне репозитория; путь задаётся --src, по умолчанию берётся из
~/Downloads. Русские страницы источника кладёт в tools/trika/src/ скрипт
ta-ru-scan.py, разбирает — ta-ru.py.

Единица страницы — строфа: указатель поиска собирает Jekyll, а он режет
содержимое на абзацы по пустой строке, и попадание должно указывать на строфу,
а не на главу в триста строф. Якорь у абзаца — его `id`, и по нему же
`ksh/ta/search-index.json` ведёт из выдачи.

Перевод стоит не при каждой строфе, а при **группе**: сколько строф источник
свёл в один абзац, к стольким и относится его перевод (см. ta-ru.py). Чаще
всего в группе одна строфа.
"""
import argparse
import os
import re
import subprocess
import sys

import importlib.util
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Имя файла с дефисом обычным import не берётся, а переименовывать его незачем:
# в tools/trika/ все скрипты названы через дефис.
ta_ru = _load('ta_ru', os.path.join(HERE, 'ta-ru.py'))

sys.path.insert(0, os.path.dirname(HERE))
from common.page import markup
from common.check import verify
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
#
# Кончается «tantrāloka» то на «e», то на «a»: перед словом на «e» сандхи
# оставляет «a» — «Atha śrītantrāloka ekādaśamāhnikam|». Требуй «e» — и пять
# глав (11, 19, 21, 29, 31) останутся без открывающей строки, а она прирастёт
# к их первой строфе.
OPENING = re.compile(r'^Atha śrītantrālok[ae]\b.{0,40}māhnikam\|$')
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


# Любой номер строфы — «||1||» у источника, «||1.1||» в собрании.
ANYNUM = re.compile(r'\|\|[\d.\s-]+\|\|')


def flat(t):
    """Транслитерация без номеров, пробелов и разнобоя в апострофах."""
    t = unicodedata.normalize('NFC', ANYNUM.sub('', t))
    t = re.sub(r'[\s\u00a0\[\]]+', '', t)
    return t.replace('\u2019', "'").replace('\u2018', "'").lower()


def merge(chapters, groups):
    """Кладёт перевод к строфам и возвращает, что при этом не сошлось.

    Сверка здесь не формальность, а единственное доказательство, что перевод
    лёг на свою строфу: собрание и страницы источника — разные файлы, и
    совпасть построчно они могут только если группа стоит там, где мы её
    поставили.

    Заодно эта же сверка вытаскивает вводную строку, которую собрание приклеило
    к первой строфе. У 3-й и 16-й глав перед первой строфой стоит ещё одна
    строка на «Atha…», у источника — отдельным абзацем со своим переводом; в
    собрании она попала в строфу 1, потому что номера не несёт. Что именно
    приклеилось, видно из расхождения: лишнее — ровно тот кусок, которого нет у
    источника.
    """
    bad = []
    by_no = {ch['no']: ch for ch in chapters}
    for no, page in sorted(groups.items()):
        ch, gs = by_no[no], page['groups']
        ch['pre'] = {flat(' '.join(p['iast'])): p['ru'] for p in page['pre']}
        at = {s: lines for _, s, lines in ch['stanzas']}
        for g in gs:
            want = ' '.join(' '.join(at.get(n, [])) for n in g['nums'])
            if flat(want) != flat(' '.join(g['iast'])):
                extra = peel(ch, g, at)
                if extra is None:
                    bad.append('глава %d, строфы %s: собрание и источник расходятся'
                               % (no, g['nums'][:4]))
                    continue
            deva = relines(g, at)
            for n in g['nums']:
                d = deva.get(n, [])
                if d and len(d) != len(at.get(n, [])):
                    odd.append('%d.%d: строк деванагари %d, транслитерации %d'
                               % (no, n, len(d), len(at.get(n, []))))
                ch.setdefault('deva', {})[n] = d
            ch.setdefault('tr', []).append(g)
    return bad


def relines(g, at):
    """Строки деванагари — по строфам так же, как строки транслитерации.

    Номер стоит в конце строфы, и по нему деванагари группы режется на строфы.
    Но издания изредка ставят его на полстроки раньше или позже, чем собрание:
    в 9-й главе строка «नियतिर्नास्ति वैरिञ्चे…» у источника попадает под номер 45,
    а в собрании она открывает 46-ю. Строк при этом столько же — значит,
    расходится только место номера, и делить надо по собранию: деванагари
    стоит на странице **над** своей транслитерацией, и разъехаться им нельзя.

    Где строк не поровну (собрание изредка сводит обе половины строфы в одну
    строку), деление остаётся как есть: там расходится сам текст, а не номер.
    """
    total_d = sum(len(g['deva'].get(n, [])) for n in g['nums'])
    total_i = sum(len(at.get(n, [])) for n in g['nums'])
    if total_d != total_i or not total_d:
        return g['deva']
    flatd = [l for n in g['nums'] for l in g['deva'].get(n, [])]
    out, i = {}, 0
    for n in g['nums']:
        k = len(at.get(n, []))
        out[n] = flatd[i:i + k]
        i += k
    return out


# Места, где строк деванагари и транслитерации не поровну: там расходятся сами
# издания, и починить это перестановкой строк нельзя.
odd = []


def peel(ch, g, at):
    """Отделяет вводную строку, приклеенную собранием к первой строфе."""
    if g['nums'][:1] != [1]:
        return None
    lines = at[1]
    for k in range(1, len(lines)):
        rest = lines[k:] + [' '.join(at.get(n, [])) for n in g['nums'][1:]]
        if flat(' '.join(rest)) == flat(' '.join(g['iast'])):
            ch['extra'] = lines[:k]
            at[1] = lines[k:]
            for i, (c, s, ls) in enumerate(ch['stanzas']):
                if s == 1:
                    ch['stanzas'][i] = (c, s, lines[k:])
            return lines[:k]
    return None


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


def wall(lines, cls, lang=''):
    return '<span class="%s"%s>%s</span>' % (cls, lang, '<br />\n'.join(esc(l) for l in lines))


def stanza_html(c, s, iast, deva):
    """Строфа — один абзац исходника, чтобы указатель поиска взял её целиком.

    Номер стоит ссылкой на самого себя: это и якорь, и способ сослаться на
    строфу. Класса `nosearch` на нём нет намеренно — он выбрасывает из
    указателя весь абзац, а выбросить надо было бы одно число.

    Деванагари есть только у глав 1–16: оно переносится вместе с переводом со
    страниц источника. У собрания, откуда взята транслитерация, деванагари нет
    вовсе.
    """
    body = []
    if deva:
        body.append(wall(deva, 'pv-sa', ' lang="sa"'))
    body.append(wall(iast, 'pv-iast'))
    return ('<p class="ta-st" id="v%d.%d"><a class="ta-num" href="#v%d.%d">%d.%d</a> '
            '%s</p>' % (c, s, c, s, c, s, '<br />\n'.join(body)))


def label(c, nums):
    """Подпись перевода: «2.1» при одной строфе, «1.116–121» при группе."""
    if len(nums) == 1:
        return '%d.%d' % (c, nums[0])
    return '%d.%d–%d' % (c, nums[0], nums[-1])


def tr_html(c, nums, paras):
    """Перевод группы строф — отдельными абзацами, с подстрочником.

    Абзац перевода — своя находка в поиске, со своим якорем: запрос по-русски
    должен приводить к переводу, а не к началу главы. Якорь у первого абзаца
    группы — `t<глава>.<первая строфа>`; ссылка на него стоит подписью слева,
    там же, где у строфы её номер.

    Санскритское слово идёт подстрочником над своим русским, как на /ksh/pv/ и
    /ksh/tantrasara/: скобка через каждое второе слово рвала фразу.
    """
    out = []
    for i, t in enumerate(paras):
        # Якорь есть у каждого абзаца, а не только у первого: находка в поиске
        # должна вести к тому абзацу, где нашлось. Продолжения группы номера
        # не повторяют — иначе выйдет, будто это перевод другой строфы.
        ident = 't%d.%d' % (c, nums[0]) if i == 0 else 't%d.%d-%d' % (c, nums[0], i + 1)
        mark = ('<a class="ta-num" href="#%s">%s</a>' % (ident, label(c, nums))
                if i == 0 else '<a class="ta-num ta-cont" href="#%s">·</a>' % ident)
        # Тело абзаца — в своём <span>, и это не украшение: номер и текст стоят
        # двумя колонками сетки, а сетка раскладывает по ячейкам **каждого**
        # своего ребёнка. Без обёртки каждый подстрочник стал бы ячейкой, и
        # абзац рассыпался бы на слова.
        out.append('<p class="ta-tr" id="%s" markdown="1">%s<span class="ta-body">%s</span></p>'
                   % (ident, mark, markup(t).replace('\n', '<br />\n')))
    return out


def chapter_page(ch, prev, nxt):
    ru = bool(ch.get('tr'))
    src = NODE % ('ru' if ru else 'en', SOURCE[ch['no']])
    what = ('деванагари, транслитерация IAST и русский перевод' if ru
            else 'только санскрит в транслитерации IAST')
    where = ('эта глава у источника' if ru
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
    out.append('<p class="ta-meta nosearch" markdown="1">%d %s · %s · [%s](%s)</p>'
               % (len(ch['stanzas']), stanzas_word(len(ch['stanzas'])), what, where, src))
    out.append('')

    pager = []
    pager.append('[← %s](%s)' % (
        ('Глава %d — %s' % (prev['no'], prev['name'])) if prev else 'Тантралока',
        ('/ksh/ta/ch%d/' % prev['no']) if prev else '/ksh/ta/'))
    if nxt:
        pager.append('[Глава %d — %s →](/ksh/ta/ch%d/)' % (nxt['no'], nxt['name'], nxt['no']))
    out.append('<p class="pv-pager nosearch" markdown="1">%s</p>' % ' · '.join(pager))
    out.append('')

    for line in [ch['opening']] + ch.get('extra', []):
        if not line:
            continue
        out.append('<p class="ta-open pv-iast">%s</p>' % esc(line))
        out.append('')
        for t in ch.get('pre', {}).get(flat(line), []):
            out.append('<p class="ta-tr ta-open-tr" markdown="1">'
                       '<span class="ta-num"></span><span class="ta-body">%s</span></p>'
                       % markup(t).replace('\n', '<br />\n'))
            out.append('')

    deva = ch.get('deva', {})
    at = {s: lines for _, s, lines in ch['stanzas']}
    groups = ch.get('tr') or [{'nums': [s], 'ru': []} for _, s, _ in ch['stanzas']]
    for g in groups:
        for n in g['nums']:
            out.append(stanza_html(ch['no'], n, at[n], deva.get(n)))
            out.append('')
        for line in tr_html(ch['no'], g['nums'], g['ru']):
            out.append(line)
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
        ru = bool(ch.get('tr'))
        src = NODE % ('ru' if ru else 'en', SOURCE[ch['no']])
        rows.append('| [%d](/ksh/ta/ch%d/) | [%s](/ksh/ta/ch%d/) | %d | %s | [%s](%s) |'
                    % (ch['no'], ch['no'], ch['name'], ch['no'], len(ch['stanzas']),
                       'деванагари, IAST, русский' if ru else 'IAST',
                       'русский' if ru else 'английский', src))

    done = sum(len(ch['stanzas']) for ch in chapters if ch.get('tr'))
    page = PAGE.replace('@ROWS@', '\n'.join(rows))
    page = page.replace('@RU@', '{:,}'.format(done).replace(',', ' '))
    page = page.replace('@RUCH@', str(sum(1 for ch in chapters if ch.get('tr'))))
    return page.replace('@TOTAL@', '{:,}'.format(total).replace(',', ' '))


PAGE = """---
title: "Тантралока: санскрит целиком, с поиском по строфам"
---

<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [Писания Трики](/ksh/scriptures/) · [Поиск по сайту](/search/) · [Тантралока у источника](https://www.sanskrit-trikashaivism.com/ru/node/581)</p>

# Тантралока

«Свет тантр» Абхинавагупты (ок. 950–1020) — свод всего учения Трики и самый
обширный труд традиции: **37 глав, @TOTAL@ строф**, больше половины всего
[собрания писаний](/ksh/scriptures/) по объёму.

Это местная копия — ради того, чтобы строфу можно было найти по любому слову и
сослаться на неё по номеру. Первые **@RUCH@ глав (@RU@ строф)** лежат здесь
целиком: деванагари, транслитерация и русский перевод при каждой строфе.
Остальные — одной транслитерацией.

Перевод и весь санскритский аппарат принадлежат **[Габриэлю
Pradīpaka](https://www.sanskrit-trikashaivism.com/)** и перенесены с его сайта
без изменений: ни строки перевода здесь не сделано нами. По-русски у него
готовы главы 1–16, и работа продолжается — главы 17–37 читаются пока только
по-английски, и от каждой из них стоит ссылка туда.

## Найти строфу

<p><input type="search" id="q" placeholder="например: anuttara, kaulika, mātṛkā" autocomplete="off" spellcheck="false" /></p>

<p id="status"></p>

<ul id="results"></ul>

<p class="ta-hint nosearch"><em>Ищет по всем @TOTAL@ строфам и по переводу первых
@RUCH@ глав; находка ведёт прямо к строфе или к её переводу, а не в начало главы.
Искать можно и по-русски, и в транслитерации, и деванагари. Диакритика
необязательна: «srngara» найдёт śṛṅgāra, «matrka» — mātṛkā. Несколько слов —
найдутся абзацы, где есть все они. То же самое находит и <a href="/search/">поиск
по сайту</a>, вместе со всем остальным.</em></p>

## Главы

| № | Глава | Строф | Что здесь | У источника |
|---:|---|---:|---|---|
@ROWS@

## Как читать эти страницы

У глав 1–16 при каждой строфе стоит <span class="pv-sa">деванагари</span>, под
ним *та же строфа в транслитерации IAST*, а следом — перевод. В переводе
санскритское слово стоит <ruby>подстрочником<rp> (</rp><rt>saṁskṛta</rt><rp>)</rp></ruby>
над своим русским, а не скобкой в строке: скобка через каждое второе слово рвала
фразу. Скобки при этом никуда не делись — они видны при копировании и в поиске.

Перевод стоит не при каждой строфе, а при **группе**: сколько строф источник
свёл в один абзац, к стольким и относится его перевод. Чаще всего в группе одна
строфа, и тогда номер перевода совпадает с номером строфы над ним; у группы
номер показан диапазоном — «1.116–121».

## Откуда это

Транслитерация взята из собрания `Trika_Scriptures_IAST_transliteration` — оно
снято с «IAST only»-версий сайта
[sanskrit-trikashaivism.com](https://www.sanskrit-trikashaivism.com/en/node/696)
и содержит один санскрит. Деванагари и русский перевод перенесены со страниц
того же сайта без изменений; их автор — **Габриэль Pradīpaka**. Что в собрании
есть и чего нет по-русски — на странице [«Писания Трики»](/ksh/scriptures/).

В санскрит внесена одна правка, и она из тех, что видны только при сверке: у
15-й главы 444-я строфа подписана у источника «441», хотя 441-я стоит двумя
группами выше. Номер взят по месту. Всё остальное сошлось с собранием знак в
знак — 1403 группы из 1405, а две оставшиеся расходятся тем, что в собрании
вводная строка 3-й и 16-й глав приклеена к первой строфе; здесь она отделена.

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
   «Тантралоки». Раздел в выдаче не повторяем: он тут у всех один.

   defer — карта слов весит под мегабайт: 5849 строф санскрита плюс перевод
   первых шестнадцати глав. Тому, кто зашёл посмотреть оглавление, везти её
   незачем; она поедет с первым же запросом. */
SiteSearch.mount({
    input: 'q', status: 'status', results: 'results',
    showSection: false,
    sources: [{ url: '/ksh/ta/search-index.json', defer: true }],
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
    bad += merge(chapters, ta_ru.collect())
    if bad:
        for b in bad:
            print('разбор разошёлся:', b, file=sys.stderr)
        return 1
    for ch, said, want in ta_ru.OFF:
        print('глава %d: номер под строфой «%s», по месту «%s» — взято по месту'
              % (ch, said, want))
    for x in odd:
        print('строк не поровну (издания расходятся): %s' % x)
    for ch in chapters:
        if ch.get('extra'):
            print('глава %d: вводная строка отделена от первой строфы: %s'
                  % (ch['no'], ch['extra'][0][:60]))

    # Подстрочник не должен менять текста абзаца: указатель поиска собирает
    # Jekyll, снимая теги, и строка обязана совпасть с прежней знак в знак.
    if verify((('глава %d' % ch['no'], label(ch['no'], g['nums']), t)
               for ch in chapters for g in ch.get('tr', []) for t in g['ru'])):
        return 1

    changed = []
    write(os.path.join(OUT, 'index.md'), index_page(chapters), args.check, changed)
    for i, ch in enumerate(chapters):
        write(os.path.join(OUT, 'ch%d' % ch['no'], 'index.md'),
              chapter_page(ch, chapters[i - 1] if i else None,
                           chapters[i + 1] if i + 1 < len(chapters) else None),
              args.check, changed)

    total = sum(len(ch['stanzas']) for ch in chapters)
    ru = sum(len(ch['stanzas']) for ch in chapters if ch.get('tr'))
    if args.check:
        for c in changed:
            print('разошлось:', c)
        print('глав %d, строф %d (с переводом %d); расхождений %d'
              % (len(chapters), total, ru, len(changed)))
        return 1 if changed else 0
    print('глав %d, строф %d (с переводом %d) — собрано в ksh/ta/'
          % (len(chapters), total, ru))
    return 0


if __name__ == '__main__':
    sys.exit(main())
