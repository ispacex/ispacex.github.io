#!/usr/bin/env python3
"""Разбирает страницу sanskrit-trikashaivism.com в список блоков.

Вёрстка у Габриэля Pradīpaka одна на все писания, поэтому разбор здесь общий:
им пользуются и /ksh/pv/, и /ksh/tantrasara/. Держится она на классах, а не на
структуре, поэтому вид блока определяется классом абзаца и письменностью
внутри:

  unicodesfontgreen + lang=sa  — деванагари комментария Абхинавагупты
  unicodesfont*   (без green)  — деванагари исходных строф писания
  alignmentcentered            — либо IAST, либо перевод: решает письменность
  stylered / stylegreen        — санскритское слово в скобках внутри перевода
"""
import re, json, sys, html as H

ENT = {'nbsp':' ','amp':'&','lt':'<','gt':'>','quot':'"','apos':"'",'ntilde':'ñ'}

def unesc(s):
    return H.unescape(s)

def unnest(s, tags):
    """Убирает вложенные теги того же вида, оставляя внешнюю пару.

    У источника попадается `<strong><b>Суть тантры</b> (…)</strong>` и
    `<strong>… <strong>Глава</strong> …</strong>` — оба раза полужирным набран
    весь заголовок, а внутренняя пара ничего не добавляет. Схлопывать её надо
    до превращения тегов в `**`: иначе выходит `**A **B** C**`, markdown видит
    в этом не то, что имелось в виду, и оставляет звёздочки прямо на странице.
    """
    out, depth, pos = [], 0, 0
    for m in re.finditer(r'</?(?:%s)\b[^>]*>' % tags, s, re.I):
        closing = m.group(0)[1] == '/'
        outer = (depth == 1) if closing else (depth == 0)
        if not outer:
            out.append(s[pos:m.start()])
            pos = m.end()
        depth = max(0, depth - 1) if closing else depth + 1
    out.append(s[pos:])
    return ''.join(out)


def mark(s, tags, sign):
    """Тег выделения → знак markdown, а пробел из-под тега — наружу.

    У источника попадается `<i> (и число)</i>` и `<em>(подлинной) </em>`:
    пробел стоит внутри тега. Подставь знак на место тега как есть — и выйдет
    `_ (и число)_`, а это для markdown не курсив вовсе: за открывающим знаком
    сразу пробел. Подчёркивание осталось бы на странице голым.
    """
    s = re.sub(r'<(?:%s)\b[^>]*>([ \t\xa0]*)' % tags, r'\1' + sign, s, flags=re.I)
    return re.sub(r'([ \t\xa0]*)</(?:%s)\s*>' % tags, sign + r'\1', s, flags=re.I)


