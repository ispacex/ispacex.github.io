# Главы «Тантрасары», их адреса на сайте и у источника.
#
# Название главы взято со страницы-оглавления источника (узел 919), а не из
# «Вступления» на самой странице главы: во «Вступлении» ко 2-й главе у
# источника стоит имя 1-й — Vijñānabhedaprakāśanam вместо Anupāyaprakāśanam.
# Оглавление же перечисляет все двадцать два имени и не путается.
CHAPTERS = [
    ('920', 1,  'Vijñānabhedaprakāśanam',   'Объяснение различных видов знания'),
    ('921', 2,  'Anupāyaprakāśanam',        'Объяснение Anupāya, лишённой методов'),
    ('935', 3,  'Śāmbhavopāyaprakāśanam',   'Объяснение метода Śambhu'),
    ('936', 4,  'Śāktopāyaprakāśanam',      'Объяснение метода Śakti'),
    ('937', 5,  'Āṇavaprakāśanam',          'Объяснение метода ограниченного существа'),
    ('938', 6,  'Kālādhvaprakāśanam',       'Объяснение пути Времени'),
    ('939', 7,  'Deśādhvaprakāśanam',       'Объяснение пути Пространства'),
    ('940', 8,  'Tattvasvarūpaprakāśanam',  'Объяснение сущностной природы категорий'),
    ('941', 9,  'Tattvabhedaprakāśanam',    'Объяснение разделения по категориям'),
    ('942', 10, 'Kalādyadhvaprakāśanam',    'Объяснение пути Kalā-s и прочих'),
    ('943', 11, 'Śaktipātaprakāśanam',      'Объяснение нисхождения Силы'),
    ('944', 12, 'Snānaprakāśanam',          'Объяснение омовения'),
    ('945', 13, 'Samayidīkṣāprakāśanam',    'Объяснение посвящения в дисциплину'),
    ('946', 14, 'Putrakadīkṣāprakāśanam',   'Объяснение посвящения в духовные сыновья'),
    ('947', 15, 'Sapratyayadīkṣāprakāśanam','Объяснение посвящения с убеждённостью'),
    ('948', 16, 'Parokṣadīkṣāprakāśanam',   'Объяснение посвящения отсутствующего'),
    ('949', 17, 'Liṅgoddhāraḥ',             'Удаление метки, или знака'),
    ('950', 18, 'Abhiṣekaprakāśanam',       'Объяснение освящения'),
    ('951', 19, 'Śrāddhadīkṣāprakāśanam',   'Объяснение посвящения при поминовении умершего'),
    ('952', 20, 'Śeṣavartanaprakāśanam',    'Объяснение того, как жить дальше'),
    ('953', 21, 'Āgamaprāmāṇyaprakāśanam',  'Объяснение авторитетности писаний'),
    ('954', 22, 'Kulayāgaprakāśanam',       'Объяснение ритуала Kaula'),
]

# (id у источника, кусок адреса, название) — в том виде, какого ждёт common/page.py.
PARTS = [(pid, 'ch%d' % n, 'Глава %d — %s' % (n, name)) for pid, n, name, _ in CHAPTERS]

SRC = 'https://www.sanskrit-trikashaivism.com/ru/'
SLUG = 'tantrasara-%s-trika-scriptures-non-dual-shaivism-of-kashmir-ru/%s'
SRC_URL = {pid: SLUG % (n, pid) for pid, n, _, _ in CHAPTERS}
# Оглавление и введение переводчика.
SRC_URL['919'] = 'tantrasara-introduction-trika-scriptures-non-dual-shaivism-of-kashmir-ru/919'
