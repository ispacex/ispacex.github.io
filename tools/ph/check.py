#!/usr/bin/env python3
"""Проверяет перевод Pratyabhijñāhṛdayam.

Четыре вещи, и каждая ломается тихо — страница при этом выглядит целой:

* **подстрочник не изменил текста абзаца** (общая проверка, common/check.py).
  Санскрит стоит над русским словом, а не скобкой в строке, но скобки никуда
  не делись — они в `<rp>`. Указатель поиска собирает Jekyll, снимая с абзаца
  теги, и строка обязана совпасть с прежней знак в знак;
* **стены сложены целиком** — у каждой строфы деванагари есть её
  транслитерация. Расхождение означает, что разбор съехал, и часть надо
  смотреть глазами;
* **сутра в части одна** — ровно одна строфа красная, и перевод её берётся у
  источника, а не пишется здесь;
* **перевод не разъехался с блоками** — ключей в `ru/<часть>.json` не больше,
  чем в части абзацев, и все они на месте. Ключ здесь — номер блока, и от
  правки разбора он бы съехал: перевод молча встал бы не под тот абзац.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.check import verify
from common.page import SA_KINDS
from book import PH
from parts import PARTS


def texts():
    for path in sorted(glob.glob(os.path.join(HERE, 'ru', '*.json'))):
        name = os.path.basename(path)
        for key, v in json.load(open(path, encoding='utf-8')).items():
            yield name, key, v


def main():
    book = PH()
    unpaired, reds, stray = [], [], []
    for pid, slug, _name in PARTS:
        bs = book.blocks(pid)
        # Складывание спрашивается у самого писания: у него оно своё,
        # см. `PH.pairing`.
        pair, eaten, _, _ = book.pairing(bs)
        for i, b in enumerate(bs):
            if b['k'] in SA_KINDS and i not in pair and i not in eaten:
                unpaired.append((slug, i, b['t'][:40]))
        n = sum(1 for b in bs if b['k'] == 'deva-red')
        if n != (0 if pid == '0' else 1):
            reds.append((slug, n))
        # Ключи перевода — номера блоков. Ключ, которому в части нет абзаца,
        # значит, что разбор съехал: перевод потерялся, и молча.
        for key in book._ru(pid):
            i = int(key.split('.')[0])
            if not (0 <= i < len(bs)) or bs[i]['k'] != 'text':
                stray.append((slug, key))

    bad = verify(texts())
    print('строф без транслитерации: %d' % len(unpaired))
    for x in unpaired:
        print('  %s блок %s: %s' % x)
    print('частей, где сутра не одна: %d' % len(reds))
    for x in reds:
        print('  %s: красных строф %d' % x)
    print('переводов не под абзацем: %d' % len(stray))
    for x in stray:
        print('  %s ключ %s' % x)
    return 1 if (bad or unpaired or reds or stray) else 0


if __name__ == '__main__':
    sys.exit(main())
