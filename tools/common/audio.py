#!/usr/bin/env python3
"""Озвучка терминов словаря: деванагари -> <раздел>/audio/<ключ>.mp3.

Читается **деванагари**, а не латиница: индийскому голосу это родное письмо, а
латинскую транслитерацию системный голос выговаривает по-английски — `rasa`
выходит «рэйсэ».

Написание берётся из столбца «Деванагари» самой страницы словаря, а не
переводится из IAST на лету. Так сделано нарочно: у Parātrīśikāvivaraṇa этот
перевод делает библиотека, и она обращает `ṁ` в ведический знак `ꣳ` — пять
файлов там пришлось переснимать вручную.

## Почему голосу дописывается висарга

Голос Lekha читает по правилам хинди, а хинди конечное краткое «а» глотает:
`शिव` он выговаривает «шив», `मद` — «мад». Померено:

    शिव   0,34 с      शिवः   0,58 с
    मद    0,38 с      मदः    0,55 с

Поэтому слову, кончающемуся согласной с призвуком «а», дописывается висарга —
и «а» возвращается. Это не подгонка под голос: `śivaḥ`, `rasaḥ`, `bhedaḥ` —
обычная словарная форма именительного падежа, ею слово и называют вслух.

Расплата одна, и её надо назвать: на странице стоит `śiva`, а голос говорит
`śivaḥ` — с лёгким придыханием на конце. Это сказано и в оговорке над таблицей.

## Почему часть файлов не синтезируется, а берётся у соседа

Словари раздела говорят об одном и том же и делят между собою десятки слов:
`tattva`, `śakti`, `mala` стоят в трёх из них. Написание на деванагари у них
одно, правило озвучки одно — значит и звук вышел бы тот же самый, байт в байт
(проверено: 37 общих файлов у /ksh/sv/ и /ksh/ta/ совпадают целиком).

Поэтому `borrow` называет уже озвученные словари, и оттуда файл копируется, а
не наговаривается заново. Сличается при этом не имя файла, а само написание на
деванагари: ключ выводится со снятой диакритикой, и совпасть он может у разных
слов. Разошлось написание — слово наговаривается своё.

Один и тот же звук ложится тогда в две папки. В репозитории это ничего не
стоит: git хранит одинаковые файлы одним объектом.

Нужен macOS (голос Lekha, hi_IN) и ffmpeg. Уже готовые файлы не
перезаписываются, так что после новой статьи скрипт можно прогнать целиком.
`--force` переснимает готовое, но занятое у соседа так и остаётся занятым:
переснимать нечего, звук там ровно тот же.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

VOICE, RATE = 'Lekha', 130

# <td class="skt" data-tts="bhakti">bhakti</td><td class="deva">भक्ति</td>
ROW = re.compile(r'data-tts="([^"]+)"[^>]*>[^<]+</td><td class="deva">([^<]+)<')

# Согласные деванагари. Кончается слово на такую — значит, при ней стоит
# призвук «а», который хинди и глотает.
CONSONANT = re.compile(r'[क-हक़-य़]$')
VISARGA = 'ः'


def spoken(deva):
    """Написание для голоса: та же строка, но с висаргой, если она нужна."""
    return deva + VISARGA if CONSONANT.search(deva) else deva


def synth(deva, dst):
    aiff = dst + '.aiff'
    subprocess.run(['say', '-v', VOICE, '-r', str(RATE), '-o', aiff, spoken(deva)],
                   check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', aiff,
                    '-ac', '1', '-ar', '22050', '-b:a', '48k', dst], check=True)
    os.remove(aiff)
    return os.path.getsize(dst)


def lent(borrow):
    """Уже озвученное у соседей: {(ключ, деванагари): путь к файлу}.

    Ключ и написание вместе, а не один ключ: диакритика при выводе ключа
    снимается, и `kalā` с `kāla` дали бы один и тот же. Совпасть должно
    написание — оно и есть то, что голос читает.
    """
    out = {}
    for page, folder in borrow:
        for key, deva in ROW.findall(open(page, encoding='utf-8').read()):
            path = os.path.join(folder, key + '.mp3')
            if os.path.exists(path):
                out.setdefault((key, deva), path)
    return out


def main(page, out, borrow=()):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--force', action='store_true', help='переснять уже готовые')
    args = ap.parse_args()

    rows = ROW.findall(open(page, encoding='utf-8').read())
    if not rows:
        sys.exit('в %s не нашлось ни одной статьи — словарь собран?' % page)
    os.makedirs(out, exist_ok=True)
    have = lent(borrow)

    made = kept = took = size = 0
    for key, deva in rows:
        dst = os.path.join(out, key + '.mp3')
        if os.path.exists(dst) and not args.force:
            kept += 1
        elif (key, deva) in have:
            shutil.copyfile(have[(key, deva)], dst)
            took += 1
        else:
            synth(deva, dst)
            made += 1
        size += os.path.getsize(dst)
    print('озвучено: %d, занято у соседей: %d, уже было: %d, всего %d КБ, '
          'висарга дописана %d раз'
          % (made, took, kept, round(size / 1024),
             sum(1 for _k, d in rows if CONSONANT.search(d))))
