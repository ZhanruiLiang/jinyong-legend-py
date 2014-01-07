import OpenGL.GL as gl
from OpenGL.arrays import vbo
import pygame as pg
import numpy as np

import config
import utils

vao = None

def display_init(size=config.screenSize):
    pg.display.init()
    pg.display.set_mode(size, pg.OPENGL | pg.DOUBLEBUF, 24)
    utils.debug('OpenGL context:', gl.glGetString(gl.GL_VERSION))

    pg.display.gl_set_attribute(pg.GL_SWAP_CONTROL, 1)

    # OpenGL context created, initialize GL stuff
    gl.glClearColor(*config.backgroundColor)
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    pg.key.set_repeat(config.keyRepeatDelayTime, config.keyRepeatInterval)

    global vao
    vao = gl.glGenVertexArrays(1)
    gl.glBindVertexArray(vao)

def quit():
    if vao is not None:
        gl.glDeleteVertexArrays(1, [vao])

def compile_shader(source, shaderType):
    """
    source: str source code
    shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER or GL_GEOMETRY_SHADER
    """
    shader = gl.glCreateShader(shaderType)
    gl.glShaderSource(shader, source)
    gl.glCompileShader(shader)
    result = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
    info = gl.glGetShaderInfoLog(shader).decode('utf-8')
    if info:
        print('Shader compilation info:\n{}'.format(info))
    if result == gl.GL_FALSE:
        raise Exception('GLSL compile error: {}'.format(shaderType))
    return shader


class Program:
    def __init__(self, shader_datas):
        """
        shader_datas: A list of (filename, shaderType) tuples.
        """
        self.id = gl.glCreateProgram()
        shaders = []
        try:
            for name, type in shader_datas:
                source = open(name, 'r').read()
                shader = compile_shader(source, type)
                gl.glAttachShader(self.id, shader)
                shaders.append(shader)
            gl.glLinkProgram(self.id)
        finally:
            for shader in shaders:
                gl.glDeleteShader(shader)
        assert self.check_valid()
        assert self.check_linked()

    def get_uniform_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = gl.glGetUniformLocation(self.id, name)
        assert loc >= 0, 'Get uniform {} failed'.format(name)
        return loc

    def get_attrib_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = gl.glGetAttribLocation(self.id, name)
        assert loc >= 0, 'Get attribute {} failed'.format(name)
        return loc

    def print_info(self):
        info = gl.glGetProgramInfoLog(self.id).decode('ascii')
        if info:
            print('Program info log:', info)

    def check_valid(self):
        gl.glValidateProgram(self.id)
        result = gl.glGetProgramiv(self.id, gl.GL_VALIDATE_STATUS)
        if result == gl.GL_FALSE:
            self.print_info()
            return False
        return True

    def check_linked(self):
        result = gl.glGetProgramiv(self.id, gl.GL_LINK_STATUS)
        if result == gl.GL_FALSE:
            self.print_info()
            return False
        return True

    def use(self):
        gl.glUseProgram(self.id)

    def unuse(self):
        gl.glUseProgram(0)

    def delete(self):
        if self.id != 0:
            gl.glDeleteProgram(self.id)


def convert_texture(image, size=None):
    """
    image: A pygame surface or raw bytes in RGBA format.
    """
    if isinstance(image, pg.Surface):
        imageBytes = pg.image.tostring(image, 'RGBA')
        size = image.get_size()
    else:
        imageBytes = image
        assert size is not None, "Don't know raw bytes image size."
    textureId = gl.glGenTextures(1)
    assert textureId > 0, 'Fail to get texture, maybe display_init not called.'
    gl.glBindTexture(gl.GL_TEXTURE_2D, textureId)
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D, 0, 
        gl.GL_RGBA,  # internal format
        size[0], size[1],
        0,  # border, must be 0
        gl.GL_RGBA,  # input data format
        gl.GL_UNSIGNED_BYTE,
        imageBytes,
    )
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    # Set this to avoid light and coloring affecting the texture.
    gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_DECAL)

    return textureId


class TextureUnit:
    ENUMS = [gl.GL_TEXTURE0, gl.GL_TEXTURE1, gl.GL_TEXTURE2, gl.GL_TEXTURE3]  # FIXME

    def __init__(self, id):
        self.id = id
        self.glenum = self.ENUMS[id]

class RenderProgam(Program):
    def __init__(self):
        super().__init__([
            ('map.v.glsl', gl.GL_VERTEX_SHADER),
            ('map.f.glsl', gl.GL_FRAGMENT_SHADER),
        ])
        self.positionLoc = self.get_attrib_loc('vertexPosition')
        self.positionBuf = vbo.VBO(np.zeros(1))

        self.uvLoc = self.get_attrib_loc('vertexUV')
        self.uvBuf = vbo.VBO(np.zeros(1))

        gl.glEnableVertexAttribArray(self.positionLoc)
        gl.glEnableVertexAttribArray(self.uvLoc)

        self.textureUnit = TextureUnit(0)

    def zoom_to(self, rate):
        gl.glUniform1f(self.get_uniform_loc('zoomRate'), float(rate))

    def set_positions(self, positions):
        self.positionBuf.set_array(positions)
        self.positionBuf.bind()
        gl.glVertexAttribPointer(self.positionLoc, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

    def set_uvs(self, uvs):
        self.uvBuf.set_array(uvs)
        self.uvBuf.bind()
        gl.glVertexAttribPointer(self.uvLoc, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

    def set_screen_size(self, size):
        gl.glUniform2f(self.get_uniform_loc('screenSize'), float(size[0]), float(size[1]))

    def set_texture(self, texture_id):
        gl.glActiveTexture(self.textureUnit.glenum)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
        gl.glUniform1i(self.get_uniform_loc('textureSampler'), self.textureUnit.id)

    def draw(self, count):
        """
        count: Multiple of 4, since we are drawing quads.
        """
        assert count % 4 == 0
        gl.glDrawArrays(gl.GL_QUADS, 0, count)

def gl_loop(func):
    @utils.pg_loop
    def newfunc(screen, events):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        func(events)
    return newfunc
