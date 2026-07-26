/* Ссылки-якоря на строфы в главах «Натьяшастры».
 *
 * Текст размечен построфно («7/», «9-10/»), и номер строфы — куда более
 * устойчивый якорь, чем порядковый номер абзаца: ссылка на 36.7 останется
 * верной, даже если абзацы перевёрстают или переведут заново.
 *
 * Для диапазонов («1-6/») заводятся ещё и якоря на каждый номер внутри, чтобы
 * ссылка на 36.3 приводила туда, где эта строфа напечатана.
 *
 * Тема подключается удалённо и точки расширения не имеет, поэтому скрипт
 * подключается строкой в конце каждой главы, а стили ставит себе сам.
 */
(function () {
	'use strict';

	var VERSE = /^\s*(\d+)\s*(?:[-–—]\s*(\d+))?\s*\//;

	function styles() {
		var css = [
			'.vh{opacity:.25;text-decoration:none;margin-right:.4em;font-size:.85em}',
			'.vh:hover,.vh:focus{opacity:1;text-decoration:none}',
			'p:target{background:rgba(255,220,120,.25);border-radius:3px}',
			'.to-top{position:fixed;left:12px;bottom:12px;z-index:998;',
			'padding:.4em .75em;border-radius:999px;cursor:pointer;',
			'font:9pt/1.4 Verdana,Arial,sans-serif;',
			'opacity:0;visibility:hidden;transition:opacity .18s ease,visibility .18s ease}',
			'.to-top.is-visible{opacity:.75;visibility:visible}',
			'.to-top:hover,.to-top:focus{opacity:1}',
			'@media (prefers-reduced-motion:reduce){.to-top{transition:none}}',
			'@media print{.vh,.to-top{display:none}}'
		].join('');
		var el = document.createElement('style');
		el.appendChild(document.createTextNode(css));
		document.head.appendChild(el);
	}

	function mark() {
		var seen = Object.create(null);

		Array.prototype.forEach.call(document.querySelectorAll('p'), function (p) {
			var m = VERSE.exec(p.textContent);
			if (!m) return;

			var from = parseInt(m[1], 10);
			var to = m[2] ? parseInt(m[2], 10) : from;
			var id = 'v' + (m[2] ? from + '-' + to : from);
			if (seen[id]) return;
			seen[id] = true;
			p.id = id;

			// Внутри диапазона — пустые якоря на каждый номер, чтобы ссылка на
			// отдельную строфу вела в нужный абзац.
			for (var n = from; n <= to && to - from < 40; n++) {
				var alias = 'v' + n;
				if (seen[alias] || document.getElementById(alias)) continue;
				seen[alias] = true;
				var a = document.createElement('span');
				a.id = alias;
				p.insertBefore(a, p.firstChild);
			}

			var link = document.createElement('a');
			link.className = 'vh';
			link.href = '#' + id;
			link.title = 'Ссылка на эту строфу';
			link.appendChild(document.createTextNode('#'));
			p.insertBefore(link, p.firstChild);
		});
	}

	/* Кнопка «наверх»: главы длинные, а листать обратно к оглавлению долго.
	   Появляется, когда прокручено больше экрана. */
	function toTop() {
		var btn = document.createElement('button');
		btn.type = 'button';
		btn.className = 'to-top';
		btn.title = 'В начало страницы';
		btn.setAttribute('aria-label', 'В начало страницы');
		btn.appendChild(document.createTextNode('↑ наверх'));
		btn.onclick = function () {
			window.scrollTo({ top: 0, behavior: 'smooth' });
		};
		document.body.appendChild(btn);

		var pending = false;
		function update() {
			pending = false;
			btn.classList.toggle('is-visible', window.scrollY > window.innerHeight);
		}
		function schedule() {
			if (pending) return;
			pending = true;
			window.requestAnimationFrame(update);
		}
		window.addEventListener('scroll', schedule, { passive: true });
		window.addEventListener('resize', schedule, { passive: true });
		update();
	}

	function run() {
		styles();
		mark();
		toTop();
		// Якоря появились только сейчас, так что переход по ссылке из адресной
		// строки нужно доиграть вручную.
		if (location.hash) {
			var target = document.getElementById(location.hash.slice(1));
			if (target) target.scrollIntoView();
		}
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
