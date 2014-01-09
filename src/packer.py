import utils
import config
import heapq
import pygame as pg
import ctypes

class ImagePack:
    """
Attributes:
    size
    poses
    rate
    """
    N_WIDTH_STEP = 8
    MAX_WIDTH = 2 ** 11

    def __init__(self, images, width=None):
        self.width = width
        self.images = list(images)
        self._packed = False
        self.pack()

    @utils.profile
    def _calculate(self, transpose):
        """
        return (size, poses, rate)
        """
        if transpose:
            swap = lambda a: (a[1], a[0])
        else:
            swap = lambda a: a
        images = self.images

        # Perform a swap here
        sizes = [(swap(img.get_size()), i) for i, img in enumerate(images)]

        # Sort by height, from high to low.
        sizes.sort(key=lambda x: (-x[0][1], -x[0][0]))
        pos = [None] * len(sizes)
        area = sum(w * h for (w, h), _ in sizes)
        maxRate = 0
        bestSize = bestPos = None
        maxSingleW = max(w for (w, h), id in sizes)
        # caculate wmax
        if self.width:
            wmax = self.width
        else:
            wmax = self.MAX_WIDTH

        @utils.profile
        def fill(gw):
            if gw < maxSingleW: 
                return
            nonlocal maxRate, bestSize, bestPos
            rowRests = []
            heapq.heappush(rowRests, (-gw, 0))
            rowYs = [0]
            rowHeight = sizes[0][0][1]
            for (w, h), id in sizes:
                maxW = -rowRests[0][0]
                if maxW >= w:
                    # Add to this row
                    i = rowRests[0][1]
                    heapq.heapreplace(rowRests, (- (maxW - w), i))
                    pos[id] = (gw - maxW, rowYs[i])
                else:
                    # Create new row
                    heapq.heappush(rowRests, (-(gw - w), len(rowRests)))
                    rowYs.append(rowYs[-1] + rowHeight)
                    rowHeight = h
                    pos[id] = (0, rowYs[-1])
            size = (gw, rowYs[-1] + rowHeight)
            rate = area / (size[0] * size[1])
            if rate > maxRate:
                maxRate = rate
                bestSize = size
                bestPos = pos[:]
        nSteps = self.N_WIDTH_STEP
        wmin = maxSingleW
        while 1:
            stepSize = (wmax - wmin) / nSteps
            if stepSize < 1:
                break
            gw = wmin
            while gw <= wmax:
                fill(int(gw))
                gw += stepSize
            gw = bestSize[0]
            wmin = gw - stepSize
            wmax = gw + stepSize
        # for gw in range(wmin, wmax + 1, self.WIDTH_STEP):
        #     fill(gw)
        # Swap again and return
        utils.debug('rate: {}, transpose: {}'.format(maxRate, transpose))
        return swap(bestSize), list(map(swap, bestPos)), maxRate

    def pack(self, transpose=False):
        """
        Calculate self.size, self.poses, self.rate
        """
        if self._packed:
            return
        self._packed = True
        images = self.images

        if config.packerAutoTranspose:
            self.size, self.poses, self.rate = max(
                (self._calculate(0), self._calculate(1)),
                key=lambda x: x[-1] 
            )
        else:
            self.size, self.poses, self.rate = self._calculate(1)

        self.image = self.make_image()
        images = [
            self.image.subsurface((p, img.get_size())) 
            for p, img in zip(self.poses, images)
        ]
        utils.debug(
            'Packed {} images. Final size {}. Memory: {:.2f}MB. Rate: {:.3f}'.
            format(
                len(images), self.size,
                self.size[0] * self.size[1] * 4 / 2 ** 20, self.rate
            )
        )
        self.images = images

    def make_image(self, waste_color=config.colorKey):
        surface = utils.new_surface(self.size)
        surface.fill(waste_color)
        for image, pos in zip(self.images, self.poses):
            colorKey = image.get_colorkey()
            image.set_colorkey(None)
            surface.blit(image, pos)
            image.set_colorkey(colorKey)
        return surface
