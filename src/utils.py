import pygame as pg
import config

def wait_exit():
    tm = pg.time.Clock()
    while 1:
        for event in pg.event.get():
            if event.type == pg.QUIT \
                    or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
        tm.tick(config.FPS)

def clear_surface(surface):
    surface.fill((0, 0, 0, 0))

NAMES = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
def number_to_chinese(x):
    assert x < 100
    a1, a0 = x // 10, x % 10
    if a1 == 0:
        return NAMES[a0]
    else:
        return NAMES[a1] + NAMES[10] + NAMES[a0]

def diff(a):
    n = len(a)
    b = list(a)
    for i in range(n - 1):
        b[i + 1] = a[i + 1] - a[i]
    return b
