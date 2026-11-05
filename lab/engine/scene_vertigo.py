# -*- coding: utf-8 -*-
"""БЛОК 15 — ДОЛЛИ-ЗУМ («эффект Вертиго»). Герой не меняется, мир наваливается.

Камера ОТЪЕЗЖАЕТ, а фокусное растёт ровно настолько, чтобы герой остался того
же размера: `f = f0 * dist/dist0`. Размер субъекта на экране `f*h/dist` при
этом постоянен, зато задний план из широкоугольного становится длиннофокусным
и наезжает на героя. Зритель видит невозможное: человек стоит, а пространство
за ним сжимается. Приём «один раз в ролике» и только под сильный смысл.

Это НЕ зум-аут: субъект не уменьшается ни на пиксель, уходит только
перспектива. Поэтому запрет на зум-аут приём не задевает.

Числа клипа: удаление 620 → 1500 (в 2,4 раза), фокус 1250 → 3024, угол обзора
по горизонтали с 75° до 35°.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import W, H, FPS, new_frame, finish, lerp, clamp, smoother
from skel3d import Cam3, body
import place
from place import HMAN, BG3

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

AIM  = np.array([0.0, 300.0, 180.0])
DIR  = np.array([-0.0896, 0.0697, -0.9956])
DIST = (620.0, 1500.0)
F0   = 1250.0
HERO = (0.0, 180.0, "dodge", 10.0, 1.04)


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    dist = lerp(*DIST, k)
    cam = Cam3(tuple(AIM + DIR*dist), tuple(AIM), f=F0*dist/DIST[0])
    im, d = new_frame(BG3 + (255,))
    x, z, pose, yaw, hk = HERO
    prims = body(HMAN*hk, pose, yaw, (x, 0.0, z))
    place.draw(im, d, cam, extra=((prims, HMAN*hk),),
               z0=-1900.0, z1=4400.0, x_half=3000.0)
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
