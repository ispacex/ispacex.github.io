#!/usr/bin/env python3
"""Проверяет перевод Parātrīśikāvivaraṇa: подстрочник не изменил текста.

Сама проверка общая (common/check.py) — здесь только то, откуда берутся
абзацы: русский текст этого раздела лежит в ru/*.json.
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from common.check import verify


def texts():
    for path in sorted(glob.glob(os.path.join(HERE, 'ru', '*.json'))):
        name = os.path.basename(path)
        for key, v in json.load(open(path, encoding='utf-8')).items():
            yield name, key, v


if __name__ == '__main__':
    sys.exit(1 if verify(texts()) else 0)
