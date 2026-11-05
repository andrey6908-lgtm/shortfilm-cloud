# -*- coding: utf-8 -*-
"""БЛОК 14 — НАКЛОН ГОРИЗОНТА (dutch angle). Самый дешёвый приём из всех.

Меняется ОДИН параметр камеры — вектор «верх»: он отклоняется от вертикали, и
весь кадр валится набок. Ни новой геометрии, ни новых предметов. Зритель не
видит причины и читает это как тревогу: что-то не так.

Как ставить: наклон НЕ включается рывком и не держится весь ролик. В клипе он
накапливается с 0 до 9° по ходу медленного подъезда — то есть кадр валится
ровно пока нарастает смысл. Потолок 9-10°: дальше читается как ошибка, а не
как приём.
"""
import os, sys, math
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
DIST = (1150.0, 1040.0)             # медленный подъезд, ~1%/с
ROLL = (0.0, 9.0)                   # наклон горизонта, градусы
HERO = (0.0, 180.0, "guard", 12.0, 1.03)


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    r = lerp(*ROLL, k)*math.pi/180.0
    cam = Cam3(tuple(AIM + DIR*lerp(*DIST, k)), tuple(AIM),
               up=(math.sin(r), math.cos(r), 0.0))
    im, d = new_frame(BG3 + (255,))
    x, z, pose, yaw, hk = HERO
    prims = body(HMAN*hk, pose, yaw, (x, 0.0, z))
    place.draw(im, d, cam, extra=((prims, HMAN*hk),),
               z0=-1600.0, z1=4400.0, x_half=3000.0)
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
