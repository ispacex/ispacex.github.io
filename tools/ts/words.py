#!/usr/bin/env python3
"""Термины «Тантрасары»: что взято у соседнего словаря и что добавлено здесь.

**Свой список здесь не сочинялся, и это сделано нарочно.** «Тантрасара» — та
же «Тантралока», сжатая самим Абхинавагуптой до одной книги: тот же автор, та
же школа, те же слова. Объяснять `tattva` на одной странице сайта одними
словами, а на соседней другими — значит наживать расхождение на ровном месте.
Поэтому статьи берутся из [`tools/trika/words.py`](../trika/words.py), а здесь
лежит только то, чем «Тантрасара» от «Тантралоки» отличается.

Отличается она двумя вещами, и обе видны в списке:

* **Шесть статей выброшено** (`SKIP`) — их в «Тантрасаре» не помечают ни разу.
  Правило то же, что у прочих словарей раздела: лучше статьи не будет вовсе,
  чем ссылка «где в тексте», ведущая в пустоту. Все шесть при этом названы в
  толкованиях соседних статей и со страницы не пропадают.
* **Тридцать добавлено** (`EXTRA`), и почти половина из них — обрядовые.
  Причина не в разнице словарей, а в разнице того, что переведено: у
  «Тантралоки» по-русски есть главы 1–16, доктринальная половина, а
  «Тантрасара» переведена вся, и вторая её половина — обряд от омовения до
  каулического яги. Отсюда `sthaṇḍila`, `arghapātra`, `pavitraka`,
  `prāyaścitta`, `naimittika`: слова, которых первой половине просто не нужно.

Помет в переведённых главах 8 525, основ — три с половиной тысячи, и вверху по
частоте, как всегда, служебные слова: `ca`, `tatra`, `tu`, `api`. Оставлено то,
обо что читатель спотыкается.

Якорей у «Тантрасары» в тексте не было — в отличие от «Тантралоки», где у
каждого абзаца перевода свой адрес. Здесь их ставит сборка страниц, как у
Parātrīśikāvivaraṇa: `anchors()` говорит, в какие абзацы, `render.py` их кладёт.
"""
import collections
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.terms import (PLACES, count, find, hits, index as _index, keyof,  # noqa: F401
                          markup, slug, stem, t, targets, terms as _terms)
from book import GLOSSARY, CYR, blocks
from parts import PARTS


