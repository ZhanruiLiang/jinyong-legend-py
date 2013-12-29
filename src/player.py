import pygame as pg
import sprite
import config
import utils
import random

class Player:
    pass

def new_random_profile():
    attributes = [
        ("内力性质", 0, 2),
        ("内力最大值", 21, 20),
        ("攻击力", 21, 10),
        ("防御力", 21, 10),
        ("轻功", 21, 10),
        ("医疗能力", 21, 10),
        ("用毒能力", 21, 10),
        ("解毒能力", 21, 10),
        ("抗毒能力", 21, 10),
        ("拳掌功夫", 21, 10),
        ("御剑能力", 21, 10),
        ("耍刀技巧", 21, 10),
        ("特殊兵器", 21, 10),
        ("暗器技巧", 21, 10),
        ("生命增长", 3, 5),
    ]

    def rnd(x):
        return random.randint(0, x - 1)

    profile = {}
    for name, base, r in attributes:
        profile[name] = base + rnd(r)
    profile["生命最大值"] = profile["生命增长"] * 3 + 29

    rate = random.randint(0, 9)
    if rate < 2:
        profile["资质"] = rnd(35) + 30
    elif rate < 8:
        profile["资质"] = rnd(20) + 60
    else:
        profile["资质"] = rnd(20) + 75

    return profile
