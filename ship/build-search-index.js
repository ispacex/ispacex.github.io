/* Собирает указатель для поиска по книге Мархая: ship/search-index.json.
 *
 * Запускается руками, когда меняются исходники раздела:
 *
 *     node ship/build-search-index.js
 *
 * Остальной сайт индексирует Jekyll на лету, но здесь так нельзя. Текст книги
 * лежит на S3, а не в репозитории, и Liquid в момент сборки в сеть не ходит;
 * справочники — страницы .html, у которых текст спрятан в литералах
 * JavaScript, и strip_html выдал бы из них CSS и код. Поэтому указатель
 * раздела собран заранее и лежит рядом готовым файлом; основной указатель
 * называет его в shards, и едет он только к тому, кто ищет.
 *
 * Формат — общий, sitesearch/FORMAT.md. Движок не знает, что это книга.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const https = require('https');

const HERE = __dirname;
const TXT = path.join(HERE, 'theory.txt');
const TXT_URL = 'https://theatre-th.s3.amazonaws.com/ship/theory.txt';
const PDF_URL = 'https://theatre-th.s3.amazonaws.com/ship/theory.pdf';
const OUT = path.join(HERE, 'search-index.json');

function get(url) {
    return new Promise((resolve, reject) => {
        https.get(url, res => {
            if (res.statusCode !== 200) return reject(new Error(url + ' → ' + res.statusCode));
            const chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => resolve(Buffer.concat(chunks)));
        }).on('error', reject);
    });
}

// Текст книги не в репозитории — он рядом с theory.pdf и theory.djvu, а те
// лежат на S3. Качается один раз и остаётся.
async function bookText() {
    if (!fs.existsSync(TXT)) {
        process.stdout.write('качаю theory.txt… ');
        fs.writeFileSync(TXT, await get(TXT_URL));
        console.log('готово');
    }
    return fs.readFileSync(TXT, 'utf8');
}

/* Разбор текста книги.
 *
 * theory.txt — это вывод pdftotext по theory.pdf, и держится разбор на том
 * единственном, что в таком выводе есть наверняка: перевод страницы (\f) стоит
 * ровно на границе страниц PDF. Их 329, и это те самые номера, которыми
 * подписан просмотрщик, — значит, находка ведёт на ту страницу, где текст и
 * лежит.
 *
 * Соблазн взять вместо этого пометки «стр. N», которых в тексте 349, кончается
 * плохо: это набранные на полях номера страниц бумажного издания (382), и с
 * номерами PDF они не совпадают. Заодно pdftotext вставляет их прямо в поток —
 * иногда посреди слова, — и вынимать их приходится руками. Отличить пометку от
 * настоящей ссылки «(рис. 15 (стр. 20))» можно: пометка стоит в конце строки
 * или на своей собственной, ссылка — в скобках.
 *
 * Главы книга объявляет сама: номер отдельной строкой, следом название. Брать
 * их с заглавной страницы раздела нельзя — там четвёртая названа
 * «Гидродинамика яхты», а в книге она «Гидромеханика парусной яхты».
 *
 * Раздел («1.1.4», следом «Условия равновесия») едет с каждым абзацем: движок
 * ищет по нему наравне с текстом и показывает его над находкой.
 */
