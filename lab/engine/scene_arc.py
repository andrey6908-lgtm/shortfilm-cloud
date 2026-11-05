# -*- coding: utf-8 -*-
"""БЛОК 12 — ДУГА 32°. То, что из облёта 360° годится в дело.

Полный облёт держит кадр сам, но съедает внимание и в ролике повторить его
нельзя (его слово 05.11: «мне такой не подходит»). Дуга — тот же ход камеры,
обрезанный до тридцати градусов: ракурс заметно меняется, у фигур и домов
открывается другая сторона, но кадр остаётся кадром, а не номером.
"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import W, H, FPS, new_frame, finish, lerp, clamp, smoother
from skel3d import Cam3
import place
from place import HMAN, BG3

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

ARC   = (-16.0, 16.0)               # дуга вокруг группы, градусы
R     = (980.0, 900.0)              # и чуть ближе к концу
EYE_Y = (300.0, 265.0)
AIM   = (0.0, HMAN*0.58, 120.0)

PL = dict(light=(0.40, 0.78, -0.42), road=(46, 60, 88),
          houses=tuple((2500.0*math.sin(a*math.pi/180.0), 120.0 + 2500.0*math.cos(a*math.pi/180.0),
                        700.0, 520.0 + 90.0*((a//45) % 4), 700.0)
                       for a in range(-135, 136, 45)),
          lamps=((-1050.0, 520.0), (1050.0, 560.0), (-760.0, 1500.0), (780.0, 1520.0)),
          people=((-470.0, 150.0, "guard", 64.0, 1.01), (-150.0, 330.0, "stand", 28.0, 0.99),
                  (210.0, 120.0, "dodge", -38.0, 1.03), (520.0, 330.0, "stand", -66.0, 1.00),
                  (60.0, 700.0, "stand", 6.0, 0.98), (-700.0, 900.0, "guard", 22.0, 0.97)))


def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    a = lerp(*ARC, k)*math.pi/180.0
    r = lerp(*R, k)
    eye = (AIM[0] + r*math.sin(a), lerp(*EYE_Y, k), AIM[2] - r*math.cos(a))
    cam = Cam3(eye, AIM)
    im, d = new_frame(BG3 + (255,))
    place.draw(im, d, cam, PL, z0=-1600.0, z1=3400.0, x_half=2800.0)
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
