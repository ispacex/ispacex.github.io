#!/usr/bin/env python3
"""Проставляет в оглавлении /ksh/tantrasara/ состав каждой главы.

Считается по тем же блокам, из которых собираются сами страницы, поэтому
оглавление не может разойтись с тем, что на страницах лежит на самом деле.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import SA_KINDS, pairing, plural
from book import TS, CYR
from parts import CHAPTERS

book = TS()
INDEX = os.path.join(book.out, 'index.md')

rows = []
for (pid, n, name, about), (_, slug, title) in zip(CHAPTERS, book.parts):
    bs = book.blocks(pid)
    pair, eaten, _, _ = pairing(bs)
    sa = sum(1 for i, b in enumerate(bs) if b['k'] in SA_KINDS)
    ru = sum(1 for i, b in enumerate(bs)
             if b['k'] == 'text' and i not in eaten and CYR.search(b['t']))
    rows.append('<li><a href="%s">%s</a> — %s — <em>%d %s, %d %s</em></li>'
                % (book.url(slug), title, about[0].lower() + about[1:],
                   sa, plural(sa, 'строфа', 'строфы', 'строф'),
                   ru, plural(ru, 'абзац', 'абзаца', 'абзацев')))

s = open(INDEX, encoding='utf-8').read()
s = re.sub(r'<ul class="pv-toc">.*?</ul>',
           '<ul class="pv-toc">\n' + '\n'.join(rows) + '\n</ul>', s, flags=re.S)
open(INDEX, 'w', encoding='utf-8').write(s)
print('\n'.join(re.sub(r'<[^>]+>', '', r) for r in rows))
