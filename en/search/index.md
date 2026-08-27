---
title: "Site search"
lang: en
search: false
ru: /search/
# Написана руками, а не машиной: страница наполовину из <script>, и
# переводить в ней надо не прозу, а обещания движку. Пометку читает
# tools/check-i18n.py — та сличает перевод с исходником построчно, а здесь
# сличать нечего: это не перевод, а английская пара.
byhand: true
---

# Site search

[Back to homepage](/en/) · [Glossary of terms](/en/dance/glossary)

<p><input type="search" id="q" placeholder="for example: rasa, śaktipāta, anuttara" autocomplete="off" spellcheck="false" /></p>

<p id="status"></p>

<ul id="results"></ul>

*Searches every section at once: art, the Nāṭyaśāstra, theatre, Kashmir
Shaivism, yoga, books. Several words — the paragraphs holding all of them.
Case and diacritics do not matter, and neither does the script: «śaktipāta»,
«saktipata» and «шактипата» are one word to the search, and any of the three
finds all of it at once — the pages that spell the term in Latin and the ones
that spell it in Cyrillic.*

*This page searches the English side of the site; [the Russian
one](/search/) searches the Russian. Every finding belongs to the language you
are reading in, which is why the same query answers differently on the two
pages.*

*Two bodies of text are offered on both. The «[Tantrāloka](/en/ksh/ta/)» is
searched whole — 5,849 stanzas, all thirty-seven chapters, and a finding leads
straight to the stanza rather than to the head of a chapter: the stanzas are
Sanskrit, and there is no second copy of them to keep for English. The same goes
for «[Theory of sailing under sail](/en/ship/)» — Marchaj's book, all 382 pages,
which exists here in Russian and nowhere in English; a finding leads into the
viewer, at the page of the book. A text nobody has translated is better found in
the language it was written in than not found at all.*

*Not everything here is ours to translate. Where a Russian page is itself a
translation of somebody's English — Gabriel Pradīpaka's, mostly — the English
page carries a note and a link to his own text instead of a machine's retelling
of it.*

<style>
/* Тема подключается удалённо и точки расширения не имеет, поэтому страница
   одевает выдачу сама — теми же правилами, что и русский поиск. */
#q{padding:.45em .6em;width:100%;max-width:32em;font-size:1em}
#results{margin:1.2em 0;padding:0;list-style:none}
#results li{margin:0 0 1.2em}
#results .where{font-size:.85em;opacity:.75;margin-bottom:.15em}
#results .snippet{margin:0;padding:0}
#results mark{background:rgba(255,220,120,.35);color:inherit;padding:0 .1em;border-radius:2px}
</style>

<script src="/sitesearch/search.js"></script>
<script>
/* Тот же указатель, что у русского поиска, и та же обвязка. Язык движку не
   называется: он читает его у самой страницы (<html lang>), а она английская —
   и выдача выходит английской без единого слова здесь. */
SiteSearch.mount({
    input: 'q',
    status: 'status',
    results: 'results',
    repeats: 4,
    sources: [
        { url: '/search-index.json' },
    ],
});
</script>
