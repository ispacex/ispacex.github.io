#!/usr/bin/env python3
"""Дописывает переводы, не теряя уже написанного. Ключ — номер строфы.

Папку надо назвать, и назвать её осознанно: от неё зависит, чью работу увидит
под страницей читатель.

    from add import add
    add('ru', '1', {'1.7': '…'})   # переведено по английскому изложению
    add('sa', '2', {'2.1': '…'})   # переведено прямо с санскрита

Одна и та же строфа в обеих папках — ошибка, и `check.py` о ней скажет.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
WHERE = ('ru', 'sa')


def add(where, pid, d):
    if where not in WHERE:
        raise SystemExit('папка бывает только %s' % ' или '.join(WHERE))
    p = os.path.join(HERE, where, '%s.json' % pid)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    cur = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    cur.update({str(k): v for k, v in d.items()})
    order = sorted(cur, key=lambda s: tuple(int(x) for x in s.split('.')))
    json.dump({k: cur[k] for k in order}, open(p, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('%s/%s: всего переводов %d' % (where, pid, len(cur)))
