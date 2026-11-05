# -*- coding: utf-8 -*-
"""Декорации в ПРОСТРАНСТВЕ для блоков камеры: сетка улицы, дома, фонари.

Нужны затем, что движение камеры само по себе невидимо: его показывают
предметы, которые при этом движении переезжают и меняют ракурс. Поэтому здесь
только то, по чему ход камеры читается:

* `grid` — прямая сетка на земле (не кольца, как в облёте): при панораме её
  линии веером разъезжаются, при подъёме раскрываются вглубь;
* `box` — дом-коробка с настоящими гранями: при повороте камеры у него
  открывается второй бок, при подъёме — крыша. Ни одной новой зависимости:
  восемь углов проецируются той же камерой `Cam3`, грани рисуются от дальней
  к ближней и заливаются по углу к свету;
* `lamp` — фонарь со свечением, он же задаёт, откуда падает свет.

Система координат та же, что в `skel3d`: X вправо, Y ВВЕРХ, Z вперёд, земля y=0.
"""
import math, random
import numpy as np
from film import mix, clamp, lerp, add_glow
from skel3d import _caps

NEAR = 70.0                 # ближе этого к плоскости камеры не рисуем ничего


def depth(cam, p):
    return cam.pr(p)[2]


def _vis(cam, pts):
    """Все точки перед камерой? Иначе грань/отрезок выкидываем целиком."""
    return all(cam.pr(p)[2] > NEAR for p in pts)


def seg(d, cam, A, B, col, width=2.0, alpha=160, step=170.0):
    """Отрезок на земле, разбитый на куски: так он честно гнётся перспективой
    и аккуратно обрезается, когда уходит за спину камеры."""
    A = np.asarray(A, dtype=float); B = np.asarray(B, dtype=float)
    n = max(2, int(np.linalg.norm(B - A)/step))
    pts = [cam.pr(A + (B - A)*(i/n)) for i in range(n + 1)]
    for a, b in zip(pts, pts[1:]):
        if a[2] > NEAR and b[2] > NEAR:
            d.line([(a[0], a[1]), (b[0], b[1])], fill=col + (alpha,), width=width)


def grid(d, cam, col, step=400.0, x_half=3200.0, z0=-900.0, z1=3800.0,
         alpha=150, width=2.0):
    """Прямая сетка улицы."""
    x = -x_half
    while x <= x_half + 1:
        seg(d, cam, (x, 0.0, z0), (x, 0.0, z1), col, width, alpha)
        x += step
    z = math.floor(z0/step)*step
    while z <= z1 + 1:
        seg(d, cam, (-x_half, 0.0, z), (x_half, 0.0, z), col, width, alpha)
        z += step


_FACES = (                      # нормаль, четыре угла в долях (sx, sy, sz)
    ((0.0, 0.0, -1.0), ((-1, 0, -1), (1, 0, -1), (1, 1, -1), (-1, 1, -1))),
    ((0.0, 0.0,  1.0), ((1, 0, 1), (-1, 0, 1), (-1, 1, 1), (1, 1, 1))),
    ((-1.0, 0.0, 0.0), ((-1, 0, 1), (-1, 0, -1), (-1, 1, -1), (-1, 1, 1))),
    ((1.0, 0.0, 0.0),  ((1, 0, -1), (1, 0, 1), (1, 1, 1), (1, 1, -1))),
    ((0.0, 1.0, 0.0),  ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1))),
)


def box(d, cam, at, size, col, light, fog=None, windows=True,
        win=(168, 190, 228), seed=0, ink=None):
    """Дом-коробка. at — центр основания (x, 0, z), size — (ширина, высота, глубина).

    Грань видна, если смотрит на камеру; заливка — по углу нормали к свету.
    Отсюда и объём: при повороте камеры второй бок открывается сам, при
    подъёме открывается крыша.
    """
    x, _, z = at
    w, h, dp = size
    L = np.asarray(light, dtype=float); L /= np.linalg.norm(L)
    rnd = random.Random(seed)
    quads = []
    for n, corners in _FACES:
        n = np.asarray(n, dtype=float)
        pts = [np.array([x + sx*w/2, sy*h, z + sz*dp/2], dtype=float)
               for sx, sy, sz in corners]
        c = sum(pts)/4.0
        if float((c - cam.e) @ n) >= 0.0:          # грань смотрит от камеры
            continue
        if not _vis(cam, pts):
            continue
        k = 0.30 + 0.70*max(0.0, float(n @ L))     # освещённость грани
        quads.append((depth(cam, c), pts, k))
    for _, pts, k in sorted(quads, key=lambda q: -q[0]):
        face = mix((0, 0, 0), col, k)
        if fog is not None:
            face = fog(face, depth(cam, sum(pts)/4.0))
        pr = [cam.pr(p) for p in pts]
        d.polygon([(p[0], p[1]) for p in pr], fill=face + (255,))
        if ink is not None:
            xy = [(p[0], p[1]) for p in pr]
            d.line(xy + [xy[0]], fill=ink + (255,), width=1.6)
        if not windows or k < 0.34:                # на тёмной стене окон не рисуем
            continue
        bl, br, tr, tl = pts
        u_v, v_v = br - bl, tl - bl
        cols = max(1, int(np.linalg.norm(u_v)//150))
        rows = max(1, int(np.linalg.norm(v_v)//190))
        if cols*rows > 160:
            continue
        wc = fog(mix(win, col, 0.25), depth(cam, sum(pts)/4.0)) if fog else win
        for r in range(rows):
            for c_ in range(cols):
                if rnd.random() < 0.45:
                    continue
                u0, u1 = (c_ + 0.30)/cols, (c_ + 0.70)/cols
                v0, v1 = (r + 0.32)/rows, (r + 0.68)/rows
                q = [bl + u_v*a + v_v*b for a, b in
                     ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
                if not _vis(cam, q):
                    continue
                pq = [cam.pr(p) for p in q]
                d.polygon([(p[0], p[1]) for p in pq], fill=wc + (255,))


def lamp(im, d, cam, at, h=520.0, pole=(104, 112, 134), glass=(252, 214, 148),
         fog=None, glow=0.40):
    """Фонарь: столб-капсула, плафон и свечение. Он же — источник света в сцене."""
    x, _, z = at
    base = np.array([x, 14.0, z]); top = np.array([x, h, z])
    zz = depth(cam, top)
    if zz <= NEAR:
        return
    pc = fog(pole, zz) if fog else pole
    gc = fog(glass, zz) if fog else glass
    _caps(d, cam, base, top, 11.0, pc + (255,))
    p = cam.pr(np.array([x, h + 26.0, z])); r = cam.rad(34.0, p[2])
    d.ellipse([p[0] - r*1.5, p[1] - r, p[0] + r*1.5, p[1] + r], fill=gc + (255,))
    # у фонаря ВПЛОТНУЮ к объективу свечение не считаем: спрайт раздувается на
    # пол-кадра и съедает память, а толку ноль — плафон всё равно за краем кадра
    if glow > 0.0 and p[2] > 420.0:
        add_glow(im, p[0], p[1], max(40.0, cam.rad(230.0, p[2])),
                 (255, 200, 126), glow)


def haze(col, z, bg, start=900.0, span=3200.0, k=0.82):
    """Воздушная перспектива: чем дальше, тем ближе цвет к фону."""
    return mix(col, bg, clamp((z - start)/span)*k)
