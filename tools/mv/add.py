#!/usr/bin/env python3
"""Дописывает переводы главы, не теряя уже написанного.

    from add import add
    add('1', {'21/2': '…'})

Ключ — «номер строфы/номер абзаца под нею» (см. `convert.py`); у пункта списка
за ним идёт номер пункта, у таблицы — слово `html`. Порядок в файле — по
строфе и абзацу, а не по алфавиту: «10/1» после «9/1», а не перед «2/1». Файл
этот читает и правит человек, и найти в нём нужное место он должен глазами.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def order(k):
    """«21/2» -> (21, 2); «0/1» -> (0, 1); «21/3/2» -> (21, 3, 2)."""
    return tuple(int(x) if x.isdigit() else 10 ** 9 for x in k.split('/'))


def add(pid, d):
    p = os.path.join(HERE, 'ru', '%s.json' % pid)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    cur = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    cur.update({str(k): v for k, v in d.items()})
    json.dump({k: cur[k] for k in sorted(cur, key=order)},
              open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ru/%s: всего переводов %d' % (pid, len(cur)))
