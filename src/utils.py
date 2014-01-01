import pygame as pg
import config
import inspect

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

_debugLogFile = open('debug.txt', 'w')

count = 0

def debug(*args, **kwargs):
    if not config.debug: 
        return 
    global count
    frame = inspect.stack()[1]
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
    modules = inspect.getmodule(inspect.stack()[1][0]).__name__
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
