from array import array
import string
from collections import namedtuple

import pylru

import texture
import config
import utils
from scrollmap import ScrollMap

GRID_FIELD_NUM = 6
EVENT_FIELD_NUM = 11
SCENE_BLOCK_SIZE = config.sceneMapXMax * config.sceneMapYMax * 2 * GRID_FIELD_NUM
EVENT_BLOCK_SIZE = config.eventNumPerScene * 2 * EVENT_FIELD_NUM

Grid = namedtuple('Grid', (
    'floor',
    'building',
    'float',
    'event',
    'height',
    'floatHeight',
))

Event = namedtuple('Event', (
    'd0',
    'd1',
    'd2',
    'd3',
    'd4',
    'd5',
    'd6',
    'texture',
    'd8',
    'd9',
    'd10',
))

textures = None

def get_textures():
    global textures
    if textures is None:
        textures = texture.TextureGroup('smap')
    return textures

# Typecode 'h' means signed short int.
TYPE_CODE = 'h'

class Scene(ScrollMap):
    """
    grids
    events
    entrance
    """
    width = config.sceneMapXMax
    height = config.sceneMapYMax

    def __init__(self, id, meta_data, sbytes, ebytes):
        ScrollMap.__init__(self, self.width, self.height)
        self.id = id
        sbuf = array(TYPE_CODE, sbytes)
        ebuf = array(TYPE_CODE, ebytes)
        del sbytes, ebytes

        self.grids = [Grid(*x) for x in self._extract(sbuf, GRID_FIELD_NUM)]
        self.events = [
            Event(*ebuf[i:i + EVENT_FIELD_NUM]) 
            for i in range(0, len(ebuf), EVENT_FIELD_NUM)
        ]
        self.metaData = meta_data
        self.set_texture_group(get_textures())

        # self.debug_dump(0)
        # self.debug_dump(1)

    @staticmethod
    def _extract(data, nFields):
        assert len(data) % nFields == 0
        nItems = len(data) // nFields
        itemDatas = [
            tuple(data[j * nItems + i] for j in range(nFields))
            for i in range(nItems)
        ]
        return itemDatas

    @staticmethod
    def _repack(items, nFields):
        return array(TYPE_CODE, (x[j] for j in range(nFields) for x in items))

    @property
    def entrance(self):
        return self.metaData['入口X'], self.metaData['入口Y']

    @property
    def name(self):
        return self.metaData['名称']

    def save(self):
        sbytes = self._repack(self.grids, GRID_FIELD_NUM).tobytes()
        ebytes = b''.join(array(TYPE_CODE, e).tobytes() for e in self.events)
        return sbytes, ebytes

    def iter_grids(self):
        for y in range(self.height):
            for x in range(self.width):
                yield (x, y), self.get_grid((x, y))

    def debug_dump(self, field):
        allIds = list({grid[field] for (x, y), grid in self.iter_grids()})
        marks = dict(zip(allIds, string.printable))

        print('  ', end=' ')
        for x in range(self.width):
            print(x // 10 if x % 10 == 0 else ' ', end=' ')
        print()
        print('  ', end=' ')
        for x in range(self.width):
            print(x % 10, end=' ')
        print()

        for y in range(self.height):
            print('{}{}'.format((y // 10 if y % 10 == 0 else ' '), y % 10),
                end=' ')
            for x in range(self.width):
                grid = self.get_grid((x, y))
                if grid[field] == -1:
                    c = '!'
                elif grid[field] == 0:
                    c = '.'
                elif self.textures.get(grid[field]) is not None:
                    c = marks.get(grid[field], '烫')
                else:
                    c = ' '
                print(c, end=' ')
            print()
        legend = [(marks[id], id // 2) for id in marks]
        legend.sort()
        print('\n'.join(map(str, legend)))

    # Implement draw_grid method to support ScrollMap operations.
    def draw_grid(self, pos, surface_pos):
        """
        Draw the grid at position `pos` to surface at dest postion 
        `surface_pos`.
        """
        try:
            grid = self.get_grid(pos)
        except KeyError:
            return
        # draw floor
        if grid.floor > 0:
            self.blit_texture(grid.floor, surface_pos, grid.height)
        # draw building
        if grid.building > 0:
            self.blit_texture(grid.building, surface_pos, grid.height)
        # draw floating
        if grid.float > 0:
            self.blit_texture(grid.float, surface_pos, grid.floatHeight)
        # draw event
        if grid.event >= 0:
            event = self.events[grid.event]
            # utils.debug("event:", event.texture, event)
            self.blit_texture(event.texture, surface_pos, grid.height)

    def get_grid(self, pos):
        x, y = pos
        if not 0 <= x < self.width or not 0 <= y < self.height:
            raise KeyError(pos)
        return self.grids[y * self.width + x]


class SceneGroup:
    @classmethod
    def load(cls, meta_datas, scene_file, event_file):
        """
        meta_datas: A list of meta data. The i(th) element is a dict storing 
            the data of the scene with id=i.
        scene_file: A file object that contains all scene data
        event_file: A file object that contains events in each scene
        """
        self = SceneGroup()
        self.sceneBuffer = scene_file.read()
        self.eventBuffer = event_file.read()
        self.metaDatas = meta_datas
        self._dirtyScenes = set()
        self._scenes = pylru.lrucache(config.sceneCacheNum, self.on_eject)
        self._nameToId = {
            meta['名称'].replace('\x00', ''): id 
            for id, meta in enumerate(meta_datas)
        }
        print(self._nameToId)
        return self

    def on_eject(self, id, scene):
        self._dirtyScenes.add(id)

    def save(self, scene_file, event_file):
        """
        scene_file: A writable file object
        event_file: A writable file object

        Note that meta cannot be changed so we don't save it here.
        """
        # First write the buffers that loaded before any modification
        scene_file.write(self.sceneBuffer)
        event_file.write(self.eventBuffer)
        utils.debug('save:', self._dirtyScenes)
        for id in self._dirtyScenes:
            scene = self.get(id)
            sbuf, ebuf = scene.save()

            scene_file.seek(SCENE_BLOCK_SIZE * id)
            scene_file.write(sbuf)

            event_file.seek(EVENT_BLOCK_SIZE * id)
            event_file.write(ebuf)

    def _load_scene(self, id):
        sbuf = self.sceneBuffer[id * SCENE_BLOCK_SIZE:(id + 1) * SCENE_BLOCK_SIZE]
        ebuf = self.eventBuffer[id * EVENT_BLOCK_SIZE:(id + 1) * EVENT_BLOCK_SIZE]
        meta = self.metaDatas[id]
        return Scene(id, meta, sbuf, ebuf)

    def get(self, id):
        if id in self._scenes:
            return self._scenes[id]
        scene = self._load_scene(id)
        self._scenes[id] = scene
        self._dirtyScenes.add(id)
        return scene

    def get_by_name(self, name):
        return self.get(self._nameToId[name])
