#!/usr/bin/env python3
"""Печатает то, что в главе ещё стоит по-английски, — с ключами перевода.

    python3 show.py 1          # что осталось в первой главе
    python3 show.py 1 --json   # то же, готовым куском для ru/1.json

Служебный скрипт для самой работы перевода: страницы он не трогает.

В главах 5–23 английского абзаца под строфой нет вовсе — там пустое место
(блок `gap`), и переводится не изложение, а сама строфа. Поэтому под ключом
здесь печатается то, что этот ключ подписывает: у главы 1–4 английский абзац
Габриэля, у главы 5–23 — транслитерация строфы, к которой пусто.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from book import MV
from convert import key

def verse(bs, i):
    """Транслитерация ближайшей строфы над пустым местом."""
    for b in reversed(bs[:i]):
        if b['k'] == 'iast':
            return b['t']
    return ''


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    as_json = '--json' in sys.argv
    b = MV()
    out = {}
    for pid in args:
        bs, tr = b.blocks(pid), b.load(pid)
        for i, x in enumerate(bs):
            if x['k'] not in ('text', 'list', 'table', 'gap') or tr(i, x) is not None:
                continue
            k = key(x)
            if x['k'] == 'gap':
                # Пустому месту подписывать нечего собою: печатаем строфу, под
                # которой оно стоит, — её и предстоит перевести.
                out[k] = verse(bs, i)
            elif x['k'] == 'text':
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
