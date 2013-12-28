import os

resourceRoot = 'resource'


def resource(*subpaths):
    return os.path.join(resourceRoot, *subpaths)

FPS = 30

screenWidth = 640
screenHeight = 480
fullscreen = 0
musicVolume = 32
soundVolume = 32
textureXScale = 18
textureYScale = 9
keyRepeatDelayTime = 200
keyRepeatInterval = 100
talkfile = resource('talk', 'oldtalk.grp')
soundDir = resource('sound')
menuMarginLeft = menuMarginRight = menuMarginTop = menuMarginBottom = 4
menuItemMarginBottom = 2
startMenuFontSize = 32

# colors
colorMenuItem = (132, 0, 4, 255)
colorMenuItemSelected = (216, 20, 40, 255)
colorMenuBackground = (128, 128, 128, 128)
colorWhite = (236, 236, 236, 255)
colorOrange = (252, 148, 16, 255)
colorGold = (236, 200, 40, 255)
colorBlack = (0, 0, 0, 255)

# fonts
# defaultFont = 'bkai00mp.ttf'
# defaultFont = 'wqy-microhei.ttc'
defaultFont = 'ukai.ttc'
fontDir = resource('font')
