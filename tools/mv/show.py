#!/usr/bin/env python3
"""Печатает то, что в главе ещё стоит по-английски, — с ключами перевода.

    python3 show.py 1          # что осталось в первой главе
    python3 show.py 1 --json   # то же, готовым куском для ru/1.json

Служебный скрипт для самой работы перевода: страницы он не трогает. Главы, у
которых изложения нет вовсе (5–23), молчат: переводить там нечего.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from book import MV
from convert import key

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    as_json = '--json' in sys.argv
    b = MV()
    out = {}
    for pid in args:
        bs, tr = b.blocks(pid), b.load(pid)
        for i, x in enumerate(bs):
            if x['k'] not in ('text', 'list', 'table') or tr(i, x) is not None:
                continue
            k = key(x)
            if x['k'] == 'text':
                out[k] = x['t']
            elif x['k'] == 'list':
                for j, item in enumerate(x['items']):
                    out['%s/%d' % (k, j + 1)] = item
            else:
                out['%s/html' % k] = x['html']
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=1)[1:-1].rstrip())
    else:
        for k, v in out.items():
            print('--- %s' % k)
            print(v)
            print()
