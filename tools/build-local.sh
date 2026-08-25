#!/bin/sh
# Собирает сайт локально, в Docker, и кладёт результат в _sitecheck/.
#
# Нужно это ровно для проверки: посмотреть страницу и померить поисковый
# указатель до того, как всё уедет на Pages. Сам сайт собирает GitHub — см.
# .github/workflows/pages.yml.
#
# Тема подключена как remote_theme, и её гема в контейнере нет: `@import
# "jekyll-theme-dracula"` в assets/css/style.scss обрывает сборку. Поэтому
# stylesheet из локальной сборки исключается — на вид страницы это влияет, на
# её разметку и на указатель не влияет никак. Список исключений своё
# «exclude» не дополняет, а заменяет, поэтому конфиг собирается из основного
# плюс одна строка, а не пишется рядом вторым файлом: разойтись им негде.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
cd "$HERE"

{ cat _config.yml; echo '  - assets/css/style.scss'; } > _config-local.yml

rm -rf _sitecheck
docker run --rm -v "$HERE":/srv/jekyll -w /srv/jekyll jekyll/jekyll:4 sh -c \
	'jekyll build --config _config-local.yml -d /tmp/_site && cp -r /tmp/_site /srv/jekyll/_sitecheck'

# Указатель на Pages раскладывается на два яруса отдельным шагом; повторяем
# его здесь, иначе померенное разойдётся с тем, что получит читатель.
node sitesearch/node/two-tier.js _sitecheck /search-index.json --repeats 4
node sitesearch/node/two-tier.js _sitecheck /dance/search-index.json

echo "готово: _sitecheck/"
