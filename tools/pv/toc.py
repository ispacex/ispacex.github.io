#!/usr/bin/env python3
"""Проставляет в оглавлении /ksh/pv/ состояние перевода каждой части.

Считается по тем же данным, что и сборка страниц, поэтому оглавление не может
разойтись с тем, что на страницах на самом деле лежит.
"""
import json, os, re
from parts import PARTS

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'pv', 'index.md'))
COMMON = json.load(open(os.path.join(HERE, 'ru', 'common.json'), encoding='utf-8'))

NOTE = {
    's1-2-1': ' — пять вступительных строф Абхинавагупты и начало комментария к строфе 1',
    's1-2-4': ' — конец строфы 1, строфа 1½ и строфа 2',
}

rows = []
for pid, slug, name in PARTS:
    blocks = json.load(open(os.path.join(HERE, 'blocks', '%s.json' % pid), encoding='utf-8'))['blocks']
    pp = os.path.join(HERE, 'ru', '%s.json' % pid)
    ru = json.load(open(pp, encoding='utf-8')) if os.path.exists(pp) else {}
    need = [i for i, b in enumerate(blocks) if b['k'] in ('text', 'h3', 'h4')]
    done = [i for i in need if str(i) in ru or blocks[i]['t'] in COMMON]
    pct = round(100 * len(done) / len(need)) if need else 100
    state = 'переведено' if pct == 100 else ('переведено %d%%' % pct if pct else 'ещё не переведено')
    rows.append('<li><a href="/ksh/pv/%s/">%s</a>%s — <em>%s</em></li>' % (slug, name, NOTE.get(slug, ''), state))

s = open(INDEX, encoding='utf-8').read()
s = re.sub(r'<ul class="pv-toc">.*?</ul>',
           '<ul class="pv-toc">\n' + '\n'.join(rows) + '\n</ul>', s, flags=re.S)
open(INDEX, 'w', encoding='utf-8').write(s)
print('\n'.join(re.sub(r'<[^>]+>', '', r) for r in rows))
