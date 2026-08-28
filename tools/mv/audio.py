#!/usr/bin/env python3
"""Озвучивает термины словаря /ksh/mv/ — общим скриптом `common/audio.py`.

Половина статей здесь общая с соседними словарями: `tattva`, `śakti`, `māyā`,
`prāṇa` стоят в трёх-четырёх из них разом. Написание на деванагари то же,
правило озвучки то же — звук вышел бы байт в байт тот же самый. Поэтому готовое
берётся у соседей, а наговаривается только своё: воспринимающие, состояния
сознания, буквы и яйца, каких у соседей нет.

    python3 audio.py            # сделать недостающие
    python3 audio.py --force    # переснять всё, что не занято у соседей
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from common.audio import main

KSH = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh'))
ROOT = os.path.join(KSH, 'mv')

# У кого занимать. `/ksh/pv/` в списке нет по той же причине, что и у соседа
# (`../ph/audio.py`): его системный комплект наговорен до того, как голосу
# стали дописывать висаргу, и общие слова звучали бы здесь по-старому.
BORROW = [(os.path.join(KSH, book, 'glossary', 'index.md'),
           os.path.join(KSH, book, 'audio'))
          for book in ('tantrasara', 'ta', 'sv', 'ph')]

if __name__ == '__main__':
    main(os.path.join(ROOT, 'glossary', 'index.md'),
         os.path.join(ROOT, 'audio'), BORROW)
