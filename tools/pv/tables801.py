#!/usr/bin/env python3
"""Переводит подписи в таблицах части 5–8/4 — единственных во всём трактате.

Таблицы почти целиком состоят из санскрита; по-английски в них только подписи
столбцов, названия таттв и несколько пояснений. Поэтому переводится не весь
HTML, а текстовые узлы: разметка и санскрит остаются нетронутыми.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))

CAT = re.compile(r'\(category (\d+)\)')
CATS = re.compile(r'\(categories (\d+) and (\d+)\)')
BETWEEN = re.compile(r'\(between categories (\d+) and (\d+)\)')
CONSIST = re.compile(r'^- (\S+) \((\S+) consisting of (\S+)\)$')
CONSIST2 = re.compile(r'^- (\S+) \((\S+) --which includes (\S+)-- consisting of (\S+)\)$')

D = {
 'Respective tattva or category': 'Соответствующая таттва (категория)',
 'Respective tattva (category)': 'Соответствующая таттва (категория)',
 'Respective tattva (category) and power (śakti)': 'Соответствующая таттва (категория) и сила (śakti)',
 'Respective tattva, which now absorbs the previous tattva within itself':
     'Соответствующая таттва, которая теперь вбирает в себя предыдущую',
 'The order and assignation of the tattva-s have been extracted from venerable Mālinīvijayatantra':
     'Порядок таттв и их соответствия взяты из досточтимой Mālinīvijayatantra',
 'The remaining 34 letters (viz.': 'Остальные 34 звука (то есть',
 'Letter': 'Звук',
 'Letter in Mālinī': 'Звук в Mālinī',
 'Mālinī letter': 'Звук Mālinī',
 'Mātṛkā letter': 'Звук Mātṛkā',
 'Experience of Śiva': 'Переживание Śiva',
 'Aspect in Mātṛkā': 'Соответствие в Mātṛkā',
 'Consonant in itself': 'Согласный сам по себе',
 'Consonant going through': 'Согласный, проходящий',
 'transformation': 'превращение',
 'Consonant assigned to a tattva': 'Согласный, приписанный таттве',
 'Reflecting in Bimba': 'Отражается в Bimba',
 'Reflecting in Paśyantī': 'Отражается в Paśyantī',
 'Chart 2': 'Таблица 2',
 'Chart 3': 'Таблица 3',
 'Sarvāgrarūpatā in Parā according to the Mātṛkā arrangement':
     'Sarvāgrarūpatā в Parā по строю Mātṛkā',
 'Sarvamadhyarūpatā in Parāparā according to the Mātṛkā arrangement':
     'Sarvamadhyarūpatā в Parāparā по строю Mātṛkā',
 'Sarvāntyarūpatā in Parāparā according to the Mātṛkā arrangement':
     'Sarvāntyarūpatā в Parāparā по строю Mātṛkā',
 'The first 16 letters in the Mālinī arrangement representing the internal life of Śiva':
     'Первые 16 звуков строя Mālinī, представляющие внутреннюю жизнь Śiva,',
 'along with their respective aspects in the Mātṛkā arrangement, all in Parā':
     'вместе с их соответствиями в строе Mātṛkā — всё в Parā',
 'The last 34 letters of Mālinī in Aparā and their corresponding reflections in Paśyantī according to the Mātṛkā arrangement':
     'Последние 34 звука Mālinī в Aparā и их отражения в Paśyantī по строю Mātṛkā',
 'The circle of tattva-s and their letters comes from the bottom of the list':
     'Круг таттв и их звуков приходит снизу списка',
 'The circle of tattva-s and their letters returns now to the top of the list':
     'Круг таттв и их звуков возвращается теперь к началу списка',
 '(vowels are always immutable)': '(гласные всегда неизменны)',
 '- a ā i ī u ū ṛ ṝ ḷ ḹ e ai o au aṁ aḥ (vowels are always immutable)':
     '- a ā i ī u ū ṛ ṝ ḷ ḹ e ai o au aṁ aḥ (гласные всегда неизменны)',
 '(vowels never undergo transformation, i.e. they never are reflected in Bimba or the Mirror of Consciousness)':
     '(гласные не претерпевают превращения: они никогда не отражаются в Bimba, Зерцале Сознания)',
 'Nāda as I-consciousness': 'Nāda как Я-сознание',
 "Śiva's I-consciousness attains full vigor and maturity":
     'Я-сознание Śiva обретает полную силу и зрелость',
 'Śiva experiences His "flavor", i.e. a realization of His own nature as "I"':
     'Śiva переживает Свой «вкус» — то есть осознание Своей природы как «Я»',
 'Śiva experiences His "odor", i.e. He fully recognizes that He is so and not otherwise':
     'Śiva переживает Свой «запах» — то есть вполне узнаёт, что Он таков, а не иной',
 'Śiva gets in touch with His own Power': 'Śiva соприкасается со Своей собственной Силой',
 'Śiva becomes established in the state relating to the Womb of Śakti':
     'Śiva утверждается в состоянии, относящемся к Лону Śakti',
 'There is a reflection of Śiva as "I" in the Karaṇaśakti --the Lord\'s Power to produce differences-- whose essence is "speech"':
     'Śiva отражается как «Я» в Karaṇaśakti — Силе Господа производить различия, — чья суть есть «речь»',
 "Śiva's I-consciousness appears in the form of these two vowels indicating introversion and extroversion":
     'Я-сознание Śiva является в виде этих двух гласных, означающих обращённость внутрь и наружу',
 "After appearing in that form, Śiva's I-consciousness rests in the Womb of Śakti whose nature is Buddhi --intellect, category 14-- and there is confirmation of Śiva's I-consciousness":
     'Явившись в этом виде, Я-сознание Śiva покоится в Лоне Śakti, чья природа — Buddhi (разум, категория 14), и Я-сознание Śiva утверждается',
 'Śiva experiences Firmness with reference to His I-consciousness':
     'Śiva переживает Твёрдость в отношении Своего Я-сознания',
 'Śiva experiences Taste --viz. Bliss-- with regard to His I-consciousness':
     'Śiva переживает Вкус — то есть Блаженство — в отношении Своего Я-сознания',
 'Śiva experiences Light with respect to His I-consciousness':
     'Śiva переживает Свет в отношении Своего Я-сознания',
 "(Śiva's Power of Will)": '(Сила Воли Śiva)',
 "(Śiva's Power of Bliss)": '(Сила Блаженства Śiva)',
 '(Emissional Power)': '(Сила Эмиссии)',
 "(Śiva's power linked to Bindu)": '(сила Śiva, связанная с Bindu)',
 '(indistinct Power of Action)': '(неотчётливая Сила Действия)',
 '(distinct Power of Action)': '(отчётливая Сила Действия)',
 '(more distinct Power of Action)': '(более отчётливая Сила Действия)',
 '(most distinct Power of Action)': '(самая отчётливая Сила Действия)',
 'Śivatattva (category 1) and Śaktitattva (category 2)':
     'Śivatattva (категория 1) и Śaktitattva (категория 2)',
}

TAIL_MALINI = ('gha ṅa i a va bha ya ḍa ḍha ṭha jha ña ja ra ṭa pa cha la ā sa aḥ ha ṣa kṣa ma śa aṁ ta e ai o au da pha) '
               'are distributed as follows:')
TAIL_MATRKA = ('ka kha ga gha ṅa ca cha ja jha ña ṭa ṭha ḍa ḍha ṇa ta tha da dha na pa pha ba bha ma ya ra la va śa ṣa sa ha kṣa) '
               'are distributed, "in reverse order", as follows:')


def tr(t):
    s = t.strip()
    if not s or not re.search(r'[A-Za-z]', s):
        return None
    if s in D:
        return D[s]
    m = CONSIST2.match(s)
    if m:
        return '- %s (%s, включающая %s, из %s)' % (m.group(1), m.group(2), m.group(3), m.group(4))
    m = CONSIST.match(s)
    if m:
        return '- %s (%s из %s)' % (m.group(1), m.group(2), m.group(3))
    if s.startswith('- ' + TAIL_MALINI[:12]) or s.endswith('are distributed as follows:'):
        return s.replace('are distributed as follows:', 'распределяются так:')
    if s.endswith('are distributed, "in reverse order", as follows:'):
        return s.replace('are distributed, "in reverse order", as follows:',
                         'распределяются «в обратном порядке» так:')
    out = BETWEEN.sub(lambda m: '(между категориями %s и %s)' % (m.group(1), m.group(2)), s)
    out = CATS.sub(lambda m: '(категории %s и %s)' % (m.group(1), m.group(2)), out)
    out = CAT.sub(lambda m: '(категория %s)' % m.group(1), out)
    return out if out != s else (None if re.search(r'\b(the|of|and|in|to|is|are|with|as)\b', s, re.I) else s)


def translate_table(inner):
    parts = re.split(r'(<[^>]+>)', inner)
    missed = []
    for i, p in enumerate(parts):
        if p.startswith('<'):
            continue
        raw = html.unescape(p)
        stripped = raw.strip()
        v = tr(stripped)
        if v is None:
            if re.search(r'[A-Za-z]', stripped):
                missed.append(stripped)
            continue
        parts[i] = p.replace(stripped, v) if stripped else p
    return ''.join(parts), missed


if __name__ == '__main__':
    blocks = json.load(open(os.path.join(HERE, 'blocks', '801.json'), encoding='utf-8'))['blocks']
    p = os.path.join(HERE, 'ru', '801.json')
    ru = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    allmissed = []
    for i, b in enumerate(blocks):
        if b['k'] != 'table':
            continue
        out, missed = translate_table(b['html'])
        allmissed += missed
        ru[str(i)] = '<table class="pv-chart">%s</table>' % out
    json.dump(ru, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('таблиц переведено:', sum(1 for b in blocks if b['k'] == 'table'))
    if allmissed:
        print('НЕ ПЕРЕВЕДЕНО:')
        for x in sorted(set(allmissed)):
            print('   ', x[:120])
