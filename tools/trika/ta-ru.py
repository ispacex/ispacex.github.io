#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Русский перевод «Тантралоки» со страниц источника — по группам строф.

Габриэль Pradīpaka перевёл главы 1–16 (31 страница из 56; см.
tools/trika/ta-ru-scan.py). Здесь его перевод разбирается, чтобы build-ta.py
положил его рядом с теми строфами, к которым он относится.

Общий разбор (tools/common/parse.py) здесь не годится: у «Тантралоки» вёрстка
третья, не такая, как у Parātrīśikāvivaraṇa и «Тантрасары».

## Почему не построфно

Соблазн велик: почти всюду строфа — один абзац, где деванагари и её
транслитерация стоят вместе, следом абзац перевода, и в конце у обоих номер
«||16||». Но верить нельзя ни номеру, ни порядку:

* У 4.8 перевод подписан «||9||» — опиской источника. Верь номеру — и восьмая
  останется без перевода, а девятая получит чужой.
* В начале 16-й главы тридцать строф свалены в один абзац стеной, а переводы
  идут следом порознь и не по одному на строфу.
* У 1.116–121 шесть строф стоят одним абзацем, а перевод к ним — сплошная
  проза в несколько абзацев, и номеров в ней нет вовсе. Разложить её по
  строфам нельзя никак: источник сам этого не сделал.

Поэтому единица здесь — **группа**: сколько строф источник поставил одним
абзацем, столько и относится к переводу, который идёт следом. Чаще всего в
группе одна строфа, и тогда перевод стоит при ней. Где группа больше — так
её и покажем, честно назвав, к каким строфам относится перевод.

Ошибиться так нельзя: описка в номере ни на что не влияет, а перевод не может
уехать на чужую строфу.

Сверяет разобранное с собранием IAST не этот скрипт, а build-ta.py --check:
собрание — его, и сходиться разбор обязан именно с тем текстом, который ляжет
на страницу.

    python3 tools/trika/ta-ru.py            # разобрать и напечатать сводку
    python3 tools/trika/ta-ru.py --json     # машинный вид
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from common.parse import strip_tags_keep

SRC = os.path.join(HERE, 'src')

# Страницы источника: глава → её страницы по порядку. Длинные главы источник
# делит на части, нумерация строф идёт по главе насквозь.
PAGES = {
    1: (582, 855, 856), 2: (857,), 3: (858, 859), 4: (860, 861), 5: (862,),
    6: (863, 864), 7: (865,), 8: (866, 867, 868), 9: (869, 870),
    10: (871, 872), 11: (873,), 12: (874,), 13: (875, 876, 877), 14: (878,),
    15: (879, 880, 881, 882), 16: (883, 884),
}

DEVA_SPAN = re.compile(r'<span[^>]*\bunicodesfont[^>]*>(.*?)</span>', re.S | re.I)
# Номер строфы в деванагари — индийскими цифрами: «॥१६॥», «॥१६-१७॥».
DEVA_DIGITS = '०१२३४५६७८९'
DEVA_NUMS = re.compile(r'॥\s*([%s]+)(?:\s*-\s*([%s]+))?\s*॥' % (DEVA_DIGITS, DEVA_DIGITS))
CYR = re.compile(r'[А-Яа-яЁё]')
DEVA = re.compile(r'[ऀ-ॿ]')


def deva_int(s):
    return int(''.join(str(DEVA_DIGITS.index(c)) for c in s))


def spread(text):
    """Номера строф, которые несёт кусок деванагари. «॥१६॥…॥१७॥» → [16, 17]."""
    out = []
    for m in DEVA_NUMS.finditer(text):
        a = deva_int(m.group(1))
        b = deva_int(m.group(2)) if m.group(2) else a
        out.extend(range(a, b + 1))
    return out


def body(html):
    """Тело страницы: без оглавления страницы, без подписи автора."""
    s = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    s = re.sub(r'<(script|style|noscript)\b.*?</\1>', '', s, flags=re.S | re.I)
    start = s.find('</h1>')
    toc = s.find('<table class="pagelinks"', start)
    end_toc = s.find('</table>', toc) if toc > 0 else -1
    if end_toc > 0:
        start = end_toc + len('</table>')
    end = s.find('<table class="artnav"')
    s = s[start:end if end > 0 else len(s)]
    fi = re.search(r'<h3><a id="Further[^"]*">.*?</h3>', s, flags=re.S)
    return s[:fi.start()] if fi else s


def lines(t):
    return [l for l in t.split('\n') if l.strip()]


