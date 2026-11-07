# -*- coding: utf-8 -*-
"""«ДИСЦИПЛИНА» — перенос хита Day One Films (5,9 млн) на наш движок.

Структура снята покадрово с оригинала `8atK0pF4oJY`, разбор лежит в
D:\\YouTube\\ОБРАЗЕЦ DAY ONE\\РАЗБОР DISCIPLINE\\РАЗБОР.md. Берём скелет и
приёмы, рисуем своими руками: ни одного кадра оригинала в сборку не входит.

Главный приём — счётчик дней в углу: сначала считает проигранные дни
(1 → 47 → 112 → 340), после перелома — выигранные (3 → 12 → 64 → 138 → 270).
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import *
from lang_disc import L
from rooms import *
from rooms import _w, rrect, line as rline
import rooms_disc as rd
from people2 import *
from render3 import phone_at          # телефон в руке — общий с первым фильмом
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_disc")
os.makedirs(OUT, exist_ok=True)

SPEED = float(os.environ.get("SHORTFILM_SPEED", "1"))
DUR = 158.0 * SPEED

S = {
 "open":   (0,   5),    "sleep":  (5,  16),   "sofa1":  (16, 24),
 "desk":   (24, 32),    "sofa2":  (32, 38),   "bed2":   (38, 42),
 "mirror": (42, 50),    "bottom": (50, 62),   "alarm":  (62, 72),
 "run":    (72, 82),    "push1":  (82, 92),   "bag":    (92, 106),
 "push2":  (106, 112),  "climb":  (112, 126), "flash":  (126, 128),
 "summit": (128, 142),  "morning":(142, 148), "title":  (148, 158),
}
def inside(t, n): a, b = S[n]; return a <= t < b
def lt(t, n): return t - S[n][0]

CUTS = [(5, .34), (16, .32), (24, .32), (32, .30), (38, .30), (42, .36),
        (50, .34), (62, .36), (72, .34), (82, .30), (92, .32), (106, .30),
        (112, .32), (142, .34), (148, .36)]
def cut_dim(t):
    a = 0.0
    for tc, hw in CUTS:
        if abs(t-tc) < hw: a = max(a, 255*smoother(1-abs(t-tc)/hw))
    return a

HERO = dict(skin=CREAM, ink=INK)
BOT = H - 150


def fade(t, a, b, inn=0.8, out=0.8):
    if t < a or t > b: return 0.0
    return clamp(min((t-a)/inn, (b-t)/out))


def caption(d, im, text, alpha, y=BOT, size=52, bold=False, col=CREAM):
    """Строка повествования по центру, как в оригинале — без плашки."""
    if alpha <= 0.004: return
    f = (FNB if bold else FN)(size)
    w = d.textlength(text, font=f)
    d.text((W/2 - w/2, y), text, font=f, fill=col + (int(255*alpha),))


def day_badge(d, n, alpha=1.0):
    """Счётчик дней в левом верхнем углу — главный приём фильма."""
    if alpha <= 0.004: return
    f = FH(30)
    d.text((72, 78), f'{L["day"]} {n}', font=f, fill=(206, 212, 226, int(230*alpha)))


def whisper(d, text, t, t0, hold=3.0, size=46, at=(0, 0), type_dur=1.3):
    """Почерк демона: печатается по буквам, красным, строчными."""
    k = (t - t0) / type_dur
    if k < 0 or t > t0 + hold + 1.2: return
    n = int(len(text) * clamp(k))
    a = clamp((t0 + hold + 1.2 - t) / 0.8)
    if n <= 0: return
    d.text(at, text[:n], font=FW(size), fill=RED + (int(235*a),))


def frame(i):
    t = i/FPS/SPEED
    im, d = new_frame((6, 7, 10, 255))

    # ---------------------------------------------------------- НАЧАЛО
    if inside(t, "open"):
        caption(d, im, L["open"], fade(t, 0.8, 4.6, 1.0, 0.8), y=H/2 - 26)

    # -------------------------------------------- КАЖДЫЙ ДЕНЬ ОДИНАКОВО
    elif inside(t, "sleep"):
        l = lt(t, "sleep")
        cam = Cam(1.12, 860, 690)
        ring = l < 3.2
        bedroom(im, d, cam, t, clock_text="5:08" if l > 6.5 else "5:00", rain=False)
        draw_person(im, d, cam, (700, 790), 430, "lie", t=t, mood="tired",
                    look=0.2, **HERO)
        if ring:
            add_glow(im, *cam.p(612, 606), cam.r(190), RED, 0.34*flicker(t, 9.0), 2.4)
        if 3.4 < l < 8.0:
            whisper(d, L["snooze"], t, S["sleep"][0]+3.6, hold=3.0, size=44, at=(980, 300))
        for k in range(2):                                   # «z z» над головой
            if l > 4.2:
                yy = 470 - k*52 - (l*8) % 40
                d.text(cam.p(840+k*26, yy), "z", font=FI(30+k*10),
                       fill=(196, 204, 222, 150))

    # ------------------------------------------------- ПАДЕНИЕ: ЧЕТЫРЕ ДНЯ
    elif inside(t, "sofa1"):
        l = lt(t, "sofa1")
        cam = Cam(1.10, 900, 700)
        _sofa(im, d, cam, t)
        inf = draw_person(im, d, cam, (820, 800), 420, "phone_face", t=t,
                          mood="wired", look=0.4, lit=0.8, **HERO)
        phone_at(im, d, cam, inf["hand_r"], 54, 1.0, l*1.4)
        dem = draw_demon(im, d, cam, (1290, 846), 430, "stand", t=t,
                         alpha=fade(t, 17.0, 24, 1.6, 0.01), heat=0.95)
        day_badge(d, 1)
        whisper(d, L["w1"], t, 17.6, hold=2.4, at=(1180, 300))
        whisper(d, L["w2"], t, 20.6, hold=2.6, at=(1140, 360))

    elif inside(t, "desk"):
        l = lt(t, "desk")
        cam = Cam(1.08, 940, 700)
        rd.desk_night(im, d, cam, t, lamp=1.0)
        inf = draw_person(im, d, cam, (900, 870), 420, "sit_chair", t=t,
                          mood="tired", look=0.3, lit=0.9, **HERO)
        dem = draw_demon(im, d, cam, (560, 880), 440, "reach", t=t,
                         alpha=fade(t, 25.0, 32, 1.6, 0.01), heat=1.0)
        day_badge(d, 47)
        whisper(d, L["w3"], t, 25.8, hold=3.0, at=(430, 330))

    elif inside(t, "sofa2"):
        l = lt(t, "sofa2")
        cam = Cam(1.14, 900, 700)
        _sofa(im, d, cam, t)
        inf = draw_person(im, d, cam, (860, 800), 420, "slump", t=t,
                          mood="wired", look=0.3, lit=0.85, **HERO)
        phone_at(im, d, cam, inf["hand_r"], 54, 1.0, l*2.2)
        day_badge(d, 112)

    elif inside(t, "bed2"):
        l = lt(t, "bed2")
        cam = Cam(1.26, 760, 700)
        bedroom(im, d, cam, t, clock_text="5:00", rain=False)
        draw_person(im, d, cam, (700, 790), 430, "lie", t=t, mood="tired", **HERO)
        add_glow(im, *cam.p(612, 606), cam.r(200), RED, 0.40*flicker(t, 11.0), 2.4)
        day_badge(d, 340)

    # ------------------------------------------------------------ ЗЕРКАЛО
    elif inside(t, "mirror"):
        l = lt(t, "mirror")
        cam = Cam(1.06, 960, 640)
        crack = clamp((l-4.6)/1.4)
        rd.mirror(im, d, cam, t, crack=crack, glow_k=0.7+0.5*crack)
        draw_demon(im, d, cam, (1260, 790), 360, "stand", t=t,
                   alpha=int(235*clamp((l-0.6)/1.6)), heat=1.1)
        draw_person(im, d, cam, (640, 880), 430, "stand", t=t, mood="tired",
                    look=0.6, lit=0.5, **HERO)
        if l > 4.2:
            f = FW(118)
            w = d.textlength(L["w4"], font=f)
            d.text((W/2 - w/2 - 180, 300), L["w4"], font=f,
                   fill=RED + (int(240*clamp((l-4.2)/0.5)),))

    # --------------------------------------------------------------- ДНО
    elif inside(t, "bottom"):
        l = lt(t, "bottom")
        rd.spotlight(im, d, Cam(1.0), 960, 980, k=clamp(l/1.4))
        cam = Cam(1.0, 960, 700)
        draw_person(im, d, cam, (960, 960), 330, "curl", t=t, mood="tired",
                    look=0.0, lit=0.9, **HERO)
        caption(d, im, L["mid_1"], fade(t, 51.0, 56.4, 0.9, 0.9), y=420)
        caption(d, im, L["mid_2a"], fade(t, 57.2, 61.6, 0.9, 0.7), y=400)
        caption(d, im, L["mid_2b"], fade(t, 58.4, 61.8, 0.9, 0.7), y=460, bold=True)

    # ------------------------------------------------------- ПЕРЕЛОМ: ДЕНЬ 1
    elif inside(t, "alarm"):
        l = lt(t, "alarm")
        if l < 5.0:                                          # будильник крупно
            cam = Cam(2.3, 612, 606)
            bedroom(im, d, cam, t, clock_text="5:00", rain=False)
            sh = math.sin(t*34)*6*clamp((2.6-l)/2.6)
            add_glow(im, *cam.p(612+sh, 606), cam.r(260), RED, 0.5, 2.2)
        else:                                                # сел на кровати
            cam = Cam(1.16, 820, 700)
            bedroom(im, d, cam, t, clock_text="5:00", rain=False)
            draw_person(im, d, cam, (700, 790), 430,
                        pose_mix("lie", "sit_bed", smoother(clamp((l-5.2)/2.0))),
                        t=t, mood="neutral", look=0.4, lit=0.6, **HERO)
            day_badge(d, 1, alpha=clamp((l-7.0)/1.0))

    # ------------------------------------------------------------- ПАХОТА
    elif inside(t, "run"):
        l = lt(t, "run")
        cam = Cam(1.0, 960, 560)
        rd.city(im, d, cam, t, pan=l*150)
        ph = l*3.4
        draw_person(im, d, cam, (960, 760), 400,
                    pose_mix("run_a", "run_b", 0.5+0.5*math.sin(ph)),
                    t=t, mood="angry", look=0.5, **HERO)
        _band(d, cam, (960, 760), 400, math.sin(ph))
        day_badge(d, 3)

    elif inside(t, "push1"):
        l = lt(t, "push1")
        cam = Cam(1.05, 960, 820)
        line(d, cam, [(200, 980), (1720, 980)], LINE, 3.2)
        k = 0.5+0.5*math.sin(l*3.0)
        inf = draw_person(im, d, cam, (900, 900), 400,
                          pose_mix("pushup_up", "pushup_dn", k), t=t,
                          mood="angry", look=0.3, **HERO)
        _band(d, cam, (900, 900), 400, 0, lie=True)
        day_badge(d, 12)
        if l > 4.0:                                          # счёт повторов
            n = 1 + int((l-4.0)*1.1)
            f = FNB(150)
            w = d.textlength(str(n), font=f)
            d.text((W/2-w/2, 230), str(n), font=f,
                   fill=CREAM + (int(235*fade(t, 86.0, 91.6, 0.5, 0.6)),))

    elif inside(t, "bag"):
        l = lt(t, "bag")
        cam = Cam(1.0, 960, 620)
        hit = max(0.0, math.sin(l*2.6))**3
        rd.heavy_bag(im, d, cam, t, hit=hit, speed_lines=clamp((l-1.0)/2.0)*0.8)
        draw_person(im, d, cam, (780, 860), 420,
                    pose_mix("guard", "punch", hit), t=t, mood="angry",
                    look=0.6, **HERO)
        _band(d, cam, (780, 860), 420, 0)
        day_badge(d, 64)
        whisper(d, L["w5"], t, 94.0, hold=2.6, size=52, at=(1420, 240))

    elif inside(t, "push2"):
        l = lt(t, "push2")
        cam = Cam(1.1, 960, 820)
        line(d, cam, [(200, 980), (1720, 980)], LINE, 3.2)
        k = 0.5+0.5*math.sin(l*3.6)
        draw_person(im, d, cam, (900, 900), 400,
                    pose_mix("pushup_up", "pushup_dn", k), t=t, mood="angry", **HERO)
        _band(d, cam, (900, 900), 400, 0, lie=True)
        day_badge(d, 138)

    # ---------------------------------------------------------- ПОСЛЕДНИЙ БОЙ
    elif inside(t, "climb"):
        l = lt(t, "climb")
        cam = Cam(1.0, 960, 620)
        rd.stairs(im, d, cam, t, shift=l*60)
        ph = l*2.2
        draw_person(im, d, cam, (760, 900 - l*22), 400,
                    pose_mix("climb", "stand", 0.5+0.5*math.sin(ph)),
                    t=t, mood="angry", look=0.5, **HERO)
        _band(d, cam, (760, 900 - l*22), 400, math.sin(ph))
        day_badge(d, 270)
        if l > 4.0:                                          # рука демона сверху
            a = clamp((l-4.0)/1.2) * clamp((12.0-l)/1.5)
            add_glow(im, *cam.p(1560, 230), cam.r(420), MAG, 0.30*a, 2.6)
            d.polygon([cam.p(1420, 60), cam.p(1720, 110), cam.p(1660, 330),
                       cam.p(1500, 300)], fill=(26, 8, 14, int(240*a)))
        caption(d, im, L["keep"], fade(t, 118.0, 125.0, 1.0, 0.8), y=250, bold=True)

    elif inside(t, "flash"):
        rd.flash(im, clamp(1.0 - abs(lt(t, "flash") - 0.7)/0.7))

    # ------------------------------------------------------------- ВЕРШИНА
    elif inside(t, "summit"):
        l = lt(t, "summit")
        cam = Cam(1.0, 960, 620)
        rd.summit(im, d, cam, t, k=1.0)
        draw_person(im, d, cam, (900, 700), 300, "stand", t=t, mood="neutral",
                    look=0.5, lit=1.0, **HERO)
        _band(d, cam, (900, 700), 300, 0)
        rd.flash(im, clamp((1.2-l)/1.2)*0.9)
        caption(d, im, L["save_1"], fade(t, 130.0, 136.0, 1.0, 0.8), y=250)
        caption(d, im, L["save_2"], fade(t, 136.6, 141.6, 1.0, 0.8), y=250, bold=True)

    # ------------------------------------------------------------ УТРО
    elif inside(t, "morning"):
        l = lt(t, "morning")
        cam = Cam(1.14, 820, 700)
        bedroom(im, d, cam, t, warm=0.55, clock_text="5:00", rain=False)
        draw_person(im, d, cam, (700, 790), 430, "sit_bed", t=t, mood="neutral",
                    look=0.4, lit=0.7, **HERO)
        draw_demon(im, d, cam, (1320, 880), 150, "stand", t=t,
                   alpha=int(150*clamp((6.0-l)/6.0)), heat=0.6)

    # ------------------------------------------------------------- ТИТР
    else:
        l = lt(t, "title")
        a = fade(t, 148.6, 158.0, 1.2, 0.9)
        f = FNB(132)
        w = d.textlength(L["title"], font=f)
        d.text((W/2-w/2, 400), L["title"], font=f, fill=CREAM + (int(250*a),))
        if l > 2.6:                                          # красное подчёркивание
            k = clamp((l-2.6)/1.1)
            d.rounded_rectangle([W/2-w/2, 556, W/2-w/2+w*k, 566], radius=5,
                                fill=RED + (int(240*a),))
        caption(d, im, L["end_1"], fade(t, 152.6, 158.0, 1.0, 0.9), y=640, size=46)
        caption(d, im, L["end_2"], fade(t, 153.6, 158.0, 1.0, 0.9), y=706, size=46,
                bold=True, col=RED)

    # ------------------------------------------------------------- ФИНИШ
    dim = cut_dim(t)
    if dim > 1:
        lay = Image.new("RGBA", im.size, (0, 0, 0, int(dim)))
        im.alpha_composite(lay, (0, 0))
    letterbox(im, 0.085)
    out = finish(im)
    out.save(os.path.join(OUT, f"f{i:05d}.jpg"), quality=92)


def _sofa(im, d, cam, t):
    """Диван — он есть в первом фильме, но там внутри сцены; здесь отдельно."""
    rrect(d, cam, (560, 700, 1420, 900), 26, FILLD, LINE, 3.2)
    rrect(d, cam, (560, 600, 1420, 720), 24, FILLD, LINE, 3.0)
    line(d, cam, [(600, 900), (600, 960)], LINE, 3.0)
    line(d, cam, [(1380, 900), (1380, 960)], LINE, 3.0)
    line(d, cam, [(200, 960), (1720, 960)], LINE, 3.0)


def _band(d, cam, hip, h, ph, lie=False):
    """Красная повязка на голове — знак второй половины фильма."""
    hx = hip[0] + (h*0.10 if lie else 0)
    hy = hip[1] - h*(0.52 if lie else 1.06)
    r = h*0.115
    d.line([cam.p(hx-r*1.15, hy-r*0.34), cam.p(hx+r*1.15, hy-r*0.34)],
           fill=rd.RED_D + (255,), width=_w(cam, r*0.42))
    d.line([cam.p(hx+r*0.9, hy-r*0.3), cam.p(hx+r*1.7, hy+r*0.3+ph*6)],
           fill=rd.RED_D + (235,), width=_w(cam, r*0.26))
