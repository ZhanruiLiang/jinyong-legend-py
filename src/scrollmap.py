import pygame as pg
import config
import utils
import sprite

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
        #     p1
        #   /    \
        #  /      \
        # p4       p2
        #  \      /
        #   \    /      
        #     p3   

        # p1, p2, p3, p4 = map(self.to_gs_pos, 
        #     ((0, 0), (xmax, 0), (xmax, ymax), (0, ymax)))
        # self.image = pg.Surface(
        #     (p3[0] - p1[0] + self.GX, p4[1] - p2[1] + self.GY), 0, 32)
        size = (
            config.screenWidth + 2 * self.GX,
            config.screenHeight + 2 * self.GY,
        )
        self.image = pg.Surface(size).convert_alpha()
        self.oldImage = self.image.copy()

        self.rect = pg.Rect((-self.GX, -self.GY), size)
        self.currentPos = (0, 0)
        self.xmax = xmax
        self.ymax = ymax
        self.looper = ScrollLooper(
            # (config.screenWidth, config.screenHeight),  # size
            (W, H),  # size
            (self.GX, self.GY),  # grid size
        )

        # If _drawn[x, y] = surfacePos, that means we have drawn grid (x, y)
        # onto surfacePos. Keep these to speed up the drawing in next draw.
        self._drawn = {}

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
        sx, sy = surface_pos
        self.image.blit(
            texture.image, 
            (sx - texture.xoff, sy - texture.yoff - height)
        )
        # self.image.blit(texture.image, (sx - texture.xoff, sy - texture.yoff))

    def move_to(self, pos):
        # utils.debug("Move to", pos)
        self.currentPos = pos
        self.redraw()

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
        cnt = 0
        for dx, dy in self.looper:
            pos = x + dx, y + dy
            surfacePos = (
                centerX + dx * baseX[0] + dy * baseY[0],
                centerY + dx * baseX[1] + dy * baseY[1],
            )
            self.draw_grid(pos, surfacePos)
            cnt += 1
        # pg.draw.rect(self.image, (0xff, 0, 0), self.clip_rect, 2)
        utils.debug('cnt:', cnt)

    def delta_draw(self, direction):
        self.redraw(); return
        x, y = self.currentPos
        centerX, centerY = self.image.get_rect().center
        baseX, baseY = self.BASE_X, self.BASE_Y

        def blit_old():
            sox, soy = self.to_gs_vec(direction)
            self.image.blit(self.oldImage, (-sox, -soy))

        def draw_along_y(ys):
            cnt = 0
            for dy in sorted(ys.keys()):
                cnt += 1
                dx = ys[dy]
                pos = x + dx, y + dy
                surfacePos = (
                    centerX + dx * baseX[0] + dy * baseY[0],
                    centerY + dx * baseX[1] + dy * baseY[1],
                )
                self.draw_grid(pos, surfacePos)
            utils.debug('cnt:', cnt)

        def draw_along_x(xs):
            cnt = 0
            for dx in sorted(xs.keys()):
                cnt += 1
                dy = xs[dx]
                pos = x + dx, y + dy
                surfacePos = (
                    centerX + dx * baseX[0] + dy * baseY[0],
                    centerY + dx * baseX[1] + dy * baseY[1],
                )
                self.draw_grid(pos, surfacePos)
            utils.debug('cnt:', cnt)

        self.swap_surface()
        utils.clear_surface(self.image)
        if direction == (1, 0):
            ys = {}
            for dx, dy in self.looper:
                if dy not in ys:
                    ys[dy] = dx
                else:
                    ys[dy] = max(ys[dy], dx)
            blit_old()
            draw_along_y(ys)
        elif direction == (-1, 0):
            ys = {}
            for dx, dy in self.looper:
                if dy not in ys:
                    ys[dy] = dx
                else:
                    ys[dy] = min(ys[dy], dx)
            draw_along_y(ys)
            blit_old()
        # pg.draw.rect(self.image, (0xff, 0, 0), ((self.GX + M, self.GY + M), (W, H)), 2)

    def swap_surface(self):
        self.oldImage, self.image = self.image, self.oldImage

    def move(self, direction):
        x, y = self.currentPos
        dx, dy = direction
        self.currentPos = (x + dx, y + dy)
        self.delta_draw(direction)

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
