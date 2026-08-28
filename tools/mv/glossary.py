#!/usr/bin/env python3
"""Собирает страницу /ksh/mv/glossary/ из списка терминов и самого перевода.

Руками страница не пишется — как и все прочие страницы раздела. Список статей
лежит в `words.py`, а ссылки «где в главах» считаются по переводу: берутся
строфы, при которых термин помечен гуще всего.

    python3 glossary.py

Якорей ради этого заводить не пришлось, и этим словарь похож на
[словарь Śivastotrāvalī](../sv/glossary.py) и не похож на
[словарь Parātrīśikāvivaraṇa](../pv/glossary.py): там ссылки в текст держатся
на якорях, которые расставляет сборка страниц, а здесь у каждой строфы уже
есть свой адрес по номеру — `#v23`.

Считается только по главам 1–4: под строфами глав 5–23 у источника нет
изложения, а значит нет и помет, из которых словарь собран.

Озвучка сюда не входит: mp3 кладёт `audio.py` в `ksh/mv/audio/`, и написание
он берёт из этой же страницы — из атрибута `data-tts`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import words
from parts import PARTS

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'mv', 'glossary'))

HEAD = '''---
title: "Mālinīvijayottaratantra: словарь терминов"
---

<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [Mālinīvijayottaratantra](/ksh/mv/) · [Поиск по сайту](/search/)</p>

# Словарь терминов

*Этого словаря нет в книге: он собран для русского перевода из тех самых
санскритских помет, которые стоят в скобках при каждом русском слове. Отбирать
пришлось: помет 3406, и чаще всего в них попадаются связки — `ca` «и» сто
тридцать три раза. Здесь оставлено то, обо что читатель спотыкается.*

*Словарь у этой тантры не такой, как у соседей. У [«Шивастотравали»](/ksh/sv/glossary/)
стихи, и самое частое слово там — `bhakti`, преданность. Здесь учебник
устройства, и самые частые слова — разряды: `tattva`, `varga`, `pada`, `kalā`.
Семь воспринимающих, пять состояний сознания под тремя именами каждое,
пятьдесят букв по частям тела, четыре яйца Брахмы.*

*Последний столбец ведёт в те строфы, где термин звучит гуще всего. Считан он
по главам 1–4: под строфами глав 5–23 изложения нет и у источника, а значит нет
и помет. У нескольких статей столбец пуст — `pramātṛ`, `pramāṇa`, `svātantrya`,
`śaktipāta` разбираются в пояснениях по-русски, а в санскритской помете не
стоят ни разу. Словарь шире подстрочника, и должен быть шире.*

*Обратный путь тоже есть: санскритское слово в подстрочнике перевода само ведёт
сюда, а при наведении показывает статью на месте.*

*Кнопка ♪ произносит термин. Звук синтезирован заранее из написания на
деванагари голосом **Lekha** (hi_IN) — это не запись чтеца и не эталон
произношения: осторожнее с придыхательными, ретрофлексными и долготами.*

*Голос читает по правилам хинди, а хинди глотает конечное краткое «а»:
`शिव` он выговаривал «шив». Поэтому слову, кончающемуся согласной, дописана
висарга — и голос произносит именительный падеж, `śivaḥ`, которым слово и
называют вслух. Расплата за это одна: на конце слышно лёгкое придыхание,
которого в написании над кнопкой нет.*

<p><label for="gl-filter">Фильтр:</label>
<input type="search" id="gl-filter" placeholder="начните вводить термин, например «таттва» или «malini»" /></p>

<p id="gl-voice" data-audio="/ksh/mv/audio/" data-store="mv-voice">Голос:
<label><input type="radio" name="gl-voice" value="lekha" checked /> системный (Lekha, hi_IN)</label></p>
'''

TAIL = '''
<p class="pv-pager nosearch" markdown="1">[← Оглавление](/ksh/mv/) · [Глава 1 →](/ksh/mv/ch1/)</p>

<script src="/assets/js/glossary.js"></script>
'''


def where(place, names):
    """Столбец «где в главах»: ссылки прямо на строфы, по их номерам."""
    return ' · '.join('<a href="/ksh/mv/%s/#%s" title="%s">%s</a>'
                      % (slug, anchor, names[slug],
                         '%s.%s' % (slug[2:], anchor[1:]))
                      for slug, anchor in place)


def row(term, place, names):
    tts = ' data-say="%s"' % term.say if term.say else ''
    return ('<tr id="t-%s" data-alias="%s">'
            '<td class="term">%s</td>'
            '<td class="skt" data-tts="%s"%s>%s</td>'
            '<td class="deva">%s</td>'
            '<td>%s</td>'
            '<td class="where">%s</td></tr>'
            % (words.keyof(term), term.alias or term.ru.lower(),
               term.ru, words.keyof(term), tts, term.iast,
               term.deva, words.markup(term.gloss), where(place, names)))


def main():
    names = {slug: title for _, slug, title in PARTS}
    links = words.links()
    out = [HEAD]
    for title, group in words.SECTIONS:
        out.append('## %s\n' % title)
        out.append('<div class="gl-wrap" markdown="0">\n<table class="gl">')
        out.append('<tr><th>Термин</th><th>Санскрит</th><th>Деванагари</th>'
                   '<th>Значение</th><th>Где в главах</th></tr>')
        for term in group:
            out.append(row(term, links.get(term.iast, ()), names))
        out.append('</table>\n</div>\n')
    out.append(TAIL)

    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.md'), 'w', encoding='utf-8').write('\n'.join(out))
    # Те же статьи, вторым файлом: подсказка при наведении на слово в
    # подстрочнике берёт их оттуда, не таща сюда читателя (common/terms.dump).
    words.dump(OUT, words.SECTIONS)
    print('статей: %d, ссылок в главы: %d'
          % (sum(1 for _ in words.terms()), sum(len(v) for v in links.values())))


if __name__ == '__main__':
    main()
