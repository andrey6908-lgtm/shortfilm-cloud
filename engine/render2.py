# -*- coding: utf-8 -*-
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import *
from rooms import *
from people import *
from PIL import Image, ImageDraw
from multiprocessing import Pool

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames2")
os.makedirs(OUT, exist_ok=True)
DUR = 52.0

CUTS = [(4.00, 0.34), (9.50, 0.32), (14.50, 0.32), (24.50, 0.32), (30.00, 0.30),
        (31.60, 0.26), (33.30, 0.26), (36.00, 0.30), (38.00, 0.22), (40.00, 0.22),
        (42.00, 0.34), (47.00, 0.34)]
def cut_dim(t):
    a = 0.0
    for tc, hw in CUTS:
        if abs(t-tc) < hw: a = max(a, 255*smoother(1-abs(t-tc)/hw))
    return a

ROOM_SPANS = [(4.0, 9.5), (14.5, 24.5), (30.0, 31.6), (33.3, 36.0), (36.0, 42.0)]
NEAR_SPANS = [(9.5, 14.5), (24.5, 30.0)]
def span_time(t, spans):
    s = 0.0
    for a, b in spans:
        if t >= b: s += b-a
        elif t > a: s += t-a
    return s
RT = sum(b-a for a, b in ROOM_SPANS); NT = sum(b-a for a, b in NEAR_SPANS)
def room_cam(t):
    k = smoother(span_time(t, ROOM_SPANS)/RT)
    return Cam(lerp(1.14, 1.27, k), lerp(830, 880, k), lerp(686, 700, k))
def near_cam(t):
    k = smoother(span_time(t, NEAR_SPANS)/NT)
    return Cam(lerp(1.00, 1.08, k), 960, lerp(520, 500, k))

def fade(t, a, b, inn=0.6, out=0.6):
    if t < a or t > b: return 0
    return int(255*clamp(smoother(clamp(min((t-a)/inn if inn > 0 else 1,
                                            (b-t)/out if out > 0 else 1, 1.0)))))

BOT = 930                                   # базовая линия подписи (внутри кинополос)
def narr(d, parts, alpha, im=None, y=BOT, size=50):
    if alpha <= 2: return
    if im is not None: lower_scrim(im, 0.80*alpha/255, 0.70)
    y = y + 7*(1-alpha/255)
    f = FN(size)
    tot = sum(d.textlength(p[0], font=f) for p in parts)
    x = W/2 - tot/2
    for txt, hl in parts:
        w = d.textlength(txt, font=f)
        if hl:
            d.rounded_rectangle([x-8, y-size*0.62, x+w+6, y+size*0.60], radius=7,
                                fill=MAG + (int(alpha*0.92),))
            d.text((x, y), txt, font=f, fill=(255, 255, 255, alpha), anchor="lm")
        else:
            d.text((x+2, y+2), txt, font=f, fill=(0, 0, 0, int(alpha*0.5)), anchor="lm")
            d.text((x, y), txt, font=f, fill=(242, 242, 242, alpha), anchor="lm")
        x += w

def hud(d, scrolled, known, alpha=255, strike=False, amber=False, night=None):
    if alpha <= 2: return
    fl, fv = FH(30), FH(42)
    x, y = 84, 128
    if night is not None:
        d.text((x, y-12), f"НОЧЬ {night}", font=FH(60), fill=(234, 238, 246, alpha), anchor="lt")
        d.text((x, y+62), "ЗАПОМНИЛ", font=fl, fill=(150, 156, 170, alpha), anchor="lt")
        w2 = d.textlength("ЗАПОМНИЛ ", font=fl)
        d.text((x+w2+10, y+56), "0", font=fv, fill=(235, 238, 245, alpha), anchor="lt")
        return
    d.text((x, y), "ПРОЛИСТАНО", font=fl, fill=(150, 156, 170, alpha), anchor="lt")
    w = d.textlength("ПРОЛИСТАНО ", font=fl)
    d.text((x+w+10, y-6), f"{scrolled:,}".replace(",", " "), font=fv,
           fill=((136, 104, 122) if strike else MAG) + (alpha,), anchor="lt")
    if strike: d.line([(x-6, y+20), (x+w+168, y+20)], fill=(176, 104, 130, alpha), width=4)
    y2 = y+52
    d.text((x, y2), "ЗАПОМНИЛ", font=fl, fill=(150, 156, 170, alpha), anchor="lt")
    w2 = d.textlength("ЗАПОМНИЛ ", font=fl)
    d.text((x+w2+10, y2-6), str(known), font=fv,
           fill=(AMBER if amber else (235, 238, 245)) + (alpha,), anchor="lt")

