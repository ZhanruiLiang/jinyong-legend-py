from OpenGL.GL import *
from OpenGL.arrays import vbo
import numpy as np
import gllib

import config
import utils

def add(a, b):
    return (a[0] + b[0], a[1] + b[1])

def minus(a, b):
    return (a[0] - b[0], a[1] - b[1])

ArrayBufTypeEnum = GL_FLOAT
ArrayBufDataType = GLfloat
IntType = GLint

def new_array(shape, type, data=None):
    if data is None:
        return np.zeros(shape, dtype=type)
    else:
        return np.array(data, dtype=type)


def init():
    global program, positionLoc, uvLoc
    gllib.display_init((config.screenWidth, config.screenHeight))

    program = gllib.Program.compile([
        ('map.v.glsl', GL_VERTEX_SHADER),
        ('map.f.glsl', GL_FRAGMENT_SHADER),
    ])
    program.use()

    positionLoc = program.get_attrib_loc('vertexPosition')
    uvLoc = program.get_attrib_loc('vertexUV')

    glEnableVertexAttribArray(positionLoc)
    glEnableVertexAttribArray(uvLoc)


class ScrollMap:
    # paddings(extra grids when render). Some objects on map is large
    # , so we need to render it's grid enter the screen.
    BOTTOM_PAD = 18
    SIDE_PAD = 4

    def __init__(self, xmax, ymax, n_levels, data):
        self.xmax = xmax
        self.ymax = ymax
        self.nLevels = n_levels
        self.uvTable = []
        self.textureUnit = gllib.GLTextureUnit(0)

        self.positions = np.zeros(1, ArrayBufDataType)
        self.positionBuf = vbo.VBO(self.positions)
        self.uvs = np.zeros(1, ArrayBufDataType)
        self.uvBuf = vbo.VBO(self.uvs)
        self.screenSize = None

        self.gridTable = np.fromstring(data, 'h').reshape((ymax, xmax, n_levels))

        self.currentPos = (0, 0)
        self.directionQueue = []

    def bind(self):
        pass

    def bind_texture_group(self, textures):
        """
        textures: A texture group
        """
        w, h = textures.size
        self.uvTable = textures.uvTable
        glUniform2i(program.get_uniform_loc('bigImgSize'), w, h)

        glActiveTexture(self.textureUnit.glenum)
        glBindTexture(GL_TEXTURE_2D, textures.textureId)
        glUniform1i(
            program.get_uniform_loc('textureSampler'), self.textureUnit.id)

    def set_screen_size(self, size=None):
        if size is None:
            size = (config.screenWidth, config.screenHeight)
        if size == self.screenSize:
            return
        cdef int kL, kR, tL, tR, k, t, rx, ry, w, h

        w, h = size
        glUniform2i(program.get_uniform_loc('screenSize'), w, h)

        rx = int(w / (2 * config.textureXScale)) + 1
        ry = int(h / (2 * config.textureYScale)) + 1
        kL, kR = (-ry, ry + self.BOTTOM_PAD + 1)
        tL, tR = (-rx - self.SIDE_PAD, rx + self.SIDE_PAD + 1)
        poses = []
        for k in range(kL, kR):
            for t in range(tL, tR):
                if (k + t) % 2 == 0:
                    poses.append(((t + k) // 2, (k - t) // 2))
        nGrids = len(poses)

        self.poses = new_array((nGrids, 2), IntType, poses)
        self.positions = new_array((nGrids * 4, 2), ArrayBufDataType)
        self.uvs = new_array((nGrids * 4, 2), ArrayBufDataType)

        self.screenSize = size

    def move_to(self, pos):
        self.currentPos = pos
        self.directionQueue.clear()

    def move(self, direction):
        if len(self.directionQueue) >= 2:
            return
        self.directionQueue.append(direction)

    def update(self):
        que = self.directionQueue
        if que:
            direction = que.pop()
            self.currentPos = add(self.currentPos, direction)

    def render_map(self, center_pos, levels):
        cdef int x, y, x1, y1, xmax, ymax, dx, dy, x0, y0, u0, v0, \
                u, v, cx, cy, uw, uh, level 
        cdef int i, j, id, nVertices
        cdef float[:, :] pview = self.positions
        cdef float[:, :] uvview = self.uvs
        cdef int[:, :] poses = self.poses
        cdef short[:, :, :] gtview = self.gridTable
        cdef int[:, :] uvTable = self.uvTable
        cdef int * Sw = [0, 1, 1, 0]
        cdef int * Sh = [0, 0, 1, 1]
        cdef int GX, GY
        GX = config.textureXScale 
        GY = config.textureYScale

        x, y = self.currentPos
        xmax, ymax = self.xmax, self.ymax
        for level in levels:
            nVertices = 0
            for i in range(len(self.poses)):
                dx = poses[i, 0]
                dy = poses[i, 1]
                x1 = x + dx
                y1 = y + dy
                id = 0
                if 0 <= x1 < xmax and 0 <= y1 < ymax:
                    id = gtview[y1, x1, level]
                if id > 0:
                    id //= 2
                if id > 0:
                    #u0, v0, uw, uh, cx, cy = uvTable[id, 0:6]
                    u0 = uvTable[id, 0]
                    v0 = uvTable[id, 1]
                    uw = uvTable[id, 2]
                    uh = uvTable[id, 3]
                    cx = uvTable[id, 4]
                    cy = uvTable[id, 5]
                    x0 = (dx - dy) * GX - u0 - cx
                    y0 = (dx + dy) * GY - v0 - cy
                    for j in range(4):
                        u = u0 + Sw[j] * uw
                        v = v0 + Sh[j] * uh
                        uvview[nVertices + j, 0] = u
                        uvview[nVertices + j, 1] = v
                        pview[nVertices + j, 0] = x0 + u
                        pview[nVertices + j, 1] = y0 + v
                    nVertices += 4
            self.positionBuf.set_array(self.positions)
            self.positionBuf.bind()
            glVertexAttribPointer(
                positionLoc, 2, ArrayBufTypeEnum, GL_FALSE, 0, None)
            self.uvBuf.set_array(self.uvs)
            self.uvBuf.bind()
            glVertexAttribPointer(
                uvLoc, 2, ArrayBufTypeEnum, GL_FALSE, 0, None)

            glDrawArrays(GL_QUADS, 0, nVertices)

    def render_items(self, center_pos):
        pass

    def render(self):
        pass

    def blit_texture(self, id, screen_pos):
        pass

