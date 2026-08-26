#!/usr/bin/env python3
"""Шесть проверок Śivastotrāvalī. Каждая ломается тихо.

1. **Подстрочник не изменил текста.** Санскритское слово стоит над русским, а
   не скобкой в строке, но скобки никуда не делись — они в `<rp>`. Указатель
   поиска собирает Jekyll, снимая с абзаца теги, и строка обязана совпасть с
   прежней знак в знак. Проверка общая, `common/check.py`.
2. **Строф столько, сколько объявил источник.** Во вступлении Габриэль
   перечисляет их число по гимнам; на странице они лежат отдельно от этого
   перечня, и разойтись два счёта могут молча.
3. **У каждой строфы есть её транслитерация и её номер.** Строфа и
   транслитерация приходят одним абзацем и разводятся надвое на разборе
   (`convert.py`), а обратно построчно их складывает `pairing`. Не сложилась
   пара — страница покажет две стены вместо строфы. Пропал номер — сломается
   якорь `#v13.11` и потеряется ключ, по которому лежит перевод.
4. **Перевод лежит при существующей строфе.** Ключ, которому на странице
   ничего не соответствует, — это перевод, которого никто никогда не увидит.
5. **Одна строфа — одна родословная.** Строфа, лежащая и в `ru/`, и в `sa/`,
   сделала бы подпись под страницей ложью: та называет номера поимённо.
6. **Каждый перевод — по-русски.** Абзац без кириллицы значит, что туда попал
   санскрит или английский, а не перевод.
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.check import verify
from common.page import SA_KINDS, pairing
from book import SV, FROM_EN, FROM_SA
from parts import HYMNS

CYR = re.compile(r'[А-Яа-яЁё]')


def texts():
    for where in (FROM_EN, FROM_SA):
        for path in sorted(glob.glob(os.path.join(HERE, where, '*.json'))):
            name = '%s/%s' % (where, os.path.basename(path))
            for key, v in json.load(open(path, encoding='utf-8')).items():
                yield name, key, v


def main():
    bad = verify(texts())

    book = SV()
    stanzas = folded = numbered = en = sa = 0
    for n, _, _, declared in HYMNS:
        pid = str(n)
        bs = book.blocks(pid)
        pair, _, _, _ = pairing(bs)
        at = [i for i, b in enumerate(bs) if b['k'] in SA_KINDS]
        nums = {bs[i]['n'] for i in at if bs[i].get('n')}
        stanzas += len(at)
        folded += sum(1 for i in at if i in pair)
        numbered += len(nums)

        def say(what, count):
            print('гимн %d: %s — %d' % (n, what, count))

        if len(at) != declared:
            bad += 1
            say('строф %d, а во вступлении объявлено' % len(at), declared)
        if len(at) != sum(1 for i in at if i in pair):
            bad += 1
            say('строф без транслитерации', len(at) - sum(1 for i in at if i in pair))
        if len(at) != len(nums):
            bad += 1
            say('строф без номера', len(at) - len(nums))

        tr = book._tr(pid)
        en += len(tr[FROM_EN])
        sa += len(tr[FROM_SA])
        for where in (FROM_EN, FROM_SA):
            lost = sorted(set(tr[where]) - nums)
            if lost:
                bad += len(lost)
                print('гимн %d, %s/: перевод при несуществующей строфе: %s'
                      % (n, where, ', '.join(lost)))
        both = sorted(set(tr[FROM_EN]) & set(tr[FROM_SA]))
        if both:
            bad += len(both)
            print('гимн %d: строфа лежит и в ru/, и в sa/: %s' % (n, ', '.join(both)))

    print('строф %d, сложено с транслитерацией %d, с номером %d' % (stanzas, folded, numbered))
    print('переведено: с изложения %d, прямо с санскрита %d, всего %d из %d'
          % (en, sa, en + sa, stanzas))

    for f, k, v in texts():
        if isinstance(v, str) and not CYR.search(v):
            bad += 1
            print('%s строфа %s: перевод без кириллицы' % (f, k))
    print('расхождений всего: %d' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
