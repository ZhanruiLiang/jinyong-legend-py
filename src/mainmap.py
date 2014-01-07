# import pylru
import numpy as np

import config
import utils
from scrollmap import ScrollMap
from texturenew import TextureGroup

# Typecode 'h' means signed short int.
TYPE_CODE = 'h'

GridFields = (
    'earth', 'surface', 'building', 'buildX', 'buildY',
)

@utils.singleton
class MainMap(ScrollMap):
    batchData = [(1, 1), (2, 2)]
    WALK_TEXTURE_ID0 = 2501
    BOAT_TEXTURE_ID0 = 3715
    WALK_TICK_PERIOD = 6
    COOL_DOWN_PERIOD = 5

    def __init__(self):
        rows = []
        for f in ('earth', 'surface', 'building', 'buildx', 'buildy'):
            rows.append(np.fromfile(
                open(config.resource('data', f + '.002'), 'rb'),
                'h',
            ))
        data = np.vstack(rows).reshape(
            (len(GridFields), config.mainMapYMax, config.mainMapXMax)
        )
        super().__init__(TextureGroup.get_group('mmap'), data)

        self._moveTick = 0
        self._tickPeriod = self.WALK_TICK_PERIOD
        self._staticTick = self.COOL_DOWN_PERIOD

    def can_move_to(self, pos):
        b, bx, by = self.gridTable[(2, 3, 4), pos[1], pos[0]]
        return b == 0 and bx == 0 and by == 0

    def update(self):
        super().update()

    def on_move(self, pos, direction):
        self._moveTick = 1 + self._moveTick % self._tickPeriod
        self._staticTick = 0
        x, y = pos
        dx, dy = direction
        self.gridTable[2, y, x] = self.cal_texture_id() * 2
        self.gridTable[2, y - dy, x - dx] = 0

    def on_pause(self, pos):
        if self._staticTick > self.COOL_DOWN_PERIOD:
            return
        if self._staticTick == self.COOL_DOWN_PERIOD:
            self._moveTick = 0
            x, y = pos
            self.gridTable[2, y, x] = self.cal_texture_id() * 2
            return
        self._staticTick += 1

    def cal_texture_id(self):
        di = config.Directions.all.index(self.orientation)
        return self.WALK_TEXTURE_ID0 + di * 7 + self._moveTick

    def _dump(self):
        utils.debug('moveTick:{} staticTick:{}'.format(self._moveTick, self._staticTick))
