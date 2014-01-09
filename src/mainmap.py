# import pylru
import numpy as np

import config
import utils
from scrollmap import ScrollMap
from texturenew import TextureGroup
from mainmap_helper import find_building_groups

# Typecode 'h' means signed short int.
TYPE_CODE = 'h'

GridFields = (
    'earth', 'surface', 'building', 'buildX', 'buildY',
)

@utils.singleton
class MainMap(ScrollMap):
    batchData = [(1, 1), (2, 2)]
    buildingI = 2

    def __init__(self):
        rows = []
        for f in ('earth', 'surface', 'building', 'buildx', 'buildy'):
            rows.append(np.fromfile(
                open(config.resource('data', f + '.002'), 'rb'),
                'h',
            ))
        gridTable = np.vstack(rows).reshape(
            (len(GridFields), config.mainMapYMax, config.mainMapXMax)
        )
        super().__init__(TextureGroup.get_group('mmap'), gridTable)
        self.adjust_building()

    DS_FIX = {
        2356 // 2: (-2, -2),
        2490 // 2: (-1, 0),
        2374 // 2: (-1, -1),
    }
    EMPTY = (0, 5000)

    def adjust_building(self):
        gridTable = self.gridTable
        buildings = find_building_groups(gridTable)

        uvTable = self.textures.uvTable
        GX, GY = config.textureXScale, config.textureYScale

        ds = self.DS_FIX.copy()
        for (bx, by), ps in buildings.items():
            textureId = gridTable[2, by, bx] // 2
            if textureId in ds:
                continue
            w = uvTable[textureId, 2]
            dy = - int((w / (2 * GX) - .5) / 2)
            ds[textureId] = (dy, dy)

        for textureId, (dx, dy) in ds.items():
            uvTable[textureId, (4, 5)] += (dx - dy) * GX, (dx + dy) * GY

        for (bx, by) in buildings.keys():
            textureId = gridTable[2, by, bx] // 2
            dx, dy = ds[textureId]
            if dy != 0 or dx != 0:
                gridTable[2, by, bx] = 0
                x1 = bx + dx
                y1 = by + dy
                assert gridTable[2, y1, x1] == 0 or gridTable[3, y1, x1] == bx and gridTable[4, y1, x1] == by
                gridTable[2, by + dy, bx + dx] = textureId * 2

    def can_move_to(self, pos):
        if not (0 <= pos[0] < self.xmax and 0 <= pos[1] < self.ymax):
            return False
        b, bx, by = self.gridTable[(2, 3, 4), pos[1], pos[0]]
        return b == 0 and bx == 0 and by == 0

    def _dump(self):
        utils.debug('moveTick:{} staticTick:{}'.format(self._moveTick, self._staticTick))
