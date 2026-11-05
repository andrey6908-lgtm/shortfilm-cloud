# -*- coding: utf-8 -*-
"""БЛОК 6 — ПАНОРАМА. Камера стоит на месте и ПОВОРАЧИВАЕТСЯ вокруг себя.

Чем панорама отличается от уже принятого параллакса: там камера ЕХАЛА вбок,
и планы расходились с разной скоростью. Здесь точка стояния не двигается ни
на единицу — меняется только направление взгляда. Поэтому параллакса нет
вообще: близкое и далёкое уезжают по кадру ОДНИМ темпом, зато перспектива
скашивается — у домов открывается второй бок, линии сетки разъезжаются
веером, фонари проходят по кадру дугой. Это и есть киношное «панорамирование»,
а не сдвиг картинки.

Считается той же камерой `Cam3`: eye закреплён, цель ходит по кругу вокруг
него. Ни новой математики, ни новых зависимостей.
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
EYE   = np.array([0.0, 205.0, -700.0])      # точка стояния — НЕ двигается
SWEEP = (-30.0, 30.0)                       # поворот камеры за клип, градусы
LOOK  = 1500.0                              # на каком удалении цель взгляда
TILT  = -0.045                              # взгляд чуть ниже горизонта
HMAN  = 430.0
LIGHT = (0.38, 0.78, -0.42)                 # свет закреплён в МИРЕ

D2R = math.pi/180.0
fog = lambda col, z: haze(col, z, BG3)


def at_ang(deg, R, y=0.0):
    """Точка на земле под углом deg от камеры, на удалении R."""
    a = deg*D2R
    return np.array([EYE[0] + R*math.sin(a), y, EYE[2] + R*math.cos(a)])


# что стоит на площади: угол от камеры, удаление, поза, разворот, рост
PEOPLE = ((-56.0, 1260.0, "stand", 28.0, 0.99), (-38.0,  780.0, "guard", -14.0, 1.02),
          (-21.0, 1520.0, "stand", -8.0, 0.97), ( -6.0,  990.0, "stand",  22.0, 1.00),
          ( 11.0,  600.0, "dodge",  -6.0, 1.04), ( 25.0, 1330.0, "guard", 16.0, 0.98),
          ( 41.0,  900.0, "stand", -24.0, 1.01), ( 57.0, 1480.0, "stand",  6.0, 0.96))

LAMPS = ((-46.0, 1080.0), (-16.0, 1010.0), (16.0, 1010.0), (46.0, 1080.0))

HOUSES = tuple((a, 2550.0 + 230.0*math.sin(a*0.7), 430.0 + 46.0*abs(a % 7),
                430.0 + 72.0*((a*13) % 9), 520.0)
               for a in range(-72, 73, 12))


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    a = lerp(*SWEEP, k)*D2R
    target = EYE + LOOK*np.array([math.sin(a), TILT, math.cos(a)])
    cam = Cam3(tuple(EYE), tuple(target))

    im, d = new_frame(BG3 + (255,))

    # 1) сетка улицы: при повороте разъезжается веером
    grid(d, cam, mix((46, 60, 88), BG3, 0.26), step=420.0, alpha=165)

    # 2) дома — у них при повороте открывается второй бок
    for ang, R, w, h, dp in sorted(HOUSES,
                                   key=lambda b: -depth(cam, at_ang(b[0], b[1]))):
        p = at_ang(ang, R)
        box(d, cam, p, (w, h, dp), (64, 72, 96), LIGHT, fog=fog,
            seed=int(ang) + 90, ink=mix((22, 26, 36), BG3, 0.2))

    # 3) фонари и фигуры — одной очередью по дальности, чтобы ближний
    #    честно закрывал дальнего
    stand = []
    for ang, R in LAMPS:
        p = at_ang(ang, R)
        stand.append((depth(cam, p + np.array([0.0, 520.0, 0.0])),
                      lambda p=p: lamp(im, d, cam, p, fog=fog)))

    figs = []
    for ang, R, pose, yaw, hk in PEOPLE:
        p = at_ang(ang, R)
        prims = body(HMAN*hk, pose, yaw, tuple(p))
        figs.append((depth(cam, p), prims))
    for _, prims in figs:                       # тени — все до фигур
        ground_shadow(d, cam, prims, (0, 0, 0), 105)
    for dz, prims in figs:
        stand.append((dz, lambda prims=prims, dz=dz: draw_body(
            im, cam, prims, fog(CREAM, dz), fog(INK, dz), HMAN*0.013,
            light=LIGHT, shade=0.58, warm=0.26)))

    for _, fn in sorted(stand, key=lambda s: -s[0]):
        fn()

    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
