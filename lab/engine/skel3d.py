# -*- coding: utf-8 -*-
"""БЛОК 5 — ОБЪЁМ. Стикмен в трёх координатах и камера, которая его облетает.

Почему это вообще работает дешево: тело стикмена — набор КАПСУЛ и ШАРОВ, а не
полигональная модель. Капсула в пространстве рисуется как капсула между двумя
спроецированными точками, шар — как эллипс; радиус делится на глубину. Значит
никакого растеризатора треугольников, Z-буфера и библиотек не нужно: хватает
перспективной проекции, сортировки примитивов по дальности и той же заливки,
что в плоском рисовальщике. Отсюда и облёт на 360° — камера просто считается
из своей точки стояния.

Система координат: X — вправо, Y — ВВЕРХ, Z — вперёд. Земля y = 0.
"""
import math
import numpy as np
from PIL import Image, ImageChops
from film import W, H, SS, SW, SH, SDraw, mix, clamp, lerp

D2R = math.pi/180.0

def _down(pitch, roll):
    """Направление конечности: вектор «вниз», наклонённый вперёд и в сторону."""
    p, r = pitch*D2R, roll*D2R
    y, z = -math.cos(p), math.sin(p)
    return np.array([-y*math.sin(r), y*math.cos(r), z])

def _up(pitch, roll):
    v = _down(pitch, roll); return np.array([-v[0], -v[1], v[2]])

class Cam3:
    """Камера: точка стояния, цель, фокус. Даёт проекцию и радиус по глубине."""
    def __init__(self, eye, target, f=1250.0, up=(0.0, 1.0, 0.0)):
        self.e = np.array(eye, dtype=float)
        fwd = np.array(target, dtype=float) - self.e
        fwd /= np.linalg.norm(fwd)
        right = np.cross(fwd, np.array(up, dtype=float))
        right /= np.linalg.norm(right)
        self.fwd, self.right, self.up = fwd, right, np.cross(right, fwd)
        self.f = f
    def pr(self, p):
        v = np.asarray(p, dtype=float) - self.e
        z = max(float(v @ self.fwd), 1.0)
        return (W/2 + self.f*float(v @ self.right)/z,
                H/2 - self.f*float(v @ self.up)/z, z)
    def rad(self, r, z): return self.f*r/max(z, 1.0)

# ---------------------------------------------------------------- скелет
# Поза: на конечность пара углов (наклон вперёд, разведение в сторону).
POSES3 = {
 "stand": dict(lean=2, head=0, twist=0,
               thigh_l=(2, 7),  shin_l=(1, 2),  thigh_r=(2, -7), shin_r=(1, -2),
               ua_l=(7, 17), fa_l=(10, 9), ua_r=(7, -17), fa_r=(10, -9)),
 "guard": dict(lean=6, head=-4, twist=26,
               thigh_l=(16, 12), shin_l=(-12, 4), thigh_r=(-12, -13), shin_r=(14, -3),
               ua_l=(-62, 26), fa_l=(-86, 10), ua_r=(-28, -34), fa_r=(-74, -16)),
 "dodge": dict(lean=-34, head=-14, twist=14,
               thigh_l=(26, 14), shin_l=(44, 5), thigh_r=(-16, -15), shin_r=(30, -4),
               ua_l=(-104, 40), fa_l=(-70, 22), ua_r=(-118, -44), fa_r=(-84, -28)),
}

def body(h, pose="stand", yaw=0.0, at=(0.0, 0.0, 0.0)):
    """Примитивы фигуры в мировых координатах. at — точка между ступнями."""
    if isinstance(pose, str): pose = POSES3[pose]
    L_th, L_sh = h*0.200, h*0.188
    L_ua, L_fa = h*0.152, h*0.142
    r_leg, r_arm = h*0.044, h*0.036
    tw, tl, hr = h*0.118, h*0.265, h*0.150

    hip = np.array([0.0, h*0.417, 0.0])          # таз над землёй
    sh_c = hip + _up(pose["lean"], 0.0)*tl
    head_c = sh_c + _up(pose["lean"] + pose["head"], 0.0)*hr*1.02
    tx = math.sin(pose["twist"]*D2R)             # разворот плеч вокруг себя

    out = []
    for side, s in (("l", 1.0), ("r", -1.0)):
        hp = hip + np.array([s*tw*0.40, 0.0, 0.0])
        knee = hp + _down(*pose[f"thigh_{side}"])*L_th
        ankle = knee + _down(*pose[f"shin_{side}"])*L_sh
        out += [("c", hp, knee, r_leg), ("c", knee, ankle, r_leg*0.88),
                ("e", ankle + np.array([0.0, -h*0.012, h*0.020]), h*0.036)]
        sp = sh_c + np.array([s*tw*0.86, -h*0.016, s*tw*0.86*tx])
        elbow = sp + _down(*pose[f"ua_{side}"])*L_ua
        hand = elbow + _down(*pose[f"fa_{side}"])*L_fa
        out += [("c", sp, elbow, r_arm), ("c", elbow, hand, r_arm*0.92),
                ("e", hand, h*0.040)]
    out += [("c", hip, sh_c, tw), ("e", head_c, hr)]

    # разворот фигуры вокруг своей вертикали и перенос на место
    cy, sy = math.cos(yaw*D2R), math.sin(yaw*D2R)
    o = np.array(at, dtype=float)
    def tr(p):
        p = np.asarray(p, dtype=float)
        return o + np.array([p[0]*cy + p[2]*sy, p[1], -p[0]*sy + p[2]*cy])
    res = []
    for t in out:
        if t[0] == "c": res.append(("c", tr(t[1]), tr(t[2]), t[3]))
        else:           res.append(("e", tr(t[1]), None, t[2]))
    return res

