#!/usr/bin/env python3
"""Режет страницу разбора на части и забирает готовый русский перевод сутр.

    python3 convert.py      # src/*.html -> blocks/N.json и sutras.json

**Части режутся не по файлам.** Весь разбор Кшемараджи лежит у источника одной
страницей, разделённой заголовками «Aphorism N». Поэтому разбор здесь один, а
файлов блоков из него выходит двадцать один: «Beginning» — вступительные
строфы — и двадцать афоризмов.

Три заголовка в части не идут вовсе:

* `Introduction` — приветствие Габриэля Pradīpaka. Оно про писание в целом, и
  место ему одно, на [/ksh/ph/](../../ksh/ph/index.md), а не на каждой из
  двадцати одной страницы;
* `Further information` и `Post your comment` — подпись автора и подвал сайта.
  Общий разбор срезает их по якорю `FurtherInfo…`, но на этой странице якорь
  назван иначе, и срезаются они здесь по имени.

**Перевод самих сутр не делается.** Двадцать сутр по-русски у источника уже
есть, отдельной страницей (узел 541), и берутся они оттуда: тот же переводчик,
то же прочтение, уже выложенное. Здесь переводится разбор — то, чего по-русски
нет нигде.

Сноски при сутрах при этом снимаются. На странице сутр Габриэль поясняет
сноской отдельные слова («**1** Здесь термин „siddhi“ означает не…»), но сами
сноски стоят там отдельными абзацами, которых в разборе нет. Пометка, ведущая
в никуда, хуже её отсутствия; за пояснением идти к нему, и ссылка на его
страницу стоит на каждой странице.

## Что здесь приходится править

Вёрстка у этой страницы та же, что у соседей, но три вещи разбор общий берёт
иначе, чем нужно, — и каждая ломает складывание стен молча:

1. **Стены кончаются не первой чертой, а последней.** У двадцатого афоризма
   после первой черты стоит колофон — «сие Pratyabhijñāhṛdayam закончено», —
   и стены на нём не кончаются, а продолжаются. Границей взята последняя
   черта; черты внутри стен убираются, иначе `pairing` обрывает складывание
   на них.
2. **Письменность вернее класса.** «iti||5||» — транслитерация, но латиницей
   без диакритики, и общий разбор зовёт это переводом; «Accordingly (tathā
   ca) —» — наоборот, перевод, но с диакритикой внутри, и разбор зовёт это
   транслитерацией. Поэтому до черты вид блока ставится по письменности, а
   после черты всё — перевод.
3. **Сутра — красным, разбор — зелёным.** У источника цвет здесь стоит как
   придётся: в пятом афоризме красным набрано всё, в первом — почти ничего.
   Красной делается первая строфа, кончающаяся номером афоризма — «॥१३॥», —
   и она же сличается с сутрой со страницы 541. Две страницы источника
   расходятся в чтении дважды, и `convert.py` про это говорит вслух:
   у 13-й сутры `चेतनापद` против `चेतनपद`, у 18-й `वाहच्छेदद्यन्त` против
   `वाहच्छेदाद्यन्त`. Разночтение источника — не наше дело поправлять, но
   молчать о нём тоже нельзя. `check.py` смотрит, что красная строфа в
   каждой части одна.

Отдельно: у первого афоризма транслитерация вступительного абзаца повторена —
у источника он стоит дважды, в «Beginning» и здесь, причём в двух разных
чтениях (`śaktipātavaśonmiṣat` и `śaktipātonmiṣita`). Деванагари при этом
одно, и стены расходились на один блок. Повтор убирается.
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.parse import parse, DEVA
from parts import APHORISMS

APHORISM = re.compile(r'^Aphorism (\d+)$')
BEGINNING = 'Beginning'
DROP = ('Introduction', 'Further information', 'Post your comment')

# Номер сутры в конце её перевода: «||1||». По нему перевод сутры и узнаётся —
# и на странице сутр, и в самом разборе, где он стоит таким же абзацем.
NUM = re.compile(r'\|\|(\d+)\|\|\s*$')

# Пометка сноски: «**1**». Полужирный к этому моменту уже стал звёздочками.
NOTE = re.compile(r'\*\*\d+\*\*')

# Вступительный абзац, повторённый у первого афоризма. Сличается по началу:
# чтения у двух его копий разные, и совпадения знак в знак не будет.
REPEAT = "Iha ye sukumāramatayo'kṛta"

DIGITS = '०१२३४५६७८९'


def numeral(n):
    """Число индийскими цифрами: 13 -> «१३»."""
    return ''.join(DIGITS[int(c)] for c in str(n))


def cut(bs):
    """Блоки разбора -> {номер части: её блоки}, заголовок первым.

    Заголовок остаётся, хотя на странице его и не будет: сборка вешает на него
    якоря — «сразу на перевод», — а рисовать его незачем, часть на странице
    одна и название у страницы уже есть. Так же сделано у «Тантрасары»: блок
    стоит, а `heading()` возвращает пустую строку.
    """
    out, cur = {}, None
    for b in bs:
        if b['k'] in ('h3', 'h4'):
            t = b.get('t', '')
            m = APHORISM.match(t)
            if m:
                cur = out.setdefault(int(m.group(1)), [b])
            elif t == BEGINNING:
                cur = out.setdefault(0, [b])
            elif t in DROP:
                cur = None
            else:
                raise SystemExit('незнакомый заголовок: %r' % t)
            continue
        if cur is not None:
            cur.append(b)
    return out


def normalise(bs, n, red):
    """Стены отдельно, перевод отдельно; вид блока — по письменности.

    `red` — деванагари сутры этой части, как оно стоит на странице сутр.
    Красной делается первая строфа, кончающаяся «॥N॥»; с `red` она сличается
    только затем, чтобы сказать о расхождении, а не чтобы выбрать её.
    """
    head, bs = bs[:1], bs[1:]
    rules = [i for i, b in enumerate(bs) if b['k'] == 'rule']
    edge = rules[-1] if rules else len(bs)
    end = '॥%s॥' % numeral(n)

    wall, marked = [], False
    for b in bs[:edge]:
        if b['k'] == 'rule':
            continue
        t = b.get('t', '')
        if not DEVA.search(t):
            if n == 1 and t.startswith(REPEAT):
                continue
            wall.append(dict(b, k='iast'))
            continue
        first = t.strip()
        if not marked and n and first.endswith(end):
            marked = True
            if red and first != red:
                print('  %2d: сутра у источника в двух чтениях' % n)
                print('      страница сутр: %s' % red)
                print('      разбор:        %s' % first)
            wall.append(dict(b, k='deva-red'))
        else:
            wall.append(dict(b, k='deva'))

    unwrap(wall, n)
    tr = [dict(b, k='text') for b in bs[edge + 1:]]
    return head + wall + ([{'k': 'rule', 't': ''}] if tr else []) + tr


def unwrap(wall, n):
    """Перенос строки внутри транслитерации, которого нет в деванагари.

    Строфа складывается со своей транслитерацией построчно, и строк у них
    обязано быть поровну. У двадцатой сутры их не поровну: транслитерация
    длинная, и у источника она перенесена вручную посередине — там, где в
    деванагари над ней стоит пробел. Это перенос, а не строка стиха, и он
    убирается; строку стиха так не тронешь, потому что деванагари над ней
    перенесена тоже.
    """
    sa = [b for b in wall if b['k'] in ('deva', 'deva-red')]
    ia = [b for b in wall if b['k'] == 'iast']
    for d, i in zip(sa, ia):
        if d['t'].count('\n') == 0 and '\n' in i['t']:
            print('  %2d: перенос внутри транслитерации убран (%s…)'
                  % (n, i['t'][:40]))
            i['t'] = i['t'].replace('\n', ' ')


def sutras(path):
    """Сутры со страницы 541: {номер: (деванагари, готовый русский перевод)}.

    Строфа и её транслитерация стоят там одним абзацем; деванагари — первая
    его строка. Оно и служит приметой, по которой сутра узнаётся в разборе.
    """
    deva, ru = {}, {}
    for b in parse(path)['blocks']:
        t = b.get('t', '')
        if b['k'] == 'text':
            m = NUM.search(t)
            if m:
                ru[int(m.group(1))] = NOTE.sub('', t).replace('  ', ' ')
        elif DEVA.search(t):
            first = t.split('\n')[0].strip()
            m = NUM.search(t)
            if m:
                deva[int(m.group(1))] = first
    missing = [n for n in range(1, 21) if n not in ru or n not in deva]
    if missing:
        raise SystemExit('на странице сутр не нашлось: %s' % missing)
    return {n: (deva[n], ru[n]) for n in ru}


def convert():
    page = parse(os.path.join(HERE, 'src', 'en543.html'))
    os.makedirs(os.path.join(HERE, 'blocks'), exist_ok=True)
    got = cut(page['blocks'])

    su = sutras(os.path.join(HERE, 'src', 'ru541.html'))
    json.dump({str(n): ru for n, (_d, ru) in su.items()},
              open(os.path.join(HERE, 'sutras.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1, sort_keys=True)
    print('сутр по-русски у источника: %d' % len(su))

    total = 0
    for n, name, _about in APHORISMS:
        bs = normalise(got.get(n, []), n, su.get(n, ('', ''))[0])
        en = sum(len(b['t']) for b in bs if b['k'] == 'text')
        total += en
        json.dump({'title': name, 'blocks': bs},
                  open(os.path.join(HERE, 'blocks', '%d.json' % n), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('%2d %-11s блоков %3d, английского %6d знаков  %s'
              % (n, name, len(bs), en, Counter(b['k'] for b in bs)))
    print('английского всего: %d знаков' % total)


if __name__ == '__main__':
    convert()
