#!/usr/bin/env python3
"""Собирает страницу Jekyll из блоков, разобранных common/parse.py.

Вёрстка у Габриэля Pradīpaka одна на все писания, и страница из неё собирается
тоже одна и та же: заголовок раздела, стена строф, перевод. Что меняется от
писания к писанию — адреса, названия и то, откуда берётся русский текст, —
собрано в классе Book: у Parātrīśikāvivaraṇa перевод лежит в ru/*.json, потому
что делался здесь, у «Тантрасары» он приходит вместе с блоками, потому что у
источника уже есть.
"""
import json, os, re

# Санскритское слово в скобках внутри перевода: латиница с диакритикой и без
# кириллицы. После перевода вокруг него стоит русский текст, поэтому спутать
# его с обычной скобкой нельзя.
#
# Пробел перед скобкой забираем вместе с ней: он вернётся внутри <rp>, и
# снятая с тегов строка совпадёт с прежней знак в знак — на этом держится
# поисковый указатель.
GLOSS = re.compile(r'[  ]*\(([^()]*?)\)')
CYR = re.compile(r'[А-Яа-яЁё]')
DIAC = re.compile(r'[āīūṛṝḷḹṭḍṇśṣñṅṁṃḥĀĪŪṚṬḌṆŚṢÑṄṀṂḤ]')
WORD = re.compile(r'[^\W\d_]', re.U)

# Докуда основа подстрочника тянется влево. За точкой, двоеточием или чертой
# стоит уже другая фраза; `_` и `*` — края авторской вставки `_(…)_` и
# полужирного заголовка, которые переводом санскритского слова не являются;
# `>` — конец вставленного тега; перевод строки — граница строки заголовка, а
# подстрочник, перешагнувший её, унёс бы `<br />` внутрь подписываемого слова.
EDGE = re.compile(r'[.;:!?|_*>»\n]')

# Длиннее этого основу не берём. Подпись стоит по середине основы, и основа в
# пол-абзаца увела бы её от слова, к которому она относится.
MAX_BASE = 48