# ------------------------------------------------------------- отрисовка
def _caps(d, cam, A, B, r, fill):
    a, b = cam.pr(A), cam.pr(B)
    ra, rb = cam.rad(r, a[2]), cam.rad(r, b[2])
    dx, dy = b[0]-a[0], b[1]-a[1]
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy/ln, dx/ln
    d.polygon([(a[0]+nx*ra, a[1]+ny*ra), (b[0]+nx*rb, b[1]+ny*rb),
               (b[0]-nx*rb, b[1]-ny*rb), (a[0]-nx*ra, a[1]-ny*ra)], fill=fill)
    for p, rr in ((a, ra), (b, rb)):
        d.ellipse([p[0]-rr, p[1]-rr, p[0]+rr, p[1]+rr], fill=fill)

def _ball(d, cam, C, r, fill):
    c = cam.pr(C); rr = cam.rad(r, c[2])
    d.ellipse([c[0]-rr, c[1]-rr*1.06, c[0]+rr, c[1]+rr*1.06], fill=fill)

def draw_body(im, cam, prims, skin, ink, stroke, light=(-0.6, 0.75, -0.3),
              shade=0.60, warm=0.26):
    """Фигура на свой слой, от дальних примитивов к ближним, затем свет вуалью.

    Сортировка по глубине и даёт объём: ближняя рука честно закрывает корпус,
    а при облёте порядок меняется сам.
    """
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = SDraw(lay, "RGBA")
    def depth(t):
        p = cam.pr(t[1])[2]
        return (p + cam.pr(t[2])[2])/2 if t[0] == "c" else p
    xs, ys = [], []
    for t in sorted(prims, key=depth, reverse=True):
        if t[0] == "c":
            _caps(d, cam, t[1], t[2], t[3]+stroke, ink+(255,))
            _caps(d, cam, t[1], t[2], t[3], skin+(255,))
            for q in (t[1], t[2]):
                p = cam.pr(q); xs.append(p[0]); ys.append(p[1])
        else:
            _ball(d, cam, t[1], t[3]+stroke, ink+(255,))
            _ball(d, cam, t[1], t[3], skin+(255,))
            p = cam.pr(t[1]); xs.append(p[0]); ys.append(p[1])

    # свет: тёмная вуаль с теневой стороны, тёплая — с освещённой
    L = np.array(light, dtype=float); L /= np.linalg.norm(L)
    lx = float(L @ cam.right)                     # куда светит в кадре
    pad = 90
    x0 = int(max(0, (min(xs)-pad)*SS)); x1 = int(min(SW, (max(xs)+pad)*SS))
    y0 = int(max(0, (min(ys)-pad)*SS)); y1 = int(min(SH, (max(ys)+pad)*SS))
    if x1-x0 > 1 and y1-y0 > 1:
        g = np.linspace(0.0, 1.0, x1-x0, dtype=np.float32)
        if lx > 0: g = g[::-1]                    # свет справа — тень слева
        k = abs(lx)*0.65 + 0.35
        mask = lay.crop((x0, y0, x1, y1)).getchannel("A")
        for col, grad, st in (((4, 6, 12), g, shade*k),
                              ((255, 208, 146), 1.0-g, warm*k)):
            a = (grad**1.5*(255*st)).astype(np.uint8)
            band = np.repeat(a[None, :], y1-y0, axis=0)
            veil = Image.fromarray(np.dstack(
                [np.full_like(band, c) for c in col] + [band]), "RGBA")
            veil.putalpha(ImageChops.multiply(veil.getchannel("A"), mask))
            lay.alpha_composite(veil, (x0, y0))
    im.alpha_composite(lay)

def ground_shadow(d, cam, prims, col, alpha=120):
    """БЛОК 4 — ТЕНЬ. Пятно под фигурой: силуэт, прижатый к земле."""
    pts = [t[1] for t in prims] + [t[2] for t in prims if t[0] == "c"]
    xs = [p[0] for p in pts]; zs = [p[2] for p in pts]
    cx, cz = (min(xs)+max(xs))/2, (min(zs)+max(zs))/2
    rx = max(26.0, (max(xs)-min(xs))*0.62); rz = max(26.0, (max(zs)-min(zs))*0.62)
    n = 26
    ring = [cam.pr((cx + rx*math.cos(a), 1.0, cz + rz*math.sin(a)))
            for a in (i*2*math.pi/n for i in range(n))]
    d.polygon([(p[0], p[1]) for p in ring], fill=col+(alpha,))

def floor(d, cam, col, rings=(170, 340, 510, 680, 850, 1020), spokes=20,
          width=2.2, alpha=190):
    """Сетка на земле — по ней облёт и читается как облёт."""
    for R in rings:
        n = 72
        pts = [cam.pr((R*math.cos(i*2*math.pi/n), 0.0, R*math.sin(i*2*math.pi/n)))
               for i in range(n+1)]
        for a, b in zip(pts, pts[1:]):
            if a[2] > 1.5 and b[2] > 1.5:
                d.line([(a[0], a[1]), (b[0], b[1])], fill=col+(alpha,), width=width)
    for k in range(spokes):
        a = k*2*math.pi/spokes
        p0 = cam.pr((rings[0]*math.cos(a), 0.0, rings[0]*math.sin(a)))
        p1 = cam.pr((rings[-1]*math.cos(a), 0.0, rings[-1]*math.sin(a)))
        if p0[2] > 1.5 and p1[2] > 1.5:
            d.line([(p0[0], p0[1]), (p1[0], p1[1])], fill=col+(alpha,), width=width)
