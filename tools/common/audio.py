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

Нужен macOS (голос Lekha, hi_IN) и ffmpeg. Уже готовые файлы не
перезаписываются, так что после новой статьи скрипт можно прогнать целиком.
"""
import argparse
import os
import re
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


def main(page, out):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--force', action='store_true', help='переснять уже готовые')
    args = ap.parse_args()

    rows = ROW.findall(open(page, encoding='utf-8').read())
    if not rows:
        sys.exit('в %s не нашлось ни одной статьи — словарь собран?' % page)
    os.makedirs(out, exist_ok=True)

    made = kept = size = 0
    for key, deva in rows:
        dst = os.path.join(out, key + '.mp3')
        if os.path.exists(dst) and not args.force:
            kept += 1
            size += os.path.getsize(dst)
            continue
        size += synth(deva, dst)
        made += 1
    print('озвучено: %d, уже было: %d, всего %d КБ, висарга дописана %d раз'
          % (made, kept, round(size / 1024),
             sum(1 for _k, d in rows if CONSONANT.search(d))))
