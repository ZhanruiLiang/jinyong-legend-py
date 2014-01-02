import pygame as pg
import config

_fontCache = {}

class Font(pg.font.Font):
    def render(self, text, aa, color, background=None):
        r, g, b = color[:3]
        k = .5
        shadowColor = int(r * k), int(g * k), int(b * k)
        surface1 = super().render(text, aa, shadowColor, background)
        surface1 = surface1.convert()
        surface2 = super().render(text, aa, color, background)
        surface1.blit(surface2, (-1, -1))
        return surface1

def get_font(name, size):
    key = (name, size)
    if key not in _fontCache:
        font = Font(config.resource('font', name), size)
        _fontCache[key] = font
    return _fontCache[key]

def get_default_font(size=config.defaultFontSize):
    return get_font(config.defaultFont, size)
