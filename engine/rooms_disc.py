# -*- coding: utf-8 -*-
"""Декорации «ДИСЦИПЛИНЫ»: девять предметов, которых не было в первом фильме.

Манера та же, что в rooms.py: чёрный фон, предметы светлым контуром, живые
линии. Ничего из rooms.py не переписано — только добавлено.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from film import (W, H, SS, Cam, mix, lerp, clamp, smoother, add_glow,
                  soft_ellipse, RED, MAG, AMBER)
from rooms import LINE, LINE2, FILLD, BG, rrect, line, _w

RED_D = (214, 44, 52)          # красный демона и повязки


# ----------------------------------------------------------------- ЗЕРКАЛО
def mirror(im, d, cam, t=0.0, crack=0.0, glow_k=1.0):
    """Овальное зеркало на подставке. В отражении — демон, не ты.

    crack 0..1 — трещины от центра; на 1 стекло пробито.
    """
    cx, cy, rx, ry = 1260, 560, 170, 250
    # подставка
    rrect(d, cam, (cx-190, cy+ry+10, cx+190, cy+ry+46), 14, FILLD, LINE, 3.0)
    # рама
    d.ellipse(cam.box(cx-rx-14, cy-ry-14, cx+rx+14, cy+ry+14), fill=FILLD + (255,))
    d.ellipse(cam.box(cx-rx-14, cy-ry-14, cx+rx+14, cy+ry+14),
              outline=LINE + (255,), width=_w(cam, 3.4))
    # стекло: тёмное, с красным свечением изнутри
    d.ellipse(cam.box(cx-rx, cy-ry, cx+rx, cy+ry), fill=(14, 10, 14, 255))
    add_glow(im, *cam.p(cx, cy), cam.r(rx*1.5), MAG, 0.30*glow_k, 2.4)
    if crack > 0.004:
        rr = random.Random(7)
        for i in range(9):
            a = i*0.698 + 0.3
            ln = (rx if abs(math.cos(a)) > abs(math.sin(a)) else ry) * (0.35 + 0.65*crack)
            pts = [(cx, cy)]
            for k in range(1, 5):
                u = k/4
                pts.append((cx + math.cos(a)*ln*u + rr.uniform(-9, 9),
                            cy + math.sin(a)*ln*u + rr.uniform(-9, 9)))
            line(d, cam, pts, (236, 232, 240), 2.2, int(230*clamp(crack*1.4)), live=False)
    return (cx, cy, rx, ry)


# ------------------------------------------------------- СТОЛ С ЛАМПОЙ
def desk_night(im, d, cam, t=0.0, lamp=1.0):
    """Стол, лампа, стопка книг, часы на стене — сцена «ты устал»."""
    x0, y0 = 980, 690
    line(d, cam, [(x0-320, y0), (x0+360, y0)], LINE, 3.4)          # столешница
    line(d, cam, [(x0-280, y0), (x0-280, y0+180)], LINE, 3.0)      # ножки
    line(d, cam, [(x0+320, y0), (x0+320, y0+180)], LINE, 3.0)
    # лампа
    line(d, cam, [(x0+250, y0), (x0+250, y0-150), (x0+180, y0-186)], LINE, 3.0)
    d.polygon([cam.p(x0+136, y0-176), cam.p(x0+226, y0-200),
               cam.p(x0+244, y0-146), cam.p(x0+154, y0-124)], fill=FILLD + (255,))
    if lamp > 0.01:
        add_glow(im, *cam.p(x0+170, y0-120), cam.r(300), (255, 196, 120), 0.40*lamp, 2.6)
        soft_ellipse(im, *cam.p(x0+120, y0-6), cam.r(240), cam.r(34),
                     (255, 196, 120), 0.30*lamp)
    # стопка книг
    for i in range(3):
        rrect(d, cam, (x0+180, y0-26-i*22, x0+330, y0-6-i*22), 4,
              mix(FILLD, (92, 70, 48), 0.5*lamp), LINE, 2.4)
    # часы на стене
    ccx, ccy, cr = x0-180, y0-330, 44
    d.ellipse(cam.box(ccx-cr, ccy-cr, ccx+cr, ccy+cr), outline=LINE + (255,), width=_w(cam, 3.0))
    a = t*0.4
    line(d, cam, [(ccx, ccy), (ccx+math.cos(a-1.2)*cr*0.62, ccy+math.sin(a-1.2)*cr*0.62)],
         LINE, 2.6, live=False)
    line(d, cam, [(ccx, ccy), (ccx+math.cos(a*0.08-1.6)*cr*0.42, ccy+math.sin(a*0.08-1.6)*cr*0.42)],
         LINE, 3.0, live=False)


# ------------------------------------------------------------ НОЧНОЙ ГОРОД
_CITY = None
def city(im, d, cam, t=0.0, pan=0.0):
    """Силуэты домов и фонари — фон бега. Здания уезжают вместе с pan."""
    global _CITY
    if _CITY is None:
        rr = random.Random(21)
        _CITY = [(x, rr.uniform(140, 420), rr.uniform(120, 260), rr.random())
                 for x in range(-400, 2600, 150)]
    ground = 760
    for x, h_, w_, seed in _CITY:
        bx = x - pan*0.35
        d.rectangle(cam.box(bx, ground-h_, bx+w_, ground), fill=(11, 13, 19, 255))
        d.rectangle(cam.box(bx, ground-h_, bx+w_, ground), outline=LINE2 + (190,),
                    width=_w(cam, 2.0))
        rr2 = random.Random(int(seed*1000))
        for k in range(int(h_/70)):                              # редкие окна
            if rr2.random() < 0.45: continue
            wx = bx + 18 + rr2.uniform(0, max(1, w_-46))
            wy = ground - h_ + 26 + k*60
            d.rectangle(cam.box(wx, wy, wx+22, wy+26), fill=(126, 112, 74, 170))
    line(d, cam, [(-200, ground), (2300, ground)], LINE, 3.0)
    for i in range(6):                                            # фонари
        lx = 120 + i*380 - pan*0.8
        line(d, cam, [(lx, ground), (lx, ground-250), (lx+54, ground-262)], LINE, 2.8)
        add_glow(im, *cam.p(lx+54, ground-258), cam.r(170), (255, 206, 142), 0.34, 2.4)


# -------------------------------------------------------------- ГРУША
def heavy_bag(im, d, cam, t=0.0, hit=0.0, speed_lines=0.0):
    """Боксёрская груша. hit 0..1 — отдача после удара, искры у точки касания."""
    bx, by = 1230, 400
    sway = math.sin(t*2.2)*10 + hit*46
    line(d, cam, [(bx, 40), (bx+sway*0.4, by-150)], LINE, 2.6, live=False)
    x = bx + sway
    d.rounded_rectangle(cam.box(x-78, by-150, x+78, by+250), radius=cam.r(62),
                        fill=(132, 26, 32, 255))
    d.rounded_rectangle(cam.box(x-78, by-150, x+78, by+250), radius=cam.r(62),
                        outline=(228, 72, 70, 255), width=_w(cam, 3.0))
    for i in range(4):
        line(d, cam, [(x-70, by-60+i*86), (x+70, by-60+i*86)], (176, 44, 48), 2.2, 200, live=False)
    add_glow(im, *cam.p(x, by+40), cam.r(300), (226, 60, 56), 0.26 + 0.30*hit, 2.6)
    if hit > 0.02:                                                # искры
        rr = random.Random(int(t*30))
        for i in range(14):
            a = rr.uniform(-1.2, 1.2)
            ln = rr.uniform(20, 90)*hit
            px, py = x-74, by+70
            line(d, cam, [(px, py), (px-math.cos(a)*ln, py+math.sin(a)*ln)],
                 (255, 214, 120), 2.4, int(220*hit), live=False)
    if speed_lines > 0.02:                                        # линии скорости
        rr = random.Random(5)
        for i in range(16):
            y0 = rr.uniform(120, 820)
            ln = rr.uniform(160, 420)*speed_lines
            line(d, cam, [(rr.uniform(60, 420), y0), (rr.uniform(60, 420)+ln, y0-ln*0.42)],
                 (236, 206, 112), 2.0, int(150*speed_lines), live=False)


# ------------------------------------------------------------- ЛЕСТНИЦА
def stairs(im, d, cam, t=0.0, shift=0.0):
    """Лестница зигзагом вверх направо. shift — уезд вместе с героем."""
    x, y = -200 - shift*0.6, 980
    pts = [(x, y)]
    for i in range(16):
        x += 150; pts.append((x, y))
        y -= 92;  pts.append((x, y))
    d.polygon([cam.p(*p) for p in pts] + [cam.p(x, 1200), cam.p(-400, 1200)],
              fill=(10, 12, 17, 255))
    line(d, cam, pts, LINE, 3.2)


# -------------------------------------------------------------- ВЕРШИНА
def summit(im, d, cam, t=0.0, k=1.0):
    """Единственная цветная сцена фильма: рассвет с вершины."""
    # Градиент неба: (H,1,3) растягивается на всю ширину. Прежняя транспозиция
    # давала полосу шириной 3 px и обрезанное небо справа (поймано 07.11).
    yy = np.linspace(0, 1, H)[:, None, None]
    sky_top = np.array([26, 18, 36], np.float32)
    sky_bot = np.array([236, 126, 46], np.float32)
    a = np.repeat(sky_top + (sky_bot - sky_top) * (yy ** 2.1), W, axis=1)
    sky = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    im.paste(sky.resize((im.width, im.height), Image.BILINEAR), (0, 0))
    sx, sy = 1080, 620
    add_glow(im, sx, sy, 520, (255, 206, 128), 0.75*k, 2.0)
    d.ellipse(cam.box(sx-70, sy-70, sx+70, sy+70), fill=(255, 226, 170, 255))
    for i, (yb, col) in enumerate(((700, (92, 54, 44)), (780, (58, 34, 32)), (860, (28, 18, 20)))):
        rr = random.Random(10+i)
        pts = [(-200, 1200)]
        xx = -200
        while xx < 2200:
            xx += rr.uniform(180, 320)
            pts.append((xx, yb + rr.uniform(-70, 60)))
        pts.append((2200, 1200))
        d.polygon([cam.p(*p) for p in pts], fill=col + (255,))


# --------------------------------------------------------- ЛУЧ И ВСПЫШКА
def spotlight(im, d, cam, cx=960, cy=980, k=1.0):
    """Узкий луч сверху — сцена «дна»."""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay, "RGBA")
    top = cam.p(cx-120, -40); bot_l = cam.p(cx-330, cy+40); bot_r = cam.p(cx+330, cy+40)
    dl.polygon([top, (cam.p(cx+120, -40)), bot_r, bot_l], fill=(226, 232, 244, int(26*k)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(26*SS)), (0, 0))
    soft_ellipse(im, *cam.p(cx, cy), cam.r(330), cam.r(50), (226, 232, 244), 0.22*k)


def flash(im, k):
    """Белая вспышка во весь кадр — переход к вершине."""
    if k <= 0.004: return
    lay = Image.new("RGBA", im.size, (255, 255, 255, int(255*clamp(k))))
    im.alpha_composite(lay, (0, 0))
