/* Проверка поиска: одно ли слово для него «śaktipāta», «saktipata» и
 * «шактипата» (VS-7).
 *
 *     ./tools/build-local.sh          # собрать сайт в _sitecheck/
 *     node tools/check-search.js      # прогнать запросы по нему
 *
 * Движок — настоящий, тот самый sitesearch/search.js, который поедет читателю;
 * пересказывать его правила здесь нельзя, иначе проверялся бы пересказ. Ему
 * нужен браузер, и браузера тут нет, поэтому ниже стоит подставка: ровно те
 * несколько вещей из DOM, которых движок касается, и fetch, читающий указатели
 * с диска. Всё остальное — его собственный код, включая двухъярусный указатель
 * с догрузкой кусков.
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

class El {
	constructor(tag) {
		this.tagName = tag;
		this.children = [];
		this.parentNode = null;
		this._text = '';
	}
	appendChild(c) {
		if (c && c.fragment) { c.children.forEach((x) => this.appendChild(x)); return c; }
		c.parentNode = this;
		this.children.push(c);
		return c;
	}
	insertBefore(c) { return this.appendChild(c); }
	addEventListener(type, fn) { (this.on || (this.on = {}))[type] = fn; }
	fire(type) { if (this.on && this.on[type]) this.on[type](); }
	set textContent(v) { this._text = v; this.children = []; }
	get textContent() {
		return this.children.length ? this.children.map((c) => c.textContent).join('') : this._text;
	}
	// Текст с пометками, чтобы видеть глазами, что подсвечено.
	get marked() {
		if (!this.children.length) return this.tagName === 'mark' ? '[' + this._text + ']' : this._text;
		return this.children.map((c) => c.marked).join('');
	}
	// Куда ведёт находка: у абзаца ссылка стоит в строке «где», у страницы —
	// в самой выдержке.
	get link() {
		if (this.href) return this.href;
		for (const c of this.children) { const l = c.link; if (l) return l; }
		return null;
	}
}

const nodes = {};
global.document = {
	getElementById: (id) => nodes[id] || (nodes[id] = new El('div')),
	createElement: (tag) => new El(tag),
	createTextNode: (t) => { const e = new El('#text'); e.textContent = t; return e; },
	createDocumentFragment: () => { const e = new El('#fragment'); e.fragment = true; return e; },
};
global.location = { pathname: '/search/', search: '' };
global.history = { replaceState() {} };

// Указатели лежат на диске; движок просит их по адресу сайта.
global.fetch = (url) => {
	const file = path.join(SITE, url.replace(/^\//, ''));
	if (!fs.existsSync(file)) return Promise.resolve({ ok: false, status: 404 });
	return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(fs.readFileSync(file, 'utf8'))) });
};

const SiteSearch = require(path.join(HERE, 'sitesearch', 'search.js'));

// --- один запрос ------------------------------------------------------------

const input = new El('input');
input.value = '';
const status = nodes.status = new El('p');
const results = nodes.results = new El('ul');
results.parentNode = new El('div');

SiteSearch.mount({ input: input, status: status, results: results, repeats: 4,
	sources: [{ url: '/search-index.json' }] });

// Движок догружает куски текста и перерисовывает выдачу сам; здесь надо просто
// дождаться, пока строка состояния перестанет обещать продолжение.
const settled = (say) => say && !/Загружаю|ищу дальше|читаю дальше/.test(say);

function ask(q) {
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
}

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
