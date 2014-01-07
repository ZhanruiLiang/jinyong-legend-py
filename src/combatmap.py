import numpy as np

import config
from scrollmap import ScrollMap
from texturenew import TextureGroup
import pyxlru
import utils

GridFields = (
    'floor', 'building', 
    # 'actor', 'movable', 'effect', 'actorTexture',
)

class CombatMap(ScrollMap):
    floorHeightI = 0
    batchData = [(1, 1)]

    def __init__(self, data):
        gridTable = np.fromstring(data, 'h').reshape(
            (len(GridFields), config.combatMapYMax, config.combatMapXMax))
        super().__init__(TextureGroup.get_group('wmap'), gridTable)


@utils.singleton
class CombatMapGroup:
    def __init__(self):
        self.idxs = np.fromfile(
            open(config.resource('data', 'warfld.idx'), 'rb'), 'L')
        self.idxs = np.hstack([self.idxs, [0]])
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
            cmap = CombatMap(self.grpData[offset:offset + self.blockByteSize])
            self._combatMaps[id] = cmap
            return cmap
