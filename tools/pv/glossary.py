#!/usr/bin/env python3
"""Собирает страницу /ksh/pv/glossary/ из списка терминов и самого перевода.

Руками страница не пишется — как и все прочие страницы раздела. Список статей
лежит в `words.py`, а ссылки «где это разбирается» считаются по переводу:
берутся абзацы, в которых термин помечен гуще всего.

    python3 glossary.py

Озвучка сюда не входит: mp3 кладутся в `ksh/pv/audio/` двумя скриптами из
~/git/site/tools (системный голос и Parler), и оба берут написание из этой же
страницы — из атрибута `data-tts`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import words
from parts import PARTS

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'pv', 'glossary'))

HEAD = '''---
title: "Parātrīśikāvivaraṇa: словарь терминов"
---

<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [Parātrīśikāvivaraṇa](/ksh/pv/) · [Поиск по сайту](/search/)</p>

# Словарь терминов

*Этого словаря нет в трактате: он собран для русского перевода из тех самых
санскритских помет, которые стоят в скобках при каждом русском слове. Написание
дано в IAST, толкования краткие и рабочие — за точным смыслом идите туда, где
термин разбирается: последний столбец ведёт прямо в те места. Обратный путь
тоже есть — санскритское слово в подстрочнике перевода само ведёт сюда.*

*Кнопки ♪ произносят термин: звук синтезирован заранее из написания на
деванагари и доступен в двух голосах. **Parler** —
[Indic Parler-TTS](https://huggingface.co/ai4bharat/indic-parler-tts) от
AI4Bharat, обученный в том числе на санскрите; **системный** — голос Lekha
(hi_IN), он читает по правилам хинди и склонен проглатывать конечное краткое
«а» (bheda → «бхед» вместо «бхеда»). Оба — синтез, а не запись чтеца, и
эталоном произношения не являются: осторожнее с придыхательными, ретрофлексными
и долготами.*

<p><label for="gl-filter">Фильтр:</label>
<input type="search" id="gl-filter" placeholder="начните вводить термин, например «шакти» или «samvid»" /></p>

<p id="gl-voice" data-audio="/ksh/pv/audio/" data-store="pv-voice">Голос:
<label><input type="radio" name="gl-voice" value="parler" checked /> Parler</label>
<label><input type="radio" name="gl-voice" value="lekha" /> системный</label></p>
'''

TAIL = '''
<p class="pv-pager nosearch" markdown="1">[← Введение](/ksh/pv/) · [Строфы 1–2, часть 1 →](/ksh/pv/s1-2-1/)</p>

<script src="/assets/js/glossary.js"></script>
'''


def label(slug):
    """Короткая подпись ссылки: «s5-8-2» → «5–8.2» — иначе столбец шире текста."""
    body, part = slug[1:].rsplit('-', 1)
    return '%s.%s' % (body.replace('-', '–'), part)


def where(place, names):
    """Столбец «где разбирается»: ссылки в те абзацы, где термин и разбирают."""
    return ' · '.join('<a href="/ksh/pv/%s/#%s" title="%s">%s</a>'
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
    # Те же статьи, вторым файлом: подсказка при наведении на слово в
    # подстрочнике берёт их оттуда, не таща сюда читателя (common/terms.dump).
    words.dump(OUT, words.SECTIONS)
    print('статей: %d, ссылок в текст: %d'
          % (sum(1 for _ in words.terms()), sum(len(v) for v in links.values())))


if __name__ == '__main__':
    main()
