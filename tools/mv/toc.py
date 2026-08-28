#!/usr/bin/env python3
"""Проставляет в оглавлении /ksh/mv/ состав каждой главы и состояние перевода.

Считается по тем же блокам и тем же переводам, из которых собираются сами
страницы, поэтому оглавление не может обещать перевода, которого на странице
нет. Состояний здесь три, и среднее — самое частое: у девятнадцати глав из
двадцати трёх изложения нет и у источника.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from book import MV
from common.page import plural
from convert import key
from parts import CHAPTERS

book = MV()
INDEX = os.path.join(book.out, 'index.md')

rows = []
for (_, n, _, about), (pid, slug, title) in zip(CHAPTERS, book.parts):
    bs = book.blocks(pid)
    head = json.load(open(os.path.join(HERE, 'blocks', '%s.json' % pid),
                          encoding='utf-8'))
    # Что на странице ждёт перевода: пустое место под строфой — там, где
    # изложения нет и у источника; английский абзац — там, где оно есть.
    blank = sum(1 for b in bs if b['k'] == 'gap')
    prose = sum(1 for b in bs if b['k'] in ('text', 'list', 'table') and key(b))
    done = sum(1 for b in bs if b['k'] in ('text', 'list', 'table')
               and key(b) in book._tr(pid))
    state = ('изложения нет и у источника' if blank else
             'переведена' if done >= prose else
             'переведено %d из %d абзацев' % (done, prose) if done else
             'перевода пока нет')
    # Полустрофа у источника считается половиной: «35.5». По-русски дробное
    # число ведёт за собою родительный падеж единственного числа — «35,5
    # строфы», — а целое склоняется как обычно.
    n_st = head['stanzas']
    count = ('' if not n_st else
             '%d %s' % (n_st, plural(int(n_st), 'строфа', 'строфы', 'строф'))
             if n_st == int(n_st) else
             '%s строфы' % ('%g' % n_st).replace('.', ','))
    rows.append('<li><a href="%s">%s</a> — %s — <em>%s, %s</em></li>'
                % (book.url(slug), title, about, count, state))

s = open(INDEX, encoding='utf-8').read()
s = re.sub(r'<ul class="pv-toc">.*?</ul>',
           '<ul class="pv-toc">\n' + '\n'.join(rows) + '\n</ul>', s, flags=re.S)
open(INDEX, 'w', encoding='utf-8').write(s)
print('\n'.join(re.sub(r'<[^>]+>', '', r) for r in rows))
