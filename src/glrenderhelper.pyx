import utils
import numpy as np
import config
import cython

cdef int GX, GY
GX, GY = config.textureXScale, config.textureYScale

cdef int[:, :, :] uvData
cdef int[:, :] offsetData
cdef int[:] remapTable

cdef int[:, :, :] gridTable

cdef int nPoses
cdef int[:, :] poses

def load_grid_table(scrollmap):
    global gridTable
    gt = np.zeros((scrollmap.xmax, scrollmap.ymax, scrollmap.nLevels), 
            dtype=np.int32)
    gridTable = gt
    cdef int xmax, ymax, x, y, d

    xmax, ymax, nLevels = gt.shape
    for y in range(ymax):
        for x in range(xmax):
            grid = scrollmap.get_grid((x, y))
            for d in range(nLevels):
                gridTable[x, y, d] = grid[d] 

def load_uvdata(newUvData, newOffsetData, newRemapTable):
    global uvData, remapTable, offsetData
    uvData = newUvData
    remapTable = newRemapTable
    offsetData = newOffsetData

def set_looper(looper):
    global nPoses, poses
    ps = np.array(looper.iter())
    nPoses = len(ps)
    poses = ps

def make_buffer(positions, uvs, currentPos, mapSize, int level):
    """
    Write to dest.
    return: n, the number of grids that has been pushed at this call.
    """
    cdef int x, y, x1, y1, xmax, ymax, dx, dy, x0, y0, u0, v0, u, v
    cdef int i, j, id, nGrids
    cdef float[:, :] pview = positions
    cdef float[:, :] uvview = uvs

    x, y = currentPos
    xmax, ymax = mapSize
    nGrids = 0
    for i in range(nPoses):
        dx = poses[i, 0]
        dy = poses[i, 1]
        x1 = x + dx
        y1 = y + dy
        id = 0
        if 0 <= x1 < xmax and 0 <= y1 < ymax:
            id = gridTable[x1][y1][level]
        if id > 0:
            id = remapTable[id // 2]
        if id > 0:
            u0 = uvData[id, 0, 0]
            v0 = uvData[id, 0, 1]
            x0 = (dx - dy) * GX - u0 - offsetData[id][0]
            y0 = (dx + dy) * GY - v0 - offsetData[id][1]
            for j in range(4):
                u = uvData[id, j, 0]
                v = uvData[id, j, 1]
                uvview[nGrids * 4 + j, 0] = u
                uvview[nGrids * 4 + j, 1] = v
                pview[nGrids * 4 + j, 0] = x0 + u
                pview[nGrids * 4 + j, 1] = y0 + v

            nGrids += 1
    return nGrids
