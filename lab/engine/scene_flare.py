# -*- coding: utf-8 -*-
"""БЛОК 16 — АНАМОРФНЫЙ БЛИК В ОБЪЕКТИВ.

Камера медленно поворачивается вдоль улицы с фонарями. Пока фонарь идёт по
кадру, из него тянется холодная горизонтальная полоса, вокруг стоит тёплый
ореол, а по линии «фонарь — центр кадра» и дальше за центр плывут кольца-
призраки. У края кадра блик слабеет, у оси — разгорается: так ведёт себя
настоящий объектив, и кадр от этого перестаёт выглядеть нарисованным.

Приём бесплатный по времени: блик кладётся на готовый кадр 1920x1080, а
полоса и ореол считаются внешним произведением двух одномерных массивов
(см. `flare.py`). Доля блика в кадре — единицы процентов.
"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import W, H, FPS, new_frame, finish, lerp, clamp, smoother
from skel3d import Cam3, body
import place, flare
from place import HMAN, BG3

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

EYE   = np.array([0.0, 205.0, -820.0])
SWEEP = (-26.0, 26.0)
LOOK  = 1500.0
TILT  = -0.03
D2R   = math.pi/180.0

PL = dict(light=(0.40, 0.78, -0.42), road=(46, 60, 88),
          houses=((-1500.0, 520.0, 620.0, 620.0, 700.0), (1540.0, 560.0, 640.0, 700.0, 720.0),
                  (-1620.0, 1560.0, 700.0, 540.0, 740.0), (1600.0, 1600.0, 660.0, 760.0, 700.0),
                  (-300.0, 2900.0, 820.0, 700.0, 760.0), (900.0, 2960.0, 760.0, 580.0, 720.0)),
          lamps=((-760.0, 300.0), (780.0, 320.0), (-700.0, 1180.0), (720.0, 1200.0),
                 (-660.0, 2100.0), (680.0, 2140.0)),
          people=((-330.0, 540.0, "stand", 22.0, 1.00), (360.0, 620.0, "guard", -18.0, 1.01),
                  (-120.0, 1500.0, "stand", 8.0, 0.98), (240.0, 1900.0, "stand", -10.0, 0.97)))
HERO = (-40.0, 240.0, "dodge", 12.0, 1.03)


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    a = lerp(*SWEEP, k)*D2R
    cam = Cam3(tuple(EYE), tuple(EYE + LOOK*np.array([math.sin(a), TILT, math.cos(a)])))

    im, d = new_frame(BG3 + (255,))
    x, z, pose, yaw, hk = HERO
    prims = body(HMAN*hk, pose, yaw, (x, 0.0, z))
    place.draw(im, d, cam, PL, extra=((prims, HMAN*hk),),
               z0=-1600.0, z1=3800.0, x_half=2800.0)

    img = finish(im)
    img = flare.add(img, flare.sources_from_lamps(cam, PL["lamps"]))
    return img.save(f"{OUT}/f{i:05d}.jpg", quality=94)
