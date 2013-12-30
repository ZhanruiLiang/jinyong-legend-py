import texture
import config

_portraits = None


def init():
    global _portraits
    if _portraits is None:
        _portraits = texture.TextureGroup(config.portraitFilename)


def get(id):
    return _portraits.get_texture(id)
