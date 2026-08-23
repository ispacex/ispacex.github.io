#!/usr/bin/env python3
"""Разбирает страницу sanskrit-trikashaivism.com в список блоков.

Вёрстка источника держится на классах, а не на структуре, поэтому вид блока
определяется классом абзаца и письменностью внутри:

  unicodesfontgreen + lang=sa  — деванагари комментария Абхинавагупты
  unicodesfont*   (без green)  — деванагари исходных строф Шивы/Шакти
  alignmentcentered            — либо IAST, либо перевод: решает письменность
  stylered / stylegreen        — санскритское слово в скобках внутри перевода
"""
import re, json, sys, html as H

ENT = {'nbsp':' ','amp':'&','lt':'<','gt':'>','quot':'"','apos':"'",'ntilde':'ñ'}

def unesc(s):
    return H.unescape(s)

def strip_tags_keep(s):
    """Схлопывает разметку до текста, сохраняя санскрит в скобках как есть."""
    s = re.sub(r'<img[^>]*greenarrow[^>]*>', ' → ', s, flags=re.I)
    s = re.sub(r'<img[^>]*doublearrow[^>]*>', ' ↔ ', s, flags=re.I)
    s = re.sub(r'<img[^>]*>', '', s)
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', s, flags=re.S|re.I)
    # Курсив источника — это слова, добавленные переводчиком «для связности».
    s = re.sub(r'</?(em|i)\b[^>]*>', '_', s, flags=re.I)
    s = re.sub(r'</?(strong|b)\b[^>]*>', '**', s, flags=re.I)
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
    letters = re.sub(r'[^A-Za-zÀ-ɏḀ-ỿ]', '', text)
    if not letters:
        return 'plain'
    # IAST-блок: диакритики много, английских служебных слов нет, есть || или |
    eng = len(ENGWORD.findall(text))
    dia = len(DIAC.findall(text))
    if dia and eng == 0 and re.search(r'\|\||॥|\|', text):
        return 'iast'
    if dia and eng == 0 and dia * 40 > len(letters):
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

    # Блок «Further Information» — это подпись автора, а не текст трактата.
    fi = re.search(r'<h3><a id="FurtherInfo[^"]*">.*?</h3>', body, flags=re.S)
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
        if not t or t.lower() in ('top', 'вверх'):
            continue
        k = kind_of(cls, t, inner)
        if k == 'plain':
            continue
        centered = 'alignmentcentered' in cls
        blocks.append({'k': k, 't': t, 'c': centered})

    return {'title': title, 'blocks': blocks}

if __name__ == '__main__':
    import os
    from collections import Counter
    from parts import PARTS

    HERE = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(HERE, 'blocks'), exist_ok=True)
    ids = sys.argv[1:] or ['540'] + [p[0] for p in PARTS]
    for pid in ids:
        out = parse(os.path.join(HERE, 'src', 'pv%s.html' % pid))
        json.dump(out, open(os.path.join(HERE, 'blocks', '%s.json' % pid), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('%s: блоков %d %s' % (pid, len(out['blocks']), Counter(b['k'] for b in out['blocks']))) 
