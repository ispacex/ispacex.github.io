#!/usr/bin/env python3
"""Скачивает исходные страницы Mālinīvijayottaratantra в tools/mv/src/.

Страниц двадцать четыре: двадцать три главы и вступление переводчика к
писанию. Все они английские — русского узла у этого писания нет вовсе (VS-5).
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.fetch import fetch
from parts import SRC, SRC_URL, NODES

if __name__ == '__main__':
    fetch(HERE, SRC, {node: SRC_URL[pid] for pid, node in NODES.items()},
          prefix='en')
