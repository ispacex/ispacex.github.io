---
title: "Натьяшастра: поиск"
search: false
---

# Поиск по «Натьяшастре»

[Оглавление](/dance) · [Словарь терминов](/dance/glossary) · [Вернуться на главную](/)

<p><input type="search" id="q" placeholder="например: раса, хаста, пурваранга" autocomplete="off" /></p>

<p id="status"></p>

<ul id="results"></ul>

*Ищет по строфам всех переведённых глав: совпадение ведёт прямо к строфе, а не
в начало главы. Диакритика необязательна — «srngara» найдёт śṛṅgāra.*

<style>
#q{padding:.4em .6em;width:100%;max-width:30em;font-size:1em}
#results{margin:1.2em 0;padding:0;list-style:none}
#results li{margin:0 0 1.1em}
#results .where{font-size:.85em;opacity:.75;margin-bottom:.15em}
#results .snippet{margin:0;padding:0}
#results mark{background:rgba(255,220,120,.35);color:inherit;padding:0 .1em;border-radius:2px}
</style>

<script src="/sitesearch/search.js"></script>
<script>
/* Тот же движок, что и у поиска по сайту, только указатель другой: строфы
   вместо абзацев и раздел у всех находок общий, поэтому над находкой он не
   повторяется. */
SiteSearch.mount({
    input: 'q',
    status: 'status',
    results: 'results',
    showSection: false,
    sources: [
        { url: '/dance/search-index.json' },
    ],
});
</script>
<script src="/dance/chapter.js"></script>
