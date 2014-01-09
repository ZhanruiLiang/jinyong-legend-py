import utils
from collections import OrderedDict


def find_building_groups(grid_table):
    cdef:
        int xmax, ymax, x, y, bx, by
        short[:, :, :] gridTable = grid_table

    _, ymax, xmax = grid_table.shape
    buildings = OrderedDict()
    for y in range(ymax):
        for x in range(xmax):
            bx = gridTable[3, y, x]
            by = gridTable[4, y, x]
            if (bx > 0 or by > 0) and gridTable[2, y, x] == 0:
                try:
                    buildings[bx, by].append((x, y))
                except KeyError:
                    buildings[bx, by] = [(x, y)]
                # gridTable[2, y, x] = 14
    utils.debug('{} buildings'.format(len(buildings)))
    return buildings
