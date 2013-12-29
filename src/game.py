import config
import pygame as pg
import menu
import sound
from sprite import Picture


class GameState:
    MENU = 0
    FIRST_MAIN_MAP = 1
    MAIN_MAP = 3
    FIRST_SCENE_MAP = 4
    SCENE_MAP = 5
    COMBAT_MAP = 6
    DEAD = 7
    EXIT = 8


class StartMenu(menu.Menu):
    def __init__(self, game):
        @self.add_item('重新开始')
        def create_profile():
            pass

        @self.add_item('载入进度')
        def load():
            pass

        @self.add_item('离开游戏')
        def quit():
            game.quit()

        super().__init__(
            config.defaultFont, config.startMenuFontSize,
            False,  # need box ?
            config.colorMenuItem, config.colorMenuItemSelected,  # item colors
        )


class ProfileMenu(menu.Menu):
    def __init__():
        pass


class Game:
    def init_sdl(self):
        pg.display.init()
        pg.font.init()
        pg.mixer.init()

        size = (config.screenWidth, config.screenHeight)
        if config.fullscreenEnable:
            flags = pg.FULLSCREEN | pg.HWSURFACE | pg.DOUBLEBUF
        else:
            flags = pg.SWSURFACE
        self.screen = pg.display.set_mode(size, flags, 32)

        pg.key.set_repeat(config.keyRepeatDelayTime, config.keyRepeatInterval)

    def exit_sdl(self):
        pg.quit()

    def init_game(self):
        self.state = GameState.MENU

    def exit_game(self):
        pass

    def run(self):
        self.init_sdl()
        self.init_game()

        self.show_main_menu()
        tm = pg.time.Clock()
        while self.state is not GameState.EXIT:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    self.on_key_down(event.key)
                elif event.type == pg.QUIT:
                    self.quit()
            if self.state is GameState.MENU:
                self.currentMenu.update()
            self.render()
            tm.tick(config.FPS)

        self.exit_game()
        self.exit_sdl()

    def show_main_menu(self):
        sound.play_music('start')
        self.set_menu(StartMenu(self))
        self.background = Picture('title.png')

    def quit(self):
        self.state = GameState.EXIT

    def set_menu(self, menu):
        self.currentMenu = menu
        menu.rect.left = int(
            (self.screen.get_width() - menu.image.get_width()) / 2)
        menu.rect.bottom = self.screen.get_height() - 20

    def on_key_down(self, key):
        if self.state is GameState.MENU:
            self.currentMenu.on_key_down(key)

    def render(self):
        if self.state is GameState.MENU:
            pg.display.update([
                self.draw_sprite(self.background),
                self.draw_sprite(self.currentMenu),
            ])
        else:
            self.screen.fill((0, 0, 0, 0))
            # TODO
            pg.display.update()

    def draw_sprite(self, sp):
        return self.screen.blit(sp.image, sp.rect)

    def show_update_rects(self, update_rects):
        for rect in update_rects:
            if not rect: 
                continue
            pg.draw.rect(self.screen, (100, 100, 200), rect, 1)


if __name__ == '__main__':
    game = Game()
    game.run()
