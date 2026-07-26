/* Словарь терминов: фильтр по строкам и озвучка санскритских слов.
 *
 * Комплектов озвучки два, и читают они по-разному: «системный» — macOS-голос
 * hi_IN, применяющий правило хинди и проглатывающий конечное краткое «а»
 * (saṅgha → «сангх»); Parler — ai4bharat/indic-parler-tts, обученный в том
 * числе на санскрите, окончание выговаривает. Выбор запоминается.
 *
 * Если файла нет ни в одном комплекте, кнопка откатывается на системный синтез
 * речи. Отдавать ему IAST как есть нельзя: диакритику он глотает (rasa и rāsa
 * звучат одинаково, ś читается как s), поэтому произносится не написание, а
 * его переложение. Где общее правило врёт — у строки стоит data-say с живым
 * произношением.
 */
(function () {
	'use strict';

	var AUDIO_BASE = '/dance/audio/';
	var VOICES = { parler: 'parler/', lekha: '' };
	var STORE = 'ns-voice';

	function chosen() {
		var v = null;
		try { v = localStorage.getItem(STORE); } catch (e) { /* приватный режим */ }
		return VOICES.hasOwnProperty(v) ? v : 'parler';
	}

	function remember(v) {
		try { localStorage.setItem(STORE, v); } catch (e) { /* не беда */ }
	}

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

		/* Хинди-голос отбрасывает конечное краткое «a»: संघ он читает «сангх».
		   В пали и санскрите этот слог произносится, поэтому отделяем его —
		   «san-gha». Придыхательные (kh, gh, ch, dh, sh) идут в перечислении
		   целиком: это один согласный, рвать его посередине нельзя. */
		out = out.replace(/(chh|[kgcjtdpbs]h|[bcdfghjklmnpqrstvyz])a$/, '-$1a');

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
			/* Деванагари при том же кегле выглядит мельче латиницы. */
			'table.gl td.deva{white-space:nowrap;font-size:1.15em;line-height:1.4}',
			'button.tts{background:none;border:1px solid rgba(128,128,128,.5);border-radius:999px;',
			'color:inherit;cursor:pointer;font-size:.8em;line-height:1;padding:.15em .4em;',
			'margin-left:.35em;opacity:.5}',
			'button.tts:hover,button.tts:focus{opacity:1}',
			'#gl-filter{padding:.3em .6em;width:100%;max-width:26em}',
			'#gl-voice{font-size:.9em;opacity:.75}',
			'#gl-voice label{margin-right:1em;white-space:nowrap}',
			'@media print{button.tts,#gl-filter,#gl-voice{display:none}}'
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
				var hay = fold(tr.textContent + ' ' + (tr.getAttribute('data-alias') || ''));
				tr.style.display = !q || hay.indexOf(q) !== -1 ? '' : 'none';
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
				/* Выбранный комплект первый, второй — запасной: словарь
				   пополняется, и файл может быть пока только в одном из них. */
				var order = chosen() === 'parler'
					? [VOICES.parler, VOICES.lekha]
					: [VOICES.lekha, VOICES.parler];

				function say() {
					if (!canSpeak) return;
					speechSynthesis.cancel();
					var u = new SpeechSynthesisUtterance(spoken);
					u.lang = 'hi-IN';
					u.rate = 0.75;
					speechSynthesis.speak(u);
				}

				(function tryAt(i) {
					if (i >= order.length) return say();
					new Audio(AUDIO_BASE + order[i] + slug + '.mp3')
						.play().catch(function () { tryAt(i + 1); });
				})(0);
			});
			td.appendChild(btn);
		});
	}

	function voicePicker() {
		var picker = document.getElementById('gl-voice');
		if (!picker) return;
		var start = chosen();
		[].forEach.call(picker.querySelectorAll('input[name="gl-voice"]'), function (r) {
			r.checked = r.value === start;
			r.addEventListener('change', function () {
				if (r.checked) remember(r.value);
			});
		});
	}

	function run() {
		styles();
		filter();
		voicePicker();
		speech();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', run);
	} else {
		run();
	}
})();
