import pygame as pg
import struct
import array
import config
import io
import utils
from parse_rle import parse_RLE

pallette = None

# TYPE_CODE will be used to :
# * decode pallette file
# * decode RLE file
TYPE_CODE = 'B'  # unsigned char

def load_idx_file(filename):
    with open(filename, 'rb') as infile:
        # Typecode 'I' means unsigned int.
        return array.array('I', infile.read())

def load_grp_file(filename):
    with open(filename, 'rb') as infile:
        return infile.read()


class Pallette:
    def __init__(self, filename):
        with open(filename, 'rb') as infile:
            buf = array.array(TYPE_CODE)
            buf.fromfile(infile, 256 * 3)
        self.colors = [None] * 256
        for i in range(256):
            r0, g0, b0 = buf[i * 3:i * 3 + 3]
            self.colors[i] = (r0 * 4, g0 * 4, b0 * 4)
            assert self.colors[i] != config.colorKey, \
                'Color key collide with pallatte'

    def get(self, idx):
        return self.colors[idx]


def get_pallette():
    global pallette
    if pallette is None:
        pallette = Pallette(config.palletteFile)
    return pallette


class Texture:
    def __init__(self, xoff, yoff, image):
        self.xoff = xoff
        self.yoff = yoff
        self.image = image

    def copy(self):
        return Texture(self.xoff, self.yoff, self.image.copy())


class TextureGroup:
    def __init__(self, name):
        # print('load texture:', name)
        self.name = name
        self.idxs = load_idx_file(config.resource('data', name + '.idx'))
        self.grp = load_grp_file(config.resource('data', name + '.grp'))
        self.idxs.append(0)
        self.empty = object()
        self.textures = [self.empty] * (len(self.idxs) - 1)
        utils.debug(name, 'textures:', len(self.textures))

    def __len__(self):
        return len(self.textures)

    def get(self, id, fail=0):
        id //= 2
        textures = self.textures
        if not 0 <= id < len(textures):
            utils.debug('{}: id: {} not in range {}'.format(
                self.name, id, (0, len(textures) - 1)))
            return None
        if textures[id] is self.empty:
            texture = self._load_texture(id)
            textures[id] = texture
            return texture
        return textures[id]

    # @utils.profile
    def _load_texture(self, id):
        start, end = self.idxs[id - 1], self.idxs[id]
        if start == end or start >= len(self.grp):
            # utils.debug('Texture#{} is empty. [{}:{}]'.format(id, start, end))
            return None
        data = self.grp[start:end]
        # print(start, end, len(self.grp))
        fileobj = io.BytesIO(data)
        try:
            image = pg.image.load(fileobj, 'png')
            xoff, yoff = image.get_size()
            xoff //= 2
            yoff //= 2
        except pg.error:
            w, h, xoff, yoff = struct.unpack('4h', data[:8])
            rle = array.array(TYPE_CODE, data[8:])
            result = parse_RLE(w, h, get_pallette().colors, rle)
            image = pg.image.fromstring(result, (w, h), 'RGB').convert()
            image.set_colorkey(config.colorKey)
        w, h = image.get_size()
        if w * h > 1:
            return Texture(xoff, yoff, image)
        return None

    def get_all(self):
        for id in range(len(self.idxs) - 1):
            texture = self.get(id)
            if texture is not None:
                yield id, texture


class MapTextureGroup(TextureGroup):
    pass


class Animation:
    def __init__(self, texture_group, ids):
        self.textureGroup = texture_group
        self.ids = ids
        self.totalFrames = len(ids)
        self.currentFrame = 0

    def next_frame(self):
        self.currentFrame += 1
        self.currentFrame %= self.totalFrames

    def get(self):
        return self.textureGroup.get(self.ids[self.currentFrame])
