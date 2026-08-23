#!/usr/bin/env python3
"""Показывает непереведённые блоки страницы: номер и английский текст."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
pid = sys.argv[1]
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
blocks = json.load(open(os.path.join(HERE, 'blocks', '%s.json' % pid), encoding='utf-8'))['blocks']
common = json.load(open(os.path.join(HERE, 'ru', 'common.json'), encoding='utf-8'))
pp = os.path.join(HERE, 'ru', '%s.json' % pid)
ru = json.load(open(pp, encoding='utf-8')) if os.path.exists(pp) else {}
n = 0
for i, b in enumerate(blocks):
    if not (lo <= i <= hi): continue
    if b['k'] not in ('text', 'h3', 'h4'): continue
    if str(i) in ru or b['t'] in common: continue
    n += 1
    print('#%d %s%s' % (i, b['k'], ' [ПЕРЕВОД]' if b.get('c') else ' [пояснение]'))
    print(b['t'])
    print()
print('--- осталось в этом отрезке: %d' % n)
