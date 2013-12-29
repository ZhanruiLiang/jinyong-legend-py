import pygame as pg
import struct
import array
import config
import io

pallette = None

TYPE_CODE = 'B'

def load_idx_file(filename):
    with open(filename, 'rb') as infile:
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
            self.colors[i] = (r0 * 4, g0 * 4, b0 * 4, 255)

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
        # self.idxs.append(len(self.grp))
        self.textures = [None] * (len(self.idxs) - 1)

    def get_texture(self, id):
        if self.textures[id] is None:
            texture = self.load_texture(id)
            self.textures[id] = texture
        else:
            texture = self.textures[id]
        return texture

    def load_texture(self, id):
        start, end = self.idxs[id], self.idxs[id + 1]
        data = self.grp[start:end]
        fileobj = io.BytesIO(data)
        try:
            image = pg.image.load(fileobj, 'png')
            xoff, yoff = image.get_size()
            xoff //= 2
            yoff //= 2
        except pg.error as err:
            xoff, yoff, image = self.parse_RLE(data)

        return Texture(xoff, yoff, image)

    def parse_RLE(self, data):
        # Parse a little endian unsigned short
        pallette = get_pallette()
        w, h, xoff, yoff = struct.unpack('<4H', data[:8])
        surface = pg.Surface((w, h)).convert_alpha()
        surface.fill((0, 0, 0, 0))
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
            nRLEDataInRow = rle[p]; p += 1
            x = 0
            while p - p0 < nRLEDataInRow:
                nEmptyPixels = rle[p]; p += 1
                x += nEmptyPixels
                # x exceeded line width, break and read next row
                if x >= w: 
                    break
                nSolidPixels = rle[p]; p += 1
                for j in range(nSolidPixels):
                    assert x < w
                    surface.set_at((x, y), pallette.get(rle[p]))
                    p += 1
                    x += 1
                # x exceeded line width, break and read next row
                if x >= w: 
                    break
        return xoff, yoff, surface

    def get_all(self):
        for id in range(len(self.idxs) - 1):
            yield self.get_texture(id)


class Animation:
    def __init__(self, texture_group, ids):
        self.textureGroup = texture_group
        self.ids = ids
        self.totalFrames = len(ids)
        self.currentFrame = 0

    def next_frame(self):
        self.currentFrame += 1
        self.currentFrame %= self.totalFrames

    def get_texture(self):
        return self.textureGroup.get_texture(self.ids[self.currentFrame])
