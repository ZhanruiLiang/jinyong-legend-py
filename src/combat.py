import array
from collections import namedtuple

import config
from scrollmap import ScrollMap
# from texture import PackedTextureGroup as TextureGroup
from texturenew import TextureGroup
import pyxlru
import utils

Grid = namedtuple('Grid', (
    'floor', 'building', 
    # 'actor', 'movable', 'effect', 'actorTexture',
))
GRID_FIELD_NUM = 2


class CombatMap(ScrollMap):
    def __init__(self, data):
        super().__init__(
            config.combatMapXMax, config.combatMapYMax, 2,
            TextureGroup.get_group('wmap'),
        )
        grids = utils.level_extract(data, GRID_FIELD_NUM)
        self.grids = {
            (x, y): Grid(*grids[y * config.combatMapXMax + x])
            for y in range(config.combatMapYMax) for x in range(config.combatMapXMax)
        }

    # Override load_grid_texture and get_floor_texture to support ScrollMap
    def load_grid_texture(self, pos):
        try:
            grid = self.grids[pos]
            toMerge = [(grid.floor // 2, 0), (grid.building // 2, 0)]
            return self.merge_textures(toMerge)
        except KeyError:
            return None

    def get_floor_texture(self, pos):
        try:
            grid = self.grids[pos]
        except KeyError:
            return None
        return self.textures.get(grid.floor // 2)


@utils.singleton
class CombatMapGroup:
    def __init__(self):
        CombatMapGroup.textures = TextureGroup.get_group('wmap')
        self.idxs = array.array('L',
            open(config.resource('data', 'warfld.idx'), 'rb').read())
        self.idxs.append(0)
        # utils.debug('idxs:', self.idxs)
        # utils.debug('idxs diff:', utils.diff(self.idxs))
        # utils.debug('idxs len:', len(self.idxs) - 1)
        self.grpData = open(config.resource('data', 'warfld.grp'), 'rb').read()
        self._combatMaps = pyxlru.lru(config.combatMapCacheNum)
        self.blockByteSize = config.combatMapXMax * config.combatMapYMax * 2 * 2

    def __len__(self):
        return len(self.idxs) - 1

    def get(self, id):
        try:
            return self._combatMaps[id]
        except KeyError:
            offset = self.idxs[id - 1]
            data = array.array('h', self.grpData[offset:offset + self.blockByteSize])
            cmap = CombatMap(data)
            self._combatMaps[id] = cmap
            return cmap
