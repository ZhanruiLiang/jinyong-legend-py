import pygame as pg
import config
import os

soundMap = {
    'start': 16,
}

currentName = None


def play_midi(name):
    global currentName
    if name == currentName:
        return
    stop_midi()
    filename = os.path.join(
        config.soundDir, 'game{:02d}.ogg'.format(soundMap['start']))
    pg.mixer.music.load(filename)
    pg.mixer.music.play()


def stop_midi():
    pg.mixer.music.stop()
