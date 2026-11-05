# -*- coding: utf-8 -*-
"""БЛОК 9 — PUSH: резкий короткий наезд на 0,6 с (удар-акцент под слово).

Это не медленный зум, а УДАР: камера за шесть десятых секунды придвигается к
субъекту и ВСТАЁТ на новом плане. Ставится под нужное слово в озвучке, держит
внимание сам по себе и склейки не требует.

Кривая удара — `punch()`: `smoother(u) ** 0.62`. Скорость на входе и выходе
по-прежнему НОЛЬ (значит ни «дрыка» на трогании, ни тычка на остановке —
правило «без рывков» не нарушено), но 65% хода проходит за первую половину
окна, и глаз читает это как удар, а не как проезд.

В клипе приём показан дважды, с выдержкой между ударами: общий план → удар →
средний → удар → крупный. Между ударами кадр НЕ мёртвый: идёт еле заметный
подъезд ~0,3%/с, иначе пауза читается как стоп-кадр.
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
HMAN  = 430.0
LIGHT = (0.40, 0.78, -0.42)
AIM   = np.array([0.0, 300.0, 180.0])                 # цель — грудь героя
DIR   = np.array([-0.0896, 0.0697, -0.9956])          # откуда смотрим, единичный

# раскладка удара: (начало, длительность, удаление с, удаление на)
# паузы между ударами — подъезд на единицы, чтобы кадр жил
BEATS = ((0.0, 2.6, 1250.0, 1205.0),      # общий план, еле заметный подъезд
         (2.6, 0.6, 1205.0,  760.0),      # УДАР 1
         (3.2, 2.8,  760.0,  733.0),      # держим средний
         (6.0, 0.6,  733.0,  470.0),      # УДАР 2
         (6.6, 3.4,  470.0,  452.0))      # держим крупный

HERO   = (0.0, 180.0, "dodge", 10.0, 1.04)
PEOPLE = ((-760.0, 300.0, "stand", 24.0, 1.00), (720.0, 360.0, "guard", -20.0, 1.02),
          (-260.0, 980.0, "stand", 10.0, 0.98), (340.0, 1040.0, "stand", -12.0, 0.99),
          (-60.0, 1900.0, "guard", 4.0, 0.96))
LAMPS  = ((-640.0, 420.0), (660.0, 440.0), (-520.0, 1500.0), (540.0, 1520.0))
HOUSES = ((-1500.0, 520.0, 620.0, 620.0, 700.0), (1540.0, 560.0, 640.0, 700.0, 720.0),
          (-1620.0, 1560.0, 700.0, 540.0, 740.0), (1600.0, 1600.0, 660.0, 760.0, 700.0),
          (-300.0, 2600.0, 820.0, 700.0, 760.0), (900.0, 2680.0, 760.0, 580.0, 720.0))

fog = lambda col, z: haze(col, z, BG3)


def punch(u):
    """Кривая удара: концы мягкие, середина стремительная."""
    return smoother(clamp(u))**0.62


def dist(t):
    for t0, d, a, b in BEATS:
        if t < t0 + d:
            u = (t - t0)/d
            return lerp(a, b, punch(u) if d < 1.0 else smoother(clamp(u)))
    return BEATS[-1][3]


def frame(i):
    t = i/FPS
    cam = Cam3(tuple(AIM + DIR*dist(t)), tuple(AIM))

    im, d = new_frame(BG3 + (255,))
    grid(d, cam, mix((46, 60, 88), BG3, 0.26), step=400.0, x_half=2800.0,
         z0=-1400.0, z1=3600.0, alpha=165)

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
        ground_shadow(d, cam, prims, (0, 0, 0), 110)
    for dz, prims in figs:
        stand.append((dz, lambda prims=prims, dz=dz: draw_body(
            im, cam, prims, fog(CREAM, dz), fog(INK, dz), HMAN*0.013,
            light=LIGHT, shade=0.58, warm=0.26)))

    for _, fn in sorted(stand, key=lambda s: -s[0]):
        fn()

    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
