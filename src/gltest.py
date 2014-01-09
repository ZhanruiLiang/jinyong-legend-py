#! /usr/bin/env python3
from testbase import testcase, disable, AutoController, main
import config
import utils
import gllib
import pygame as pg
import pickle

@testcase
def compile():
    gllib.display_init()
    gllib.RenderProgam()

def load_state(filename):
    return pickle.load(open(filename, 'rb'))

def save_state(filename, data):
    pickle.dump(data, open(filename, 'wb'), -1)

@testcase
def mainmap(start=None):
    from mainmap import MainMap
    from scrollmap import MainCharacter, Follower, FormationManager
    from render import Render
    gllib.display_init()

    render = Render()
    STATE_FILE = '.mainmap_state.dat'

    mp = MainMap()
    mp.bind(render)
    if start:
        start = eval(start)
    else:
        try:
            data = load_state(STATE_FILE)
            start = data['start']
            orientation = data['orientation']
        except:
            start = (200, 200)
            orientation = config.Directions.left
    mainChar = MainCharacter(orientation)
    mp.add_character(mainChar, start)
    formation = FormationManager(9, mainChar)
    for i in range(60):
        char = Follower(orientation)
        formation.add(char)
        mp.add_character(char, start)

    @gllib.gl_loop
    def loop(events):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in config.directionKeyMap:
                    mp.mainChar.move(config.directionKeyMap[event.key])
                elif event.key == pg.K_j:
                    render.zoom(-.02)
                elif event.key == pg.K_k:
                    render.zoom(+.02)
                elif event.key == pg.K_p:
                    ps = [mp.currentPos]
                    for dx, dy in config.Directions.all:
                        ps.append((ps[0][0] + dx, ps[0][1] + dy))
                    for x, y in ps:
                        utils.debug((x, y), mp.gridTable[:, y, x])
        mp.update()
        formation.update()
        # render
        mp.draw()

    save_state(STATE_FILE,
        {'start': mp.mainChar.pos, 'orientation': mp.mainChar.orientation})

@testcase
def scene():
    from record import Record
    from render import Render

    gllib.display_init()

    render = Render()
    scenes = Record.load('anger').scenes
    STATE_FILE = '.scene_state.dat'

    try:
        data = load_state(STATE_FILE)
        sid = data['sid']
        center = data['center']
        orientation = data['orientation']
    except:
        sid = 0
        center = 31, 31
        orientation = config.Directions.left

    scene = None

    def switch(new_sid):
        nonlocal sid, scene
        sid = new_sid % len(scenes)
        scene = scenes.get(sid)
        scene.bind(render)
        scene.move_to((31, 31))

    switch(sid)
    scene.orientation = orientation
    scene.move_to(center)

    @gllib.gl_loop
    def loop(events):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in config.directionKeyMap:
                    scene.move(config.directionKeyMap[event.key])
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
                elif event.key == pg.K_c:
                    ps = [scene.currentPos]
                    for dx, dy in config.Directions.all:
                        ps.append((ps[0][0] + dx, ps[0][1] + dy))
                    for x, y in ps:
                        eid = scene.origGridTable[3, y, x]
                        e = scene.events[eid] if eid >= 0 else None
                        utils.debug((x, y), scene.gridTable[:, y, x], e)
        scene.update()
        scene.draw()

    save_state(STATE_FILE, 
        {'sid': sid, 'center': scene.currentPos, 'orientation': scene.orientation})

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
