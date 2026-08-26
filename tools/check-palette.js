/* Проверка палитры перехода (⌘K): свёртка та же, что у поиска, и указатель цел.
 *
 *     ./tools/build-local.sh            # собрать сайт в _sitecheck/
 *     node tools/check-palette.js       # прогнать проверки по нему
 *
 * Проверяется три вещи, и каждая ломается тихо:
 *
 *   1. **Свёртка не разошлась.** У палитры она своя — сорок строк в
 *      assets/js/palette.js, — потому что тащить ради неё весь движок поиска
 *      (49 КБ) на каждую страницу незачем. Копия расходится с оригиналом
 *      молча: «натья» перестанет находить `nāṭya`, и никто не заметит, пока не
 *      попробует. Здесь обе прогоняются по одному набору слов и обязаны
 *      совпасть знак в знак.
 *   2. **Указатель собрался и он полон.** У каждой страницы есть название,
 *      адрес и раздел; названий, оставшихся адресом, — не больше, чем было.
 *   3. **Палитра доводит до места.** Запросы, которые читатель наберёт в
 *      первую очередь, — «Тантралока», «tantraloka», «словарь», «паруса» —
 *      дают первой строкой ту самую страницу.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const HERE = path.dirname(__dirname);
const SITE = process.argv[2] || path.join(HERE, '_sitecheck');

const SiteSearch = require(path.join(HERE, 'sitesearch', 'search.js'));

// --- свёртка палитры, вынутая из её собственного файла ----------------------
//
// Вынимается кусок исходника, а не переписывается сюда: переписанное проверяло
// бы себя само. Скрипт браузерный и в require не годится — там DOM с первой же
// строки, — поэтому берётся ровно то, что стоит между метками.

const src = fs.readFileSync(path.join(HERE, 'assets', 'js', 'palette.js'), 'utf8');
const from = src.indexOf('var CYRILLIC = {');
const to = src.indexOf('/* --- отбор и порядок');
if (from < 0 || to < 0) {
	console.log('в palette.js не нашлось свёртки — метки переехали?');
	process.exit(1);
}
const fold = new Function(src.slice(from, to) + '\nreturn fold;')();

// Слова, на которых свёртка и ломается: буква зависит от соседней, кириллица
// встречается с диакритикой, «дж» читается как одно.
const WORDS = [
	'śaktipāta', 'шактипата', 'saktipata', 'Тантралока', 'Tantrāloka',
	'натья', 'nāṭya', 'Natya', 'джняна', 'jñāna', 'нритта', 'nṛtta',
	'кальпа юга', 'яма', 'майя', 'объявление', 'пятая', 'по-японски',
	'Пратьябхиджняхридаям', 'Pratyabhijñāhṛdayam', 'Śivastotrāvalī',
	'Шивастотравали', 'щока', 'цвет', 'Ṣaṭtriṁśattattvasandoha',
	'Теория плавания под парусами', 'Обруч', 'Kṣemarāja', 'Кшемараджа',
];

function drift() {
	let bad = 0;
	for (const w of WORDS) {
		const a = SiteSearch.fold(w), b = fold(w);
		if (a !== b) {
			console.log('   ✗ %s → поиск «%s», палитра «%s»', w, a, b);
			bad++;
		}
	}
	console.log('\nСвёртка: сошлось %d из %d', WORDS.length - bad, WORDS.length);
	return bad;
}

// --- указатель --------------------------------------------------------------

function index() {
	const file = path.join(SITE, 'nav-index.json');
	if (!fs.existsSync(file)) {
		console.log('\nnav-index.json не собран — сначала ./tools/build-local.sh');
		return null;
	}
	const data = JSON.parse(fs.readFileSync(file, 'utf8'));
	const pages = data.pages || [];
	const noTitle = pages.filter((p) => !p.title || !p.title.trim());
	const noSection = pages.filter((p) => !p.section);
	const asUrl = pages.filter((p) => p.title === p.url.replace(/^\//, '').replace(/\//g, ' / ').trim());
	console.log('\nУказатель: страниц %d, без названия %d, без раздела %d, названием стал адрес: %d',
		pages.length, noTitle.length, noSection.length, asUrl.length);
	for (const p of asUrl) console.log('   · %s', p.url);
	return { pages, bad: noTitle.length + noSection.length };
}

// --- сама выдача ------------------------------------------------------------
//
// Отбор и порядок берутся из того же файла, тем же приёмом, что и свёртка.

const pickFrom = src.indexOf('function against(t, q)');
const pickTo = src.indexOf('/* --- подсветка');
if (pickFrom < 0 || pickTo < 0) { console.log('в palette.js не нашлось отбора'); process.exit(1); }
// SHOWN стоит в шапке файла, вне обоих кусков, — берём его тем же чтением,
// чтобы число строк в выдаче проверялось то же, что у читателя.
const SHOWN = /var SHOWN = (\d+)/.exec(src)[1];
// HERE_LANG в браузере берётся из <html lang>; здесь браузера нет, и проверка
// смотрит с русской страницы — как читатель, пришедший на сайт впервые.
const pick = new Function(
	'var SHOWN = ' + SHOWN + ';\nvar HERE_LANG = "ru";\n'
	+ src.slice(from, to) + src.slice(pickFrom, pickTo) + '\nreturn pick;')();

const WANT = [
	['Тантралока', '/ksh/ta/'],
	['tantraloka', '/ksh/ta/'],
	['Тантрасара', '/ksh/tantrasara/'],
	['Шивастотравали', '/ksh/sv/'],
	['Пратьябхиджняхридаям', '/ksh/ph/'],
	['натьяшастра', '/dance/'],
	['паруса', '/ship/'],
	['поиск по сайту', '/search/'],
	['писания трики', '/ksh/scriptures/'],
	['афоризм 12', '/ksh/ph/s12/'],
	// Имя раздела повышает только его заглавную страницу — но не заслоняет
	// того, кто назван точнее.
	['натьяшастра глава 12', '/dance/ns-ch12.html'],
	['натьяшастра словарь', '/dance/glossary.html'],
	['кашмирский шиваизм', '/ksh/'],
	['искусство', '/art/'],
	// Порядок внутри одинаково подходящих: главы идут числом, а не как
	// придётся.
	['тантралока глава', '/ksh/ta/ch1/'],
	// Появился перевод — и английские страницы полезли вперёд русских: их
	// первый сегмент адреса «en» в перечне разделов не значится, они падали в
	// умолчание, а у того порядок 0. Раздел берётся теперь после языка, а свой
	// язык читателя идёт впереди чужого.
	['scriptures of trika', '/en/ksh/scriptures/'],
	['натьяшастра', '/dance/'],
];

function jumps(pages) {
	const ready = pages.map((p) => ({
		url: p.url, title: p.title, section: p.section, order: p.order,
		fold: fold(p.title), tail: fold(p.url + ' ' + (p.section || '')),
		lang: p.lang || 'ru',
		depth: p.url.split('/').filter(Boolean).length,
		home: p.url.split('/').filter(Boolean).length <= 1 && p.section ? fold(p.section) : null,
	}));
	let bad = 0;
	console.log('\nПереходы (что стоит первой строкой):');
	for (const [q, want] of WANT) {
		const got = pick(ready, q);
		const first = got.length ? got[0].url : null;
		const ok = first === want;
		if (!ok) bad++;
		console.log('  %s «%s» → %s%s', ok ? ' ' : '✗', q, first || 'ничего',
			ok ? '' : '   ожидалось ' + want);
	}
	return bad;
}

let bad = drift();
const idx = index();
if (idx) {
	bad += idx.bad;
	bad += jumps(idx.pages);
}
console.log(bad ? '\nрасхождений: ' + bad : '\nрасхождений нет');
process.exit(bad ? 1 : 0);
