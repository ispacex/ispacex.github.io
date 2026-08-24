/* Забрать строфы целиком — санскритом или транслитерацией.
 *
 * На странице они стоят построчно, одно под другим, и выделить мышью только
 * деванагари или только транслитерацию нельзя: строки чередуются. Кнопка
 * собирает из стены строфы одного письма и кладёт их в буфер по порядку.
 *
 * Стена помечена одинаковым data-pv у кнопок и у абзацев, поэтому на странице
 * их может быть сколько угодно, и каждая копируется отдельно.
 */
(function () {
	'use strict';

	function collect(group, what) {
		var rows = document.querySelectorAll(
			'p.pv-pair[data-pv="' + group + '"] span.' + what);
		return Array.prototype.map.call(rows, function (s) {
			return s.textContent;
		}).join('\n');
	}

	function put(text) {
		if (navigator.clipboard && navigator.clipboard.writeText) {
			return navigator.clipboard.writeText(text);
		}
		// Старый способ — на случай, когда буфера в этом виде нет.
		return new Promise(function (ok, no) {
			var area = document.createElement('textarea');
			area.value = text;
			area.setAttribute('readonly', '');
			area.style.position = 'fixed';
			area.style.left = '-9999px';
			document.body.appendChild(area);
			area.select();
			var done = document.execCommand && document.execCommand('copy');
			document.body.removeChild(area);
			done ? ok() : no(new Error('нет доступа к буферу'));
		});
	}

	document.addEventListener('click', function (e) {
		var btn = e.target.closest && e.target.closest('button[data-pv-copy]');
		if (!btn) return;
		var text = collect(btn.getAttribute('data-pv-copy'), btn.getAttribute('data-pv-what'));
		if (!text) return;
		// Слово на кнопке возвращается назад: без ответа непонятно, сработало
		// ли, а буфер собой не показывает.
		var was = btn.textContent;
		put(text).then(function () {
			btn.textContent = 'Скопировано';
		}, function () {
			btn.textContent = 'Не вышло — скопируйте вручную';
		}).then(function () {
			setTimeout(function () { btn.textContent = was; }, 1600);
		});
	});
})();
