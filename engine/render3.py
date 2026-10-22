# -*- coding: utf-8 -*-
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import *
from rooms import *
from people2 import *
from PIL import Image
from multiprocessing import Pool

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames3")
os.makedirs(OUT, exist_ok=True)
DUR = 186.0   # 190 минус 4 срезанные с уличной сцены (см. TRIM ниже)
SKIN2 = (222, 204, 182)

TRIM_AT, TRIM = 18.0, 4.0   # вырез 4 с из уличной сцены, см. frame()

# ---------- сцены: (начало, конец) ----------
S = {
 "cold":   (0,    7),    "street1": (7,   22),   "bed1":  (22,  34),
 "feed":   (34,  48),    "appear":  (48,  62),   "deep":  (62,  74),
 "lying":  (74,  86),    "morning": (86,  98),   "street2":(98, 110),
 "chat":   (110, 124),   "bottom":  (124, 136),  "off":   (136, 146),
 "relapse":(146, 153),   "turn":    (153, 166),  "nights":(166, 178),
 "cafe":   (178, 190),
}
def sc(name): return S[name]
def inside(t, name):
    a, b = S[name]; return a <= t < b
def lt(t, name): return t - S[name][0]

CUTS = [(7, .36), (22, .34), (34, .32), (48, .32), (62, .30), (74, .32), (86, .36),
        (98, .34), (110, .32), (124, .32), (136, .32), (141.5, .28), (146, .28),
        (153, .34), (166, .32), (170, .22), (174, .22), (178, .36), (186.2, .34)]
def cut_dim(t):
    """Затемнение склеек. Считается по НАРУЖНОМУ времени ролика, поэтому точки
    из CUTS, лежащие после выреза (см. TRIM ниже), сдвигаются на столько же.
    Так срез уличной сцены приходится ровно в середину провала в чёрный и
    рывка в кадре не видно."""
    a = 0.0
    for tc, hw in CUTS:
        tc = tc - TRIM if tc >= TRIM_AT + TRIM else tc
        if abs(t-tc) < hw: a = max(a, 255*smoother(1-abs(t-tc)/hw))
    return a

# сквозной наезд по комнатным сценам
ROOM = ["bed1", "appear", "deep", "lying", "morning", "bottom", "off", "relapse", "turn", "nights"]
RSP = [S[k] for k in ROOM]
NSP = [S["feed"], S["chat"]]
def span_time(t, spans):
    s = 0.0
    for a, b in spans:
        if t >= b: s += b-a
        elif t > a: s += t-a
    return s
RT = sum(b-a for a, b in RSP); NT = sum(b-a for a, b in NSP)
def room_cam(t, zoom=0.0):
    k = smoother(span_time(t, RSP)/RT)
    return Cam(lerp(1.12, 1.30, k)+zoom, lerp(820, 880, k), lerp(680, 700, k))
def near_cam(t):
    k = smoother(span_time(t, NSP)/NT)
    return Cam(lerp(1.00, 1.08, k), 960, lerp(520, 500, k))

def fade(t, a, b, inn=0.8, out=0.8):
    if t < a or t > b: return 0
    return int(255*clamp(smoother(clamp(min((t-a)/inn if inn > 0 else 1,
                                            (b-t)/out if out > 0 else 1, 1.0)))))

# Одежда (22.10). Герой во всех сценах в одном худи, иначе он не узнаётся как
# один человек. Второстепенные — в куртках, девушка со своим характером.
HERO  = dict(outfit="hoodie", cloth=(118, 128, 148))
GIRL  = dict(outfit="jacket", cloth=(96, 110, 128), hair=(38, 34, 40),
             lashes=True, scarf=(206, 84, 94))
GUY   = dict(outfit="jacket", cloth=(104, 118, 132))
FRIEND = dict(outfit="jacket", cloth=(92, 118, 102), scarf=(196, 150, 86))

