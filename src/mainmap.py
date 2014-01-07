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
