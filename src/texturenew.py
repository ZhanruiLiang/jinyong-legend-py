from collections import namedtuple
import pickle
import gzip
import pygame as pg

import config
import utils

Texture = namedtuple('Texture', (
    'image', 'xoff', 'yoff', 
    # 'packX', 'packY', 'width', 'height',
))

class TextureGroup:
    _groups = {}
    _data = None

    def __init__(self, meta):
        self.name = meta['name']
        self.image = pg.image.fromstring(
            gzip.decompress(meta['image']), meta['size'], meta['format']
        ).convert()
        self.image.set_colorkey(config.colorKey)
        self.textures = {}
        for t in meta['textureMetas']:
            id = t[0]
            subImage = self.image.subsurface(t[3:])
            self.textures[id] = Texture(subImage, t[1], t[2])
        utils.debug(self.name, 'textures:', len(self.textures))

    @classmethod
    def get_group(cls, name):
        if cls._data is None:
            with open(config.dataFile, 'rb') as infile:
                data = pickle.load(infile)
                cls._data = {meta['name']: meta for meta in data}
        if name not in cls._groups:
            cls._groups[name] = TextureGroup(cls._data[name])
        return cls._groups[name]

    def load_all(self):
        pass

    def iter_all(self):
        yield from self.textures.items()

    def __len__(self):
        return len(self.textures)

    def get(self, id, fail=0):
        id //= 2
        if id not in self.textures:
            utils.debug('{}: id: {} not in range {}'.format(
                self.name, id, (0, len(textures) - 1)))
            return None
        return self.textures[id]


if __name__ == '__main__':
    utils.pg_init()
    image = TextureGroup.get_group('smap').image
    utils.show_surface(image)
