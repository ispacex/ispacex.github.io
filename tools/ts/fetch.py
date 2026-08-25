#!/usr/bin/env python3
"""Скачивает исходные страницы «Тантрасары» в tools/ts/src/."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from common.fetch import fetch
from parts import SRC, SRC_URL

if __name__ == '__main__':
    fetch(HERE, SRC, SRC_URL, prefix='ts')
