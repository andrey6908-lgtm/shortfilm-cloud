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
_WIN = None
def city(im, d, cam, t=0.0, pan=0.0):
    """Ночной город в ТРИ плана с параллаксом, живыми окнами и фонарями.

    Его слово 07.11: «окошки должны загораться, одно загорается, другое
    гаснет, свет чуть ярче». Поэтому у каждого окна свой период и своя фаза —
    город дышит, а не стоит картинкой. Планы расходятся с разной скоростью
    (приём параллакса из лаборатории камеры, блок 1).
    """
    global _CITY, _WIN
    if _CITY is None:
        rr = random.Random(21)
        _CITY = []
        # (глубина, скорость, цвет, высоты) — дальний план почти стоит
        for depth, k, col, hmin, hmax, step in (
                (0, 0.18, (9, 11, 17), 220, 520, 190),
                (1, 0.42, (12, 14, 21), 150, 400, 165),
                (2, 0.82, (15, 17, 25), 110, 260, 145)):
            row = [(x, rr.uniform(hmin, hmax), rr.uniform(110, 250), rr.random())
                   for x in range(-600, 3000, step)]
            _CITY.append((depth, k, col, row))
        _WIN = random.Random(77)
    ground = 780
    win_rr = random.Random(99)
    for depth, k, col, row in _CITY:
        gy = ground - depth*26
        for x, h_, w_, seed in row:
            bx = x - pan*k
            if bx > 2100 or bx + w_ < -200: continue
            d.rectangle(cam.box(bx, gy-h_, bx+w_, gy), fill=col + (255,))
            d.rectangle(cam.box(bx, gy-h_, bx+w_, gy),
                        outline=LINE2 + (150 + depth*30,), width=_w(cam, 2.0))
            cols = max(2, int(w_/62))
            rows_n = max(2, int(h_/74))
            for cy_ in range(rows_n):
                for cx_ in range(cols):
                    ph = win_rr.random()*9.0
                    per = 7.0 + win_rr.random()*16.0
                    on = ((t/per + ph) % 1.0) > 0.42        # окно живёт своим циклом
                    if not on: continue
                    wx = bx + 14 + cx_*(w_-24)/max(1, cols-1) * 0.92
                    wy = gy - h_ + 22 + cy_*62
                    if wy > gy - 26: continue
                    warm = 0.6 + 0.4*math.sin(t*1.7 + ph*6)
                    c = (int(214*warm) + 30, int(178*warm) + 24, int(96*warm) + 16)
                    d.rectangle(cam.box(wx, wy, wx+24, wy+30), fill=c + (235,))
                    if depth == 2 and ((t/per + ph) % 1.0) > 0.92:
                        add_glow(im, *cam.p(wx+12, wy+15), cam.r(64), (255, 210, 130), 0.30, 2.4)
    line(d, cam, [(-300, ground), (2400, ground)], LINE, 3.0)
    for i in range(7):                                        # фонари ближнего плана
        lx = 60 + i*330 - pan*0.95
        if lx < -220 or lx > 2200: continue
        line(d, cam, [(lx, ground), (lx, ground-262), (lx+58, ground-276)], LINE, 2.8)
        fl = 0.42 + 0.10*math.sin(t*3.1 + i*1.7)              # фонарь подрагивает
        add_glow(im, *cam.p(lx+58, ground-272), cam.r(230), (255, 206, 142), fl, 2.2)
        soft_ellipse(im, *cam.p(lx+58, ground-6), cam.r(190), cam.r(26),
                     (255, 196, 128), 0.20)
    add_glow(im, *cam.p(1680 - pan*0.10, 180), cam.r(240), (176, 196, 236), 0.16, 2.6)


