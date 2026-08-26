#!/usr/bin/env python3
"""Режет одну страницу источника на двадцать гимнов -> blocks/<номер>.json.

От соседних конвейеров этот отличается тремя вещами, и все три идут от того,
как выложено писание.

**Части режутся не по файлам.** Все двадцать гимнов лежат у источника одной
страницей, разделённые заголовками «Chapter N». Поэтому разбор здесь один, а
файлов блоков из него выходит двадцать. Сам заголовок в блоки не идёт: гимн
на странице один, и название у неё уже есть — второй такой же заголовок под
первым читался бы как сбой вёрстки.

**Строфа и её транслитерация стоят в одном абзаце**: две строки деванагари, под
ними те же две строки IAST. В Parātrīśikāvivaraṇa они стоят двумя стенами —
сперва весь санскрит раздела, потом вся транслитерация, — и `pairing` в
common/page.py складывает стены построчно. Здесь складывать нечего, наоборот:
абзац надо развести надвое, чтобы тот же `pairing` собрал его обратно уже
построчно, а не двумя блоками подряд.

**Перевода у источника почти нет.** Под 444 строфами из 450 стоит одно слово —
«Untranslated». Это пометка, а не текст писания, и в блоки она не идёт: абзац
с ней выбрасывается здесь. Сколько строф в гимне осталось без перевода,
страница считает сама — по числу переводов при её строфах (см. `head_note` в
book.py).
"""
import json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.parse import parse, DEVA
from parts import HYMNS

CHAPTER = re.compile(r'^Chapter (\d+) - ')
# Пометка источника «строфа ещё не изложена по-английски». Полужирный к этому
# моменту уже стал звёздочками markdown.
GAP = re.compile(r'^\*\*Untranslated\*\*$')

# Номер строфы в конце её транслитерации: «||13.11||». Берётся отсюда, а не из
# деванагари над ним, где он набран индийскими цифрами: «॥१३.११॥». По этому
# номеру строфу зовут — «Шивастотравали 13.11» стоит и в «Тантралоке», и у
# самого Абхинавагупты, — и по нему же на неё ставится якорь.
NUM = re.compile(r'\|\|(\d+\.\d+)\|\|\s*$')


def split(b):
    """Абзац источника — строфа вместе с её транслитерацией; разводим надвое.

    Разводим только то, что сошлось: строки деванагари должны идти подряд и
    первыми, а числом совпадать со строками латиницы. Абзац, устроенный иначе,
    остаётся как был — он сам скажет о себе на странице, а тихо разъехавшаяся
    строфа не скажет ничего.
    """
    ls = [l for l in b['t'].split('\n') if l.strip()]
    flags = ''.join('D' if DEVA.search(l) else 'i' for l in ls)
    n = len(ls) // 2
    if not re.fullmatch('D+i+', flags) or flags.count('D') != n:
        return None
    sa = {'k': b['k'], 't': '\n'.join(ls[:n]), 'c': b.get('c', False)}
    num = NUM.search(ls[-1])
    if num:
        sa['n'] = num.group(1)
    return sa, {'k': 'iast', 't': '\n'.join(ls[n:]), 'c': b.get('c', False)}


def cut(bs):
    """Блоки разбора -> {номер гимна: его блоки}. Вступление сюда не идёт.

    Вступление переводчика переведено один раз на /ksh/sv/, откуда оно и
    взято: двадцати страницам оно ни к чему, а в поисковом указателе двадцать
    раз лежать не должно.
    """
    out, cur = {}, None
    for b in bs:
        if b['k'] in ('h3', 'h4'):
            m = CHAPTER.match(b.get('t', ''))
            cur = out.setdefault(int(m.group(1)), []) if m else None
            continue
        if cur is not None:
            cur.append(b)
    return out


def convert():
    page = parse(os.path.join(HERE, 'src', 'sv1005.html'))
    os.makedirs(os.path.join(HERE, 'blocks'), exist_ok=True)
    chapters = cut(page['blocks'])
    whole = 0
    for n, name, _, _ in HYMNS:
        bs, gaps, kept = [], 0, 0
        for b in chapters.get(n, []):
            if b['k'] == 'text' and GAP.match(b['t']):
                gaps += 1
                continue
            pair = split(b) if b['k'] in ('deva', 'deva-red') else None
            if pair:
                bs.extend(pair)
                kept += 1
            else:
                bs.append(b)
        whole += kept
        blind = kept - sum(1 for b in bs if b.get('n'))
        if blind:
            print('%2d: строф без номера: %d' % (n, blind))
        json.dump({'title': name, 'blocks': bs},
                  open(os.path.join(HERE, 'blocks', '%d.json' % n), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('%2d: строф %3d, без перевода у источника %3d, блоков %3d %s'
              % (n, kept, gaps, len(bs), Counter(b['k'] for b in bs)))
    print('строф разведено надвое: %d' % whole)


if __name__ == '__main__':
    convert()
