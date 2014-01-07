import os
import pygame as pg
import pyximport
pyximport.install()

os.environ['SDL_VIDEO_CENTERED'] = '1'

resourceRoot = 'resource'

class Directions:
    all = (right, down, left, up) = ((1, 0), (0, 1), (-1, 0), (0, -1))

def resource(*subpaths):
    return os.path.join(resourceRoot, *subpaths)

debug = 1

FPS = 60
showFPS = 1
smoothTicks = 1
drawFloor = 1

# screenWidth, screenHeight = 160, 120
# screenWidth, screenHeight = 320, 240
screenWidth, screenHeight = 640, 480
# screenWidth, screenHeight = 800, 600
# screenWidth, screenHeight = 1366, 768

depthBits = 32

fullscreenEnable = 0
musicVolume = 32
soundVolume = 32
textureXScale = 18
textureYScale = 9
keyRepeatDelayTime = 50
keyRepeatInterval = 20
talkfile = resource('talk', 'oldtalk.grp')
menuMarginLeft = menuMarginRight = menuMarginTop = menuMarginBottom = 4
menuItemMarginBottom = 2

debugMargin = 0
drawDebugRect = True
bottomPadding = textureYScale * 32

# colors
palletteFile = resource('data', 'mmap.col')
colorKey = (11, 22, 33)
colorMenuItem = (132, 0, 4, 255)
colorMenuItemSelected = (216, 20, 40, 255)
colorMenuBackground = (128, 128, 128, 128)
colorWhite = (236, 236, 236, 255)
colorRed = (216, 20, 24, 255)
colorOrange = (252, 148, 16, 255)
colorGold = (236, 200, 40, 255)
colorBlack = (0, 0, 0, 255)
colorFontShadow = (50, 50, 50, 100)

# fonts
# defaultFont = 'bkai00mp.ttf'
# defaultFont = 'wqy-microhei.ttc'
defaultFont = 'ukai.ttc'
defaultFontSize = 16
menuFontSize = 32
fontAntiAliasEnable = False

# sound effect
soundEffectEnable = True
soundEffectVolume = 0.6

# music
musicEnable = True
musicVolume = 0.6

nSaveSlots = 4

# restrictions
maxTeamMemberNumber = 6
maxItemNumber = 200
maxCombatEnemyNumber = 20

# textures
#  If textureGroupPreloadAll is set to True, then all textures in this group
#  will be parsed when initializing.
textureGroupPreloadAll = 0
portraitFilename = 'hdgrp'
sceneMapFilename = 'smap'

# scene
sceneMapXMax = 64
sceneMapYMax = 64
sceneNum = 200
eventNumPerScene = 200
sceneCacheNum = 8

# main map
mainMapXMax = 480
mainMapYMax = 480
mainMapCacheSize = 2 ** 14

directionKeyMap = {
    pg.K_UP: Directions.up, 
    pg.K_DOWN: Directions.down,
    pg.K_LEFT: Directions.left,
    pg.K_RIGHT: Directions.right,
}

# combat map
combatMapXMax = 64
combatMapYMax = 64
combatMapCacheNum = 16

# Packer
packerAutoTranspose = 1
dataFile = resource('data', 'data.dat')
