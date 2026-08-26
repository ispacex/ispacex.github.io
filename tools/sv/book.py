#!/usr/bin/env python3
"""Чем Śivastotrāvalī отличается от прочих писаний источника.

Отличие одно, и оно определяет здесь всё: **переводить почти не с чего**.
Санскрит у источника выложен целиком — все 450 строф, деванагари и
транслитерация, — а английское изложение написано только для вступления и для
строф 1.1–1.6. Под остальными 444 стоит одно слово: «Untranslated».

Отсюда две родословные у перевода, и они не равны:

* `ru/<гимн>.json` — переведено **по английскому изложению** Габриэля
  Pradīpaka, как весь /ksh/pv/. Между санскритом и русским стоит его работа;
* `sa/<гимн>.json` — переведено **прямо с санскрита**, здесь. Изложения, на
  которое можно опереться, для этих строф нет вовсе, и сверить перевод не с
  чем: два полных английских перевода «Шивастотравали» существуют, но оба под
  копирайтом и в работу не брались.

Смешивать их молча нельзя: читатель вправе знать, чью работу он читает.
Поэтому подпись под страницей называет обе родословные поимённо, с номерами
строф, а `check.py` следит, чтобы одна и та же строфа не лежала в обеих папках.

Ключ в обеих — **номер строфы** («13.11»), а не номер блока: по номеру строфу
зовут, и от правки разбора такой ключ не съезжает.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

import words
from common.page import Book, SA_KINDS, plural
from parts import PARTS, SRC, SRC_URL

GLOSSARY = '/ksh/sv/glossary/'

# Откуда взялся перевод: папка и то, как это называется вслух.
FROM_EN, FROM_SA = 'ru', 'sa'


def load(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}


def ranges(nums):
    """[«1.1», «1.2», «1.3», «1.7»] -> «1.1–1.3, 1.7» — подпись читает человек."""
    def key(s):
        a, b = s.split('.')
        return int(a), int(b)
    out, run = [], []
    for s in sorted(nums, key=key):
        if run and key(s)[1] == key(run[-1])[1] + 1 and key(s)[0] == key(run[-1])[0]:
            run.append(s)
            continue
        if run:
            out.append(run)
        run = [s]
    if run:
        out.append(run)
    return ', '.join(r[0] if len(r) == 1 else '%s–%s' % (r[0], r[-1]) for r in out)


class SV(Book):
    key = 'sv'
    name = 'Śivastotrāvalī'
    parts = PARTS
    src = SRC
    src_url = SRC_URL
    home_name = 'Оглавление'

    def __init__(self, here=HERE):
        Book.__init__(self, here)
        self.tr = {}
        # Словарь считается один раз на всю сборку: обход перевода ради каждой
        # из двадцати страниц был бы двадцатью обходами.
        self.words = words.index()

    def _tr(self, pid):
        if pid not in self.tr:
            self.tr[pid] = {w: load(os.path.join(self.here, w, '%s.json' % pid))
                            for w in (FROM_EN, FROM_SA)}
        return self.tr[pid]

    def load(self, pid):
        en, sa = self._tr(pid)[FROM_EN], self._tr(pid)[FROM_SA]
        return lambda i, b: en.get(b.get('n')) or sa.get(b.get('n'))

    def page_title(self, name):
        # Названия гимнов санскритские, и строчными их писать нельзя:
        # «bhaktivilāsākhyaṁ stotram» вместо «Bhaktivilāsākhyaṁ stotram».
        return '%s: %s' % (self.name, name)

    # --- строфы ---

    def pairing(self, blocks):
        """Кнопки копирования — одни на гимн, а не над каждой строфой.

        У соседних писаний стена строф на странице одна: сперва весь санскрит
        раздела, потом вся транслитерация. Здесь строфа и её транслитерация
        стоят порознь у каждой строфы, и общий разбор видит на странице не
        одну стену, а двадцать шесть — по одной на строфу. Кнопки над каждой
        из них были бы издевательством; гимн же копируется целиком, и это как
        раз то, за чем на страницу приходят.
        """
        pair, eaten, opens, group = Book.pairing(self, blocks)
        if not opens:
            return pair, eaten, opens, group
        return pair, eaten, {min(opens): 'w1'}, {i: 'w1' for i in group}

    def verse_id(self, pid, block):
        """Якорь строфы — её номер: /ksh/sv/ch13/#v13.11.

        Строфу здесь зовут по номеру: «Шивастотравали 13.11» приводит целиком
        «Тантралока» 13.290. Номер лежит в блоке с разбора (см. `NUM` в
        convert.py).
        """
        n = block.get('n')
        return 'v%s' % n if n else None

    # --- словарь терминов ---

    def link(self, word):
        """Санскритское слово в подстрочнике — ссылка на статью словаря.

        Слово стоит в падеже, и статью ему подбирает `words.find`. Чего в
        словаре нет — остаётся простым текстом: восемьдесят две статьи на пять
        с лишним тысяч помет, и большая их часть — служебные слова.
        """
        term = words.find(word, self.words)
        return GLOSSARY + '#t-' + words.slug(term.iast) if term else None

    def crumbs(self):
        return ' · [Словарь терминов](%s)' % GLOSSARY

    # --- что на странице чьё ---

    def counts(self, pid):
        """(строф в гимне, переведено с изложения, переведено с санскрита)."""
        blocks = self.blocks(pid)
        at = {b['n'] for b in blocks if b['k'] in SA_KINDS and b.get('n')}
        tr = self._tr(pid)
        return (len(at),
                len(at & set(tr[FROM_EN])),
                len(at & set(tr[FROM_SA])))

    def todo(self, n):
        return ('<p class="pv-todo">Ещё без перевода %d %s. У источника под ними стоит'
                ' пометка «Untranslated»: английского изложения для них не написано, и'
                ' перевод сюда придёт прямо с санскрита. Санскрит и транслитерация на'
                ' месте.</p>' % (n, plural(n, 'строфа', 'строфы', 'строф')))

    def footer(self, pid, name):
        tr = self._tr(pid)
        at = ['*Санскрит (деванагари и IAST) перенесён без изменений с сайта'
              ' **Габриэля Pradīpaka**: [%s](%s).' % (name, self.at_source(pid))]
        if tr[FROM_EN]:
            at.append(' Строфы %s переведены по его английскому изложению.'
                      % ranges(tr[FROM_EN]))
        if tr[FROM_SA]:
            at.append(' Строфы %s переведены прямо с санскрита, для этого сайта:'
                      ' изложения, на которое можно было бы опереться, для них у'
                      ' источника нет.' % ranges(tr[FROM_SA]))
        at.append('*')
        return ''.join(at)
