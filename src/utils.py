import pygame as pg
import config
import inspect
import builtins
import functools
import time
from array import array
from contextlib import contextmanager

def wait_exit():
    tm = pg.time.Clock()
    while 1:
        for event in pg.event.get():
            if event.type == pg.QUIT \
                    or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
        tm.tick(config.FPS)

def clear_surface(surface):
    surface.fill(config.colorKey)

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

_debugLogFile = open('debug.txt', 'w')

count = 0

def debug(*args, **kwargs):
    if not config.debug: 
        return 
    global count
    # frame = inspect.stack()[1]
    # modules = []
    # stacks = inspect.stack()[1:]
    # for frame in stacks:
    #     name = inspect.getmodule(frame[0]).__name__
    #     if name != '__main__':
    #         modules.append(name)
    # if not modules:
    #     modules.append('__main__')
    # modules = '->'.join(x for x in reversed(modules))

    def p():
        print('{}: [{}]:'.format(count, modules), *args, **kwargs)
    module = inspect.getmodule(inspect.stack()[1][0])
    if module:
        modules = module.__name__
    else:
        modules = ''
    p()
    kwargs['file'] = _debugLogFile
    p()
    count += 1

def step():
    tm = pg.time.Clock()
    while 1:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                yield
                break
        tm.tick(config.FPS)

def wait_key():
    while 1:
        event = pg.event.poll()
        if event.type == pg.KEYDOWN:
            return event.key

def singleton(cls):
    cls.instance = None

    def get_instance():
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance
    cls.get_instance = get_instance
    return cls

class ProgressBar:
    def __init__(self, total):
        self.total = total
        self.cnt = 0

    def update(self):
        self.cnt += 1
        if self.cnt == self.total or self.cnt % 1000 == 0:
            bar = '{:60s} '.format('|' * (60 * self.cnt // self.total))
            print('\rprogress: [{}] {}/{} ({:.2f})%'.format(
                bar, self.cnt, self.total, 100 * self.cnt / self.total), end='')

def new_surface(size):
    surface = pg.Surface(size, 0, config.depthBits)
    surface.set_colorkey(config.colorKey)
    surface.fill(config.colorKey)
    return surface

if not hasattr(builtins, 'profile'):
    profile = lambda x: x
else:
    profile = builtins.profile


def level_extract(data, n_fields):
    assert len(data) % n_fields == 0
    nItems = len(data) // n_fields
    itemDatas = [
        tuple(data[j * nItems + i] for j in range(n_fields))
        for i in range(nItems)
    ]
    return itemDatas

def level_repack(items, typecode, n_fields):
    return array(typecode, (x[j] for j in range(n_fields) for x in items))

def pg_init(size=(800, 600)):
    pg.display.init()
    pg.font.init()
    screen = pg.display.set_mode(size, 0, 32)
    return screen

def pg_loop(func):
    """
    func: (screen, events) -> quit?
    """
    if pg.display.get_surface() is None:
        screen = init_pg()
    else:
        screen = pg.display.get_surface()
    quit = False
    tm = pg.time.Clock()
    while not quit:
        events = pg.event.get()
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    pg.display.toggle_fullscreen()
        quit = func(screen, events)
        tm.tick(config.FPS)

def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        debug('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)))
    return newfunc

@contextmanager
def timeit_context(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    debug('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)))

def show_surface(surface):
    size = surface.get_size()
    W, H = 1366, 768
    scale = 1
    scale = min(1, W / size[0], H / size[1])

    if scale != 1:
        debug('image too large(size:{}), scale to rate {:.3f}'.format(size, scale))
        size = int(size[0] * scale), int(size[1] * scale)
        surface = pg.transform.scale(surface, size)
    pg_init(size)
    screen = pg.display.get_surface()
    screen.fill(0)
    screen.blit(surface, (0, 0))
    pg.display.update()

    @pg_loop
    def loop(screen, events):
        pass
