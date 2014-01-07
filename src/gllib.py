from OpenGL.GL import *
import pygame as pg

import config
import utils

vao = None

def display_init(size):
    pg.display.init()
    pg.display.set_mode(size, pg.OPENGL | pg.DOUBLEBUF, 24)
    utils.debug('OpenGL context:', glGetString(GL_VERSION))

    pg.display.gl_set_attribute(pg.GL_SWAP_CONTROL, 1)

    # OpenGL context created, initialize GL stuff
    glClearColor(0, 0, 0, 1)
    glEnable(GL_TEXTURE_2D)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    pg.key.set_repeat(config.keyRepeatDelayTime, config.keyRepeatInterval)

    global vao
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

def quit():
    if vao is not None:
        glDeleteVertexArrays(1, [vao])

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


class Program(int):
    @staticmethod
    def compile(shader_datas):
        """
        shader_datas: A list of (filename, shaderType) tuples.
        """
        self = Program(glCreateProgram())
        shaders = []
        try:
            for name, type in shader_datas:
                source = open(name, 'r').read()
                shader = compile_shader(source, type)
                glAttachShader(self, shader)
                shaders.append(shader)
            glLinkProgram(self)
        finally:
            for shader in shaders:
                glDeleteShader(shader)
        assert self.check_valid()
        assert self.check_linked()
        return self

    def get_uniform_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = glGetUniformLocation(self, name)
        assert loc >= 0, 'Get uniform {} failed'.format(name)
        return loc

    def get_attrib_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = glGetAttribLocation(self, name)
        assert loc >= 0, 'Get attribute {} failed'.format(name)
        return loc

    def print_info(self):
        info = glGetProgramInfoLog(self).decode('ascii')
        if info:
            print('Program info log:', info)

    def check_valid(self):
        glValidateProgram(self)
        result = glGetProgramiv(self, GL_VALIDATE_STATUS)
        if result == GL_FALSE:
            self.print_info()
            return False
        return True

    def check_linked(self):
        result = glGetProgramiv(self, GL_LINK_STATUS)
        if result == GL_FALSE:
            self.print_info()
            return False
        return True

    def use(self):
        glUseProgram(self)

    def unuse(self):
        glUseProgram(0)

    def delete(self):
        if self != 0:
            glDeleteProgram(self)


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
    textureId = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textureId)
    glTexImage2D(
        GL_TEXTURE_2D, 0, 
        GL_RGBA,  # internal format
        size[0], size[1],
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


class GLTextureUnit:
    ENUMS = [GL_TEXTURE0, GL_TEXTURE1, GL_TEXTURE2, GL_TEXTURE3]  # FIXME

    def __init__(self, id):
        self.id = id
        self.glenum = self.ENUMS[id]

