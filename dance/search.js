/* Поиск по главам «Натьяшастры».
 *
 * Индекс собирает Jekyll (dance/search-index.json), единица — строфа. Здесь
 * остаётся сопоставление и показ: найденное ведёт не в начало главы, а прямо
 * к строфе — её номер вынимается из самого текста, который начинается с «7/»
 * или «9-10/».
 */
(function () {
	'use strict';

	var INDEX = '/dance/search-index.json';
	var VERSE = /^\s*(\d+)\s*(?:[-–—]\s*(\d+))?\s*\//;
	var LIMIT = 60;

	var entries = null;
	var input, out, status;

	function styles() {
		var css = [
			'#q{padding:.4em .6em;width:100%;max-width:30em;font-size:1em}',
			'.sr{margin:1.2em 0}',
			'.sr-item{margin:0 0 1.1em}',
			'.sr-head{font-size:.85em;opacity:.75;margin-bottom:.15em}',
			'.sr-text mark{background:rgba(255,220,120,.35);color:inherit;padding:0 .1em;border-radius:2px}',
			'.sr-none{opacity:.7;font-style:italic}'
		].join('');
		var el = document.createElement('style');
		el.appendChild(document.createTextNode(css));
		document.head.appendChild(el);
	}

	/* Диакритика в запросе — лишний барьер: ищущий «шрингара» латиницей
	   напишет «srngara», а не «śṛṅgāra». Сводим обе стороны к простому виду. */
	function fold(s) {
		return s.toLowerCase()
			.normalize('NFD').replace(/[̀-ͯ]/g, '')
			.replace(/ё/g, 'е');
	}

	function anchor(text) {
		var m = VERSE.exec(text);
		if (!m) return '';
		return '#v' + (m[2] ? m[1] + '-' + m[2] : m[1]);
	}

	function highlight(text, terms) {
		var folded = fold(text);
		var hits = [];
		terms.forEach(function (t) {
			var from = 0, at;
			while ((at = folded.indexOf(t, from)) !== -1) {
				hits.push([at, at + t.length]);
				from = at + t.length;
			}
		});
		if (!hits.length) return document.createTextNode(text);

		hits.sort(function (a, b) { return a[0] - b[0]; });

		/* Показываем окно вокруг первого совпадения, а не всю строфу. */
		var start = Math.max(0, hits[0][0] - 90);
		var end = Math.min(text.length, hits[0][0] + 220);

		var frag = document.createDocumentFragment();
		if (start > 0) frag.appendChild(document.createTextNode('…'));

		var pos = start;
		hits.forEach(function (h) {
			if (h[0] < pos || h[0] >= end) return;
			frag.appendChild(document.createTextNode(text.slice(pos, h[0])));
			var mark = document.createElement('mark');
			mark.appendChild(document.createTextNode(text.slice(h[0], h[1])));
			frag.appendChild(mark);
			pos = h[1];
		});
		frag.appendChild(document.createTextNode(text.slice(pos, end)));
		if (end < text.length) frag.appendChild(document.createTextNode('…'));
		return frag;
	}

	function render(query) {
		out.innerHTML = '';
		var terms = fold(query).split(/\s+/).filter(function (t) { return t.length > 1; });
		if (!terms.length) {
			status.textContent = entries ? 'Строф в индексе: ' + entries.length : '';
			return;
		}

		var found = entries.filter(function (e) {
			var f = fold(e.x);
			return terms.every(function (t) { return f.indexOf(t) !== -1; });
		});

		status.textContent = found.length
			? 'Найдено строф: ' + found.length + (found.length > LIMIT ? ', показаны первые ' + LIMIT : '')
			: 'Ничего не найдено.';

		found.slice(0, LIMIT).forEach(function (e) {
			var item = document.createElement('div');
			item.className = 'sr-item';

			var head = document.createElement('div');
			head.className = 'sr-head';
			var a = document.createElement('a');
			a.href = e.u + anchor(e.x);
			a.appendChild(document.createTextNode(e.t));
			head.appendChild(a);
			item.appendChild(head);

			var body = document.createElement('div');
			body.className = 'sr-text';
			body.appendChild(highlight(e.x, terms));
			item.appendChild(body);

			out.appendChild(item);
		});
	}

	function run() {
		input = document.getElementById('q');
		out = document.getElementById('results');
		status = document.getElementById('status');
		if (!input || !out || !status) return;

		styles();
		status.textContent = 'Загружаю индекс…';

		fetch(INDEX).then(function (r) { return r.json(); }).then(function (data) {
			entries = data;
			var q = new URLSearchParams(location.search).get('q') || '';
			if (q) input.value = q;
			render(input.value);
			input.focus();
		}).catch(function () {
			status.textContent = 'Не удалось загрузить индекс поиска.';
		});

		var timer;
		input.addEventListener('input', function () {
			clearTimeout(timer);
			timer = setTimeout(function () {
				if (entries) render(input.value);
			}, 120);
		});
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
