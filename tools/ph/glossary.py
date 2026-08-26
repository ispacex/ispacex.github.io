#!/usr/bin/env python3
"""Собирает страницу /ksh/ph/glossary/ из списка терминов и самого перевода.

Руками страница не пишется — как и все прочие страницы раздела. Список статей
лежит в `words.py`, а ссылки «где это разбирается» считаются по переводу:
берутся абзацы, в которых термин помечен гуще всего.

    python3 glossary.py

Ссылки идут в абзац перевода по якорю, который ставит сборка страниц:
`/ksh/ph/s12/#g-vyamohitata`. Своих адресов у абзацев Pratyabhijñāhṛdayam не
было, и якоря заводит словарь — как у Parātrīśikāvivaraṇa и «Тантрасары».

Озвучка сюда не входит: mp3 кладёт `audio.py`, и написание он берёт из этой же
страницы — из столбца «Деванагари».
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import words
from parts import PARTS, SUTRAS, SUTRAS_PAGE

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'ph', 'glossary'))

HEAD = '''---
title: "Pratyabhijñāhṛdayam: словарь терминов"
---

<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [Pratyabhijñāhṛdayam](/ksh/ph/) · [Поиск по сайту](/search/)</p>

# Словарь терминов

*Этого словаря нет в трактате. Он собран из тех самых санскритских помет,
которые стоят в скобках при каждом русском слове: помет в переводе разбора
**2 232**, и вверху по частоте, как всегда, служебные слова — `iti`, `eva`,
`tad`, `ca`. Здесь оставлено то, обо что читатель спотыкается.*

> **Чья это работа.** Разбор Кшемараджи переведён **для этого сайта**: у
> источника его нет по-русски, есть только английский. А вот **сами двадцать
> сутр** — перевод **Габриэля Pradīpaka**, взятый у него готовым, [со страницы
> двадцати сутр]({sutras}). Санскрит — деванагари и транслитерация — тоже его.
> Толкования в этом словаре написаны здесь и за его слова не выдаются.

*Список у этой книги свой, а не общий с соседями, и это решено замером.
«[Тантрасара](/ksh/tantrasara/glossary/)» берёт словарь у
«[Тантралоки](/ksh/ta/glossary/)» целиком — книга та же, сжатая тем же
автором. Здесь автор другой, Кшемараджа, и книга другая: из ста двадцати
статей «Тантралоки» **тридцать** не встречаются в ней ни разу — весь обряд, —
а самое частое её слово, `citi`, в том словаре отсутствует вовсе.*

*Помет тут вдвадцатеро меньше, чем у «Тантралоки», и последний столбец стоит
на тонком счёте: у части статей ссылка выходит одна, а не три. Это не поломка,
а всё, что книга о слове говорит.*

*Обратный путь тоже есть: санскритское слово в подстрочнике перевода само ведёт
сюда.*

*Кнопка ♪ произносит термин. Звук синтезирован заранее из написания на
деванагари голосом **Lekha** (hi_IN) — это не запись чтеца и не эталон
произношения: осторожнее с придыхательными, ретрофлексными и долготами.*

*Голос читает по правилам хинди, а хинди глотает конечное краткое «а»:
`शिव` он выговаривал «шив». Поэтому слову, кончающемуся согласной, дописана
висарга — и голос произносит именительный падеж, `śivaḥ`, которым слово и
называют вслух. Расплата за это одна: на конце слышно лёгкое придыхание,
которого в написании над кнопкой нет.*

<p><label for="gl-filter">Фильтр:</label>
<input type="search" id="gl-filter" placeholder="начните вводить термин, например «чити» или «sankoca»" /></p>

<p id="gl-voice" data-audio="/ksh/ph/audio/" data-store="ph-voice">Голос:
<label><input type="radio" name="gl-voice" value="lekha" checked /> системный (Lekha, hi_IN)</label></p>
'''.replace('{sutras}', SUTRAS + SUTRAS_PAGE)

TAIL = '''
<p class="pv-pager nosearch" markdown="1">[← Оглавление](/ksh/ph/) · [Начало →](/ksh/ph/begin/)</p>

<script src="/assets/js/glossary.js"></script>
'''


def label(slug):
    """Короткая подпись ссылки: «s12» → «12», «begin» → «нач.»."""
    return slug[1:] if slug.startswith('s') else 'нач.'


def where(place, names):
    """Столбец «где разбирается»: ссылки прямо в абзацы перевода.

    Подписью служит номер афоризма: название части — «Афоризм 12» — в узкий
    служебный столбец не встанет, поэтому оно уходит во всплывающую подсказку.
    """
    return ' · '.join('<a href="/ksh/ph/%s/#%s" title="%s">%s</a>'
                      % (slug, anchor, names[slug], label(slug))
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
    names = {slug: name for _pid, slug, name in PARTS}
    links = words.links()
    out = [HEAD]
    for title, group in words.SECTIONS:
        out.append('## %s\n' % title)
        out.append('<div class="gl-wrap" markdown="0">\n<table class="gl">')
        out.append('<tr><th>Термин</th><th>Санскрит</th><th>Деванагари</th>'
                   '<th>Значение</th><th>Где в тексте</th></tr>')
        for term in group:
            out.append(row(term, links.get(term.iast, ()), names))
        out.append('</table>\n</div>\n')
    out.append(TAIL)

    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.md'), 'w', encoding='utf-8').write('\n'.join(out))
    print('статей: %d, ссылок в текст: %d'
          % (sum(1 for _ in words.terms()), sum(len(v) for v in links.values())))


if __name__ == '__main__':
    main()
