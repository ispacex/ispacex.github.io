#!/usr/bin/env python3
"""Проверяет, что подстрочник не изменил текста страницы.

Санскрит стоит над строкой, а не в скобке внутри неё, но скобки при этом
никуда не делись: они лежат в `<rp>`. На этом держится поиск по сайту —
`/search-index.json` собирает Jekyll, снимая с абзаца теги, и после
подстрочника строка обязана совпасть с прежней знак в знак.

Проверка дешёвая, а поломка тихая: разъедется указатель, а страница будет
выглядеть целой. Запускать после правок в common/page.py.
"""
import re

from . import page

TAG = re.compile(r'<[^>]*>')


def plain(t):
    """Текст без разметки — то же, что оставит от абзаца strip_html."""
    return TAG.sub('', t)


def verify(items):
    """items — (откуда, ключ, текст). Печатает расхождения, возвращает их число."""
    bad = ruby = paren = total = 0
    for where, key, v in items:
        if not isinstance(v, str):
            continue
        total += 1
        out = page.markup(v)
        ruby += out.count('<ruby>')
        paren += out.count('pv-w')
        want = plain(page.notes(v, '— ', ' —'))
        if plain(out) != want:
            bad += 1
            i = next((i for i, (a, b) in enumerate(zip(plain(out), want)) if a != b), 0)
            print('%s блок %s разошёлся:' % (where, key))
            print('  было:  %r' % want[max(0, i - 60):i + 60])
            print('  стало: %r' % plain(out)[max(0, i - 60):i + 60])
        # Разметка не должна попадать внутрь основы подстрочника: она
        # открылась бы снаружи, а закрылась внутри. Голые подчёркивания и
        # звёздочки видны на странице сразу; тег виден не сразу и хуже —
        # закрытый внутри <span> оставляет «</span>» в поисковом указателе.
        for m in re.finditer(r'<ruby>(.*?)<rp>', out, re.S):
            if re.search(r'[_*<>]', m.group(1)):
                bad += 1
                print('%s блок %s: разметка внутри подстрочника: %r'
                      % (where, key, m.group(1)[:80]))
    print('абзацев %d, подстрочников %d, скобкой осталось %d' % (total, ruby, paren))
    print('расхождений: %d' % bad)
    return bad
