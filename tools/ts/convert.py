#!/usr/bin/env python3
"""Разбирает скачанные страницы «Тантрасары» в blocks/<id>.json."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from common.parse import convert
from parts import PARTS

if __name__ == '__main__':
    ids = sys.argv[1:] or [p[0] for p in PARTS] + ['919']
    convert(HERE, ids, prefix='ts')
