import pygame as pg
import struct
import array
import config
import io
import utils

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


class TextureGroup:
    def __init__(self, name):
        # print('load texture:', name)
        self.name = name
        self.idxs = load_idx_file(config.resource('data', name + '.idx'))
        self.grp = load_grp_file(config.resource('data', name + '.grp'))
        self.idxs.append(0)
        self.textures = [None] * (len(self.idxs) - 1)
        utils.debug(name, 'textures:', len(self.textures))

    def __len__(self):
        return len(self.textures)

    def get(self, id, fail=0):
        id //= 2
        if not 0 <= id < len(self.textures):
            utils.debug('{}: id: {} not in range {}'.format(
                self.name, id, (0, len(self.textures) - 1)))
            return None
        if self.textures[id] is None:
            texture = self._load_texture(id)
            self.textures[id] = texture
        else:
            texture = self.textures[id]
        return texture

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
            xoff, yoff, image = self._parse_RLE(data)

        return Texture(xoff, yoff, image)

    def _parse_RLE(self, data):
        # Parse a little endian unsigned short
        pallette = get_pallette()
        w, h, xoff, yoff = struct.unpack('4h', data[:8])
        surface = utils.new_surface((w, h))
        pixels = pg.pixelarray.PixelArray(surface)
        # Start run length decoding
        rle = array.array(TYPE_CODE, data[8:])
        del data
        n = len(rle)
        p = 0
        for y in range(h):
            if p >= n:
                break
            p0 = p
            # Read how many RLE items in this row
            nRLEDataInRow = rle[p]
            p += 1
            x = 0
            while p - p0 < nRLEDataInRow:
                nEmptyPixels = rle[p]
                p += 1
                x += nEmptyPixels
                # x exceeded line width, break and read next row
                if x >= w: 
                    break
                nSolidPixels = rle[p]
                p += 1
                for j in range(nSolidPixels):
                    assert x < w
                    # surface.set_at((x, y), pallette.get(rle[p]))
                    pixels[x, y] = pallette.get(rle[p])
                    p += 1
                    x += 1
                # x exceeded line width, break and read next row
                if x >= w: 
                    break
        return xoff, yoff, surface

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
