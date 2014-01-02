import config
import pygame as pg
import sound
import player
import utils
from sprite import Picture
from record import Record, RecordNotExistError
from menu import BaseMenu, menuitem
from mainmap import MainMap


class GameState:
    MENU = 0
    FIRST_MAIN_MAP = 1
    MAIN_MAP = 3
    FIRST_SCENE_MAP = 4
    SCENE_MAP = 5
    COMBAT_MAP = 6
    DEAD = 7
    EXIT = 8


class Misc:
    """
Attributes:
    boating
    unused
    playerX
    playerY
    playerX1
    playerY1
    playerDir
    boatX
    boatY
    boatX1
    boatY1
    boatDir
    members
    items
    """
    ATTRS = [
        ('boating', '乘船'), ('unused', '无用'), 
        ('playerX', '人X'), ('playerY', '人Y'),
        ('playerX1', '人X1'), ('playerY1', '人Y1'), ('playerDir', '人方向'),
        ('boatX', '船X'), ('boatY', '船Y'), 
        ('boatX1', '船X1'), ('boatY1', '船Y1'), ('boatDir', '船方向'),
    ]

    def __init__(self, data):
        subdata = data['misc'][0]
        for name1, name2 in self.ATTRS:
            setattr(self, name1, subdata[name2])
        self.members = [
            subdata['队伍' + str(i)] 
            for i in range(config.maxTeamMemberNumber)
        ]
        self.items = [
            ('物品' + str(i), '物品数量' + str(i))
            for i in range(config.maxItemNumber)
        ]

    def save(self, data):
        subdata = data['misc'][0]
        for name1, name2 in self.ATTRS:
            subdata[name2] = getattr(self, name1)
        for i, x in enumerate(self.members):
            subdata['队伍' + str(i)] = x
        for i, x in enumerate(self.items):
            subdata['物品' + str(i)] = x[0]
            subdata['物品数量' + str(i)] = x[1]


class StartMenu(BaseMenu):
    need_box = False

    @menuitem('重新开始')
    def create_profile(self):
        self.game.set_menu(ProfileMenu(game))

    @menuitem('载入进度')
    def load(self):
        self.game.set_menu(LoadMenu(game))

    @menuitem('离开游戏')
    def quit(self):
        self.game.quit()


class ProfileMenu(BaseMenu):
    HORIZONTAL_MARGIN = 2
    TABLE = [
        [("内力", "内力最大值"), ("攻击", "攻击力"), ("轻功", "轻功"), ("防御", "防御力")],
        [("生命", "生命最大值"), ("医疗", "医疗能力"), ("用毒", "用毒能力"), ("解毒", "解毒能力")],
        [("拳掌", "拳掌功夫"), ("御剑", "御剑能力"), ("耍刀", "耍刀技巧"), ("暗器", "暗器技巧")],
    ]

    selected_color = config.colorWhite

    @menuitem('是')
    def yes(self):
        game.new_game()

    @menuitem('否')
    def no(self):
        self.generate()

    def make_rect(self, items):
        width = max(
            sum(self.HORIZONTAL_MARGIN + self.font.size(name + ' 00')[0]
                for (name, _) in line) 
            for line in self.TABLE
        ) + config.menuMarginLeft + config.menuMarginRight
        return pg.Rect((0, 0), (width, 180))

    def draw(self):
        utils.clear_surface(self.image)
        x, y = (config.menuMarginLeft, config.menuMarginRight)
        w1, h1 = self.font.size('拳掌00')
        w1 += self.HORIZONTAL_MARGIN

        def draw_text(text, color):
            nonlocal x, y
            self.image.blit(
                self.font.render(text, config.fontAntiAliasEnable, color),
                (x, y),
            )
            x += self.font.size(text)[0] + self.HORIZONTAL_MARGIN

        def new_line():
            nonlocal x, y
            x = config.menuMarginLeft
            y += h1 + config.menuItemMarginBottom

        draw_text('这样的属性满意吗?', config.colorGold)
        for (_, _, fontSurf) in self.items:
            self.image.blit(fontSurf, (x, y))
            x += self.HORIZONTAL_MARGIN + fontSurf.get_width()

        profile = self.profile
        for line in self.TABLE:
            new_line()
            for sortName, attribute in line:
                draw_text(sortName, config.colorRed)
                draw_text(str(profile[attribute]), config.colorWhite) 

    def generate(self):
        self.profile = player.new_random_profile()
        self._dirty = True


class LoadMenu(BaseMenu):
    for i in range(config.nSaveSlots):
        exec(
            "@menuitem('进度' + utils.number_to_chinese(i + 1))\n" +
            "def load_{}(self, i=i):\n".format(i) +
            "    self.game.load_record(str(i + 1))"
        )


