import pygame as pg
import config

class Sprite(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()


class Picture(Sprite):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.image = pg.image.load(config.resource('pic', name))
        self.rect = pg.Rect((0, 0), self.image.get_size())

# class SpriteManager:
#     def __init__(self, spriteLayerPairs):
#         self.sprites = []
# 
#         self.extend(spriteLayerPairs)
# 
#     def add(self, sprite, layer):
#         self.sprites.append((sprite, layer))
# 
#     def extend(self, spriteLayerPairs):
#         for sprite, layer in spriteLayerPairs:
#             self.add(sprite, layer)
# 
#     def draw(self, surface):
#         self.sprites.sort(key=lambda x: x[1])
#         for sp, layer in self.sprites:
#             sp.update()
#         rects = []
#         for sp, layer in self.sprites:
#             rects.append(surface.blit(sp.image, sp.rect))
#         return rects
