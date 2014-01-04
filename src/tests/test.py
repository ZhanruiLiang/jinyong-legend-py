#! /usr/bin/env python3
import sys
import time
import functools
from time import sleep
import pygame as pg
import utils
import threading
import config
from combat import CombatMapGroup
from collections import OrderedDict
sys.path.append('..')

pg.display.init()

cases = OrderedDict()

def testcase(case):

    @functools.wraps(case)
    def run_case(*args, **kwargs):
        print('-' * 80)
        print('|| Start test case [{}]'.format(case.__name__))
        startTime = time.time()
        case(*args, **kwargs)
        elapsedTime = time.time() - startTime
        print('|| Case [{}] finished in {} ms'.format(
            case.__name__, int(1000 * elapsedTime)))
        print('-' * 80)

    cases[case.__name__] = run_case
    run_case.enable = True
    return run_case

def disable(case):
    case.enable = False
    return case

def run_all():
    for case in cases.values():
        if case.enable:
            case()


class AutoController(threading.Thread):
    def __init__(self, schedule):
        """
        schedule: A list of (key, mod, time) tuples.
        """
        super().__init__()
        self.schedule = schedule
        self.daemon = True
        self._quit = False

    def run(self):
        try:
            for data in self.schedule:
                self.press(*data)
                if self._quit:
                    break
        except pg.error:
            pass
        utils.debug('controller finished.')

    def start(self):
        if self.is_alive():
            self.join()
        super().start()

    def press(self, key, mod, time):
        e = pg.event.Event(pg.KEYDOWN, key=key, mod=mod)
        dt = config.keyRepeatInterval / 1000
        while time >= 0 and not self._quit:
            pg.event.post(e)
            time -= dt
            sleep(dt)
            if not pg.display.get_init():
                self._quit = True
        pg.event.post(pg.event.Event(pg.KEYUP, key=key, mod=mod))

def get_walker():
    dt = 1.2
    return AutoController([
        (pg.K_UP, 0, dt / 2),
        (pg.K_RIGHT, 0, dt / 2),
        (pg.K_DOWN, 0, dt),
        (pg.K_LEFT, 0, dt),
        (pg.K_UP, 0, dt),
        (pg.K_ESCAPE, 0, .1),
    ])

@testcase
def save_load():
    utils.pg_init()
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
    g.enter_scene('梅莊')
    # g.enter_scene('絕情谷底')
    get_walker().start()
    g.loop()

@testcase
# @profile
def mmap():
    import game

    g = game.Game()
    g.init()
    g.load_record('1')
    g.enter_main_map()
    get_walker().start()
    g.loop()

@testcase
def cmap():
    import game

    g = game.Game()
    g.init()
    g.load_record('1')
    g.enter_combat_map(13)
    get_walker().start()
    g.loop()

@disable
@testcase
def all_cmap(start=0):
    import game

    for i in range(start, len(CombatMapGroup.get_instance())):
        g = game.Game()
        g.init()
        g.load_record('1')
        if CombatMapGroup.get_instance().get(i):
            g.enter_combat_map(i)
            g.loop()

@testcase
def extract_1():
    data = [1, 2, 3, 4, 5, 6]
    result = utils.level_extract(data, 3)
    answer = [(1, 3, 5), (2, 4, 6)]
    assert answer == result, (answer, result)

@testcase
def extract_2():
    data = [1, 2, 3, 4, 5, 6]
    result = utils.level_extract(data, 2)
    answer = [(1, 4), (2, 5), (3, 6)]
    assert answer == result, (answer, result)

@testcase
def extract_3():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = utils.level_extract(data, 2)
    answer = [(1, 6), (2, 7), (3, 8), (4, 9), (5, 10)]
    assert answer == result, (answer, result)

@testcase
def load_smap(id=70):
    import texture
    utils.pg_init()
    tg = texture.TextureGroup.get_group('smap')
    t1 = tg.get(int(id)).image
    utils.show_surface(t1)

@testcase
def load_mmap(id=0):
    import texture
    utils.pg_init()
    tg = texture.TextureGroup.get_group('mmap')
    t1 = tg.get(int(id)).image
    utils.show_surface(t1)

@testcase
def map_size():
    import texture
    utils.pg_init()
    for name in ('smap', 'mmap', 'wmap'):
        tg = texture.TextureGroup.get_group(name)
        print(name, len(tg))

@disable
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

@testcase
def packer(map_name='wmap', save_to=None):
    import texture
    import packer
    utils.pg_init()
    textures = texture.TextureGroup.get_group(map_name)
    with utils.timeit_context('Packing'):
        pack = packer.ImagePack(img.image for _, img in textures.iter_all())
    if save_to:
        pg.image.save(pack.image, save_to)
    else:
        utils.show_surface(pack.image)

@testcase
def pack_all():
    import texture
    import packer
    utils.pg_init()
    allNames = [
        'smap', 'wmap', 'mmap'
    ] + ['fight{:03d}'.format(i) for i in range(110)]
    rates = []
    for name in allNames:
        with utils.timeit_context('Load and pack ' + name):
            try:
                textures = texture.TextureGroup.get_group(name)
                pack = packer.ImagePack(img.image for _, img in textures.iter_all())
                rates.append(pack.rate)
            except FileNotFoundError:
                pack = None
                pass
        # if pack:
        #     utils.show_surface(pack.image)
    pg.quit()
    import matplotlib.pyplot as plt
    plt.hist(rates)
    plt.show()

@testcase
def load_image(name='smap.png'):
    utils.pg_init()
    with utils.timeit_context('Load image: ' + name):
        pg.image.load(name)

@testcase
def exit():
    pg.quit()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        run_all()
    else:
        cases[sys.argv[1]](*sys.argv[2:])
