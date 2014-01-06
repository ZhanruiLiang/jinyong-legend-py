from OpenGL.GL import *
import pygame as pg
import numpy as np
import itertools

import config
import utils
import glrenderhelper

ArrayBufDataType = np.float32
ArrayBufTypeEnum = GL_FLOAT

def gl_display_init(size):
    pg.display.init()
    # pg.display.set_mode(size, pg.OPENGL | pg.DOUBLEBUF, 24)
    pg.display.set_mode(size, pg.OPENGL, 24)
    utils.debug('OpenGL context:', glGetString(GL_VERSION))

    pg.display.gl_set_attribute(pg.GL_SWAP_CONTROL, 0)

    # OpenGL context created, initialize GL stuff
    glClearColor(0, .1, 0, 1)
    glEnable(GL_TEXTURE_2D)
    # glEnable(GL_DEPTH_TEST)
    # glDepthFunc(GL_LESS)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    pg.key.set_repeat(config.keyRepeatDelayTime, config.keyRepeatInterval)


def compile_shader(source, shaderType):
    """
    source: str source code
    shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER or GL_GEOMETRY_SHADER
    """
    shader = glCreateShader(shaderType)
    glShaderSource(shader, source)
    glCompileShader(shader)
    result = glGetShaderiv(shader, GL_COMPILE_STATUS)
    info = glGetShaderInfoLog(shader).decode('utf-8')
    if info:
        print('Shader compilation info:\n{}'.format(info))
    if result == GL_FALSE:
        raise Exception('GLSL compile error: {}'.format(shaderType))
    return shader


def compile_program(shaderDatas):
    program = glCreateProgram()
    for name, type in shaderDatas:
        source = open(name, 'r').read()
        glAttachShader(program, compile_shader(source, type))
    glLinkProgram(program)

    result = glGetProgramiv(program, GL_LINK_STATUS)
    info = glGetProgramInfoLog(program).decode('utf-8')
    if info:
        print('Program linking info:\n{}'.format(info))
    if result == GL_FALSE:
        raise Exception('Program compile failed')
    return program


def convert_texture(image):
    imageBytes = pg.image.tostring(image, 'RGBA')
    textureId = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textureId)
    glTexImage2D(
        GL_TEXTURE_2D, 0, 
        GL_RGBA,  # internal format
        image.get_width(), image.get_height(),
        0,  # border, must be 0
        GL_RGBA,  # input data format
        GL_UNSIGNED_BYTE,
        imageBytes,
    )
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    # Set this to avoid light and coloring affecting the texture.
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    return textureId

def getUniformLoc(program, uniform):
    if isinstance(uniform, str):
        uniform = uniform.encode('utf-8')
    loc = glGetUniformLocation(program, uniform)
    assert loc >= 0, 'Get uniform {} failed'.format(uniform)
    return loc

def getAttributeLoc(program, name):
    if isinstance(name, str):
        name = name.encode('utf-8')
    loc = glGetAttribLocation(program, name)
    assert loc >= 0, 'Get attribute {} failed'.format(name)
    return loc

def test():
    # Test rendering mmap
    import texture
    import scrollmap
    import mainmap
    # W, H = 800, 600
    # W, H = 1366, 768
    W, H = 1266, 768
    gl_display_init((W, H))

    textures = texture.PackedTextureGroup.get_group('mmap')
    pack = textures.pack
    textureId = convert_texture(pack.image)
    nSolidTextures = sum(1 for _ in textures.iter_all())
    # TODO: switch to integers
    uvData = np.zeros((nSolidTextures, 4, 2), dtype=np.int32)
    # Since uvData is a compat array without empty slots, we need to remapTable to 
    # map mp.grids[id] to uvData[i].
    remapTable = np.zeros(len(textures), dtype=np.int32)
    remapTable[:] = -1
    # offsets[remapTable[i]] = grids[i].xoff, grids[i].yoff
    offsets = np.zeros((nSolidTextures, 2), dtype=np.int32)
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

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    program = compile_program([
        ('map.v.glsl', GL_VERTEX_SHADER),
        ('map.f.glsl', GL_FRAGMENT_SHADER),
    ])
    glUseProgram(program)

    glUniform2i(getUniformLoc(program, 'screenSize'), W, H)
    glUniform2i(getUniformLoc(program, 'bigImgSize'), *pack.image.get_size())
    glUniform1i(getUniformLoc(program, 'textureSampler'), 0)

    positionLoc = getAttributeLoc(program, 'vertexPosition')
    uvLoc = getAttributeLoc(program, 'vertexUV')

    bufs = positionBuf, uvBuf = glGenBuffers(2)

    looper = scrollmap.ScrollLooper(
        (W, H), (config.textureXScale, config.textureYScale),
        10,  # bottom padding
        4,  # side padding
    )
    glrenderhelper.set_looper(looper)
    # nGrids: The number grids that will be draw on screen on each frame.
    nGrids = sum(1 for _ in looper.iter())
    positions = np.zeros((nGrids * 4, 2), dtype=ArrayBufDataType)
    # positions = (GLint * 2 * (nGrids * 4))()
    uvs = np.zeros((nGrids * 4, 2), dtype=ArrayBufDataType)
    # uvs = (GLint * 2 * (nGrids * 4))()

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

            glBindBuffer(GL_ARRAY_BUFFER, positionBuf)
            glBufferData(GL_ARRAY_BUFFER, positions, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(positionLoc, 2, ArrayBufTypeEnum, GL_FALSE, 0, None)

            glBindBuffer(GL_ARRAY_BUFFER, uvBuf)
            glBufferData(GL_ARRAY_BUFFER, uvs, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(uvLoc, 2, ArrayBufTypeEnum, GL_FALSE, 0, None)

            glDrawArrays(GL_QUADS, 0, drawN * 4)

        pg.display.flip()

    glDeleteBuffers(len(bufs), bufs)
    glDeleteProgram(program)
    glDeleteTextures([textureId])
    glDeleteVertexArrays(1, [vao])

if __name__ == '__main__':
    test()
