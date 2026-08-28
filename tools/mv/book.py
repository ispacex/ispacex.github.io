#!/usr/bin/env python3
"""Чем Mālinīvijayottaratantra отличается от прочих писаний источника.

Отличие одно, и оно делит писание надвое. **Изложение написано не ко всему
тексту.** Санскрит у источника выложен целиком — все 23 главы, 1282,5 строфы,
деванагари и транслитерация, — а английское изложение есть только к главам
1–4, а это 219 строф. Под остальными стоит «Untranslated yet», и таких пометок
1062: то же, что у [Śivastotrāvalī](../sv/README.md), только там неизложенного
444 строфы из 450.

Отсюда у главы два вида, и страница у них разная не оттого, что так задумано,
а оттого, что у источника разное:

* **главы 1–4** — строфа, её транслитерация, перевод строфы слово в слово и
  пояснения Габриэля Pradīpaka. Всё это переведено здесь, с его английского,
  и лежит в `ru/<глава>.json`;
* **главы 5–23** — строфа и транслитерация, и больше ничего. Место под перевод
  остаётся пустым (блок `gap`), и страница честно говорит об этом вверху.

Переводить эти главы прямо с санскрита, как сделано у Śivastotrāvalī, здесь не
взялись, и причина не в объёме: гимн Утпаладевы — стихи о любви к Богу, и
ошибка в них остаётся ошибкой в стихах, а главы 5–23 этой тантры — обряд,
посвящение и йога, где строфа предписывает действие. Изложения, на которое
можно опереться, для них нет ни английского, ни русского, и перевод без него
был бы догадкой, выданной за наставление.

Ключ перевода — «номер строфы/номер абзаца под нею»: см. `convert.py`.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

import words
from common.page import Book, plural
from convert import key
from parts import PARTS, SRC, SRC_URL, INTRO

GLOSSARY = '/ksh/mv/glossary/'

# Заголовки источника внутри главы. Первый — «Chapter 7», и стоит он не над
# главой (её название есть у страницы), а над первым десятком строф; остальные
# называют свой десяток сами.
CHAPTER = re.compile(r'^Chapter (\d+)$')
STANZAS = re.compile(r'^Stanzas ([\d.]+) to ([\d.]+)$')


def load_json(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}


def stanzas(a, b):
    return 'Строфы %s–%s' % (a, b)


class MV(Book):
    key = 'mv'
    name = 'Mālinīvijayottaratantra'
    parts = PARTS
    src = SRC
    src_url = SRC_URL
    home_name = 'Оглавление'

    def __init__(self, here=HERE):
        Book.__init__(self, here)
        self.cache = {}
        self.tr = {}
        self.words = words.index()

    # --- словарь ---

    def link(self, word):
        """Санскритское слово в подстрочнике — ссылка на статью словаря.

        Слово стоит в падеже, и статью ему подбирает `words.find`. Чего в
        словаре нет — остаётся простым текстом: сто с небольшим статей на 3406
        помет, и большая часть помет — связки вроде `ca` и `api`.
        """
        term = words.find(word, self.words)
        return GLOSSARY + '#t-' + words.keyof(term) if term else None

    def crumbs(self):
        return ' · [Словарь терминов](%s)' % GLOSSARY

    # --- блоки и перевод ---

    def blocks(self, pid):
        if pid not in self.cache:
            self.cache[pid] = Book.blocks(self, pid)
        return self.cache[pid]

    def _tr(self, pid):
        if pid not in self.tr:
            self.tr[pid] = load_json(os.path.join(self.here, 'ru', '%s.json' % pid))
        return self.tr[pid]

    def heads(self, pid):
        """Заголовки внутри главы, по-русски: {номер блока: название}.

        Переводить их через `ru/*.json` было бы двадцатью тремя списками
        одинаковых строк: заголовок у источника всегда «Stanzas A to B». Первый
        же заголовок называется «Chapter N» и своих строф не называет вовсе —
        их видно по следующему заголовку.
        """
        bs = self.blocks(pid)
        out, first = {}, None
        for i, b in enumerate(bs):
            if b['k'] not in ('h3', 'h4'):
                continue
            m = STANZAS.match(b.get('t', ''))
            if m:
                out[i] = stanzas(*m.groups())
                if first is not None and first not in out:
                    out[first] = stanzas('1', str(int(float(m.group(1))) - 1))
                continue
            if CHAPTER.match(b.get('t', '')) and first is None:
                first = i
        if first is not None and first not in out:
            # Глава без второго заголовка: строфы в ней все до последней.
            last = [b['n'] for b in bs if b.get('n', '').isdigit()]
            out[first] = stanzas('1', last[-1]) if last else 'Строфы'
        return out

    def load(self, pid):
        ru, heads = self._tr(pid), self.heads(pid)
        def lookup(i, b):
            if b['k'] in ('h3', 'h4'):
                return heads.get(i)
            return ru.get(key(b))
        return lookup

    def item(self, pid, i, j, text):
        """Перевод j-го пункта списка: ключ блока, а за ним номер пункта."""
        k = key(self.blocks(pid)[i])
        return self._tr(pid).get('%s/%d' % (k, j + 1)) if k else None

    def table(self, pid, i, html):
        """Готовая таблица целиком: у неё своя вёрстка, и разбирать её нечего.

        Таблицы источника — карты соответствий: тридцать шесть таттв, пятьдесят
        Рудр, буквы Mālinī по частям тела. Перевод такой карты — это её же
        вёрстка с русскими подписями, поэтому в `ru/*.json` она и лежит целиком.
        """
        k = key(self.blocks(pid)[i])
        return self._tr(pid).get('%s/html' % k) if k else None

    def page_title(self, name):
        # Строчными название главы писать нельзя целиком: половина названий
        # санскритские, и «bhuvanādhvādhikāraḥ» — это уже другое слово.
        return '%s: %s' % (self.name, name[:1].lower() + name[1:])

    # --- строфы ---

    def pairing(self, blocks):
        """Кнопки копирования — одни на главу, а не над каждой строфой.

        Строфа и её транслитерация стоят здесь в одном абзаце источника и
        разведены надвое при разборе, поэтому стен на странице выходит не одна,
        а по одной на строфу — сто тридцать семь в восьмой главе. Кнопки над
        каждой были бы издевательством; глава же копируется целиком, и это как
        раз то, за чем на страницу приходят. Так же сделано у Śivastotrāvalī.
        """
        pair, eaten, opens, group = Book.pairing(self, blocks)
        if not opens:
            return pair, eaten, opens, group
        return pair, eaten, {min(opens): 'w1'}, {i: 'w1' for i in group}

    def verse_id(self, pid, block):
        """Якорь строфы — её номер: /ksh/mv/ch1/#v21.

        Строфу этой тантры зовут по главе и номеру: «Mālinīvijayottara 1.21»
        приводит и «Тантралока», и сам Абхинавагупта, объявивший её своим
        главным основанием. Глава — это страница, номер — якорь на ней.
        """
        n = block.get('n')
        return 'v%s' % n if n and n.isdigit() else None

    # --- что на странице чьё ---

    def done(self, pid):
        """(строф в главе, абзацев перевода) — по чему считается вид главы."""
        bs = self.blocks(pid)
        return (sum(1 for b in bs if b.get('n', '').isdigit()
                    and b['k'] in ('deva', 'deva-red')),
                len(self._tr(pid)))

    def todo(self, pid, n):
        """Предупреждение вверху страницы, и оно здесь двух родов.

        В главах 1–4 без перевода стоит английский абзац Габриэля Pradīpaka:
        изложение есть, а мы до него ещё не дошли. В главах 5–23 стоять там
        нечему — изложения нет и у него, — и обещать перевод, которому неоткуда
        взяться, нельзя. Отличаются они по тому, что в блоке: `gap` — пустое
        место под строфой, `text` — английский абзац.
        """
        blank = sum(1 for b in self.blocks(pid) if b['k'] == 'gap')
        if blank >= n:
            return ('<p class="pv-todo">Перевода у этой главы нет. У источника под'
                    ' каждой из %d строф стоит пометка «Untranslated yet»: английского'
                    ' изложения для этой главы он не написал, а переводить обрядовые'
                    ' предписания прямо с санскрита, без опоры, значило бы выдать'
                    ' догадку за наставление. Санскрит и транслитерация на месте, и'
                    ' страница ждёт перевода.</p>' % blank)
        return ('<p class="pv-todo">Эта глава переведена ещё не полностью: %d %s ниже'
                ' стоят по-английски — так, как они у источника. Санскрит и'
                ' транслитерация на месте.</p>'
                % (n, plural(n, 'абзац', 'абзаца', 'абзацев')))

    def footer(self, pid, name):
        at = ('*Санскрит (деванагари и IAST) перенесён без изменений с сайта'
              ' **Габриэля Pradīpaka**: [%s](%s).' % (name, self.at_source(pid)))
        if self._tr(pid):
            return at + (' Перевод сделан здесь, по его английскому изложению:'
                         ' по-русски этой тантры нет нигде.*')
        return at + (' Английского изложения для этой главы у него нет — под каждой'
                     ' строфой стоит пометка «Untranslated yet», — поэтому нет и'
                     ' перевода: переводить не с чего, а строить догадки о том, что'
                     ' предписывает обряд, хуже, чем не переводить вовсе.*')
