#!/usr/bin/env python3
"""Проверяет, что подстрочник не изменил текста страницы.

Санскрит стоит над строкой, а не в скобке внутри неё, но скобки при этом
никуда не делись: они лежат в `<rp>`. На этом держится поиск по сайту —
`/search-index.json` собирает Jekyll, снимая с абзаца теги, и после
подстрочника строка обязана совпасть с прежней знак в знак.

Проверка дешёвая, а поломка тихая: разъедется указатель, а страница будет
выглядеть целой. Запускать после правок в render.py.
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render

TAG = re.compile(r'<[^>]*>')
NOTE = re.compile(r'--(.+?)--', re.S)


def plain(t):
    """Текст без разметки — то же, что оставит от абзаца strip_html."""
    return TAG.sub('', t)


def main():
    bad = ruby = paren = total = 0
    for path in sorted(glob.glob(os.path.join(HERE, 'ru', '*.json'))):
        for key, v in json.load(open(path, encoding='utf-8')).items():
            if not isinstance(v, str):
                continue
            total += 1
            out = render.markup(v)
            ruby += out.count('<ruby>')
            paren += out.count('pv-w')
            want = plain(NOTE.sub(lambda m: '— ' + m.group(1) + ' —', v))
            if plain(out) != want:
                bad += 1
                i = next((i for i, (a, b) in enumerate(zip(plain(out), want)) if a != b), 0)
                print('%s блок %s разошёлся:' % (os.path.basename(path), key))
                print('  было:  %r' % want[max(0, i - 60):i + 60])
                print('  стало: %r' % plain(out)[max(0, i - 60):i + 60])
            # Курсив автора не должен попадать внутрь подстрочника: открылся бы
            # снаружи, а закрылся внутри — и на странице остались бы голые
            # подчёркивания вместо наклонного текста.
            for m in re.finditer(r'<ruby>(.*?)</ruby>', out, re.S):
                if '_' in m.group(1):
                    bad += 1
                    print('%s блок %s: подчёркивание внутри подстрочника: %r'
                          % (os.path.basename(path), key, m.group(1)[:80]))
    print('абзацев %d, подстрочников %d, скобкой осталось %d' % (total, ruby, paren))
    print('расхождений: %d' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
