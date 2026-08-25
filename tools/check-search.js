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
 * Проверяется три вещи:
 *
 *   1. запись латиницей, запись латиницей без диакритики и запись кириллицей
 *      дают одну и ту же выдачу;
 *   2. свёртка сводит воедино все 54 записи `data-alias` из dance/glossary.md —
 *      там кириллическое написание проставлено рядом с IAST вручную, и это
 *      готовая таблица правильных ответов;
 *   3. подсветка попадает в текст: запрос кириллицей, а подсвечивать надо то,
 *      что написано в абзаце, — латиницей и с диакритикой.
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
];

function aliases() {
	const md = fs.readFileSync(path.join(HERE, 'dance', 'glossary.md'), 'utf8');
	const rows = [...md.matchAll(/<tr data-alias="([^"]*)">.*?<td class="skt"[^>]*>([^<]*)<\/td>/g)];
	let ok = 0;
	const bad = [];
	for (const [, alias, iast] of rows) {
		const want = SiteSearch.fold(iast);
		const cyr = alias.split(/\s+/)[0];
		if (SiteSearch.fold(cyr) === want) ok++; else bad.push([iast, want, cyr, SiteSearch.fold(cyr)]);
	}
	console.log('\nСловарь «Натьяшастры»: сошлось ' + ok + ' из ' + rows.length);
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
			console.log((same ? '  ' : '✗ ') + ('«' + q + '»').padEnd(16) + r.say.padEnd(28) +
				'страниц ' + String(p.length).padStart(3));
		}
	}
	bad += aliases();

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
