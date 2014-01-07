from OpenGL.GL import *
import numpy as np
import pygame as pg

import config
import utils
import render
import gllib
from texturenew import TextureGroup

render.init()

class MainMap(render.ScrollMap):
    def __init__(self):
        row = []
        for f in ('earth', 'surface', 'building', 'buildx', 'buildy'):
            row.append(np.fromfile(
                open(config.resource('data', f + '.002'), 'rb'),
                'h',
            ))
        data = np.array(row).T.tostring()
        super().__init__(config.mainMapXMax, config.mainMapYMax, 5, data)

    def render(self):
        self.render_map(self.currentPos, (0, 1, 2))


mp = MainMap()
textures = TextureGroup.get_group('mmap')

mp.bind_texture_group(textures)
mp.set_screen_size()

mp.move_to((200, 200))

glClearColor(0, 1, 0, 1)

@utils.pg_loop
def loop(screen, events):
    for event in events:
        if event.type == pg.KEYDOWN:
            if event.key in config.directionKeyMap:
                mp.move(config.directionKeyMap[event.key])
    mp.update()
    # render
    glClear(GL_COLOR_BUFFER_BIT)
    mp.render()
