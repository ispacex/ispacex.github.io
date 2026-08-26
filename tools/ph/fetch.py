#!/usr/bin/env python3
"""Скачивает исходные страницы Pratyabhijñāhṛdayam в tools/ph/src/.

Страниц две, и они на разных языках — это не оплошность, а устройство задачи:

* `en543.html` — весь разбор Кшемараджи, по-английски. Ради него всё и затеяно:
  по-русски его нет нигде;
* `ru541.html` — двадцать сутр без разбора, по-русски. Перевод самих сутр
  оттуда и берётся: он у Габриэля Pradīpaka уже есть, и переводить его заново
  значило бы разойтись с ним на ровном месте.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from common.fetch import fetch
from parts import SRC, PAGE, SUTRAS, SUTRAS_PAGE

if __name__ == '__main__':
    fetch(HERE, SRC, {'543': PAGE}, prefix='en')
    fetch(HERE, SUTRAS, {'541': SUTRAS_PAGE}, prefix='ru')
