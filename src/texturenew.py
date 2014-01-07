import pickle
import gzip

import config
import utils
import gllib
import numpy as np
from OpenGL.GL import GLint

class TextureGroup:
    """
    uvTable: [(x, y, w, h, cx, cy)]
    """
    _data = None
    _groups = {}

    def __init__(self, meta):
        self.name = meta['name']
        self.size = meta['size']

        maxId = 0
        uvs = {}
        for item in meta['textureMetas']:
            id, cx, cy, x, y, w, h = item
            uvs[id] = (x, y, w, h, cx, cy)
            maxId = max(id, maxId)
        self.uvTable = np.zeros((maxId + 1, 6), GLint)
        for id, v in uvs.items():
            self.uvTable[id] = v

        rawImageBytes = gzip.decompress(meta['image'])
        self.textureId = gllib.convert_texture(rawImageBytes, meta['size'])

    @classmethod
    def get_group(cls, name):
        if cls._data is None:
            with open(config.dataFile, 'rb') as infile:
                data = pickle.load(infile)
                cls._data = {meta['name']: meta for meta in data}
        if name not in cls._groups:
            cls._groups[name] = TextureGroup(cls._data[name])
        return cls._groups[name]

    def __len__(self):
        return len(self.textures)


if __name__ == '__main__':
    utils.pg_init()
    image = TextureGroup.get_group('smap').image
    utils.show_surface(image)
