#!/usr/bin/env python3
"""Термины Pratyabhijñāhṛdayam: сам список и то, как он сходится с текстом.

Список **свой**, и это решено замером, а не на глаз. У «Тантрасары» словарь
взят у «Тантралоки» целиком — книга та же, сжатая тем же автором, и из 120
статей там не встречались шесть. Здесь автор другой, Кшемараджа, и книга
другая: из тех же 120 статей **тридцать не встречаются ни разу** — весь обряд
(`dīkṣā`, `nyāsa`, `maṇḍala`, `yāga`, `homa`, `pūjā`, `abhiṣeka`), а из
оставшихся у половины по одному-два вхождения. «Сердце Узнавания» — не свод, а
самое короткое изложение всей системы, и слова у него свои.

Вверху по частоте стоят они и стоят: `citi` — то самое слово, которым книга
открывается и которого в словаре «Тантралоки» нет вовсе, — `saṅkoca` и
`vikāsa`, `pañcakṛtya`, `grāhaka`, `bhūmikā`, `vyāmohitatā`, `samādhi`.

**Перевод здесь наш**, и это второе отличие от двух соседних словарей. У них
пришлось оговаривать врезкой, что толкования написаны здесь, а перевод чужой.
Здесь наоборот: разбор переведён нами, а вот **сами двадцать сутр** взяты у
Габриэля Pradīpaka готовыми, и слова из них — его. Оговорка нужна ровно об
этом.

Помет в переводе разбора 2232 — против 46 302 у «Тантралоки» и 8 525 у
«Тантрасары». Счёт «где термин разбирается» стоит поэтому на тонком основании:
у части статей ссылка выходит одна, а не три, и это не поломка, а всё, что
книга о слове говорит.

Механика общая на пять словарей — `tools/common/terms.py`. Здесь только то, что
у Pratyabhijñāhṛdayam своё: откуда берётся перевод (`ru/<часть>.json`, по номеру
блока) и как на место в нём ставится якорь. Своих адресов у абзацев нет, и
якоря расставляет сборка страниц — как у Parātrīśikāvivaraṇa и «Тантрасары».
"""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.terms import (PLACES, count, find, hits, index as _index, keyof,  # noqa: F401
                          markup, slug, stem, t, targets, terms as _terms)
from parts import PARTS

GLOSSARY = '/ksh/ph/glossary/'


