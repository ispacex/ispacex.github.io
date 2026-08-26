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
    # Тег HTML целиком, вместе с атрибутами: подписи внутри `title=` и `alt=`
    # на этих страницах нет ни одной (проверено), а класс и адрес трогать нельзя.
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
    '- Do not add, remove, explain or comment. Return only the translation.'
)


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


def ask(masked, lang, tries=3):
    """Один запрос к модели. Возвращает перевод или бросает."""
    body = json.dumps({
        'model': MODEL,
        'temperature': 0,
        'messages': [
            {'role': 'system', 'content': PROMPT % {'lang': lang}},
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
        except (urllib.error.URLError, KeyError, TimeoutError) as e:
            last = e
            time.sleep(2 * (n + 1))
    raise RuntimeError('DeepSeek не ответил: %s' % last)


def translate(text, lang, cache, stats=None):
    """Перевод куска. Метки не вернулись — возвращает None, и это не чинится.

    `stats` — счётчик: сколько взято из кеша, сколько куплено, сколько
    отвергнуто.
    """
    masked, parts = mask(text)
    # Нечего переводить: остались одни метки и знаки препинания.
    if not re.search(r'[^\W\d_]', SLOT_RE.sub('', masked), re.U):
        return text
    fp = fingerprint(masked, lang)
    got = cache.get(fp)
    if got is None:
        got = ask(masked, lang)
        cache.put(fp, got)
        if stats is not None:
            stats['bought'] = stats.get('bought', 0) + 1
    elif stats is not None:
        stats['cached'] = stats.get('cached', 0) + 1
    out = unmask(got, parts)
    if out is None and stats is not None:
        stats['lost'] = stats.get('lost', 0) + 1
    return out
