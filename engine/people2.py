# -*- coding: utf-8 -*-
"""Персонаж на скелете: позы задаются углами, между ними можно переходить."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from film import (W, H, SS, SW, SH, SDraw, Cam, mix, lerp, clamp, smoother, blink,
                  breathe, add_glow, soft_ellipse, flicker, CREAM, RED, MAG, AMBER)

OUTLINE = (12, 12, 14)
D2R = math.pi/180.0

# ---------- геометрия ----------
def _rot(a_deg, ln):
    a = a_deg*D2R
    return (math.cos(a)*ln, math.sin(a)*ln)

def _add(p, v): return (p[0]+v[0], p[1]+v[1])

def capsule(d, cam, p0, p1, r, fill, alpha=255):
    """Отрезок с круглыми концами — любая конечность под любым углом."""
    dx, dy = p1[0]-p0[0], p1[1]-p0[1]
    ln = math.hypot(dx, dy)
    if ln < 1e-6:
        d.ellipse(cam.box(p0[0]-r, p0[1]-r, p0[0]+r, p0[1]+r), fill=fill+(alpha,)); return
    nx, ny = -dy/ln*r, dx/ln*r
    pts = [(p0[0]+nx, p0[1]+ny), (p1[0]+nx, p1[1]+ny),
           (p1[0]-nx, p1[1]-ny), (p0[0]-nx, p0[1]-ny)]
    d.polygon([cam.p(*q) for q in pts], fill=fill+(alpha,))
    for p in (p0, p1):
        d.ellipse(cam.box(p[0]-r, p[1]-r, p[0]+r, p[1]+r), fill=fill+(alpha,))

def ellipse_at(d, cam, c, rx, ry, fill, alpha=255):
    d.ellipse(cam.box(c[0]-rx, c[1]-ry, c[0]+rx, c[1]+ry), fill=fill+(alpha,))

# ---------- позы ----------
# углы в градусах: 90 = вниз, 0 = вправо, 180 = влево
POSES = {
 "stand":    dict(thigh_l=92, shin_l=90, thigh_r=88, shin_r=90,
                  ua_l=99, fa_l=95, ua_r=81, fa_r=85, lean=0, head=0, hip_y=0.0),
 "sit_bed":  dict(thigh_l=18, shin_l=28, thigh_r=14, shin_r=24,
                  ua_l=104, fa_l=78, ua_r=74, fa_r=38, lean=-4, head=2, hip_y=0.0),
 "sit_chair":dict(thigh_l=6,  shin_l=88, thigh_r=2,  shin_r=90,
                  ua_l=108, fa_l=36, ua_r=72, fa_r=144, lean=-3, head=0, hip_y=0.0),
 "lie":      dict(thigh_l=4,  shin_l=6,  thigh_r=-2, shin_r=2,
                  ua_l=150, fa_l=196, ua_r=30, fa_r=-16, lean=-82, head=-78, hip_y=0.0),
 "slump":    dict(thigh_l=22, shin_l=34, thigh_r=18, shin_r=30,
                  ua_l=104, fa_l=92, ua_r=76, fa_r=88, lean=10, head=12, hip_y=0.02),
 "reach":    dict(thigh_l=92, shin_l=90, thigh_r=88, shin_r=90,
                  ua_l=99, fa_l=95, ua_r=38, fa_r=6, lean=-4, head=-8, hip_y=0.0),
 # рука подносит телефон к лицу — второй разрыв с оригиналом, закрыт 22.10
 "phone_face":dict(thigh_l=18, shin_l=28, thigh_r=14, shin_r=24,
                  ua_l=104, fa_l=78, ua_r=58, fa_r=-54, lean=-6, head=8, hip_y=0.0),
}

def pose_mix(a, b, k):
    k = clamp(k)
    A, B = POSES[a], POSES[b]
    return {key: lerp(A[key], B[key], k) for key in A}

def walk_pose(phase, base="stand"):
    p = dict(POSES[base])
    s = math.sin(phase); c = math.cos(phase)
    p["thigh_l"] = 90 + s*21;  p["shin_l"] = 90 + max(0, -s)*30 + 6
    p["thigh_r"] = 90 - s*21;  p["shin_r"] = 90 + max(0,  s)*30 + 6
    p["ua_l"] = 90 - s*15;     p["fa_l"] = p["ua_l"] + 6
    p["ua_r"] = 90 + s*15;     p["fa_r"] = p["ua_r"] + 6
    p["hip_y"] = -abs(c)*0.012
    # Качание корпуса (22.10): раньше ноги шагали, а туловище ехало ровно —
    # первый из пяти разрывов с оригиналом. Корпус качается в такт шагу, голова
    # гасит качание наполовину, как у живого человека.
    p["lean"] = -2 + s*2.6
    p["head"] = -s*1.4
    return p

# ---------- отрисовка ----------
def draw_person(im, d, cam, hip, h, pose, t=0.0, seed=0.0, skin=CREAM,
                mood="neutral", look=0.0, alpha=255, stroke=None, lit=0.0,
                flip=False, ink=OUTLINE, face_on=True, lashes=False, hair=None,
                cloth=None, outfit=None, scarf=None):
    """hip — точка таза в мировых координатах, h — рост фигуры.

    outfit (22.10, третий разрыв с оригиналом): раньше тело было залито одним
    цветом и читалось как комбинезон. Теперь "hoodie" — капюшон за головой,
    горловина, карман-кенгуру, манжеты и подол; "jacket" — воротник клином,
    планка и манжеты. scarf — цвет шарфа, им отличаются второстепенные лица.
    """
    if isinstance(pose, str): pose = POSES[pose]
    stroke = stroke if stroke is not None else h*0.013
    br = breathe(t, 4.6, h*0.004, seed*2.0)
    f = -1 if flip else 1
    hx, hy0 = hip[0], hip[1] + pose.get("hip_y", 0.0)*h + br

    L_th, L_sh = h*0.200, h*0.188
    L_ua, L_fa = h*0.152, h*0.142
    r_leg, r_arm = h*0.044, h*0.036
    tw, tl = h*0.118, h*0.265
    hr = h*0.150

    lean = pose["lean"]*f
    sh_c = _add((hx, hy0), _rot(-90+lean, tl))
    head_c = _add(sh_c, _rot(-90+lean+pose["head"]*f, hr*1.02))

    legs, arms = [], []
    for side, (ta, sa) in (("l", (pose["thigh_l"], pose["shin_l"])),
                           ("r", (pose["thigh_r"], pose["shin_r"]))):
        off = (-1 if side == "l" else 1)*tw*0.40*f
        hip_p = (hx+off, hy0)
        knee = _add(hip_p, _rot(ta if not flip else 180-ta, L_th))
        ankle = _add(knee, _rot(sa if not flip else 180-sa, L_sh))
        legs.append(("c", hip_p, knee, r_leg))
        legs.append(("c", knee, ankle, r_leg*0.88))
        legs.append(("e", (ankle[0]+f*h*0.015, ankle[1]+h*0.008), h*0.036, h*0.021))
    for side, (ua, fa) in (("l", (pose["ua_l"], pose["fa_l"])),
                           ("r", (pose["ua_r"], pose["fa_r"]))):
        off = (-1 if side == "l" else 1)*tw*0.86*f
        sp = (sh_c[0]+off, sh_c[1]+h*0.016)
        elbow = _add(sp, _rot(ua if not flip else 180-ua, L_ua))
        hand = _add(elbow, _rot(fa if not flip else 180-fa, L_fa))
        arms.append(("c", sp, elbow, r_arm))
        arms.append(("c", elbow, hand, r_arm*0.92))
        arms.append(("e", hand, h*0.040, h*0.040))

    torso = [("c", (hx, hy0), sh_c, tw)]
    head = [("e", head_c, hr, hr*1.08)]

    def paint(group, grow, col, a):
        for it in group:
            if it[0] == "c": capsule(d, cam, it[1], it[2], it[3]+grow, col, a)
            else: ellipse_at(d, cam, it[1], it[2]+grow, it[3]+grow, col, a)

    body_col = cloth or skin
    for grp, col in ((legs, body_col), (torso, body_col)):
        paint(grp, stroke, ink, alpha)
        paint(grp, 0, col, alpha)

    hc2, hr2 = head_c, hr
    if outfit == "hoodie":   # капюшон лежит ЗА головой — рисуем до неё
        # ГОЧА 22.10: капюшон шириной больше 1.3 радиуса головы и поднятый к
        # лицу читается как ГРИВА или платок. Он должен лежать на плечах.
        ellipse_at(d, cam, (hc2[0]-f*hr2*0.20, hc2[1]+hr2*0.78),
                   hr2*1.22+stroke, hr2*0.92+stroke, ink, alpha)
        ellipse_at(d, cam, (hc2[0]-f*hr2*0.20, hc2[1]+hr2*0.78),
                   hr2*1.22, hr2*0.92, mix(body_col, (0, 0, 0), 0.22), alpha)

    paint(head, stroke, ink, alpha)
    paint(head, 0, skin, alpha)

    if outfit:               # горловина поверх шеи, под руками
        nx, ny = sh_c[0], sh_c[1] - h*0.012
        if outfit == "hoodie":
            # ГОЧА 22.10: вертикальные шнурки вместе с подолом и карманом
            # читались как ЛЯМКИ — фигура выглядела в рабочем комбинезоне.
            # Осталась только широкая горловина: её хватает, чтобы капюшон
            # прочитался, и ничего вертикального на груди больше нет.
            capsule(d, cam, (nx-tw*1.02, ny+h*0.020), (nx+tw*1.02, ny+h*0.020),
                    h*0.034+stroke*0.8, ink, alpha)
            capsule(d, cam, (nx-tw*1.02, ny+h*0.020), (nx+tw*1.02, ny+h*0.020),
                    h*0.034, mix(body_col, (255, 255, 255), 0.12), alpha)
        else:
            for sg in (-1, 1):
                capsule(d, cam, (nx+sg*tw*0.12, ny+h*0.010),
                        (nx+sg*tw*0.78, ny+h*0.052), h*0.016,
                        mix(body_col, (255, 255, 255), 0.12), alpha)

    if scarf:
        sx, sy = sh_c[0], sh_c[1] + h*0.020
        capsule(d, cam, (sx-tw*0.82, sy), (sx+tw*0.82, sy), h*0.030, ink, alpha)
        capsule(d, cam, (sx-tw*0.82, sy), (sx+tw*0.82, sy), h*0.024, scarf, alpha)
        capsule(d, cam, (sx+f*tw*0.42, sy), (sx+f*tw*0.50, sy+h*0.105), h*0.020, ink, alpha)
        capsule(d, cam, (sx+f*tw*0.42, sy), (sx+f*tw*0.50, sy+h*0.105), h*0.015, scarf, alpha)

    paint(arms, stroke, ink, alpha)
    paint(arms, 0, body_col, alpha)

    if outfit:
        # манжет — короткая тёмная перетяжка у самой кисти, а не весь рукав
        for a_i in (1, 4):
            seg = arms[a_i]
            (ex, ey), (wx, wy) = seg[1], seg[2]
            mx, my = lerp(ex, wx, 0.80), lerp(ey, wy, 0.80)
            capsule(d, cam, (mx, my), (wx, wy), seg[3]*1.12,
                    mix(body_col, (0, 0, 0), 0.26), alpha)
        # кисти — цвета кожи: иначе рука выглядит culminating в рукав без ладони
        for a_i in (2, 5):
            seg = arms[a_i]
            rr = seg[2]*0.74
            ellipse_at(d, cam, seg[1], rr+stroke*0.9, rr*0.94+stroke*0.9, ink, alpha)
            ellipse_at(d, cam, seg[1], rr, rr*0.94, mix(skin, (0, 0, 0), 0.08), alpha)
        # подол
        capsule(d, cam, (hx-tw*0.96, hy0+h*0.034), (hx+tw*0.96, hy0+h*0.034),
                h*0.013, mix(body_col, (0, 0, 0), 0.26), alpha)
        if outfit == "hoodie":   # карман-кенгуру: ниже пояса и уже плеч
            capsule(d, cam, (hx-tw*0.52, hy0-h*0.002), (hx+tw*0.52, hy0-h*0.002),
                    h*0.020, mix(body_col, (0, 0, 0), 0.16), alpha)
    if hair:
        ellipse_at(d, cam, (head_c[0], head_c[1]-hr*0.28), hr*1.06, hr*0.86, ink, alpha)
        ellipse_at(d, cam, (head_c[0], head_c[1]-hr*0.30), hr*1.0, hr*0.80, hair, alpha)
        for sg in (-1, 1):
            capsule(d, cam, (head_c[0]+sg*hr*0.92, head_c[1]-hr*0.30),
                    (head_c[0]+sg*hr*0.92, head_c[1]+hr*0.62), hr*0.16, hair, alpha)
    if lit > 0:
        soft_ellipse(im, *cam.p(head_c[0], head_c[1]+hr*0.2), cam.r(hr*1.5), cam.r(hr*1.6),
                     (150, 180, 255), 0.22*lit, 1.6)
    if face_on:
        face(d, cam, head_c[0], head_c[1], hr, t, seed, alpha, mood, look*f, skin, lashes)
    return dict(head=head_c, hr=hr, shoulder=sh_c,
                hand_l=arms[2][1], hand_r=arms[5][1], hip=(hx, hy0))

# ---------- лицо ----------
def face(d, cam, hx, hy, hr, t=0.0, seed=0.0, alpha=255, mood="neutral",
         look=0.0, skin=CREAM, lashes=False):
    bl = blink(t, seed)
    # «wired» — залип в ленту: глаза выпучены, зрачок мелкий, почти не моргает.
    # «tired» — никакущий: веко сползает ниже половины. Оба настроения заказаны
    # пользователем 22.10 («когда листает — глаза выпученные, а хочет спать —
    # никакущий»), ими и отыгрывается ночь.
    wide = 1.0
    if mood == "wired":
        bl *= 0.28; wide = 1.52
    ew, ex = hr*0.215*(1.12 if mood == "wired" else 1.0), hr*0.345
    eh = hr*0.265*wide*(1.0-bl*0.92)
    ey = hy + hr*0.06
    dx = look*hr*0.09
    ink = OUTLINE + (alpha,)
    for s in (-1, 1):
        cxx = hx + s*ex + dx
        if eh < hr*0.045:
            d.line([cam.p(cxx-ew, ey), cam.p(cxx+ew, ey)], fill=ink,
                   width=max(1, int(cam.r(hr*0.055)))); continue
        d.ellipse(cam.box(cxx-ew, ey-eh, cxx+ew, ey+eh), fill=(252, 252, 252, alpha))
        d.ellipse(cam.box(cxx-ew, ey-eh, cxx+ew, ey+eh), outline=ink,
                  width=max(1, int(cam.r(hr*0.030))))
        pr = min(ew*0.42, eh*0.40) if mood == "wired" else min(ew*0.60, eh*0.70)
        px, py = cxx + look*ew*0.30, ey + eh*0.10
        d.ellipse(cam.box(px-pr, py-pr, px+pr, py+pr), fill=ink)
        d.ellipse(cam.box(px-pr*0.65, py-pr*0.85, px-pr*0.29, py-pr*0.49),
                  fill=(255, 255, 255, alpha))
        if mood in ("tired", "sad"):
            lid = eh*(0.30 if mood == "tired" else 0.0)   # усталое веко ниже половины
            d.chord(cam.box(cxx-ew, ey-eh, cxx+ew, ey+eh+lid*2), 180, 360, fill=skin+(alpha,))
            d.line([cam.p(cxx-ew, ey-eh*0.05+lid), cam.p(cxx+ew, ey-eh*0.05+lid)], fill=ink,
                   width=max(1, int(cam.r(hr*0.032))))
        if lashes:
            for k in (-1, 0, 1):
                lx = cxx + k*ew*0.62
                d.line([cam.p(lx, ey-eh*1.05), cam.p(lx+s*ew*0.20, ey-eh*1.50)],
                       fill=ink, width=max(1, int(cam.r(hr*0.028))))
    bw = hr*0.30
    by = ey - hr*(0.40 if mood != "sad" else 0.34) - bl*hr*0.03 - (hr*0.07 if mood == "wired" else 0)
    for s in (-1, 1):
        inner = (hx+s*(ex-bw*0.75)+dx, by + (hr*0.075 if mood == "sad" else -hr*0.02))
        outer = (hx+s*(ex+bw*0.75)+dx, by - (hr*0.055 if mood in ("angry", "tired") else 0.0))
        d.line([cam.p(*inner), cam.p(*outer)], fill=ink, width=max(2, int(cam.r(hr*0.058))))
    my, mw = hy + hr*0.46, hr*0.22
    if mood == "talk":
        d.ellipse(cam.box(hx-mw*0.8, my-mw*0.5, hx+mw*0.8, my+mw*0.8), fill=(64, 26, 30, alpha))
        d.ellipse(cam.box(hx-mw*0.8, my-mw*0.5, hx+mw*0.8, my+mw*0.8), outline=ink,
                  width=max(1, int(cam.r(hr*0.030))))
    elif mood == "sad":
        d.arc(cam.box(hx-mw, my-mw*0.18, hx+mw, my+mw*0.82), 200, 340, fill=ink,
              width=max(2, int(cam.r(hr*0.045))))
    elif mood == "smile":
        d.arc(cam.box(hx-mw, my-mw*0.82, hx+mw, my+mw*0.30), 20, 160, fill=ink,
              width=max(2, int(cam.r(hr*0.045))))
    elif mood == "wired":
        d.ellipse(cam.box(hx-mw*0.42, my-mw*0.16, hx+mw*0.42, my+mw*0.42),
                  fill=(58, 24, 28, alpha), outline=ink, width=max(1, int(cam.r(hr*0.026))))
    else:
        d.line([cam.p(hx-mw*0.72, my), cam.p(hx+mw*0.72, my)], fill=ink,
               width=max(2, int(cam.r(hr*0.045))))

# ---------- демон ----------
class _Off:
    def __init__(self, cam, ox, oy): self.cam, self.ox, self.oy, self.s = cam, ox, oy, cam.s
    def p(self, x, y):
        px, py = self.cam.p(x, y); return (px-self.ox, py-self.oy)
    def r(self, v): return self.cam.r(v)
    def box(self, x0, y0, x1, y1):
        a = self.p(x0, y0); b = self.p(x1, y1); return [a[0], a[1], b[0], b[1]]

def draw_demon(im, d, cam, hip, h, pose, t=0.0, alpha=255, grin=1.0, flip=False, heat=1.0):
    """heat — сила розового ореола. Он ДЫШИТ (22.10, слово пользователя: «ореол
    прекрасный… если бы он менял яркость, чуть ярче, чуть тусклее») и, кроме
    того, разгорается по ходу ролика: render3 поднимает heat от сцены к сцене,
    от 0,9 в первом появлении до 1,4 в сцене срыва."""
    if alpha <= 6: return None
    sway = math.sin(t*0.62)*h*0.010
    hip = (hip[0]+sway, hip[1])
    ink = (10, 9, 14)
    bx0, by0 = cam.p(hip[0]-h*0.55, hip[1]-h*0.80)
    bx1, by1 = cam.p(hip[0]+h*0.55, hip[1]+h*0.55)
    pad = cam.r(h*0.12)
    X0, Y0 = bx0-pad, by0-pad
    LW, LH = max(8, int((bx1-bx0+pad*2)*SS)), max(8, int((by1-by0+pad*2)*SS))
    if LW < 5200 and LH < 5200:
        lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        dl = SDraw(lay, "RGBA")
        draw_person(lay, dl, _Off(cam, X0, Y0), hip, h, pose, t=t, skin=(255, 70, 150),
                    alpha=255, stroke=h*0.030, ink=(255, 70, 150), face_on=False, flip=flip)
        lay = lay.filter(ImageFilter.GaussianBlur(cam.r(h*0.055)*SS))
        arr = np.asarray(lay).astype(np.float32)
        arr[..., 3] *= 1.15*(alpha/255.0)*heat*flicker(t, 0.73, 0.26, 0.62)
        arr[..., 3] = np.clip(arr[..., 3], 0, 255)
        im.alpha_composite(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"),
                           (int(X0*SS), int(Y0*SS)))
    info = draw_person(im, d, cam, hip, h, pose, t=t, skin=ink, alpha=alpha,
                       stroke=h*0.010, ink=(12, 8, 14), face_on=False, flip=flip)
    hc, hr = info["head"], info["hr"]
    eb = 1.0 - blink(t, 0.37, 5.6, 0.12)*0.85
    ea = int(alpha*eb*(alpha/255.0)**0.5)
    if ea < 10: return info
    pc = (255, 120, 190, ea)
    lw = max(2, int(cam.r(hr*0.085)))
    for sg in (-1, 1):
        d.arc(cam.box(hc[0]+sg*hr*0.36-hr*0.24, hc[1]-hr*0.28,
                      hc[0]+sg*hr*0.36+hr*0.24, hc[1]+hr*0.16), 200, 340, fill=pc, width=lw)
    if grin > 0:
        gw = hr*0.46*grin
        d.arc(cam.box(hc[0]-gw, hc[1]+hr*0.06, hc[0]+gw, hc[1]+hr*0.80), 20, 160,
              fill=pc, width=lw)
        add_glow(im, *cam.p(hc[0], hc[1]+hr*0.40), cam.r(hr*0.9), MAG,
                 0.28*(alpha/255)*heat*flicker(t, 0.73, 0.26, 0.62), 2.0)
    return info
