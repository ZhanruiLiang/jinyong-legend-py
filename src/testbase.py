import sys
sys.path.append('..')
from collections import OrderedDict
import threading
import functools
import time

import utils

class ExceptionHook:
    instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            from IPython.core import ultratb
            self.instance = ultratb.FormattedTB(mode='Plain',
                 color_scheme='Linux', call_pdb=1)
        return self.instance(*args, **kwargs)

sys.excepthook = ExceptionHook()

import pygame as pg

import config

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

def main():
    if len(sys.argv) == 1:
        run_all()
    else:
        run_case(*sys.argv[1:])

def run_case(name, *args):
    cases[name](*args)


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

    def press(self, key, mod, period):
        e = pg.event.Event(pg.KEYDOWN, key=key, mod=mod)
        dt = config.keyRepeatInterval / 1000
        while period >= 0 and not self._quit:
            pg.event.post(e)
            period -= dt
            time.sleep(dt)
            if not pg.display.get_init():
                self._quit = True
        pg.event.post(pg.event.Event(pg.KEYUP, key=key, mod=mod))
