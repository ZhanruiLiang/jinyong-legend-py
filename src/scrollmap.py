import pygame as pg
import threading
import string
from collections import deque

import pyxlru

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
    PAD_X = GX * 8
    PAD_Y = GY * 10

    def __init__(self, xmax, ymax, textures):
        super().__init__()
        self.textures = textures
        size = (
            config.screenWidth + self.PAD_X * 2, 
            config.screenHeight + self.PAD_Y * 2 + config.bottomPadding,
        )
        innerSize = (
            config.screenWidth - 2 * config.debugMargin,
            config.screenHeight - 2 * config.debugMargin,
        )
        self.rect = pg.Rect((-self.PAD_X, -self.PAD_Y), size)

        self.image = utils.new_surface(size)
        self.drawImage = self.image.copy()
        self.floorImage = self.image.copy()

        if CLIP:
            clip_rect = (
                (self.PAD_X + config.debugMargin - self.GX,
                    self.PAD_Y + config.debugMargin - self.GY),
                add(innerSize, (2 * self.GX, 2 * self.GY)),
            )
            self.image.set_clip(clip_rect)
            self.drawImage.set_clip(clip_rect)

        self.currentPos = (0, 0)
        self.directionQueue = []
        self.xmax = xmax
        self.ymax = ymax
        self.looper = ScrollLooper(
            # (config.screenWidth, config.screenHeight),  # size
            innerSize,  # size
            (self.GX, self.GY),  # grid size
        )

        self._gridTextureCache = pyxlru.lru(config.mainMapCacheSize)
        # self._gridTextureCache = {}
        self._dirty = threading.Condition()
        self._swapped = False
        self._drawnPos = (-1, -1)
        self._rows = deque()
        self._quit = False
        self.drawLock = threading.RLock()
        if config.smoothTicks > 1:
            self.drawerThread = threading.Thread(target=self.drawer)
            self.drawerThread.daemon = True
            self.drawerThread.start()
        self.rAdjuster = SimpleRateAdjuster()
        # self.rAdjuster = RateAdjuster()

    def swap_image(self):
        self.image, self.drawImage = self.drawImage, self.image
        self._swapped = True

    def quit(self):
        self._quit = True
        if config.smoothTicks > 1:
            self.notify_redraw()
            self.drawerThread.join()

    def to_gs_pos(self, pos):
        " Convert map pos to global screen pos. "
        x, y = pos
        return (x * self.BASE_X[0] + y * self.BASE_Y[0],
                x * self.BASE_X[1] + y * self.BASE_Y[1])

    def to_gs_vec(self, vec):
        dx, dy = vec
        return (dx * self.BASE_X[0] + dy * self.BASE_Y[0],
                dx * self.BASE_X[1] + dy * self.BASE_Y[1])

    # This method shound be overrided. It loads the grid's texture, except 
    # the floor.
    def load_grid_texture(self, pos):
        raise NotImplementedError

    # This method shound be overrided. It loads the grid's floor texture
    def get_floor_texture(self, pos):
        raise NotImplementedError

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

    # @utils.profile
    def redraw(self):
        with self.drawLock:
            currentX, currentY = self.currentPos
            x1, y1 = self._drawnPos
            dir = minus((currentX, currentY), self._drawnPos)
            self._swapped = False
            image = self.drawImage
            centerX, centerY = image.get_rect().center
            centerY -= config.bottomPadding // 2
            GX, GY = self.GX, self.GY

            def convert(dx, dy, texture):
                return (centerX + (dx - dy) * GX - texture.xoff,
                        centerY + (dx + dy) * GY - texture.yoff)

            # Speed up by removing 'self.*' in inner loop
            get_grid_texture = self.get_grid_texture
            get_floor_texture = self.get_floor_texture
            looper = self.looper
            floor = self.floorImage

            deltaDraw = dir in config.Directions.all

            utils.clear_surface(image)
            if deltaDraw:
                if config.drawFloor:
                    # Delta draw floor
                    dx, dy = negate(dir)
                    floor.scroll((dx - dy) * GX, (dx + dy) * GY)
                    for dx, dy in self.looper.iter_delta(dir):
                        texture = get_floor_texture((currentX + dx, currentY + dy))
                        if not texture:
                            texture = self.textures.get(0)
                        floor.blit(texture.image, convert(dx, dy, texture))
                    image.blit(floor, (0, 0))
                # Delta draw other
                rows = self._rows
                kL, kR = looper.kRange
                tL, tR = looper.tRange
                if dir == config.Directions.left \
                        or dir == config.Directions.up:
                    rows.pop()
                    rows.appendleft(deque())
                else:
                    rows.popleft()
                    rows.append(deque())
                if dir == config.Directions.left \
                        or dir == config.Directions.down:
                    for row in rows:
                        if not row:
                            continue
                        dx, dy = minus(row[0], (currentX, currentY))
                        if dx - dy < tL:
                            row.popleft()
                else:
                    for row in rows:
                        if not row:
                            continue
                        dx, dy = minus(row[-1], (currentX, currentY))
                        if dx - dy >= tR:
                            row.pop()

                for dx, dy in self.looper.iter_delta(dir):
                    pos = currentX + dx, currentY + dy
                    texture = get_grid_texture(pos)
                    if texture:
                        rows[dx + dy - kL].append(pos)
                for row in rows:
                    for pos in row:
                        texture = get_grid_texture(pos)
                        spos = convert(pos[0] - currentX, pos[1] - currentY, texture)
                        image.blit(texture.image, spos)
            else:  # Redraw
                # Redraw floor
                utils.clear_surface(floor)
                for dx, dy in self.looper.iter():
                    pos = currentX + dx, currentY + dy
                    texture = get_floor_texture(pos)
                    if texture:
                        spos = convert(dx, dy, texture)
                        floor.blit(texture.image, spos)
                image.blit(floor, (0, 0))
                # Delta draw other
                rows = deque(deque() for k in range(*self.looper.kRange))
                kL = looper.kRange[0]
                for dx, dy in self.looper.iter():
                    pos = currentX + dx, currentY + dy
                    texture = get_grid_texture(pos)
                    if texture:
                        rows[dx + dy - kL].append(pos)
                        spos = convert(dx, dy, texture)
                        image.blit(texture.image, spos)
                self._rows = rows

            # utils.debug('-' * 30)
            # for i, row in enumerate(rows):
            #     utils.debug(i, row)
            self._drawnPos = (currentX, currentY)

    def drawer(self):
        while not self._quit:
            with self._dirty:
                self._dirty.wait()
            if self._quit: 
                break
            self.redraw()

    # @utils.profile
    def merge_textures(self, data):
        """
        data: A list of (id, height) tuples.
        """
        texturesToMerge = []
        for id, height in data:
            if id <= 0:
                continue
            texture = self.textures.get(id)
            if texture is None: 
                continue
            texturesToMerge.append((height, texture))

        if not texturesToMerge:
            return None
        rects = [
            pg.Rect((-t.xoff, -t.yoff - height), t.image.get_size()) 
            for height, t in texturesToMerge
        ]
        rect = rects[0].unionall(rects)
        image = utils.new_surface(rect.size)
        # image.fill((0x50, 0x50, 0x50, 100))
        x, y = -rect.x, -rect.y
        for height, t in texturesToMerge:
            image.blit(t.image, (x - t.xoff, y - t.yoff - height))
        return Texture(x, y, image)

    # @utils.profile
    def get_grid_texture(self, pos):
        try:
            texture = self._gridTextureCache[pos]
        except KeyError:
            texture = self.load_grid_texture(pos)
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
                if config.smoothTicks > 1:
                    self.notify_redraw()
                else:
                    self.redraw()
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
        allIds = list({getter(grid) 
            for _, grid in self.iter_grids(topleft, size)})
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

        surface = utils.new_surface((width, height))
        print('dest size:', surface.get_size())
        centerX, centerY = surface.get_rect().center

        utils.clear_surface(surface)
        tmpSize = tmpWidth, tmpHeight = (2 ** 12,) * 2
        print('tmp buffer size:', tmpSize)
        tmpScaleSize = (int(tmpWidth * scale), int(tmpHeight * scale))
        print('tmpScaleSize:', tmpScaleSize)
        tmpSurface = utils.new_surface(tmpSize)
        blockDx = blockDy = int(min(tmpWidth / self.GX / 2, tmpHeight / self.GY / 2))

        for blockX in range(0, xmax, blockDx):
            for blockY in range(0, ymax, blockDy):
                utils.clear_surface(tmpSurface)
                for x in range(blockDx):
                    for y in range(blockDy):
                        if not 0 <= x < xmax or not 0 <= y < ymax:
                            continue
                        # Draw floor
                        texture = self.get_floor_texture((blockX + x, blockY + y))\
                            or self.textures.get(0)
                        spos = (
                            tmpWidth / 2 - texture.xoff + (x - y) * self.GX, 
                            -texture.yoff + (x + y + 1) * self.GY,
                        )
                        tmpSurface.blit(texture.image, spos)
                        # Draw other
                        texture = self.get_grid_texture((blockX + x, blockY + y))
                        if texture:
                            spos = (
                                tmpWidth / 2 - texture.xoff + (x - y) * self.GX, 
                                -texture.yoff + (x + y + 1) * self.GY,
                            )
                            tmpSurface.blit(texture.image, spos)
                        progress.update()

                surface.blit(
                    pg.transform.scale(tmpSurface, add((1, 1), tmpScaleSize)),
                    minus(to_spos((blockX, blockY)), (tmpScaleSize[0] / 2, gy))
                )
                # print((blockX, blockY), to_spos((blockX, blockY)))

        pg.image.save(surface, save_to)
        print('\nfinished')


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
    def __init__(self, size, grid_size, bottom_pad=18, side_pad=4):
        self.size = size
        self.gridSize = grid_size

        w, h = size
        gx, gy = grid_size
        rx = int(w / (2 * gx) + .99999) + 2
        ry = int(h / (2 * gy) + .99999) + 2
        kL, kR = self.kRange = (-ry, ry + bottom_pad+ 1)
        tL, tR = self.tRange = (-rx, rx + side_pad + 1)

        self._list = []
        D = config.Directions
        self._deltaLists = {d: [] for d in D.all}

        for k in range(*self.kRange):
            for t in range(*self.tRange):
                if (t + k) % 2 == 0:
                    dxy = (t + k) // 2, (k - t) // 2
                    self._list.append(dxy)
                    if k == kL or t == tR - 1:
                        self._deltaLists[D.up].append(dxy)
                    if k == kR - 1 or t == tL:
                        self._deltaLists[D.down].append(dxy)
                    if k == kL or t == tL:
                        self._deltaLists[D.left].append(dxy)
                    if k == kR - 1 or t == tR - 1:
                        self._deltaLists[D.right].append(dxy)

    def iter_delta(self, direction):
        return self._deltaLists[direction]

    def iter(self):
        return self._list
