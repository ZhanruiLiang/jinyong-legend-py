import config
import pygame as pg
import menu
import sound


class GameState:
    MENU = 0
    FIRST_MAIN_MAP = 1
    MAIN_MAP = 3
    FIRST_SCENE_MAP = 4
    SCENE_MAP = 5
    COMBAT_MAP = 6
    DEAD = 7
    EXIT = 8


class Character:
    pass


class Game:
    def init_sdl(self):
        pg.display.init()
        pg.font.init()
        pg.mixer.init()

        size = (config.screenWidth, config.screenHeight)
        flags = 0 | (pg.FULLSCREEN if config.fullscreen else 0)
        self.screen = pg.display.set_mode(size, flags, 32)

        pg.key.set_repeat(config.keyRepeatDelayTime, config.keyRepeatInterval)

    def exit_sdl(self):
        pg.quit()

    def init_game(self):
        self.state = GameState.MENU
        self.mainLoopFunc = self.menu_main_loop

    def exit_game(self):
        pass

    def run(self):
        self.init_sdl()
        self.init_game()

        self.mainLoopFunc()

        self.exit_game()
        self.exit_sdl()

    def MI_create_profile(self):
        pass

    def MI_load(self):
        pass

    def MI_quit(self):
        self.quit()

    def quit(self):
        self.state = GameState.EXIT

    def menu_main_loop(self):
        items = [
            ('重新开始', self.MI_create_profile),
            ('载入进度', self.MI_load),
            ('离开游戏', self.MI_quit),
        ]

        startMenu = menu.StartMenu(items, (0, 0))
        self.menu = startMenu
        startMenu.rect.left = int(
            (self.screen.get_width() - startMenu.image.get_width()) / 2)
        startMenu.rect.bottom = self.screen.get_height() - 20

        tm = pg.time.Clock()

        sound.play_midi('start')
        while self.state is not GameState.EXIT:
            for event in pg.event.get():
                # for debug only
                # if event.type == pg.KEYDOWN and event.key == pg.K_a:
                #     pg.image.save(self.screen, 'a.png')
                # elif event.type == pg.KEYDOWN and event.key == pg.K_b:
                #     pg.image.save(self.screen, 'b.png')
                if event.type == pg.KEYDOWN:
                    self.menu.on_key_down(event.key)
                elif event.type == pg.QUIT:
                    self.quit()
            self.screen.fill((0, 0, 0, 0))
            updateRects = []
            updateRects.append(
                self.menu.update())
            updateRects.append(
                self.screen.blit(self.menu.image, self.menu.rect))
            pg.display.update(updateRects)
            tm.tick(config.FPS)

    def show_update_rects(self, update_rects):
        for rect in update_rects:
            if not rect: 
                continue
            pg.draw.rect(self.screen, (100, 100, 200), rect, 1)

    def game_main_loop(self):
        tm = pg.time.Clock()
        while self.state is not GameState.EXIT:
            tm.tick(config.FPS)
            pg.display.update()

if __name__ == '__main__':
    game = Game()
    game.run()
