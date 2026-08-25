#!/usr/bin/env python3
"""Собирает страницы ksh/tantrasara/ из разобранных блоков.

Сама сборка общая (common/page.py) — здесь только то, что относится к
«Тантрасаре»: см. book.py.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.page import main
from book import TS

if __name__ == '__main__':
    main(TS(), sys.argv[1:])
