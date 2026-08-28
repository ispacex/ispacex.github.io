#!/usr/bin/env python3
"""Пять проверок Mālinīvijayottaratantra. Каждая ломается тихо.

1. **Подстрочник не изменил текста.** Санскритское слово стоит над русским, а
   не скобкой в строке, но скобки никуда не делись — они в `<rp>`. Указатель
   поиска собирает Jekyll, снимая с абзаца теги, и строка обязана совпасть с
   прежней знак в знак. Проверка общая, `common/check.py`.
2. **Строф столько, сколько объявил источник.** Вступление к каждой главе
   называет их число словами («This eighth chapter consists of 135 stanzas»);
   на странице они лежат отдельно от этого счёта, и разойтись два счёта могут
   молча. Считается по последней строфе главы, а не по числу блоков: строфы у
   источника собраны в группы по одной-восьми.
3. **У каждой строфы есть её транслитерация.** Строфа и транслитерация
   приходят одним абзацем и разводятся надвое на разборе (`convert.py`), а
   обратно построчно их складывает `pairing`. Не сложилась пара — страница
   покажет две стены вместо строфы.

   Номера при этом требовать нельзя: строфы без номера на странице стоят
   законно — это цитаты из других писаний внутри пояснений, колофон и заголовок
   главы. Что ни одна **своя** строфа номера не потеряла, говорит проверка 2:
   счёт сплошной, и пропусти разбор строфу — последняя не сошлась бы с
   объявленной.
4. **Перевод лежит при существующем абзаце.** Ключ — «строфа/номер абзаца под
   нею», и от правки источника он не съезжает целиком, как съехал бы сквозной
   номер блока. Но съехать он всё же может: автор дописывает пояснение, и
   бывший второй абзац становится третьим. Ключ, которому на странице ничего не
   соответствует, — это перевод, которого никто никогда не увидит.
5. **Каждый перевод — по-русски.** Абзац без кириллицы значит, что туда попал
   санскрит или английский, а не перевод. Таблицы сюда не идут: они и есть
   вёрстка, и кириллица в них лежит по ячейкам.

   Исключение одно, и оно узнаётся само: строка, совпадающая с источником знак в
   знак. У Габриэля есть списки вида «Sakala = Sakalapramātā» — семь строк, в
   которых нет ни одного английского слова. Переводить в них нечего, и оставить
   их без перевода нельзя: непереведённый абзац страница честно показывает как
   английский, а английского в них нет. Совпадение целиком — это сказанное вслух
   «переводить нечего», и отличается оно от забытого абзаца тем, что забытого
   абзаца в `ru/*.json` попросту нет.
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.check import verify
from common.page import SA_KINDS, pairing
from book import MV
from convert import key, keys
from parts import CHAPTERS

CYR = re.compile(r'[А-Яа-яЁё]')


def source(book, pid):
    """Ключи главы и то, что стоит у источника под каждым из них.

    Ключ пункта списка длиннее ключа блока на номер пункта, ключ таблицы — на
    слово `html`, и проверкам 4 и 5 нужно одно и то же представление о том,
    какой ключ существует: одна считает по нему лишние переводы, другая ищет по
    нему строку, которую переводить нечего.
    """
    d = {}
    for b in book.blocks(pid):
        ks = keys(b)
        if b['k'] == 'list':
            d.update(zip(ks, b['items']))
        else:
            d.update(dict.fromkeys(ks, b.get('t', '')))
    return d


def texts():
    """(файл, ключ, перевод) по всем главам. Таблицы — не проза, их не берём."""
    for path in sorted(glob.glob(os.path.join(HERE, 'ru', '*.json'))):
        name = 'ru/%s' % os.path.basename(path)
        for k, v in json.load(open(path, encoding='utf-8')).items():
            if not k.endswith('/html'):
                yield name, k, v


def main():
    bad = verify(texts())

    book = MV()
    stanzas = folded = numbered = done = 0
    src = {}
    for _, n, _, _ in CHAPTERS:
        pid = str(n)
        bs = book.blocks(pid)
        head = json.load(open(os.path.join(HERE, 'blocks', '%s.json' % pid),
                              encoding='utf-8'))
        pair, _, _, _ = pairing(bs)
        at = [i for i, b in enumerate(bs) if b['k'] in SA_KINDS]
        nums = [bs[i] for i in at if bs[i].get('n')]
        stanzas += len(at)
        folded += sum(1 for i in at if i in pair)
        numbered += len(nums)

        def say(what):
            print('глава %s: %s' % (pid, what))

        # Последняя строфа главы — она же их число: счёт сплошной, а
        # полустрофа у источника считается половиной («35.5»), и вторая её
        # половина открывает следующую главу.
        last = max((int(b['to']) for b in nums), default=0)
        if head['stanzas'] and abs(head['stanzas'] - last) > 0.5:
            bad += 1
            say('последняя строфа %d, а во вступлении объявлено %s'
                % (last, head['stanzas']))
        lost = len(at) - sum(1 for i in at if i in pair)
        if lost:
            bad += 1
            say('строф без транслитерации: %d' % lost)

        keys = source(book, pid)
        src[pid] = keys
        tr = book._tr(pid)
        done += len(tr)
        gone = sorted(k for k in tr if k not in keys)
        if gone:
            bad += len(gone)
            say('перевод при несуществующем абзаце: %s' % ', '.join(gone))

    print('строф %d, сложено с транслитерацией %d, с номером %d'
          % (stanzas, folded, numbered))
    print('переведено абзацев: %d' % done)

    for f, k, v in texts():
        if isinstance(v, str) and not CYR.search(v):
            pid = os.path.splitext(f.split('/')[1])[0]
            if v.strip() == src.get(pid, {}).get(k, '').strip():
                continue
            bad += 1
            print('%s, %s: перевод без кириллицы' % (f, k))
    print('расхождений всего: %d' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
