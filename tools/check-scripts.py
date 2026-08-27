#!/usr/bin/env python3
"""Проверка: слово на странице — то самое слово, которое ищет читатель.

Ловятся две беды, у которых один исход. Слово можно **набрать двумя
алфавитами**: «А» и «A», «р» и «p», «ó» и «о́» на экране неразличимы, а для
поиска это разные строки. И слово можно **разорвать переносом** со страницы
бумажного исходника: в конце строки «соз-», в начале следующей «вездия».
В обоих случаях читатель видит слово, которого в тексте нет, и не находит его
**никаким** правильным запросом, не понимая, почему абзац не ищется.

    python3 tools/check-scripts.py

Чисто — печатает, сколько просмотрено, и выходит нулём. Иначе показывает
находки с местом и выходит единицей.

## Два алфавита

Свести их поиском нельзя — это значило бы объявить неразличимыми латиницу и
кириллицу вообще, — так что чинится оно только в тексте.

Ловится всё, что затесалось в русское слово, а не одна латиница: у «Шринґара»
украинская «ґ», у «Мріттикавата» — украинская «і», и не находятся они ровно так
же. Одинокое слово чужим алфавитом — не улика: «ӣ» в перечне гласных набрана
так нарочно.

Конвейеры /ksh/ подменённую букву правят сами (`unmix` в tools/common/parse.py)
и молчат там, где правило решить не может, — вот это здесь и всплывёт.
Написанные руками страницы правил не знают вовсе, и проверка у них одна: эта.

## Перенос посреди слова

Ломает он не один поиск. Перевод режет страницу на куски по пустым строкам, а
разорванное слово приносит с собой и разрыв абзаца: куском выходит обрывок
«вездия **Пушья**.», и переводить в нём нечего — отсюда реплики модели вместо
перевода (VS-45, VS-47). И по-русски абзац обрывается на полуслове.

Дефис в конце строки бывает и настоящим: «теле- и радиовещание». Отличает их
продолжение — перенос сращивается в слово, а за настоящим дефисом стоит
отдельное слово, и такие места проверка пропускает (`HANGING`). Ищется это
только на страницах: в `ru/*.json` строка не разбита на строки вовсе.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.parse import unmix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Что читатель видит: страницы сайта и русский перевод, который в них попадает.
# tools/*/src/ — скачанные страницы источника, их правит конвейер на лету.
PAGES = ('*.md', '*.html')
RUSSIAN = ('tools/*/ru/*.json',)

RU = set('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя')
# Знак ударения — часть слова, а не разрыв: «что́» одно слово, а не «что» и «ка».
WORD = re.compile(r'(?:[^\W\d_]|[\u0300-\u036f\u0483-\u0489])+')

# Хвост строки, оборванной переносом: буквы и дефис на самом краю.
TAIL = re.compile(r'[^\W\d_]+-$')
HEAD = re.compile(r'[^\W\d_]+')
# Слова, перед которыми дефис висит по праву: «теле- и радиовещание».
HANGING = ('и', 'или', 'а', 'но', 'да', 'либо')


def strangers(word):
    """Буквы не из русского алфавита в слове, где русские буквы есть.

    Считаются только буквы: знак над буквой — не алфавит («что́» русское слово
    с ударением), степень в «м²» — не буква и подавно.
    """
    if not any(c in RU for c in word):
        return []
    return [c for c in word if c not in RU and c.isalpha()]


def broken(lines, n):
    """Слово, срастающееся из строки `n` и продолжения, — или None.

    Продолжение ищется через пустую строку тоже: на месте разрыва страницы
    исходник её и оставил, и половины абзаца разошлись по разным кускам.
    """
    tail = TAIL.search(lines[n].rstrip())
    if not tail:
        return None
    nxt = next((s for s in (l.strip() for l in lines[n + 1:n + 3]) if s), '')
    head = HEAD.match(nxt)
    if not head or nxt.split(' ')[0].lower() in HANGING:
        return None
    return tail.group(0)[:-1] + head.group(0)


def look(name, text, report, breaks=None):
    lines = text.split('\n')
    for n, line in enumerate(lines):
        for m in WORD.finditer(line):
            w = m.group(0)
            if strangers(w):
                report(name, n + 1, w)
        if breaks is None:
            continue
        whole = broken(lines, n)
        if whole:
            breaks(name, n + 1, line.rstrip().split(' ')[-1], whole)


def files(globs):
    return subprocess.check_output(
        ['git', '-C', HERE, 'ls-files'] + list(globs), text=True).split()


def texts(obj):
    """Строки из ru/*.json — сам файл скрести нельзя: в нём есть \\t и \\u."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from texts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from texts(v)


def main():
    found, torn = [], []

    def report(name, n, w):
        found.append((name, n, w))
        fixed = unmix(w)
        hint = '→ %s' % fixed if fixed != w else '— правило не решает, нужен глаз'
        print('%s:%s: %s %s' % (name, n, w, hint))

    def breaks(name, n, half, whole):
        torn.append((name, n, whole))
        print('%s:%s: %s … → %s' % (name, n, half, whole))

    seen = files(PAGES)
    for name in seen:
        with open(os.path.join(HERE, name), encoding='utf-8') as fh:
            look(name, fh.read(), report, breaks)

    for name in files(RUSSIAN):
        seen.append(name)
        with open(os.path.join(HERE, name), encoding='utf-8') as fh:
            look(name, '\n'.join(texts(json.load(fh))), report)

    if found or torn:
        print('')
        if found:
            print('слов из двух алфавитов: %d' % len(found))
        if torn:
            print('слов, разорванных переносом: %d' % len(torn))
        return 1
    print('слов из двух алфавитов и разорванных переносом нет — '
          'просмотрено файлов: %d' % len(seen))
    return 0


if __name__ == '__main__':
    sys.exit(main())
