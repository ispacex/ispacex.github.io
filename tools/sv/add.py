#!/usr/bin/env python3
"""Дописывает переводы в ru/<номер гимна>.json, не теряя уже написанного."""
import json, os


def add(pid, d):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ru', '%s.json' % pid)
    cur = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    cur.update({str(k): v for k, v in d.items()})
    json.dump(cur, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: всего переводов %d' % (pid, len(cur)))
