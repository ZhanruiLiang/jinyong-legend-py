from array import array
from collections import namedtuple

import pylru

from texture import PackedTextureGroup as TextureGroup
# from texture import TextureGroup
import config
import utils
from scrollmap import ScrollMap

GRID_FIELD_NUM = 6
EVENT_FIELD_NUM = 11
SCENE_BLOCK_SIZE = (
    config.sceneMapXMax * config.sceneMapYMax * GRID_FIELD_NUM * 2)
EVENT_BLOCK_SIZE = config.eventNumPerScene * EVENT_FIELD_NUM * 2

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

@utils.singleton
class SceneTextures(TextureGroup):
    def __init__(self):
        super().__init__('smap')

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

    @utils.profile
    def __init__(self, id, meta_data, sbytes, ebytes):
        super().__init__(self.width, self.height, SceneTextures.get_instance())
        self.id = id
        sbuf = array(TYPE_CODE, sbytes)
        ebuf = array(TYPE_CODE, ebytes)
        del sbytes, ebytes

        self.grids = [Grid(*x) for x in utils.level_extract(sbuf, GRID_FIELD_NUM)]
        self.events = [
            Event(*ebuf[i:i + EVENT_FIELD_NUM]) 
            for i in range(0, len(ebuf), EVENT_FIELD_NUM)
        ]
        self.metaData = meta_data

        # self.debug_dump(0)
        # self.debug_dump(1)

    @property
    def entrance(self):
        return self.metaData['入口X'], self.metaData['入口Y']

    @property
    def name(self):
        return self.metaData['名称']

    def save(self):
        sbytes = utils.level_repack(self.grids, TYPE_CODE, GRID_FIELD_NUM).tobytes()
        ebytes = b''.join(array(TYPE_CODE, e).tobytes() for e in self.events)
        return sbytes, ebytes

    def debug_dump(self, field):
        def getter(grid):
            return grid[field]
        super().debug_dump(getter)

    # Override this method to support ScrollMap operations.
    def load_grid_texture(self, pos):
        grid = self.get_grid(pos, None)
        if grid:
            eventTexture = self.events[grid.event].texture \
                if grid.event >= 0 else -1
            return self.merge_textures([
                (grid.floor, grid.height),
                (grid.building, grid.height),
                (grid.float, grid.floatHeight),
                (eventTexture, grid.height),
            ])

    # Override this for ScrollMap
    def get_floor_texture(self, pos):
        grid = self.get_grid(pos)
        if grid and grid.floor > 0:
            return self.textures.get(grid.floor)
        return None

    def get_grid(self, pos, default=None):
        x, y = pos
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return default
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
        # utils.debug(self._nameToId)
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
        S = SCENE_BLOCK_SIZE
        E = EVENT_BLOCK_SIZE
        sbuf = self.sceneBuffer[id * S:(id + 1) * S]
        ebuf = self.eventBuffer[id * E:(id + 1) * E]
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