const MARGIN = /(?:^|\s)стр\.\s*\d+\s*$/;
const FOLIO = /^\d{1,3}$/;
const SECTION_NO = /^\d+(?:\.\d+)+$/;
const CHAPTER_NO = /^[1-9]$/;
const LEADERS = '. . .';
const CAPTION = /^(?:Рис|Табл(?:ица)?)\.? ?\d+\s*[.:]/;
const TITLE = /^[«"(]?[А-ЯЁA-Z]/;

function parseBook(raw) {
    const chapters = [];
    let front = [];                       // титул и предисловие — до первой главы
    let current = front;
    let section = null, toc = false, expect = 1;
    let buf = [], bufPage = 0, bufSection = null, hyphen = false;

    function add(text) {
        if (text.length < 25) return;
        current.push({ text: text, page: bufPage, section: bufSection });
    }

    function flush() {
        if (!buf.length) return;
        const own = buf;
        buf = [];
        // Подпись под рисунком приклеена к абзацу, который продолжается с
        // предыдущей страницы: в потоке строк они стоят подряд без пустой
        // строки между ними. Отделяется по строке, а не по числу знаков:
        // подпись занимает ровно одну строку, и это про её длину единственное,
        // что известно наверняка.
        let head = 0;
        if (own.length > 1 && CAPTION.test(own[0])) { add(own[0].trim()); head = 1; }
        const rest = own.slice(head).join('').replace(/\s+/g, ' ').trim();
        if (rest) add(rest);
    }

    // Строки склеиваются пробелом, кроме перенесённого слова: там пробела быть
    // не должно, а дефис — часть переноса, а не слова.
    function append(line) {
        if (hyphen) { buf.push(line); hyphen = false; }
        else buf.push(buf.length ? ' ' + line : line);
    }

    const pdfPages = raw.split('\f');
    pdfPages.forEach((pageText, idx) => {
        const page = idx + 1;
        const lines = pageText.split('\n');
        // Глава всегда открывает страницу — иначе одинокая цифра в середине
        // текста сойдёт за её номер, и главой станет соседняя строка.
        let atTop = true;

        for (let i = 0; i < lines.length; i++) {
            let s = lines[i].trim();
            if (!s) { flush(); continue; }

            // Пометка на полях: в конце строки или на своей собственной.
            if (/^стр\.\s*\d+$/.test(s)) continue;
            if (MARGIN.test(s)) s = s.replace(MARGIN, '').trim();
            if (!s) continue;

            if (s.includes(LEADERS)) { flush(); continue; }

            /* Оглавление выкидывается целиком: строки в нём короткие, и та их
               часть, что без точечных лидеров, иначе осела бы в указателе
               вторым, обрезанным экземпляром названий. Кончается оно на первой
               строке основного текста — то есть на первой длинной. */
            if (s === 'Содержание') { flush(); toc = true; continue; }
            if (toc) { if (s.length < 60) continue; toc = false; }

            const ahead = next(lines, i + 1);

            // Начало главы: её номер по порядку в самом верху полосы, следом
            // название.
            if (atTop && CHAPTER_NO.test(s) && +s === expect && ahead.title) {
                flush();
                expect++;
                section = null;
                current = [];
                chapters.push({ title: ahead.title, page: page, blocks: current });
                i = ahead.at;
                continue;
            }

            // Номер полосы — он же конец абзаца. Номера главы среди них уже нет.
            if (FOLIO.test(s)) { flush(); continue; }

            if (SECTION_NO.test(s) && ahead.title) {
                flush();
                atTop = false;
                section = s + ' ' + ahead.title;
                i = ahead.at;
                continue;
            }

            atTop = false;
            if (!buf.length) { bufPage = page; bufSection = section; }
            const soft = /[а-яa-z]-$/i.test(s);
            append(soft ? s.slice(0, -1) : s);
            hyphen = soft;
        }
        flush();
    });

    return { front: front, chapters: chapters };
}

// Следующая непустая строка, если она похожа на название: с заглавной, без
// точечных лидеров и не длиннее строки заголовка.
function next(lines, from) {
    for (let k = from; k < lines.length && k < from + 4; k++) {
        let t = lines[k].trim();
        if (/^стр\.\s*\d+$/.test(t)) continue;
        if (MARGIN.test(t)) t = t.replace(MARGIN, '').trim();
        if (!t) continue;
        const ok = TITLE.test(t) && !t.includes(LEADERS) && t.length < 80 && !/[.;:]$/.test(t);
        return { title: ok ? t : null, at: k };
    }
    return { title: null, at: from };
}

// Литерал массива из страницы-справочника. Это наши же файлы, и разбирать их
// разметку нечем: данные лежат в JavaScript. Берём literal по скобкам и
// исполняем — регулярным выражением такое не вынуть.
function literal(file, name) {
    const src = fs.readFileSync(path.join(HERE, file), 'utf8');
    const at = src.search(new RegExp('(?:const|var|let)\\s+' + name + '\\s*=\\s*\\['));
    if (at === -1) throw new Error(file + ': не нашёл ' + name);
    const start = src.indexOf('[', at);
    let depth = 0, end = -1, quote = null;
    for (let i = start; i < src.length; i++) {
        const c = src[i];
        if (quote) {
            if (c === '\\') i++;
            else if (c === quote) quote = null;
            continue;
        }
        if (c === '"' || c === "'" || c === '`') { quote = c; continue; }
        if (c === '[') depth++;
        else if (c === ']') { depth--; if (!depth) { end = i + 1; break; } }
    }
    if (end === -1) throw new Error(file + ': литерал ' + name + ' не закрыт');
    return new Function('return ' + src.slice(start, end))();
}

function clean(s) {
    return String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
}

function join(parts) {
    return parts.map(clean).filter(Boolean).join(' · ');
}

function build() {
    return bookText().then(raw => {
        const pages = [];

        // --- книга: глава на страницу указателя, абзац на блок ---
        const book = parseBook(raw);

        function viewer(title) {
            return '/ship/pdf-viewer.html?pdf=' + encodeURIComponent(PDF_URL) +
                '&title=' + encodeURIComponent(title);
        }
        function chapterPage(title, blocks) {
            return {
                url: viewer(title),
                title: title,
                also: 'Теория плавания под парусами',
                blocks: blocks.map(b => ({
                    text: b.text,
                    anchor: 'page=' + b.page,
                    section: b.section || undefined,
                })),
            };
        }

        pages.push(chapterPage('Предисловие', book.front));
        book.chapters.forEach((ch, i) => {
            pages.push(chapterPage('Гл. ' + (i + 1) + ' — ' + ch.title, ch.blocks));
        });

        // --- справочники ---
        const pics = literal('pictures.html', 'pics');
        pages.push({
            url: '/ship/pictures.html',
            title: 'Рисунки к книге',
            also: 'Теория плавания под парусами',
            blocks: pics.map(p => ({
                text: 'Рис. ' + p.n + '. ' + clean(p.cap),
                anchor: 'pic' + p.n,
                section: 'Глава ' + String(p.ch).replace('ch', ''),
            })),
        });

        const formulas = literal('formulas.html', 'formulas');
        pages.push({
            url: '/ship/formulas.html',
            title: 'Формулы книги',
            also: 'Теория плавания под парусами',
            blocks: formulas.map(f => ({
                text: join([f.description, f.params]),
                section: clean(f.section) || undefined,
            })),
        });

        const tables = literal('tables.html', 'tables');
        pages.push({
            url: '/ship/tables.html',
            title: 'Таблицы книги',
            also: 'Теория плавания под парусами',
            blocks: tables.map(t => ({
                // Заголовки столбцов и содержимое — одна находка на таблицу:
                // искать в ней имеет смысл слово, а ведёт находка к таблице
                // целиком, читать её по строчкам в выдаче незачем.
                text: join([t.title].concat(t.headers || [], (t.rows || []).map(r => r.join(' ')))),
                anchor: 'table-' + t.id,
                section: 'Глава ' + t.chapter,
            })),
        });

        const dict = literal('dictionary.html', 'DATA');
        pages.push({
            url: '/ship/dictionary.html',
            title: 'Словарь терминов',
            also: 'Теория плавания под парусами',
            blocks: dict.map(r => ({ text: join(r.slice(0, 3)) })),
        });

        // Сводная таблица яхт — единственный справочник, где данные лежат
        // готовой разметкой, а не литералом: строки вынимаются по ячейкам.
        const yachts = fs.readFileSync(path.join(HERE, 'yachts.html'), 'utf8');
        const heads = (/<thead>([\s\S]*?)<\/thead>/.exec(yachts) || [])[1] || '';
        const columns = (heads.match(/<th[^>]*>[\s\S]*?<\/th>/g) || [])
            .map(th => clean(th.replace(/<[^>]+>/g, ' ')));
        const rows = (yachts.match(/<tr>(?:(?!<\/tr>)[\s\S])*?<\/tr>/g) || [])
            .map(tr => (tr.match(/<td[^>]*>[\s\S]*?<\/td>/g) || [])
                .map(td => clean(td.replace(/<[^>]+>/g, ' '))))
            .filter(cells => cells.length > 2);
        pages.push({
            url: '/ship/yachts.html',
            title: 'Сводная таблица яхт',
            also: 'Теория плавания под парусами',
            blocks: rows.map(cells => ({
                // Столбец с картинкой пуст после снятия разметки; имя яхты
                // стоит первым, остальное подписано названиями столбцов —
                // иначе строка «5.05 · 4.57 · 1.88» ничего не говорит.
                text: cells.slice(1).map((c, i) => c && c !== '—'
                    ? (i === 0 ? c : columns[i + 1] + ' ' + c) : '')
                    .filter(Boolean).join(' · '),
            })),
        });

        pages.forEach(p => {
            p.blocks = p.blocks.filter(b => b.text && b.text.length >= 10);
        });

        const out = { pages: pages };
        fs.writeFileSync(OUT, JSON.stringify(out));
        const n = pages.reduce((a, p) => a + p.blocks.length, 0);
        const chars = pages.reduce((a, p) => a + p.blocks.reduce((x, b) => x + b.text.length, 0), 0);
        console.log('ship/search-index.json: ' + pages.length + ' страниц, ' + n + ' блоков, ' +
            chars.toLocaleString('ru') + ' знаков, ' + Math.round(fs.statSync(OUT).size / 1024) + ' КБ');
    });
}

build().catch(e => { console.error(e.message); process.exit(1); });
