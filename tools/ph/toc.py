#!/usr/bin/env python3
"""Проставляет в оглавлении /ksh/ph/ состав каждой части и ход перевода.

Считается по тем же блокам, из которых собираются сами страницы, поэтому
оглавление не может разойтись с тем, что на страницах лежит на самом деле.
Заодно оно честно показывает, сколько переведено: пока разбор переводится,
строка говорит, сколько абзацев в ней ещё по-английски.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import SA_KINDS, plural
from book import PH
from parts import APHORISMS

book = PH()
INDEX = os.path.join(book.out, 'index.md')

rows, done, all_tr = [], 0, 0
for (n, name, about), (pid, slug, title) in zip(APHORISMS, book.parts):
    bs = book.blocks(pid)
    tr = book.load(pid)
    _pair, eaten, _, _ = book.pairing(bs)
    sa = sum(1 for i, b in enumerate(bs) if b['k'] in SA_KINDS and i not in eaten)
    text = [i for i, b in enumerate(bs) if b['k'] == 'text']
    left = sum(1 for i in text if tr(i, bs[i]) is None)
    done += len(text) - left
    all_tr += len(text)
    state = ('<em>%d %s, %d %s</em>'
             % (sa, plural(sa, 'строфа', 'строфы', 'строф'),
                len(text), plural(len(text), 'абзац', 'абзаца', 'абзацев')))
    if left:
        state += (' — <strong>%d %s ещё по-английски</strong>'
                  % (left, plural(left, 'абзац', 'абзаца', 'абзацев')))
    rows.append('<li><a href="%s">%s</a> — %s — %s</li>'
                % (book.url(slug), title, about, state))

s = open(INDEX, encoding='utf-8').read()
s = re.sub(r'<ul class="pv-toc">.*?</ul>',
           '<ul class="pv-toc">\n' + '\n'.join(rows) + '\n</ul>', s, flags=re.S)
open(INDEX, 'w', encoding='utf-8').write(s)
print('\n'.join(re.sub(r'<[^>]+>', '', r) for r in rows))
print('переведено абзацев: %d из %d' % (done, all_tr))
