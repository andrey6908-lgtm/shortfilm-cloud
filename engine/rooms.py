# -*- coding: utf-8 -*-
"""Локации в манере оригинала: чёрный фон, предметы светлыми контурами."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from film import W, H, SS, SW, SH, Cam, mix, lerp, clamp, add_glow, soft_ellipse, flicker, AMBER, RED, MAG

LINE  = (96, 104, 124)      # контур мебели в темноте
LINE2 = (64, 70, 86)        # дальний план
FILLD = (17, 19, 25)        # заливка предметов — чуть светлее фона
BG    = (7, 8, 11)

def _w(cam, v): return max(1, int(cam.r(v)))

def rrect(d, cam, box, r, fill=None, line=LINE, lw=3.0, alpha=255):
    b = cam.box(*box)
    if fill: d.rounded_rectangle(b, radius=cam.r(r), fill=fill + (alpha,))
    if line: d.rounded_rectangle(b, radius=cam.r(r), outline=line + (alpha,), width=_w(cam, lw))

def line(d, cam, pts, col=LINE, lw=3.0, alpha=255):
    d.line([cam.p(*p) for p in pts], fill=col + (alpha,), width=_w(cam, lw), joint="curve")

def bedroom(im, d, cam, t=0.0, warm=0.0, lamp=0.0, rain=True, clock_text="23:41",
            phone_glow=None, calendar="ОКТ"):
    """Спальня ночью. phone_glow=(x,y,r,strength)."""
    d.rectangle([0, 0, W, H], fill=mix(BG, (26, 17, 11), warm) + (255,))
    L  = mix(LINE,  (122, 92, 60), warm)
    L2 = mix(LINE2, (86, 62, 40), warm)
    F  = mix(FILLD, (32, 22, 15), warm)

    # --- окно ---
    wx0, wy0, wx1, wy1 = 1180, 190, 1570, 560
    d.rounded_rectangle(cam.box(wx0, wy0, wx1, wy1), radius=cam.r(10),
                        fill=mix((13, 16, 26), (30, 21, 14), warm) + (255,))
    if rain:
        rr = random.Random(31)
        for i in range(30):
            spd = rr.uniform(150, 240)
            x0 = rr.uniform(wx0+10, wx1-10)
            y0 = (rr.uniform(0, 1)*(wy1-wy0) + t*spd) % (wy1-wy0) + wy0
            ln = min(rr.uniform(20, 38), wy1-y0)
            if ln < 4: continue
            line(d, cam, [(x0, y0), (x0-ln*0.20, y0+ln)], (118, 130, 154), 2.2, 150)
        for i in range(10):                                   # капли на стекле
            x0 = rr.uniform(wx0+16, wx1-16); y0 = rr.uniform(wy0+16, wy1-16)
            rad = rr.uniform(3, 6)
            d.ellipse(cam.box(x0-rad, y0-rad, x0+rad, y0+rad), fill=(130, 142, 166, 140))
    rnd = random.Random(7)
    for i in range(14):                                       # дальние окна
        lx = rnd.uniform(wx0+18, wx1-34); ly = rnd.uniform(wy0+24, wy1-36)
        sz = rnd.uniform(9, 15)
        tw = 0.5 + 0.5*math.sin(t*0.5 + i*1.7)
        d.rectangle(cam.box(lx, ly, lx+sz, ly+sz*1.2),
                    fill=mix((34, 40, 58), AMBER, 0.25+0.45*tw) + (255,))
    d.rounded_rectangle(cam.box(wx0, wy0, wx1, wy1), radius=cam.r(10),
                        outline=L + (255,), width=_w(cam, 4))
    line(d, cam, [((wx0+wx1)/2, wy0), ((wx0+wx1)/2, wy1)], L, 4)
    line(d, cam, [(wx0, (wy0+wy1)/2), (wx1, (wy0+wy1)/2)], L, 4)
    line(d, cam, [(wx0-18, wy1+12), (wx1+18, wy1+12)], L, 5)   # подоконник

    # --- календарь ---
    cx0, cy0 = 1700, 210
    rrect(d, cam, (cx0, cy0, cx0+170, cy0+44), 6, (122, 40, 46), (168, 70, 74), 3)
    rrect(d, cam, (cx0, cy0+44, cx0+170, cy0+200), 6, F, L, 3)
    for r_ in range(4):
        line(d, cam, [(cx0+10, cy0+74+r_*32), (cx0+160, cy0+74+r_*32)], L2, 2)
    line(d, cam, [(cx0+42, cy0+192), (cx0+42, cy0+230)], L2, 3)

    # --- стол со стопкой книг ---
    tx0, ty = 1690, 640
    line(d, cam, [(tx0-20, ty), (tx0+250, ty)], L, 5)
    line(d, cam, [(tx0+10, ty), (tx0+10, ty+180)], L, 4)
    line(d, cam, [(tx0+230, ty), (tx0+230, ty+180)], L, 4)
    for i, c in enumerate([(132, 74, 62), (62, 92, 118), (120, 110, 60), (78, 70, 112)]):
        rrect(d, cam, (tx0+40+i*6, ty-26-i*24, tx0+210-i*4, ty-4-i*24), 3, c, L2, 2)

    # --- кровать ---
    rrect(d, cam, (300, 470, 372, 880), 10, F, L, 4)               # изголовье
    rrect(d, cam, (312, 690, 1140, 880), 16, F, L, 4)              # матрас
    rrect(d, cam, (352, 640, 596, 712), 26, F, L, 3)               # подушка
    line(d, cam, [(340, 880), (340, 940)], L, 4)                   # ножки
    line(d, cam, [(1110, 880), (1110, 940)], L, 4)

    # --- тумбочка ---
    rrect(d, cam, (120, 700, 292, 900), 8, F, L, 4)
    line(d, cam, [(132, 790), (280, 790)], L2, 3)
    d.ellipse(cam.box(196, 744, 216, 764), outline=L + (255,), width=_w(cam, 3))

    # --- часы ---
    cl_x, cl_y = 206, 668
    rrect(d, cam, (cl_x-66, cl_y-26, cl_x+66, cl_y+26), 6, (14, 12, 16), L2, 3)
    from film import FH
    sep = ":" if (t % 2.0) < 1.0 else " "
    d.text(cam.p(cl_x, cl_y), clock_text.replace(":", sep), font=FH(max(8, int(cam.r(38)))),
           fill=(255, 62, 70, 255), anchor="mm")
    # живой свет (22.10): приборы дышат яркостью, у каждого своя фаза
    add_glow(im, *cam.p(cl_x, cl_y), cam.r(130), (255, 40, 50),
             0.26*flicker(t, 0.11, 0.20, 0.8), 2.3)

    # --- пол ---
    line(d, cam, [(-200, 952), (W+200, 952)], L2, 4)
    if lamp > 0:
        add_glow(im, *cam.p(980, 300), cam.r(620), AMBER,
                 0.26*lamp*flicker(t, 0.43, 0.14, 0.5), 2.3)
    if phone_glow:
        px, py, pr, st = phone_glow
        add_glow(im, *cam.p(px, py), cam.r(pr), (150, 185, 255), st, 2.3)

def cafe_morning(im, d, cam, t=0.0):
    """Тёплое кафе — финальная сцена."""
    d.rectangle([0, 0, W, H], fill=(38, 26, 19, 255))
    d.rectangle(cam.box(-200, 680, W+200, H+200), fill=(28, 19, 14, 255))
    line(d, cam, [(-200, 680), (W+200, 680)], (92, 64, 42), 5)
    # окно с утренним городом
    wx0, wy0, wx1, wy1 = 420, 196, 1520, 660
    d.rectangle(cam.box(wx0, wy0, wx1, wy1), fill=(58, 44, 58, 255))
    arr = np.zeros((H, 1, 3), dtype=np.uint8)
    for y in range(H): arr[y, 0] = mix((62, 46, 62), (250, 176, 96), clamp((y-wy0)/(wy1-wy0)) ** 1.5)
    box = cam.box(wx0, wy0, wx1, wy1)
    bw_, bh_ = max(1, int((box[2]-box[0])*SS)), max(1, int((box[3]-box[1])*SS))
    sky = Image.fromarray(arr, "RGB").resize((bw_, bh_)).convert("RGBA")
    im.alpha_composite(sky, (int(box[0]*SS), int(box[1]*SS)))
    rnd = random.Random(21)
    for i in range(14):
        bx = wx0 + 20 + i*78 + rnd.uniform(-14, 14)
        bh = rnd.uniform(120, 330)
        d.rectangle(cam.box(bx, wy1-bh, bx+rnd.uniform(48, 76), wy1), fill=(44, 30, 26, 255))
    d.rectangle(cam.box(wx0, wy0, wx1, wy1), outline=(112, 80, 52, 255), width=_w(cam, 6))
    line(d, cam, [((wx0+wx1)/2, wy0), ((wx0+wx1)/2, wy1)], (112, 80, 52), 5)
    # лампа
    d.line([cam.p(960, 0), cam.p(960, 250)], fill=(70, 50, 34, 255), width=_w(cam, 4))
    d.chord(cam.box(870, 210, 1050, 330), 180, 360, fill=(246, 190, 96, 255))
    d.chord(cam.box(870, 210, 1050, 330), 180, 360, outline=(130, 96, 50, 255), width=_w(cam, 4))
    add_glow(im, *cam.p(960, 320), cam.r(420), (255, 198, 112),
             0.55*flicker(t, 0.67, 0.11, 0.45), 2.0)
    # полка с кружками
    line(d, cam, [(70, 372), (310, 372)], (104, 74, 48), 5)
    for i in range(3):
        rrect(d, cam, (90+i*76, 320, 146+i*76, 370), 8, (76, 66, 58), (122, 94, 66), 3)
    # растение
    for a in range(5):
        ang = -1.35 + a*0.34
        line(d, cam, [(1640, 862), (1640+math.cos(ang)*132, 862-abs(math.sin(ang))*216-52)],
             (62, 110, 70), 14)
    rrect(d, cam, (1582, 848, 1698, 956), 10, (120, 74, 52), (160, 104, 70), 4)

def table_two(d, cam, t=0.0):
    """Столик на двоих: столешница, ножка, две чашки с паром."""
    rrect(d, cam, (610, 800, 1350, 826), 8, (104, 70, 44), (146, 104, 64), 4)
    rrect(d, cam, (946, 826, 990, 962), 4, (96, 64, 40), (134, 94, 58), 3)
    rrect(d, cam, (882, 958, 1054, 976), 6, (96, 64, 40), (134, 94, 58), 3)

def cups_and_hands(d, cam, t=0.0, skin=(238, 230, 218), skin2=(222, 206, 186)):
    from people import OUTLINE
    for cx, col in ((796, skin), (1168, skin2)):              # кисти на столешнице
        d.rounded_rectangle(cam.box(cx-46, 770, cx+46, 806), radius=cam.r(18),
                            fill=col + (255,), outline=OUTLINE + (255,),
                            width=max(2, int(cam.r(5))))
    for cx in (912, 1056):                                    # чашки
        rrect(d, cam, (cx-30, 756, cx+30, 800), 10, (240, 238, 234), (122, 112, 102), 4)
        d.arc(cam.box(cx+24, 764, cx+54, 794), 300, 60, fill=(122, 112, 102, 255), width=_w(cam, 4))
        rrect(d, cam, (cx-42, 798, cx+42, 808), 5, (236, 232, 226), (122, 112, 102), 3)
        for k in range(2):
            ph = t*1.3 + k*2.1 + cx*0.01
            pts = [(cx-9+k*18 + math.sin(ph+j*0.85)*8, 750-j*20) for j in range(5)]
            line(d, cam, pts, (186, 176, 168), 2.6, 110)


def street_evening(im, d, cam, t=0.0, warm=0.30):
    """Вечерняя улица: дома, фонари, тротуар."""
    sky_t = mix((16, 19, 30), (52, 32, 22), warm)
    sky_b = mix((34, 38, 54), (120, 72, 46), warm)
    arr = np.zeros((H, 1, 3), dtype=np.uint8)
    for y in range(H): arr[y, 0] = mix(sky_t, sky_b, (y/H) ** 1.5)
    im.alpha_composite(Image.fromarray(arr, "RGB").resize((SW, SH)).convert("RGBA"), (0, 0))
    rnd = random.Random(44)
    for layer, (col, hmin, hmax) in enumerate([((22, 25, 38), 300, 560), ((14, 16, 25), 180, 380)]):
        c = mix(col, (44, 28, 20), warm)
        x = -160
        while x < W + 160:
            bw_ = rnd.uniform(130, 210); bh = rnd.uniform(hmin, hmax)
            d.rectangle(cam.box(x, 820-bh, x+bw_, 840), fill=c + (255,))
            d.rectangle(cam.box(x, 820-bh, x+bw_, 840), outline=mix(c, (120, 128, 150), 0.35) + (255,),
                        width=_w(cam, 3))
            if layer == 0:
                for k in range(int(bh//92)):
                    for j in range(3):
                        lit = (math.sin(k*2.7 + j*1.9 + x*0.013) > -0.25)
                        d.rectangle(cam.box(x+26+j*44, 820-bh+34+k*92, x+52+j*44, 820-bh+70+k*92),
                                    fill=mix(c, AMBER, 0.62 if lit else 0.10) + (255,))
            x += bw_ + rnd.uniform(14, 40)
    d.rectangle(cam.box(-200, 840, W+200, H+200), fill=mix((20, 23, 34), (46, 30, 20), warm) + (255,))
    line(d, cam, [(-200, 840), (W+200, 840)], (112, 120, 142), 4)
    line(d, cam, [(-200, 966), (W+200, 966)], (72, 78, 96), 3)
    for lx in (180, 820, 1480):                            # фонари
        line(d, cam, [(lx, 840), (lx, 420)], (110, 118, 140), 7)
        line(d, cam, [(lx, 424), (lx+74, 410)], (110, 118, 140), 6)
        d.ellipse(cam.box(lx+58, 398, lx+102, 428), fill=(255, 222, 160, 255))
        add_glow(im, *cam.p(lx+80, 414), cam.r(240), (255, 210, 150),
                 0.42*flicker(t, lx*0.0013, 0.17, 0.7), 2.1)

def bus_stop(d, cam, x=1400):
    rrect(d, cam, (x-300, 470, x+300, 500), 6, (34, 38, 50), (118, 126, 148), 4)
    for sx in (x-280, x+280):
        line(d, cam, [(sx, 500), (sx, 840)], (118, 126, 148), 5)
    rrect(d, cam, (x-270, 520, x+270, 820), 4, (26, 30, 42), (86, 94, 116), 3)
    rrect(d, cam, (x-170, 700, x+200, 726), 6, (40, 44, 58), (118, 126, 148), 4)
    for sx in (x-150, x+180):
        line(d, cam, [(sx, 726), (sx, 840)], (118, 126, 148), 4)
