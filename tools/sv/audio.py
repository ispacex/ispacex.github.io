#!/usr/bin/env python3
"""Озвучивает термины словаря: деванагари -> ksh/sv/audio/<ключ>.mp3.

Читается **деванагари**, а не латиница: индийскому голосу это родное письмо, а
латинскую транслитерацию системный голос выговаривает по-английски — `rasa`
выходит «рэйсэ».

Написание берётся из столбца «Деванагари» самой страницы словаря, а не
переводится из IAST на лету. Так сделано нарочно: у соседнего конвейера
`indic-transliteration` переводит `ṁ` в ведический знак `ꣳ`, и пять файлов в
словаре Parātrīśikāvivaraṇa пришлось переснимать вручную. Здесь расходиться
нечему — читатель видит на странице ровно то, что читает голос.

    python3 audio.py            # сделать недостающие
    python3 audio.py --force    # переснять всё

Нужен macOS (голос Lekha, hi_IN) и ffmpeg. Уже готовые файлы не
перезаписываются, так что после новой статьи скрипт можно прогнать целиком.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'sv', 'glossary', 'index.md'))
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'sv', 'audio'))

VOICE, RATE = 'Lekha', 130

# <td class="skt" data-tts="bhakti">bhakti</td><td class="deva">भक्ति</td>
ROW = re.compile(r'data-tts="([^"]+)"[^>]*>[^<]+</td><td class="deva">([^<]+)<')


def synth(deva, dst):
    aiff = dst + '.aiff'
    subprocess.run(['say', '-v', VOICE, '-r', str(RATE), '-o', aiff, deva], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', aiff,
                    '-ac', '1', '-ar', '22050', '-b:a', '48k', dst], check=True)
    os.remove(aiff)
    return os.path.getsize(dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--force', action='store_true', help='переснять уже готовые')
    args = ap.parse_args()

    rows = ROW.findall(open(PAGE, encoding='utf-8').read())
    if not rows:
        sys.exit('в %s не нашлось ни одной статьи — словарь собран?' % PAGE)
    os.makedirs(OUT, exist_ok=True)

    made = kept = size = 0
    for slug, deva in rows:
        dst = os.path.join(OUT, slug + '.mp3')
        if os.path.exists(dst) and not args.force:
            kept += 1
            size += os.path.getsize(dst)
            continue
        size += synth(deva, dst)
        made += 1
    print('озвучено: %d, уже было: %d, всего %d КБ'
          % (made, kept, round(size / 1024)))


if __name__ == '__main__':
    main()
