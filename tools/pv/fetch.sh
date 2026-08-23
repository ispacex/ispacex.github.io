#!/bin/sh
# Забирает исходные страницы Parātrīśikāvivaraṇa с sanskrit-trikashaivism.com
# в tools/pv/src/. Уже скачанное не перекачивается — сайт чужой, дёргать его
# лишний раз незачем.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HERE/src"

UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
BASE='https://www.sanskrit-trikashaivism.com/ru/'

python3 - "$HERE" <<'PY' | while IFS='	' read -r id url; do
import sys, os
sys.path.insert(0, sys.argv[1])
from parts import SRC_URL
for pid, path in SRC_URL.items():
    print('%s\t%s' % (pid, path))
PY
	out="$HERE/src/pv$id.html"
	if [ -f "$out" ]; then
		echo "$id — уже есть"
		continue
	fi
	enc=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe="/"))' "$url")
	echo "$id — качаю"
	curl -sSfL --compressed -A "$UA" -o "$out" "$BASE$enc"
	sleep 1
done
