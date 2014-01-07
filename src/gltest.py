#! /usr/bin/env python3
from testbase import testcase, disable, AutoController, main
import config
import utils
import gllib
import pygame as pg

@testcase
def compile():
    gllib.display_init()
    gllib.RenderProgam()

@testcase
def mainmap():
    from mainmap import MainMap
    from render import Render
    gllib.display_init()

    render = Render()

    mp = MainMap()
    mp.bind(render)
    mp.move_to((300, 300))

    @gllib.gl_loop
    def loop(events):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in config.directionKeyMap:
                    mp.move(config.directionKeyMap[event.key])
                elif event.key == pg.K_j:
                    render.zoom(-.02)
                elif event.key == pg.K_k:
                    render.zoom(+.02)
        mp.update()
        # render
        mp.draw()

@testcase
def scene():
    from record import Record
    from render import Render

    gllib.display_init()

    render = Render()
    scenes = Record.load('anger').scenes

    sid = 0
    center = 31, 31

    scene = scenes.get(sid)
    scene.bind(render)
    scene.move_to(center)

    @gllib.gl_loop
    def loop(events):
        nonlocal scene, sid
        switch = False
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in config.directionKeyMap:
                    scene.move(config.directionKeyMap[event.key])
                if event.key == pg.K_n:
                    # next
                    sid += 1
                    switch = True
                elif event.key == pg.K_p:
                    # prev
                    sid -= 1
                    switch = True
                elif event.key == pg.K_j:
                    render.zoom(-.02)
                elif event.key == pg.K_k:
                    render.zoom(+.02)
        if switch:
            sid %= 80
            scene = scenes.get(sid)
            scene.bind(render)
            scene.move_to(center)
        scene.update()
        scene.draw()

@testcase
def cmap():
    from render import Render
    from combatmap import CombatMapGroup

    gllib.display_init()

    render = Render()
    manager = CombatMapGroup.get_instance()

    sid = 0
    center = 31, 31
    mp = None

    def switch(new_sid):
        nonlocal sid, mp
        sid = new_sid % len(manager)
        mp = manager.get(sid)
        mp.bind(render)
        mp.move_to(center)
    switch(0)

    @gllib.gl_loop
    def loop(events):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in config.directionKeyMap:
                    mp.move(config.directionKeyMap[event.key])
                if event.key == pg.K_n:
                    # next
                    switch(sid + 1)
                elif event.key == pg.K_p:
                    # prev
                    switch(sid - 1)
                elif event.key == pg.K_j:
                    render.zoom(-.02)
                elif event.key == pg.K_k:
                    render.zoom(+.02)
        mp.update()
        mp.draw()

if __name__ == '__main__':
    main()
