# -*- coding: utf-8 -*-
"""Общая улица для блоков камеры + шаг ходьбы в трёх координатах.

Отдельный модуль затем, чтобы каждая новая сцена не переписывала раскладку
места заново: движение камеры читается по предметам, а предметы одни и те же.
Принятые блоки 1-9 сюда не переводятся — у них своя раскладка, их не трогаем.
"""
import math
import numpy as np
from film import mix, clamp, lerp, CREAM, INK
from skel3d import body, draw_body, ground_shadow, POSES3
from stage3 import grid, box, lamp, haze, depth

HMAN = 430.0
BG3  = (10, 12, 18)

STREET = dict(
    light=(0.40, 0.78, -0.42), road=(46, 60, 88),
    houses=((-1500.0, 520.0, 620.0, 620.0, 700.0), (1540.0, 560.0, 640.0, 700.0, 720.0),
            (-1620.0, 1560.0, 700.0, 540.0, 740.0), (1600.0, 1600.0, 660.0, 760.0, 700.0),
            (-1560.0, 2600.0, 720.0, 640.0, 720.0), (1580.0, 2640.0, 700.0, 580.0, 720.0),
            (-300.0, 3500.0, 820.0, 700.0, 760.0), (900.0, 3560.0, 760.0, 580.0, 720.0)),
    lamps=((-640.0, 420.0), (660.0, 440.0), (-620.0, 1500.0), (640.0, 1520.0),
           (-620.0, 2580.0), (640.0, 2600.0)),
    people=((-760.0, 300.0, "stand", 24.0, 1.00), (720.0, 360.0, "guard", -20.0, 1.02),
            (-300.0, 980.0, "stand", 10.0, 0.98), (360.0, 1040.0, "stand", -12.0, 0.99),
            (-680.0, 1900.0, "guard", 4.0, 0.96), (700.0, 2200.0, "stand", -8.0, 0.97)))


def fog(col, z):
    return haze(col, z, BG3)


def walk3(t, speed=1.45, lean=5.0):
    """Поза идущего человека в пространстве: маятник ног и встречный ход рук.

    В `skel3d.POSES3` лежат только стойки, а проводка без шага превращается в
    скользящую фигуру. Поэтому углы считаются по фазе: бедро качается вперёд и
    назад, голень подгибается на заднем взмахе, руки идут навстречу ногам.
    """
    p = 2.0*math.pi*speed*t
    sw = lambda ph: 24.0*math.sin(ph)
    kn = lambda ph: 26.0*max(0.0, -math.sin(ph - 0.9))
    return dict(lean=lean, head=0.0, twist=7.0*math.sin(p),
                thigh_l=(sw(p), 6.0),            shin_l=(kn(p), 2.0),
                thigh_r=(sw(p + math.pi), -6.0), shin_r=(kn(p + math.pi), -2.0),
                ua_l=(7.0 + 20.0*math.sin(p + math.pi), 15.0),
                fa_l=(10.0 + 9.0*math.sin(p + math.pi), 8.0),
                ua_r=(7.0 + 20.0*math.sin(p), -15.0),
                fa_r=(10.0 + 9.0*math.sin(p), -8.0))


def bob(t, speed=1.45, amp=5.0):
    """Подскок таза на шаге: без него ходьба читается как езда на коньках."""
    return amp*abs(math.sin(2.0*math.pi*speed*t))


def draw(im, d, cam, pl=STREET, extra=(), z0=-1400.0, z1=4200.0, x_half=2800.0,
         grid_step=400.0):
    """Место целиком: сетка, дома, фонари, люди. extra — свои фигуры сцены:
    кортежи (примитивы, высота_для_обводки)."""
    light = pl["light"]
    grid(d, cam, mix(pl["road"], BG3, 0.26), step=grid_step, x_half=x_half,
         z0=z0, z1=z1, alpha=165)

    for x, z, w, h, dp in sorted(pl["houses"],
                                 key=lambda b: -depth(cam, (b[0], b[3]/2, b[1]))):
        box(d, cam, (x, 0.0, z), (w, h, dp), (64, 72, 96), light, fog=fog,
            seed=int(x + z), ink=mix((22, 26, 36), BG3, 0.2))

    stand = []
    for x, z in pl["lamps"]:
        p = np.array([x, 0.0, z])
        stand.append((depth(cam, p + np.array([0.0, 520.0, 0.0])),
                      lambda p=p: lamp(im, d, cam, p, fog=fog)))

    figs = []
    for x, z, pose, yaw, hk in pl["people"]:
        p = np.array([x, 0.0, z])
        figs.append((depth(cam, p + np.array([0.0, HMAN*0.5, 0.0])),
                     body(HMAN*hk, pose, yaw, tuple(p)), HMAN*hk))
    for prims, h in extra:
        c = np.mean([t[1] for t in prims], axis=0)
        figs.append((depth(cam, c), prims, h))

    for _, prims, _ in figs:
        ground_shadow(d, cam, prims, (0, 0, 0), 110)
    for dz, prims, h in figs:
        stand.append((dz, lambda prims=prims, dz=dz, h=h: draw_body(
            im, cam, prims, fog(CREAM, dz), fog(INK, dz), h*0.013,
            light=light, shade=0.58, warm=0.26)))

    for _, fn in sorted(stand, key=lambda s: -s[0]):
        fn()
