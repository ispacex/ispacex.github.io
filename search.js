/* Поиск по всему сайту.
 *
 * Указатель собирает сам Jekyll (search-index.json): страницы, внутри каждой —
 * абзацы её исходника. Здесь остаётся три вещи: снять с абзацев разметку
 * Markdown, сопоставить запрос и показать найденное.
 *
 * Разметку снимаем один раз при загрузке, а не при каждом запросе: указатель
 * большой, а запросов за сеанс много.
 */
(function () {
	'use strict';

	var INDEX = '/search-index.json';
	var LIMIT = 80;

	/* Раздел выводим рядом с найденным: без него выдача по всему сайту
	   нечитаема — непонятно, откуда абзац. Ключ — первый сегмент адреса. */
	var SECTIONS = {
		'art': 'Искусство',
		'dance': 'Натьяшастра',
		'nt': 'Natya talam',
		'theatre': 'Театр',
		'ksh': 'Кашмирский шиваизм',
		'yoga': 'Йога',
		'hoop': 'Обруч',
		'books': 'Книги',
		'ship': 'Теория плавания под парусами'
	};

	var pages = null;
	var input, out, status;

	function styles() {
		var css = [
			'#q{padding:.45em .6em;width:100%;max-width:32em;font-size:1em}',
			'.ss{margin:1.2em 0}',
			'.ss-item{margin:0 0 1.2em}',
			'.ss-head{font-size:.85em;opacity:.75;margin-bottom:.15em}',
			'.ss-sec{opacity:.75}',
			'.ss-text mark{background:rgba(255,220,120,.35);color:inherit;padding:0 .1em;border-radius:2px}',
			'.ss-more{opacity:.7;font-style:italic}'
		].join('');
		var el = document.createElement('style');
		el.appendChild(document.createTextNode(css));
		document.head.appendChild(el);
	}

	/* Диакритику сворачиваем с обеих сторон: ищущий наберёт «paratrishika», а в
	   тексте стоит «Parātrīśikā». NFD разбивает букву на основу и знак, знак
	   выбрасываем. Длина строки при этом не меняется — на ней держится
	   подсветка, — потому что каждый составной знак даёт ровно одну основу. */
	function fold(s) {
		return s.toLowerCase()
			.normalize('NFD').replace(/[̀-ͯ]/g, '')
			.replace(/ё/g, 'е');
	}

	/* Указатель хранит исходник как есть, вместе с разметкой Markdown. Ссылку
	   сводим к её тексту, служебные значки убираем — иначе в выдаче окажутся
	   адреса и звёздочки, которых читатель на странице не видит. */
	function clean(s) {
		return s
			.replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
			.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
			.replace(/^\s{0,3}#{1,6}\s+/gm, '')
			.replace(/^\s{0,3}>\s?/gm, '')
			.replace(/^\s*[-*+]\s+/gm, '')
			.replace(/^\s*\d+[.)]\s+/gm, '')
			.replace(/[*_`]{1,3}/g, '')
			.replace(/\|/g, ' ')
			.replace(/^\s*[-:\s]{6,}$/gm, ' ')
			.replace(/\s+/g, ' ')
			.trim();
	}

	function sectionOf(url) {
		var seg = url.split('/')[1] || '';
		return SECTIONS[seg] || 'Институт';
	}

	/* Русский язык склоняет окончания, поэтому «индрии» должно находить
	   «индрий», а «мантра» — «мантрам». Из каждого слова делаем лесенку
	   префиксов, от целого слова вниз на четыре буквы, но не короче четырёх.
	   Берём самый длинный, который действительно встретился, — так подсветка
	   остаётся точной. */
	function terms(q) {
		return fold(q).split(/\s+/).filter(function (t) { return t.length > 1; }).map(function (t) {
			var min = t.length <= 4 ? t.length : Math.max(4, t.length - 4);
			var v = [];
			for (var len = t.length; len >= min; len--) v.push(t.slice(0, len));
			return v;
		});
	}

	function present(hay, variants) {
		for (var i = 0; i < variants.length; i++) {
			if (hay.indexOf(variants[i]) !== -1) return variants[i];
		}
		return null;
	}

	function matches(hay, ts) {
		return ts.every(function (v) { return present(hay, v) !== null; });
	}

	function hits(hay, ts) {
		var out = [];
		ts.forEach(function (variants) {
			var t = present(hay, variants);
			if (!t) return;
			var from = 0, at;
			while ((at = hay.indexOf(t, from)) !== -1) {
				out.push([at, at + t.length]);
				from = at + t.length;
			}
		});
		return out.sort(function (a, b) { return a[0] - b[0]; });
	}

	/* Отрывок собираем из текстовых узлов и <mark>, а не из HTML: в тексте
	   встречается и «<», и «&», и подставлять его через innerHTML нельзя. */
	function snippet(text, ts) {
		var spans = hits(fold(text), ts);
		var frag = document.createDocumentFragment();

		if (!spans.length) {
			/* Совпал заголовок страницы, а не сам абзац: показываем начало. */
			if (text.length <= 220) {
				frag.appendChild(document.createTextNode(text));
				return frag;
			}
			var cut = text.lastIndexOf(' ', 220);
			frag.appendChild(document.createTextNode(text.slice(0, cut > 0 ? cut : 220) + '…'));
			return frag;
		}

		var start = Math.max(0, spans[0][0] - 70);
		if (start > 0) {
			var space = text.indexOf(' ', start);
			if (space !== -1 && space - start < 20) start = space + 1;
		}
		var end = Math.min(text.length, start + 260);

		var pos = start;
		if (start > 0) frag.appendChild(document.createTextNode('…'));
		spans.forEach(function (s) {
			if (s[1] <= pos || s[0] >= end) return;
			if (s[0] > pos) frag.appendChild(document.createTextNode(text.slice(pos, s[0])));
			var m = document.createElement('mark');
			m.textContent = text.slice(s[0], Math.min(s[1], end));
			frag.appendChild(m);
			pos = Math.min(s[1], end);
		});
		if (pos < end) frag.appendChild(document.createTextNode(text.slice(pos, end)));
		if (end < text.length) frag.appendChild(document.createTextNode('…'));
		return frag;
	}

	function plural(n, one, few, many) {
		var a = n % 100, b = n % 10;
		if (a > 10 && a < 20) return many;
		if (b === 1) return one;
		if (b >= 2 && b <= 4) return few;
		return many;
	}

	function item(page, text, ts, asTitle) {
		var li = document.createElement('div');
		li.className = 'ss-item';

		var head = document.createElement('div');
		head.className = 'ss-head';
		var a = document.createElement('a');
		a.href = page.u;
		a.textContent = page.t;
		head.appendChild(a);
		var sec = document.createElement('span');
		sec.className = 'ss-sec';
		sec.textContent = ' — ' + page.s;
		head.appendChild(sec);
		li.appendChild(head);

		var body = document.createElement('div');
		body.className = 'ss-text';
		body.appendChild(snippet(text, ts));
		li.appendChild(body);
		return li;
	}

	function render(query) {
		out.textContent = '';
		if (!pages) return;

		var ts = terms(query);
		if (!ts.length) {
			status.textContent = 'В указателе страниц: ' + pages.length + '.';
			return;
		}

		var found = [];
		pages.forEach(function (p) {
			/* Страница, чьё название подошло, — сама по себе результат:
			   иначе «Паша» не найдётся, ведь слово живёт в заголовке. */
			if (matches(p.tf, ts)) found.push([p, p.t, true]);
			for (var i = 0; i < p.b.length; i++) {
				if (matches(p.bf[i], ts)) found.push([p, p.b[i], false]);
			}
		});

		status.textContent = found.length
			? 'Найдено: ' + found.length + ' ' + plural(found.length, 'совпадение', 'совпадения', 'совпадений')
				+ (found.length > LIMIT ? ', показаны первые ' + LIMIT : '')
			: 'Ничего не нашлось.';

		found.slice(0, LIMIT).forEach(function (f) {
			out.appendChild(item(f[0], f[1], ts, f[2]));
		});
	}

	function prepare(data) {
		return data.map(function (p) {
			var blocks = p.b.map(clean).filter(function (x) { return x.length > 12; });
			return {
				u: p.u,
				t: p.t,
				s: sectionOf(p.u),
				tf: fold(p.t + ' ' + sectionOf(p.u)),
				b: blocks,
				bf: blocks.map(fold)
			};
		}).filter(function (p) { return p.b.length || p.t; });
	}

	function run() {
		input = document.getElementById('q');
		out = document.getElementById('results');
		status = document.getElementById('ss-status');
		if (!input || !out || !status) return;

		styles();
		status.textContent = 'Загружаю указатель…';

		fetch(INDEX).then(function (r) {
			if (!r.ok) throw new Error(r.status);
			return r.json();
		}).then(function (data) {
			pages = prepare(data);
			var q = new URLSearchParams(location.search).get('q') || '';
			if (q) input.value = q;
			render(input.value);
			input.focus();
		}).catch(function () {
			status.textContent = 'Не удалось загрузить указатель для поиска.';
		});

		var timer;
		input.addEventListener('input', function () {
			clearTimeout(timer);
			timer = setTimeout(function () {
				render(input.value);
				var q = input.value.trim();
				history.replaceState(null, '', q ? location.pathname + '?q=' + encodeURIComponent(q) : location.pathname);
			}, 140);
		});
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
