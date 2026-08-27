/* Проверка поиска: одно ли слово для него «śaktipāta», «saktipata» и
 * «шактипата» (VS-7).
 *
 *     ./tools/build-local.sh          # собрать сайт в _sitecheck/
 *     node tools/check-search.js      # прогнать запросы по нему
 *
 * Движок — настоящий, тот самый sitesearch/search.js, который поедет читателю;
 * пересказывать его правила здесь нельзя, иначе проверялся бы пересказ. Ему
 * нужен браузер, и браузера тут нет: подставка — в tools/browser.js, общая с
 * проверкой палитры. Всё остальное — его собственный код, включая двухъярусный
 * указатель с догрузкой кусков.
 *
 * Проверяется пять вещей:
 *
 *   1. запись латиницей, запись латиницей без диакритики и запись кириллицей
 *      дают одну и ту же выдачу;
 *   2. свёртка сводит воедино все записи `data-alias` из словарей сайта —
 *      «Натьяшастры» и Parātrīśikāvivaraṇa: там кириллическое написание
 *      проставлено рядом с IAST вручную, и это готовая таблица правильных
 *      ответов;
 *   3. подсветка попадает в текст: запрос кириллицей, а подсвечивать надо то,
 *      что написано в абзаце, — латиницей и с диакритикой;
 *   4. опечатка не даёт пустоты: движок ищет по ближайшему слову и называет
 *      его — то самое, а не что-нибудь похожее (VS-24);
 *   5. свёртка на словах, где буква зависит от соседней: «я» в начале слова —
 *      не то же, что «я» после согласной.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const HERE = path.dirname(__dirname);
const SITE = process.argv[2] || path.join(HERE, '_sitecheck');

// --- подставка вместо браузера ----------------------------------------------
//
// Она общая с проверкой палитры (tools/browser.js): движок один, и браузера
// ему не хватает одинаково.

const { El, install } = require('./browser.js');
install(SITE, 'ru');

const SiteSearch = require(path.join(HERE, 'sitesearch', 'search.js'));

// --- читатель и его запрос --------------------------------------------------
//
// Читателей двое, русский и английский, и указатель у них один и тот же —
// разной должна быть выдача. Поэтому движок здесь не один: у каждого свой, со
// своим языком. Язык называется движку прямо, а не через <html lang>:
// подставка держит один документ на всю проверку, а читателя надо двух.

// Движок догружает куски текста и перерисовывает выдачу сам; здесь надо просто
// дождаться, пока строка состояния перестанет обещать продолжение.
const settled = (say) => say && !/Загружаю|ищу дальше|читаю дальше/.test(say);

function reader(lang) {
	const input = new El('input');
	input.value = '';
	const status = new El('p');
	const results = new El('ul');
	results.parentNode = new El('div');

	SiteSearch.mount({ input: input, status: status, results: results, repeats: 4,
		lang: lang, sources: [{ url: '/search-index.json' }] });

	return function ask(q) {
		input.value = q;
		results.children = [];
		status.textContent = '';
		input.fire('input');   // движок откладывает перерисовку на 120 мс
		return new Promise((done) => {
			const tick = () => {
				if (!settled(status.textContent)) return setTimeout(tick, 40);
				done({
					say: status.textContent,
					items: results.children.map((li) => ({
						link: li.link,
						where: li.children[0].textContent,
						text: li.children[1].marked,
					})),
				});
			};
			setTimeout(tick, 200);
		});
	};
}

const ask = reader('ru');
const askEn = reader('en');

// --- сами проверки ----------------------------------------------------------

function pagesOf(items) {
	return [...new Set(items.map((i) => (i.link || '?').split('#')[0]))].sort();
}

/* Каждый ряд — одно слово, записанное по-разному. Выдача должна совпасть вся,
   до страницы.

   Третьего написания — «shaktipata», «natyashastra», где ś передана парой букв
   «sh», — здесь нет намеренно. Это отдельное соглашение, не кириллица против
   латиницы, и стоит оно дороже, чем кажется: правило `sh → s` свело бы на всём
   сайте всего семь пар слов, зато в английском тексте склеило бы «short» с
   «sort» и «ship» с «sip». Мерено, а не прикинуто. */
const SETS = [
	['śaktipāta', 'saktipata', 'шактипата', 'шактипаты'],
	['pāśa', 'паша'],
	['ṣaṭ', 'шат'],
	['Parātrīśikā', 'Паратришика'],
	['śṛṅgāra', 'srngara', 'sringara', 'шрингара'],
	['jñāna', 'джняна'],
	['nāṭya', 'натья'],
	['Śivastotrāvalī', 'Шивастотравали'],
	['Tantrasāra', 'Тантрасара'],
	['Pratyabhijñāhṛdayam', 'Пратьябхиджняхридаям'],
];

