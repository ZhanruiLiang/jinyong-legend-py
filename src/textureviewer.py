import fonts
from texture import TextureGroup
import config
import pygame as pg
import utils

def viewer(init=None):
    import os
    names = []
    allT = {}
    for f in os.listdir(config.resource('data')):
        name, ext = os.path.splitext(f)
        if ext == '.grp':
            names.append(name)
    excludes = [
        'danger', 'sanger', 'ranger', 'alldef', 'allsin', 'allsinbk', 
        'warfld', 's1', 's2', 's3', 'r1', 'r2', 'r3', 'd1', 'd2', 'd3', 
        'r9', 'd9', 's9',
    ]
    for name in excludes:
        names.remove(name)
    names.sort()
    print(names)
    if init is None:
        idx = 0
    else:
        idx = names.index(init)

    pg.display.init()
    pg.font.init()
    screen = pg.display.set_mode((800, 600), 0, 32)

    font = fonts.get_default_font(16)

    def draw(idx_new):
        nonlocal idx
        idx = idx_new % len(names)
        name = names[idx]
        if name not in allT:
            allT[name] = TextureGroup(name)
        textures = allT[name]
        print(len(textures.idxs) - 1)

        utils.clear_surface(screen)
        w, h = screen.get_size()
        x, y = 0, 0
        rowMaxH = 0
        margin = 2
        for id, texture in textures.iter_all():
            image = texture.image
            w1, h1 = image.get_size()
            if x + w1 < w:
                screen.blit(image, (x, y))
                rowMaxH = max(rowMaxH, h1)
            else:
                x = 0
                y += rowMaxH + margin
                if y >= screen.get_height():
                    break
                rowMaxH = 0
            screen.blit(image, (x, y))
            screen.blit(font.render(str(id), 1, (0, 0xff, 0)), (x, y))
            x += w1 + margin
        textSize = font.size(name)
        rect = pg.Rect((0, 0), (textSize[0], textSize[1]))
        rect.right = screen.get_width() - 10
        rect.bottom = screen.get_height() - 10
        screen.blit(font.render(name, 1, (0xff, 0xff, 0xff)), rect)
        pg.display.update()

    tm = pg.time.Clock()
    draw(idx)
    while 1:
        for event in pg.event.get():
            if event.type == pg.QUIT \
                    or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RIGHT:
                    draw(idx + 1)
                elif event.key == pg.K_LEFT:
                    draw(idx - 1)
        tm.tick(config.FPS)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        viewer()
    else:
        viewer(sys.argv[1])
