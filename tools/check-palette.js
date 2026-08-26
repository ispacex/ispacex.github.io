/* Проверка палитры перехода (⌘K) — того, что в ней от этого сайта.
 *
 *     ./tools/build-local.sh            # собрать сайт в _sitecheck/
 *     node tools/check-palette.js       # прогнать проверки по нему
 *
 * Сама палитра живёт в общем репозитории поиска (sitesearch/palette.js), и
 * то, что она обещает всем сайтам сразу, проверяют её собственные check-fold.js
 * (свёртка палитры и свёртка движка обязаны совпасть знак в знак) и
 * check-prepare.js (какая страница считается дверью в раздел). Пока копия
 * палитры лежала здесь, свёртку сличал этот файл; теперь копии нет, и сличать
 * нечего — обе живут в одном репозитории, там же и проверка.
 *
 * Здесь остаётся то, чего общая палитра о сайте не знает и знать не должна:
 *
 *   1. **Указатель собрался и он полон.** У каждой страницы есть название,
 *      адрес и раздел; названий, оставшихся адресом, — не больше, чем было.
 *   2. **Палитра доводит до места.** Запросы, которые читатель наберёт в
 *      первую очередь, — «Тантралока», «tantraloka», «словарь», «паруса» —
 *      дают первой строкой ту самую страницу. И у каждого языка своя выдача:
 *      читающему по-русски английский перевод той же книги не нужен вовсе.
 *   3. **Запасной ход доводит до места.** Слово, которого нет ни в одном
 *      названии, но которое есть в тексте, — «гидродинамика» — палитра отдаёт
 *      движку поиска. Проверяются оба звена сразу: что по названиям и правда
 *      пусто (иначе запасной ход не позовётся вовсе) и что движок доводит до
 *      места — до страницы книги в просмотрщике, до строфы.
 *
 *      Движок для этого запускается **настоящий**, тот самый файл, что уедет
 *      в браузер, — на подставке из tools/browser.js. Пересказать его правила — отброшенное
 *      окончание, опечатку, догрузку кусков — значило бы проверять пересказ.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const HERE = path.dirname(__dirname);
const SITE = process.argv[2] || path.join(HERE, '_sitecheck');

// Оба файла ничего не трогают в документе, пока их не позвали, — потому их и
// можно прочесть из ноды вовсе.
const SitePalette = require(path.join(HERE, 'sitesearch', 'palette.js'));
const SiteSearch = require(path.join(HERE, 'sitesearch', 'search.js'));

// --- указатель --------------------------------------------------------------

function index() {
	const file = path.join(SITE, 'nav-index.json');
	if (!fs.existsSync(file)) {
		console.log('nav-index.json не собран — сначала ./tools/build-local.sh');
		return null;
	}
	const data = JSON.parse(fs.readFileSync(file, 'utf8'));
	const pages = data.pages || [];
	const noTitle = pages.filter((p) => !p.title || !p.title.trim());
	const noSection = pages.filter((p) => !p.section);
	const asUrl = pages.filter((p) => p.title === p.url.replace(/^\//, '').replace(/\//g, ' / ').trim());
	console.log('Указатель: страниц %d, без названия %d, без раздела %d, названием стал адрес: %d',
		pages.length, noTitle.length, noSection.length, asUrl.length);
	for (const p of asUrl) console.log('   · %s', p.url);
	return { pages, bad: noTitle.length + noSection.length };
}

// --- переходы ---------------------------------------------------------------
//
// Отбор и порядок берутся у самой палитры: `prepare` раскладывает указатель в
// то, по чему она ищет, `pick` отбирает. Вывести то же самое здесь руками
// значило бы завести вторую копию правил и проверять её.

const WANT = [
	['Тантралока', '/ksh/ta/'],
	['tantraloka', '/ksh/ta/'],
	['Тантрасара', '/ksh/tantrasara/'],
	['Шивастотравали', '/ksh/sv/'],
	['Пратьябхиджняхридаям', '/ksh/ph/'],
	['натьяшастра', '/dance/'],
	['паруса', '/ship/'],
	['поиск по сайту', '/search/'],
	['писания трики', '/ksh/scriptures/'],
	['афоризм 12', '/ksh/ph/s12/'],
	// Имя раздела повышает только его заглавную страницу — но не заслоняет
	// того, кто назван точнее.
	['натьяшастра глава 12', '/dance/ns-ch12.html'],
	['натьяшастра словарь', '/dance/glossary.html'],
	['кашмирский шиваизм', '/ksh/'],
	['искусство', '/art/'],
	// Порядок внутри одинаково подходящих: главы идут числом, а не как
	// придётся.
	['тантралока глава', '/ksh/ta/ch1/'],
	// Перевод. У читателя по-русски английских страниц в палитре нет вовсе —
	// иначе всякий запрос отвечался бы дважды, тем же самым под именем, какого
	// он не набирал; у читателя по-английски они и есть его выдача.
	['scriptures of trika', null, 'ru'],
	['scriptures of trika', '/en/ksh/scriptures/', 'en'],
	['tantraloka', '/en/ksh/ta/', 'en'],
];

function jumps(pages) {
	const ready = { ru: SitePalette.prepare(pages, 'ru'), en: SitePalette.prepare(pages, 'en') };
	console.log('\nПереходы (что стоит первой строкой): по-русски %d страниц, по-английски %d',
		ready.ru.length, ready.en.length);
	let bad = 0;
	for (const [q, want, lang] of WANT) {
		const got = SitePalette.pick(ready[lang || 'ru'], q);
		const first = got.length ? got[0].url : null;
		const ok = first === want;
		if (!ok) bad++;
		console.log('  %s %s«%s» → %s%s', ok ? ' ' : '✗', lang === 'en' ? 'en ' : '   ', q,
			first || 'ничего', ok ? '' : '   ожидалось ' + (want || 'ничего'));
	}
	return bad;
}

// --- запасной ход -----------------------------------------------------------
//
// Движку нужен браузер, и подставка та же, что у проверки поиска
// (tools/browser.js): узлы, куда он кладёт находки, `fetch`, читающий из
// собранного сайта, и язык страницы, на которой мы как бы стоим. Первая ссылка
// в выдаче — то самое место, куда движок ведёт читателя, — тоже оттуда.

const { El, install } = require('./browser.js');
install(SITE, 'ru');

// Адрес в просмотрщик книги — это сама книга, её название и номер страницы,
// всё в процентах: полторы строки, за которыми не видно ответа. Показывается
// начало и якорь — то есть куда и на какое место.
function short(url) {
	const hash = url.indexOf('#');
	const head = hash === -1 ? url : url.slice(0, hash);
	const bare = decodeURIComponent(head).split('?')[0];
	return bare + (bare === head ? '' : '…') + (hash === -1 ? '' : url.slice(hash));
}

const idle = (ms) => new Promise((ok) => setTimeout(ok, ms || 30));

/* Ждём, пока движок договорит. Он сам сообщает, что не закончил: «Загружаю
   указатель…», «ищу дальше…», «читаю дальше…». Ждать по часам, а не по его же
   словам, значило бы угадывать, сколько кусков он решит прочитать.

   Но начать ждать надо не раньше, чем он начал: на событие `input` движок
   отвечает не сразу, а через 120 мс — читатель ещё печатает. Без этой паузы
   проверка успевала прочесть строку состояния от **прошлого** запроса и
   спрашивала «гидродинамику», а смотрела на ответ про «остойчивость»: все
   четыре запроса дали одно и то же число совпадений, и это единственное, что
   было заметно. */