BOT = 930
def narr(d, parts, alpha, im=None, y=BOT, size=50):
    """Подпись внизу кадра.

    ЗАПРЕТ 22.10 (прямое слово пользователя): затемняющая шторка под подписью
    НЕ рисуется никогда. Она срезала пятую часть кадра и читалась как траурная
    рамка — «ни в коем случае её не применять никогда, для таких задач».
    Параметр `im` оставлен, чтобы не переписывать 15 вызовов, и не используется.
    Читаемость держит мягкая тень в четыре стороны, как в оригинале.
    """
    if alpha <= 2: return
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
            for dx, dy in ((0, 3), (0, -2), (3, 1), (-3, 1), (2, 3), (-2, 3)):
                d.text((x+dx, y+dy), txt, font=f, fill=(0, 0, 0, int(alpha*0.42)), anchor="lm")
            d.text((x, y), txt, font=f, fill=(246, 246, 246, alpha), anchor="lm")
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

def demon_anchor(cam, info, up=1.45):
    """Точка над головой демона в экранных координатах — туда кладётся реплика."""
    hc, hr = info["head"], info["hr"]
    return cam.p(hc[0], hc[1] - hr*up)

def _wrap(d, text, f, max_w):
    out, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if not cur or d.textlength(trial, font=f) <= max_w: cur = trial
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def whisper(d, text, t, t0, hold=3.2, type_dur=1.7, size=56, x=330, y=252,
            at=None, max_w=540):
    """Реплика демона: его почерк, печатается буква за буквой, тает.

    22.10, слово пользователя: «если говорит демон, надо эти слова ближе к нему
    ставить». Поэтому реплика теперь привязана к ЕГО голове — `at` принимает
    экранную точку от demon_anchor(), текст центрируется по ней, при нужде
    переносится на две строки и зажимается в границы кадра. Старое положение
    (вверху под счётчиком, как в оригинале Day One) остаётся запасным: без `at`
    всё работает по-прежнему.
    """
    if t < t0: return
    el = t - t0
    out = t0 + type_dur + hold
    a = 255
    if t > out: a = int(255*clamp(smoother(clamp(1 - (t-out)/1.1))))
    if a <= 2: return
    n = max(0, min(len(text), int(len(text)*clamp(el/type_dur) + 0.001)))
    shown = text[:n]
    if not shown: return
    f = FW(size)

    if at is None:
        d.text((x+2, y+3), shown, font=f, fill=(0, 0, 0, int(a*0.45)), anchor="lm")
        d.text((x, y), shown, font=f, fill=(255, 116, 184, a), anchor="lm")
        if n < len(text) and (t*6) % 2 < 1:
            w = d.textlength(shown, font=f)
            d.line([(x+w+6, y-size*0.34), (x+w+6, y+size*0.30)], fill=(255, 116, 184, a), width=3)
        return

    lines = _wrap(d, text, f, max_w)
    lh = size*1.18
    cx, by = at
    # не выпускаем реплику за кинополосы и за края кадра
    top = by - lh*(len(lines)-1)
    if top < H*0.14: by += H*0.14 - top
    left_pad = max(d.textlength(ln, font=f) for ln in lines)/2 + 40
    cx = min(max(cx, left_pad), W - left_pad)

    done = 0
    for i, ln in enumerate(lines):
        if done >= n: break
        part = ln[:max(0, n - done)]
        done += len(ln) + 1
        if not part: break
        ly = by - lh*(len(lines)-1-i)
        d.text((cx+2, ly+3), part, font=f, fill=(0, 0, 0, int(a*0.5)), anchor="mm")
        d.text((cx, ly), part, font=f, fill=(255, 116, 184, a), anchor="mm")
        if n < len(text) and part is not None and (t*6) % 2 < 1 and done >= n:
            w = d.textlength(part, font=f)
            d.line([(cx+w/2+8, ly-size*0.34), (cx+w/2+8, ly+size*0.30)],
                   fill=(255, 116, 184, a), width=3)

