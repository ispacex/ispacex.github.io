---
title: "Поиск по сайту"
search: false
---

# Поиск по сайту

[Вернуться на главную](/) · [Поиск по строфам «Натьяшастры»](/dance/search) · [Словарь терминов](/dance/glossary)

<p><input type="search" id="q" placeholder="например: раса, шактипата, anuttara, остойчивость" autocomplete="off" spellcheck="false" /></p>

<p id="status"></p>

<ul id="results"></ul>

*Ищет по всем разделам сразу: искусство, Натьяшастра, театр, кашмирский шиваизм,
йога, книги, «Теория плавания под парусами». Несколько слов — найдутся абзацы,
где есть все они. Регистр, «ё» и диакритика не важны: «srngara» найдёт śṛṅgāra,
«paratrishika» — Parātrīśikā. Окончание тоже можно не угадывать — «индрии»
найдёт «индрий».*

*По строфам «Натьяшастры» есть [отдельный поиск](/dance/search): он ведёт прямо
к строфе, а не к началу главы.*

<style>
/* Тема подключается удалённо и точки расширения не имеет, поэтому страница
   одевает выдачу сама. Движок ставит <li> с .where и .snippet внутри и
   подсвечивает найденное через <mark>; как это выглядит — дело сайта. */
#q{padding:.45em .6em;width:100%;max-width:32em;font-size:1em}
#results{margin:1.2em 0;padding:0;list-style:none}
#results li{margin:0 0 1.2em}
#results .where{font-size:.85em;opacity:.75;margin-bottom:.15em}
#results .snippet{margin:0;padding:0}
#results mark{background:rgba(255,220,120,.35);color:inherit;padding:0 .1em;border-radius:2px}
</style>

<script src="/sitesearch/search.js"></script>
<script>
SiteSearch.mount({
    input: 'q',
    status: 'status',
    results: 'results',
    /* Обвязку разделов — врезку «как читать эти страницы», одно и то же
       оглавление — сборщику на Liquid от текста не отличить: ни регулярных
       выражений, ни счёта повторов там нет. Считает движок. */
    repeats: 4,
    sources: [
        { url: '/search-index.json' },
    ],
});
</script>