/* Свёртка там, где буква зависит от соседей. Проверяется фразой, а не словом:
   «я» и «ю» в начале слова несут «й» («юга» → `yuga`), а после согласной нет
   («пятая» → `pataya`), и разницу видно только когда перед словом что-то
   стоит. Одно слово целиком этого не покажет — с него начинается строка. */
const FOLDS = [
	['кальпа юга', 'kalpa yuga'],
	['на язык', 'na yazyk'],
	['по-японски', 'po-yaponski'],
	['и яма', 'i yama'],
	['майя', 'maya'],
	['объявление', 'obyavlenie'],
	['пятая', 'pataya'],
	['джняна', 'jnana'],
	['натья', 'natya'],
	['нритта', 'nritta'],
	['śṛṅgāra', 'sringara'],
];

function folds() {
	console.log('\nСвёртка по соседям:');
	let bad = 0;
	for (const [s, want] of FOLDS) {
		const got = SiteSearch.fold(s);
		if (got !== want) bad++;
		console.log((got === want ? '  ' : '✗ ') + ('«' + s + '»').padEnd(18) +
			'→ ' + got + (got === want ? '' : '   ждали ' + want));
	}
	return bad;
}

/* Опечатка — и что после неё обязано быть названо в строке состояния.
   Правый столбец пишется так, как слово стоит на странице; сверяется он
   свёрнутым, потому что назвать движок может и более длинную форму того же
   слова — «śaktipātataḥ» там, где в абзаце нет одиночного «śaktipāta». Чего
   свёртка не прощает — так это чужого слова: подсказка, называющая не то,
   хуже молчания.

   Последние два ряда — про молчание. Слова нет и похожего нет: выдумывать
   нечего. Слово есть: подсказке тут делать нечего вовсе. */
const TYPOS = [
	['paratrisikavirana', 'Parātrīśikāvivaraṇa'],
	['sactipata', 'śaktipāta'],
	['saktipta', 'śaktipāta'],
	['шактипта', 'śaktipāta'],
	['mandla', 'maṇḍala'],
	['bhairva', 'bhairava'],
	['abhinvagupta', 'Абхинавагупта'],
	['страхами', 'страха'],
	// Второе написание того же слова: кто снял диакритику руками, пишет
	// «srngara», на сайте стоит «Шрингара», и меж ними нет никакой опечатки —
	// но две буквы есть, и мерить надо от обоих написаний.
	['srngra', 'śṛṅgāra'],
	// Слов два, неверное — одно: править второе значило бы искать не то, о чём
	// спросили. Названо исправленное, а найдено — где есть оба.
	['saktipta abhinavagupta', 'śaktipāta'],
	['qqqqqqqq', null],
	// То же, но со вторым написанием: «r» без гласной даёт «ri», и обход
	// словаря идёт дважды — пустой ответ обязан остаться пустым и там.
	['qrqrqrqr', null],
	['натьяшастра', null],
];

const SAID = /показано по «([^»]+)»/;

async function typos() {
	console.log('\nОпечатки (что названо в строке состояния):');
	let bad = 0;
	for (const [q, want] of TYPOS) {
		const r = await ask(q);
		const said = (SAID.exec(r.say) || [])[1] || null;
		const ok = want === null
			? said === null
			: said !== null && SiteSearch.fold(said).startsWith(SiteSearch.fold(want));
		if (!ok) bad++;
		console.log((ok ? '  ' : '✗ ') + ('«' + q + '»').padEnd(22) +
			(said ? '→ «' + said + '»' : '→ молчит').padEnd(26) +
			(ok ? '' : 'ждали ' + (want ? '«' + want + '»' : 'молчания')) +
			'   ' + r.say);
	}
	return bad;
}

/* Словари сайта: в каждой строке кириллическое написание проставлено рядом с
   IAST вручную, и это готовая таблица правильных ответов для свёртки. Первым в
   `data-alias` стоит то написание, которое свёртка обязана свести с IAST; за
   ним идут прочие, по которым ищут на самой странице словаря.

   Дефис из сравнения выкидывается: в Parātrīśikāvivaraṇa есть составные
   термины — `parā-aparā`, `mahā-mantra`, — а кириллицей их пишут слитно. Это
   не расхождение свёртки, а разное членение одного слова. */
