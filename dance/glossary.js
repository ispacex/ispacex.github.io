/* Словарь терминов: фильтр по строкам и озвучка санскритских слов.
 *
 * Пока звуковые файлы не сгенерированы, кнопки откатываются на системный
 * синтез речи. Отдавать ему IAST как есть нельзя: диакритику он глотает
 * (rasa и rāsa звучат одинаково, ś читается как s), поэтому произносится не
 * написание, а его переложение. Где общее правило врёт — у строки стоит
 * data-say с живым произношением.
 */
(function () {
	'use strict';

	var AUDIO_BASE = '/dance/audio/';

	/* Порядок значим: сочетания разбираются раньше одиночных знаков. */
	var RESPELL = [
		['jñ', 'gy'],                 /* jñāna → гьяана, а не джняана */
		['ch', 'chh'], ['c', 'ch'],   /* IAST c — это «ч» */
		['ññ', 'nny'], ['ñ', 'ny'],
		['ṅg', 'ng'], ['ṅk', 'nk'], ['ṅ', 'ng'],
		['ā', 'aa'], ['ī', 'ee'], ['ū', 'oo'],
		['ṛ', 'ri'], ['ṝ', 'ree'], ['ḷ', 'l'],
		['ṇ', 'n'], ['ṃ', 'm'], ['ṁ', 'm'],
		['ṭ', 't'], ['ḍ', 'd'],
		['ś', 'sh'], ['ṣ', 'sh'], ['ḥ', 'h']
	];

	function respell(s) {
		var out = RESPELL.reduce(function (acc, pair) {
			return acc.split(pair[0]).join(pair[1]);
		}, s.toLowerCase());

		/* «y» после согласной — глайд, а не слог: в hāsya это «хасья». Но
		   синтезатор на «haasya» вставляет гласную и выговаривает «хасая»,
		   поэтому слог разделяем явно: «haas-ya».

		   Условие «есть предшествующий знак» отсекает начало слова: во
		   vyabhicāri тот же «vy» читается как «вья» и правильно, разрывать
		   его не надо. После гласной (abhinaya, laya) «ya» и так слог. */
		return out.replace(/(.)([bcdfghjklmnpqrstvz])y/g, '$1$2-y');
	}

	function styles() {
		var css = [
			'.gl-wrap{overflow-x:auto}',
			'table.gl{border-collapse:collapse;width:100%}',
			'table.gl th,table.gl td{text-align:left;vertical-align:top;padding:.35em .6em;',
			'border-bottom:1px solid rgba(128,128,128,.35)}',
			'table.gl th{white-space:nowrap}',
			'table.gl td.term{white-space:nowrap}',
			'table.gl td.skt{white-space:nowrap;font-style:italic}',
			'button.tts{background:none;border:1px solid rgba(128,128,128,.5);border-radius:999px;',
			'color:inherit;cursor:pointer;font-size:.8em;line-height:1;padding:.15em .4em;',
			'margin-left:.35em;opacity:.5}',
			'button.tts:hover,button.tts:focus{opacity:1}',
			'#gl-filter{padding:.3em .6em;width:100%;max-width:26em}',
			'@media print{button.tts,#gl-filter{display:none}}'
		].join('');
		var el = document.createElement('style');
		el.appendChild(document.createTextNode(css));
		document.head.appendChild(el);
	}

	/* Диакритику сворачиваем с обеих сторон: ищущий наберёт «rangapuja», а в
	   таблице стоит «raṅgapūjā». NFD разбивает букву на основу и знак, знак
	   выбрасываем. */
	function fold(s) {
		return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
	}

	function filter() {
		var input = document.getElementById('gl-filter');
		if (!input) return;
		var rows = [].filter.call(document.querySelectorAll('table.gl tr'), function (tr) {
			return !tr.querySelector('th');
		});
		input.addEventListener('input', function () {
			var q = fold(input.value.trim());
			rows.forEach(function (tr) {
				tr.style.display = !q || fold(tr.textContent).indexOf(q) !== -1 ? '' : 'none';
			});
		});
	}

	function speech() {
		var canSpeak = 'speechSynthesis' in window;

		[].forEach.call(document.querySelectorAll('td[data-tts]'), function (td) {
			var slug = td.getAttribute('data-tts');
			/* Снимаем написание до вставки кнопки, иначе её символ уедет в озвучку. */
			var iast = td.textContent.trim();
			var spoken = td.getAttribute('data-say') || respell(iast);

			var btn = document.createElement('button');
			btn.className = 'tts';
			btn.type = 'button';
			btn.title = 'Произношение';
			btn.setAttribute('aria-label', 'Произношение: ' + iast);
			btn.appendChild(document.createTextNode('♪'));
			btn.addEventListener('click', function () {
				new Audio(AUDIO_BASE + slug + '.mp3').play().catch(function () {
					if (!canSpeak) return;
					speechSynthesis.cancel();
					var u = new SpeechSynthesisUtterance(spoken);
					u.lang = 'hi-IN';
					u.rate = 0.75;
					speechSynthesis.speak(u);
				});
			});
			td.appendChild(btn);
		});
	}

	function run() {
		styles();
		filter();
		speech();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
