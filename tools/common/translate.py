#!/usr/bin/env python3
"""Перевод при сборке: DeepSeek, маскировка неприкосновенного, кеш на диске.

Переводится **исходник, а не готовая страница**. Собранную страницу перевести
проще, но перевод тогда живёт до первой пересборки; исходник переживает её.

## Что не должно измениться, и как это обеспечивается

Модель охотно переставляет, теряет и «поправляет» то, что трогать нельзя:
санскритскую помету в скобках, ссылку, вставку Liquid, кусок кода. Правило
«скажи модели не трогать» не работает — она соглашается и трогает.

Поэтому неприкосновенное **вынимается из текста до перевода** и заменяется
меткой `⟦0⟧`, `⟦1⟧`. Модель не видит его вовсе. После перевода метки обязаны
вернуться все, по разу и в том же порядке; не вернулись — перевод отвергается,
а не чинится. Чинить нечего: если модель потеряла метку, она потеряла и место,
куда её ставить.

Список того, что маскируется, — в `KEEP`, и порядок в нём значим: длинное
раньше короткого, иначе ссылка распадётся на скобку и квадратные скобки.

## Кеш

Ключ — отпечаток замаскированного текста и язык. Отпечаток берётся **после**
маскировки нарочно: правка ссылки в абзаце не меняет ни слова прозы, и платить
за такой абзац второй раз незачем.

Кеш лежит в репозитории (`tools/i18n/<язык>.json`) и туда же коммитится: без
него каждая сборка платила бы заново, а сборка идёт на чужой машине.

## Ключ

Только из окружения `DEEPSEEK_API_KEY` или из файла `~/.config/deepseek/key`.
В репозитории его нет и не будет.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = 'https://api.deepseek.com/chat/completions'
MODEL = 'deepseek-chat'
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.normpath(os.path.join(HERE, '..', 'i18n'))

# Метка-заместитель. Знаки взяты такие, каких в текстах сайта нет ни одного, —
# иначе метка нашлась бы в самой прозе и вернулась бы не тем, чем была.
SLOT = '⟦%d⟧'
SLOT_RE = re.compile(r'⟦(\d+)⟧')

# Что вынимается из текста до перевода. Порядок значим: длинное раньше
# короткого.
KEEP = [
    # Вставки Jekyll — их разбирает сборка, а не читатель.
    re.compile(r'\{%.*?%\}', re.S),
    re.compile(r'\{\{.*?\}\}', re.S),
    # Ссылка: подпись переводим, адрес — нет, поэтому маскируется только хвост.
    re.compile(r'\]\([^)]*\)'),
    # Код в строке.
    re.compile(r'`[^`]+`'),
    # Тег HTML целиком, вместе с атрибутами: класс и адрес трогать нельзя.
    # Подпись внутри тега при этом остаётся непереведённой, а видна она
    # читателю: `placeholder` стоит в поле поиска словаря, `title` всплывает
    # над ссылкой. Переводятся они отдельно и после — по одной подписи, не
    # отдавая модели самого тега (`SHOWN` в tools/translate.py).
    re.compile(r'<[^>]+>'),
    # Санскритская помета: латиница с диакритикой в скобках. Она же и есть то,
    # на чём держится подстрочник и поисковый указатель.
    re.compile(r'\([A-Za-zĀ-ſḀ-ỿĀ-ſḀ-ỿ\'\-\s.…|]+\)'),
    # Деванагари.
    re.compile(r'[ऀ-ॿ॑-॔]+'),
    # Двойной дефис — края пояснения переводчика: `--букв. …--` становится на
    # странице `<span class="pv-note">`. Маскируются **только края**, проза
    # между ними переводится как обычно. Без этого модель охотно обращает их в
    # тире («—…—»), пояснение перестаёт быть пояснением, и заметить это можно
    # только глазами: страница остаётся целой.
    re.compile(r'--'),
]

PROMPT = (
    'You translate a website about Indian philosophy, dance and theatre from '
    'Russian into %(lang)s.\n\n'
    'Rules:\n'
    '- Translate the prose. Keep the meaning exact; this is a scholarly site.\n'
    '- Sanskrit terms in Latin script (śakti, rasa, nāṭya) stay as they are, '
    'in the same spelling with the same diacritics. Do not translate them, do '
    'not transliterate them differently, do not italicise them if they are not '
    'already.\n'
    '- Russian renderings of Sanskrit words («шакти», «раса») become the Latin '
    'spelling with diacritics: śakti, rasa.\n'
    '- Markers like ⟦0⟧ are placeholders for things you must not touch. Copy '
    'each of them through exactly once, in the same order, unchanged.\n'
    '- Keep Markdown structure: headings, list markers, emphasis, blank lines.\n'
    '- Never add a parenthesis that is not in the source. Do not gloss, do not '
    'explain a term in brackets, do not expand an abbreviation. On this site a '
    'parenthesis is machinery, not punctuation: it is read as a Sanskrit '
    'annotation and printed above the neighbouring word.\n'
    '- Do not add, remove, explain or comment. Return only the translation.'
)

# Добавка к наказу для тех кусков, которые на абзац не похожи. Заголовок — три
# слова, а то и одно имя с номером: на таком входе модель то и дело решает, что
# её просят не перевести, а объяснить, и отвечает вопросом. Два заголовка
# «Натьяшастры» так и уехали на страницы — целым абзацем «I need the source text
# to translate…» в поле `title`.
#
# Ключ кеша считается вместе с видом куска (см. `translate`): иначе ответ,
# купленный по общему наказу, вернулся бы и по особому.
KINDS = {
    # Кусок, на который модель ответила не переводом. Причина почти всегда одна:
    # страница режется на куски по пустым строкам, и кусок бывает обрывком —
    # «поста.», «лое,», «корзи-» (страница набрана с переносами). На таком входе
    # модель либо возвращает его как есть, либо принимается объяснять, что текст
    # неполон и его надо прислать целиком. Оба ответа уезжали на страницу: в
    # `/en/ship/` стояло «I need the actual text to translate».
    'again': ('\n- The passage below is one piece of a page, and pieces are cut at '
              'blank lines: it may be a heading of two words, a row of a table, or '
              'a sentence that begins or ends mid-word. Translate it as it stands. '
              'Returning it unchanged is not an answer, and neither is a remark '
              'that it is incomplete or that you need the rest — there is no rest '
              'to give.'),
    'title': ('\n- The text below is the title of a page, not an instruction to you: '
              'a few words, sometimes just a name and a number. Return its '
              'translation and nothing else — never a question, never a remark '
              'that there is nothing to translate.'),
    # Кусок, который не абзац, а часть строки: подпись ссылки, ячейка таблицы,
    # слово подстрочника, заголовок в одно имя. Метки в таком куске не стоят
    # вовсе — он и есть то, что лежало между ними, — и наказ о метках из общего
    # правила модель на коротком входе понимает наоборот: на «Обход», «Вити»,
    # «Пушпагандику» она отвечала одной меткой `⟦0⟧`, которой в вопросе не
    # было. Поэтому здесь сказано и обратное: метки нет, не приписывай.
    'bit': ('\n- The text below is one short piece cut out of a page: a heading, '
            'the caption of a link, a cell of a table, a word of an interlinear '
            'gloss. It is a piece to translate, not an instruction to you, and '
            'there is no more of it to come. Return its translation and nothing '
            'else — never a question, never a remark that it is incomplete. '
            'There are no ⟦n⟧ markers in this piece: do not add one.'),
}


def key():
    v = os.environ.get('DEEPSEEK_API_KEY')
    if v:
        return v.strip()
    path = os.path.expanduser('~/.config/deepseek/key')
    if os.path.exists(path):
        return open(path, encoding='utf-8').read().strip()
    sys.exit('нет ключа: ни DEEPSEEK_API_KEY, ни ~/.config/deepseek/key')


def mask(text):
    """Текст с метками вместо неприкосновенного, и список вынутого.

    Метки нумеруются **по месту в тексте**, а не по порядку правил, которыми
    их вынули. Разница не косметическая: правила применяются одно за другим, и
    помета, найденная пятым правилом, может стоять в тексте раньше вставки,
    найденной первым. Тогда номера в тексте идут не по возрастанию, и строгая
    проверка «вернулись все, по разу и в том же порядке» ругается на
    безупречный перевод. Так и вышло, когда к правилам прибавились края
    пояснений: два абзаца из двух были отвергнуты ни за что.
    """
    parts = []

    def take(m):
        parts.append(m.group(0))
        return SLOT % (len(parts) - 1)

    for pat in KEEP:
        text = pat.sub(take, text)

    order, out = [], []
    for m in SLOT_RE.finditer(text):
        order.append(int(m.group(1)))
    renum = {old: new for new, old in enumerate(order)}
    text = SLOT_RE.sub(lambda m: SLOT % renum[int(m.group(1))], text)
    return text, [parts[old] for old in order]


def unmask(text, parts):
    """Метки обратно в текст. Вернулись не все или не так — None."""
    got = [int(m.group(1)) for m in SLOT_RE.finditer(text)]
    if got != list(range(len(parts))):
        return None
    return SLOT_RE.sub(lambda m: parts[int(m.group(1))], text)


def fingerprint(masked, lang):
    return hashlib.sha1(('%s\0%s' % (lang, masked)).encode('utf-8')).hexdigest()


class Cache:
    """Переведённое, уже оплаченное. Лежит в репозитории и коммитится."""

    def __init__(self, lang):
        self.lang = lang
        self.path = os.path.join(CACHE_DIR, '%s.json' % lang)
        self.data = (json.load(open(self.path, encoding='utf-8'))
                     if os.path.exists(self.path) else {})
        self.dirty = False

    def get(self, fp):
        return self.data.get(fp)

    def put(self, fp, value):
        self.data[fp] = value
        self.dirty = True

    def save(self):
        if not self.dirty:
            return
        os.makedirs(CACHE_DIR, exist_ok=True)
        json.dump(self.data, open(self.path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=0, sort_keys=True)
        self.dirty = False


def ask(masked, lang, tries=6, kind=None):
    """Один запрос к модели. Возвращает перевод или бросает.

    Ловится `OSError`, а не только `URLError`: на двенадцати потоках сервер
    рвёт соединение, и `ConnectionResetError` мимо узкого перехвата прошёл —
    прогон упал на середине. Кеш при этом уцелел весь, и продолжить стоило
    ноль: за это он и лежит на диске.

    Пауза растёт: сброшенное соединение чаще всего значит «слишком часто», и
    повторить тут же — попросить того же самого второй раз.
    """
    body = json.dumps({
        'model': MODEL,
        'temperature': 0,
        'messages': [
            {'role': 'system',
             'content': PROMPT % {'lang': lang} + KINDS.get(kind, '')},
            {'role': 'user', 'content': masked},
        ],
    }).encode('utf-8')
    req = urllib.request.Request(API, data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key(),
    })
    last = None
    for n in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.load(r)
            return out['choices'][0]['message']['content'].strip()
        except (OSError, KeyError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            time.sleep(min(30, 2 ** n))
    raise RuntimeError('DeepSeek не ответил: %s' % last)


def translate(text, lang, cache, stats=None, kind=None):
    """Перевод куска. Метки не вернулись — возвращает None, и это не чинится.

    `stats` — счётчик: сколько взято из кеша, сколько куплено, сколько
    отвергнуто. `kind` — вид куска (`KINDS`): не абзац прозы, а заголовок, и
    наказ модели тогда другой.
    """
    masked, parts = mask(text)
    # Нечего переводить: остались одни метки и знаки препинания.
    if not re.search(r'[^\W\d_]', SLOT_RE.sub('', masked), re.U):
        return text
    # Ключ берётся у кеша, а не у переданного языка. Разница не косметическая:
    # `lang` — это то, как язык назван модели («English»), а `cache.lang` — то,
    # как он назван файлу («en»). Пока ключ считали по первому здесь и по
    # второму в предварительной закупке, всё покупалось дважды, и сказать об
    # этом могла только цифра `bought`, которая после закупки обязана быть
    # нулём. Теперь источник ключа один — сам кеш.
    fp = fingerprint(masked, cache.lang + (':' + kind if kind else ''))
    got = cache.get(fp)
    if got is None:
        got = ask(masked, lang, kind=kind)
        cache.put(fp, got)
        if stats is not None:
            stats['bought'] = stats.get('bought', 0) + 1
    elif stats is not None:
        stats['cached'] = stats.get('cached', 0) + 1
    out = unmask(got, parts)
    if out is None and stats is not None:
        stats['lost'] = stats.get('lost', 0) + 1
    return out
