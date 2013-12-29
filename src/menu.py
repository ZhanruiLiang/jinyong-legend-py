import pygame as pg
import config
import fonts
import sprite


class Menu(sprite.Sprite):
    def __init__(
            self, font_name, font_size, 
            need_box, color, selected_color):
        """
        items: List of (name, callback) tuples
        need_box: draw box or not
        color: normal item color
        selected_color: selected item color
        """
        super().__init__()
        self.font = fonts.get_font(font_name, font_size)
        self.color = color
        self.selectedColor = selected_color
        self.needBox = need_box
        self.items = [
            self.make_item(name, callback, color) 
            for (name, callback) in self.items]
        self.currentIdx = 0
        self.change_color(self.currentIdx, self.selectedColor)

        self.rect = self.make_rect(self.items)
        self.image = pg.Surface(self.rect.size).convert_alpha()
        self._dirty = True

    def make_item(self, name, callback, color):
        fontSurf = self.font.render(
            name,  # text
            config.fontAntiAliasEnable,  # antialias
            color,  # color
        )
        return (name, callback, fontSurf)

    def make_rect(self, items):
        width = config.menuMarginLeft + config.menuMarginRight \
            + max(fontSurf.get_width() for (_, _, fontSurf) in items)
        height = config.menuMarginTop + config.menuMarginBottom \
            + sum(fontSurf.get_height() + config.menuItemMarginBottom 
                for (_, _, fontSurf) in items)
        return pg.Rect((0, 0), (width, height))

    def escape(self):
        pass

    def on_key_down(self, key):
        if key == pg.K_ESCAPE:
            self.escape()
        elif key in (pg.K_RETURN, pg.K_SPACE):
            _, callback, _ = self.items[self.currentIdx]
            callback()
        elif key == pg.K_UP:
            self._dirty = True
            self.select(self.currentIdx - 1)
        elif key == pg.K_DOWN:
            self._dirty = True
            self.select(self.currentIdx + 1)

    def select(self, idx):
        idx %= len(self.items)
        oldIdx = self.currentIdx
        self.change_color(oldIdx, self.color)
        self.change_color(idx, self.selectedColor)
        self.currentIdx = idx

    def change_color(self, idx, color):
        name, callback, _ = self.items[idx]
        self.items[idx] = self.make_item(name, callback, color)

    def update(self):
        if self._dirty:
            image = self.image
            image.fill((0, 0, 0, 0))
            if self.needBox:
                # Draw background.
                pg.draw.rect(image, config.colorMenuBackground, self.rect)
                # Draw box border with width 2.
                pg.draw.rect(image, config.colorWhite, self.rect, 2)
            x, y = config.menuMarginLeft, config.menuMarginTop
            for (_, _, fontSurf) in self.items:
                image.blit(fontSurf, (x, y))
                y += fontSurf.get_height() + config.menuItemMarginBottom
            self._dirty = False
            return self.rect
        return None

    def add_item(self, name, callback=None):
        if not hasattr(self, 'items'):
            self.items = []
        if callback is None:
            def decorator(callback):
                self.items.append((name, callback))
                return callback
            return decorator
        else:
            self.items.append((name, callback))
