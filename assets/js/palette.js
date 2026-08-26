/* Палитра быстрого перехода: ⌘K на macOS, Ctrl-K на всём остальном.
 *
 * Набрал «Тантралока» — попал в раздел. Не поиск: поиск отвечает «где про это
 * написано» и живёт на /search/, а палитра отвечает «отведи меня туда» и живёт
 * на каждой странице. Разделов на сайте полтора десятка, и переход из середины
 * одного в другой стоил трёх щелчков по хлебным крошкам.
 *
 * Указатель свой и маленький — /nav-index.json, только названия и адреса.
 * Поисковый (766 КБ карты слов) возить на каждой странице ради этого нельзя.
 * Забирается он не при загрузке страницы, а на простое или при первом же
 * нажатии: страница от палитры не должна становиться тяжелее.
 *
 * Кнопка в шапке — не украшение. Сочетание клавиш, о котором никто не знает,
 * всё равно что его нет; а на телефоне клавиатуры нет вовсе.
 */
(function () {
	'use strict';

	var INDEX = '/nav-index.json';
	var SHOWN = 12;

	/* Язык страницы, на которой стоит читатель. Палитра показывает сперва свой
	   язык: читающему по-английски русский перевод той же книги не нужен вовсе,
	   и наоборот.

	   Стоит здесь, а не рядом с отбором, нарочно: проверка вынимает отбор
	   куском исходника и подставляет своё значение, а `document` в ноде нет. */
	var HERE_LANG = (document.documentElement.getAttribute('lang') || 'ru').slice(0, 2);

	/* --- свёртка письменности -------------------------------------------
	 *
	 * Та же, что в поиске (sitesearch/search.js): регистр, «ё» и диакритика
	 * снимаются, кириллица переводится в латиницу. На сайте о санскрите одно
	 * слово пишется двояко — `śaktipāta` в одной главе, «шактипата» в
	 * соседней, — и для читателя это одно слово.
	 *
	 * Почему копия, а не вызов SiteSearch.fold: там она внутри движка поиска
	 * на 49 КБ, и тащить его на каждую страницу ради сорока строк незачем.
	 * Копия расходится молча, поэтому tools/check-palette.js прогоняет обе по
	 * одному набору слов и требует совпадения знак в знак.
	 */
	var CYRILLIC = {
		'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
		'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
		'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
		'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'c', 'ш': 's', 'щ': 's', 'ъ': '',
		'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'u', 'я': 'a'
	};
	var VOWEL = /[аеёиоуыэюя]/;
	var GLIDED = /[яюеёи]/;
	var MARK = /[̀-ͯ]/g;
	var VOCALIC = { 'ṛ': 'ri', 'ṝ': 'ri', 'Ṛ': 'ri', 'Ṝ': 'ri' };

	function fold(s) {
		var out = '', n = s.length;
		for (var i = 0; i < n; i++) {
			var c = s.charAt(i).toLowerCase(), took = 1, piece;
			if (VOCALIC[c] !== undefined) piece = VOCALIC[c];
			else if (c === 'д' && s.charAt(i + 1).toLowerCase() === 'ж') { piece = 'j'; took = 2; }
			else if (c === 'ь' || c === 'ъ') piece = GLIDED.test(s.charAt(i + 1).toLowerCase()) ? 'y' : '';
			else if (c === 'я' || c === 'ю') {
				var before = i > 0 ? s.charAt(i - 1).toLowerCase() : '';
				var after = CYRILLIC[before] !== undefined && !VOWEL.test(before);
				piece = after ? CYRILLIC[c] : (c === 'я' ? 'ya' : 'yu');
			}
			else if (CYRILLIC[c] !== undefined) piece = CYRILLIC[c];
			else piece = c.normalize('NFD').replace(MARK, '');
			out += piece;
			i += took - 1;
		}
		return out;
	}

	/* --- отбор и порядок -------------------------------------------------
	 *
	 * Палитра ищет по названию, а не по тексту, и потому может позволить себе
	 * то, чего не может поиск: расставить находки по тому, насколько начало
	 * названия совпало с набранным. Кто набирает «тант», ждёт «Тантралоку» и
	 * «Тантрасару» первыми, а не страницу, где это слово стоит в середине
	 * заголовка.
	 *
	 * Разряды, от лучшего к худшему: точное совпадение, название начинается с
	 * набранного, с набранного начинается слово в названии, набранное есть
	 * внутри названия, набранное нашлось в адресе или в имени раздела.
	 *
	 * При равенстве вперёд идёт раздел, который выше на главной, а за ним —
	 * страница, лежащая ближе к корню. Последнее важнее, чем кажется: у
	 * «Тантралоки» и раздел, и словарь начинаются со слова «Тантралока», и без
	 * этого правила набравший его попадал в словарь, а не в саму книгу. Кто
	 * называет раздел, хочет раздел; страницы внутри него он назовёт точнее.
	 */
	function against(t, q) {
		if (t === q) return 0;
		if (t.indexOf(q) === 0) return 1;
		if (t.indexOf(' ' + q) !== -1 || t.indexOf('—' + q) !== -1) return 2;
		if (t.indexOf(q) !== -1) return 3;
		return -1;
	}

	/* Заглавная страница раздела сличается ещё и с именем самого раздела, а не
	   только со своим названием. Иначе набравший «Натьяшастра» попадал не в
	   раздел, а на страницу поиска по нему: у той название с этого слова
	   начинается, а у раздела — «Индийский танец и театр, Натьяшастра» — оно
	   стоит в конце. Страница раздела **и есть** раздел, как бы она себя ни
	   назвала; на страницы внутри него это не распространяется — там имя
	   раздела общее у всех, и разряд стал бы у всех одинаковым. */
	function rank(page, q) {
		var r = against(page.fold, q);
		if (page.home) {
			var h = against(page.home, q);
			if (h >= 0 && (r < 0 || h < r)) r = h;
		}
		if (r >= 0) return r;
		return page.tail.indexOf(q) !== -1 ? 4 : -1;
	}

	/* Несколько слов — все должны найтись, и разряд берётся худший из них:
	   строка хороша ровно настолько, насколько плохо в неё легло самое
	   неудобное слово. */
	function score(page, words) {
		var worst = 0;
		for (var i = 0; i < words.length; i++) {
			var r = rank(page, words[i]);
			if (r < 0) return -1;
			if (r > worst) worst = r;
		}
		return worst;
	}

	// Последняя разводка — по названию, естественным порядком: иначе главы
	// «Тантралоки» выходили как 8, 21, 31, 6, 3 — в том порядке, в каком Jekyll
	// случилось собрать страницы. `numeric` нужен, чтобы «глава 2» шла перед
	// «главой 10», а не после.
	var byName = new Intl.Collator('ru', { numeric: true }).compare;

	function pick(pages, query) {
		var words = fold(query).split(/\s+/).filter(function (w) { return w.length > 0; });
		if (!words.length) return [];
		var out = [];
		for (var i = 0; i < pages.length; i++) {
			var s = score(pages[i], words);
			if (s >= 0) out.push({ page: pages[i], s: s, i: i });
		}
		out.sort(function (a, b) {
			return a.s - b.s
				|| (a.page.lang === HERE_LANG ? 0 : 1) - (b.page.lang === HERE_LANG ? 0 : 1)
				|| a.page.order - b.page.order
				|| a.page.depth - b.page.depth
				|| byName(a.page.title, b.page.title);
		});
		return out.slice(0, SHOWN).map(function (x) { return x.page; });
	}

	/* --- подсветка -------------------------------------------------------
	 *
	 * Свёртка длину строки не сохраняет («ш» — одна буква, `s` — тоже, а «ю»
	 * становится двумя), поэтому найти место в исходном названии по месту в
	 * свёрнутом напрямую нельзя. Свёртываем название по букве и запоминаем,
	 * откуда каждая пришла, — тот же приём, что у поиска.
	 */
	function foldMap(s) {
		var out = '', map = [], n = s.length;
		for (var i = 0; i < n; i++) {
			var piece = fold(s.charAt(i));
			// Пара «дж» и мягкий знак зависят от соседей, и посимвольно их не
			// свернуть. Для подсветки это неважно: место всё равно то же.
			out += piece;
			for (var k = 0; k < piece.length; k++) map.push(i);
		}
		map.push(n);
		return { text: out, map: map };
	}

	function mark(title, words) {
		var fm = foldMap(title), spans = [];
		words.forEach(function (w) {
			var at = fm.text.indexOf(w);
			if (at !== -1) spans.push([fm.map[at], fm.map[at + w.length]]);
		});
		if (!spans.length) return document.createTextNode(title);
		spans.sort(function (a, b) { return a[0] - b[0]; });
		var frag = document.createDocumentFragment(), pos = 0;
		spans.forEach(function (s) {
			if (s[0] < pos) return;
			frag.appendChild(document.createTextNode(title.slice(pos, s[0])));
			var b = document.createElement('mark');
			b.appendChild(document.createTextNode(title.slice(s[0], s[1])));
			frag.appendChild(b);
			pos = s[1];
		});
		frag.appendChild(document.createTextNode(title.slice(pos)));
		return frag;
	}

	/* --- указатель -------------------------------------------------------- */

	var pages = null, loading = null;

	function load() {
		if (pages) return Promise.resolve(pages);
		if (loading) return loading;
		loading = fetch(INDEX).then(function (r) {
			if (!r.ok) throw new Error(r.status);
			return r.json();
		}).then(function (data) {
			pages = (data.pages || []).map(function (p) {
				var deep = p.url.split('/').filter(Boolean).length;
				return {
					url: p.url, title: p.title, section: p.section, order: p.order,
					fold: fold(p.title),
					// Насколько страница глубоко: «/ksh/ta/» — один сегмент,
					// «/ksh/ta/glossary/» — два.
					depth: deep,
					// Имя раздела — но только у его заглавной страницы, см. `rank`.
					home: deep <= 1 && p.section ? fold(p.section) : null,
					// Хвост — то, по чему находят во вторую очередь: адрес и
					// имя раздела. «моне» найдёт /art/monet/, у которого своего
					// названия нет вовсе.
					tail: fold(p.url + ' ' + (p.section || ''))
				};
			});
			return pages;
		}).catch(function () {
			loading = null;
			return null;
		});
		return loading;
	}

	/* --- сама палитра ----------------------------------------------------- */

	var box, input, list, status, items = [], at = -1, opener = null;

	function styles() {
		var css = [
			'#nav-palette{position:fixed;inset:0;z-index:9999;display:none;',
			'background:rgba(0,0,0,.55);padding:8vh 1rem 1rem}',
			'#nav-palette.on{display:block}',
			'#nav-box{max-width:34rem;margin:0 auto;background:#1a1d24;color:#e6e6e6;',
			'border:1px solid rgba(128,128,128,.4);border-radius:.5rem;overflow:hidden;',
			'box-shadow:0 1.5rem 3rem rgba(0,0,0,.5)}',
			'#nav-q{width:100%;box-sizing:border-box;border:0;border-bottom:1px solid rgba(128,128,128,.3);',
			'background:transparent;color:inherit;font:inherit;font-size:1.05rem;padding:.7em .9em;outline:none}',
			'#nav-list{list-style:none;margin:0;padding:.25rem;max-height:52vh;overflow-y:auto}',
			'#nav-list li{padding:.4em .65em;border-radius:.35rem;cursor:pointer;display:flex;',
			'gap:.6em;align-items:baseline}',
			'#nav-list li[aria-selected="true"]{background:rgba(128,128,160,.28)}',
			'#nav-list .t{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
			'#nav-list .s{font-size:.8em;opacity:.55;white-space:nowrap}',
			'#nav-list mark{background:transparent;color:#8be9fd;font-weight:600}',
			'#nav-note{padding:.5em .9em;font-size:.85em;opacity:.6}',
			/* Кнопка в шапке. Тема даёт #title с h1 и <hr>; кладём кнопку в тот
			   же блок, справа от названия. */
			'#title{position:relative}',
			'#nav-open{position:absolute;right:0;top:0;background:none;color:inherit;',
			'border:1px solid rgba(128,128,128,.45);border-radius:999px;cursor:pointer;',
			'font:inherit;font-size:.8rem;line-height:1;padding:.4em .7em;opacity:.6}',
			'#nav-open:hover,#nav-open:focus{opacity:1}',
			'#nav-open kbd{font:inherit;opacity:.75}',
			/* Подсказка — своя, а не title: системная всплывает через секунду и
			   на сенсорном экране не всплывает вовсе. */
			'#nav-open::after{content:attr(data-tip);position:absolute;right:0;top:110%;',
			'white-space:nowrap;background:#1a1d24;border:1px solid rgba(128,128,128,.4);',
			'border-radius:.35rem;padding:.35em .6em;font-size:.75rem;opacity:0;',
			'pointer-events:none;transition:opacity .12s;z-index:10}',
			'#nav-open:hover::after,#nav-open:focus::after{opacity:1}',
			/* Страница без шапки темы — просмотрщики книги, страницы поддержки:
			   у них своя вёрстка и своего #title нет. Кнопка тогда висит в углу
			   окна, чтобы обещание «на каждой странице» осталось обещанием. */
			'#nav-open.float{position:fixed;top:.6rem;right:.6rem;z-index:9998;',
			'background:rgba(26,29,36,.85);backdrop-filter:blur(2px)}',
			'@media (max-width:640px){#nav-open{position:static;display:block;margin:.4rem 0 0}',
			'#nav-open.float{position:fixed;display:inline-block;margin:0}',
			'#nav-open::after{display:none}}',
			'@media print{#nav-open,#nav-palette{display:none!important}}'
		].join('');
		var el = document.createElement('style');
		el.appendChild(document.createTextNode(css));
		document.head.appendChild(el);
	}

	function build() {
		box = document.createElement('div');
		box.id = 'nav-palette';
		box.setAttribute('role', 'dialog');
		box.setAttribute('aria-modal', 'true');
		box.setAttribute('aria-label', 'Переход по разделам');
		box.innerHTML =
			'<div id="nav-box">' +
			'<input id="nav-q" type="search" autocomplete="off" spellcheck="false" ' +
			'role="combobox" aria-expanded="true" aria-controls="nav-list" ' +
			'placeholder="Куда идём? например: Тантралока, словарь, паруса" />' +
			'<ul id="nav-list" role="listbox" aria-label="Разделы"></ul>' +
			'<p id="nav-note"></p></div>';
		document.body.appendChild(box);
		input = box.querySelector('#nav-q');
		list = box.querySelector('#nav-list');
		status = box.querySelector('#nav-note');

		box.addEventListener('mousedown', function (e) {
			if (e.target === box) close();
		});
		input.addEventListener('input', function () { render(input.value); });
		input.addEventListener('keydown', keys);
		list.addEventListener('mousedown', function (e) {
			var li = e.target.closest('li');
			if (li && li.dataset.url) { e.preventDefault(); go(li.dataset.url); }
		});
	}

	function note(text) {
		status.textContent = text;
		status.style.display = text ? '' : 'none';
	}

	function render(query) {
		list.textContent = '';
		items = [];
		at = -1;
		var q = query.trim();
		if (!pages) { note('Указатель ещё едет…'); return; }
		if (!q) { note('Начните вводить название раздела или страницы.'); return; }
		var found = pick(pages, q);
		if (!found.length) { note('Ничего не нашлось. Полный поиск по тексту — на /search/'); return; }
		note('');
		var words = fold(q).split(/\s+/).filter(function (w) { return w.length > 0; });
		found.forEach(function (p, i) {
			var li = document.createElement('li');
			li.id = 'nav-i' + i;
			li.setAttribute('role', 'option');
			li.dataset.url = p.url;
			var t = document.createElement('span');
			t.className = 't';
			t.appendChild(mark(p.title, words));
			var s = document.createElement('span');
			s.className = 's';
			s.textContent = p.section;
			li.appendChild(t);
			li.appendChild(s);
			list.appendChild(li);
			items.push(li);
		});
		select(0);
	}

	function select(i) {
		if (!items.length) return;
		if (at >= 0 && items[at]) items[at].setAttribute('aria-selected', 'false');
		at = (i + items.length) % items.length;
		items[at].setAttribute('aria-selected', 'true');
		input.setAttribute('aria-activedescendant', items[at].id);
		var li = items[at], top = li.offsetTop, bottom = top + li.offsetHeight;
		if (top < list.scrollTop) list.scrollTop = top;
		else if (bottom > list.scrollTop + list.clientHeight) list.scrollTop = bottom - list.clientHeight;
	}

	function keys(e) {
		if (e.key === 'ArrowDown') { e.preventDefault(); select(at + 1); }
		else if (e.key === 'ArrowUp') { e.preventDefault(); select(at - 1); }
		else if (e.key === 'Enter') {
			e.preventDefault();
			if (items[at]) go(items[at].dataset.url);
		}
		else if (e.key === 'Escape') { e.preventDefault(); close(); }
		else if (e.key === 'Tab') e.preventDefault();   // фокус не уходит из палитры
	}

	function go(url) {
		close();
		location.href = url;
	}

	function open() {
		if (!box) build();
		opener = document.activeElement;
		box.classList.add('on');
		input.value = '';
		render('');
		input.focus();
		load().then(function (ok) {
			if (!box.classList.contains('on')) return;
			if (!ok) { note('Указатель не загрузился. Поиск по тексту — на /search/'); return; }
			render(input.value);
		});
	}

	function close() {
		if (!box) return;
		box.classList.remove('on');
		// Фокус уводится из палитры обязательно: после закрытия она спрятана, и
		// оставленный в ней фокус — это фокус в никуда. Возвращается он туда,
		// откуда палитру открыли; а открыли её могли и с `body` (мышью по
		// кнопке фокус не ставится, да и сочетание клавиш ловится на документе),
		// и тогда место фокусу — на кнопке: она и есть дверь в палитру.
		if (input) input.blur();
		var back = opener && opener.focus && opener !== document.body
			? opener : document.getElementById('nav-open');
		if (back && back.focus) back.focus();
		opener = null;
	}

	function isOpen() {
		return box && box.classList.contains('on');
	}

	/* --- сочетание клавиш -------------------------------------------------
	 *
	 * ⌘K на macOS, Ctrl-K на всём прочем. В Firefox Ctrl-K фокусирует строку
	 * поиска браузера, а в Chrome — адресную; preventDefault снимает и то и
	 * другое.
	 *
	 * Второе сочетание — «/», как заведено у многих: оно ничего не занимает.
	 * Но только когда читатель не пишет: в поле ввода «/» — это косая черта.
	 */
	function typing(el) {
		if (!el) return false;
		var tag = el.tagName;
		return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable;
	}

	function shortcut(e) {
		if (isOpen()) return;
		if ((e.metaKey || e.ctrlKey) && !e.altKey && (e.key === 'k' || e.key === 'K')) {
			e.preventDefault();
			open();
			return;
		}
		if (e.key === '/' && !e.metaKey && !e.ctrlKey && !e.altKey && !typing(e.target)) {
			e.preventDefault();
			open();
		}
	}

	/* --- кнопка в шапке ---------------------------------------------------- */

	function button() {
		var title = document.getElementById('title');
		var mac = /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent);
		var b = document.createElement('button');
		b.id = 'nav-open';
		b.type = 'button';
		b.setAttribute('aria-label', 'Быстрый переход по разделам');
		b.setAttribute('data-tip', 'Быстрый переход по разделам — ' + (mac ? '⌘K' : 'Ctrl K') + ' или /');
		b.innerHTML = '⌕ <kbd>' + (mac ? '⌘K' : 'Ctrl K') + '</kbd>';
		b.addEventListener('click', open);
		if (title) {
			title.appendChild(b);
		} else {
			b.className = 'float';
			document.body.appendChild(b);
		}
	}

	function run() {
		styles();
		button();
		document.addEventListener('keydown', shortcut);
		// Указатель забирается на простое: к первому нажатию он уже здесь, а
		// загрузку страницы это не задерживает.
		var idle = window.requestIdleCallback || function (f) { setTimeout(f, 1200); };
		idle(function () { load(); });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
