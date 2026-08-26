#!/usr/bin/env python3
"""Чем Pratyabhijñāhṛdayam отличается от прочих писаний источника.

Отличается оно тем, что перевод на страницу приходит **из двух рук**, и обе
надо назвать.

* **Двадцать сутр** по-русски у Габриэля Pradīpaka уже есть — отдельной
  страницей, без разбора. Переводить их заново значило бы разойтись с ним на
  ровном месте, поэтому они берутся готовыми (`sutras.json`);
* **разбор Кшемараджи** по-русски нет нигде: у источника он выложен только
  по-английски. Он переведён здесь и лежит в `ru/<часть>.json` по номеру
  блока.

Смешать эти два в одну строку страница не может: сутра стоит своим абзацем и
подписана, чей перевод. Абзац, которому перевода ещё нет, показывается
по-английски в рамке `pv-en` — выдать английский за русский конвейер не умеет
по построению.

Санскрит (деванагари и IAST) перенесён из источника как есть.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import Book, pairing, plural
from parts import PARTS, SRC, SRC_URL, SUTRAS, SUTRAS_PAGE

GLOSSARY = '/ksh/ph/glossary/'

# Номер в конце абзаца: «||13||». Так у источника кончается перевод сутры — но
# не только он: тем же номером закрывается и последний абзац разбора, а во
# вступительных строфах так же пронумерованы сами строфы. Поэтому одного этого
# признака мало, см. `sutra_at`.
NUM = re.compile(r'\|\|(\d+)\|\|\s*$')


def load(path, default):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


class PH(Book):
    key = 'ph'
    name = 'Pratyabhijñāhṛdayam'
    parts = PARTS
    src = SRC
    src_url = SRC_URL
    home_name = 'Оглавление'

    def __init__(self, here=HERE):
        Book.__init__(self, here)
        self.sutras = load(os.path.join(here, 'sutras.json'), {})
        self.ru = {}
        self._at = {}
        # Внутри, а не наверху модуля: `words` читает перевод, а перевод
        # приходит отсюда — встречный `import` наверху замкнул бы круг.
        import words
        self.words = words.index()
        self.marks = words.anchors()

    def link(self, word):
        """Санскритское слово в подстрочнике — ссылка на статью словаря.

        Слово стоит в падеже, и статью ему подбирает `words.find`. Чего в
        словаре нет — остаётся простым текстом: сто одиннадцать статей на две
        с небольшим тысячи помет, и добрая половина последних — служебные
        слова.
        """
        import words
        term = words.find(word, self.words)
        return GLOSSARY + '#t-' + words.keyof(term) if term else None

    def anchors(self, pid):
        return self.marks.get(pid, {})

    def crumbs(self):
        return ' · [Словарь терминов](%s)' % GLOSSARY

    def _ru(self, pid):
        if pid not in self.ru:
            self.ru[pid] = load(os.path.join(self.here, 'ru', '%s.json' % pid), {})
        return self.ru[pid]

    def load(self, pid):
        """Перевод абзаца: сутра — от источника, разбор — здешний.

        Сутра берётся со страницы сутр, и наш перевод для неё не спрашивается
        вовсе: одна и та же сутра не должна оказаться на сайте в двух
        прочтениях.
        """
        ru, at = self._ru(pid), self.sutra_at(pid)
        # Заголовок части у источника английский («Aphorism 2»), а название
        # части здесь уже есть — им он и переводится. Рисовать его всё равно
        # не будут (см. `heading`), но пометкой «не переведено» он быть не
        # должен: переведён он ровно настолько, насколько нужен.
        head = dict(zip((p[0] for p in PARTS), (p[2] for p in PARTS)))[pid]

        def tr(i, b):
            if b['k'] in ('h3', 'h4'):
                return head
            if i == at:
                return self.sutras[pid]
            return ru.get(str(i))
        return tr

    def sutra_at(self, pid):
        """Номер блока с переводом сутры этой части, или None.

        Номера в конце абзаца мало: тем же «||13||» источник закрывает и
        последний абзац разбора — так принято закрывать раздел, — а во
        вступительных строфах пронумерованы сами строфы. Поэтому берётся
        **первый** абзац, закрытый номером **этой** части: перевод сутры стоит
        сразу за переводом подводки к ней, до всякого разбора.
        """
        if pid not in self.sutras:
            return None
        if pid not in self._at:
            end = '||%s||' % pid
            self._at[pid] = next(
                (i for i, b in enumerate(self.blocks(pid))
                 if b['k'] == 'text' and b.get('t', '').rstrip().endswith(end)),
                None)
        return self._at[pid]

    def pairing(self, blocks):
        """Транслитерация узнаётся по виду блока, и только по нему.

        Общее правило вдобавок смотрит, нет ли в блоке скобки: скобка — верный
        признак перевода, потому что у Габриэля в скобке стоит санскритское
        слово при каждом русском. Здесь это правило врёт: в самой
        транслитерации у двенадцатого афоризма стоит ссылка на девятую сутру,
        «Cidvaditi (9) sūtre», и стена обрывалась ровно на ней.

        Здесь такая догадка и не нужна: вид блока расставлен по письменности
        при разборе (см. `normalise` в convert.py), а не унаследован от вёрстки
        источника.
        """
        return pairing(blocks, lambda b: b['k'] == 'iast')

    def sutras_url(self):
        return SUTRAS + SUTRAS_PAGE

    def page_title(self, name):
        return '%s: %s' % (self.name, name.lower())

    def heading(self, tag, title, anchor):
        """Заголовка раздела на странице нет.

        Раздел на ней один, и назван он тем же, чем названа сама страница.
        Второй такой заголовок под первым читается как сбой вёрстки.
        """
        return ''

    def nav(self, secs, titles):
        """Прыжок к переводу, а не оглавление страницы.

        Раздел на странице один, и оглавление из одной строки выглядело бы
        издевательством. Прыжок при этом нужен: сперва идёт весь санскрит
        части, и в двадцатом афоризме это две дюжины строф, которые пришлось
        бы листать до перевода.
        """
        if not secs or secs[0]['ru'] is None:
            return ''
        s = secs[0]
        links = [('санскрит', 'sa'), ('транслитерацию', 'iast'), ('перевод', 'ru')]
        row = ' · '.join('[%s](#%s-%s)' % (name, s['id'], key)
                         for name, key in links if s[key] is not None)
        return '<p class="pv-nav nosearch" markdown="1">Сразу на %s</p>' % row

    def todo(self, n):
        return ('<p class="pv-todo">Эта часть переведена ещё не полностью: %d %s ниже '
                'стоят по-английски — так, как они у источника. Санскрит, транслитерация '
                'и сама сутра на месте.</p>'
                % (n, plural(n, 'абзац', 'абзаца', 'абзацев')))

    def footer(self, pid, name):
        return ('*Санскрит и транслитерация перенесены с сайта **Габриэля Pradīpaka** без'
                ' изменений: [%s](%s). Перевод самих сутр — тоже его, со [страницы двадцати'
                ' сутр](%s). Перевод разбора Кшемараджи сделан для этого сайта по его'
                ' английскому изложению: по-русски этого разбора нет больше нигде.*'
                % (name, self.at_source(pid), self.sutras_url()))
