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
