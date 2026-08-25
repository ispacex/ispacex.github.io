#!/usr/bin/env python3
"""Проверка: ни одно русское слово на сайте не набрано двумя алфавитами.

«А» и «A», «р» и «p», «ó» и «о́» на экране неразличимы, а для поиска это разные
строки: слово с подменённой буквой не находится **никаким** правильным
запросом, и читатель не поймёт, почему абзац не ищется. Свести их поиском
нельзя — это значило бы объявить неразличимыми латиницу и кириллицу вообще, —
так что чинится оно только в тексте.

    python3 tools/check-scripts.py

Чисто — печатает, сколько просмотрено, и выходит нулём. Иначе показывает
слова с местом и выходит единицей.

Ловится всё, что затесалось в русское слово, а не одна латиница: у «Шринґара»
украинская «ґ», у «Мріттикавата» — украинская «і», и не находятся они ровно так
же. Одинокое слово чужим алфавитом — не улика: «ӣ» в перечне гласных набрана
так нарочно.

Конвейеры /ksh/ подменённую букву правят сами (`unmix` в tools/common/parse.py)
и молчат там, где правило решить не может, — вот это здесь и всплывёт.
Написанные руками страницы правил не знают вовсе, и проверка у них одна: эта.
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


def strangers(word):
    """Буквы не из русского алфавита в слове, где русские буквы есть.

    Считаются только буквы: знак над буквой — не алфавит («что́» русское слово
    с ударением), степень в «м²» — не буква и подавно.
    """
    if not any(c in RU for c in word):
        return []
    return [c for c in word if c not in RU and c.isalpha()]


def look(name, text, report):
    for n, line in enumerate(text.split('\n'), 1):
        for m in WORD.finditer(line):
            w = m.group(0)
            if strangers(w):
                report(name, n, w)


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
    found = []

    def report(name, n, w):
        found.append((name, n, w))
        fixed = unmix(w)
        hint = '→ %s' % fixed if fixed != w else '— правило не решает, нужен глаз'
        print('%s:%s: %s %s' % (name, n, w, hint))

    seen = files(PAGES)
    for name in seen:
        with open(os.path.join(HERE, name), encoding='utf-8') as fh:
            look(name, fh.read(), report)

    for name in files(RUSSIAN):
        seen.append(name)
        with open(os.path.join(HERE, name), encoding='utf-8') as fh:
            look(name, '\n'.join(texts(json.load(fh))), report)

    if found:
        print('\nслов из двух алфавитов: %d' % len(found))
        return 1
    print('слов из двух алфавитов нет — просмотрено файлов: %d' % len(seen))
    return 0


if __name__ == '__main__':
    sys.exit(main())
