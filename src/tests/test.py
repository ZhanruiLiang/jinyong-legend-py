#! /usr/bin/env python3
import sys, os
import pygame as pg
import utils
sys.path.append('..')

pg.display.init()

cases = {}

def testcase(case):
    cases[case.__name__] = case
    return case

def run_all():
    for case in cases.values():
        case()


@testcase
def save_load():
    import record
    r = record.Record.load('1')
    r.save('9')
    r1 = record.Record.load('9')
    assert r == r1

    r = record.Record.load('anger')
    r.scenes.get(1)
    r.scenes.get(3)
    r.scenes.get(6)
    r.save('9')
    r1 = record.Record.load('9')
    assert r == r1

@testcase
def scene():
    import game

    g = game.Game()
    g.init()
    g.load_record('1')
    # g.enter_scene('梅莊')
    g.enter_scene('絕情谷底')
    g.loop()

@testcase
def mmap():
    import game

    g = game.Game()
    g.init()
    g.load_record('1')
    g.enter_main_map()
    g.loop()

@testcase
def extract_1():
    import scene
    data = [1, 2, 3, 4, 5, 6]
    result = scene.Scene._extract(data, 3)
    answer = [(1, 3, 5), (2, 4, 6)]
    assert answer == result, (answer, result)

@testcase
def extract_2():
    import scene
    data = [1, 2, 3, 4, 5, 6]
    result = scene.Scene._extract(data, 2)
    answer = [(1, 4), (2, 5), (3, 6)]
    assert answer == result, (answer, result)

@testcase
def extract_3():
    import scene
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = scene.Scene._extract(data, 2)
    answer = [(1, 6), (2, 7), (3, 8), (4, 9), (5, 10)]
    assert answer == result, (answer, result)

@testcase
def load_smap(id=70):
    import texture
    pg.display.set_mode((1, 1), 0, 32)
    tg = texture.TextureGroup('smap')
    t1 = tg.get(int(id)).image
    pg.image.save(t1, 'a.png')
    os.system('feh a.png')

@testcase
def map_size():
    import texture
    pg.display.set_mode((1, 1), 0, 32)
    for name in ('smap', 'mmap', 'wmap'):
        tg = texture.TextureGroup(name)
        print(name, len(tg))

@testcase
def mini_map():
    import game
    import mainmap

    g = game.Game()
    g.init()
    mmap = mainmap.MainMap.get_instance()
    mmap.make_minimap('/tmp/a.png')
    mmap.quit()
    g.quit()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        run_all()
    else:
        cases[sys.argv[1]](*sys.argv[2:])