def phone_at(im, d, cam, p, w, bright=1.0, rows=0.0, off=False, ang=0.0):
    """Телефон в точке кисти."""
    h = w*1.95
    x, y = p
    d.rounded_rectangle(cam.box(x-w/2, y-h/2, x+w/2, y+h/2), radius=cam.r(w*0.17),
                        fill=(30, 33, 42, 255), outline=(12, 12, 14, 255),
                        width=max(2, int(cam.r(w*0.075))))
    if off: return
    pad = w*0.10
    d.rounded_rectangle(cam.box(x-w/2+pad, y-h/2+pad, x+w/2-pad, y+h/2-pad),
                        radius=cam.r(w*0.10), fill=(150, 176, 226, 255))
    sh = h-pad*2; rowh = sh*0.30
    o = (rows % 1.0)*rowh
    yy = y-h/2+pad-rowh+o; i = 0
    while yy < y+h/2-pad:
        top, bot = max(yy, y-h/2+pad), min(yy+rowh*0.82, y+h/2-pad)
        if bot-top > 2:
            c = [(104, 126, 186), (138, 104, 170), (96, 134, 170)][i % 3]
            d.rounded_rectangle(cam.box(x-w/2+pad*1.5, top, x+w/2-pad*1.5, bot),
                                radius=cam.r(w*0.06), fill=c + (255,))
        yy += rowh; i += 1
    add_glow(im, *cam.p(x, y), cam.r(w*3.6), (150, 185, 255), 0.42*bright, 2.2)

def bed_cover(d, cam, warm=0.0, top=800):
    rrect(d, cam, (312, top, 1140, 886), 18, mix((23, 26, 34), (48, 34, 23), warm), LINE, 4)

def closeup_phone(im, d, cam, t, rows, bright=1.0, chat=False):
    blurred_room(im, "n")
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, 120)), (0, 0))
    from people2 import OUTLINE as OL
    w = 290; x, y = 960, 452
    h = w*1.95
    d.rounded_rectangle(cam.box(x-w/2, y-h/2, x+w/2, y+h/2), radius=cam.r(w*0.16),
                        fill=(30, 33, 42, 255), outline=(12, 12, 14, 255),
                        width=max(2, int(cam.r(w*0.055))))
    pad = w*0.085
    base = (26, 29, 38) if chat else (150, 176, 226)
    d.rounded_rectangle(cam.box(x-w/2+pad, y-h/2+pad, x+w/2-pad, y+h/2-pad),
                        radius=cam.r(w*0.10), fill=base + (255,))
    if not chat:
        sh = h-pad*2; rowh = sh*0.30
        o = (rows % 1.0)*rowh
        yy = y-h/2+pad-rowh+o; i = 0
        while yy < y+h/2-pad:
            top, bot = max(yy, y-h/2+pad), min(yy+rowh*0.82, y+h/2-pad)
            if bot-top > 2:
                c = [(104, 126, 186), (138, 104, 170), (96, 134, 170)][i % 3]
                d.rounded_rectangle(cam.box(x-w/2+pad*1.6, top, x+w/2-pad*1.6, bot),
                                    radius=cam.r(w*0.06), fill=c + (255,))
            yy += rowh; i += 1
    add_glow(im, *cam.p(x, y), cam.r(w*3.0), (150, 185, 255), 0.34*bright, 2.2)
    for sg in (-1, 1):
        hxp = 960 + sg*190
        d.rounded_rectangle(cam.box(hxp-54, 672, hxp+54, 1060), radius=cam.r(52),
                            fill=CREAM + (255,), outline=OL + (255,), width=max(2, int(cam.r(7))))
        for k in range(3):
            fy = 700 + k*72
            xa, xb = hxp, hxp - sg*92
            d.rounded_rectangle(cam.box(min(xa, xb), fy, max(xa, xb), fy+46),
                                radius=cam.r(23), fill=CREAM + (255,),
                                outline=OL + (255,), width=max(2, int(cam.r(6))))

