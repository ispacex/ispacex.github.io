#!/usr/bin/env python3
"""Четыре проверки переноса Śivastotrāvalī. Каждая ломается тихо.

1. **Подстрочник не изменил текста.** Санскритское слово стоит над русским, а
   не скобкой в строке, но скобки никуда не делись — они в `<rp>`. Указатель
   поиска собирает Jekyll, снимая с абзаца теги, и строка обязана совпасть с
   прежней знак в знак. Проверка общая, `common/check.py`.
2. **Строф столько, сколько объявил источник.** Во вступлении Габриэль
   перечисляет число строф по гимнам; на странице они лежат отдельно от этого
   перечня, и разойтись они могут молча.
3. **У каждой строфы есть её транслитерация и её номер.** Строфа и
   транслитерация приходят одним абзацем и разводятся надвое на разборе
   (`convert.py`), а обратно построчно их складывает `pairing`. Не сложилась
   пара — страница покажет две стены вместо строфы, и это увидишь только
   глазом. Номер держит якорь `#v13.11`, по которому на строфу ссылаются.
4. **Каждый перевод — по-русски.** Абзац без кириллицы в `ru/*.json` означает,
   что туда попал английский текст источника, а не перевод.
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.check import verify
from common.page import SA_KINDS, pairing
from book import SV
from parts import HYMNS

CYR = re.compile(r'[А-Яа-яЁё]')


def texts():
    for path in sorted(glob.glob(os.path.join(HERE, 'ru', '*.json'))):
        name = os.path.basename(path)
        for key, v in json.load(open(path, encoding='utf-8')).items():
            yield name, key, v


def main():
    bad = verify(texts())

    book = SV()
    stanzas = folded = numbered = 0
    for n, _, _, declared in HYMNS:
        bs = book.blocks(str(n))
        pair, _, _, _ = pairing(bs)
        sa = [i for i, b in enumerate(bs) if b['k'] in SA_KINDS]
        stanzas += len(sa)
        folded += sum(1 for i in sa if i in pair)
        numbered += sum(1 for i in sa if bs[i].get('n'))
        if len(sa) != declared:
            bad += 1
            print('гимн %d: строф %d, а во вступлении объявлено %d' % (n, len(sa), declared))
        if len(sa) != sum(1 for i in sa if i in pair):
            bad += 1
            print('гимн %d: без транслитерации осталось строф %d'
                  % (n, len(sa) - sum(1 for i in sa if i in pair)))
        if len(sa) != sum(1 for i in sa if bs[i].get('n')):
            bad += 1
            print('гимн %d: без номера осталось строф %d'
                  % (n, len(sa) - sum(1 for i in sa if bs[i].get('n'))))
    print('строф %d, сложено с транслитерацией %d, с номером %d'
          % (stanzas, folded, numbered))

    dead = [(f, k) for f, k, v in texts() if isinstance(v, str) and not CYR.search(v)]
    for f, k in dead:
        bad += 1
        print('%s блок %s: перевод без кириллицы' % (f, k))
    print('расхождений всего: %d' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
