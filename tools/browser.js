/* Браузер, которого нет: столько DOM, сколько трогает движок поиска.
 *
 *     const { El, install } = require('./browser.js');
 *     const { nodes } = install('_sitecheck', 'ru');
 *
 * Проверки поиска и палитры гоняют **настоящий** sitesearch/search.js — тот
 * самый файл, что поедет читателю. Пересказать его правила в проверке значило
 * бы проверять пересказ: свёртку письменности, отброшенное окончание,
 * опечатку, двухъярусный указатель с догрузкой кусков. Взамен пересказывается
 * то, что вокруг него, и этого мало: узлы, в которые он кладёт находки,
 * `fetch`, читающий указатели с диска, да строка адреса.
 *
 * Подставка стоит здесь, а не в каждой проверке, по той же причине, по какой
 * сама палитра переехала в общий репозиторий: две копии расходятся молча. Так
 * и вышло — движок научился спрашивать язык страницы, и проверка поиска
 * упала на `document.documentElement`, которого у неё не было, а проверка
 * палитры на своей копии прошла.
 */
'use strict';
const fs = require('fs');
const path = require('path');

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

// `site` — собранный сайт на диске, `lang` — язык страницы, на которой мы как
// бы стоим: движок ищет по нему, как ищет у читателя.
function install(site, lang) {
	const nodes = {};
	global.document = {
		getElementById: (id) => nodes[id] || (nodes[id] = new El('div')),
		createElement: (tag) => new El(tag),
		createTextNode: (t) => { const e = new El('#text'); e.textContent = t; return e; },
		createDocumentFragment: () => { const e = new El('#fragment'); e.fragment = true; return e; },
		// Язык берётся оттуда же, откуда его берёт браузер: страница объявила
		// его для себя, и повторять это второй раз незачем.
		documentElement: { getAttribute: (a) => (a === 'lang' ? lang || 'ru' : null) },
	};
	global.location = { pathname: '/search/', search: '' };
	global.history = { replaceState() {} };

	// Указатели лежат на диске; движок просит их по адресу сайта. Отсутствующий
	// файл отвечает 404, как ответил бы хостинг: движок это умеет и должен уметь.
	global.fetch = (url) => {
		const file = path.join(site, url.replace(/^\//, ''));
		if (!fs.existsSync(file)) return Promise.resolve({ ok: false, status: 404 });
		return Promise.resolve({
			ok: true, status: 200,
			json: () => Promise.resolve(JSON.parse(fs.readFileSync(file, 'utf8'))),
		});
	};

	return { nodes };
}

module.exports = { El, install };
