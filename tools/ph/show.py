#!/usr/bin/env python3
"""Печатает английские абзацы части, которым перевода ещё нет.

    python3 show.py 4        # что осталось в четвёртом афоризме

Служебный скрипт для самой работы перевода: страницы он не трогает.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from book import PH

if __name__ == '__main__':
    b = PH()
    for pid in sys.argv[1:]:
        bs, tr = b.blocks(pid), b.load(pid)
        for i, x in enumerate(bs):
            if x['k'] == 'text' and tr(i, x) is None:
                print('--- %s/%d' % (pid, i))
                print(x['t'])
                print()
