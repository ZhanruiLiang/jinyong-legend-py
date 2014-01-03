import pygame as pg
import utils


pg.display.init()
size = w, h = 800, 600
bits = 32

flags = pg.HWSURFACE | pg.DOUBLEBUF
screen = pg.display.set_mode(size, flags, 32)
screen.fill((0xff, 0xff, 0xff))

surface = screen.copy()

image = screen.copy()
image.set_colorkey((1, 1, 1))
image.fill((1, 1, 1))
pg.draw.rect(image, (0, 0, 0), ((int(w / 4), int(h / 4)), (int(w / 2), int(h / 2))))

T = 1000

@utils.timeit(T)
def blit_on_screen():
    screen.blit(image, (0, 0))

@utils.timeit(T)
def blit_on_surface():
    surface.blit(image, (0, 0))

blit_on_screen()
blit_on_surface()