# ---------- кадр ----------
# УКОРОЧЕНИЕ НАЧАЛА (22.10, слово пользователя: «вот это вообще начало,
# "Раньше вечер заканчивался разговором" — длинноватая сцена, надо немного
# укоротить»). Срезано 4 секунды с уличной сцены. Сделано СДВИГОМ ВРЕМЕНИ, а не
# переписыванием шестидесяти абсолютных отметок в раскадровке: наружное время
# после 18-й секунды отображается на внутреннее +4. Любая правка таймингов ниже
# по-прежнему считается в старой сетке, ошибиться негде. Длительность ролика при
# этом 186 с, и ровно на столько же сдвинуты отметки звука в cloud/sound.sh.
def frame(i):
    t_out = i/FPS
    t = t_out + TRIM if t_out >= TRIM_AT else t_out
    im, d = new_frame((6, 7, 10, 255))

    if inside(t, "cold"):
        narr(d, [("Он открыл ленту  ", False), ("  на минуту.  ", True)],
             fade(t, 1.0, 6.4, 0.9, 0.8), y=H/2)

    elif inside(t, "street1"):
        l = lt(t, "street1")
        cam = Cam(lerp(1.00, 1.06, smoother(l/15)), 960, 640)
        street_evening(im, d, cam, t, warm=0.34)
        walk = -160 + l*58
        ph = l*3.1
        draw_person(im, d, cam, (700+walk, 700), 430, walk_pose(ph), t=t, seed=0.0,
                    mood="smile" if (l % 5) > 2.2 else "talk", look=0.5, **HERO)
        draw_person(im, d, cam, (980+walk, 700), 418, walk_pose(ph+2.9), t=t, seed=0.6,
                    mood="talk" if (l % 5) > 2.2 else "smile", look=-0.5, skin=SKIN2,
                    **GIRL)
        narr(d, [("Раньше вечер заканчивался разговором.", False)],
             fade(t, 9.0, 20.5, 0.9, 0.9), im)

    elif inside(t, "bed1"):
        l = lt(t, "bed1")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="23:41",
                phone_glow=(752, 600, 200, 0.26*clamp((l-3)/2)))
        k = smoother(clamp((l-0.6)/2.4))
        inf = draw_person(im, d, cam, (700, 790), 430, pose_mix("stand", "sit_bed", k),
                          t=t, mood="wired" if l > 5.0 else "neutral",
                          look=0.4, lit=0.8*clamp((l-3)/2), **HERO)
        bed_cover(d, cam)
        if l > 3.0: phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*1.2)
        hud(d, cnt(t, 26, 34, 2417, 2436), 0, fade(t, 25.4, 34, 1.0, 0.01))
        narr(d, [("Это было в одиннадцать вечера.", False)], fade(t, 24.5, 32.6, 0.9, 0.9), im)

    elif inside(t, "feed"):
        l = lt(t, "feed")
        closeup_phone(im, d, near_cam(t), t, l*(1.2+l*1.1))
        hud(d, cnt(t, 34, 48, 2436, 2904), 0, 255)
        narr(d, [("Лента не кончается. ", False), ("В этом вся идея.", False)],
             fade(t, 36.0, 46.6, 0.9, 0.8), im)

    elif inside(t, "appear"):
        l = lt(t, "appear")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="01:07", phone_glow=(752, 600, 200, 0.26))
        dem = draw_demon(im, d, cam, (1215, 846), 440, "stand", t=t,
                         alpha=fade(t, 49.4, 62, 2.2, 0.01), heat=0.9)
        inf = draw_person(im, d, cam, (700, 790), 430,
                          pose_mix("sit_bed", "phone_face", smoother(clamp((l-4.5)/3.0))),
                          t=t, mood="wired", look=0.4, lit=0.85, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*1.6)
        hud(d, cnt(t, 48, 62, 2904, 3015), 0, 255)
        whisper(d, "ещё один.", t, 54.6, hold=3.4, size=50,
                at=demon_anchor(cam, dem) if dem else None)
        narr(d, [("Сначала он выбирал, что смотреть.", False)], fade(t, 50.0, 60.6, 0.9, 0.9), im)

    elif inside(t, "deep"):
        l = lt(t, "deep")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="02:14", phone_glow=(752, 604, 190, 0.24))
        dem = draw_demon(im, d, cam, (1150, 846), 462, "stand", t=t, heat=1.05)
        inf = draw_person(im, d, cam, (700, 790), 430,
                          pose_mix("sit_bed", "slump", smoother(clamp(l/9))),
                          t=t, mood="wired" if (l % 5.5) < 1.5 else "tired", lit=0.8,
                          **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 0.9, l*2.0)
        hud(d, cnt(t, 62, 74, 3015, 3108), 0, 255)
        whisper(d, "кто вообще спит в твоём возрасте?", t, 64.4, hold=3.6, size=46,
                at=demon_anchor(cam, dem) if dem else None, max_w=470)
        narr(d, [("Потом выбирали за него.", False)], fade(t, 63.5, 72.6, 0.9, 0.8), im)

    elif inside(t, "lying"):
        l = lt(t, "lying")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="03:21", phone_glow=(770, 648, 220, 0.30))
        dem = draw_demon(im, d, cam, (1010, 790), 430, "sit_bed", t=t, flip=True, heat=1.15)
        inf = draw_person(im, d, cam, (700, 790), 430, "slump", t=t, mood="tired",
                          lit=0.9, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*2.2)
        hud(d, cnt(t, 74, 86, 3108, 3203), 0, 255)
        whisper(d, "видишь? тебе никто и не нужен.", t, 76.6, hold=3.8, size=46,
                at=demon_anchor(cam, dem) if dem else None, max_w=470)
        narr(d, [("Он перестал замечать, где кончается ночь.", False)],
             fade(t, 75.5, 84.6, 0.9, 0.8), im)

    elif inside(t, "morning"):
        l = lt(t, "morning")
        cam = room_cam(t)
        bedroom(im, d, cam, t, warm=0.46, lamp=0.95, clock_text="07:10", rain=False)
        k = smoother(clamp((l-2.5)/4.0))
        draw_person(im, d, cam, (700, lerp(790, 866, k)), 430,
                    pose_mix("slump", "stand", k), t=t, mood="tired", look=-0.2, **HERO)
        if k < 0.25: bed_cover(d, cam)
        hud(d, 3203, 0, 255)
        narr(d, [("Утро стало наказанием.", False)], fade(t, 88.0, 96.6, 0.9, 0.8), im)

    elif inside(t, "street2"):
        l = lt(t, "street2")
        cam = Cam(lerp(1.00, 1.05, smoother(l/12)), 960, 640)
        street_evening(im, d, cam, t, warm=0.10)
        bus_stop(d, cam, 1460)
        draw_person(im, d, cam, (1420, 700), 400, "stand", t=t, seed=1.2, mood="smile",
                    **GIRL,
                    look=-0.4, skin=SKIN2, cloth=(96, 110, 126))
        draw_person(im, d, cam, (1620, 700), 392, "stand", t=t, seed=1.7, mood="talk",
                    **GUY,
                    look=0.4, skin=(234, 222, 206), cloth=(86, 96, 116))
        walk = -260 + l*74
        draw_person(im, d, cam, (560+walk, 712), 430, walk_pose(l*2.6), t=t, seed=0.0,
                    **HERO,
                    mood="tired", look=0.0)
        hud(d, cnt(t, 98, 110, 3203, 3246), 0, 255)
        narr(d, [("Он шёл мимо людей.", False)], fade(t, 100.0, 108.6, 0.9, 0.8), im)

    elif inside(t, "chat"):
        l = lt(t, "chat")
        cam = near_cam(t)
        closeup_phone(im, d, cam, t, 0, bright=0.55, chat=True)
        s_ = cam.s
        d.rounded_rectangle(cam.box(960-120, 452-262, 960+120, 452-202), radius=cam.r(14),
                            fill=(44, 48, 60, 255))
        d.ellipse(cam.box(960-106, 452-252, 960-70, 452-216), fill=(110, 118, 140, 255))
        d.text(cam.p(960-58, 452-234), "Макс", font=FNB(int(26*s_)),
               fill=(228, 232, 242, 255), anchor="lm")
        ox, oy = cam.p(960-112, 452-178)
        y = oy
        if l > 1.0: y = bubble(d, "встретимся в субботу?", ox, y, False, fade(t, 111.5, 124, 0.7, 0.01), int(24*s_))
        if l > 3.4: y = bubble(d, "не могу", ox+256*s_, y, True, fade(t, 113.8, 124, 0.7, 0.01), int(24*s_))
        if l > 6.0: y = bubble(d, "ты норм?", ox, y, False, fade(t, 116.4, 124, 0.7, 0.01), int(24*s_))
        if l > 8.6:
            aa = fade(t, 119.0, 124, 0.8, 0.01)
            for k in range(3):
                pa = int(aa*(0.45+0.55*abs(math.sin(t*2.2-k*0.6))))
                d.ellipse([ox+112*s_+k*24*s_-5*s_, y+24*s_-5*s_,
                           ox+112*s_+k*24*s_+5*s_, y+24*s_+5*s_], fill=(150, 158, 174, pa))
        hud(d, 3246, 0, 255)
        narr(d, [("Друзья перестали спрашивать.", False)], fade(t, 112.5, 122.6, 0.9, 0.8), im)

    elif inside(t, "bottom"):
        l = lt(t, "bottom")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="02:46", phone_glow=(752, 610, 230, 0.34))
        dem = draw_demon(im, d, cam, (930, 790), 430, "sit_bed", t=t, flip=True, heat=1.25)
        inf = draw_person(im, d, cam, (700, 790), 430, "slump", t=t, mood="sad",
                          lit=1.0, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*2.4)
        hud(d, cnt(t, 124, 136, 3246, 3290), 0, 255)
        whisper(d, "остались только мы с тобой.", t, 126.6, hold=3.6, size=46,
                at=demon_anchor(cam, dem) if dem else None, max_w=470)
        narr(d, [("Ждать стало нечего.", False)], fade(t, 126.0, 134.6, 0.9, 0.8), im)

    elif inside(t, "off"):
        l = lt(t, "off")
        if t < 141.5:
            cam = room_cam(t)
            bedroom(im, d, cam, t, clock_text="02:58")
            draw_demon(im, d, cam, (1150, 846), 462, "stand", t=t, alpha=92, heat=0.75)
            inf = draw_person(im, d, cam, (700, 790), 430, "sit_bed", t=t, mood="tired",
                              **HERO)
            bed_cover(d, cam)
            phone_at(im, d, cam, inf["hand_r"], 56, off=True)
            hud(d, 3290, 0, 255)
            narr(d, [("Он выключил телефон.", False)], fade(t, 137.4, 141.2, 0.9, 0.5), im)
        else:
            d.text((W/2, H/2), "через двадцать минут…", font=FN(50),
                   fill=(214, 214, 220, fade(t, 142.2, 145.7, 0.9, 0.7)), anchor="mm")

    elif inside(t, "relapse"):
        l = lt(t, "relapse")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="03:21", phone_glow=(752, 600, 250, 0.42))
        dem = draw_demon(im, d, cam, (1110, 846), 488, "stand", t=t, heat=1.4)
        inf = draw_person(im, d, cam, (700, 790), 430,
                          pose_mix("sit_bed", "phone_face", smoother(clamp((l-3.0)/2.5))),
                          t=t, mood="wired" if l > 2.2 else "sad", lit=1.0, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*2.6)
        hud(d, cnt(t, 146, 153, 3290, 3341), 0, 255)
        whisper(d, "я же говорил.", t, 147.0, hold=2.4, type_dur=1.1, size=50,
                at=demon_anchor(cam, dem) if dem else None)
        narr(d, [("Он включил его снова.", False)], fade(t, 147.4, 152.4, 0.9, 0.6), im)

    elif inside(t, "turn"):
        l = lt(t, "turn")
        cam = room_cam(t)
        bedroom(im, d, cam, t, warm=0.34, lamp=0.80, clock_text="05:48", rain=False)
        k = smoother(clamp((l-1.0)/3.5))
        px = lerp(700, 1180, k)
        if k < 0.98:
            draw_person(im, d, cam, (px, lerp(790, 866, k)), 430,
                        pose_mix("sit_bed", "stand", k), t=t, mood="neutral", look=0.5,
                        **HERO)
        else:
            inf = draw_person(im, d, cam, (1180, 866), 430, "reach", t=t,
                              mood="neutral", look=0.6, **HERO)
            if l > 7.0: phone_at(im, d, cam, inf["hand_r"], 56, 0.9, 0)
        if k < 0.25: bed_cover(d, cam)
        hud(d, 3341, 0, 255)
        narr(d, [("Потом он написал первым.", False)], fade(t, 157.0, 165.0, 0.9, 0.8), im)

    elif inside(t, "nights"):
        l = lt(t, "nights")
        k = min(int(l//4.0), 2)
        night, dal, clk = [(1, 150, "01:40"), (4, 48, "00:35"), (30, 0, "23:05")][k]
        cam = room_cam(t)
        bedroom(im, d, cam, t, warm=0.16 if night == 30 else 0.0,
                lamp=0.5 if night == 30 else 0.0, clock_text=clk)
        draw_demon(im, d, cam, (1150, 846), 462, "stand", t=t, alpha=dal, heat=0.8)
        if night == 30:
            draw_person(im, d, cam, (640, 764), 360, "lie", t=t, mood="neutral",
                        face_on=True, **HERO)
            rrect(d, cam, (312, 742, 1140, 886), 18, (50, 40, 34), LINE, 4)
        else:
            draw_person(im, d, cam, (700, 790), 430, "sit_bed", t=t, mood="neutral", **HERO)
            bed_cover(d, cam)
        hud(d, 0, 0, fade(t, 166+k*4, 170+k*4, 0.7, 0.6), night=night)

    elif t < 186.2:
        l = lt(t, "cafe")
        cam = Cam(lerp(1.02, 1.08, smoother(l/8)), 975, lerp(612, 600, smoother(l/8)))
        cafe_morning(im, d, cam, t)
        draw_person(im, d, cam, (796, 846), 460, "sit_chair", t=t, seed=0.0,
                    mood="smile" if (l % 4) > 1.8 else "talk", look=0.6, lit=0.7, **HERO)
        draw_person(im, d, cam, (1168, 846), 448, "sit_chair", t=t, seed=0.7,
                    mood="talk" if (l % 4) > 1.8 else "smile", look=-0.6,
                    skin=SKIN2, lit=0.7, **FRIEND)
        table_two(d, cam, t)
        cups_and_hands(d, cam, t)
        hud(d, 3341, 1, fade(t, 178.6, 186.2, 1.0, 0.01), strike=True, amber=True)
        a2 = fade(t, 180.4, 186.2, 0.9, 0.01)
        # Шторка под финальной надписью снята 22.10 — см. запрет в narr().
        for dx, dy in ((0, 3), (0, -2), (3, 1), (-3, 1)):
            d.text((W/2+dx, BOT-58+dy), "Он пролистал три тысячи.", font=FN(42),
                   fill=(0, 0, 0, int(a2*0.58)), anchor="mm")
            d.text((W/2+dx, BOT+dy), "Он запомнил один день.", font=FNB(50),
                   fill=(0, 0, 0, int(a2*0.62)), anchor="mm")
        d.text((W/2, BOT-58), "Он пролистал три тысячи.", font=FN(42),
               fill=(236, 238, 244, int(a2*0.92)), anchor="mm")
        d.text((W/2, BOT), "Он запомнил один день.", font=FNB(50),
               fill=(255, 255, 255, a2), anchor="mm")

    else:
        a = fade(t, 186.6, 190, 1.0, 0.01)
        d.text((W/2, 400), "ЛЕНТА", font=FH(92), fill=(238, 240, 246, a), anchor="mm")
        d.text((W/2, 470), "vs", font=FN(40), fill=(150, 156, 170, a), anchor="mm")
        d.text((W/2, 548), "ЖИЗНЬ.", font=FH(92), fill=(238, 240, 246, a), anchor="mm")
        wl = d.textlength("ЖИЗНЬ.", font=FH(92))
        gr = fade(t, 187.2, 190, 0.9, 0.01)
        d.line([(W/2-wl/2, 632), (W/2-wl/2+wl*(gr/255), 632)], fill=RED + (255,), width=6)
        a2 = fade(t, 187.6, 190, 0.9, 0.01)
        d.text((W/2, 712), "Положи телефон.", font=FN(44), fill=(226, 228, 234, a2), anchor="mm")
        d.text((W/2, 772), "Или ещё один свайп.", font=FI(40), fill=RED + (a2,), anchor="mm")

    letterbox(im)
    dim(im, cut_dim(t_out))
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)

if __name__ == "__main__":
    os.nice(19)
    with Pool(4) as p:
        for _ in p.imap_unordered(frame, range(int(DUR*FPS)), chunksize=16): pass
    print("кадров:", int(DUR*FPS))
