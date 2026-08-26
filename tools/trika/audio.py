#!/usr/bin/env python3
"""Озвучивает термины словаря /ksh/ta/ — общим скриптом `tools/common/audio.py`.

    python3 audio.py            # сделать недостающие
    python3 audio.py --force    # переснять всё
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from common.audio import main

ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'ksh', 'ta'))

if __name__ == '__main__':
    main(os.path.join(ROOT, 'glossary', 'index.md'), os.path.join(ROOT, 'audio'))
