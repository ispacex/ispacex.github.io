#!/usr/bin/env python3
"""Проверяет перенос «Тантрасары».

Три вещи, каждая из которых ломается тихо:

* подстрочник не изменил текста абзаца (общая проверка, common/check.py) —
  иначе поисковый указатель разойдётся со страницей, а страница будет
  выглядеть целой;
* каждый абзац перевода — по-русски. Пустой список значит, что у источника
  ничего не осталось по-английски: ради этого перенос и затевался;
* стены сложены целиком — у каждой строфы деванагари есть её транслитерация.
  Расхождение здесь означает, что у источника прибавилось или убыло абзацев,
  и главу надо смотреть глазами.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.check import verify
from common.page import SA_KINDS, pairing
from book import TS, CYR
from parts import PARTS


def main():
    book = TS()
    items, en, unpaired = [], [], []
    for pid, slug, name in PARTS:
        bs = book.blocks(pid)
        pair, eaten, _, _ = pairing(bs)
        for i, b in enumerate(bs):
            if b['k'] == 'text' and i not in eaten:
                if CYR.search(b['t']):
                    items.append((slug, i, b['t']))
                else:
                    en.append((slug, i, b['t'][:70]))
            elif b['k'] in SA_KINDS and i not in pair:
                unpaired.append((slug, i, b['t'][:40]))
    bad = verify(items)
    print('абзацев без кириллицы: %d' % len(en))
    for x in en:
        print('  %s блок %s: %s' % x)
    print('строф без транслитерации: %d' % len(unpaired))
    for x in unpaired:
        print('  %s блок %s: %s' % x)
    return 1 if (bad or en or unpaired) else 0


if __name__ == '__main__':
    sys.exit(main())
