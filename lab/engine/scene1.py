# -*- coding: utf-8 -*-
"""БЛОК 1 — ПАРАЛЛАКС. Тестовая сцена на наших стикменах.

Четыре плана на разной глубине: город, цепочка далёких фигур, фонари с двумя
стоящими, герой крупно спереди. Камера едет вбок и чуть вперёд.

Экранное положение КАЖДОГО плана считается одной перспективной формулой
s = F/(z - camz), центр камеры — её точка стояния. Поэтому параллакс и наезд
получаются сами: передний план проносится и прибавляет в размере, город почти
стоит. Ни одной новой зависимости — тот же numpy+PIL, что и короткометражка.
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import (W, H, FPS, Cam, new_frame, finish, mix, lerp, clamp,
                  smoother, add_glow, CREAM, INK)
from people2 import draw_person, walk_pose, POSES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
DUR = 10.0

BG3   = (10, 12, 18)          # ночной фон
F     = 1000.0                # фокус: на z=F масштаб ровно 1
EYE   = 250.0                 # высота камеры над землёй, мировые единицы
PAN   = (-620.0, 620.0)       # ход камеры вбок за весь клип
DOLLY = (0.0, 400.0)          # ход камеры вперёд
FOOT  = 0.417                 # таз выше земли на столько ростов (бедро+голень+ступня)

Z_CITY, Z_CROWD, Z_LAMPS, Z_HERO = 9000.0, 4400.0, 2400.0, 1250.0

def plane(z, camx, camz):
    """Камера одного плана."""
    return Cam(F/(z-camz), camx, -EYE)

def far(col, z, k=0.78):
    """Атмосферная перспектива: чем дальше, тем ближе цвет к фону."""
    return mix(col, BG3, clamp((z-1150.0)/8000.0)*k)

# ---------------------------------------------------------------- наполнение
def city(d, cam, z):
    col = far((60, 68, 92), z); win = far((158, 178, 216), z, 0.60)
    rnd = random.Random(7)
    for i in range(-7, 8):
        x = i*950 + rnd.randint(-170, 170)
        w = rnd.randint(380, 720); h = rnd.randint(900, 2400)
        d.rectangle(cam.box(x, -h, x+w, 0), fill=col+(255,))
        for r in range(int(h/230)):
            for c in range(int(w/200)):
                if rnd.random() < 0.52: continue
                wx, wy = x+58+c*200, -h+96+r*230
                d.rectangle(cam.box(wx, wy, wx+72, wy+98), fill=win+(255,))

def kerb(d, cam, z, x0, x1, step, post=170):
    """Бордюр со столбиками: при движении камеры они и гонят параллакс."""
    col = far((78, 86, 104), z)
    d.rectangle(cam.box(x0, 0, x1, 30), fill=col+(255,))
    x = math.floor(x0/step)*step
    while x < x1:
        d.rectangle(cam.box(x-11, -post, x+11, 0), fill=col+(255,))
        d.ellipse(cam.box(x-19, -post-19, x+19, -post+19), fill=col+(255,))
        x += step

def lamp(im, d, cam, z, x, h=560):
    col = far((96, 104, 124), z)
    d.rectangle(cam.box(x-10, -h, x+10, 0), fill=col+(255,))
    d.ellipse(cam.box(x-58, -h-34, x+58, -h+24), fill=far((250, 212, 142), z, 0.45)+(255,))
    add_glow(im, *cam.p(x, -h), cam.r(210), (255, 198, 120), 0.38)

def figure(im, d, cam, z, x, h, pose, t, seed=0.0, face=True, **kw):
    """Фигура, стоящая ступнями ровно на земле (y=0)."""
    return draw_person(im, d, cam, (x, -FOOT*h), h, pose, t=t, seed=seed,
                       skin=far(CREAM, z, 0.70), ink=far(INK, z, 0.45),
                       face_on=face, **kw)

# -------------------------------------------------------------------- кадр
def frame(i):
    t = i/FPS
    k = smoother(clamp(t/DUR))
    camx = lerp(PAN[0], PAN[1], k)
    camz = lerp(DOLLY[0], DOLLY[1], k)
    im, d = new_frame(BG3+(255,))

    # 1) город — почти стоит на месте
    city(d, plane(Z_CITY, camx, camz), Z_CITY)

    # 2) цепочка далёких фигур
    cam = plane(Z_CROWD, camx, camz)
    kerb(d, cam, Z_CROWD, -4200, 4200, 1150, post=120)
    for n in range(7):
        x = -2160 + n*720
        figure(im, d, cam, Z_CROWD, x + (18 if n % 2 else -14)*t, 418,
               walk_pose(t*2.6 + n*1.7), t, seed=n*0.37, face=False,
               flip=bool(n % 2))

    # 3) фонари и двое стоящих — средний план
    cam = plane(Z_LAMPS, camx, camz)
    kerb(d, cam, Z_LAMPS, -2800, 2800, 640)
    for n in range(-4, 5):
        lamp(im, d, cam, Z_LAMPS, n*640)
    figure(im, d, cam, Z_LAMPS, 150, 420, "stand", t, seed=1.4, look=0.6,
           outfit="jacket")
    figure(im, d, cam, Z_LAMPS, 400, 410, "stand", t, seed=2.1, look=-0.6,
           flip=True, outfit="hoodie")

    # 4) герой крупно спереди — проносится и прибавляет в размере
    cam = plane(Z_HERO, camx, camz)
    kerb(d, cam, Z_HERO, -2000, 2000, 300, post=210)
    figure(im, d, cam, Z_HERO, -250 + 70*t, 420, walk_pose(t*3.1), t,
           seed=0.0, look=0.35, outfit="hoodie")

    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)
