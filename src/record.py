import array
import struct
import config
import utils
from collections import UserDict
from scene import SceneGroup

class RecordNotExistError(Exception): 
    pass

class Type:
    def __init__(self, size, typecode):
        self.size = size
        self.typecode = typecode

    def encode(self, val):
        return val

    def decode(self, val):
        return val

class SType(Type):
    ENCODING = 'hkscs'

    def __init__(self, size):
        super().__init__(size, str(size) + 's')

    def encode(self, val):
        return val.encode(self.ENCODING)

    def decode(self, val):
        return val.decode(self.ENCODING)

class STypeDebug(SType):
    def encode(self, val):
        if isinstance(val, bytes):
            return val
        return val.encode(self.ENCODING)

    def decode(self, val):
        try:
            return val.decode(self.ENCODING)
        except UnicodeDecodeError:
            print(val)
            return val

Tint16 = Type(2, 'h')
Tuint16 = Type(2, 'I')
Ts10 = SType(10)
Ts20 = SType(20)
Ts30 = SType(30)


class FrozenDict(UserDict):
    def __setitem__(self, key, value):
        if key in self:
            raise Exception("Can not modify FrozenDict")
        super().__setitem__(key, value)


class Field:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Struct:
    def __init__(self, name, fields):
        """
        fields: [(name, type)]
        """
        self.name = name
        self.fields = [Field(*field) for field in fields]
        self.size = sum(field.type.size for field in self.fields)
        self.fmt = ''.join(field.type.typecode for field in self.fields)

    def load(self, data):
        """
        data: bytes
        return: obj containing the loaded attributes
        """
        values = struct.unpack(self.fmt, data[:self.size])
        obj = {
            field.name: field.type.decode(value)
            for field, value in zip(self.fields, values)
        }
        return obj

    def save(self, obj):
        """
        obj: obj containing attributes that need to save
        return: data bytes
        """
        values = [field.type.encode(obj[field.name]) for field in self.fields]
        data = struct.pack(self.fmt, *values)
        return data


def m(names, times, type=Tint16):
    return [(x + str(i), type) for i in range(times) for x in names]

structMisc = Struct('misc', [
    ('乘船', Tint16),
    ('无用', Tint16),
    ('人X', Tint16), ('人Y', Tint16),
    ('人X1', Tint16), ('人Y1', Tint16),
    ('人方向', Tint16),
    ('船X', Tint16), ('船Y', Tint16),
    ('船X1', Tint16), ('船Y1', Tint16),
    ('船方向', Tint16),
] + m(('队伍',), config.maxTeamMemberNumber)
  + m(('物品', '物品数量'), config.maxItemNumber)
)

structPlayer = Struct('player', [
    ('代号', Tint16),
    ('头像代号', Tint16),
    ('生命增长', Tint16),
    ('无用', Tint16),
    ('姓名', Ts10),
    ('外号', Ts10),
    ('性别', Tint16),
    ('等级', Tint16),
    ('经验', Tint16),
    ('生命', Tint16),
    ('生命最大值', Tint16),
    ('受伤程度', Tint16),
    ('中毒程度', Tint16),
    ('体力', Tint16),
    ('物品修炼点数', Tint16),
    ('武器', Tint16),
    ('防具', Tint16),
] + m(('出招动画帧数', '出招动画延迟', '武功音效延迟'), 5) + [
    ('内力性质', Tint16),
    ('内力', Tint16),
    ('内力最大值', Tint16),
    ('攻击力', Tint16),
    ('轻功', Tint16),
    ('防御力', Tint16),
    ('医疗能力', Tint16),
    ('用毒能力', Tint16),
    ('解毒能力', Tint16),
    ('抗毒能力', Tint16),
    ('拳掌功夫', Tint16),
    ('御剑能力', Tint16),
    ('耍刀技巧', Tint16),
    ('特殊兵器', Tint16),
    ('暗器技巧', Tint16),
    ('武学常识', Tint16),
    ('品德', Tint16),
    ('攻击带毒', Tint16),
    ('左右互搏', Tint16),
    ('声望', Tint16),
    ('资质', Tint16),
    ('修炼物品', Tint16),
    ('修炼点数', Tint16),
] + m(('武功', '武功等级'), 10)
  + m(('携带物品', '携带物品数量'), 4)
)

structItem = Struct('item', [
    ('代号', Tint16),
    ('名称', Ts20),
    ('名称2', Ts20),
    ('物品说明', Ts30),
    ('练出武功', Tint16),
    ('暗器动画编号', Tint16),
    ('使用人', Tint16),
    ('装备类型', Tint16),
    ('显示物品说明', Tint16),
    ('类型', Tint16),
    ('未知5', Tint16),
    ('未知6', Tint16),
    ('未知7', Tint16),
    ('加生命', Tint16),
    ('加生命最大值', Tint16),
    ('加中毒解毒', Tint16),
    ('加体力', Tint16),
    ('改变内力性质', Tint16),
    ('加内力', Tint16),

    ('加内力最大值', Tint16),
    ('加攻击力', Tint16),
    ('加轻功', Tint16),
    ('加防御力', Tint16),
    ('加医疗能力', Tint16),

    ('加用毒能力', Tint16),
    ('加解毒能力', Tint16),
    ('加抗毒能力', Tint16),
    ('加拳掌功夫', Tint16),
    ('加御剑能力', Tint16),

    ('加耍刀技巧', Tint16),
    ('加特殊兵器', Tint16),
    ('加暗器技巧', Tint16),
    ('加武学常识', Tint16),
    ('加品德', Tint16),

    ('加攻击次数', Tint16),
    ('加攻击带毒', Tint16),
    ('仅修炼人物', Tint16),
    ('需内力性质', Tint16),
    ('需内力', Tint16),

    ('需攻击力', Tint16),
    ('需轻功', Tint16),
    ('需用毒能力', Tint16),
    ('需医疗能力', Tint16),
    ('需解毒能力', Tint16),

    ('需拳掌功夫', Tint16),
    ('需御剑能力', Tint16),
    ('需耍刀技巧', Tint16),
    ('需特殊兵器', Tint16),
    ('需暗器技巧', Tint16),

    ('需资质', Tint16),
    ('需经验', Tint16),
    ('练出物品需经验', Tint16),
    ('需材料', Tint16),
] + m(('练出物品', '需要物品数量'), 5)
)

