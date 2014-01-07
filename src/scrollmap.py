import numpy as np
import config
# import utils

def add(a, b):
    return (a[0] + b[0], a[1] + b[1])

class ScrollMap:
    floorHeightI = 0
    batchData = []

    def __init__(self, main_textures, grid_table):
        self.gridTable = grid_table
        self.render = None
        self.textures = main_textures

        self.currentPos = (0, 0)
        self.directionQueue = []

    def move_to(self, pos):
        self.currentPos = pos
        self.directionQueue.clear()

    def move(self, direction):
        if len(self.directionQueue) >= 2:
            return
        self.directionQueue.append(direction)

    def update(self):
        que = self.directionQueue
        if que:
            direction = que.pop()
            self.currentPos = add(self.currentPos, direction)

    def bind(self, render):
        self.render = render
        render.set_texture_group(self.textures)
        render.set_grid_table(self.gridTable)

    def draw(self):
        assert self.render, 'Need to bind before drawing.'
        self.render.set_pos(self.currentPos)
        self.render.batch_draw(((0, self.floorHeightI),))
        if self.batchData:
            self.render.batch_draw(self.batchData)
