import os

resourceRoot = 'resource'


def resource(*subpaths):
    return os.path.join(resourceRoot, *subpaths)

FPS = 20

screenWidth = 640
screenHeight = 480
fullscreenEnable = 0
musicVolume = 32
soundVolume = 32
textureXScale = 18
textureYScale = 9
keyRepeatDelayTime = 200
keyRepeatInterval = 100
talkfile = resource('talk', 'oldtalk.grp')
menuMarginLeft = menuMarginRight = menuMarginTop = menuMarginBottom = 4
menuItemMarginBottom = 2
startMenuFontSize = 32

# colors
palletteFile = resource('data', 'mmap.col')
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
portraitFilename = 'hdgrp'
sceneMapFilename = 'smap'

# scene
sceneMapXMax = 64
sceneMapYMax = 64
sceneNum = 200
eventNumPerScene = 200
sceneCacheNum = 8
