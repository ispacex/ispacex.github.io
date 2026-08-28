/* Толкование санскритского слова — на месте, при наведении.
 *
 * Слово в подстрочнике, у которого есть статья в словаре, — ссылка туда:
 * точечная черта снизу, `.pv-gl`. Чтобы узнать, что оно значит, читателю
 * приходилось уходить со страницы, искать строку в словаре и возвращаться, а
 * таких слов на странице десятки: по пяти разделам КШ их 5537. Подсказка
 * показывает термин и толкование прямо тут (VS-35).
 *
 * Ссылка при этом остаётся ссылкой. Подсказка — вдобавок к переходу в словарь,
 * а не вместо: там есть озвучка, деванагари и «где в тексте это разбирается».
 *
 * Откуда берётся текст. Рядом со страницей словаря лежит `terms.json` — те же
 * статьи, но три поля из пяти и без разметки таблицы: 20–30 КБ на раздел, 6–9
 * в сжатом виде, против сотни килобайт самой страницы. Собирает его та же
 * сборка, что и словарь (tools/common/terms.py, `dump`), поэтому разойтись им
 * негде. Забирается он при первом наведении и остаётся в памяти — тем же
 * приёмом, каким палитра забирает /nav-index.json.
 *
 * На языке страницы подсказка говорит сама собою: у переведённого словаря лежит
 * свой `terms.json`, собранный из переведённой же страницы, а адрес словаря
 * скрипт берёт из ссылки — на английской странице она ведёт в /en/.
 *
 * Свои стили скрипт вставляет сам и ставит первыми в <head> — как outline.js и
 * glossary.js: правила сайта тогда выигрывают спор о весе, и подсказка видна в
 * локальной сборке, где темы нет (tools/build-local.sh).
 *
 * Висит скрипт в макете, то есть на всех страницах сайта, а подстрочник есть
 * только в разделах КШ: страница без `.pv-gl` выходит из run() первой строкой,
 * ничего не построив и никуда не сходив. Перечня разделов здесь поэтому нет —
 * он разошёлся бы со страницами при первой же правке.
 */
