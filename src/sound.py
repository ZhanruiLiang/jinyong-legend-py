import pygame as pg
import config

soundMap = {
    'start': 16,
}

currentName = None


def play_music(name):
    if not config.musicEnable:
        return
    global currentName
    if name == currentName:
        return
    stop_music()
    filename = config.resource('sound', 
            'game{:02d}.ogg'.format(soundMap['start']))
    try:
        pg.mixer.music.load(filename)
        pg.mixer.music.set_volume(config.musicVolume)
        pg.mixer.music.play()
    except pg.error:
        pass

def stop_music():
    pg.mixer.music.stop()
