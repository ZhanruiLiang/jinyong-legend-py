import pygame as pg
import config
import utils
import sprite
import pylru
from texture import Texture

def minus(a, b):
    return (a[0] - b[0], a[1] - b[1])

# M = 100
M = 0
W = config.screenWidth - M * 2
H = config.screenHeight - M * 2
CLIP = 0

class ScrollMap(sprite.Sprite):
    GX = config.textureXScale 
    GY = config.textureYScale
    BASE_X = (GX, GY)
    BASE_Y = (-GX, GY)

    def __init__(self, xmax, ymax):
        size = (config.screenWidth, config.screenHeight)

        self.rect = pg.Rect((0, 0), size)
        # self.image = pg.Surface(size).convert_alpha()
        self.image = pg.display.get_surface()
        self.currentPos = (0, 0)
        self.xmax = xmax
        self.ymax = ymax
        self.looper = ScrollLooper(
            # (config.screenWidth, config.screenHeight),  # size
            (W, H),  # size
            (self.GX, self.GY),  # grid size
        )

        self._gridTextureCache = pylru.lrucache(2 ** 14)
        self._dirty = True

    def set_texture_group(self, textures):
        self.textures = textures

    def to_gs_pos(self, pos):
        " Convert map pos to global screen pos. "
        x, y = pos
        return (x * self.BASE_X[0] + y * self.BASE_Y[0],
                x * self.BASE_X[1] + y * self.BASE_Y[1])

    def to_gs_vec(self, vec):
        dx, dy = vec
        return (dx * self.BASE_X[0] + dy * self.BASE_Y[0],
                dx * self.BASE_X[1] + dy * self.BASE_Y[1])

    def draw_grid(self, pos, surface_pos):
        raise NotImplementedError

    def blit_texture(self, texture_id, surface_pos, height):
        if texture_id == -1:
            return
        texture = self.textures.get(texture_id)
        if texture is None:
            # utils.debug('Invalid to blit None on {}'.format(surface_pos))
            return
        self._texturesToMerge.append((height, texture))

    def move_to(self, pos):
        # utils.debug("Move to", pos)
        self.currentPos = pos
        self._dirty = True
        self.redraw()

    def render(self):
        if self._dirty:
            self.redraw()
            self._dirty = False

    @property
    def clip_rect(self):
        return ((self.GX + M, self.GY + M), (W, H))

    def redraw(self):
        x, y = self.currentPos
        centerX, centerY = self.image.get_rect().center
        baseX, baseY = self.BASE_X, self.BASE_Y
        utils.clear_surface(self.image)
        if CLIP:
            self.image.set_clip(self.clip_rect)
        # cnt = 0
        for dx, dy in self.looper:
            pos = x + dx, y + dy
            surfacePos = (
                centerX + dx * baseX[0] + dy * baseY[0],
                centerY + dx * baseX[1] + dy * baseY[1],
            )
            # if dx == 0 and dy == 0:
            #     self.draw_grid_cache(pos, surfacePos)
            self.draw_grid_cache(pos, surfacePos)
            # cnt += 1
        # pg.draw.rect(self.image, (0xff, 0, 0), self.clip_rect, 2)
        # utils.debug('cnt:', cnt)

    def draw_grid_cache(self, pos, surface_pos):
        if pos in self._gridTextureCache:
            texture = self._gridTextureCache[pos]
        else:
            self._texturesToMerge = []
            self.draw_grid(pos, surface_pos)
            # Merge textures
            rects = [
                pg.Rect((-t.xoff, -t.yoff - height), t.image.get_size()) 
                for height, t in self._texturesToMerge
            ]
            if not rects:
                texture = None
            else:
                rect = rects[0].unionall(rects)
                image = pg.Surface(rect.size).convert_alpha()
                utils.clear_surface(image)
                x, y = -rect.x, -rect.y
                for height, t in self._texturesToMerge:
                    image.blit(t.image, (x - t.xoff, y - t.yoff - height))
                texture = Texture(x, y, image)
                self._gridTextureCache[pos] = texture
        if texture is None:
            return
        sx, sy = surface_pos
        self.image.blit(
            texture.image, 
            (sx - texture.xoff, sy - texture.yoff)
        )

    def move(self, direction):
        x, y = self.currentPos
        dx, dy = direction
        self.currentPos = (x + dx, y + dy)
        self._dirty = True

    def update(self):
        pass

class ScrollLooper:
    def __init__(self, size, grid_size):
        self.size = size
        self.gridSize = grid_size

        w, h = size
        gx, gy = grid_size
        rx = int(w / (2 * gx) + .99999) + 2
        ry = int(h / (2 * gy) + .99999) + 2
        self._kRange = (-ry, ry + 20)
        self._tRange = (-rx, rx + 1)

    def __iter__(self):
        for k in range(*self._kRange):
            for t in range(*self._tRange):
                if (t + k) % 2 == 0:
                    dx = (t + k) // 2
                    dy = (k - t) // 2
                    yield dx, dy
