import pygame as pg
import os
import config

_fontCache = {}


def get_font(name, size):
    key = (name, size)
    if key not in _fontCache:
        font = pg.font.Font(os.path.join(config.fontDir, name), size)
        _fontCache[key] = font
    return _fontCache[key]
