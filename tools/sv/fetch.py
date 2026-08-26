#!/usr/bin/env python3
"""Скачивает исходную страницу Śivastotrāvalī в tools/sv/src/.

Страница одна на всё писание, и берётся она с английской стороны сайта:
русского узла у Śivastotrāvalī не заведено вовсе — `/ru/node/1005` не
открывает писания, а перекидывает на русскую главную.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from common.fetch import fetch
from parts import SRC, SRC_PAGE

if __name__ == '__main__':
    fetch(HERE, SRC, SRC_PAGE, prefix='sv')
