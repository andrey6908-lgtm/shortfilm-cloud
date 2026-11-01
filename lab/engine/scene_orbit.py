# -*- coding: utf-8 -*-
"""БЛОК 5 — ОБЛЁТ НА 360°. Камера кружит вокруг замершей фигуры.

Фигуры стоят неподвижно (как в остановленном времени), крутится только
камера. Пространство настоящее: порядок частей тела меняется сам, свет
закреплён в МИРЕ, поэтому освещённый бок переезжает по ходу облёта, а сетка
на земле показывает, что это именно облёт, а не поворот картинки.
"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import (W, H, FPS, new_frame, finish, mix, lerp, clamp, smoother,
                  CREAM, INK)
from skel3d import Cam3, body, draw_body, ground_shadow, floor

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

BG3   = (9, 11, 16)
HMAN  = 430.0
LIGHT = (-0.55, 0.72, -0.42)      # закреплён в мире, а не в кадре
RING  = 560.0                     # на каком радиусе стоят остальные

def fig_depth(cam, prims):
    c = np.mean(np.array([t[1] for t in prims]), axis=0)
    return cam.pr(c)[2]

def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    a = (360.0*k - 90.0)*math.pi/180.0          # полный круг за клип
    R = lerp(800.0, 620.0, k)                   # и чуть ближе к концу
    eye = (R*math.cos(a), lerp(310.0, 175.0, k), R*math.sin(a))
    cam = Cam3(eye, (0.0, HMAN*0.60, 0.0))

    im, d = new_frame(BG3+(255,))
    floor(d, cam, mix((44, 58, 84), BG3, 0.22))

    figs = [(body(HMAN, "dodge", 18.0, (0.0, 0.0, 0.0)), CREAM, 0.0)]
    for n in range(5):
        aa = (n*72 + 24)*math.pi/180.0
        pos = (RING*math.cos(aa), 0.0, RING*math.sin(aa))
        yaw = math.degrees(math.atan2(-math.cos(aa), -math.sin(aa)))
        figs.append((body(HMAN*0.98, "stand" if n % 2 else "guard", yaw, pos),
                     mix(CREAM, BG3, 0.34), 0.34))

    for prims, _, _ in figs:
        ground_shadow(d, cam, prims, (0, 0, 0), 115)

    for prims, skin, dim in sorted(figs, key=lambda f: fig_depth(cam, f[0]),
                                   reverse=True):
        draw_body(im, cam, prims, skin, mix(INK, BG3, dim*0.5), HMAN*0.013,
                  light=LIGHT, shade=0.60*(1.0-dim*0.4),
                  warm=0.26*(1.0-dim*0.5))

    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
