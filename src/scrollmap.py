import config
import utils
from collections import deque
from scrollmap_helper import search_path, add, minus 

class Character:
    WALK_TEXTURE_ID0 = 2501
    BOAT_TEXTURE_ID0 = 3715
    WALK_TICK_PERIOD = 6
    COOL_DOWN_PERIOD = 5

    pos = None
    direction = None
    mp = None
    
    def __init__(self, orientation):
        self.orientation = orientation

        self._moveTick = 0
        self._tickPeriod = self.WALK_TICK_PERIOD
        self._staticTick = self.COOL_DOWN_PERIOD

    def on_add(self, mp, pos):
        self.mp = mp
        self.fly_to(pos)

    def cal_texture_id(self):
        di = config.Directions.all.index(self.orientation)
        return self.WALK_TEXTURE_ID0 + di * 7 + self._moveTick

    def fly_to(self, pos):
        self.on_move(self.pos, pos)
        self.pos = pos
        self.direction = None

    def move(self, direction):
        self.direction = direction

    def on_move(self, from_pos, pos):
        mp = self.mp
        if from_pos:
            x, y = from_pos
            mp.gridTable[mp.buildingI, y, x] = 0

        self._moveTick = 1 + self._moveTick % self._tickPeriod
        self._staticTick = 0

        x, y = pos
        mp.gridTable[mp.buildingI, y, x] = self.cal_texture_id() * 2

    def on_hit(self, from_pos, pos):
        utils.debug('Hit', pos, self.mp.gridTable[:, pos[1], pos[0]])

    def on_pause(self, pos):
        if self._staticTick > self.COOL_DOWN_PERIOD:
            return
        if self._staticTick == self.COOL_DOWN_PERIOD:
            self._moveTick = 0
            x, y = pos
            self.mp.gridTable[self.mp.buildingI, y, x] = self.cal_texture_id() * 2
            return
        self._staticTick += 1

    def update(self):
        direction = self.direction
        if direction:
            self.orientation = direction
            newPos = add(self.pos, direction)
            if 0 <= newPos[0] < self.mp.xmax and 0 <= newPos[1] < self.mp.ymax:
                if self.mp.can_move_to(newPos):
                    self.on_move(self.pos, newPos)
                    self.pos = newPos
                    self.direction = direction
                else:
                    self.on_hit(self.pos, newPos)
        else:
            self.on_pause(self.pos)
        self.direction = None



class FormationManager:
    def __init__(self, width, head):
        self.width = width
        self.head = head
        self.followers = []
        self.ques = [[] for i in range(width)]

    def add(self, char):
        queI = min(range(self.width), key=lambda i: (len(self.ques[i]), i))
        que = self.ques[queI]
        char.follow(self.head,
            (- 2 * (len(que) + 1), (-1, 1)[queI % 2] * ((queI + 1) // 2)))
        que.append(char)

    def update(self):
        pass


class MainCharacter(Character):
    def on_move(self, from_pos, pos):
        self.mp.set_view_pos(pos)
        super().on_move(from_pos, pos)

    def on_pause(self, pos):
        self.mp.set_view_pos(pos)
        super().on_pause(pos)


class Follower(Character):
    dest = None
    blocked = False

    def follow(self, char, offset):
        self.dest = char
        self.offset = offset
        self.path = []

    def update(self):
        self.direction = None
        self.blocked = True
        if not self.path:
            ix, iy = self.dest.orientation
            jx, jy = iy, -ix
            xoff, yoff = self.offset
            destPos = add(self.dest.pos, (xoff * ix + yoff * jx, xoff * iy + yoff * jy))
            if destPos == self.pos:
                self.orientation = self.dest.orientation
                self.blocked = False
            else:
                self.path = search_path(
                    self.mp.gridTable, self.mp.buildingI, self.pos, destPos, 200)
        if self.blocked and self.path:
            nextPos = self.path.pop()
            direction = minus(nextPos, self.pos)
            if direction in config.Directions.all:
                if self.mp.can_move_to(nextPos):
                    self.direction = minus(nextPos, self.pos)
                    self.blocked = False
        if self.blocked:
            self.orientation = self.dest.orientation
        super().update()


class ScrollMap:
    floorHeightI = 0
    batchData = [(1, 1)]
    buildingI = 1

    def __init__(self, main_textures, grid_table):
        self.gridTable = grid_table
        self.ymax, self.xmax = grid_table.shape[1:]
        self.debugGridTable = (2 * (grid_table[self.buildingI, :, :] > 0))\
            .reshape((1, self.ymax, self.xmax)).astype('h')

        self.render = None
        self.textures = main_textures
        self.currentPos = (0, 0)
        self.chars = []

    def set_view_pos(self, pos):
        self.currentPos = pos

    def find_empty_around(self, pos):
        que = deque([pos])
        while que:
            head = que.popleft()
            for direction in config.Directions.all:
                newPos = add(head, direction)
                if self.can_move_to(newPos):
                    return newPos
                if 0 <= newPos[0] < self.xmax and 0 <= newPos[1] < self.ymax:
                    que.append(newPos)
        return None

    def add_character(self, char, pos):
        if not self.chars:
            self.mainChar = char
        if not self.can_move_to(pos):
            pos1 = self.find_empty_around(pos)
            assert pos1
            pos = pos1
                    
        char.on_add(self, pos)
        self.chars.append(char)
        self.currentPos = char.pos

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
        # self.render.set_grid_table(self.debugGridTable)
        # self.render.batch_draw(((0, 0),))
        # self.render.set_grid_table(self.gridTable)

    def can_move_to(self, pos):
        if not (0 <= pos[0] < self.xmax and 0 <= pos[1] < self.ymax):
            return False
        return True

    def update(self):
        for char in self.chars:
            char.update()
