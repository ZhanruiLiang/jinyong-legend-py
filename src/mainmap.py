# import pylru
from collections import namedtuple
import array

import config
import utils
from scrollmap import ScrollMap
# from texture import PackedTextureGroup as TextureGroup
from texturenew import TextureGroup

# Typecode 'h' means signed short int.
TYPE_CODE = 'h'

Grid = namedtuple('Grid', (
    'earth', 'surface', 'building', 'buildX', 'buildY',
))

@utils.singleton
class MainMap(ScrollMap):
    def __init__(self):
        super().__init__(config.mainMapXMax, config.mainMapYMax, 
            TextureGroup.get_group('mmap'))
        grids = [Grid(*x) for x in zip(*(self.load_002(f) 
            for f in ('earth', 'surface', 'building', 'buildx', 'buildy')))]
        self.grids = grids

    def load_002(self, name):
        with open(config.resource('data', name + '.002'), 'rb') as file002:
            return array.array(TYPE_CODE, file002.read())

    # Override this for ScrollMap
    def get_floor_texture(self, pos):
        grid = self.get_grid(pos)
        if grid and grid.earth > 0:
            return self.textures.get(grid.earth)
        return None

    # Override this for ScrollMap
    # @utils.profile
    def load_grid_texture(self, pos):
        grid = self.get_grid(pos)
        if grid is None:
            return None
        return self.merge_textures([(grid.surface, 0), (grid.building, 0)])

    def get_grid(self, pos):
        x, y = pos
        if not 0 <= x < self.xmax or not 0 <= y < self.ymax:
            return None
        return self.grids[y * self.xmax + x]
