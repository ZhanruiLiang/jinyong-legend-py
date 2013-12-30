import texture
import config
import array
import pylru


class SceneGroup:
    SCENE_BLOCK_SIZE = config.sceneMapXMax * config.sceneMapYMax * 2 * 6
    EVENT_BLOCK_SIZE = config.eventNumPerScene * 2 * 11
    textures = None

    @classmethod
    def load(cls, scene_file, event_file):
        self = SceneGroup()
        self.sceneBuffer = scene_file.read()
        self.eventBuffer = event_file.read()
        self.scenes = pylru.lrucache(config.sceneCacheNum)
        return self

    def __init__(self):
        if SceneGroup.textures is None:
            SceneGroup.textures = texture.TextureGroup('smap')

    def save(self, scene_file, event_file):
        scene_file.write(self.sceneBuffer)
        event_file.write(self.eventBuffer)
        for id, scene in self.scenes.items():
            sbuf, ebuf = scene.save()

            scene_file.seek(self.SCENE_BLOCK_SIZE * id)
            scene_file.write(sbuf)

            event_file.seek(self.EVENT_BLOCK_SIZE * id)
            event_file.write(ebuf)

    def get_scene(self, id):
        if id in self.scenes:
            return self.scenes[id]
        sbuf = self.sceneBuffer[
            id * self.SCENE_BLOCK_SIZE: (id + 1) * self.SCENE_BLOCK_SIZE
        ]
        ebuf = self.eventBuffer[
            id * self.EVENT_BLOCK_SIZE: (id + 1) * self.EVENT_BLOCK_SIZE
        ]
        scene = Scene(id, sbuf, ebuf)
        self.scenes[id] = scene
        return scene

class Scene:
    def __init__(self, id, sbuf, ebuf):
        self.id = id
        self.sbuf = array.array('h', sbuf)
        self.ebuf = array.array('h', ebuf)

    def save(self):
        return self.sbuf.tobytes(), self.ebuf.tobytes()