structScene = Struct('scene', [
    ('代号', Tint16),
    ('名称', Ts10),
    ('出门音乐', Tint16),
    ('进门音乐', Tint16),
    ('跳转场景', Tint16),
    ('进入条件', Tint16),
    ('外景入口X1', Tint16),
    ('外景入口Y1', Tint16),
    ('外景入口X2', Tint16),
    ('外景入口Y2', Tint16),
    ('入口X', Tint16),
    ('入口Y', Tint16),
    ('出口X1', Tint16),
    ('出口X2', Tint16),
    ('出口X3', Tint16),
    ('出口Y1', Tint16),
    ('出口Y2', Tint16),
    ('出口Y3', Tint16),
    ('跳转口X1', Tint16),
    ('跳转口Y1', Tint16),
    ('跳转口X2', Tint16),
    ('跳转口Y2', Tint16),
])

structSkill = Struct('skill', [
    ('代号', Tint16),
    ('名称', Ts10),
    ('未知1', Tint16),
    ('未知2', Tint16),
    ('未知3', Tint16),
    ('未知4', Tint16),
    ('未知5', Tint16),
    ('出招音效', Tint16),
    ('武功类型', Tint16),
    ('武功动画&音效', Tint16),
    ('伤害类型', Tint16),
    ('攻击范围', Tint16),
    ('消耗内力点数', Tint16),
    ('敌人中毒点数', Tint16),
] + m(('攻击力', '移动范围', '杀伤范围', '加内力', '杀内力'), 10)
)

structShop = Struct('shop', m(('物品', '物品数量', '物品价格'), 5))

structCombatData = Struct('combatdata', [
    ('代号', Tint16),
    ('名称', Ts10),
    ('地图', Tint16),
    ('经验', Tint16),
    ('音乐', Tint16),
] + m(('手动选择参战人', '自动选择参战人', '我方X', '我方Y'), config.maxTeamMemberNumber)
  + m(('敌人', '敌方X', '敌方Y'), config.maxCombatEnemyNumber)
)


class FilePair:
    MODE_READ = 'rb'
    MODE_WRITE = 'wb'

    def __init__(self, filename, mode=MODE_READ):
        self.mode = mode
        idxName = config.resource('data', filename + '.idx') 
        grpName = config.resource('data', filename + '.grp')

        if mode == self.MODE_READ:
            self.idxs = array.array('I', open(idxName, 'rb').read())
            self.idxs.append(0)
            self.grpFile = open(grpName, 'rb')
            self.pos = -1
        elif mode == self.MODE_WRITE:
            self.idxs = []
            self.idxFile = open(idxName, 'wb')
            self.grpFile = open(grpName, 'wb')

    def read_block(self):
        assert self.mode == self.MODE_READ
        idxs = self.idxs
        self.pos += 1
        p = self.pos
        return self.grpFile.read(idxs[p] - idxs[p - 1])

    def write_block(self, data):
        assert self.mode == self.MODE_WRITE
        last = self.idxs[-1] if self.idxs else 0
        self.idxs.append(last + len(data))
        self.grpFile.write(data)

    def __del__(self):
        if self.mode == self.MODE_READ:
            self.grpFile.close()
        elif self.mode == self.MODE_WRITE:
            self.idxFile.write(array.array('I', self.idxs).tobytes())
            self.idxFile.close()
            self.grpFile.close()

def open_grp(type, suffix, mode):
    return open(config.resource('data', '{}{}.grp'.format(type, suffix)), mode)


class Record(UserDict):
    STRUCTS = [
        structMisc, structPlayer, structItem, structScene, structSkill, structShop,
    ]

    @staticmethod
    def load(suffix):
        self = Record()
        try:
            rFilePair = FilePair('r' + suffix)
            sceneFile = open_grp('s', suffix, 'rb')
            eventFile = open_grp('d', suffix, 'rb')
        except FileNotFoundError:
            raise RecordNotExistError()

        # parse r fild
        for i, st in enumerate(self.STRUCTS):
            block = rFilePair.read_block()
            # print(st.name, len(block) / st.size)
            data = [
                st.load(block[j:j + st.size]) for j in range(0, len(block), st.size)
            ]
            self[st.name] = data
        del rFilePair

        sceneMetas = [FrozenDict(meta) for meta in self[structScene.name]]
        self.scenes = SceneGroup.load(sceneMetas, sceneFile, eventFile)
        return self

    def save(self, suffix):
        rFilePair = FilePair('r' + suffix, FilePair.MODE_WRITE)
        for st in self.STRUCTS:
            data = b''.join(st.save(x) for x in self[st.name])
            rFilePair.write_block(data)
        del rFilePair

        sceneFile = open_grp('s', suffix, 'wb')
        eventFile = open_grp('d', suffix, 'wb')
        self.scenes.save(sceneFile, eventFile)
        sceneFile.close()
        eventFile.close()
