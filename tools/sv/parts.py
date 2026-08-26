# Двадцать гимнов Śivastotrāvalī, их адреса на сайте и у источника.
#
# Санскритское имя гимна перенесено из заголовков источника как есть, вместе с
# порядковым числительным внутри («dvitīyaṁ», «trayodaśaṁ»): это часть имени, а
# не подпись, которую мы к нему добавили. Русская строка рядом — перевод того,
# как называет гимн по-английски Габриэль Pradīpaka.
#
# Число строф — не наш счёт, а объявленное во вступлении источника. Сошлись ли
# они со строфами на странице, спрашивает `check.py`.
HYMNS = [
    (1,  'Bhaktivilāsākhyaṁ stotram',                 'игра преданности',              26),
    (2,  'Sarvātmaparibhāvanākhyaṁ dvitīyaṁ stotram', 'созерцание Самости всего',      29),
    (3,  'Praṇayaprasādākhyaṁ tṛtīyaṁ stotram',       'милость в ответ на поклон',     21),
    (4,  'Surasodbalākhyaṁ caturthaṁ stotram',        'сила от доброго сока',          25),
    (5,  'Svabalanideśanākhyaṁ pañcamaṁ stotram',     'указание на собственную силу',  26),
    (6,  'Adhvavisphuraṇākhyaṁ ṣaṣṭhaṁ stotram',      'борение на пути',               11),
    (7,  'Vidhuravijayanāmadheyaṁ saptamaṁ stotram',  'победа над мукой разлуки',       9),
    (8,  'Alaukikodbalanākhyamaṣṭamaṁ stotram',       'нездешняя сила',                13),
    (9,  'Svātantryavijayākhyaṁ navamaṁ stotram',     'победа Абсолютной Свободы',     20),
    (10, 'Avicchedabhaṅgākhyaṁ daśamaṁ stotram',      'разрыв непрерывности',          26),
    (11, 'Autsukyaviśvasitanāmaikādaśaṁ stotram',     'томление и уверенность',        15),
    (12, 'Rahasyanirdeśanāma dvādaśaṁ stotram',       'указание на тайну',             29),
    (13, 'Saṅgrahastotranāma trayodaśaṁ stotram',     'гимн, ставший сводом',          20),
    (14, 'Jayastotranāma caturdaśaṁ stotram',         'гимн победы',                   24),
    (15, 'Bhaktistotranāma pañcadaśaṁ stotram',       'гимн преданности',              19),
    (16, 'Pāśān-udbhedanāma ṣoḍaśaṁ stotram',         'разрыв пут',                    30),
    (17, 'Divyakrīḍābahumānanāma saptadaśaṁ stotram', 'дар божественной Игры',         48),
    (18, 'Āviṣkāranāmāṣṭādaśaṁ stotram',              'откровение',                    21),
    (19, 'Udyotanābhidhānamekonaviṁśaṁ stotram',      'озарение',                      17),
    (20, 'Carvarṇābhidhānaṁ viṁśaṁ stotram',          'вкушение',                      21),
]

# (id у источника, кусок адреса, название) — в том виде, какого ждёт common/page.py.
#
# id части здесь не номер узла, как у соседних конвейеров, а номер гимна: всё
# писание лежит у источника одной страницей, и режет её `convert.py`.
PARTS = [(str(n), 'ch%d' % n, 'Гимн %d — %s' % (n, name)) for n, name, _, _ in HYMNS]

SRC = 'https://www.sanskrit-trikashaivism.com/en/'
NODE = 'scriptures-trika-scriptures-shivastotraavalii/1005'

# Качается одна страница; у каждого гимна на ней свой якорь «#ChapterN».
SRC_PAGE = {'1005': NODE}
SRC_URL = {str(n): '%s#Chapter%d' % (NODE, n) for n, _, _, _ in HYMNS}