const GLOSSARIES = [
	['Натьяшастры', path.join(HERE, 'dance', 'glossary.md')],
	['Parātrīśikāvivaraṇa', path.join(HERE, 'ksh', 'pv', 'glossary', 'index.md')],
	['Śivastotrāvalī', path.join(HERE, 'ksh', 'sv', 'glossary', 'index.md')],
	['Тантралоки', path.join(HERE, 'ksh', 'ta', 'glossary', 'index.md')],
	['Тантрасары', path.join(HERE, 'ksh', 'tantrasara', 'glossary', 'index.md')],
	['Pratyabhijñāhṛdayam', path.join(HERE, 'ksh', 'ph', 'glossary', 'index.md')],
];

function aliases() {
	let bad = 0;
	for (const [name, file] of GLOSSARIES) bad += aliasesOf(name, file);
	return bad;
}

function aliasesOf(name, file) {
	const md = fs.readFileSync(file, 'utf8');
	const rows = [...md.matchAll(/<tr [^>]*data-alias="([^"]*)">.*?<td class="skt"[^>]*>([^<]*)<\/td>/g)];
	const flat = (s) => SiteSearch.fold(s).replace(/-/g, '');
	let ok = 0;
	const bad = [];
	for (const [, alias, iast] of rows) {
		const want = flat(iast);
		const cyr = alias.split(/\s+/)[0];
		if (flat(cyr) === want) ok++; else bad.push([iast, want, cyr, flat(cyr)]);
	}
	console.log('\nСловарь ' + name + ': сошлось ' + ok + ' из ' + rows.length);
	for (const [i, w, c, g] of bad) console.log('   ✗ ' + i + ' → ' + w + '   ≠   ' + c + ' → ' + g);
	return bad.length;
}

/* Язык читателя. У 96 страниц сайта есть английский двойник, и лежат обе в
   одном указателе: русская находка не должна выдаваться дважды, на двух
   языках, — ровно этим перевод и был опасен, и ровно поэтому его из поиска
   временно убирали целиком (VS-40).

   Оговорка у английского читателя нарочная. «Тантралока» и книга Мархая языка
   о себе не сообщают: строфы на санскрите и русский текст, которого никто не
   переводил, лучше найти, чем не найти. Их и показывают обоим — а перечислены
   они здесь поимённо, чтобы исключение оставалось перечнем, а не дырой. */
const NEUTRAL = ['/ksh/ta/', '/ship/'];

const TWO = ['śaktipāta', 'rasa', 'Abhinavagupta', 'раса'];

async function langs() {
	console.log('\nЯзык читателя (одна страница — одному из двух):');
	let bad = 0;
	for (const q of TWO) {
		const ru = pagesOf((await ask(q)).items);
		const en = pagesOf((await askEn(q)).items);
		const strayRu = ru.filter((u) => u.startsWith('/en/'));
		const strayEn = en.filter((u) => !u.startsWith('/en/') &&
			!NEUTRAL.some((n) => u.startsWith(n)));
		// Пустая выдача согласна с любым правилом и потому ничего не значит:
		// у обоих читателей должно найтись хоть что-нибудь.
		const ok = !strayRu.length && !strayEn.length && ru.length && en.length;
		if (!ok) bad++;
		console.log((ok ? '  ' : '✗ ') + ('«' + q + '»').padEnd(18) +
			('ru ' + ru.length).padEnd(9) + ('en ' + en.length).padEnd(9) +
			(strayRu.length ? '   по-русски выдано ' + strayRu.slice(0, 3).join(' ') : '') +
			(strayEn.length ? '   по-английски выдано ' + strayEn.slice(0, 3).join(' ') : ''));
	}
	return bad;
}

(async () => {
	let bad = 0;
	for (const set of SETS) {
		console.log('');
		let first = null;
		for (const q of set) {
			const r = await ask(q);
			const p = pagesOf(r.items);
			if (first === null) first = p.join('|');
			const same = p.join('|') === first;
			if (!same) bad++;
			console.log((same ? '  ' : '✗ ') + ('«' + q + '»').padEnd(18) + r.say.padEnd(28) +
				'страниц ' + String(p.length).padStart(3));
		}
	}
	bad += await langs();
	bad += folds();
	bad += aliases();
	bad += await typos();

	// Подсветка: запрос кириллицей, а в тексте — IAST.
	console.log('\nПодсветка (запрос кириллицей, текст латиницей):');
	const r = await ask('паша');
	for (const it of r.items.slice(0, 3)) console.log('   ' + it.text.replace(/\s+/g, ' ').slice(0, 150));
	if (!r.items.some((i) => /\[[^\]]*[āīūṛṅṣśṭḍṇḥṁ][^\]]*\]/i.test(i.text))) {
		console.log('   ✗ ни одна пометка не попала в слово с диакритикой');
		bad++;
	}

	console.log('\n' + (bad ? 'расхождений: ' + bad : 'расхождений нет'));
	process.exit(bad ? 1 : 0);
})();