def _shared():
    """Список статей «Тантралоки» — по имени файла, а не через `import`.

    Соседний конвейер лежит рядом, но пакетом не является: у обоих есть свои
    `book.py` и `parts.py`, и обычный `import` подтянул бы не тот. Модуль,
    загруженный по пути, живёт под своим именем и чужих не задевает.
    """
    path = os.path.join(HERE, '..', 'trika', 'words.py')
    spec = importlib.util.spec_from_file_location('trika_words', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SECTIONS


# Статьи «Тантралоки», которых в «Тантрасаре» не помечают ни разу.
SKIP = {
    'vaikharī',     # названа в толковании vāc
    'suṣumnā',      # названа в толковании udāna: «срединное русло»
    'kuṇḍalinī',
    'vedaka',       # названа в толковании vedya
    'jīvanmukti',   # названа в толковании mokṣa
    'siddhānta',
}


# Слова, которые есть у «Тантрасары» и которых не понадобилось «Тантралоке» —
# в те же разделы, что и у неё. Порядок внутри раздела смысловой: статья
# ложится рядом с той, вместе с которой её читают.
EXTRA = {

'Свет, отклик и Сила': [
t('parāmarśa', 'परामर्श', 'Парамарша',
  '«схватывание»: тот самый акт, которым Сознание касается себя и говорит «Я». '
  'Не мысль о себе, а само себя-держание, из которого выходят и звуки речи, и '
  'мир.',
  forms='parāmarśaḥ parāmarśam parāmarśe parāmarśāḥ parāmarśānām parāmarśena '
        'parāmarśasya parāmṛśati parāmarśatva'),
t('viśrānti', 'विश्रान्ति', 'Вишранти',
  'покой — не отдых после дела, а то, во что всякое движение приходит и в чём '
  'держится. «Упокоение в себе» и есть блаженство.',
  forms='viśrāntiḥ viśrāntim viśrāntyā viśrāntau viśrāntaḥ viśrāntam '
        'viśrānte viśrāntena viśrāntāḥ viśrāmyati'),
t('visarga', 'विसर्ग', 'Висарга',
  '«исторжение»: то, чем Полнота изливает из себя мир, ничего не теряя. Оно же '
  'знак `ḥ` — две точки, которыми кончается звуковой ряд.',
  forms='visargaḥ visargam visarge visargāt visargasya visargeṇa'),
t('pratibimba', 'प्रतिबिम्ब', 'Пратибимба',
  'отражение. Третья глава на нём и держится: мир стоит в Сознании, как '
  'отражение в зеркале, — и подлинника, с которого он снят, нет вовсе.',
  forms='pratibimbam pratibimbe pratibimbasya pratibimbena pratibimbita'),
t('rasa', 'रस', 'Раса',
  'сок, вкус: то, чем вещь схватывается изнутри, а не рассматривается снаружи. '
  'Сознание берёт мир «соком собственного отклика».',
  forms='rasaḥ rasam rasena rase rasāt rasasya'),
],

'Таттвы, пути и мир': [
t('vidyā', 'विद्या', 'Видья',
  'знание — и та таттва (śuddhavidyā), на которой «Я» и «это» ещё держатся '
  'вместе; ниже майи она же становится узким знанием одного человека.',
  forms='vidyām vidyayā vidyāyāḥ vidyāḥ vidyāsu'),
t('aṇḍa', 'अण्ड', 'Анда',
  '«яйцо» — оболочка мироздания. Их четыре, вложенных одна в другую: земли, '
  'природы, майи и Силы.',
  forms='aṇḍam aṇḍe aṇḍāni aṇḍānām aṇḍasya'),
t('tanmātra', 'तन्मात्र', 'Танматра',
  '«только то»: тонкая основа стихии — звук, касание, цвет, вкус, запах, взятые '
  'сами по себе, до всякой вещи.',
  forms='tanmātram tanmātre tanmātrāṇi tanmātrāt tanmātrāṇām'),
t('indriya', 'इन्द्रिय', 'Индрия',
  'орудие: пять чувств и пять действий. Не сам глаз, а то, чем видят.',
  forms='indriyam indriye indriyāṇi indriyāṇām indriyasya indriyaiḥ'),
],

'Речь и слово': [
t('varga', 'वर्ग', 'Варга',
  'ряд — пятёрка согласных одного места произнесения (ka-varga, ca-varga). '
  'Ими расписан весь алфавит, а по алфавиту — весь мир.',
  forms='vargaḥ vargam varge vargasya vargāḥ vargeṣu'),
],

'Тело, дыхание, средоточия': [
t('śūnya', 'शून्य', 'Шунья',
  'пустота — состояние, в котором нет ничего познаваемого. Не цель: за ней '
  'открывается то, для чего и пустота была предметом.',
  forms='śūnyam śūnye śūnyāt śūnyena śūnyasya śūnyatā'),
],

'Познающий и познаваемое': [
t('ajñāna', 'अज्ञान', 'Аджняна',
  'незнание — не нехватка сведений, а неполное знание, принятое за полное. '
  'Двух родов: сидящее в существе и сидящее в уме.',
  forms='ajñānam ajñāne ajñānena ajñānasya ajñānāt'),
],

'Узы': [
t('sakala', 'सकल', 'Сакала',
  '«с долями» — связанное существо, у которого все три грязи. Над ним '
  'pralayākala, у кого нет майической, и vijñānākala, у кого осталась одна '
  'первая.',
  forms='sakalaḥ sakalam sakale sakalāḥ sakalasya akalaḥ akalam akale akalāḥ '
        'akalasya pralayākala pralayākalaḥ pralayākalāḥ vijñānākala '
        'vijñānākalaḥ vijñānākalāḥ',
  alias='сакала пралаякала виджнянакала'),
],

'Пути и вхождение': [
t('avasthā', 'अवस्था', 'Авастха',
  'состояние: бодрствование, сон со сновидениями, глубокий сон — и четвёртое, '
  'Турья, которое не рядом с ними, а сквозь них.',
  forms='avasthām avasthāḥ avasthāyām avasthayā avasthānām'),
t('abhyāsa', 'अभ्यास', 'Абхьяса',
  'повторение — то, чем однажды понятое становится своим. У Абхинавагупты оно '
  'не наработка навыка, а возвращение внимания туда же.',
  forms='abhyāsaḥ abhyāsam abhyāse abhyāsāt abhyāsena abhyāsasya'),
t('tarka', 'तर्क', 'Тарка',
  'рассуждение. Из всех частей йоги Абхинавагупта ставит его первым: правильное '
  'рассуждение (sattarka) само разбирает разделение, которого не берут ни поза, '
  'ни задержка дыхания.',
  forms='tarkaḥ tarkam tarke tarkāt tarkeṇa tarkasya sattarka sattarkaḥ'),
],

'Посвящение и обряд': [
t('devatā', 'देवता', 'Девата',
  'божество — и круг божеств (devatā-cakra), которым в обряде поклоняются как '
  'силам собственного Сознания, а не как чужим лицам.',
  forms='devatām devatāḥ devatayā devatāyāḥ devatānām'),
t('sthaṇḍila', 'स्थण्डिल', 'Стхандила',
  'ровная площадка, на которой правят обряд, — место, ставшее престолом.',
  forms='sthaṇḍilam sthaṇḍile sthaṇḍilāni sthaṇḍilasya'),
t('samaya', 'समय', 'Самая',
  'устав посвящённого: правила, которые принимают вместе с первым посвящением. '
  'Samayin — тот, кто их держит.',
  forms='samayaḥ samayam samaye samayāḥ samayānām samayī samayinaḥ'),
t('pavitraka', 'पवित्रक', 'Павитрака',
  'освящённый шнур — и обряд, которым его подносят: им раз в год покрывают всё '
  'недоделанное и упущенное. Ему отдана последняя глава.',
  forms='pavitrakam pavitrake pavitrakeṇa pavitrakasya pavitrakāṇi'),
t('naimittika', 'नैमित्तिक', 'Наймиттика',
  'обряд по случаю — в отличие от `nitya`, ежедневного: случаем бывает и '
  'праздник, и смерть, и просто нечаянная радость.',
  forms='naimittikam naimittike naimittikāḥ naimittikeṣu naimittikasya',
  alias='наимиттика наймиттика'),
t('tarpaṇa', 'तर्पण', 'Тарпана',
  'насыщение: возлияние, которым питают божества круга — а через них себя '
  'самого.',
  forms='tarpaṇam tarpaṇe tarpaṇena tarpayet tarpayitvā tarpayanti'),
t('mūrti', 'मूर्ति', 'Мурти',
  'образ, изваяние — одно из мест, в которых правят обряд, наравне с сосудом, '
  'огнём и собственным телом.',
  forms='mūrtiḥ mūrtim mūrtau mūrtayaḥ mūrteḥ'),
t('kumbha', 'कुम्भ', 'Кумбха',
  'сосуд с водой, который ставят в средоточие обряда и в котором божество '
  'присутствует так же, как в изваянии.',
  forms='kumbhaḥ kumbham kumbhe kumbhena kumbhasya'),
t('arghapātra', 'अर्घपात्र', 'Аргхапатра',
  'чаша подношения: в ней смешивают то, что обряд предлагает, и из неё же '
  'вкушают.',
  forms='arghapātram arghapātre arghapātreṇa arghapātrasya argha arghaḥ'),
t('astra', 'अस्त्र', 'Астра',
  '«оружие» — мантра, которой очищают место и отводят помеху. Одна из '
  'мантр-частей тела наравне с сердцем и головой.',
  forms='astram astre astreṇa astrasya'),
t('vrata', 'व्रत', 'Врата',
  'обет — принятое ограничение, которым держат себя в начатом.',
  forms='vratam vrate vratāni vratasya vratāt'),
t('prāyaścitta', 'प्रायश्चित्त', 'Праяшчитта',
  'искупление: чем поправляют нарушенное правило или недоделанный обряд.',
  forms='prāyaścittam prāyaścitte prāyaścittāni prāyaścittānām prāyaścittasya'),
t('vīra', 'वीर', 'Вира',
  '«герой» — участник каулического обряда: тот, кто способен взять его, не '
  'испугавшись и не польстившись.',
  forms='vīraḥ vīram vīrāḥ vīrāṇām vīrasya vīre'),
t('dāna', 'दान', 'Дана',
  'дарение — и то, что отдают: одно из действий, которыми обряд и держится.',
  forms='dānam dāne dānena dānāt dānasya'),
],
}


def _sections():
    """Общий список плюс здешний, раздел в раздел.

    Обе проверки нужны потому, что ошибка тут молчит: название раздела с
    опечаткой просто потеряло бы свои статьи, а имя в `SKIP`, которого в общем
    списке нет, ничего бы не выбросило — и то и другое видно только счётом
    статей, который никто не помнит наизусть.
    """
    shared, out, seen = _shared(), [], set()
    known = {x.iast for _title, group in shared for x in group}
    if SKIP - known:
        raise SystemExit('в SKIP имена, которых нет в общем списке: %s'
                         % ', '.join(sorted(SKIP - known)))
    for title, group in shared:
        seen.add(title)
        out.append((title, [x for x in group if x.iast not in SKIP]
                    + EXTRA.get(title, [])))
    if set(EXTRA) - seen:
        raise SystemExit('в EXTRA разделы, которых нет в общем списке: %s'
                         % ', '.join(sorted(set(EXTRA) - seen)))
    return out


SECTIONS = _sections()


def terms():
    return _terms(SECTIONS)


def index():
    return _index(SECTIONS)


# --- где термин разбирается ------------------------------------------------


def occurrences():
    """Сколько раз термин помечен в каждом абзаце перевода.

    Возвращает {термин: {(глава, номер блока): сколько раз}}. Номер блока —
    его место в том самом списке, который выкладывает на страницу `render.py`
    (см. `blocks` в book.py): по нему и встанет якорь.

    Своего `ru/*.json` у этого конвейера нет — перевод приходит вместе с
    блоками, и переведённым блок признаётся по кириллице в нём.
    """
    tables = index()
    out = hits()
    for pid, _slug, _name in PARTS:
        for i, b in enumerate(blocks(pid)):
            text = b.get('t', '')
            if text and CYR.search(text):
                count(out, text, (pid, i), tables)
    return out


def anchors():
    """Якоря, которые сборка страниц должна расставить: {глава: {блок: id}}.

    На один абзац якорь один, даже если в него метят несколько статей: id у
    элемента может быть только один. Первая по порядку словаря статья даёт имя,
    остальные ссылаются на то же имя — адрес от этого не портится.
    """
    out = collections.defaultdict(dict)
    tgt = targets(occurrences())
    for term in terms():
        for pid, block in tgt.get(term.iast, ()):
            out[pid].setdefault(block, 'g-' + keyof(term))
    for pid, marks in out.items():
        if len(set(marks.values())) != len(marks):
            raise SystemExit('якорь повторяется в главе %s' % pid)
    return out


def links():
    """Ссылки словаря в текст: {термин: [(адрес главы, якорь)]}."""
    marks, out = anchors(), {}
    where = {pid: slug for pid, slug, _ in PARTS}
    for iast, places in targets(occurrences()).items():
        out[iast] = [(where[pid], marks[pid][block]) for pid, block in places]
    return out


_TABLES = None


def link(word):
    """Санскритское слово в подстрочнике — ссылка на статью словаря, или None.

    Слово стоит в падеже, и статью ему подбирает `find`. Чего в словаре нет —
    остаётся простым текстом.
    """
    global _TABLES
    if _TABLES is None:
        _TABLES = index()
    term = find(word, _TABLES)
    return GLOSSARY + '#t-' + keyof(term) if term else None


if __name__ == '__main__':
    got = occurrences()
    print('статей: %d (из них здешних: %d)'
          % (sum(1 for _ in terms()), sum(len(v) for v in EXTRA.values())))
    print('без единого вхождения: %s'
          % (', '.join(x.iast for x in terms() if not got.get(x.iast)) or '—'))
    tgt = targets(got)
    for term in terms():
        n = sum(got.get(term.iast, {}).values())
        print('%5d %-14s %s' % (n, term.iast,
                                ' · '.join('%s:%d' % p for p in tgt.get(term.iast, ()))))