# Порядок статей внутри раздела — не алфавитный, а смысловой: соседние понятия
# стоят рядом, чтобы статья читалась вместе с парной к ней.
SECTIONS = [

('Сознание и его имена', [
t('citi', 'चिति', 'Чити',
  'Сознание, взятое как Сила: то самое слово, которым книга открывается. Не '
  '«сознание чего-то», а само собой светящееся, свободное и потому способное '
  'разворачивать вселенную из себя.',
  forms='citiḥ citim citeḥ citau citayā'),
t('cit', 'चित्', 'Чит',
  'Сознание как таковое — Свет, в котором всё является. `citi` — то же самое, '
  'названное со стороны Силы.',
  forms='cetas cetasā citaḥ cite cita'),
t('saṁvid', 'संविद्', 'Самвид',
  'Сознавание — Сознание, взятое как то, чем всякая вещь вообще есть для '
  'кого-то. У Кшемараджи это же слово стоит и на месте Высшего.',
  forms='saṁvidaḥ saṁvidi saṁvittiḥ saṁvitti saṁvedanam saṁvedana'),
t('prakāśa', 'प्रकाश', 'Пракаша',
  'Свет: то, чем вещь вообще явлена. Без вхождения в него, говорит Кшемараджа, '
  'не может быть явлено ничто.',
  forms='prakāśaḥ prakāśam prakāśena prakāśāt prakāśane prakāśate'),
t('vimarśa', 'विमर्श', 'Вимарша',
  'отклик Света на себя самого — то, чем Свет знает, что он есть. Пара к '
  '`prakāśa`, и они не два.',
  forms='vimarśaḥ vimarśam vimarśena vimarśa parāmarśaḥ parāmarśa parāmarśena '
        'parāmarśanam'),
t('ahantā', 'अहन्ता', 'Аханта',
  'Я-сознание — не самомнение, а то «Я», в котором покоится всякое '
  'переживание. Полное Я-сознание (`pūrṇāhantā`) и есть плод всей книги.',
  forms='ahantāyām ahantām ahaṁbhāvaḥ ahaṁ-bhāvaḥ'),
t('ānanda', 'आनन्द', 'Ананда',
  'Блаженство — не радость по поводу, а то, чем полнота ощущает саму себя.',
  forms='ānandaḥ ānandam ānandena ānande'),
t('camatkāra', 'चमत्कार', 'Чаматкара',
  'Изумление: тот вкус, с каким Сознание узнаёт себя — как вздрагивают, узнав '
  'давно знакомое лицо.',
  forms='camatkāraḥ camatkāram camatkārāt'),
t('sphurattā', 'स्फुरत्ता', 'Спхуратта',
  'вспыхивание, дрожание Света — Сознание, взятое как живое, а не как '
  'неподвижная основа.',
  forms='sphurati sphurantī sphuritam sphuraṇam asphuraṇe parisphurantī'),
t('śakti', 'शक्ति', 'Шакти',
  'Сила Бога, Его Я-Сознание. У Кшемараджи она же и есть `citi`: Шива без '
  'Силы ничего не являет, и разницы между ними нет.',
  forms='śaktiḥ śaktim śaktyā śaktayaḥ śakteḥ śaktau śaktibhiḥ śaktīḥ'),
t('svātantrya', 'स्वातन्त्र्य', 'Сватантрья',
  'Абсолютная Свобода: то, чем Сознание ни от чего не зависит — и чем оно '
  'вольно связать себя самого.',
  forms='svātantryam svātantryāt svātantryeṇa svātantrye svatantraḥ svatantrā '
        'svatantram'),
t('icchā', 'इच्छा', 'Иччха',
  'Воля — первая из трёх Сил: воля, знание, действие.',
  forms='icchayā icchām icchāyāḥ icchā-śaktiḥ'),
t('jñāna', 'ज्ञान', 'Джняна',
  'Знание как Сила Бога — и знание отдельного человека, когда та же Сила '
  'сжата.',
  forms='jñānam jñāne jñānena jñānāt jñāna-śaktiḥ'),
t('kriyā', 'क्रिया', 'Крия',
  'Действие — третья Сила: то, чем Бог не только знает, но и делает.',
  forms='kriyām kriyāyāḥ kriyayā kriyā-śaktiḥ'),
t('śiva', 'शिव', 'Шива',
  'Бог как покоящаяся сторона Реальности — Свет Сознания, неотличный от '
  'собственной Силы. Книга кончается словами «iti śivam»: «итак, всё есть '
  'Шива».',
  forms='śivaḥ śivam śivena śivasya śivāt śive śivatā'),
t('bhairava', 'भैरव', 'Бхайрава',
  'имя Высшего Господа в Трике: Тот, кто держит вселенную, несёт её и вбирает '
  'обратно.',
  forms='bhairavaḥ bhairavam bhairave bhairavīya parabhairavaḥ parabhairava',
  alias='бхаирава бхайрава'),
t('parameśvara', 'परमेश्वर', 'Парамешвара',
  '«Высший Господь» — Бог, взятый как владыка проявления.',
  forms='parama-īśvaraḥ parama-īśvaram parama-īśvarasya parama-īśvare īśvaraḥ '
        'īśvara īśvarasya īśvare mahā-īśvaraḥ maheśvaraḥ māheśvarī māheśvaryam',
  alias='парамешвара парамаишвара махешвара'),
t('bhagavatī', 'भगवती', 'Бхагавати',
  '«Блаженная», «Владычица» — Сила, названная как лицо; в мужском роде '
  '`bhagavat`, «Блаженный Господь».',
  forms='bhagavat bhagavān bhagavataḥ bhagavatā devī devyaḥ bhaṭṭārikā',
  alias='бхагавати бхагават деви'),
t('anuttara', 'अनुत्तर', 'Ануттара',
  '«то, выше чего нет»: Высшая Реальность — и звук «a», которым начинается '
  'алфавит и в котором вселенная упокоивается.',
  forms='anuttaram anuttare anuttarasya anuttareṇa'),
t('sadāśiva', 'सदाशिव', 'Садашива',
  'третья таттва: ступень, где вселенная уже видна, но как смутное «это», '
  'покрытое «Я».',
  forms='sadāśivaḥ sadāśivam sadāśive sadāśiva-tattve'),
t('anāśritaśiva', 'अनाश्रितशिव', 'Анашритащива',
  '«Шива, ни на что не опёртый» — тот миг, когда вселенная ещё не явлена и '
  'единство с Сознанием не видно даже Ему: пустота пустее пустоты.',
  forms='anāśrita anāśritaḥ anāśrita-śiva anāśrita-śivaḥ',
  alias='анашритащива анашриташива'),
]),

('Сжатие и раскрытие', [
t('saṅkoca', 'सङ्कोच', 'Санкоча',
  'сжатие: то, чем безмерное Сознание становится вот этим, отдельным. Не '
  'порча и не утрата — приём собственной Свободы. Главное слово книги наравне '
  'с `citi`.',
  forms='saṅkocaḥ saṅkocam saṅkocāt saṅkocena saṅkoce saṅkocinī saṅkucita '
        'saṅkucitaḥ saṅkucitā saṅkucitam saṅkucitāḥ saṅkocavatyaḥ'),
t('vikāsa', 'विकास', 'Викаса',
  'раскрытие — пара к сжатию. Освобождение здесь и описано как раскрытие '
  'середины, а не как приход куда-то ещё.',
  forms='vikāsaḥ vikāsam vikāse vikāsāt vikasati vikāsinā'),
t('prathā', 'प्रथा', 'Пратха',
  'развёртывание: то, как Сознание расстилает себя вовне. Глагол `prathate` — '
  '«разворачивается», и им у Кшемараджи описано всякое явление.',
  forms='prathām prathayantyaḥ prathate prathamānatā prathana prathanam'),
t('ābhāsa', 'आभास', 'Абхаса',
  'явление — вещь, взятая как то, чем она сияет в Сознании, а не как то, что '
  'стоит вне его.',
  forms='ābhāsaḥ ābhāsam ābhāse ābhāsayati ābhāti avabhāsaḥ avabhāsita '
        'avabhāsitāḥ avabhāsakatvāt'),
t('svarūpa', 'स्वरूप', 'Сварупа',
  'собственная сущностная природа — то, чем существо было всегда и что от него '
  'закрыто. `svabhāva` — то же самое другим словом.',
  forms='svarūpam svarūpe svarūpeṇa svarūpasya svarūpāt svabhāvaḥ svabhāva '
        'svabhāvam svabhāvatvāt'),
t('viśrānti', 'विश्रान्ति', 'Вишранти',
  'упокоение — не отдых после дела, а то, во что всякое движение приходит и в '
  'чём держится. Утпаладева говорит: упокоение всего пережитого в себе самом '
  'и зовётся «Я».',
  forms='viśrāntiḥ viśrāntim viśrāntyā viśrāntau viśrāntāḥ viśrāntayaḥ '
        'viśrāmyati viśrāmāt viśrāntā'),
t('bala', 'बल', 'Бала',
  'Сила — то, ухватившись за что, мантры делают своё дело; и то, обретя что, '
  'человек уподобляет вселенную себе.',
  forms='balam balāt balena balasya'),
t('unmeṣa', 'उन्मेष', 'Унмеша',
  '«раскрытие глаз»: миг, в который Сознание раскрывается вовне. Пара к нему — '
  '`nimeṣa`, смыкание.',
  forms='unmeṣaḥ unmeṣam unmeṣāt unmīlayati unmīlanam unmīlana unmiṣat '
        'nimeṣa nimīlana'),
]),

('Вселенная и её ступени', [
t('viśva', 'विश्व', 'Вишва',
  'вселенная — всё, от Садашивы до стихии земли. У Кшемараджи она не сделана '
  'из чего-то, а развёрнута на собственном холсте Сознания.',
  forms='viśvam viśve viśvasya viśvāt viśvena'),
t('jagat', 'जगत्', 'Джагат',
  'мир — та же вселенная, взятая как движущееся и живое.',
  forms='jagataḥ jagati jagatā'),
t('tattva', 'तत्त्व', 'Таттва',
  'начало, «то-самость»: ступень Реальности. Их тридцать шесть, от Шивы до '
  'земли; в этой книге они пересчитаны в седьмом афоризме.',
  forms='tattvam tattve tattvāni tattvasya tattvāt tattvānām'),
t('māyā', 'माया', 'Майя',
  'не иллюзия, а Сила разделения: то, чем Единый являет себя многим, ничего '
  'при этом не теряя.',
  forms='māyāyām māyām māyayā māyā-śaktiḥ māyīyaḥ māyīya māyīyam'),
t('kañcuka', 'कञ्चुक', 'Канчука',
  'оболочка: пять сжатий всемогущества, всеведения, полноты, вечности и '
  'вездесущия — `kalā`, `vidyā`, `rāga`, `kāla`, `niyati`.',
  forms='kañcukam kañcuke kañcukāḥ kañcuka-valitatvāt'),
t('kalā', 'कला', 'Кала',
  'доля: оболочка, оставляющая существу «умение кое-что» вместо всемогущества. '
  'В другом месте — просто «доля», часть.',
  forms='kalām kalāyāḥ kalayā kalāḥ kalābhiḥ'),
t('vidyā', 'विद्या', 'Видья',
  'знание — и та таттва, `śuddhavidyā`, где «Я» и «это» ещё держатся вместе; '
  'ниже майи она же становится узким знанием одного человека.',
  forms='vidyām vidyayā vidyāyāḥ vidyā-pade'),
t('prakṛti', 'प्रकृति', 'Пракрити',
  'природа — исток вещественного мира и трёх его свойств.',
  forms='prakṛtiḥ prakṛtim prakṛteḥ prakṛtyā'),
t('pada', 'पद', 'Пада',
  '«место», ступень, состояние: `cetanapada` — уровень чистого Сознания, '
  '`pāśavapada` — состояние связанного.',
  forms='padam pade padāt padasya padāni padaiḥ'),
t('bheda', 'भेद', 'Бхеда',
  'разделение, двойственность — то, из-за чего вселенная видится многой. '
  'Обратное ему — `abheda`, недвойственность.',
  forms='bhedaḥ bhedam bhede bhedāt bhedena bhedāḥ bhinnaḥ bhinnam bhinna '
        'bhinnāḥ vibhinnam'),
t('abheda', 'अभेद', 'Абхеда',
  'недвойственность: не «слияние двух», а то, что двух и не было. Пара к '
  '`bheda`.',
  forms='abhedaḥ abhedam abhede abhedāt abhedena abhinnaḥ abhinnam abhinna '
        'aikātmyam aikātmyena aikātmyāt aikyam aikyena'),
]),

('Познающий и познаваемое', [
t('pramātṛ', 'प्रमातृ', 'Праматри',
  'познающий — тот, для кого что-либо есть. Уровней его семь, от Шивы до '
  'связанного существа.',
  forms='pramātā pramātuḥ pramātaraḥ pramātṛtā pramātṛtāyām pramātari '
        'pramātṝṇām pramātṛbhiḥ'),
t('pramāṇa', 'प्रमाण', 'Прамана',
  'способ познания — то, чем познающий берёт познаваемое.',
  forms='pramāṇam pramāṇe pramāṇena pramāṇāni'),
t('prameya', 'प्रमेय', 'Прамея',
  'познаваемое — то, что взято. То же слово другим боком — `vedya`.',
  forms='prameyam prameye prameyāṇi prameyasya vedyam vedye vedyaḥ'),
t('grāhaka', 'ग्राहक', 'Грахака',
  '«берущий» — познающий, взятый как тот, кто схватывает. Пара к `grāhya`, '
  'схватываемому; их разделение и делает вселенную многой.',
  forms='grāhakaḥ grāhakam grāhakasya grāhakāṇām grāhakatva grāhakatvam '
        'grāhyam grāhya grāhyāṇām'),
t('cetana', 'चेतन', 'Четана',
  'сознающий; `cetanapada` — уровень чистого Сознания, `cetya` — то, что им '
  'сознаётся.',
  forms='cetanaḥ cetanam cetane cetya cetyena cetyam'),
t('citta', 'चित्त', 'Читта',
  'ум. Пятая сутра говорит о нём главное: ум — не что-то другое, а сама Citi, '
  'сжавшаяся до предмета.',
  forms='cittam cittena cittasya citte'),
t('buddhi', 'बुद्धि', 'Буддхи',
  'различающая способность: та, что решает «это — то».',
  forms='buddhiḥ buddhim buddhyā buddheḥ buddhau buddhi-tattve'),
t('manas', 'मनस्', 'Манас',
  'ум как орудие: тот, что складывает впечатления в образ.',
  forms='manaḥ manasā manasi manasaḥ mano'),
t('bodha', 'बोध', 'Бодха',
  'разумение, пробуждённость — Сознание, взятое как то, что понимает.',
  forms='bodhaḥ bodham bodhe bodhena bodhāt'),
t('śūnya', 'शून्य', 'Шунья',
  'пустота — состояние, где нет ничего познаваемого. Не цель: и в ней, '
  'говорит Кшемараджа, остаются отпечатки ума.',
  forms='śūnyam śūnye śūnyāt śūnyena śūnyasya śūnya-bhūmiḥ'),
]),

('Семь познающих', [
t('sakala', 'सकल', 'Сакала',
  '«с долями» — связанное существо, у которого все три грязи: обычный человек.',
  forms='sakalaḥ sakalam sakale sakalāḥ sakalānām sakalasya'),
t('pralayākala', 'प्रलयाकल', 'Пралаякала',
  'познающий пустоту: тот, у кого нет майической грязи, но кто спит в '
  'растворении.',
  forms='pralayākalaḥ pralayākalāḥ pralayakevalinām pralayakevalī',
  alias='пралаякала пралаякевалин'),
t('vijñānākala', 'विज्ञानाकल', 'Виджнянакала',
  'чистое Сознание без делания: у него осталась одна первая грязь. Выше майи и '
  'ниже Чистой Видьи.',
  forms='vijñānākalaḥ vijñānākalāḥ vijñāna-akalatā vijñānākalatā',
  alias='виджнянакала виджнанакала'),
t('paśu', 'पशु', 'Пашу',
  '«скот» — связанное существо, взятое как привязанное. Не брань: слово '
  'говорит о путах, а не о достоинстве. Пара к нему — `pati`, Владыка.',
  forms='paśoḥ paśum paśavaḥ paśūnām pāśave paśu-daśāyām'),
t('pati', 'पति', 'Пати',
  'Владыка — то же существо, но узнавшее себя. Состояние `pati` и состояние '
  '`paśu` различаются не природой, а тем, видна ли она.',
  forms='patiḥ patyuḥ pati-daśāyām pati-bhūmikāyām'),
t('bhūmikā', 'भूमिका', 'Бхумика',
  '«роль» — та, что играет лицедей. Восьмая сутра говорит ими о философских '
  'школах: все они — роли одного и того же Сознания.',
  forms='bhūmikām bhūmikāḥ bhūmikāyām bhūmikābhyām'),
]),

('Узы', [
t('mala', 'मल', 'Мала',
  'грязь, пятно: то, чем сознание закрыто от себя самого. Их три, и в девятой '
  'сутре они выведены из сжатия трёх Сил.',
  forms='malam male malāḥ malāni mala-āvṛtaḥ'),
t('āṇava', 'आणव', 'Анава',
  'первая грязь: «я неполон». Не проступок и не незнание чего-то, а сжатие '
  'самой Воли.',
  forms='āṇavam āṇavaḥ āṇavasya āṇave apūrṇam-manyatā apūrṇammanyatā'),
t('akhyāti', 'अख्याति', 'Акхьяти',
  '«неявленность» — изначальное неведение. Кшемараджа ловит его на слове: если '
  'оно не является, остаётся одно знание; а если является — то являет себя '
  'знание же.',
  forms='akhyātiḥ akhyātim khyāti khyātiḥ aparijñāne aparijñānam aparijñāna'),
t('vyāmohitatā', 'व्यामोहितता', 'Вьямохитата',
  'сбитость с толку собственными силами. Двенадцатая сутра говорит, что это и '
  'значит быть душою в круговороте: не грех и не кара, а неузнавание.',
  forms='vyāmohitatām vyāmohitatvam vyāmohitatvena vyāmohitaḥ vyāmohayati '
        'vyāmohinā'),
t('saṁsāra', 'संसार', 'Самсара',
  'круговорот — не место, а состояние: быть душою в нём значит не знать, что '
  'пять действий совершаешь ты.',
  forms='saṁsāraḥ saṁsāre saṁsāram saṁsṛtau saṁsāritvam saṁsārī saṁsāri'),
t('vikalpa', 'विकल्प', 'Викальпа',
  'мысль, различающее представление: «это — не то». `avikalpa` — состояние, '
  'где их нет, и туда ведёт первое из средств восемнадцатой сутры.',
  forms='vikalpaḥ vikalpam vikalpe vikalpāt vikalpānām vikalpa-kṛiyām '
        'avikalpa avikalpaḥ avikalpam'),
t('abhimāna', 'अभिमान', 'Абхимана',
  'ошибочное представление о себе: принять тело, дыхание или ум за Самость.',
  forms='abhimānaḥ abhimānam abhimāne abhimānena abhimanyate'),
t('saṁskāra', 'संस्कार', 'Самскара',
  'отпечаток: след пережитого, который поднимет его вновь. Ими же держится '
  'самадхи в состоянии после самадхи.',
  forms='saṁskāraḥ saṁskāram saṁskāreṇa saṁskārāḥ saṁskāravatī'),
t('pāśa', 'पाश', 'Паша',
  'путы. Растворяются они не силой, а узнаванием собственной природы.',
  forms='pāśaḥ pāśam pāśān pāśa-rāśi bandhaḥ bandha'),
]),

('Пять действий', [
t('pañcakṛtya', 'पञ्चकृत्य', 'Панчакритья',
  'пятеричное действие: явление, поддержание, вбирание, сокрытие и милость. '
  'Совершает их Господь — и совершает то же самое каждый, но не знает об этом; '
  'в знании об этом авторстве вся книга и держится.',
  forms='kṛtyam kṛtya kṛtyāni pañcavidha pañca-kṛtya kāritvam kāritva '
        'kāritvasya kāritve',
  alias='панчакритья пятеричное действие'),
t('sṛṣṭi', 'सृष्टि', 'Сришти',
  'проявление, извержение мира — первое из пяти действий.',
  forms='sṛṣṭiḥ sṛṣṭim sṛṣṭau sṛṣṭi-sthiti sṛjati sarga sargaḥ sarge'),
t('sthiti', 'स्थिति', 'Стхити',
  'поддержание: то, чем явленное держится.',
  forms='sthitiḥ sthitim sthitau sthitayaḥ sthiti-devyā sthāpakatā sthāpyate'),
t('saṁhāra', 'संहार', 'Самхара',
  'вбирание, растворение — не уничтожение, а возвращение в Того, кто явил.',
  forms='saṁhāraḥ saṁhāram saṁhāre saṁhārau saṁhṛtiḥ saṁhriyate saṁhartṛtā'),
t('vilaya', 'विलय', 'Вилая',
  'сокрытие: четвёртое действие, которым Бог прячет Себя от Себя же. Без него '
  'не было бы и милости.',
  forms='vilayaḥ vilayam vilaye vilaya-padam vilaya-kāritā'),
t('anugraha', 'अनुग्रह', 'Ануграха',
  'милость — пятое действие: то, чем Он открывает Себя. Здесь оно описано как '
  'раскрытие того, что вещь едина со Светом.',
  forms='anugrahaḥ anugraham anugrahe anugrahāt anugṛhyate anugrahītṛtā'),
t('kartṛtva', 'कर्तृत्व', 'Картритва',
  'деятельность, авторство: то, что делаешь ты. Ограниченное `kiñcitkartṛtva` '
  '— «умение кое-что» — и есть всемогущество, сжатое оболочкой.',
  forms='kartṛtvam kartṛtva kartṛtvena sarvakartṛtvam kiñcid-kartṛtva'),
t('devatācakra', 'देवताचक्र', 'Деватачакра',
  'круг божеств Сознания: силы чувств и ума, взятые не как орудия, а как '
  'божества. Власть над ним — плод двадцатой сутры.',
  forms='devatā devatām devatāḥ devatā-cakram devatā-cakra saṁvid-devatā',
  alias='деватачакра круг божеств'),
t('vāmeśvarī', 'वामेश्वरी', 'Вамешвари',
  '«Владычица, изливающая» — Сила, извергающая вселенную; она же ведёт '
  'обратным ходом из круговорота. Её четыре круга — `khecarī`, `gocarī`, '
  '`dikcarī`, `bhūcarī`.',
  forms='vāma-īśvarī vāmeśā vāma-īśvarī-ākhyā vāmeśā-ādyāḥ'),
t('khecarī', 'खेचरी', 'Кхечари',
  '«идущая в пространстве» — круг сил самого познающего. В связанном она '
  'прячет Небо Сознания, в свободном раскрывает.',
  forms='khecarīm khecaryāḥ khecarī-cakreṇa khecarītva'),
t('gocarī', 'गोचरी', 'Гочари',
  'круг сил внутреннего орудия души — ума, самости и разума.',
  forms='gocarīm gocaryāḥ gocarī-cakreṇa gocarītvena gocarītva'),
t('dikcarī', 'दिक्चरी', 'Дикчари',
  'круг сил внешнего орудия — чувств, глядящих по сторонам.',
  forms='dikcarīm dikcaryāḥ dikcarī-cakreṇa dikcarītvena dikcarītva '
        'dikcarīcakreṇa'),
t('bhūcarī', 'भूचरी', 'Бхучари',
  'круг сил самих вещей: то, чем предметы стоят вовне и порознь — или, у '
  'свободного, раскрывают Сердце.',
  forms='bhūcarīm bhūcaryāḥ bhūcarī-cakreṇa bhūcarītvena bhūcarītva'),
]),

('Тело, дыхание, средоточия', [
t('deha', 'देह', 'Деха',
  'тело. Не помеха: у Кшемараджи освобождение случается в теле, а не после '
  'него.',
  forms='dehaḥ deham dehe dehena dehasya dehāt deha-ādi'),
t('prāṇa', 'प्राण', 'Прана',
  'дыхание-жизнь — и восходящий его ток в частности. Пятеричное дыхание: '
  '`prāṇa`, `apāna`, `samāna`, `udāna`, `vyāna`.',
  forms='prāṇaḥ prāṇam prāṇe prāṇena prāṇāḥ prāṇasya prāṇān prāṇa-śakti '
        'apānaḥ apāna samānaḥ samāna udānaḥ udāna udāna-śaktim vyānaḥ vyāna '
        'vyāna-śaktim'),
t('nāḍī', 'नाडी', 'Нади',
  'русло, по которому идёт дыхание. Срединное — `suṣumnā`, и семнадцатая сутра '
  'говорит о нём как о середине всего.',
  forms='nāḍyaḥ nāḍīm nāḍyā nāḍyām nāḍī-dvaya brahmanāḍī suṣumnā'),
t('madhya', 'मध्य', 'Мадхья',
  'середина. У Кшемараджи это не место в теле, а само Сознание: то '
  'внутреннейшее, к чему всё прилеплено. Его раскрытие и есть путь.',
  forms='madhyam madhye madhyāt madhyena madhyasya madhya-śakti madhya-bhūtā'),
t('hṛdaya', 'हृदय', 'Хридая',
  'Сердце — не орган, а средоточие: то, куда всё сходится и откуда всё '
  'исходит.',
  forms='hṛdayam hṛdaye hṛdayena hṛdayasya hṛdi hṛd'),
t('dvādaśānta', 'द्वादशान्त', 'Двадашанта',
  '«конец двенадцати» — точка на двенадцать пальцев от тела, где дыхание '
  'кончается и начинается.',
  forms='dvādaśānte dvādaśāntaḥ dvādaśāntam'),
t('puryaṣṭaka', 'पुर्यष्टक', 'Пурьяштака',
  '«восьмиградие» — тонкое тело из восьми: пяти тонких стихий, разума, '
  'самости и ума. Им и осаждён человек, пока не укоренится в одном.',
  forms='puryaṣṭakam puryaṣṭakena puryaṣṭake'),
t('cakra', 'चक्र', 'Чакра',
  'колесо: и круг божеств, и собрание сил, и средоточие в теле. У Кшемараджи '
  'чаще первое.',
  forms='cakram cakre cakrāṇi cakrasya cakreṇa cakrāṇām cakra-īśvaraḥ'),
]),

('Путь и вхождение', [
t('upāya', 'उपाय', 'Упая',
  'средство. Лёгкое средство (`sukhopāya`) — то, чем эта книга и хвалится: '
  'путь, не требующий ни задержек дыхания, ни поз.',
  forms='upāyaḥ upāyam upāyāḥ upāye upāyena sukha-upāya sukha-upāyatvam'),
t('samāveśa', 'समावेश', 'Самавеша',
  'поглощённость, в которой существо совпадает с Шивой. `āveśa` — то же '
  'слово, вхождение.',
  forms='samāveśaḥ samāveśam samāveśe samāveśena samāveśa-bhūḥ samāviṣṭaḥ '
        'āveśaḥ āveśam āveśāt āveśe āveśa-vaśāt'),
t('samādhi', 'समाधि', 'Самадхи',
  'сосредоточение. Девятнадцатая сутра о том, как сделать его постоянным '
  '(`nityodita`) — то есть не терять и в состоянии после него, `vyutthāna`.',
  forms='samādhiḥ samādhim samādhau samādhinā vyutthānam vyutthāne '
        'vyutthāna-daśāyām nitya-udita nitya-udite'),
t('mudrā', 'मुद्रा', 'Мудра',
  'печать. `bhairavīmudrā` — взор вовне при внимании внутрь; `kramamudrā` — '
  'та, что вмещает разом внешнее и внутреннее и потому держит самадхи всегда.',
  forms='mudrām mudrayā mudrā-ātmā mudrā-kramaḥ bhairavīya-mudrā krama-mudrayā'),
t('krama', 'क्रम', 'Крама',
  'череда, последовательность — и имя школы, у которой Кшемараджа берёт '
  '`kramamudrā`, `haṭhapāka` и `alaṅgrāsa`.',
  forms='kramaḥ kramam krame krameṇa kramāt krama-sūtreṣu'),
t('haṭhapāka', 'हठपाक', 'Хатхапака',
  '«варка силой» — приём Крамы: держать предмет в Сознании, пока он не '
  'сравняется с ним, как пища с огнём.',
  forms='haṭhapāka haṭhapākaḥ haṭhapāka-krameṇa'),
t('alaṅgrāsa', 'अलंग्रास', 'Аланграса',
  '«поглощение досыта» — пара к `haṭhapāka`: предмет поглощается без остатка, '
  'и семени для нового круговорота не остаётся.',
  forms='alaṅgrāsa alaṅgrāsaḥ alaṅgrāsa-yuktyā'),
t('bhāvanā', 'भावना', 'Бхавана',
  'созерцательное держание в уме — не воображение, а приведение к бытию.',
  forms='bhāvanām bhāvanayā bhāvayet bhāvanā-ādikam'),
t('pariśīlana', 'परिशीलन', 'Паришилана',
  'упражнение: усматривать одно и то же снова и снова, покуда оно не станет '
  'своим.',
  forms='pariśīlanam pariśīlana pariśīlyamānam pariśīlayanti abhyāsaḥ abhyāsa'),
t('turya', 'तुर्य', 'Турья',
  '«четвёртое» состояние — за бодрствованием, сном со сновидениями и глубоким '
  'сном. За ним `turyātīta`, «превзошедшее четвёртое».',
  forms='turyam turye turyasya turīya turīyā turya-atīta turyātīta',
  alias='турья турия'),
]),

('Плод', [
t('pratyabhijñā', 'प्रत्यभिज्ञा', 'Пратьябхиджня',
  '«узнавание»: не приобретение нового, а признание давно знакомого — как '
  'узнают лицо. Имя и книги, и всей школы.',
  forms='pratyabhijñām pratyabhijñāyām pratyabhijñāyāḥ pratyabhijñāta '
        'pratyabhijñāyamānaḥ'),
t('mukti', 'मुक्ति', 'Мукти',
  'Освобождение; то же самое — `mokṣa`.',
  forms='muktiḥ muktim mukteḥ mukti-daḥ mokṣaḥ mokṣam mokṣāt'),
t('jīvanmukti', 'जीवन्मुक्ति', 'Дживанмукти',
  'освобождение при жизни: свобода, не покидая тела. Шестнадцатая сутра только '
  'о нём.',
  forms='jīvat jīvataḥ jīvat-muktiḥ jīvanmuktaḥ jīvat-muktāḥ jīvanmuktāḥ',
  alias='дживанмукти дживанмукта'),
t('īśvaratā', 'ईश्वरता', 'Ишварата',
  'владычество: власть над кругом божеств собственного Сознания. Тот самый '
  'плод, которым книга кончается.',
  forms='īśvaratām īśvaratā-padam aiśvaryam aiśvaryasya aiśvarya-śaktiḥ '
        'sāmrājyam'),
t('pūrṇatā', 'पूर्णता', 'Пурната',
  'полнота — состояние, в котором нечего добавить и нечего желать.',
  forms='pūrṇatām pūrṇatvam pūrṇaḥ pūrṇam pūrṇā pūrṇa-ānanda pūrṇatāpādanena'),
t('bhoga', 'भोग', 'Бхога',
  'вкушение, наслаждение. В Трике оно не противопоставлено освобождению: '
  'путь ведёт к обоим.',
  forms='bhogaḥ bhogam bhoge bhogena bhogāḥ bhoga-mokṣa'),
t('siddhi', 'सिद्धि', 'Сиддхи',
  'свершение. В первой же сутре оно значит не сверхспособность, а тройное '
  'дело: явление мира, его держание и вбирание.',
  forms='siddhiḥ siddhim siddhau siddheḥ siddhīnām sidhyanti'),
]),

('Писание, учитель, милость', [
t('śaktipāta', 'शक्तिपात', 'Шактипата',
  '«нисхождение Силы»: миг, в который Милость касается человека. Без него, '
  'говорит Кшемараджа, собственная сила не развернётся.',
  forms='śaktipātaḥ śaktipātam śakti-pāta śakti-pātaḥ śāṅkaraḥ'),
t('guru', 'गुरु', 'Гуру',
  'учитель. Одиннадцатая сутра кончается тем, что без его наставления тайный '
  'ход пяти действий не открывается никому.',
  forms='guruḥ gurum guroḥ guruṇā gurave gurubhiḥ sat-guru'),
t('upadeśa', 'उपदेश', 'Упадеша',
  'наставление: устное указание учителя, а не вычитанное знание.',
  forms='upadeśaḥ upadeśam upadeśena upadeśe upadeśāt upadeśatas'),
t('bhakti', 'भक्ति', 'Бхакти',
  'преданность. Книга написана для тех, у кого она есть, а острого ума для '
  '«Ишварапратьябхиджни» — нет.',
  forms='bhaktiḥ bhaktim bhaktyā bhakti-bhājaḥ bhakti-bhājām bhakta-janam'),
t('śāstra', 'शास्त्र', 'Шастра',
  'писание, трактат; `āgama` — переданное откровение.',
  forms='śāstram śāstre śāstreṣu śāstrasya āgamaḥ āgamam āgame āgameṣu'),
t('sūtra', 'सूत्र', 'Сутра',
  '«нить» — краткое изречение, которое без разбора не разворачивается. Их '
  'здесь двадцать.',
  forms='sūtram sūtre sūtreṣu sūtrasya'),
t('spanda', 'स्पन्द', 'Спанда',
  'трепет, вибрация: то живое дрожание Сознания, о котором учат '
  '«Спанда-карики». Кшемараджа ссылается на них чаще всего.',
  forms='spandaḥ spandam spande spanda-śāstre spanda-bhūḥ'),
t('trika', 'त्रिक', 'Трика',
  '«троица» — имя школы: Шива, Шакти и связанное существо, взятые как одно.',
  forms='trikam trike trikasya trika-sāre trikasāre'),
]),
]


