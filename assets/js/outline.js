/* Разделы страницы: список подзаголовков, висящий справа от текста.
 *
 * Страницы стали длинными — у словаря Pratyabhijñāhṛdayam одиннадцать разделов
 * и 111 статей, у обзора писаний Трики таблица на полэкрана, — и дойдя до
 * середины, читатель не видит ни где он, ни что на странице есть ещё. Список
 * висит на месте, отмечает текущий раздел и переносит в любой другой одним
 * щелчком.
 *
 * Правило общее и никем не ведётся руками: подзаголовков на странице больше
 * двух — список есть, меньше — нет вовсе. Список, набранный отдельно от
 * страницы, разошёлся бы с ней при первой же правке; этот собирается из самих
 * заголовков и разойтись не может.
 *
 * Свои стили скрипт вставляет сам, как это делает glossary.js, и ставит их
 * первыми в <head> — чтобы правила сайта из assets/css/style.scss выигрывали
 * спор о весе, если сайту понадобится что-то поправить. Заодно список виден и
 * в локальной сборке, где темы нет и style.scss исключён (tools/build-local.sh).
 */
(function () {
	'use strict';

	/* Список говорит на языке страницы — по тому же <html lang>, по которому
	   выбирает свои слова палитра перехода. Русский — запасной: он был здесь
	   первым и остаётся ответом для языка, которого никто не назвал. */
	var SAY = {
		ru: { cap: 'На этой странице', label: 'Разделы этой страницы' },
		en: { cap: 'On this page', label: 'Sections of this page' }
	};

	/* Меньше трёх разделов — не оглавление, а повтор начала страницы. */
	var LEAST = 3;

	/* Насколько выше верха окна должен уйти заголовок, чтобы считаться
	   текущим. Ноль тут не годится: у заголовка с адресом стоит
	   `scroll-margin-top:1.2em`, и тот, к которому только что перешли по
	   ссылке, встаёт не вплотную к верху, а на два десятка точек ниже — с нулём
	   он оказался бы «ещё не достигнут» сразу после перехода к нему. */
	var PASSED = 48;

	function words() {
		var lang = (document.documentElement.getAttribute('lang') || '')
			.slice(0, 2).toLowerCase();
		return SAY[lang] || SAY.ru;
	}

	function styles() {
		var css = [
			'#page-outline{--o-line:rgba(128,128,128,.35);--o-mark:#8be9fd;',
			/* Колонка текста у темы шириной 650px и стоит посередине окна,
			   поэтому список привязан к её краю, а не к краю окна: иначе на
			   широком экране он уезжал бы от текста всё дальше. */
			'position:fixed;top:8.5rem;left:calc(50% + 350px);width:210px;',
			'max-height:68vh;overflow-y:auto;z-index:20;',
			'font-size:.82rem;line-height:1.35;display:none}',
			'#page-outline .cap{font-size:.68rem;letter-spacing:.08em;',
			'text-transform:uppercase;opacity:.45;margin:0 0 .5em .7em}',
			'#page-outline ul{list-style:none;margin:0;padding:0;',
			'border-left:1px solid var(--o-line)}',
			'#page-outline li{margin:0}',
			'#page-outline a{display:block;padding:.25em .7em;color:inherit;',
			'text-decoration:none;opacity:.5;margin-left:-1px;',
			'border-left:2px solid transparent}',
			'#page-outline a.sub{padding-left:1.6em;opacity:.4}',
			'#page-outline a:hover,#page-outline a:focus-visible{opacity:1}',
			'#page-outline a[aria-current]{opacity:1;color:var(--o-mark);',
			'border-left-color:currentColor}',
			/* Справа от колонки место есть не на всяком экране: ниже этого
			   порога список наехал бы на текст, и его нет — как на телефоне.
			   650 колонки, 40 её полей, 25 просвета, 210 списка и поле окна. */
			'@media (min-width:1180px){#page-outline{display:block}}',
			/* Фильтр словаря может убрать со страницы почти всё: с одним
			   оставшимся разделом список ни к чему. Правило весом выше
			   предыдущего — идентификатор и класс против одного
			   идентификатора, — поэтому спор выигрывает без !important. */
			'#page-outline.empty{display:none}',
			'@media print{#page-outline{display:none}}'
		].join('');
		var el = document.createElement('style');
		el.appendChild(document.createTextNode(css));
		document.head.insertBefore(el, document.head.firstChild);
	}

	/* Заголовки самой страницы. Шапка и подвал темы сюда не идут: название
	   сайта — не раздел страницы, а строка, повторяющаяся на всех.
	 *
	   Уровня два, и оба нужны. Главы «Натьяшастры» размечены то `h2`, то `h3`
	   — у 22-й главы тридцать `h3` и ни одного `h2`, — а у /ship/ раздел один,
	   зато под ним три. Считать только `h2` значило бы обойти список ровно те
	   страницы, где он нужнее всего. */
	function headings() {
		var root = document.querySelector('.wrapper section') || document.body;
		return [].filter.call(root.querySelectorAll('h2, h3'), function (h) {
			return !h.closest('#title, #footer');
		});
	}

	function build(hs, say) {
		/* Уровень, с которого страница начинается, у каждой свой: у 22-й главы
		   «Натьяшастры» все тридцать заголовков — `h3`, и отступ у всех тридцати
		   значил бы ровно ничего. Отступ получает тот, кто глубже верхнего
		   уровня этой страницы, а не тот, кто глубже `h2`. */
		var upmost = Math.min.apply(null, hs.map(function (h) {
			return +h.tagName.slice(1);
		}));

		var nav = document.createElement('nav');
		nav.id = 'page-outline';
		nav.setAttribute('aria-label', say.label);

		var cap = document.createElement('p');
		cap.className = 'cap';
		cap.appendChild(document.createTextNode(say.cap));
		nav.appendChild(cap);

		var ul = document.createElement('ul');
		var items = hs.map(function (h, i) {
			/* Адрес заголовку ставит сборка страниц, и на страницах этого
			   макета он есть у всех до одного. Но написанный руками заголовок
			   может остаться без адреса; тогда заводим свой, проверив, что
			   такой на странице не занят: две одинаковые метки уводили бы
			   ссылку не туда, и молча. */
			if (!h.id) {
				var n = i + 1;
				while (document.getElementById('h' + n)) n += hs.length;
				h.id = 'h' + n;
			}
			var li = document.createElement('li');
			var a = document.createElement('a');
			// Подзаголовок, стоящий под другим, — отступом: список о том, как
			// страница устроена, а плоский он про это и умалчивает.
			if (+h.tagName.slice(1) > upmost) a.className = 'sub';
			a.href = '#' + h.id;
			a.appendChild(document.createTextNode((h.textContent || '').trim()));
			li.appendChild(a);
			ul.appendChild(li);
			return { h: h, li: li, a: a, gone: false };
		});
		nav.appendChild(ul);
		document.body.appendChild(nav);
		return { nav: nav, items: items };
	}

	function run() {
		var hs = headings();
		if (hs.length < LEAST) return;

		styles();
		var made = build(hs, words());
		var nav = made.nav, items = made.items;

		/* Фильтр словаря убирает разделы, из которых после отбора не осталось
		   ни строки, — вместе с их заголовками (assets/js/glossary.js). Список,
		   оставивший такой пункт, вёл бы в пустоту.
		 *
		   Слушаем не событие, а сам заголовок: тот, кто его прячет, ничего о
		   списке знать не обязан, и завтра прятать может кто-то ещё. Разговор
		   через событие пришлось бы заводить с каждым из них порознь. */
		function sync() {
			var live = 0;
			items.forEach(function (it) {
				it.gone = it.h.offsetParent === null;
				it.li.style.display = it.gone ? 'none' : '';
				if (!it.gone) live++;
			});
			nav.classList.toggle('empty', live < 2);
		}

		/* Текущий — последний заголовок, ушедший выше верха окна, а не
		   «видимый»: короткий раздел проскакивает окно целиком, и подсветка по
		   видимости на нём прыгает через раз. */
		function mark() {
			var cur = null;
			items.forEach(function (it) {
				if (it.gone) return;
				if (it.h.getBoundingClientRect().top <= PASSED) cur = it;
			});
			items.forEach(function (it) {
				if (it === cur) it.a.setAttribute('aria-current', 'location');
				else it.a.removeAttribute('aria-current');
			});
			if (cur) reveal(cur.a);
		}

		/* Разделов бывает и тридцать — у 22-й главы «Натьяшастры», — и тогда
		   список сам становится прокручиваемым, а отмеченный раздел уезжает за
		   его край. Двигаем только сам список: `scrollIntoView` увёз бы заодно
		   и страницу, отняв её у читателя, который её и прокручивает. */
		function reveal(a) {
			var box = nav.getBoundingClientRect();
			var r = a.getBoundingClientRect();
			if (r.top < box.top) nav.scrollTop -= box.top - r.top;
			else if (r.bottom > box.bottom) nav.scrollTop += r.bottom - box.bottom;
		}

		var waiting = false;
		function later() {
			if (waiting) return;
			waiting = true;
			requestAnimationFrame(function () { waiting = false; mark(); });
		}

		var watch = new MutationObserver(function () { sync(); mark(); });
		items.forEach(function (it) {
			watch.observe(it.h, { attributes: true, attributeFilter: ['style', 'class'] });
		});

		addEventListener('scroll', later, { passive: true });
		addEventListener('resize', later, { passive: true });
		sync();
		mark();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
