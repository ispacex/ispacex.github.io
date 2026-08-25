#!/usr/bin/env python3
"""Проверяет озвучку словаря на глаз, а не на слух: длительность против слогов.

Модель Parler не seed-ится и от запуска к запуску читает по-разному. Дурных
исходов два, и оба слышны сразу: слово обрывается на середине (`bhaṭṭāraka`
звучал как «бхат») или, наоборот, достраивается до фразы — модель обучена на
предложениях, и `tattva` вышла на шесть секунд вместо полутора. Слушать сотню
файлов после каждой пересъёмки некому, а в числах оба случая видны.

Мерка — секунды на слог, и пороги взяты не с потолка: они сняты со словаря
«Натьяшастры», где озвучка проверена на слух и признана годной. Там разброс
0,16–1,24 с/слог у Parler и 0,12–0,32 у системного голоса; здесь границы
чуть шире, чтобы проверка ловила брак, а не придиралась к чтению.

Односложные слова считаются отдельно: у `vāk` и `cit` на слог приходится
всё слово целиком, вместе с паузой на конце, и общая мерка их бракует зря.

    python3 check-audio.py

Молчит, когда всё в порядке; иначе печатает, что переснять, и возвращает 1.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
PAGE = os.path.join(REPO, 'ksh', 'pv', 'glossary', 'index.md')
SETS = (('parler', os.path.join('ksh', 'pv', 'audio', 'parler'), 0.14, 1.35, 2.2),
        ('системный', os.path.join('ksh', 'pv', 'audio'), 0.09, 0.45, 0.8))

ROW = re.compile(r'data-tts="([^"]+)"[^>]*>([^<]+)</td>')
# Слог считается по гласной; дифтонги ai и au — один слог, а не два.
VOWEL = re.compile(r'ai|au|[aāiīuūṛṝḷeo]')


def seconds(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                          '-of', 'csv=p=0', path], capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


def main():
    rows = ROW.findall(open(PAGE, encoding='utf-8').read())
    bad = []
    for name, folder, lo, hi, hi1 in SETS:
        for slug, iast in rows:
            path = os.path.join(REPO, folder, slug + '.mp3')
            if not os.path.exists(path):
                bad.append('%-10s %-14s файла нет' % (name, slug))
                continue
            n = max(1, len(VOWEL.findall(iast.lower())))
            per = seconds(path) / n
            top = hi1 if n == 1 else hi
            if per < lo:
                bad.append('%-10s %-14s %.2f с/слог — оборвано' % (name, slug, per))
            elif per > top:
                bad.append('%-10s %-14s %.2f с/слог — досочинено' % (name, slug, per))
    for line in bad:
        print(line)
    print('озвучка: %d файлов, всё в норме' % (2 * len(rows)) if not bad
          else 'переснять: %d' % len(bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
