#!/usr/bin/env python3
"""Собирает страницу /ksh/sv/glossary/ из списка терминов и самого перевода.

Руками страница не пишется — как и все прочие страницы раздела. Список статей
лежит в `words.py`, а ссылки «где в гимнах» считаются по переводу: берутся
строфы, в которых термин помечен гуще всего.

    python3 glossary.py

Якорей ради этого заводить не пришлось, и этим словарь отличается от
[словаря Parātrīśikāvivaraṇa](../pv/glossary.py): там ссылки в текст держатся
на якорях, которые расставляет сборка страниц, а здесь у каждой строфы уже
есть свой адрес по номеру — `#v13.11`.

Озвучка сюда не входит: mp3 кладутся в `ksh/sv/audio/` скриптом из
~/git/site/tools, и он берёт написание из этой же страницы — из атрибута
`data-tts`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import words
from parts import HYMNS

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'sv', 'glossary'))

HEAD = '''---
title: "Śivastotrāvalī: словарь терминов"
---

<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [Śivastotrāvalī](/ksh/sv/) · [Поиск по сайту](/search/)</p>

# Словарь терминов

*Этого словаря нет в книге: он собран для русского перевода из тех самых
санскритских помет, которые стоят в скобках при каждом русском слове. Отбирать
пришлось: помет пять с лишним тысяч, и чаще всего в них попадаются служебные
слова — `api` «также» двести восемь раз. Здесь оставлено то, обо что читатель
спотыкается.*

*Словарь у гимнов не такой, как у [Паратришика-вивараны](/ksh/pv/glossary/).
Там трактат, и словарь его школьный. Здесь стихи, и самое частое слово всей
книги — `bhakti`, преданность: девяносто четыре раза. За нею идут её вкус,
нектар и почитание. Школьные понятия тоже есть, но стоят там, где Утпаладева на
них опирается.*

*Последний столбец ведёт в те строфы, где термин звучит гуще всего. Обратный
путь тоже есть: санскритское слово в подстрочнике перевода само ведёт сюда.*

*Кнопка ♪ произносит термин. Звук синтезирован заранее из написания на
деванагари голосом **Lekha** (hi_IN) — это не запись чтеца и не эталон
произношения: осторожнее с придыхательными, ретрофлексными и долготами.*

*Голос читает по правилам хинди, а хинди глотает конечное краткое «а»:
`शिव` он выговаривал «шив». Поэтому слову, кончающемуся согласной, дописана
висарга — и голос произносит именительный падеж, `śivaḥ`, которым слово и
называют вслух. Расплата за это одна: на конце слышно лёгкое придыхание,
которого в написании над кнопкой нет.*

<p><label for="gl-filter">Фильтр:</label>
<input type="search" id="gl-filter" placeholder="начните вводить термин, например «бхакти» или «samvid»" /></p>

<p id="gl-voice" data-audio="/ksh/sv/audio/" data-store="sv-voice">Голос:
<label><input type="radio" name="gl-voice" value="lekha" checked /> системный (Lekha, hi_IN)</label></p>
'''

TAIL = '''
<p class="pv-pager nosearch" markdown="1">[← Оглавление](/ksh/sv/) · [Гимн 1 — Bhaktivilāsākhyaṁ stotram →](/ksh/sv/ch1/)</p>

<script src="/assets/js/glossary.js"></script>
'''


def where(place, names):
    """Столбец «где в гимнах»: ссылки прямо на строфы, по их номерам."""
    return ' · '.join('<a href="/ksh/sv/%s/#%s" title="%s">%s</a>'
                      % (slug, anchor, names[slug], anchor[1:])
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
               term.deva, term.gloss, where(place, names)))


def main():
    names = {'ch%d' % n: 'Гимн %d — %s' % (n, name) for n, name, _, _ in HYMNS}
    links = words.links()
    out = [HEAD]
    for title, group in words.SECTIONS:
        out.append('## %s\n' % title)
        out.append('<div class="gl-wrap" markdown="0">\n<table class="gl">')
        out.append('<tr><th>Термин</th><th>Санскрит</th><th>Деванагари</th>'
                   '<th>Значение</th><th>Где в гимнах</th></tr>')
        for term in group:
            out.append(row(term, links.get(term.iast, ()), names))
        out.append('</table>\n</div>\n')
    out.append(TAIL)

    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.md'), 'w', encoding='utf-8').write('\n'.join(out))
    print('статей: %d, ссылок в гимны: %d'
          % (sum(1 for _ in words.terms()), sum(len(v) for v in links.values())))


if __name__ == '__main__':
    main()
