#!/usr/bin/env python3
"""Чем Śivastotrāvalī отличается от прочих писаний источника.

Отличие одно, и оно определяет здесь всё: **переводить почти не с чего**.
Санскрит у источника выложен целиком — все 450 строф, деванагари и
транслитерация, — а английское изложение написано только для вступления и для
первых шести строф первого гимна. Под остальными 444 стоит одно слово:
«Untranslated».

Поэтому конвейер тот же, что у Parātrīśikāvivaraṇa (перевод лежит здесь, в
`ru/*.json`, и доливается по частям), но страница обязана сказать о себе
правду сразу: перевода нет не потому, что до него не дошли руки здесь, а
потому, что его нет и у источника. Это и говорит `head_note`.

Пометка `pv-en`, которой Parātrīśikāvivaraṇa показывает ещё не переведённый
абзац, здесь не работает вовсе: показывать в рамке слово «Untranslated»
двадцать шесть раз подряд — не честность, а шум. Такие абзацы выброшены на
разборе (см. `convert.py`), и счёт им ведётся по строфам, у которых перевода
не оказалось.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import Book, SA_KINDS, plural
from parts import PARTS, SRC, SRC_URL


def load(path, default):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


class SV(Book):
    key = 'sv'
    name = 'Śivastotrāvalī'
    parts = PARTS
    src = SRC
    src_url = SRC_URL
    home_name = 'Оглавление'

    def __init__(self, here=HERE):
        Book.__init__(self, here)
        self.ru = {}

    def _ru(self, pid):
        if pid not in self.ru:
            self.ru[pid] = load(os.path.join(self.here, 'ru', '%s.json' % pid), {})
        return self.ru[pid]

    def load(self, pid):
        ru = self._ru(pid)
        return lambda i, b: ru.get(str(i))

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

        Строфу здесь зовут по номеру: «Шивастотравали 13.11» цитирует и
        «Тантралока», и сам Абхинавагупта в Parātrīśikāvivaraṇa. Номер лежит
        в блоке с разбора (см. `NUM` в convert.py).
        """
        n = block.get('n')
        return 'v%s' % n if n else None

    # --- чего на странице нет ---

    def counts(self, pid):
        """(строф в гимне, из них с русским переводом)."""
        blocks = self.blocks(pid)
        ru = self._ru(pid)
        sa = [i for i, b in enumerate(blocks) if b['k'] in SA_KINDS]
        return len(sa), sum(1 for i, b in enumerate(blocks)
                            if b['k'] == 'text' and ru.get(str(i)))

    def head_note(self, pid):
        total, done = self.counts(pid)
        if done >= total:
            return ''
        if not done:
            return ('<p class="pv-todo">Перевода здесь нет, и взять его неоткуда: под'
                    ' каждой строфой этого гимна у Габриэля Pradīpaka стоит пометка'
                    ' «Untranslated». Английского изложения, с которого здесь переводят,'
                    ' для него ещё не написано. Санскрит и транслитерация на месте.</p>')
        left = total - done
        return ('<p class="pv-todo">Переведены %d %s из %d — те, которые у источника'
                ' изложены по-английски. Под остальными %d стоит пометка «Untranslated»:'
                ' изложения для них ещё не написано, и перевода здесь не будет, пока оно'
                ' не появится. Санскрит и транслитерация на месте.</p>'
                % (done, plural(done, 'строфа', 'строфы', 'строф'), total, left))

    def footer(self, pid, name):
        _, done = self.counts(pid)
        made = ('' if not done else
                ' Перевод тех строф, у которых он здесь есть, сделан для этого сайта'
                ' по его английскому изложению.')
        return ('*Санскрит (деванагари и IAST) перенесён без изменений с сайта'
                ' **Габриэля Pradīpaka**: [%s](%s).%s За точным смыслом идите в источник.*'
                % (name, self.at_source(pid), made))