# -------------------------------------------------------------- ГРУША
def heavy_bag(im, d, cam, t=0.0, hit=0.0, speed_lines=0.0, hero_x=900, floor=980):
    """Груша на уровне груди героя + обстановка зала.

    Его слово 07.11: «она как-то должна быть на уровне хотя бы его, очень
    бедная сцена». Поэтому мешок опущен к высоте груди, а вокруг появился зал:
    маты, гантели, стойка, окно с решёткой и лампа под потолком.
    """
    bx = hero_x + 330
    chest = floor - 300                     # грудь героя ростом 420 от пола
    sway = math.sin(t*2.2)*12 + hit*54
    x = bx + sway
    # лампа под потолком и её конус
    line(d, cam, [(bx-40, 0), (bx-40, 120)], LINE, 2.4, live=False)
    d.polygon([cam.p(bx-96, 120), cam.p(bx+16, 120), cam.p(bx+70, 190), cam.p(bx-150, 190)],
              fill=FILLD + (255,))
    add_glow(im, *cam.p(bx-40, 210), cam.r(420), (255, 212, 150), 0.26, 2.6)
    # окно зала с решёткой
    rrect(d, cam, (bx+300, chest-290, bx+660, chest+40), 10, (10, 12, 18), LINE2, 2.6)
    for i in range(4):
        line(d, cam, [(bx+300+i*90, chest-290), (bx+300+i*90, chest+40)], LINE2, 2.0, 170, live=False)
    # маты у стены
    for i in range(3):
        rrect(d, cam, (hero_x-620+i*34, floor-150, hero_x-470+i*34, floor), 10, FILLD, LINE2, 2.4)
    # гантели на полу
    for gx in (hero_x-300, hero_x-220):
        line(d, cam, [(gx-26, floor-16), (gx+26, floor-16)], LINE, 5.0, live=False)
        d.ellipse(cam.box(gx-40, floor-32, gx-14, floor), fill=FILLD + (255,))
        d.ellipse(cam.box(gx+14, floor-32, gx+40, floor), fill=FILLD + (255,))
    line(d, cam, [(hero_x-900, floor), (hero_x+900, floor)], LINE, 3.2)
    # подвес и сам мешок — центр на уровне груди
    line(d, cam, [(bx, 150), (x, chest-170)], LINE, 2.6, live=False)
    d.rounded_rectangle(cam.box(x-82, chest-170, x+82, chest+200), radius=cam.r(66),
                        fill=(132, 26, 32, 255))
    d.rounded_rectangle(cam.box(x-82, chest-170, x+82, chest+200), radius=cam.r(66),
                        outline=(228, 72, 70, 255), width=_w(cam, 3.0))
    for i in range(4):
        line(d, cam, [(x-74, chest-100+i*84), (x+74, chest-100+i*84)],
             (176, 44, 48), 2.2, 200, live=False)
    add_glow(im, *cam.p(x, chest), cam.r(330), (226, 60, 56), 0.24 + 0.32*hit, 2.6)
    soft_ellipse(im, *cam.p(x, floor-10), cam.r(130), cam.r(24), (0, 0, 0), 0.55)
    if hit > 0.02:
        rr = random.Random(int(t*30))
        for i in range(16):
            a = rr.uniform(-1.3, 1.3)
            ln = rr.uniform(26, 110)*hit
            px, py = x-78, chest+10
            line(d, cam, [(px, py), (px-math.cos(a)*ln, py+math.sin(a)*ln)],
                 (255, 214, 120), 2.4, int(230*hit), live=False)
    if speed_lines > 0.02:
        rr = random.Random(5)
        for i in range(18):
            y0 = rr.uniform(120, 860)
            ln = rr.uniform(160, 420)*speed_lines
            x0 = rr.uniform(60, 460)
            line(d, cam, [(x0, y0), (x0+ln, y0-ln*0.42)],
                 (236, 206, 112), 2.0, int(140*speed_lines), live=False)


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
def summit(im, d, cam, t=0.0, k=1.0, rise=0.0):
    """Вершина на рассвете — единственная цветная сцена, и она ЖИВАЯ.

    Его слово 07.11: «стоит эта сцена, нет динамики, не на чем залипнуть».
    Поэтому солнце ВСХОДИТ (rise 0→1), небо вместе с ним теплеет, облака
    идут поперёк кадра, по склонам ползёт свет.
    """
    yy = np.linspace(0, 1, H)[:, None, None]
    top = np.array([26, 18, 36], np.float32) + np.array([10, 6, 4]) * rise
    bot = np.array([208, 104, 42], np.float32) + np.array([40, 34, 22]) * rise
    a = np.repeat(top + (bot - top) * (yy ** (2.3 - 0.5*rise)), W, axis=1)
    sky = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    im.paste(sky.resize((im.width, im.height), Image.BILINEAR), (0, 0))

    # облака: длинные полосы, идут поперёк кадра с разной скоростью
    rr = random.Random(4)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay, "RGBA")
    for i in range(7):
        y0 = 180 + i*74 + rr.uniform(-20, 20)
        spd = 10 + i*4
        x0 = (rr.uniform(-600, 1800) + t*spd) % 3000 - 700
        ln = rr.uniform(300, 760)
        hh = rr.uniform(14, 30)
        al = int(40 + 50*rise - i*4)
        dl.rounded_rectangle([int(x0*SS), int(y0*SS), int((x0+ln)*SS), int((y0+hh)*SS)],
                             radius=int(hh*SS/2), fill=(255, 196, 150, max(0, al)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10*SS)), (0, 0))

    sx = 1080
    sy = int(lerp(700, 540, rise))                 # солнце поднимается
    add_glow(im, sx, sy, int(460 + 180*rise), (255, 206, 128), 0.55 + 0.30*rise, 2.0)
    d.ellipse(cam.box(sx-70, sy-70, sx+70, sy+70), fill=(255, 230, 182, 255))

    for i, (yb, col) in enumerate(((700, (92, 54, 44)), (780, (58, 34, 32)),
                                   (860, (28, 18, 20)))):
        rr2 = random.Random(10+i)
        pts = [(-200, 1200)]
        xx = -200
        while xx < 2200:
            xx += rr2.uniform(180, 320)
            pts.append((xx, yb + rr2.uniform(-70, 60)))
        pts.append((2200, 1200))
        c = tuple(int(v + (34 + i*8)*rise) for v in col)   # свет ползёт по склонам
        d.polygon([cam.p(*p) for p in pts], fill=c + (255,))


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


