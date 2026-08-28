#!/usr/bin/env python3
"""Проверка: страницу, которую видит читатель, видит и локальная сборка.

    python3 tools/check-frontmatter.py

Чисто — печатает, сколько просмотрено, и выходит нулём. Иначе показывает
страницы без front matter и выходит единицей. Сборки не требует: смотрит
исходники.

## Отчего расхождение

GitHub Pages включает `jekyll-optional-front-matter`: `.md` без YAML-шапки там
всё равно становится страницей. В контейнере (`tools/build-local.sh`,
`jekyll/jekyll:4`) этого плагина нет — гема нет, а Gemfile не трекается нарочно,
— и такой файл просто копируется как есть.

Так из локальной сборки выпали 19 страниц: весь `/nt/`, весь `/hoop/`,
четыре страницы `/art/` и `/ksh/pashas/` (VS-43). А по `_sitecheck` ходят все
проверки: они говорили «расхождений нет» о сайте, который на 19 страниц меньше
настоящего, и молчали ровно о тех страницах, где у сборщика указателя нет ни
`title`, ни `search`, ни `lang` — то есть где всё работает по умолчанию.
Сломать их незаметно было легче всего.

Чинится это со стороны страницы: front matter ей проставляется, и обе сборки
видят одно и то же. Проверка стережёт, чтобы новая страница не вернула
расхождение обратно.

## Что не страница

Два перечня, и оба не выдуманы здесь.

Первый — `exclude` из `_config.yml`: он читается оттуда, а не повторяется тут,
иначе разойдётся с ним при первой же правке.

Второй — имена, которые плагин не трогает сам: README и прочие бумаги
репозитория. Он их пропускает по имени, на любой глубине, и страницами они не
становятся: `https://ispacex.github.io/README` отвечает 404.
"""
import os
import posixpath
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Бумаги репозитория: плагин пропускает их по имени, без расширения и регистра.
PAPERS = ('readme', 'license', 'copying', 'code_of_conduct', 'contributing',
          'issue_template', 'pull_request_template', 'support')


def excluded(rel, rules):
    """Попадает ли файл под `exclude` из конфига.

    Правило — либо сам файл, либо каталог: Jekyll считает исключённым всё, что
    лежит под ним, а косая черта на конце для него необязательна.
    """
    for rule in rules:
        rule = rule.rstrip('/')
        if rel == rule or rel.startswith(rule + '/'):
            return True
    return False


def main():
    with open(os.path.join(HERE, '_config.yml'), encoding='utf-8') as fh:
        rules = yaml.safe_load(fh).get('exclude') or []

    names = subprocess.check_output(
        ['git', '-C', HERE, 'ls-files', '*.md'], text=True).split()

    bare, seen = [], 0
    for rel in names:
        if excluded(rel, rules):
            continue
        stem = posixpath.splitext(posixpath.basename(rel))[0].lower()
        if stem in PAPERS:
            continue
        seen += 1
        with open(os.path.join(HERE, rel), encoding='utf-8') as fh:
            if fh.readline().rstrip('\n') != '---':
                bare.append(rel)
                print('%s: страница без front matter' % rel)

    if bare:
        print('')
        print('на сайте они есть, в локальной сборке их нет: %d' % len(bare))
        print('лечится шапкой `---` с `title:` — как у соседних страниц')
        return 1
    print('front matter есть у всех страниц — просмотрено: %d' % seen)
    return 0


if __name__ == '__main__':
    sys.exit(main())
