import pygame as pg
import config
import fonts
import sprite

pg.font.init()

class MenuItem:
    def __init__(self, parent, name, callback):
        self.name = name
        self.callback = callback
        self.selected = False
        self.parent = parent
        self._surfaces = [None, None]

    @property
    def fontSurf(self):
        surface = self._surfaces[self.selected]
        if surface is None:
            color = self.parent.color if not self.selected \
                else self.parent.selected_color
            surface = self.parent.font.render(
                self.name,  # text
                config.fontAntiAliasEnable,  # antialias
                color,  # color
            )
            self._surfaces[self.selected] = surface
        return surface


class MenuMeta(type):
    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        items = []
        for name, method in dict.items(): 
            if hasattr(method, 'item_name'):
                items.append(MenuItem(cls, method.item_name, method))
        items.sort(key=lambda item: item.callback.item_id)
        cls.items = items
        cls.font = fonts.get_font(cls.font_name, cls.font_size)


class BaseMenu(sprite.Sprite, metaclass=MenuMeta):
    font_name = config.defaultFont
    font_size = config.menuFontSize
    need_box = False
    color = config.colorMenuItem
    selected_color = config.colorMenuItemSelected

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.currentIdx = 0
        self.select(0)

        self.rect = self.make_rect(self.items)
        self.image = pg.Surface(self.rect.size).convert_alpha()
        self._dirty = True

    def make_rect(self, items):
        width = config.menuMarginLeft + config.menuMarginRight \
            + max(item.fontSurf.get_width() for item in items)
        height = config.menuMarginTop + config.menuMarginBottom \
            + sum(item.fontSurf.get_height() + config.menuItemMarginBottom 
                for item in items)
        return pg.Rect((0, 0), (width, height))

    def select(self, idx):
        idx %= len(self.items)
        oldIdx = self.currentIdx
        self.items[oldIdx].selected = False
        self.items[idx].selected = True
        self.currentIdx = idx

    def escape(self):
        pass

    def on_key_down(self, key):
        if key == pg.K_ESCAPE:
            self.escape()
        elif key in (pg.K_RETURN, pg.K_SPACE):
            self.items[self.currentIdx].callback(self)
        elif key in (pg.K_UP, pg.K_LEFT):
            self._dirty = True
            self.select(self.currentIdx - 1)
        elif key in (pg.K_DOWN, pg.K_RIGHT):
            self._dirty = True
            self.select(self.currentIdx + 1)

    def update(self):
        if self._dirty:
            self.draw()
            self._dirty = False
            return self.rect
        return None

    def draw(self):
        image = self.image
        image.fill((0, 0, 0, 0))
        if self.need_box:
            # Draw background.
            pg.draw.rect(image, config.colorMenuBackground, self.rect)
            # Draw box border with width 2.
            pg.draw.rect(image, config.colorWhite, self.rect, 2)
        # draw items
        x, y = config.menuMarginLeft, config.menuMarginTop
        for item in self.items:
            image.blit(item.fontSurf, (x, y))
            y += item.fontSurf.get_height() + config.menuItemMarginBottom

_idcount = 0
def menuitem(name):
    def decorator(callback):
        global _idcount
        callback.item_name = name
        callback.item_id = _idcount
        _idcount += 1
        return callback
    return decorator
