import config

def add(a, b):
    return (a[0] + b[0], a[1] + b[1])

class ScrollMap:
    floorHeightI = 0
    batchData = []

    def __init__(self, main_textures, grid_table):
        self.gridTable = grid_table
        self.ymax, self.xmax = grid_table.shape[1:]
        self.render = None
        self.textures = main_textures

        self.currentPos = (0, 0)
        self.directionQueue = []
        self.direction = None
        self.orientation = config.Directions.all[0]

    def move_to(self, pos):
        self.currentPos = pos
        self.directionQueue.clear()
        self.on_pause(pos)

    def move(self, direction):
        if len(self.directionQueue) >= 2:
            return
        self.directionQueue.append(direction)

    def update(self):
        que = self.directionQueue
        self.direction = None
        if que:
            direction = que.pop()
            self.orientation = direction
            newPos = add(self.currentPos, direction)
            if 0 <= newPos[0] < self.xmax and 0 <= newPos[1] < self.ymax \
                    and self.can_move_to(newPos):
                self.on_move(newPos, direction)
                self.currentPos = newPos
                self.direction = direction
        if self.direction is None:
            self.on_pause(self.currentPos)

    def on_move(self, pos, direction):
        pass

    def on_pause(self, pos):
        pass

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

    def can_move_to(self, pos):
        raise NotImplementedError
