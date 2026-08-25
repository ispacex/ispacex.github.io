#!/usr/bin/env python3
"""Чем Parātrīśikāvivaraṇa отличается от прочих писаний источника.

Санскрит (деванагари и IAST) переносится с sanskrit-trikashaivism.com как
есть. Русского текста у источника нет вовсе — там английский, — поэтому
перевод лежит здесь: `ru/<id>.json` по номеру блока и `ru/common.json` по
самому английскому тексту, для повторяющихся вставок вроде «Important:».
Блок, которому перевода ещё нет, страница показывает по-английски в рамке
`pv-en`: выдать английский за русский конвейер не может по построению.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

import words
from common.page import Book
from parts import PARTS, SRC, SRC_URL

GLOSSARY = '/ksh/pv/glossary/'


def load(path, default):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


class PV(Book):
    key = 'pv'
    name = 'Parātrīśikāvivaraṇa'
    parts = PARTS
    src = SRC
    src_url = SRC_URL

    def __init__(self, here=HERE):
        Book.__init__(self, here)
        self.common = load(os.path.join(here, 'ru', 'common.json'), {})
        self.ru = {}
        # Словарь и его якоря считаются один раз на всю сборку: обход перевода
        # ради каждой из четырнадцати страниц был бы четырнадцатью обходами.
        self.words = words.index()
        self.marks = words.anchors()

    def _ru(self, pid):
        if pid not in self.ru:
            self.ru[pid] = load(os.path.join(self.here, 'ru', '%s.json' % pid), {})
        return self.ru[pid]

    def load(self, pid):
        ru = self._ru(pid)
        def tr(i, b):
            return ru.get(str(i)) or self.common.get(b['t'])
        return tr

    def item(self, pid, i, j, text):
        return self._ru(pid).get('%d.%d' % (i, j))

    def table(self, pid, i, html):
        return self._ru(pid).get(str(i))

    def link(self, word):
        """Санскритское слово в подстрочнике — ссылка на статью словаря.

        Слово стоит в падеже, и статью ему подбирает `words.find`. Чего в
        словаре нет — остаётся простым текстом: сотня статей на без малого
        шесть тысяч помет, и большая их часть — служебные слова.
        """
        term = words.find(word, self.words)
        return GLOSSARY + '#t-' + words.slug(term.iast) if term else None

    def anchors(self, pid):
        return self.marks.get(pid, {})

    def crumbs(self):
        return ' · [Словарь терминов](%s)' % GLOSSARY

    def footer(self, pid, name):
        return ('*Перевод на русский сделан для этого сайта по английскому изложению Габриэля'
                ' Pradīpaka: [%s](%s). Санскрит (деванагари и IAST) перенесён из источника без изменений.*'
                % (name, self.at_source(pid)))
