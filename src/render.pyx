# Cython: profile=True
from OpenGL.GL import *
from OpenGL.arrays import vbo
import numpy as np
import gllib
from contextlib import contextmanager

import config
import utils

cdef int * Sw = [0, 1, 1, 0]
cdef int * Sh = [0, 0, 1, 1]
cdef int GX = config.textureXScale 
cdef int GY = config.textureYScale

def new_array(shape, type, data=None):
    if data is None:
        return np.zeros(shape, dtype=type)
    else:
        return np.array(data, dtype=type)

class Render:
    # paddings(extra grids when render). Some objects on map is large
    # , so we need to render it's grid enter the screen.
    BOTTOM_PAD = 18
    SIDE_PAD = 4
    MIN_ZOOM = .1
    MAX_ZOOM = 20.
    MAX_GRIDS = 6000
    MAX_BATCH = 5

    def __init__(self):
        self.currentPos = (0, 0)
        self.screenSize = None
        self.program = gllib.RenderProgam()
        self.program.use()
        self.gridTable = None
        self.uvTable = None
        self._ready = False
        self.zoomRate = 1.
        self.program.zoom_to(self.zoomRate)
        self.poses = np.zeros((self.MAX_GRIDS, 2), 'i')

    def is_ready(self):
        return self.gridTable is not None and self.uvTable is not None

    def set_grid_table(self, grid_table):
        """
        grid_table: A numpy array with shape (xmax, ymax, nLevels).
        """
        self.gridTable = grid_table
        utils.debug("attach grid table, shape {}.".format(grid_table.shape))

    def set_texture_group(self, textures):
        """
        textures: A  TextureGroup instance
        """
        w, h = textures.size
        self.uvTable = textures.uvTable
        self.program.set_texture(textures.textureId)
        utils.debug("Attach texture group, shape {}.".format(self.uvTable.shape))

    def set_pos(self, pos):
        self.currentPos = pos

    def set_screen_size(self, size=None):
        """
        rebuild self.poses, self.positions, self.uvs
        """
        if size is None: size = (config.screenWidth, config.screenHeight)
        if size == self.screenSize:
            return
        utils.debug("configure render by screen size {}".format(size))
        cdef int kL, kR, tL, tR, k, t, rx, ry, w, h

        w, h = size
        self.program.set_screen_size(size)

        rx = int(w / (2 * config.textureXScale)) + 1
        ry = int(h / (2 * config.textureYScale)) + 1
        kL, kR = (-ry, ry + self.BOTTOM_PAD + 1)
        tL, tR = (-rx - self.SIDE_PAD, rx + self.SIDE_PAD + 1)

        cdef int i = 0
        cdef int[:, :] poses = self.poses
        cdef int maxi = self.MAX_GRIDS
        for k in range(kL, kR):
            for t in range(tL, tR):
                if (k + t) % 2 == 0:
                    poses[i, 0] = (t + k) // 2
                    poses[i, 1] = (k - t) // 2
                    i += 1
                    if i >= maxi:
                        break
            if i >= maxi:
                utils.debug('warning: MAX_GRIDS({}) reached'.format())
                break
        self.nPoses = nPoses = i

        self.positions = new_array((nPoses * self.MAX_BATCH * 4, 2), GLfloat)
        self.uvs = new_array((self.MAX_BATCH * nPoses * 4, 2), GLfloat)

        self.screenSize = size

    def zoom(self, delta_rate):
        r = self.zoomRate = np.clip(self.zoomRate + delta_rate, 
            self.MIN_ZOOM, self.MAX_ZOOM)
        self.program.zoom_to(r)
        w, h = self.screenSize
        self.set_screen_size((w / r, h / r))
        self.screenSize = w, h

    def batch_draw(self, lhs):
        """
        lhs: [(levelField, heightField)]
        """
        assert self.is_ready()
        if self.screenSize is None:
            self.set_screen_size()

        self.program.use()

        cdef int x, y, height, x1, y1, xmax, ymax, dx, dy, x0, y0, u0, v0, \
                u, v, cx, cy, uw, uh, level, maxUVID, heightI 
        cdef int i, j, k, id, nVertices
        cdef float[:, :] pview = self.positions
        cdef float[:, :] uvview = self.uvs
        cdef int[:, :] poses = self.poses
        cdef short[:, :, :] gtview = self.gridTable
        cdef int[:, :] uvTable = self.uvTable
        
        cdef int[:, :] lhsview = np.array(lhs)
        cdef int nLhs = len(lhs)
        cdef int nPoses = self.nPoses

        x, y = self.currentPos
        nLevels, ymax, xmax = self.gridTable.shape
        maxUVID = self.uvTable.shape[0]
        nVertices = 0
        for i in range(nPoses):
            dx = poses[i, 0]
            dy = poses[i, 1]
            x1 = x + dx
            y1 = y + dy
            if not (0 <= x1 < xmax and 0 <= y1 < ymax):
                continue
            for k in range(nLhs):
                level = lhsview[k, 0]
                id = gtview[level, y1, x1]
                if not (0 < id < maxUVID * 2):
                    continue
                id //= 2
                heightI = lhsview[k, 1]
                if heightI != level:
                    height = gtview[heightI, y1, x1]
                else:
                    height = 0
                #u0, v0, uw, uh, cx, cy = uvTable[id, 0:6]
                u0 = uvTable[id, 0]
                v0 = uvTable[id, 1]
                uw = uvTable[id, 2]
                uh = uvTable[id, 3]
                x0 = (dx - dy) * GX - u0 - uvTable[id, 4]
                y0 = (dx + dy) * GY - v0 - uvTable[id, 5] + height
                for j in range(4):
                    u = u0 + Sw[j] * uw
                    v = v0 + Sh[j] * uh
                    uvview[nVertices + j, 0] = u
                    uvview[nVertices + j, 1] = v
                    pview[nVertices + j, 0] = x0 + u
                    pview[nVertices + j, 1] = y0 + v
                nVertices += 4
        self.flush(nVertices)

    def flush(self, nVertices):
        self.program.set_positions(self.positions)
        self.program.set_uvs(self.uvs)
        self.program.draw(nVertices)

    @contextmanager
    def single_draw_mode(self):
        self._toDraw = 0
        yield

        cdef int x, y, x1, y1, dx, dy, u0, v0, x0, y0, i, j, u, v, uw, uh, id, height
        cdef int[:, :] uvTable = self.uvTable
        cdef float[:, :] pview = self.positions
        cdef float[:, :] uvview = self.uvs
        x, y = self.currentPos
        i = 0
        for (id, x1, y1, height) in self._toDraw:
            dx = x1 - x
            dy = y1 - y
            #u0, v0, uw, uh, cx, cy = uvTable[id, 0:6]
            u0 = uvTable[id, 0]; v0 = uvTable[id, 1]
            uw = uvTable[id, 2]; uh = uvTable[id, 3]
            x0 = (dx - dy) * GX - u0 - uvTable[id, 4]
            y0 = (dx + dy) * GY - v0 - uvTable[id, 5] + height
            for j in range(4):
                u = u0 + Sw[j] * uw
                v = v0 + Sh[j] * uh
                uvview[i + j, 0] = u
                uvview[i + j, 1] = v
                pview[i + j, 0] = x0 + u
                pview[i + j, 1] = y0 + v
            i += 4
        self.flush(i)
        del self._toDraw

    def blit_texture(self, id, pos, height):
        self._toDraw.append((id, pos[0], pos[1], height))
