# import pylru
from collections import namedtuple
import array

import config
import utils
from scrollmap import ScrollMap
import texture

# Typecode 'h' means signed short int.
TYPE_CODE = 'h'

Grid = namedtuple('Grid', (
    'earth', 'surface', 'building', 'buildX', 'buildY',
))

@utils.singleton
class MainMap(ScrollMap):
    def __init__(self):
        self.textures = texture.TextureGroup('mmap')
        super().__init__(config.mainMapXMax, config.mainMapYMax)
        self.grids = [Grid(*x) for x in zip(*(self.load_002(f) 
            for f in ('earth', 'surface', 'building', 'buildx', 'buildy')))]

    def load_002(self, name):
        with open(config.resource('data', name + '.002'), 'rb') as file002:
            return array.array(TYPE_CODE, file002.read())

    def draw_grid(self, pos):
        grid = self.get_grid(pos, None)
        if grid is None:
            return
        if config.drawFloor:
            if grid.earth > 0:
                self.blit_texture(grid.earth, 0)
        if grid.surface > 0:
            self.blit_texture(grid.surface, 0)
        if grid.building > 0:
            self.blit_texture(grid.building, 0)

    def get_grid(self, pos, default=None):
        x, y = pos
        if not 0 <= x < self.xmax or not 0 <= y < self.ymax:
            return default
        return self.grids[y * self.xmax + x]
