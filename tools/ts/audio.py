#!/usr/bin/env python3
"""Озвучивает термины словаря /ksh/tantrasara/ — общим скриптом `common/audio.py`.

Больше сотни статей здесь общие с «Тантралокой», а часть — ещё и с гимнами.
Написание на деванагари у них то же, правило озвучки то же, и звук вышел бы
байт в байт тот же самый. Поэтому готовое берётся у соседей, а наговаривается
только своё — обрядовые слова, которых в тех словарях нет.

    python3 audio.py            # сделать недостающие
    python3 audio.py --force    # переснять всё, что не занято у соседей
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from common.audio import main

KSH = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh'))
ROOT = os.path.join(KSH, 'tantrasara')

# У кого занимать. Порядок значим только тем, что первый найденный и берётся;
# файлы там одинаковые, так что выбор ни на что не влияет.
BORROW = [(os.path.join(KSH, book, 'glossary', 'index.md'),
           os.path.join(KSH, book, 'audio')) for book in ('ta', 'sv')]

if __name__ == '__main__':
    main(os.path.join(ROOT, 'glossary', 'index.md'),
         os.path.join(ROOT, 'audio'), BORROW)
