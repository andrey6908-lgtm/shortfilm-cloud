# -*- coding: utf-8 -*-
"""БЛОК 10 — ПРОВОДКА. Камера идёт ВМЕСТЕ с героем, мир уезжает мимо.

Отличие от блока 1: там камера ехала мимо места и герой был одной из деталей.
Здесь камера привязана к герою — он стоит в кадре на одном месте, а дома,
фонари и прохожие проносятся мимо. Привязка в одной строке: точка стояния
камеры считается ОТ координаты героя, цель взгляда — его грудь.

Шаг согласован со скоростью: `speed = v/(2*stride)`, иначе ноги скользят по
земле, как на коньках. При v=330 единиц/с и шаге 170 это 0,97 — около двух
шагов в секунду, человеческая походка.
"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import W, H, FPS, new_frame, finish, lerp, clamp
from skel3d import body, Cam3
import place
from place import HMAN, BG3

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

V      = 330.0                       # скорость героя, единиц/с
STRIDE = 170.0                       # шаг
STEP   = V/(2.0*STRIDE)              # частота цикла ходьбы
X0     = -V*DUR/2.0                  # идёт через всё место, не разгоняясь
HERO_Z = 180.0
OFF    = np.array([-150.0, 205.0, -820.0])   # камера относительно героя

# место под проводку: застройка вдоль ДАЛЬНЕЙ стороны, чтобы она стримилась мимо
PL = dict(
    light=(0.40, 0.78, -0.42), road=(46, 60, 88),
    houses=tuple((x*760.0, 1560.0 + 90.0*math.sin(x), 640.0, 460.0 + 120.0*((x*7) % 5),
                  700.0) for x in range(-5, 6)),
    lamps=tuple((x*780.0 - 120.0, 760.0) for x in range(-4, 5)),
    people=tuple((x*820.0 + 230.0, 1080.0 + 140.0*math.cos(x),
                  ("stand", "guard")[x % 2], -18.0 + 9.0*x, 0.98 + 0.02*(x % 3))
                 for x in range(-4, 5)))


def frame(i):
    t = i/FPS
    hx = X0 + V*t
    hero = np.array([hx, place.bob(t, STEP), HERO_Z])
    cam_at = np.array([hx, 0.0, HERO_Z]) + OFF
    cam = Cam3(tuple(cam_at), (hx, 300.0, HERO_Z))

    im, d = new_frame(BG3 + (255,))
    prims = body(HMAN*1.03, place.walk3(t, STEP), 96.0, tuple(hero))
    place.draw(im, d, cam, PL, extra=((prims, HMAN*1.03),),
               z0=-1600.0, z1=3000.0, x_half=4400.0, grid_step=480.0)
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