# ------------------------------------------------------- СНАРЯДЫ И ЗАЛ
def dumbbell(d, cam, p, r=26, col=(150, 156, 170)):
    """Гантель в кисти: гриф и два блина."""
    x, y = p
    line(d, cam, [(x-r*1.5, y), (x+r*1.5, y)], col, 5.0, live=False)
    for s_ in (-1, 1):
        d.rounded_rectangle(cam.box(x+s_*r*1.5-r*0.42, y-r*0.86, x+s_*r*1.5+r*0.42, y+r*0.86),
                            radius=cam.r(r*0.3), fill=col + (255,))


def kettlebell(d, cam, p, r=34):
    """Гиря: шар и дужка."""
    x, y = p
    d.ellipse(cam.box(x-r, y-r*0.9, x+r, y+r), fill=(66, 70, 84, 255))
    d.ellipse(cam.box(x-r, y-r*0.9, x+r, y+r), outline=LINE + (255,), width=_w(cam, 2.6))
    d.arc(cam.box(x-r*0.66, y-r*1.9, x+r*0.66, y-r*0.3), start=200, end=340,
          fill=LINE + (255,), width=_w(cam, 5.0))


def treadmill(im, d, cam, t=0.0, x=960, floor=980, speed=0.0):
    """Беговая дорожка: полотно бежит, на консоли мигают цифры."""
    bw, bh = 460, 46
    rrect(d, cam, (x-bw/2, floor-bh, x+bw/2, floor), 14, FILLD, LINE, 3.0)
    off = (t*speed*120) % 46
    for i in range(int(bw/46)+2):
        px = x-bw/2+10+i*46-off
        if px < x-bw/2+6 or px > x+bw/2-6: continue
        line(d, cam, [(px, floor-bh+8), (px, floor-8)], LINE2, 2.2, 170, live=False)
    line(d, cam, [(x+bw/2-30, floor-bh), (x+bw/2-10, floor-250)], LINE, 3.0)
    line(d, cam, [(x-bw/2+30, floor-bh), (x-bw/2+10, floor-250)], LINE, 3.0)
    line(d, cam, [(x-bw/2+10, floor-250), (x+bw/2-10, floor-250)], LINE, 3.0)
    rrect(d, cam, (x+bw/2-150, floor-350, x+bw/2+20, floor-250), 10, (12, 14, 20), LINE, 2.6)
    add_glow(im, *cam.p(x+bw/2-65, floor-300), cam.r(90), (120, 210, 255), 0.26, 2.4)
    soft_ellipse(im, *cam.p(x, floor-6), cam.r(240), cam.r(28), (0, 0, 0), 0.5)


def pull_bar(d, cam, x=960, top=240, floor=980):
    """Турник у стены — фон для залов, чтобы сцена не была пустой."""
    line(d, cam, [(x-260, top), (x+260, top)], LINE, 4.0)
    line(d, cam, [(x-260, top), (x-260, floor)], LINE, 3.0)
    line(d, cam, [(x+260, top), (x+260, floor)], LINE, 3.0)
