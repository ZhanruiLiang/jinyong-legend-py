"""
Testing environment for packing algorithms.
"""
import utils
import pygame as pg
import config
from texture import TextureGroup
import numpy as np
import colorsys

bgColor = 0xffffff

scale = 0.5

def scale_rect(k, rect):
    r = rect.copy()
    r.width *= k
    r.height *= k
    return r


class Packer:
    def __init__(self, size):
        self.size = size

    def step(self):
        pass

    def pack(self, rects):
        w, h = self.size
        rowMax = 0
        x, y = 0, 0
        results = []
        for r in rects:
            w1, h1 = r.size
            r1 = r.copy()
            if w1 + x <= w:
                # Add r1 to this row
                pass
            else:
                # Add r1 to next row
                y += rowMax
                rowMax = 0
                x = 0
            r1.topleft = x, y
            x += w1
            rowMax = max(rowMax, h1)
            results.append(r1)
        if y + rowMax > h:
            utils.debug('Warning: Packing failed, maxh: {}, h: {}'.format(h, y + rowMax))
        return results

def vec2(x, y):
    return np.array([x, y])

dt = 1 / config.FPS

class GravityPacker(Packer):
    def pack(self, rects):
        w, h = self.size
        n = len(rects)
        print('n:', n)
        # positions
        P = self.P = np.zeros((n, 2), dtype=np.double)
        self.V = np.zeros((n, 2), dtype=np.double)
        # Dist
        D = self.D = np.zeros(n, dtype=np.double)
        self.k = 1e-5
        for i, r in enumerate(rects):
            P[i] = np.random.rand() * w, np.random.rand() * h
            D[i] = max(r.width, r.height) / 2

        self.results = [r.copy() for r in rects]

    def step(self):
        P = self.P
        D = self.D
        k = self.k
        V = self.V
        for i in range(len(P)):
            dP = P - P[i]
            dPLen = (dP ** 2 + 1e-8).sum(1) ** 0.5
            D2 = (D[i] + D)
            R = dPLen - D2
            s = k * (R ** 2)
            V[i] += np.dot(s / dPLen, dP) / D[i]**2
        P += V * dt
        # V *= .99
        for i, r in enumerate(self.results):
            r.topleft = P[i]
        # print(P)

class SortPacker(Packer):
    def pack(self, rects):
        results = self.results = [r.copy() for r in rects]
        rects = [(r.size, i) for i, r in enumerate(rects)]
        rects.sort(key=lambda x: -x[0][1])  # sort by height
        W, H = self.size
        currentH = rects[0][0][1]
        thd = 2
        x, y = 0, 0
        for (w, h), i in rects:
            # if currentH - h <= thd and w + x <= W:
            if w + x <= W:
                # add to this row
                pass
            else:
                # add to now row
                x = 0
                y += currentH
                currentH = h
            results[i].topleft = (x, y)
            x += w
        self.rate = sum(w * h for (w, h), _ in rects) / (W * (y + currentH))

screen = utils.pg_init()

textures = TextureGroup('smap')
rectsOrig = [t.image.get_rect() for _, t in textures.iter_all()]
rects = [scale_rect(scale, r) for r in rectsOrig]

# rects = rects[:150]
# packer = GravityPacker(screen.get_size())
packer = SortPacker(screen.get_size())
packer.pack(rects)

colors = [
    tuple(map(lambda x:int(x * 255), colorsys.hsv_to_rgb(h, .45, .82)))
    for h in np.linspace(0, 1, len(rects))
]

reflesh = True

@utils.pg_loop
def loop(screen, events):
    global scale, reflesh
    for e in events:
        if e.type == pg.KEYDOWN:
            if e.key == pg.K_UP:
                scale += .1
            elif e.key == pg.K_DOWN:
                scale -= .1
            scale = max(scale, .1)
            reflesh = True
    if reflesh:
        w, h = packer.size
        w, h = int(w / scale + 1), int(h / scale + 1)
        rects = [scale_rect(scale, r) for r in rectsOrig]
        packer.pack(rects)
        print(
            'rescale to:', scale, 
            'realsize: {:d}x{:d}={:.3f}M'.format(w, h, w * h * 4 / 1024 ** 2),
            'rate:', packer.rate,
        )

        screen.fill(bgColor)
        # for r, c in zip(packer.results, colors):
        #     pg.draw.rect(screen, c, r, 1)
        for (_, t), r in zip(textures.iter_all(), packer.results):
            screen.blit(pg.transform.scale(t.image, r.size), r)
        pg.display.update()
    reflesh = False
