#!/usr/bin/env python3
"""Показывает, что в гимне ещё не переведено: номер блока и строфа над ним.

Переводить здесь есть что только там, где у источника есть английское
изложение. Остальные строфы этот список не покажет вовсе — их абзацы выброшены
на разборе (см. convert.py), и придумывать перевод не из чего.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
pid = sys.argv[1]
blocks = json.load(open(os.path.join(HERE, 'blocks', '%s.json' % pid), encoding='utf-8'))['blocks']
pp = os.path.join(HERE, 'ru', '%s.json' % pid)
ru = json.load(open(pp, encoding='utf-8')) if os.path.exists(pp) else {}

n = 0
for i, b in enumerate(blocks):
    if b['k'] != 'text' or str(i) in ru:
        continue
    n += 1
    at = next((blocks[j].get('n') for j in range(i - 1, -1, -1) if blocks[j].get('n')), '?')
    print('#%d — строфа %s' % (i, at))
    print(b['t'])
    print()
print('--- осталось: %d' % n)
