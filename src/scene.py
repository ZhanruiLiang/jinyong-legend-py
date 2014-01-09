from array import array
import numpy as np

import pylru

import config
import utils
from scrollmap import ScrollMap, MainCharacter
from texturenew import TextureGroup

GRID_FIELD_NUM = 6
EVENT_FIELD_NUM = 11
SCENE_BLOCK_SIZE = config.sceneMapXMax * config.sceneMapYMax * GRID_FIELD_NUM * 2
EVENT_BLOCK_SIZE = config.eventNumPerScene * EVENT_FIELD_NUM * 2

class GridFields:
    floor = 0
    building = 1
    float = 2
    event = 3
    height = 4
    floatHeight = 5

class Event(utils.NamedStruct):
    __slots__ = [
        'blocked', 'id', 'interact', 'item', 'stepOn', 
        'frameStart', 'frameEnd', 'texture', 'delay', 'x', 'y',
    ]

class MainSceneCharacter(MainCharacter):
    def on_hit(self, from_pos, pos):
        event = self.mp.get_event_at(pos)
        utils.debug('Hit', pos, self.mp.gridTable[:, pos[1], pos[0]], event)

# Typecode 'h' means signed short int.
TYPE_CODE = 'h'

class Scene(ScrollMap):
    """
    grids
    events
    entrance
    name
    """
    floorHeightI = GridFields.height
    batchData = [
        (GridFields.building, GridFields.height),
        (GridFields.float, GridFields.floatHeight),
        (GridFields.event, GridFields.height)
    ]

    def __init__(self, id, meta_data, sbytes, ebytes):
        self.id = id

        self.origGridTable = np.fromstring(sbytes, TYPE_CODE)\
            .reshape((GRID_FIELD_NUM, config.sceneMapYMax, config.sceneMapXMax))

        ebuf = array(TYPE_CODE, ebytes)
        del ebytes
        self.events = [
            Event(*ebuf[i:i + EVENT_FIELD_NUM]) 
            for i in range(0, len(ebuf), EVENT_FIELD_NUM)
        ]
        super().__init__(TextureGroup.get_group('smap'), self.make_grid_table())

        self.metaData = meta_data
        self._eventTick = 0

    def can_move_to(self, pos):
        x, y = pos
        grid = self.origGridTable[:, y, x]
        if grid[GridFields.building] > 0:
            return False  # Blocked by building
        eventId = grid[GridFields.event]
        if eventId >= 0 and self.events[eventId].blocked:
            return False
        # TODO: water
        return True

    def get_event_at(self, pos):
        eid = self.origGridTable[GridFields.event, pos[1], pos[0]]
        return self.events[eid] if eid >= 0 else None

    def make_grid_table(self):
        gridTable = self.origGridTable.copy()
        xmax, ymax = gridTable.shape[1:]
        for y in range(ymax):
            for x in range(xmax):
                e = gridTable[GridFields.event, y, x]
                if e >= 0:
                    gridTable[GridFields.event, y, x] = self.events[e].texture
        return gridTable

    @property
    def entrance(self):
        return self.metaData['入口X'], self.metaData['入口Y']

    @property
    def name(self):
        return self.metaData['名称']

    def save(self):
        sbytes = self.gridTable.tostring()
        ebytes = b''.join(array(TYPE_CODE, e).tobytes() for e in self.events)
        return sbytes, ebytes

    def iter_valid_events(self):
        for event in self.events:
            if self.origGridTable[GridFields.event, event.y, event.x] >= 0:
                yield event

    def update(self):
        if self._eventTick % 4 == 0:
            for event in self.iter_valid_events():
                if not (0 < event.frameStart < event.frameEnd):
                    continue
                event.texture += 2
                if event.texture > event.frameEnd:
                    # Wrap back the frame to start - delay
                    event.texture = event.frameStart - event.delay
                if event.texture >= event.frameStart:
                    self.gridTable[GridFields.event, event.y, event.x] = event.texture

        self._eventTick = (self._eventTick + 1) % 100
        super().update()


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

    def __len__(self):
        return len(self.eventBuffer) // EVENT_BLOCK_SIZE

    def get(self, id):
        if id in self._scenes:
            return self._scenes[id]
        scene = self._load_scene(id)
        self._scenes[id] = scene
        self._dirtyScenes.add(id)
        return scene

    def get_by_name(self, name):
        return self.get(self._nameToId[name])
