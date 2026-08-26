#!/usr/bin/env python3
"""Проверяет перевод: сохранилось ли то, за что цепляется механика страницы.

    python3 tools/check-i18n.py

Перевод портит не текст, а **связь текста с механикой вокруг него**. Абзац
может быть переведён безупречно и при этом перестать работать: подстрочник
потеряет слово, фильтр словаря перестанет находить статью, поиск не найдёт
термин. Страница при этом выглядит целой — этим и опасно.

Отсюда правило, по которому написаны все проверки ниже: **где механика
цепляется за текст, там же и проверка.** Что ни с чем не связано — например,
название книги в прозе, — проверить нечем, и делать вид, что проверено, не
надо.

Проверяется пять вещей:

1. **Транслитерация в словарях не тронута.** Одно и то же слово стоит в статье
   дважды: в `data-tts="citi"` — внутри тега, а тег маскируется целиком и до
   модели не доходит, — и текстом в столбце «Санскрит», куда модель смотрит.
   Сличается **пара из перевода с парой из исходника**, а не половинки между
   собой: в словаре «Натьяшастры» они и по-русски разные — там `data-tts` это
   имя звукового файла, с которого диакритика снята нарочно. Проверять надо
   «не изменилось ли», а не «одинаково ли»; первая же попытка перепутала это и
   выдала 422 расхождения на ровном месте.
2. **Пометы целы — там, где на них что-то держится.** Последовательность
   санскритских помет в скобках должна совпасть с исходной: из них собирается
   подстрочник. Но собирается он только на страницах писаний; на рукописных
   скобка — обычная скобка, и добавленная моделью «(movements)» там ничего не
   ломает. Поэтому расхождения показываются везде, а роняют проверку только
   там, где подстрочник и правда есть.
3. **Разметка цела.** Ссылок, разделителей таблицы и полужирных — поровну.
4. **Ничего не осталось по-русски.** Кусок, вернувшийся без меток, конвейер
   оставляет русским нарочно — лучше по-русски, чем испорченным. Но знать,
   сколько таких, надо.
5. **У каждой английской страницы есть русская.** Иначе перевод пережил
   страницу, которой больше нет.

Страницы-заместители (те, у кого во front matter стоит `source:`) проверяются
иначе, и по тому же правилу. Своего текста у них нет — сличать нечего; вся их
работа держится на двух ссылках: на подлинник у источника и на русскую
страницу, за которой читатель шёл. Их и проверяем.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EN = os.path.join(ROOT, 'en')

CYR = re.compile(r'[А-Яа-яЁё]')
# Та же помета, что маскируется при переводе (см. KEEP в common/translate.py).
MARK = re.compile(r'\([A-Za-zĀ-ſḀ-ỿ\'\-\s.…|]+\)')
ROW = re.compile(r'data-tts="([^"]+)"[^>]*>([^<]*)</td>')
LINK = re.compile(r'\]\((?:/|https?://)[^)]*\)')
SOURCE = re.compile(r'^source:\s*(\S+)\s*$', re.M)
RU = re.compile(r'^ru:\s*(\S+)\s*$', re.M)
TITLE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.M)
BOLD = re.compile(r'\*\*')
CELL = re.compile(r'</t[dh]>')


def pairs():
    """(английская страница, её русский исходник)."""
    out = []
    for base, dirs, files in os.walk(EN):
        for f in sorted(files):
            if f.endswith('.md'):
                en = os.path.relpath(os.path.join(base, f), EN)
                out.append((en, os.path.join(ROOT, en)))
    return out


def main():
    bad = 0
    rows = pairs()
    if not rows:
        print('в /en/ ничего нет — сперва python3 tools/translate.py')
        return 1

    lost_pages, missing, tts_bad, mark_bad, mark_soft, markup_bad = [], [], [], [], [], []
    stubs, stub_bad, stub_ru_title = [], [], []
    for en_rel, ru_path in rows:
        en_path = os.path.join(EN, en_rel)
        en = open(en_path, encoding='utf-8').read()
        if not os.path.exists(ru_path):
            missing.append(en_rel)
            continue
        ru = open(ru_path, encoding='utf-8').read()

        # Страница-заместитель: текста нет, есть две ссылки, и обе обязаны быть
        # на месте. Пропала ссылка на подлинник — страница стала тупиком;
        # пропала ссылка на русскую — читатель, шедший за главой, её не найдёт.
        src = SOURCE.search(en)
        if src:
            stubs.append(en_rel)
            back = RU.search(en)
            if src.group(1) not in en[src.end():]:
                stub_bad.append((en_rel, 'нет ссылки на подлинник'))
            if not back:
                stub_bad.append((en_rel, 'нет обратного адреса'))
            elif '](%s)' % back.group(1) not in en:
                stub_bad.append((en_rel, 'нет ссылки на русскую страницу'))
            t = TITLE.search(en[:en.index('---', 4)] if '---' in en[4:] else en)
            if t and CYR.search(t.group(1)):
                stub_ru_title.append((en_rel, t.group(1)))
            continue

        # 1. Транслитерация: пара из перевода против пары из исходника.
        was = dict(ROW.findall(ru))
        for tts, shown in ROW.findall(en):
            if tts in was and shown.strip() != was[tts].strip():
                tts_bad.append((en_rel, tts, was[tts].strip(), shown.strip()))

        # 2. Пометы. Роняют проверку только там, где из них строится
        # подстрочник, — на страницах писаний.
        a, b = MARK.findall(ru), MARK.findall(en)
        if a != b:
            at = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            row = (en_rel, len(a), len(b),
                   a[at] if at < len(a) else '—', b[at] if at < len(b) else '—')
            (mark_bad if 'pv-tr' in ru or 'pv-pair' in ru else mark_soft).append(row)

        # 3. Разметка. Ссылки и ячейки обязаны совпасть числом: потерянная
        # ссылка — потерянная страница, потерянная ячейка — разъехавшаяся
        # таблица. С полужирным иначе: важно не «столько же», а «парно».
        # Непарная звёздочка выводит на страницу саму себя; лишняя пара —
        # только вопрос вкуса.
        for pat, what in ((LINK, 'ссылок'), (CELL, 'ячеек')):
            x, y = len(pat.findall(ru)), len(pat.findall(en))
            if x != y:
                markup_bad.append((en_rel, what, x, y))
        # Сличается **чётность до и после**, а не сама чётность: на
        # `art/index.md` звёздочка непарна и по-русски, и перевод тут ни при
        # чём. Проверять надо «не испортил ли перевод», а не «хорошо ли
        # написано».
        x, y = len(BOLD.findall(ru)), len(BOLD.findall(en))
        if x % 2 != y % 2:
            markup_bad.append((en_rel, 'звёздочка потерялась', x, y))

        # 4. Осталось по-русски.
        body = re.sub(r'\A---\n.*?\n---\n', '', en, flags=re.S)
        left = [b for b in re.split(r'\n\s*\n', body) if CYR.search(b)]
        if left:
            lost_pages.append((en_rel, len(left)))

    print('страниц переведено: %d, из них со ссылкой на подлинник: %d'
          % (len(rows), len(stubs)))

    print('\nу заместителя порвана ссылка: %d' % len(stub_bad))
    for rel, why in stub_bad[:20]:
        print('   %-34s %s' % (rel, why))

    print('\nзаголовок заместителя остался русским: %d' % len(stub_ru_title))
    for rel, t in stub_ru_title[:10]:
        print('   %-34s %s' % (rel, t))

    print('\nбез русского исходника: %d' % len(missing))
    for x in missing:
        print('   %s' % x)

    print('\nтранслитерация тронута: %d' % len(tts_bad))
    for rel, tts, was, now in tts_bad[:20]:
        print('   %-30s %s: было «%s», стало «%s»' % (rel, tts, was, now))

    print('\nпометы разошлись там, где на них держится подстрочник: страниц %d'
          % len(mark_bad))
    for rel, x, y, a, b in mark_bad[:20]:
        print('   %-34s было %d, стало %d; первое: «%s» → «%s»' % (rel, x, y, a, b))

    print('\nскобки прибавились там, где они просто скобки: страниц %d, всего %d'
          % (len(mark_soft), sum(y - x for _r, x, y, _a, _b in mark_soft if y > x)))
    for rel, x, y, _a, b in sorted(mark_soft, key=lambda r: r[1] - r[2])[:8]:
        print('   %-34s было %d, стало %d; например «%s»' % (rel, x, y, b))

    print('\nразметка разошлась: %d' % len(markup_bad))
    for rel, what, x, y in markup_bad[:20]:
        print('   %-34s %s: было %d, стало %d' % (rel, what, x, y))

    print('\nосталось по-русски: страниц %d, кусков %d'
          % (len(lost_pages), sum(n for _, n in lost_pages)))
    for rel, n in sorted(lost_pages, key=lambda x: -x[1])[:10]:
        print('   %-34s %d' % (rel, n))

    bad = len(missing) + len(tts_bad) + len(mark_bad) + len(markup_bad) + len(stub_bad)
    print('\n%s' % ('расхождений нет' if not bad else 'расхождений: %d' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
