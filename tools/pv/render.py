#!/usr/bin/env python3
"""Собирает страницы ksh/pv/ из разобранных блоков и русских переводов.

Деванагари и IAST переносятся из источника как есть — их никто не набирает
заново. Переводится только то, что по-английски: русский текст лежит в
ru/<id>.json (ключ — номер блока) и в ru/common.json (ключ — сам английский
текст, для повторяющихся вставок вроде «Important:»).
"""
import json, os, re, sys, glob
from parts import PARTS, SRC, SRC_URL

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'pv'))

def load(p, default):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default

COMMON = load(os.path.join(HERE, 'ru', 'common.json'), {})

# Санскритское слово в скобках внутри перевода: латиница с диакритикой и без
# кириллицы. После перевода вокруг него стоит русский текст, поэтому спутать
# его с обычной скобкой нельзя.
PAREN = re.compile(r'\(([^()]*?)\)')
CYR = re.compile(r'[А-Яа-яЁё]')
DIAC = re.compile(r'[āīūṛṝḷḹṭḍṇśṣñṅṁṃḥĀĪŪṚṬḌṆŚṢÑṄṀṂḤ]')

def markup(t):
    """Внутристрочная разметка: санскрит в скобках и вставки автора."""
    def paren(m):
        inner = m.group(1).strip()
        if not inner or CYR.search(inner):
            return m.group(0)
        # Санскрит узнаётся по диакритике IAST либо по тому, что это одно
        # латинское слово: «(ca)», «(mahā)», «(tad-ubhaya-yāmala)».
        if not (DIAC.search(inner) or re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", inner)):
            return m.group(0)
        return '<span class="pv-w">(' + m.group(1) + ')</span>'
    t = re.sub(r'--(.+?)--', lambda m: '<span class="pv-note">— ' + m.group(1) + ' —</span>', t, flags=re.S)
    t = PAREN.sub(paren, t)
    return t

def para(t, cls=None):
    t = markup(t).replace('\n', '<br />\n')
    if cls:
        return '<p class="%s" markdown="1">%s</p>' % (cls, t)
    return t

def sanskrit(t, cls):
    return '<p class="%s" lang="sa">%s</p>' % (cls, t.replace('\n', '<br />\n'))

def iast(t, cls):
    return '<p class="%s">%s</p>' % (cls, t.replace('\n', '<br />\n'))

def render(pid, slug, name, idx):
    blocks = json.load(open(os.path.join(HERE, 'blocks', '%s.json' % pid), encoding='utf-8'))['blocks']
    ru = load(os.path.join(HERE, 'ru', '%s.json' % pid), {})

    missing = []
    def tr(i, b):
        t = b['t']
        v = ru.get(str(i)) or COMMON.get(t)
        if v is None:
            missing.append((i, t))
            return None
        return v

    body = []
    for i, b in enumerate(blocks):
        k = b['k']
        if k == 'rule':
            body.append('<hr class="pv-rule" />')
        elif k in ('h3', 'h4'):
            v = tr(i, b)
            body.append(('## ' if k == 'h3' else '### ') + (v or b['t']))
            if v is None:
                body[-1] += ' <span class="pv-en">(не переведено)</span>'
        elif k == 'deva':
            body.append(sanskrit(b['t'], 'pv-sa' + (' pv-c' if b.get('c') else '')))
        elif k == 'deva-red':
            body.append(sanskrit(b['t'], 'pv-sa pv-src' + (' pv-c' if b.get('c') else '')))
        elif k == 'iast':
            body.append(iast(b['t'], 'pv-iast' + (' pv-c' if b.get('c') else '')))
        elif k == 'text':
            v = tr(i, b)
            if v is None:
                # Ещё не переведено: показываем как у источника и помечаем, а не
                # выдаём английский абзац за русский.
                body.append('<p class="pv-en" lang="en">%s</p>' % markup(b['t']).replace('\n', '<br />\n'))
            else:
                body.append(para(v, 'pv-tr' if b.get('c') else None))
        elif k == 'list':
            items = [ru.get('%d.%d' % (i, j), x) for j, x in enumerate(b['items'])]
            if any(ru.get('%d.%d' % (i, j)) is None for j in range(len(b['items']))):
                missing.append((i, '|'.join(b['items'])[:80] + ' [список]'))
            body.append('\n'.join(('%d. ' % (j + 1) if b['ordered'] else '* ') + x
                                  for j, x in enumerate(items)))
        elif k == 'table':
            v = ru.get(str(i))
            if v is None:
                missing.append((i, '[таблица]'))
                v = '<table>%s</table>' % b['html']
            body.append(v)

    n_en = len(missing)
    missing_note = ('<p class="pv-todo">Эта часть переведена ещё не полностью: %d %s ниже '
                    'стоят по-английски — так, как они у источника. Санскрит и транслитерация '
                    'на месте.</p>' % (n_en, 'абзац' if n_en % 10 == 1 and n_en % 100 != 11 else
                                       ('абзаца' if n_en % 10 in (2, 3, 4) and n_en % 100 not in (12, 13, 14)
                                        else 'абзацев'))) if missing else ''

    prev_link = '[← %s](/ksh/pv/%s/)' % (PARTS[idx - 1][2], PARTS[idx - 1][1]) if idx > 0 else '[← Введение](/ksh/pv/)'
    next_link = '[%s →](/ksh/pv/%s/)' % (PARTS[idx + 1][2], PARTS[idx + 1][1]) if idx + 1 < len(PARTS) else ''

    head = [
        '---\ntitle: "Parātrīśikāvivaraṇa: %s"\n---' % name.lower(),
        '[КШ](/ksh/) · [Parātrīśikāvivaraṇa](/ksh/pv/) · [Поиск по сайту](/search/)',
        '',
        '# %s' % name,
        '',
        '<p class="pv-pager">%s%s</p>' % (prev_link, ' · ' + next_link if next_link else ''),
        '',
    ]
    if missing_note:
        head.append(missing_note)
        head.append('')
    tail = [
        '',
        '<p class="pv-pager">%s%s</p>' % (prev_link, ' · ' + next_link if next_link else ''),
        '',
        '---',
        '',
        '*Перевод на русский сделан для этого сайта по английскому изложению Габриэля'
        ' Pradīpaka: [%s](%s%s). Санскрит (деванагари и IAST) перенесён из источника без изменений.*'
        % (name, SRC, SRC_URL[pid]),
    ]

    text = '\n\n'.join(head + body + tail)
    text = re.sub(r'\n{3,}', '\n\n', text)
    os.makedirs(os.path.join(OUT, slug), exist_ok=True)
    open(os.path.join(OUT, slug, 'index.md'), 'w', encoding='utf-8').write(text.rstrip() + '\n')
    return missing

if __name__ == '__main__':
    only = sys.argv[1:] or [p[0] for p in PARTS]
    total = 0
    for idx, (pid, slug, name) in enumerate(PARTS):
        if pid not in only:
            continue
        m = render(pid, slug, name, idx)
        total += len(m)
        print('%s %-8s блоков без перевода: %d' % (pid, slug, len(m)))
    print('итого без перевода:', total)