(function () {
	'use strict';

	/* Задержка перед появлением. Подстрочники стоят плотно и мелко, и мышь
	   пересекает десяток за одно движение: без задержки подсказки вспыхивали бы
	   одна за другой всю дорогу поперёк строки. Исчезновение мгновенное — то,
	   что мешает читать, обязано убираться сразу. */
	var DELAY = 350;
	/* Просвет между словом и подсказкой и поле окна, за которое она не заходит. */
	var GAP = 8;
	var EDGE = 8;

	var books = {};    /* адрес словаря → обещание карты статей */
	var tip = null;
	var at = null;     /* ссылка, на которой читатель сейчас */
	var asked = null;  /* ссылка, по которой уже тапнули: второй тап — переход */
	var timer = 0;

	function anchor(node) {
		return node && node.closest ? node.closest('a.pv-gl') : null;
	}

	/* Где лежит словарь и какая в нём строка — сказано в самой ссылке:
	   `/ksh/pv/glossary/#t-srsti`. Ключ статьи в ней уже есть, искать нечего.
	   Раздел отсюда же: не список разделов в скрипте, а адрес, по которому
	   читатель и так пойдёт щелчком. */
	function which(a) {
		var href = a.getAttribute('href') || '';
		var cut = href.indexOf('#t-');
		if (cut < 1) return null;
		return { url: href.slice(0, cut) + 'terms.json', key: href.slice(cut + 3) };
	}

	/* Словарь раздела забирается один раз на страницу. Не отдался — пустая
	   карта: подсказки не будет, а ссылка работает, как работала. */
	function book(url) {
		if (!books[url]) {
			books[url] = fetch(url).then(function (r) {
				return r.ok ? r.json() : {};
			}).catch(function () { return {}; });
		}
		return books[url];
	}

	function styles() {
		var css = [
			'#gl-tip{--g-bg:#1a1d24;--g-fg:#e6e6e6;--g-line:rgba(128,128,128,.4);',
			'position:fixed;z-index:9990;max-width:min(24rem,calc(100vw - 1rem));',
			'background:var(--g-bg);color:var(--g-fg);border:1px solid var(--g-line);',
			'border-radius:.4rem;box-shadow:0 .6rem 1.6rem rgba(0,0,0,.45);',
			'padding:.5em .7em;font-size:.85rem;line-height:1.45;',
			/* Подсказка не ловит указатель: она стоит вплотную к строке, и
			   курсор, зашедший на неё, ушёл бы со слова и погасил бы её же. */
			'pointer-events:none}',
			/* Своё правило, а не одно умолчание браузера: у темы `display`
			   ставится многим, и скрытая подсказка мигнула бы в углу. */
			'#gl-tip[hidden]{display:none}',
			'#gl-tip p{margin:0}',
			'#gl-tip .gl-head{margin-bottom:.25em}',
			'#gl-tip .gl-iast{font-style:italic;opacity:.7}',
			'#gl-tip .gl-say{opacity:.85}',
			'@media print{#gl-tip{display:none}}'
		].join('');
		var el = document.createElement('style');
		el.appendChild(document.createTextNode(css));
		document.head.insertBefore(el, document.head.firstChild);
	}

	function fill(term) {
		var head = document.createElement('p');
		head.className = 'gl-head';
		var name = document.createElement('strong');
		name.appendChild(document.createTextNode(term.name));
		var iast = document.createElement('span');
		iast.className = 'gl-iast';
		iast.appendChild(document.createTextNode(term.iast));
		head.appendChild(name);
		head.appendChild(document.createTextNode(' '));
		head.appendChild(iast);

		var say = document.createElement('p');
		say.className = 'gl-say';
		/* Толкование приходит размеченным — `код` и полужирное в нём стоят и в
		   таблице словаря, и без разметки читатель увидел бы кавычки глазами.
		   Разметку ставит наша же сборка (common/terms.py, `markup`), опасные
		   знаки она экранирует там же, и со стороны сюда ничего не приходит. */
		say.innerHTML = term.gloss;

		tip.textContent = '';
		tip.appendChild(head);
		tip.appendChild(say);
	}

	function place(a) {
		/* Мерить надо развёрнутую подсказку, поэтому показываем её раньше, чем
		   ставим на место, — но в углу, где она ничего не заслоняет. */
		tip.style.left = EDGE + 'px';
		tip.style.top = EDGE + 'px';
		tip.hidden = false;

		var r = a.getBoundingClientRect();
		var box = tip.getBoundingClientRect();

		/* Ниже строки, а не выше. Подстрочники стоят плотно, и подсказка,
		   вылезающая вверх, накрыла бы ту самую строку, которую читают. У
		   нижнего края окна места нет — тогда выше; не помещается и там —
		   прижимаем к низу: в окне высотой меньше подсказки заслонить
		   что-нибудь придётся в любом случае. */
		var top = r.bottom + GAP;
		if (top + box.height > innerHeight - EDGE) {
			var over = r.top - GAP - box.height;
			top = over >= EDGE ? over : Math.max(EDGE, innerHeight - EDGE - box.height);
		}

		/* По середине слова, но не за краем окна. */
		var left = r.left + r.width / 2 - box.width / 2;
		left = Math.max(EDGE, Math.min(left, innerWidth - EDGE - box.width));

		tip.style.left = Math.round(left) + 'px';
		tip.style.top = Math.round(top) + 'px';
		a.setAttribute('aria-describedby', 'gl-tip');
	}

	function show(a) {
		var where = which(a);
		if (!where) return;
		book(where.url).then(function (map) {
			var term = map[where.key];
			/* Пока ходили за словарём, читатель мог увести мышь или уйти
			   дальше: подсказка тогда уже не про то слово. Статьи нет —
			   молчим: ссылка ведёт в словарь и без нас. */
			if (!term || at !== a) return;
			fill(term);
			place(a);
		});
	}

	function hide() {
		clearTimeout(timer);
		timer = 0;
		asked = null;
		if (at) at.removeAttribute('aria-describedby');
		at = null;
		if (tip) tip.hidden = true;
	}

	/* Мышь есть не у всех, а пальцем «навести» нельзя. Спрашиваем не про
	   устройство, а про то, умеет ли указатель зависать, и спрашиваем каждый
	   раз: на планшете с приставной клавиатурой ответ меняется по ходу дела. */
	function hovers() {
		return matchMedia('(hover: hover)').matches;
	}

	function watch() {
		document.addEventListener('mouseover', function (e) {
			if (!hovers()) return;
			var a = anchor(e.target);
			if (!a || a === at) return;
			hide();
			at = a;
			timer = setTimeout(function () { show(a); }, DELAY);
		});

		document.addEventListener('mouseout', function (e) {
			if (!hovers()) return;
			var a = anchor(e.target);
			/* Переход внутри той же ссылки уходом не считается. */
			if (a && a === at && !(e.relatedTarget && a.contains(e.relatedTarget))) hide();
		});

		/* С клавиатуры — сразу и без задержки: до ссылки дошли табуляцией, то
		   есть нарочно, а не пересекли её по дороге. */
		document.addEventListener('focusin', function (e) {
			var a = anchor(e.target);
			if (!a) return;
			hide();
			at = a;
			show(a);
		});

		document.addEventListener('focusout', function (e) {
			if (anchor(e.target)) hide();
		});

		document.addEventListener('click', function (e) {
			var a = anchor(e.target);
			if (!a) {
				hide();
				return;
			}
			/* Мышью щелчок ведёт в словарь, как и вёл. */
			if (hovers()) return;
			/* Пальцем навести нельзя, поэтому первый тап показывает толкование,
			   а второй уводит в словарь. Помним саму ссылку, а не то, видна ли
			   подсказка: слова без статьи в `terms.json` быть не должно, но
			   если оно там окажется, второй тап обязан сработать всё равно. */
			if (asked === a) return;
			e.preventDefault();
			if (at !== a) hide();
			at = a;
			asked = a;
			show(a);
		});

		/* Подсказка привязана к окну, а не к строке: при прокрутке она уехала
		   бы от своего слова, и убрать её дешевле, чем возить следом. */
		addEventListener('scroll', hide, { passive: true });
		addEventListener('resize', hide);
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape') hide();
		});
	}

	function run() {
		if (!document.querySelector('a.pv-gl')) return;

		styles();
		tip = document.createElement('div');
		tip.id = 'gl-tip';
		tip.setAttribute('role', 'tooltip');
		tip.hidden = true;
		document.body.appendChild(tip);
		watch();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
