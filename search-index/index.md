---
title: "Состояние поисковых указателей"
search: false
sitemap: false
noindex: true
---

# Состояние поисковых указателей

Служебная страница: на неё ниоткуда не ведут ссылки и она закрыта от поисковых
роботов. Показывает, что [поиск по сайту](/search/) и [поиск по
«Натьяшастре»](/dance/search) получают на самом деле — размер по проводу, сколько
страниц и абзацев в указателе, как он делится на разделы и что в нём выглядит
непохожим на текст.

<div id="report"></div>

<style>
/* Тема подключается удалённо и точки расширения не имеет — страница одевает
   отчёт сама, как это делает страница поиска. */
#report .index{margin:2em 0 0}
#report h2{font-size:1.1em;margin:1.6em 0 .4em}
#report h3{font-size:.95em;margin:1.4em 0 .3em;opacity:.8}
#report h4{font-size:.9em;margin:1.1em 0 .2em}
#report table{border-collapse:collapse;margin:.3em 0 .8em;font-size:.9em;width:100%}
#report td,#report th{padding:.15em .8em .15em 0;text-align:left;vertical-align:top}
#report th{font-weight:600;opacity:.7}
#report .facts td:first-child{opacity:.7;white-space:nowrap}
#report .suspect td:first-child{white-space:nowrap;opacity:.7}
#report .note,#report .why{font-size:.85em;opacity:.7;margin:.2em 0 .4em}
#report .failed{color:#f87171}
</style>

<script src="/sitesearch/status.js"></script>
<script>
/* Указателя два, и один другого не называет: поиск по сайту и поиск по
   строфам «Натьяшастры» — разные страницы с разными единицами текста. */
SiteSearchStatus.mount({
    into: 'report',
    sources: [
        { url: '/search-index.json' },
        { url: '/dance/search-index.json', section: 'Натьяшастра' },
    ],
});
</script>