def is_sanskrit(inner):
    inner = inner.strip()
    if not inner or CYR.search(inner):
        return False
    # Санскрит узнаётся по диакритике IAST либо по тому, что это одно
    # латинское слово: «(ca)», «(mahā)», «(tad-ubhaya-yāmala)».
    return bool(DIAC.search(inner) or re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", inner))


def cut(span):
    """Делит текст перед глоссом на строку и основу подстрочника."""
    edge = 0
    for m in EDGE.finditer(span):
        if span[m.end():].strip():
            edge = m.end()
    # Ближайшая граница слова справа: основа начинается со слова целиком.
    if len(span) - edge > MAX_BASE:
        j = span.find(' ', len(span) - MAX_BASE)
        if j != -1:
            edge = j + 1
    # Тег в основе означает, что она захватила чужую разметку. Уточнение
    # Габриэля `--букв. …--` уже стало <span>, и его `</span>` стоит вплотную
    # перед скобкой: подстрочник закрывал бы span внутри себя, а открылся бы
    # тот снаружи. Отодвигаем границу за последний тег; если слова за ним не
    # осталось, скобка останется скобкой в строке — это честнее сломанной
    # вёрстки, из-за которой в поисковый указатель уезжает «</span>».
    lt = span.rfind('<', edge)
    if lt != -1:
        gt = span.find('>', lt)
        edge = gt + 1 if gt != -1 else len(span)
    # Запятая и тире, с которых начинается кусок, к подписи не относятся:
    # их место в строке, а не под ней.
    base = span[edge:]
    edge += len(base) - len(base.lstrip('  ,;:—–-_'))
    return span[:edge], span[edge:]


def gloss(t):
    """Санскрит — подстрочником над своим словом, а не скобкой в строке.

    `<rp>` держит скобки для тех, кто подстрочник не рисует, и заодно для
    указателя поиска: `strip_html` оставляет от подстрочника ровно ту строку,
    что стояла до него.
    """
    # `bar` — левая граница, за которую основа не заходит: за ней осталась
    # скобка, которую мы не тронули. Затяни её в основу — и `_(…)_` разорвётся
    # пополам: курсив открылся снаружи подстрочника, а закрылся внутри.
    out, pos, bar = [], 0, 0
    for m in GLOSS.finditer(t):
        ws = m.group(0)[:m.group(0).index('(')]
        op = m.start() + len(ws)
        # `_(Bhairava)_` — не глосс, а вставка Габриэля: он подставляет слово,
        # которое в санскрите стоит местоимением. Подписывать ею нечего.
        insert = t[op - 1:op] == '_' and t[m.end():m.end() + 1] == '_'
        if insert or not is_sanskrit(m.group(1)):
            bar = m.end()     # русская скобка — часть строки, её не трогаем
            continue
        keep, base = cut(t[bar:m.start()])
        keep = t[pos:bar] + keep
        pos = bar = m.end()
        # Подпись, которая вдвое длиннее подписываемого, подстрочником быть
        # перестаёт: перечисление в сотню знаков над словом «звуков» растянет
        # строку шире экрана. Такое остаётся скобкой в строке, как было.
        g = m.group(1)
        if len(g) > 24 and len(g) > 2 * len(base.strip()):
            keep, base = keep + base, ''
        if not WORD.search(base):
            # Подписывать нечего: два глосса подряд, начало абзаца, конец
            # авторской вставки. Оставляем скобку как была, вместе с пробелом
            # перед ней — его забрал разбор, и без него слова слипнутся.
            out.append(keep + base + ws + '<span class="pv-w">(%s)</span>' % m.group(1))
            continue
        out.append(keep)
        # Пробел уходит внутрь <rp>: со снятыми тегами строка обязана совпасть
        # с прежней знак в знак, иначе разойдётся поисковый указатель.
        out.append('<ruby>%s<rp>%s(</rp><rt>%s</rt><rp>)</rp></ruby>'
                   % (base, ws, m.group(1)))
    out.append(t[pos:])
    return ''.join(out)


def markup(t):
    """Внутристрочная разметка: санскрит подстрочником и вставки автора."""
    t = re.sub(r'--(.+?)--', lambda m: '<span class="pv-note">— ' + m.group(1) + ' —</span>', t, flags=re.S)
    return gloss(t)


def bold(t):
    """`**…**` → тег, а не звёздочки на странице.

    Внутри стены строф markdown не работает: строфа стоит в <span> без
    `markdown="1"`, потому что kramdown разобрал бы её вертикальные черты как
    таблицу. У «Тантрасары» заголовок главы набран в источнике полужирным и
    попадает как раз туда.

    Полужирный, открытый на одной строке и закрытый на другой, закрывается на
    каждом переводе строки и открывается снова: строки стены расходятся по
    разным <span>, и тег, перешагнувший границу, оставил бы их незакрытыми.
    """
    return re.sub(r'\*\*(.+?)\*\*',
                  lambda m: '<strong>%s</strong>' % m.group(1).replace('\n', '</strong>\n<strong>'),
                  t, flags=re.S)


def para(t, cls=None, anchor=None):
    t = markup(t).replace('\n', '<br />\n')
    if cls:
        return '<p class="%s"%s markdown="1">%s</p>' % (mark(cls, anchor), ident(anchor), t)
    # Обычный абзац разметки обёртки не имеет, и якорь ему ставится
    # блочным IAL — своего тега, к которому можно приписать id, у него нет.
    return t + ('\n{: #%s .pv-anchor}' % anchor if anchor else '')

def ident(anchor):
    return ' id="%s"' % anchor if anchor else ''

def mark(cls, anchor):
    """Класс якорного абзаца: по нему держится отступ от верха окна."""
    return cls + ' pv-anchor' if anchor else cls

def sanskrit(t, cls, anchor=None):
    return '<p class="%s"%s lang="sa">%s</p>' % (mark(cls, anchor), ident(anchor),
                                                 bold(t).replace('\n', '<br />\n'))

def iast(t, cls, anchor=None):
    # Разбор изредка относит к транслитерации абзац, который на деле —
    # пояснение Габриэля с курсивом. Без markdown="1" курсив в нём остаётся
    # голыми подчёркиваниями прямо на странице.
    md = ' markdown="1"' if '_' in t else ''
    return '<p class="%s"%s%s>%s</p>' % (mark(cls, anchor), ident(anchor), md,
                                         bold(t).replace('\n', '<br />\n'))


# Страница устроена одинаково: заголовок раздела, затем стена строф и только
# потом перевод — по три-четыре десятка абзацев каждая. Читателю, которому
# нужен перевод, иначе пришлось бы пролистать их все, поэтому у каждого раздела
# метится начало его частей. Транслитерация своей части больше не имеет: она
# стоит в тех же абзацах, что и деванагари (см. pairing).
SA_KINDS = ('deva', 'deva-red')

DEVA = re.compile(r'[ऀ-ॿ]')


def lines(t):
    return [l for l in t.split('\n') if l.strip()]


def looks_iast(b):
    """Похож ли блок на ту же строфу в транслитерации.

    Разбор изредка относит строку транслитерации к обычному тексту — «iti|»,
    «Taduktam spande», — и стена от этого обрывается на середине. Поэтому вид
    блока здесь не единственный признак: важнее, что в блоке нет ни кириллицы,
    ни деванагари и нет скобки. Скобка — верный признак перевода: в переводе
    Габриэля в скобке стоит санскритское слово при каждом русском, а в самой
    транслитерации скобок не бывает вовсе.
    """
    t = b.get('t')
    if t is None or b['k'] not in ('iast', 'text'):
        return False
    return not CYR.search(t) and not DEVA.search(t) and '(' not in t


def pairing(blocks):
    """Строфа деванагари и та же строфа в транслитерации — рядом, а не стенами.

    Источник даёт их двумя стенами: сперва весь санскрит раздела, потом весь
    он же в транслитерации. Читать это построчно нельзя — приходится листать
    туда-сюда. Стены складываются здесь: k-й блок первой к k-му блоку второй.

    Складывается только то, что сошлось: у пары должны совпасть и признак
    центрирования, и число строк. Первое же расхождение обрывает складывание —
    дальше стена остаётся стеной. Так страница, где транслитерации нет вовсе
    (таблицы соответствий), просто остаётся как была, а не съезжает на строку.
    """
    pair, eaten, opens, group = {}, set(), {}, {}
    i = 0
    while i < len(blocks):
        if blocks[i]['k'] not in SA_KINDS:
            i += 1
            continue
        j = i
        while j < len(blocks) and blocks[j]['k'] in SA_KINDS:
            j += 1
        n = 0
        while n < j - i and j + n < len(blocks):
            sa, ia = blocks[i + n], blocks[j + n]
            if not looks_iast(ia) or ia.get('c') != sa.get('c'):
                break
            if len(lines(ia['t'])) != len(lines(sa['t'])):
                break
            n += 1
        if n:
            g = 'w%d' % (len(opens) + 1)
            opens[i] = g
            for x in range(n):
                pair[i + x] = j + x
                group[i + x] = g
                eaten.add(j + x)
        i = j + n
    return pair, eaten, opens, group


def stanza(sa, ia, cls, group, anchor=None):
    """Строфа: строка деванагари, под ней та же строка в транслитерации.

    Всё это один абзац, а не четыре: сборщик указателя режет страницу по
    пустым строкам, и строфа должна остаться одной находкой, а не рассыпаться
    на строки. Заодно её теперь находит и запрос в транслитерации.
    """
    rows = []
    # Полужирный снимается со всей строфы разом, а не со строки: заголовок
    # главы у «Тантрасары» открыт на первой строке и закрыт на второй.
    for d, t in zip(lines(bold(sa['t'])), lines(bold(ia['t']))):
        rows.append('<span class="%s" lang="sa">%s</span>' % (cls, d))
        rows.append('<span class="pv-iast">%s</span>' % t)
    return '<p class="pv-pair%s"%s data-pv="%s">%s</p>' % (
        ' pv-c' if sa.get('c') else '', ident(anchor), group, '<br />\n'.join(rows))


def copybar(group, anchor=None):
    """Кнопки над стеной: забрать её санскрит или её транслитерацию целиком.

    `nosearch` — чтобы кнопки не попали в поиск отдельной находкой.
    """
    return ('<p class="pv-copy nosearch%s"%s>'
            '<button type="button" data-pv-copy="%s" data-pv-what="pv-sa">Копировать санскрит</button> '
            '<button type="button" data-pv-copy="%s" data-pv-what="pv-iast">Копировать транслитерацию</button>'
            '</p>') % (' pv-anchor' if anchor else '', ident(anchor), group, group)


def sections(blocks, tr):
    """Разделы страницы и якорные блоки внутри каждого."""
    starts = [i for i, b in enumerate(blocks) if b['k'] in ('h3', 'h4')]
    out = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(blocks)
        sec = {'head': i, 'id': 's%d' % (n + 1), 'sa': None, 'iast': None, 'ru': None}
        for j in range(i + 1, end):
            k = blocks[j]['k']
            if sec['sa'] is None and k in SA_KINDS:
                sec['sa'] = j
            elif sec['iast'] is None and k == 'iast':
                sec['iast'] = j
        # Начало перевода — первый достаточно длинный русский абзац после
        # санскритской стены. Порог нужен: между абзацами IAST попадаются
        # коротыши вроде «iti|», которые разбором признаны обычным текстом.
        after = max(x for x in (i, sec['sa'], sec['iast']) if x is not None)
        for j in range(after + 1, end):
            b = blocks[j]
            if b['k'] != 'text':
                continue
            v = tr(j, b) or ''
            # Кириллицы должно быть много: среди абзацев попадается IAST,
            # который разбор счёл текстом, и «перевод» у него — он же сам.
            if len(v) >= 120 and len(CYR.findall(v)) >= 60:
                sec['ru'] = j
                break
        # Во «Введении» санскритской стены нет: там одна строка IAST и четыре
        # абзаца пояснений, делить их на части незачем.
        if sec['sa'] is None:
            sec['iast'] = sec['ru'] = None
        if sec['ru'] is None and sec['sa'] is not None:
            for j in range(after + 1, end):
                if blocks[j]['k'] == 'text':
                    sec['ru'] = j
                    break
        out.append(sec)
    return out


def nav(secs, titles):
    """Оглавление страницы: раздел, а рядом — три его части.

    Строки разделены `<br />`, а не пустой строкой: пустая строка для сборщика
    указателя — граница абзаца, и оглавление попало бы в поиск по кускам.
    """
    if len(secs) < 2:
        return ''
    rows = ['**На этой странице**']
    for sec in secs:
        row = '[%s](#%s)' % (titles[sec['head']], sec['id'])
        parts = [('санскрит', 'sa'), ('транслитерация', 'iast'), ('перевод', 'ru')]
        links = ['[%s](#%s-%s)' % (name, sec['id'], key)
                 for name, key in parts if sec[key] is not None]
        if links:
            row += ' — ' + ' · '.join(links)
        rows.append(row)
    return ('<div class="pv-nav nosearch" markdown="1">\n%s\n</div>'
            % '<br />\n'.join(rows))


def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


class Book:
    """Что отличает одно писание от другого. Всё прочее — общее.

    `key`     — каталог под /ksh/, он же корень адресов;
    `name`    — как писание зовётся в заголовках и хлебных крошках;
    `parts`   — [(id у источника, кусок адреса, название)] по порядку;
    `src_url` — id → путь страницы у источника.
    """
    key = ''
    name = ''
    parts = ()
    src = 'https://www.sanskrit-trikashaivism.com/ru/'
    src_url = {}
    home_name = 'Введение'
    copy_js = True

    def __init__(self, here):
        self.here = here
        self.out = os.path.normpath(os.path.join(here, '..', '..', 'ksh', self.key))

    # --- адреса и подписи ---

    def home(self):
        return '/ksh/%s/' % self.key

    def url(self, slug):
        return '/ksh/%s/%s/' % (self.key, slug)

    def at_source(self, pid):
        return self.src + self.src_url[pid]

    def page_title(self, name):
        return '%s: %s' % (self.name, name.lower())

    def footer(self, pid, name):
        raise NotImplementedError

    # --- откуда берётся русский текст ---

    def blocks(self, pid):
        path = os.path.join(self.here, 'blocks', '%s.json' % pid)
        return json.load(open(path, encoding='utf-8'))['blocks']

    def load(self, pid):
        """Всё, что нужно для перевода этой страницы. Возвращает tr(i, block)."""
        raise NotImplementedError

    def item(self, pid, i, j, text):
        """Перевод j-го пункта списка в блоке i, или None."""
        return None

    def table(self, pid, i, html):
        """Готовая таблица вместо разобранной, или None."""
        return None

    # --- предупреждение о непереведённом ---

    def nav(self, secs, titles):
        return nav(secs, titles)

    def heading(self, tag, title, anchor):
        """Заголовок раздела внутри страницы. Пустая строка — раздела не будет."""
        return ('## ' if tag == 'h3' else '### ') + title + (' {#%s}' % anchor if anchor else '')

    def todo(self, n):
        return ('<p class="pv-todo">Эта часть переведена ещё не полностью: %d %s ниже '
                'стоят по-английски — так, как они у источника. Санскрит и транслитерация '
                'на месте.</p>' % (n, plural(n, 'абзац', 'абзаца', 'абзацев')))


def render(book, pid, slug, name, idx):
    blocks = book.blocks(pid)
    lookup = book.load(pid)

    missing = []
    def tr(i, b):
        v = lookup(i, b)
        if v is None:
            missing.append((i, b['t']))
        return v

    secs = sections(blocks, lookup)
    pair, eaten, opens, group = pairing(blocks)
    # Сложенной стене отдельного якоря на транслитерацию не нужно: она стоит
    # в тех же абзацах, что и деванагари, и ссылка вела бы туда же.
    for sec in secs:
        if sec['sa'] in pair:
            sec['iast'] = None
    at = {}
    titles = {}
    for sec in secs:
        for key in ('sa', 'iast', 'ru'):
            if sec[key] is not None:
                at[sec[key]] = '%s-%s' % (sec['id'], key)
        at.setdefault(sec['head'], sec['id'])

    body = []
    for i, b in enumerate(blocks):
        k = b['k']
        a = at.get(i)
        if k == 'rule':
            body.append('<hr class="pv-rule" />')
        elif k in ('h3', 'h4'):
            v = tr(i, b)
            titles[i] = v or b['t']
            head_md = book.heading(k, titles[i], a)
            if not head_md:
                continue
            body.append(head_md)
            if v is None:
                body[-1] += ' <span class="pv-en">(не переведено)</span>'
        elif k in SA_KINDS and i in pair:
            if i in opens:
                body.append(copybar(opens[i], a))
                a = None
            body.append(stanza(b, blocks[pair[i]],
                               'pv-sa pv-src' if k == 'deva-red' else 'pv-sa', group[i], a))
        elif i in eaten:
            continue
        elif k == 'deva':
            body.append(sanskrit(b['t'], 'pv-sa' + (' pv-c' if b.get('c') else ''), a))
        elif k == 'deva-red':
            body.append(sanskrit(b['t'], 'pv-sa pv-src' + (' pv-c' if b.get('c') else ''), a))
        elif k == 'iast':
            body.append(iast(b['t'], 'pv-iast' + (' pv-c' if b.get('c') else ''), a))
        elif k == 'text':
            v = tr(i, b)
            if v is None:
                # Ещё не переведено: показываем как у источника и помечаем, а не
                # выдаём английский абзац за русский.
                body.append('<p class="%s"%s lang="en">%s</p>'
                            % (mark('pv-en', a), ident(a), markup(b['t']).replace('\n', '<br />\n')))
            else:
                body.append(para(v, 'pv-tr' if b.get('c') else None, a))
        elif k == 'list':
            items = [book.item(pid, i, j, x) or x for j, x in enumerate(b['items'])]
            if any(book.item(pid, i, j, x) is None for j, x in enumerate(b['items'])):
                missing.append((i, '|'.join(b['items'])[:80] + ' [список]'))
            body.append('\n'.join(('%d. ' % (j + 1) if b['ordered'] else '* ') + x
                                  for j, x in enumerate(items)))
        elif k == 'table':
            v = book.table(pid, i, b['html'])
            if v is None:
                missing.append((i, '[таблица]'))
                v = '<table>%s</table>' % b['html']
            body.append(v)

    missing_note = book.todo(len(missing)) if missing else ''

    prev_link = ('[← %s](%s)' % (book.parts[idx - 1][2], book.url(book.parts[idx - 1][1]))
                 if idx > 0 else '[← %s](%s)' % (book.home_name, book.home()))
    next_link = ('[%s →](%s)' % (book.parts[idx + 1][2], book.url(book.parts[idx + 1][1]))
                 if idx + 1 < len(book.parts) else '')

    head = [
        '---\ntitle: "%s"\n---' % book.page_title(name),
        '<p class="pv-crumbs nosearch" markdown="1">[КШ](/ksh/) · [%s](%s) · '
        '[Поиск по сайту](/search/) · [Эта часть у источника](%s)</p>'
        % (book.name, book.home(), book.at_source(pid)),
        '',
        '# %s' % name,
        '',
        '<p class="pv-pager nosearch" markdown="1">%s%s</p>' % (prev_link, ' · ' + next_link if next_link else ''),
        '',
    ]
    page_nav = book.nav(secs, titles)
    if page_nav:
        head.append(page_nav)
        head.append('')
    if missing_note:
        head.append(missing_note)
        head.append('')
    tail = [
        '',
        '<p class="pv-pager nosearch" markdown="1">%s%s</p>' % (prev_link, ' · ' + next_link if next_link else ''),
        '',
        '---',
        '',
        book.footer(pid, name),
    ]

    if pair and book.copy_js:
        tail.append('<script src="/assets/js/pv-copy.js"></script>')

    text = '\n\n'.join(head + body + tail)
    text = re.sub(r'\n{3,}', '\n\n', text)
    os.makedirs(os.path.join(book.out, slug), exist_ok=True)
    open(os.path.join(book.out, slug, 'index.md'), 'w', encoding='utf-8').write(text.rstrip() + '\n')
    return missing


def main(book, only):
    total = 0
    for idx, (pid, slug, name) in enumerate(book.parts):
        if only and pid not in only:
            continue
        m = render(book, pid, slug, name, idx)
        total += len(m)
        print('%s %-10s блоков без перевода: %d' % (pid, slug, len(m)))
    print('итого без перевода:', total)
