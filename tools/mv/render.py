#!/usr/bin/env python3
"""Собирает страницы ksh/mv/ из разобранных блоков и русских переводов.

Сама сборка общая (common/page.py) — здесь только то, что относится к
Mālinīvijayottaratantra: см. book.py. `markup` вынесен наружу для check.py,
который проверяет, что подстрочник не изменил текста абзаца.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import main, markup   # noqa: F401 — markup нужен check.py
from book import MV

if __name__ == '__main__':
    main(MV(), sys.argv[1:])
