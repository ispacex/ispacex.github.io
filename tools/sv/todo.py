#!/usr/bin/env python3
"""Показывает строфы гимна, которым перевода ещё нет: номер, санскрит, IAST.

    python3 todo.py 2          # весь второй гимн
    python3 todo.py 2 1 8      # строфы 2.1–2.8

Английского изложения под этими строфами нет — потому они здесь и оказались, —
так что переводить придётся прямо с санскрита. Транслитерация печатается рядом
с деванагари: с неё и работают.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import SA_KINDS
from book import SV

pid = sys.argv[1]
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9

book = SV()
blocks = book.blocks(pid)
known = book.load(pid)

n = 0
for i, b in enumerate(blocks):
    if b['k'] not in SA_KINDS or not b.get('n'):
        continue
    if not (lo <= int(b['n'].split('.')[1]) <= hi):
        continue
    if any(known(j, blocks[j]) for j in range(i, min(i + 3, len(blocks)))
           if blocks[j]['k'] in ('text', 'gap')):
        continue
    n += 1
    print('--- %s' % b['n'])
    print(b['t'])
    print(blocks[i + 1]['t'] if i + 1 < len(blocks) and blocks[i + 1]['k'] == 'iast' else '')
print('--- осталось в этом отрезке: %d' % n)
