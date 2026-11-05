# -*- coding: utf-8 -*-
"""БЛОК 7 — ПОДЪЁМ-КРАН. Камера идёт снизу вверх и раскрывает место.

Начало: камера почти у земли, в полуметре от плитки — виден герой во весь
рост, остальные перекрыты им и домами, пространства не читается.
Конец: камера высоко, взгляд опущен — открылась вся площадь, расстановка
людей, тени, сетка плитки и КРЫШИ домов, которых снизу не было видно.

Эффект даёт сам подъём точки стояния: грань «верх» у коробки появляется
только когда камера выше неё, фигуры из силуэтов в рост превращаются в
фигуры, стоящие НА плоскости, а тени из полосок у ног становятся пятнами
рядом. Ход один, медленный, в одну сторону, со смягчёнными концами —
рывков и обратного хода нет.
"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import (W, H, FPS, new_frame, finish, mix, lerp, clamp, smoother,
                  CREAM, INK)
from skel3d import Cam3, body, draw_body, ground_shadow
from stage3 import grid, box, lamp, haze, depth

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

BG3   = (10, 12, 18)
EYE0  = np.array([0.0,   95.0, -640.0])     # почти у земли
EYE1  = np.array([0.0, 1040.0, -560.0])     # высоко; вбок не уходим
AIM0  = np.array([0.0,  300.0,  200.0])     # сначала смотрим герою в грудь
AIM1  = np.array([0.0,   70.0,  480.0])     # к концу взгляд опущен на площадь
HMAN  = 430.0
LIGHT = (0.30, 0.82, -0.48)                 # свет закреплён в МИРЕ

fog = lambda col, z: haze(col, z, BG3)

# герой и расстановка вокруг: (x, z, поза, разворот, рост)
HERO   = (0.0, 200.0, "dodge", 8.0, 1.03)
PEOPLE = ((-560.0,  620.0, "stand", 26.0, 0.99), (520.0,  660.0, "guard", -22.0, 1.01),
          (-980.0, 1120.0, "stand", 14.0, 0.97), (880.0, 1180.0, "stand", -16.0, 0.98),
          (-300.0, 1520.0, "guard",  6.0, 0.96), (360.0, 1560.0, "stand",  -4.0, 0.99),
          (  40.0, 2040.0, "stand", -2.0, 0.95))

LAMPS  = ((-760.0, 820.0), (760.0, 820.0), (-240.0, 1760.0), (300.0, 1760.0))

# дома: (x, z, ширина, высота, глубина) — крыши открываются на подъёме
HOUSES = ((-1760.0,  -60.0, 620.0, 560.0, 700.0), (1800.0,  120.0, 660.0, 620.0, 740.0),
          (-1840.0, 1000.0, 700.0, 700.0, 760.0), (1880.0, 1060.0, 640.0, 660.0, 720.0),
          (-1700.0, 2150.0, 720.0, 520.0, 700.0), (1760.0, 2200.0, 680.0, 580.0, 700.0),
          ( -900.0, 2900.0, 760.0, 760.0, 720.0), ( 160.0, 3000.0, 820.0, 640.0, 740.0),
          ( 1150.0, 2860.0, 700.0, 820.0, 700.0))


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    eye = EYE0 + (EYE1 - EYE0)*k
    aim = AIM0 + (AIM1 - AIM0)*k
    cam = Cam3(tuple(eye), tuple(aim))

    im, d = new_frame(BG3 + (255,))

    grid(d, cam, mix((46, 60, 88), BG3, 0.26), step=400.0, x_half=2600.0,
         z0=-760.0, z1=3500.0, alpha=165)

    for x, z, w, h, dp in sorted(HOUSES,
                                 key=lambda b: -depth(cam, (b[0], b[3]/2, b[1]))):
        box(d, cam, (x, 0.0, z), (w, h, dp), (64, 72, 96), LIGHT, fog=fog,
            seed=int(x + z), ink=mix((22, 26, 36), BG3, 0.2))

    stand = []
    for x, z in LAMPS:
        p = np.array([x, 0.0, z])
        stand.append((depth(cam, p + np.array([0.0, 520.0, 0.0])),
                      lambda p=p: lamp(im, d, cam, p, fog=fog)))

    figs = []
    for x, z, pose, yaw, hk in (HERO,) + PEOPLE:
        p = np.array([x, 0.0, z])
        figs.append((depth(cam, p + np.array([0.0, HMAN*0.5, 0.0])),
                     body(HMAN*hk, pose, yaw, tuple(p))))
    for _, prims in figs:
        ground_shadow(d, cam, prims, (0, 0, 0), 112)
    for dz, prims in figs:
        stand.append((dz, lambda prims=prims, dz=dz: draw_body(
            im, cam, prims, fog(CREAM, dz), fog(INK, dz), HMAN*0.013,
            light=LIGHT, shade=0.58, warm=0.26)))

    for _, fn in sorted(stand, key=lambda s: -s[0]):
        fn()

    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
