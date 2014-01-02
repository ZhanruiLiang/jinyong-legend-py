import pygame as pg
import threading
import string
import os

import pylru

import config
import utils
import sprite
from texture import Texture

def minus(a, b):
    return (a[0] - b[0], a[1] - b[1])

def add(a, b):
    return (a[0] + b[0], a[1] + b[1])

def negate(a):
    return (-a[0], -a[1])

CLIP = 0

class ScrollMap(sprite.Sprite):
    GX = config.textureXScale 
    GY = config.textureYScale
    BASE_X = (GX, GY)
    BASE_Y = (-GX, GY)
    PAD_X = GX * 2
    PAD_Y = GY * 2

    def __init__(self, xmax, ymax):
        size = (
            config.screenWidth + self.PAD_X * 2, 
            config.screenHeight + self.PAD_Y * 2,
        )

        self.rect = pg.Rect(
            (-self.PAD_X, -self.PAD_Y),
            size,
        )
        self.image = pg.Surface(size).convert_alpha()
        self.drawImage = self.image.copy()
        self.currentPos = (0, 0)
        self.directionQueue = []
        self.xmax = xmax
        self.ymax = ymax
        innerSize = (
            config.screenWidth - 2 * config.debugMargin,
            config.screenHeight - 2 * config.debugMargin,
        )
        self.looper = ScrollLooper(
            # (config.screenWidth, config.screenHeight),  # size
            innerSize,  # size
            (self.GX, self.GY),  # grid size
        )
        self.clip_rect = ((config.debugMargin, config.debugMargin), innerSize)

        self._gridTextureCache = pylru.lrucache(2 ** 12)
        # self._gridTextureCache = {}
        self._dirty = threading.Condition()
        self._swapped = False
        self._quit = False
        self.drawLock = threading.Lock()
        self.drawerThread = threading.Thread(target=self.drawer)
        self.drawerThread.start()
        self.rAdjuster = SimpleRateAdjuster()
        # self.rAdjuster = RateAdjuster()

    def swap_image(self):
        self.image, self.drawImage = self.drawImage, self.image
        self._swapped = True

    def quit(self):
        self._quit = True
        self.notify_redraw()
        self.drawerThread.join()

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

    def blit_texture(self, texture_id, height):
        if texture_id == -1:
            return
        texture = self.textures.get(texture_id, -1)
        if texture is None:
            # utils.debug('Invalid to blit None on {}'.format(surface_pos))
            return
        self._texturesToMerge.append((height, texture))

    def move_to(self, pos):
        # utils.debug("Move to", pos)
        self.currentPos = pos
        self._smoothTick = config.smoothTicks
        self.directionQueue.clear()
        self.rect.topleft = (-self.PAD_X, -self.PAD_Y)
        self.redraw()
        self.swap_image()

    def notify_redraw(self):
        with self._dirty:
            self._dirty.notify_all()

    def redraw(self):
        with self.drawLock:
            x, y = self.currentPos
            self._swapped = False
            image = self.drawImage
            centerX, centerY = image.get_rect().center
            baseX, baseY = self.BASE_X, self.BASE_Y
            utils.clear_surface(image)
            if CLIP:
                image.set_clip(self.clip_rect)
            self.cnt = 0
            for dx, dy in self.looper.iter():
                pos = x + dx, y + dy
                sx = centerX + dx * baseX[0] + dy * baseY[0]
                sy = centerY + dx * baseX[1] + dy * baseY[1]
                texture = self.get_grid_texture(pos)
                if not texture:
                    continue
                self.drawImage.blit(
                    texture.image, 
                    (sx - texture.xoff, sy - texture.yoff)
                )
                self.cnt += 1
            # utils.debug('cnt:', self.cnt)

    def make_minimap(self, save_to, scale=1 / 4):
        gx = self.GX * scale
        gy = self.GY * scale
        print('gx gy:', (gx, gy))
        xmax, ymax = self.xmax, self.ymax
        # xmax //= 2
        # ymax //= 2
        # Left most grid: (0, ymax) 
        # Right most grid: (xmax, 0)
        # Top most grid: (0, 0)
        # Bottom most grid: (xmax, ymax)
        centerX, centerY = 0, 0
        open(save_to, 'wb').close()

        # Function to convert from grid to surface
        def to_spos(pos):
            x, y = pos
            return ((centerX + (x - y) * gx), ((x + y + 1) * gy))

        width = int(gx * 2 + minus(to_spos((xmax, 0)), to_spos((0, ymax)))[0])
        height = int(gy * 2 + minus(to_spos((xmax, ymax)), to_spos((0, 0)))[1])

        progress = utils.ProgressBar(xmax * ymax)

        surface = pg.Surface((width, height)).convert_alpha()
        print('dest size:', surface.get_size())
        centerX, centerY = surface.get_rect().center

        utils.clear_surface(surface)
        tmpSize = tmpWidth, tmpHeight = (2 ** 12,) * 2
        print('tmp buffer size:', tmpSize)
        tmpScaleSize = (int(tmpWidth * scale), int(tmpHeight * scale))
        print('tmpScaleSize:', tmpScaleSize)
        tmpSurface = pg.Surface(tmpSize).convert_alpha()
        blockDx = blockDy = int(min(tmpWidth / self.GX / 2, tmpHeight / self.GY / 2))

        for blockX in range(0, xmax, blockDx):
            for blockY in range(0, ymax, blockDy):
                utils.clear_surface(tmpSurface)
                for x in range(blockDx):
                    for y in range(blockDy):
                        if not 0 <= x < xmax or not 0 <= y < ymax:
                            continue
                        texture = self.get_grid_texture((blockX + x, blockY + y))
                        if texture:
                            spos = (
                                tmpWidth / 2 - texture.xoff + (x - y) * self.GX, 
                                -texture.yoff + (x + y + 1) * self.GY,
                            )
                            tmpSurface.blit(texture.image, spos)
                        progress.update()

                surface.blit(
                    pg.transform.scale(tmpSurface, tmpScaleSize),
                    minus(to_spos((blockX, blockY)), (tmpScaleSize[0] / 2 + .5, gy + .5))
                )
                # print((blockX, blockY), to_spos((blockX, blockY)))

        pg.image.save(surface, save_to)
        print('\nfinished')

    def drawer(self):
        while not self._quit:
            with self._dirty:
                self._dirty.wait()
            if self._quit: 
                break
            self.redraw()

    def get_grid_texture(self, pos):
        if pos in self._gridTextureCache:
            texture = self._gridTextureCache[pos]
        else:
            self._texturesToMerge = []
            self.draw_grid(pos)
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
        return texture

    def move(self, direction):
        if len(self.directionQueue) >= 2:
            return
        self.directionQueue.append(direction)

    def update(self):
        if self._smoothTick == config.smoothTicks:
            que = self.directionQueue
            if que:
                self.rAdjuster.retick()
                direction = self.directionQueue.pop(0)
                self._smoothTick = 0
                self._scrollDir = negate(self.to_gs_vec(direction))
                with self.drawLock:
                    if not self._swapped:
                        self.swap_image()
                self.currentPos = add(self.currentPos, direction)
                self.notify_redraw()
            else:
                return
        else:
            self.rAdjuster.tick()
        self._smoothTick += 1
        r = self.rAdjuster.adjust(self._smoothTick)
        sdx, sdy = self._scrollDir
        self.rect.topleft = (-self.PAD_X + r * sdx, -self.PAD_Y + r * sdy)

    def iter_grids(self, topleft=(0, 0), size=None):
        w, h = size or (self.xmax, self.ymax)
        x0, y0 = topleft
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                yield (x, y), self.get_grid((x, y))

    def debug_dump(self, getter, topleft=(0, 0), size=None):
        w, h = size = size or (self.xmax, self.ymax)
        x0, y0 = topleft
        allIds = list({getter(grid) for _, grid in self.iter_grids(topleft, size)})
        marks = dict(zip(allIds, string.printable))

        print('  ', end=' ')
        for x in range(x0, x0 + w):
            print(x // 10 if x % 10 == 0 else ' ', end=' ')
        print()
        print('  ', end=' ')
        for x in range(x0, x0 + w):
            print(x % 10, end=' ')
        print()

        for y in range(y0, y0 + size[1]):
            print('{}{}'.format((y // 10 if y % 10 == 0 else ' '), y % 10),
                end=' ')
            for x in range(x0, x0 + w):
                grid = self.get_grid((x, y))
                id = getter(grid)
                if id == -1:
                    c = '!'
                elif id == 0:
                    c = '.'
                elif self.textures.get(id) is not None:
                    c = marks.get(id, '烫')
                else:
                    c = ' '
                print(c, end=' ')
            print()
        legend = [(marks[id], id // 2) for id in marks]
        legend.sort()
        print('\n'.join(map(str, legend)))


class SimpleRateAdjuster:
    def __init__(self):
        pass

    def tick(self):
        pass

    def retick(self):
        pass

    def adjust(self, tick):
        return tick / config.smoothTicks


class RateAdjuster(SimpleRateAdjuster):
    def __init__(self):
        self.timer = pg.time.Clock()
        T = config.smoothTicks
        self._dts = self._lastDts = [i / T for i in range(T + 1)]
        # self.retick()

    def tick(self):
        self._dts.append(self._dts[-1] + self.timer.tick())

    def retick(self):
        utils.debug('dts:', utils.diff(self._dts))
        self._lastDts = self._dts
        self._dts = [0]

    def adjust(self, tick):
        try:
            return self._lastDts[tick] / self._lastDts[-1]
        except IndexError:
            return 1.


class ScrollLooper:
    def __init__(self, size, grid_size):
        self.size = size
        self.gridSize = grid_size

        w, h = size
        gx, gy = grid_size
        rx = int(w / (2 * gx) + .99999) + 2
        ry = int(h / (2 * gy) + .99999) + 2
        self._kRange = (-ry, ry + 15)
        self._tRange = (-rx, rx + 3)

        self._list = []
        for k in range(*self._kRange):
            for t in range(*self._tRange):
                if (t + k) % 2 == 0:
                    dx = (t + k) // 2
                    dy = (k - t) // 2
                    self._list.append((dx, dy))

    def iter(self):
        return self._list
