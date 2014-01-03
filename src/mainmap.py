# import pylru
from collections import namedtuple
import array

import config
import utils
import fonts
from scrollmap import ScrollMap, minus
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
    def load_grid_texture(self, pos):
        grid = self.get_grid(pos)
        if grid is None:
            return None
        texture = self.merge_textures([
            # (grid.earth, 0),
            (grid.surface, 0),
            (grid.building, 0),
        ])
        # if texture and (grid.buildX or grid.buildY):
        #     f = fonts.get_default_font(8)
        #     bpos = grid.buildX, grid.buildY
        #     if texture.image.get_width() > 1 and pos != bpos:
        #         utils.debug(pos, bpos, texture.image, grid.building)
        #         texture = texture.copy()
        #         # utils.clear_surface(texture.image)
        #         texture.image.blit(
        #             f.render('{},{}'.format(*bpos), 0, (0xff, 0x0, 0x0), 
        #                 config.colorKey), 
        #             (5, 3),
        #         )
        #     else: return None
        return texture

    def get_grid(self, pos):
        x, y = pos
        if not 0 <= x < self.xmax or not 0 <= y < self.ymax:
            return None
        return self.grids[y * self.xmax + x]