async function settle(status) {
	await idle(200);
	for (let i = 0; i < 200; i++) {
		if (status.textContent.trim() && !/…$/.test(status.textContent.trim())) return;
		await idle();
	}
}

const TEXT = [
	// С этого запроса задача и началась. «Гидродинамика» — строка оглавления
	// книги на /ship/, а не название страницы, и палитра была права, отвечая
	// «ничего»: перехода с таким именем нет. Ведёт он туда же, куда ведёт
	// поиск, — на оглавление, где эта глава стоит ссылкой в просмотрщик.
	['гидродинамика', '/ship/'],
	// Окончание не то, какое стоит в тексте (там «остойчивости»), и находка
	// ведёт не на страницу, а в место: в просмотрщик на нужную страницу книги.
	['остойчивость', '/ship/pdf-viewer.html'],
	// Строфа, а не начало главы на триста строф.
	['вимарша', '/ksh/ta/ch1/#'],
	// Опечатка: такого слова на сайте нет вовсе, а «Тантралока» есть.
	['тантралка', '/ksh/ta/'],
];

async function fallback(pages) {
	const ready = SitePalette.prepare(pages, 'ru');
	const input = new El('input'), status = new El('p'), results = new El('ul');
	// results должен лежать в чём-то: движок ставит «Показать ещё» рядом с ним.
	results.parentNode = new El('div');
	SiteSearch.mount({
		input, status, results, repeats: 4, address: false,
		sources: [{ url: '/search-index.json' }],
	});

	let bad = 0;
	console.log('\nЗапасной ход (чего нет в названиях, но есть в тексте):');
	for (const [q, want] of TEXT) {
		const jump = SitePalette.pick(ready, q);
		input.value = q;
		results.children = [];
		status.textContent = '';
		input.fire('input');   // движок откладывает перерисовку на 120 мс
		await settle(status);
		const got = results.link;
		// Оба звена: по названиям пусто — иначе запасной ход не позовётся; и
		// движок довёл до места.
		const ok = jump.length === 0 && got && got.indexOf(want) === 0;
		if (!ok) bad++;
		console.log('  %s «%s» → %s%s', ok ? ' ' : '✗', q,
			jump.length ? 'перехват переходом: ' + jump[0].url : (got ? short(got) : 'ничего'),
			ok ? '' : '   ожидалось ' + want);
		if (!ok) console.log('      строка состояния: %s', status.textContent);
	}
	return bad;
}

async function main() {
	let bad = 0;
	const idx = index();
	if (idx) {
		bad += idx.bad;
		bad += jumps(idx.pages);
		bad += await fallback(idx.pages);
	}
	console.log(bad ? '\nрасхождений: ' + bad : '\nрасхождений нет');
	process.exit(bad ? 1 : 0);
}

main();
