# -*- coding: utf-8 -*-
"""БЛОК 11 — НАКЛОН ВВЕРХ (tilt). Камера стоит, взгляд идёт по фасаду вверх.

Вертикальный близнец панорамы: точка стояния не двигается, меняется только
направление взгляда — снизу от подножия и людей у входа до крыши. Приём
отвечает за одну мысль: «он меньше этого». Требование то же, что у панорамы:
нужен предмет С ГРАНЯМИ и фактурой (окна), иначе наклон читается как сдвиг.
"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import W, H, FPS, new_frame, finish, lerp, clamp, smoother, mix
from skel3d import Cam3
from stage3 import grid, box, lamp
import place
from place import HMAN, BG3, fog

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

EYE   = (0.0, 165.0, -260.0)        # стоим у подножия
AIM_Y = (95.0, 2060.0)              # взгляд: от входа до крыши
AIM_Z = 980.0
LIGHT = (0.42, 0.74, -0.44)

PL = dict(light=LIGHT, road=(46, 60, 88),
          houses=((0.0, 980.0, 900.0, 2100.0, 700.0),          # башня
                  (-1420.0, 1500.0, 700.0, 980.0, 720.0),
                  (1440.0, 1540.0, 680.0, 1120.0, 700.0),
                  (-1500.0, 2700.0, 740.0, 700.0, 720.0),
                  (1520.0, 2760.0, 720.0, 840.0, 700.0)),
          lamps=((-520.0, 380.0), (540.0, 400.0)),
          people=((-330.0, 420.0, "stand", 22.0, 1.00), (300.0, 450.0, "guard", -18.0, 1.01),
                  (-60.0, 560.0, "stand", 8.0, 0.99)))


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    cam = Cam3(EYE, (0.0, lerp(*AIM_Y, k), AIM_Z))
    im, d = new_frame(BG3 + (255,))
    place.draw(im, d, cam, PL, z0=-400.0, z1=3400.0, x_half=2200.0)
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
