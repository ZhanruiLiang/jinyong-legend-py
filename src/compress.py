import pygame as pg
import gzip
import pickle

import config
import utils
from texture import PackedTextureGroup

filenames = [
    'smap', 'wmap', 'mmap'
] + [
    'fight{:03d}'.format(i) for i in range(110)
]

def compress_textures(filenames, dest, image_format='RGBA'):
    utils.pg_init((10, 10))
    data = []

    for name in filenames:
        try:
            textures = PackedTextureGroup(name)
        except FileNotFoundError:
            continue
        image = textures.pack.image
        rawImageStr = pg.image.tostring(image, image_format)
        compressedImageStr = gzip.compress(rawImageStr)
        utils.debug('compressed size: {}MB. ratio: {}'.format(
            len(compressedImageStr) / 1024 ** 2,
            len(compressedImageStr) / len(rawImageStr)
        ))
        textureMetas = []
        for p, (id, t) in zip(textures.pack.poses, textures.iter_all()):
            textureMetas.append((
                id, t.xoff, t.yoff, p[0], p[1], t.image.get_width(), t.image.get_height(),
            ))
        metaItem = {
            'name': textures.name,
            'size': image.get_size(),
            'format': image_format,
            'image': compressedImageStr,
            'textureMetas': textureMetas,
        }
        data.append(metaItem)
    with open(dest, 'wb') as outfile:
        pickle.dump(data, outfile, -1)


if __name__ == '__main__':
    compress_textures(filenames, config.dataFile)
