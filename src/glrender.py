from OpenGL.GL import *
from OpenGL.arrays import vbo
import pygame as pg
import numpy as np

import config
import utils
import glrenderhelper
import gllib

ArrayBufTypeEnum = GL_FLOAT
ArrayBufDataType = np.float32
IntType = np.int32

def new_array(shape, type, data=None):
    if data is None:
        return np.zeros(shape, dtype=type)
    else:
        return np.array(data, dtype=type)

# ArrayBufDataType = GLfloat
# IntType = GLint
# 
# def new_array(shape, type, data=None):
#     T = type
#     for n in reversed(shape):
#         T = T * n
#     print(T)
#     if data is None:
#         return T()
#     else:
#         return T(*data)
# 
def test():
    # Test rendering mmap
    import texture
    import scrollmap
    import mainmap
    W, H = 800, 600
    # W, H = 1366, 768
    # W, H = 1024, 768
    gllib.display_init((W, H))

    textures = texture.PackedTextureGroup.get_group('mmap')
    pack = textures.pack
    textureId = gllib.convert_texture(pack.image)
    nSolidTextures = sum(1 for _ in textures.iter_all())
    uvData = new_array((nSolidTextures, 4, 2), IntType)
    # Since uvData is a compat array without empty slots, we need to remapTable to 
    # map mp.grids[id] to uvData[i].
    remapTable = new_array((len(textures),), IntType)
    # offsets[remapTable[i]] = grids[i].xoff, grids[i].yoff
    offsets = new_array((nSolidTextures, 2), IntType)
    i = 0
    for id, t in textures.iter_all():
        remapTable[id] = i
        w1, h1 = t.image.get_size()
        x1, y1 = pack.poses[i]
        uvData[i] = (
            (x1, y1),
            (x1 + w1, y1),
            (x1 + w1, y1 + h1),
            (x1, y1 + h1),
        )
        offsets[i] = t.xoff, t.yoff
        i += 1

    program = gllib.Program.compile([
        ('map.v.glsl', GL_VERTEX_SHADER),
        ('map.f.glsl', GL_FRAGMENT_SHADER),
    ])
    program.use()

    glUniform2i(program.get_uniform_loc('screenSize'), W, H)
    glUniform2i(program.get_uniform_loc('bigImgSize'), *pack.image.get_size())
    glUniform1i(program.get_uniform_loc('textureSampler'), 0)

    positionLoc = program.get_attrib_loc('vertexPosition')
    uvLoc = program.get_attrib_loc('vertexUV')

    looper = scrollmap.ScrollLooper(
        (W, H), (config.textureXScale, config.textureYScale),
        10,  # bottom padding
        4,  # side padding
    )
    glrenderhelper.set_looper(looper)
    # nGrids: The number grids that will be draw on screen on each frame.
    nGrids = sum(1 for _ in looper.iter())
    positions = new_array((nGrids * 4, 2), ArrayBufDataType)
    uvs = new_array((nGrids * 4, 2), ArrayBufDataType)

    # bufs = positionBuf, uvBuf = glGenBuffers(2)
    positionBuf = vbo.VBO(positions)
    uvBuf = vbo.VBO(uvs)

    mp = mainmap.MainMap.get_instance()

    # Use texture unit 0
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, textureId)

    glEnableVertexAttribArray(positionLoc)
    glEnableVertexAttribArray(uvLoc)

    currentPos = 200, 200

    mapSize = mp.xmax, mp.ymax
    glrenderhelper.load_grid_table(mp)
    glrenderhelper.load_uvdata(uvData, offsets, remapTable)

    @utils.pg_loop
    @utils.profile
    def loop(screen, events):
        nonlocal currentPos
        currentX, currentY = currentPos
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    currentX -= 1
                elif event.key == pg.K_RIGHT:
                    currentX += 1
                elif event.key == pg.K_UP:
                    currentY -= 1
                elif event.key == pg.K_DOWN:
                    currentY += 1
                break
        currentPos = currentX, currentY

        glClear(GL_COLOR_BUFFER_BIT)

        for level in range(3):
            # with utils.timeit_context('make buffer'):
            drawN = glrenderhelper.make_buffer(
                positions, uvs, currentPos, mapSize, level)

            positionBuf.set_array(positions)
            positionBuf.bind()
            # glBindBuffer(GL_ARRAY_BUFFER, positionBuf)
            # glBufferData(GL_ARRAY_BUFFER, positions, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(positionLoc, 2, ArrayBufTypeEnum, GL_FALSE, 0, None)

            # glBindBuffer(GL_ARRAY_BUFFER, uvBuf)
            # glBufferData(GL_ARRAY_BUFFER, uvs, GL_DYNAMIC_DRAW)
            uvBuf.set_array(uvs)
            uvBuf.bind()
            glVertexAttribPointer(uvLoc, 2, ArrayBufTypeEnum, GL_FALSE, 0, None)

            glDrawArrays(GL_QUADS, 0, drawN * 4)

        pg.display.flip()

    glDeleteTextures([textureId])
    program.delete()
    gllib.quit()

if __name__ == '__main__':
    test()