def bubble(d, text, x, y, mine, alpha, size):
    f = FNB(size)
    tw = d.textlength(text, font=f); pad = size*0.62
    w, h = tw+pad*2, size*1.95
    x0 = x-w if mine else x
    y = y + 5*(1-alpha/255)
    d.rounded_rectangle([x0, y, x0+w, y+h], radius=h*0.46,
                        fill=((56, 118, 235) if mine else (54, 58, 72)) + (alpha,))
    d.text((x0+w/2, y+h/2), text, font=f, fill=(242, 244, 250, alpha), anchor="mm")
    return y+h+size*0.55

def cnt(t, a, b, v0, v1): return int(lerp(v0, v1, clamp((t-a)/(b-a))))

def bed_cover(d, cam, warm=0.0):
    rrect(d, cam, (312, 800, 1140, 886), 18, mix((23, 26, 34), (44, 31, 21), warm), LINE, 4)

def closeup_phone(im, d, cam, t, rows, bright=1.0, chat=False, lt=0.0):
    blurred_room(im, "n")
    im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)), (0, 0))
    phone_in_hand(im, d, cam, 960, 452, 290, bright, rows,
                  screen=('chat' if chat else 'feed'))
    for sg in (-1, 1):                                        # две кисти
        hxp = 960 + sg*190
        d.rounded_rectangle(cam.box(hxp-54, 672, hxp+54, 1060), radius=cam.r(52),
                            fill=CREAM + (255,), outline=OUTLINE + (255,),
                            width=max(2, int(cam.r(7))))
        for k in range(3):
            fy = 700 + k*72
            xa, xb = hxp, hxp - sg*92
            d.rounded_rectangle(cam.box(min(xa, xb), fy, max(xa, xb), fy+46),
                                radius=cam.r(24), fill=CREAM + (255,),
                                outline=OUTLINE + (255,), width=max(2, int(cam.r(6))))