def terms():
    return _terms(SECTIONS)


def index():
    return _index(SECTIONS)


# --- где термин разбирается ------------------------------------------------


def occurrences():
    """Сколько раз термин помечен в каждом абзаце перевода.

    Возвращает {термин: {(часть, номер блока): сколько раз}}. Номер блока —
    ключ в `ru/<часть>.json`, то есть тот же номер, которым абзац зовётся при
    сборке страницы.

    Перевод самих сутр сюда не идёт, и это нарочно: он не наш, и якорь «здесь
    это разбирается» на нём стоял бы не по делу — сутра не разбирает, она
    называет.
    """
    tables = index()
    out = hits()
    for path in sorted(glob.glob(os.path.join(HERE, 'ru', '*.json'))):
        pid = os.path.basename(path)[:-len('.json')]
        for key, text in json.load(open(path, encoding='utf-8')).items():
            if isinstance(text, str):
                count(out, text, (pid, int(key)), tables)
    return out


def anchors():
    """Якоря, которые сборка страниц должна расставить: {часть: {блок: id}}.

    На один абзац якорь один, даже если в него метят несколько статей: id у
    элемента может быть только один. Первая по порядку словаря статья даёт
    имя, остальные ссылаются на то же имя — адрес от этого не портится.
    """
    out = collections.defaultdict(dict)
    tgt = targets(occurrences())
    for term in terms():
        for pid, block in tgt.get(term.iast, ()):
            out[pid].setdefault(block, 'g-' + keyof(term))
    for pid, marks in out.items():
        if len(set(marks.values())) != len(marks):
            raise SystemExit('якорь повторяется в части %s' % pid)
    return out


def links():
    """Ссылки словаря в текст: {термин: [(адрес части, якорь)]}."""
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
    print('статей: %d' % sum(1 for _ in terms()))
    print('без единого вхождения: %s'
          % (', '.join(x.iast for x in terms() if not got.get(x.iast)) or '—'))
    tgt = targets(got)
    for term in terms():
        n = sum(got.get(term.iast, {}).values())
        print('%4d %-16s %s' % (n, term.iast,
                                ' · '.join('%s:%d' % p for p in tgt.get(term.iast, ()))))
