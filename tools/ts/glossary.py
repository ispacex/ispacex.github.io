#!/usr/bin/env python3
"""Собирает страницу /ksh/tantrasara/glossary/ из списка терминов и перевода.

Руками страница не пишется — как и все прочие страницы раздела. Список статей
лежит в `words.py` (общий с «Тантралокой» плюс здешние), а ссылки «где это
разбирается» считаются по переводу: берутся абзацы, в которых термин помечен
гуще всего.

    python3 glossary.py

Ссылки идут в абзац перевода по якорю, который ставит сборка страниц:
`/ksh/tantrasara/ch3/#g-pratibimba`. Своих адресов у абзацев «Тантрасары» не
было — в отличие от «Тантралоки», — и якоря заводит словарь, как у
Parātrīśikāvivaraṇa.

Озвучка сюда не входит: mp3 кладёт `audio.py`, и написание он берёт из этой же
страницы — из столбца «Деванагари».
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import words
from parts import PARTS

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'tantrasara', 'glossary'))

HEAD = '''---
title: "Tantrasāra: словарь терминов"
---

<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [Tantrasāra](/ksh/tantrasara/) · [Поиск по сайту](/search/)</p>

# Словарь терминов

*Этого словаря нет в трактате. Он собран из тех самых санскритских помет,
которые стоят в скобках при каждом русском слове: помет в двадцати двух главах
**8 525**, и вверху по частоте — служебные слова, `ca`, `tatra`, `tu`. Здесь
оставлено то, обо что читатель спотыкается.*

> **Чья это работа.** Перевод «Тантрасары» на русский — **Габриэля
> Pradīpaka**; здесь он перенесён без изменений, и ни строки его мы не писали.
> Статьи словаря отобраны из его помет, но **толкования написаны для этого
> сайта** и за его слова не выдаются. За точным смыслом идите туда, где термин
> разбирается: последний столбец ведёт прямо в те абзацы.

*Словарь общий со [словарём «Тантралоки»](/ksh/ta/glossary/), и это не лень:
«Тантрасара» — та же «Тантралока», сжатая самим Абхинавагуптой до одной книги.
Объяснять `tattva` на одной странице сайта одними словами, а на соседней
другими значило бы разойтись с собою на ровном месте. Тридцать статей здесь
всё же свои — почти все обрядовые: у «Тантралоки» по-русски есть только
доктринальная половина, а «Тантрасара» переведена вся, вместе с обрядом от
омовения до каулической яги.*

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
<input type="search" id="gl-filter" placeholder="начните вводить термин, например «мандала» или «samvid»" /></p>

<p id="gl-voice" data-audio="/ksh/tantrasara/audio/" data-store="ts-voice">Голос:
<label><input type="radio" name="gl-voice" value="lekha" checked /> системный (Lekha, hi_IN)</label></p>
'''

TAIL = '''
<p class="pv-pager nosearch" markdown="1">[← Оглавление](/ksh/tantrasara/) · [Глава 1 — Vijñānabhedaprakāśanam →](/ksh/tantrasara/ch1/)</p>

<script src="/assets/js/glossary.js"></script>
'''


def where(place, names):
    """Столбец «где разбирается»: ссылки прямо в абзацы перевода.

    Подписью служит номер главы: имя её — «Kalādyadhvaprakāśanam» — в узкий
    служебный столбец не встанет, поэтому оно уходит во всплывающую подсказку.
    """
    return ' · '.join('<a href="/ksh/tantrasara/%s/#%s" title="%s">%s</a>'
                      % (slug, anchor, names[slug], slug[2:])
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
    # Те же статьи, вторым файлом: подсказка при наведении на слово в
    # подстрочнике берёт их оттуда, не таща сюда читателя (common/terms.dump).
    words.dump(OUT, words.SECTIONS)
    print('статей: %d, ссылок в текст: %d'
          % (sum(1 for _ in words.terms()), sum(len(v) for v in links.values())))


if __name__ == '__main__':
    main()