def frame(i):
    t = i/FPS
    im = Image.new("RGBA", (W, H), (6, 7, 10, 255))
    d = ImageDraw.Draw(im, "RGBA")

    if t < 4.0:
        narr(d, [("Он открыл ленту  ", False), ("  на минуту.  ", True)],
             fade(t, 0.6, 3.6, 0.7, 0.6), y=H/2)

    elif t < 9.5:
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="23:41", phone_glow=(746, 620, 215, 0.30))
        person_sitting_bed(im, d, cam, 700, 812, 430, t=t, mood="neutral", look=0.4, lit=0.9)
        phone_in_hand(im, d, cam, 766, 652, 54, 1.0, (t-4)*1.2)
        bed_cover(d, cam)
        hud(d, cnt(t, 5.4, 9.5, 2417, 2431), 0, fade(t, 5.2, 9.5, 0.9, 0.01))
        narr(d, [("Это было в одиннадцать вечера.", False)], fade(t, 4.9, 9.1, 0.7, 0.6), im)

    elif t < 14.5:
        cam = near_cam(t)
        closeup_phone(im, d, cam, t, (t-9.5)*(1.2+(t-9.5)*1.5))
        hud(d, cnt(t, 9.5, 14.5, 2431, 2886), 0, 255)
        narr(d, [("Лента не кончается. ", False), ("В этом вся идея.", False)],
             fade(t, 10.3, 14.2, 0.7, 0.5), im)

    elif t < 20.0:
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="01:07", phone_glow=(746, 620, 215, 0.30))
        demon_figure(im, d, cam, 1215, 884, 452, t=t, alpha=fade(t, 15.3, 20.0, 1.6, 0.01))
        person_sitting_bed(im, d, cam, 700, 812, 430, t=t, mood="neutral", look=0.4, lit=0.9)
        phone_in_hand(im, d, cam, 766, 652, 54, 1.0, (t-14.5)*1.7)
        bed_cover(d, cam)
        hud(d, cnt(t, 14.5, 20.0, 2886, 3012), 0, 255)
        a = fade(t, 17.1, 19.6, 0.8, 0.7)
        if a > 2:
            d.text(cam.p(1215, 640), "ещё один", font=FI(46), fill=(255, 110, 180, a), anchor="mm")
        narr(d, [("Сначала он выбирал, что смотреть.", False)], fade(t, 15.0, 19.4, 0.7, 0.6), im)

    elif t < 24.5:
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="02:14", phone_glow=(746, 620, 200, 0.26))
        demon_figure(im, d, cam, 1150, 884, 476, t=t)
        person_sitting_bed(im, d, cam, 700, 812, 430, t=t, mood="tired", lit=0.8)
        phone_in_hand(im, d, cam, 766, 652, 54, 0.9, (t-20)*2.0)
        bed_cover(d, cam)
        hud(d, cnt(t, 20.0, 24.5, 3012, 3104), 0, 255)
        narr(d, [("Потом выбирали за него.", False)], fade(t, 20.5, 24.2, 0.7, 0.5), im)

    elif t < 30.0:
        cam = near_cam(t); lt = t-24.5
        closeup_phone(im, d, cam, t, 0, bright=0.55, chat=True)
        sc = cam.s
        d.rounded_rectangle(cam.box(960-120, 452-262, 960+120, 452-202), radius=cam.r(14),
                            fill=(44, 48, 60, 255))
        d.ellipse(cam.box(960-106, 452-252, 960-70, 452-216), fill=(110, 118, 140, 255))
        d.text(cam.p(960-58, 452-234), "Макс", font=FNB(int(26*sc)),
               fill=(228, 232, 242, 255), anchor="lm")
        ox, oy = cam.p(960-112, 452-178)
        y = oy
        if lt > 0.4: y = bubble(d, "встретимся в субботу?", ox, y, False, fade(t, 25.0, 30.0, 0.5, 0.01), int(24*sc))
        if lt > 1.6: y = bubble(d, "не могу", ox+256*sc, y, True, fade(t, 26.2, 30.0, 0.5, 0.01), int(24*sc))
        if lt > 2.9: y = bubble(d, "ты норм?", ox, y, False, fade(t, 27.5, 30.0, 0.5, 0.01), int(24*sc))
        if lt > 4.1:
            aa = fade(t, 28.7, 30.0, 0.6, 0.01)
            for k in range(3):
                pa = int(aa*(0.45+0.55*abs(math.sin(t*2.2-k*0.6))))
                d.ellipse([ox+112*sc+k*24*sc-5*sc, y+24*sc-5*sc,
                           ox+112*sc+k*24*sc+5*sc, y+24*sc+5*sc], fill=(150, 158, 174, pa))
        hud(d, 3180, 0, 255)
        narr(d, [("Друзья перестали спрашивать.", False)], fade(t, 26.0, 29.6, 0.7, 0.5), im)

    elif t < 31.6:
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="02:58")
        demon_figure(im, d, cam, 1150, 884, 476, t=t, alpha=92)
        person_sitting_bed(im, d, cam, 700, 812, 430, t=t, mood="neutral")
        phone_in_hand(im, d, cam, 766, 652, 54, off=True)
        bed_cover(d, cam)
        hud(d, 3180, 0, 255)
        narr(d, [("Он выключил телефон.", False)], fade(t, 30.3, 31.5, 0.6, 0.3), im)

    elif t < 33.3:
        d.text((W/2, H/2), "через двадцать минут…", font=FN(50),
               fill=(214, 214, 220, fade(t, 31.9, 33.2, 0.7, 0.5)), anchor="mm")

    elif t < 36.0:
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="03:21", phone_glow=(746, 616, 240, 0.40))
        demon_figure(im, d, cam, 1110, 884, 502, t=t)
        person_sitting_bed(im, d, cam, 700, 812, 430, t=t, mood="sad", lit=1.0)
        phone_in_hand(im, d, cam, 766, 652, 54, 1.0, (t-33.3)*2.5)
        bed_cover(d, cam)
        hud(d, cnt(t, 33.3, 36.0, 3180, 3290), 0, 255)
        narr(d, [("Он включил его снова.", False)], fade(t, 34.0, 35.8, 0.6, 0.3), im)

    elif t < 42.0:
        k = min(int((t-36.0)//2.0), 2)
        night, dal, clk = [(1, 150, "01:40"), (4, 52, "00:35"), (30, 0, "23:05")][k]
        cam = room_cam(t)
        bedroom(im, d, cam, t, warm=0.14 if night == 30 else 0.0,
                lamp=0.5 if night == 30 else 0.0, clock_text=clk)
        demon_figure(im, d, cam, 1150, 884, 476, t=t, alpha=dal)
        if night == 30:
            person_sitting_bed(im, d, cam, 560, 742, 300, t=t, mood="neutral", phone_arm=False)
            rrect(d, cam, (312, 736, 1140, 886), 18, (48, 38, 32), LINE, 4)
        else:
            person_sitting_bed(im, d, cam, 700, 812, 430, t=t, mood="neutral")
            phone_in_hand(im, d, cam, 766, 652, 54, off=True)
            bed_cover(d, cam)
        hud(d, 0, 0, fade(t, 36.0+k*2.0, 38.0+k*2.0, 0.5, 0.4), night=night)

    elif t < 47.0:
        lt = t-42.0
        cam = Cam(lerp(1.02, 1.08, smoother(lt/5.0)), 975, lerp(612, 600, smoother(lt/5.0)))
        cafe_morning(im, d, cam, t)
        person_sitting_chair(im, d, cam, 796, 880, 470, t=t, seed=0.0, mood="smile",
                             look=0.6, lit=0.7)
        person_sitting_chair(im, d, cam, 1168, 880, 456, t=t, seed=0.7, mood="smile",
                             look=-0.6, skin=(222, 206, 186), lit=0.7)
        table_two(d, cam, t)
        cups_and_hands(d, cam, t)
        hud(d, 3290, 1, fade(t, 42.4, 47.0, 0.8, 0.01), strike=True, amber=True)
        a2 = fade(t, 43.2, 47.0, 0.7, 0.01)
        lower_scrim(im, 1.0*a2/255, 0.62)
        d.text((W/2, BOT-58), "Он пролистал три тысячи.", font=FN(42),
               fill=(210, 212, 220, int(a2*0.85)), anchor="mm")
        d.text((W/2, BOT), "Он запомнил один день.", font=FNB(50),
               fill=(255, 255, 255, a2), anchor="mm")

    else:
        a = fade(t, 47.4, 52.0, 0.9, 0.01)
        d.text((W/2, 400), "ЛЕНТА", font=FH(92), fill=(238, 240, 246, a), anchor="mm")
        d.text((W/2, 470), "vs", font=FN(40), fill=(150, 156, 170, a), anchor="mm")
        d.text((W/2, 548), "ЖИЗНЬ.", font=FH(92), fill=(238, 240, 246, a), anchor="mm")
        wl = d.textlength("ЖИЗНЬ.", font=FH(92))
        gr = fade(t, 48.2, 52.0, 0.8, 0.01)
        d.line([(W/2-wl/2, 632), (W/2-wl/2+wl*(gr/255), 632)], fill=RED + (255,), width=6)
        a2 = fade(t, 48.8, 52.0, 0.8, 0.01)
        d.text((W/2, 712), "Положи телефон.", font=FN(44), fill=(226, 228, 234, a2), anchor="mm")
        d.text((W/2, 772), "Или ещё один свайп.", font=FI(40), fill=RED + (a2,), anchor="mm")

    letterbox(im)
    dim(im, cut_dim(t))
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)

if __name__ == "__main__":
    os.nice(19)
    with Pool(4) as p:
        for _ in p.imap_unordered(frame, range(int(DUR*FPS)), chunksize=16): pass
    print("кадров:", int(DUR*FPS))
