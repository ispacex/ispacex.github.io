#!/usr/bin/env python3
"""Разбирает скачанные страницы Parātrīśikāvivaraṇa в blocks/<id>.json."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from common.parse import convert
from parts import PARTS

if __name__ == '__main__':
    ids = sys.argv[1:] or ['540'] + [p[0] for p in PARTS]
    convert(HERE, ids, prefix='pv')
