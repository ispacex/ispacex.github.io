#!/usr/bin/env python3
"""Проставляет в оглавлении /ksh/sv/ состав каждого гимна и состояние перевода.

Считается по тем же блокам и тем же переводам, из которых собираются сами
страницы, поэтому оглавление не может обещать перевода, которого на странице
нет.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import plural
from book import SV
from parts import HYMNS

book = SV()
INDEX = os.path.join(book.out, 'index.md')

rows = []
for (n, name, about, _), (pid, slug, title) in zip(HYMNS, book.parts):
    total, en, sa = book.counts(pid)
    done = en + sa
    state = ('переведён' if done >= total else
             'переведено %d' % done if done else 'перевода нет')
    rows.append('<li><a href="%s">%s</a> — %s — <em>%d %s, %s</em></li>'
                % (book.url(slug), title, about,
                   total, plural(total, 'строфа', 'строфы', 'строф'), state))

s = open(INDEX, encoding='utf-8').read()
s = re.sub(r'<ul class="pv-toc">.*?</ul>',
           '<ul class="pv-toc">\n' + '\n'.join(rows) + '\n</ul>', s, flags=re.S)
open(INDEX, 'w', encoding='utf-8').write(s)
print('\n'.join(re.sub(r'<[^>]+>', '', r) for r in rows))