def parse_page(path):
    """Одна страница: группы строф и куски без номера (открывающая строка)."""
    html = body(open(path, encoding='utf-8', errors='replace').read())
    groups, pre, cur = [], [], None
    for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', html, flags=re.S | re.I):
        inner = m.group(1)
        spans = [d.group(1) for d in DEVA_SPAN.finditer(inner) if DEVA.search(d.group(1))]
        if spans:
            # Новая группа. Пролётов деванагари в абзаце бывает несколько — по
            # одному на строфу; номера строф берутся из них.
            cur = {'nums': [], 'deva': {}, 'iast': [], 'ru': []}
            rest = inner[:]
            for d in reversed(list(DEVA_SPAN.finditer(inner))):
                rest = rest[:d.start()] + rest[d.end():]
            cur['iast'] = lines(strip_tags_keep(rest))
            for raw in spans:
                t = strip_tags_keep(raw)
                cur['nums'].extend(spread(t))
                # Пролёт бывает и на несколько строф разом — тогда режем его по
                # собственным номерам: иначе все двенадцать строк деванагари
                # достались бы каждой из шести строф.
                buf = []
                for line in lines(t):
                    buf.append(line)
                    ns = spread(line)
                    if ns:
                        for n in ns:
                            cur['deva'][n] = buf
                        buf = []
                if buf and cur['nums']:
                    cur['deva'].setdefault(cur['nums'][-1], []).extend(buf)
            # Открывающая строка главы номера не имеет: строфой она не
            # является. Но перевод у неё есть, и он нужен — «Здесь начинается
            # вторая глава почтенной Tantrāloka». Такие куски идут отдельным
            # списком, а сводит их со строками собрания build-ta.py.
            (groups if cur['nums'] else pre).append(cur)
            continue
        t = strip_tags_keep(inner)
        # Перевод — абзац с кириллицей после строфы. Вступление к главе стоит
        # до первой строфы и сюда не попадает; «в начало» и подписи к разделам
        # отсеиваются длиной.
        if cur is not None and CYR.search(t) and len(t) >= 20:
            cur['ru'].append(t)
    return groups, pre


def renumber(ch, groups):
    """Номера строф — по месту, а подпись под ними — только проверка.

    Группы идут по порядку и покрывают главу подряд, поэтому номер каждой
    вычисляется из того, сколько строф стояло до неё. Подпись у источника
    изредка врёт: в 15-й главе 444-я подписана «441», хотя 441-я прошла двумя
    группами выше. Верь подписи — и 444-й на странице не окажется вовсе, а
    441-я встретится дважды.

    Всякое расхождение печатается: молча переставлять номера строф нельзя.
    """
    off, at = [], 1
    for g in groups:
        want = list(range(at, at + len(g['nums'])))
        if want != g['nums']:
            off.append((ch, g['nums'], want))
            g['deva'] = {w: g['deva'].get(n, []) for w, n in zip(want, g['nums'])}
            g['nums'] = want
        at += len(want)
    return off


# Куда номер под строфой разошёлся с её местом в главе.
OFF = []


def collect(chapters=None):
    """Переведённые главы: {глава: [группа, …]} по порядку строф."""
    got = {}
    for ch, nodes in sorted(PAGES.items()):
        if chapters and ch not in chapters:
            continue
        groups, pre = [], []
        for node in nodes:
            path = os.path.join(SRC, 'ta-ru-%d.html' % node)
            if not os.path.exists(path):
                raise SystemExit('нет %s — сперва tools/trika/ta-ru-scan.py' % path)
            g, p = parse_page(path)
            groups.extend(g)
            pre.extend(p)
        OFF.extend(renumber(ch, groups))
        got[ch] = {'groups': groups, 'pre': pre}
    return got


def report(got):
    total = covered = empty = 0
    sizes = {}
    for ch in sorted(got):
        groups = got[ch]['groups']
        nums = [n for g in groups for n in g['nums']]
        seen = sorted(set(nums))
        dup = len(nums) - len(seen)
        gaps = [n for n in range(1, max(seen) + 1) if n not in set(seen)] if seen else []
        nofit = [g['nums'] for g in groups if not g['ru']]
        covered += sum(len(g['nums']) for g in groups if g['ru'])
        total += len(seen)
        empty += sum(len(g['nums']) for g in nofit)
        for g in groups:
            sizes[len(g['nums'])] = sizes.get(len(g['nums']), 0) + 1
        note = ''
        if gaps:
            note += ', пропущены %s' % gaps[:6]
        if dup:
            note += ', повторов %d' % dup
        if nofit:
            note += ', без перевода %s' % nofit[:4]
        print('глава %2d: строф %4d, групп %4d%s' % (ch, len(seen), len(groups), note))
    print('итого строф %d, с переводом %d, без перевода %d' % (total, covered, empty))
    print('размер группы: %s' % ', '.join('%d строф(ы) — %d' % (k, v)
                                          for k, v in sorted(sizes.items())))
    for ch, said, want in OFF:
        print('глава %d: подписано %s, по месту %s' % (ch, said, want))
    return empty


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--json', action='store_true', help='машинный вид')
    ap.add_argument('--chapter', type=int, action='append', help='только эта глава')
    a = ap.parse_args()
    got = collect(a.chapter)
    if a.json:
        json.dump(got, sys.stdout, ensure_ascii=False)
        return 0
    return 1 if report(got) else 0


if __name__ == '__main__':
    sys.exit(main())
