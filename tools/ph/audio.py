#!/usr/bin/env python3
"""Озвучивает термины словаря /ksh/ph/ — общим скриптом `common/audio.py`.

Больше половины статей здесь общие с соседними словарями: написание на
деванагари то же, правило озвучки то же, и звук вышел бы байт в байт тот же
самый. Поэтому готовое берётся у них, а наговаривается только своё — слова,
которых у соседей нет: `citi`, `saṅkoca`, `vikāsa`, `pañcakṛtya`, `bhūmikā`,
`vyāmohitatā`, `haṭhapāka`, `alaṅgrāsa`.

    python3 audio.py            # сделать недостающие
    python3 audio.py --force    # переснять всё, что не занято у соседей
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from common.audio import main

KSH = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh'))
ROOT = os.path.join(KSH, 'ph')

# У кого занимать. Порядок значим только тем, что первый найденный и берётся;
# файлы у этих трёх одинаковые, так что выбор ни на что не влияет.
#
# `/ksh/pv/` в списке **нет**, и это не оплошность. Его системный комплект
# наговорен до того, как голосу стали дописывать висаргу, и десять общих с ним
# слов — `saṅkoca`, `ahantā`, `abheda`, `unmeṣa` и ещё шесть — звучали бы здесь
# по-старому: «санкоч» вместо «санкочах». Занимать такое нельзя; эти десять
# наговариваются заново. Сам комплект /ksh/pv/ от этого не чинится — там он
# запасной при голосе Parler, — но и не расходится с этой страницей.
BORROW = [(os.path.join(KSH, book, 'glossary', 'index.md'),
           os.path.join(KSH, book, 'audio'))
          for book in ('tantrasara', 'ta', 'sv')]

if __name__ == '__main__':
    main(os.path.join(ROOT, 'glossary', 'index.md'),
         os.path.join(ROOT, 'audio'), BORROW)
