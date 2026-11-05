# -*- coding: utf-8 -*-
"""БЛОК 13 — СНИЖЕНИЕ С ВЫСОТЫ К ГЕРОЮ (обратный кран).

Кран вверх (блок 7) раскрывает место. Снижение делает обратное: начинает над
крышами, где видно всё, и приводит зрителя к одному человеку. Это НЕ зум-аут —
камера всё время ПРИБЛИЖАЕТСЯ, просто приходит сверху вниз. Ход один,
медленный, со смягчёнными концами.

Чем держится: по дороге вниз у домов закрываются крыши и открываются фасады,
сетка земли из плана превращается в перспективу, тень героя из пятна рядом
становится пятном у ног. На пустом фоне снижение не читается.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import W, H, FPS, new_frame, finish, clamp, smoother
from skel3d import Cam3, body
import place
from place import HMAN, BG3

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

EYE0 = np.array([0.0, 1010.0, -1180.0])
EYE1 = np.array([0.0,  235.0,  -430.0])
AIM0 = np.array([0.0,  560.0,  1400.0])      # сначала смотрим на крыши
AIM1 = np.array([0.0,  300.0,   180.0])      # приходим к груди героя
HERO = (0.0, 180.0, "dodge", 10.0, 1.04)


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    cam = Cam3(tuple(EYE0 + (EYE1 - EYE0)*k), tuple(AIM0 + (AIM1 - AIM0)*k))
    im, d = new_frame(BG3 + (255,))
    x, z, pose, yaw, hk = HERO
    prims = body(HMAN*hk, pose, yaw, (x, 0.0, z))
    place.draw(im, d, cam, extra=((prims, HMAN*hk),),
               z0=-1600.0, z1=4400.0, x_half=3000.0)
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