class Game:
    """
Attributes:
    player
    misc
    items
    scenes
    skills
    shops
    """
    def init_pg(self):
        pg.display.init()
        pg.font.init()
        pg.mixer.init()

        size = (config.screenWidth, config.screenHeight)
        if config.fullscreenEnable:
            flags = pg.FULLSCREEN | pg.HWSURFACE | pg.DOUBLEBUF
        else:
            flags = pg.SWSURFACE | pg.DOUBLEBUF
        self.screen = pg.display.set_mode(size, flags, config.depthBits)

        pg.key.set_repeat(config.keyRepeatDelayTime, config.keyRepeatInterval)
        pg.mouse.set_visible(False)

    def init(self):
        self.init_pg()

        self.currentMenu = None
        self.currentMap = None
        self._keyCallbacks = []
        self.add_key_callback(debugger)

    def clean_up(self):
        if self.currentMap:
            self.currentMap.quit()
        pg.quit()

    def play(self):
        self.state = GameState.MENU
        self.background = Picture('title.png')
        sound.play_music('start')

        # self.set_menu(StartMenu(self))
        self.set_menu(LoadMenu(self))
        self.loop()

    def loop(self):
        tm = pg.time.Clock()
        self.round = 0
        while self.state is not GameState.EXIT:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    self.on_key_down(event.key, event.mod)
                elif event.type == pg.QUIT:
                    self.quit()
            self.logic()
            self.render()
            tm.tick(config.FPS)
            if config.showFPS and self.round % 30 == 0:
                    utils.debug('FPS:', tm.get_fps())
            self.round += 1

        self.clean_up()

    def quit(self):
        self.state = GameState.EXIT

    def set_menu(self, menu):
        self.currentMap = menu
        menu.rect.left = int(
            (self.screen.get_width() - menu.image.get_width()) / 2)
        menu.rect.bottom = self.screen.get_height() - 20

    def on_key_down(self, key, mod):
        if self.state is GameState.MENU:
            self.currentMenu.on_key_down(key)
        elif self.state in (GameState.SCENE_MAP, GameState.MAIN_MAP):
            if key == pg.K_ESCAPE:
                self.quit()
            if key in config.directionKeyMap:
                if not mod:
                    self.currentMap.move(config.directionKeyMap[key])
        for callback in self._keyCallbacks:
            callback(self, key, mod)

    def add_key_callback(self, callback):
        """
        callback: A callable with arguments, (game, key, mod)
        """
        self._keyCallbacks.append(callback)

    def render(self):
        screen = self.screen
        state = self.state
        if state is GameState.MENU:
            pg.display.update([
                self.draw_sprite(self.background),
                self.draw_sprite(self.currentMenu),
            ])
        elif state in (GameState.SCENE_MAP, GameState.MAIN_MAP):
            screen.fill((0, 0, 0))
            map = self.currentMap
            screen.blit(map.image, map.rect)
            if config.debugMargin:
                rect = pg.Rect((config.debugMargin, config.debugMargin),
                    (config.screenWidth - 2 * config.debugMargin,
                     config.screenHeight - 2 * config.debugMargin),
                )
                pg.draw.rect(screen, (0xff, 0, 0), rect, 2)

            pg.display.update()
        else:
            # TODO
            pg.display.update()

    def logic(self):
        if self.state is GameState.MENU:
            self.currentMenu.update()
        elif self.state in (GameState.SCENE_MAP, GameState.MAIN_MAP):
            self.currentMap.update()

    def draw_sprite(self, sp):
        return self.screen.blit(sp.image, sp.rect)

    def show_update_rects(self, update_rects):
        for rect in update_rects:
            if not rect: 
                continue
            pg.draw.rect(self.screen, (100, 100, 200), rect, 1)

    def configure(self, record):
        self.misc = Misc(record)
        self.player = player.Player(record)
        self.scenes = record.scenes
        # print('\n'.join(str(x['名称']) for x in record['scene']))

    def load_record(self, name):
        try:
            record = Record.load(name)
        except RecordNotExistError:
            utils.debug('Record "{}" not exist'.format(name))
            return
        utils.debug('Record "{}" loaded'.format(name))
        self.configure(record)

    def save_record(self, name):
        # record = self.make_record()
        # record.save(name)
        pass

    def new_game(self):
        self.configure(Record.load('ranger'))

    def enter_main_map(self):
        self.state = GameState.MAIN_MAP
        self.currentMap = MainMap.get_instance()
        self.currentMap.move_to((200, 200))
        utils.debug("enter main map")

    def enter_scene(self, id):
        self.state = GameState.SCENE_MAP
        if isinstance(id, int):
            scene = self.scenes.get(id)
        elif isinstance(id, str):
            scene = self.scenes.get_by_name(id)
        else:
            raise KeyError('unknown id: {}'.format(id))
        scene.move_to(scene.entrance)
        utils.debug("enter scene:", scene.name)

        self.currentMap = scene

def debugger(game, key, mod):
    if key == pg.K_f:
        pg.display.toggle_fullscreen()
    elif key == pg.K_g:
        config.drawFloor = not config.drawFloor
    elif mod & pg.KMOD_CTRL and key in config.directionKeyMap:
        if game.state in (GameState.SCENE_MAP, GameState.MAIN_MAP):
            dx, dy = config.directionKeyMap[key]
            x, y = game.currentMap.currentPos
            d = 5
            game.currentMap.move_to((x + dx * d, y + dy * d))

if __name__ == '__main__':
    game = Game()
    game.init()
    game.play()