def strip_tags_keep(s):
    """Схлопывает разметку до текста, сохраняя санскрит в скобках как есть."""
    s = re.sub(r'<img[^>]*greenarrow[^>]*>', ' → ', s, flags=re.I)
    s = re.sub(r'<img[^>]*doublearrow[^>]*>', ' ↔ ', s, flags=re.I)
    s = re.sub(r'<img[^>]*>', '', s)
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', s, flags=re.S|re.I)
    # Курсив источника — это слова, добавленные переводчиком «для связности».
    s = mark(unnest(s, 'em|i'), 'em|i', '_')
    s = mark(unnest(s, 'strong|b'), 'strong|b', '**')
    s = re.sub(r'<span class="stylered">(.*?)</span>', r'\1', s, flags=re.S)
    s = re.sub(r'<span class="stylegreen">(.*?)</span>', r'\1', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    s = unesc(s)
    s = re.sub(r'__', '', s)          # пустой курсив от смежных тегов
    s = re.sub(r'\*\*\*\*', '', s)
    s = re.sub(r'[ \t\xa0]+', ' ', s)
    s = re.sub(r' *\n *', '\n', s)
    s = re.sub(r'\n{2,}', '\n', s)   # <br /> и перевод строки за ним — один разрыв
    return s.strip()

DEVA = re.compile(r'[ऀ-ॿ]')
CYR  = re.compile(r'[А-Яа-яЁё]')
# Буквы, которые встречаются только в IAST-транслитерации.
DIAC = re.compile(r'[āīūṛṝḷḹṭḍṇśṣñṅṁṃḥĀĪŪṚṬḌṆŚṢÑṄṀṂḤ]')
ENGWORD = re.compile(r'\b(the|of|is|and|to|in|that|this|which|not|by|with|from|as|it|its|be|are|was|for|on|his|her|their|because|when|so|also|but|there|here|has|have|all|one|who|what|such|even|only|now|then|i|you|we|they|he|she)\b', re.I)

def kind_of(cls, text, raw):
    if DEVA.search(text):
        return 'deva-red' if 'green' not in cls else 'deva'
    # Кириллица — это перевод, и решается это до всякой диакритики. У Габриэля
    # в переводе при каждом русском слове стоит санскритское в скобке, так что
    # диакритики в переведённом абзаце не меньше, чем в самой транслитерации, а
    # английских служебных слов нет вовсе: без этой проверки перевод целиком
    # уходил бы в IAST. У Parātrīśikāvivaraṇa вопрос не вставал — там текст
    # приходит по-английски, — у «Тантрасары» он и есть весь текст страницы.
    if CYR.search(text):
        return 'text'
    letters = re.sub(r'[^A-Za-zÀ-ɏḀ-ỿ]', '', text)
    if not letters:
        return 'plain'
    # IAST-блок узнаётся по плотности диакритики и по отсутствию английской
    # служебной речи. Одно совпадение прощаем: в санскрите сплошь и рядом
    # попадается кусок, который выглядит английским служебным словом, — «he
    # prabho» («о Господь») даёт «he», «sa eva» даёт «sa». В переводе же таких
    # слов не одно и не два, так что спутать его с IAST нельзя.
    eng = len(ENGWORD.findall(text))
    dia = len(DIAC.findall(text))
    if dia and eng <= 1 and re.search(r'\|\||॥|\|', text):
        return 'iast'
    if dia and eng <= 1 and dia * 25 > len(letters):
        return 'iast'
    return 'text'

def parse(path):
    s = open(path, encoding='utf-8').read()
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<(script|style|noscript)\b.*?</\1>', '', s, flags=re.S|re.I)

    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, flags=re.S)
    title = strip_tags_keep(h1.group(1)) if h1 else path

    start = s.find('</h1>')
    # Внутреннее оглавление страницы нам не нужно — своё построим сами.
    # Искать его надо после <h1>: до заголовка стоит такая же таблица со
    # ссылкой на шрифты.
    toc = s.find('<table class="pagelinks"', start)
    tocend = s.find('</table>', toc) if toc > 0 else -1
    if tocend > 0:
        start = tocend + len('</table>')
    end = s.find('<table class="artnav"')
    if end < 0:
        end = len(s)
    body = s[start:end]

    # Блок «Дополнительная информация» — это подпись автора, а не текст
    # трактата. Якорь у него на каждой странице свой («FurtherInfo…»,
    # «FurtherTantrasaara7»), общее в нём — только начало.
    fi = re.search(r'<h3><a id="Further[^"]*">.*?</h3>', body, flags=re.S)
    if fi:
        body = body[:fi.start()]

    blocks = []
    for m in re.finditer(
            r'<(h3|h4|p|div|table|ol|ul|hr)\b([^>]*)>(.*?)</\1>|<hr\b([^>]*)/?>',
            body, flags=re.S|re.I):
        tag = (m.group(1) or 'hr').lower()
        attrs = m.group(2) or m.group(4) or ''
        inner = m.group(3) or ''
        cls = (re.search(r'class="([^"]*)"', attrs) or re.match('','')).group(1) if re.search(r'class="([^"]*)"', attrs) else ''

        if tag == 'hr':
            if 'short' in cls:
                blocks.append({'k': 'rule'})
            continue
        if tag in ('h3', 'h4'):
            t = strip_tags_keep(inner)
            if t:
                blocks.append({'k': tag, 't': t})
            continue
        if tag == 'table':
            blocks.append({'k': 'table', 'html': inner.strip()})
            continue
        if tag in ('ol', 'ul'):
            items = [strip_tags_keep(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', inner, flags=re.S)]
            items = [i for i in items if i]
            if items:
                blocks.append({'k': 'list', 'ordered': tag == 'ol', 'items': items})
            continue

        t = strip_tags_keep(inner)
        if not t or t.lower() in ('top', 'вверх', 'в начало'):
            continue
        k = kind_of(cls, t, inner)
        if k == 'plain':
            continue
        centered = 'alignmentcentered' in cls
        blocks.append({'k': k, 't': t, 'c': centered})

    return {'title': title, 'blocks': blocks}


def convert(here, ids, prefix):
    """Разбирает src/<prefix><id>.html в blocks/<id>.json и печатает состав."""
    import os
    from collections import Counter
    os.makedirs(os.path.join(here, 'blocks'), exist_ok=True)
    for pid in ids:
        out = parse(os.path.join(here, 'src', '%s%s.html' % (prefix, pid)))
        json.dump(out, open(os.path.join(here, 'blocks', '%s.json' % pid), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('%s: блоков %d %s' % (pid, len(out['blocks']), Counter(b['k'] for b in out['blocks'])))
