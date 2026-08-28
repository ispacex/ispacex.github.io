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
«Untranslated». Сам текст пометки в блоки не идёт — показывать её на странице
нечего, — но место под ней остаётся: блок вида `gap`, пустой и помеченный
номером своей строфы. Пустым он молчит, а перевод, сделанный прямо с
санскрита, встаёт ровно сюда.

Номер строфы служит ключом и абзацам перевода, и местам под него: по номеру
строфу зовут, и от правки разбора такой ключ не съезжает, а порядковый номер
блока съехал бы весь.
"""
import json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.parse import parse, split
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


def numbered(b):
    """Строфу разводим надвое (см. `split`) и помечаем её номером.

    Само разведение — общее, `common/parse.py`: так же устроен и источник
    Mālinīvijayottaratantra. Номер же здесь свой — «13.11» в конце
    транслитерации, — и берётся он тут.
    """
    pair = split(b)
    if pair is None:
        return None
    sa, ia = pair
    num = NUM.search([l for l in ia['t'].split('\n') if l.strip()][-1])
    if num:
        sa['n'] = num.group(1)
    return sa, ia


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
        bs, gaps, kept, at = [], 0, 0, None
        for b in chapters.get(n, []):
            pair = numbered(b) if b['k'] in ('deva', 'deva-red') else None
            if pair:
                bs.extend(pair)
                kept += 1
                at = pair[0].get('n')
                continue
            # Абзац под строфой — место под её перевод, и помечается он номером
            # той строфы, а не своим номером в списке блоков: по номеру строфу
            # зовут, по нему же лежит перевод, и от правки разбора он не едет.
            if b['k'] == 'text' and GAP.match(b['t']):
                bs.append({'k': 'gap', 't': '', 'n': at})
                gaps += 1
                continue
            if b['k'] == 'text':
                b = dict(b, n=at)
            bs.append(b)
        whole += kept
        blind = kept - sum(1 for b in bs if b['k'] in ('deva', 'deva-red') and b.get('n'))
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
