# -*- coding: utf-8 -*-
"""«ЛЕНТА vs ЖИЗНЬ» — версия FABLE (12.11.2026). Своя режиссура на том же
движке, в том же стиле и с теми же утверждёнными элементами, что v11:
счётчик-HUD, демон с ореолом и почерком, подписи внизу, часы красным,
календарь, финальная карточка.

Чем отличается от render3 (v11):
  * часы — сквозной мотив: ролик открывается не текстом, а красными цифрами
    в темноте; «через двадцать минут» показано не карточкой, а бегущими
    цифрами часов; ночь дана ХРОНОМЕТРОМ — шесть статичных планов по 4 с с
    прыгающими часами (00:12 → 03:21), герой оседает, демон с каждым планом
    ближе и крупнее, камера с каждым планом теснее;
  * демон впервые появляется ОТРАЖЕНИЕМ В ОКНЕ, и только потом — в комнате;
  * на улице днём девушка МАШЕТ ему, а он идёт, уткнувшись в телефон;
  * переписка рифмуется: в конце тот же экран, но теперь пишет ОН первым;
  * демон после перелома не просто бледнеет — мельчает по ночам 1 → 4 → 30;
  * в кафе телефон лежит экраном вниз на столе.

Длительность 186 с — ровно как у v11, потому что звуковой рецепт облака
(щелчок 133,6 с, шорох 148,9 с, смена музыки 168 с) привязан к секундам;
ключевые события версии поставлены на те же отметки.

Запуск в облаке: ship.sh --film render_fable <имя>
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import *
from lang import L
from rooms import *
from people2 import *
from people2 import _Off
import camera3 as cam3
from PIL import Image, ImageFilter
import numpy as np
from multiprocessing import Pool

# общие рисовалки берём у v11 — они утверждены, переписывать их незачем
from render3 import (narr, hud, bubble, whisper, phone_at, closeup_phone, bed_cover,
                     demon_anchor, fade, cnt, talks, HERO, GIRL, GUY, FRIEND, SKIN2, BOT)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_fable")
os.makedirs(OUT, exist_ok=True)
SPEED = float(os.environ.get("SHORTFILM_SPEED", "1"))
DUR = 186.0 * SPEED

# ---------- свои реплики (русская версия) ----------
T = {
    "dawn":    "Ночь кончилась без него.",
    "wave":    "Он шёл мимо людей.",
    "typing":  "Макс печатает…",
    "my_msg":  "прости. суббота в силе?",
    "reply":   "в силе.",
}

# ---------- сцены ----------
S = {
 "clock":   (0, 6),      "street1": (6, 19),     "bed1":   (19, 30),
 "feed":    (30, 40),    "window":  (40, 50),    "lapse":  (50, 74),
 "dawn":    (74, 84),    "morning": (84, 96),    "street2":(96, 110),
 "chat":    (110, 124),  "bottom":  (124, 133),  "off":    (133, 141),
 "twenty":  (141, 146),  "relapse": (146, 153),  "turn":   (153, 162),
 "chat2":   (162, 168),  "nights":  (168, 176),  "cafe":   (176, 182.4),
 "title":   (182.4, 186.5),
}
def inside(t, name):
    a, b = S[name]; return a <= t < b
def lt(t, name): return t - S[name][0]

# склейки — мягкие провалы в чёрный; внутри «хронометра» склейки ЖЁСТКИЕ
CUTS = [(6, .30), (19, .34), (30, .30), (40, .30), (50, .30), (74, .34), (84, .36),
        (96, .34), (110, .32), (124, .32), (133, .26), (141, .30), (146, .26),
        (153, .34), (162, .30), (168, .30), (176, .36), (182.4, .34), (186.3, .30)]
def cut_dim(t):
    a = 0.0
    for tc, hw in CUTS:
        if abs(t-tc) < hw: a = max(a, 255*smoother(1-abs(t-tc)/hw))
    return a

# сквозной наезд по комнатным сценам (кроме хронометра — там камера стоит)
ROOM = ["bed1", "window", "dawn", "morning", "bottom", "off", "relapse", "turn", "nights"]
RSP = [S[k] for k in ROOM]
def span_time(t, spans):
    s = 0.0
    for a, b in spans:
        if t >= b: s += b-a
        elif t > a: s += t-a
    return s
RT = sum(b-a for a, b in RSP)
def room_cam(t):
    k = smoother(span_time(t, RSP)/RT)
    return Cam(lerp(1.12, 1.28, k), lerp(820, 870, k), lerp(680, 700, k))

# ---------- свои рисовалки ----------
def big_clock(im, d, text, t, cx, cy, size=120, alpha=255, glow=0.5):
    """Красные цифры часов в темноте — мотив версии."""
    if alpha <= 2: return
    sep = ":" if (t % 2.0) < 1.0 else " "
    f = FH(size)
    d.text((cx+3, cy+4), text.replace(":", sep), font=f,
           fill=(0, 0, 0, int(alpha*0.5)), anchor="mm")
    d.text((cx, cy), text.replace(":", sep), font=f,
           fill=(255, 62, 70, alpha), anchor="mm")
    add_glow(im, cx, cy, size*3.2, (255, 40, 50),
             glow*(alpha/255)*flicker(t, 0.11, 0.20, 0.8), 2.3)

def window_demon(im, d, cam, t, alpha, heat=0.8, h=300):
    """Демон ОТРАЖЕНИЕМ в оконном стекле: рисуется на слой размером с окно
    (плюс запас под ореол), обрезается по раме и кладётся полупрозрачным.
    Слой не полноэкранный — память бережём, как велит film.py."""
    if alpha <= 6: return
    wx0, wy0, wx1, wy1 = 1180, 190, 1570, 560
    box = cam.box(wx0, wy0, wx1, wy1)
    pad = cam.r(h*0.9)
    X0, Y0 = box[0]-pad, box[1]-pad
    LW = int((box[2]-box[0] + pad*2)*SS); LH = int((box[3]-box[1] + pad*2)*SS)
    lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    dl = SDraw(lay, "RGBA")
    draw_demon(lay, dl, _Off(cam, X0, Y0), (1375, wy1+h*0.10), h, "stand",
               t=t, alpha=255, heat=heat)
    lay = lay.filter(ImageFilter.GaussianBlur(1.6*SS))
    crop = lay.crop((int(pad*SS), int(pad*SS),
                     int(pad*SS + (box[2]-box[0])*SS), int(pad*SS + (box[3]-box[1])*SS)))
    arr = np.asarray(crop).astype(np.float32)
    arr[..., 3] *= 0.82*(alpha/255.0)
    im.alpha_composite(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"),
                       (int(box[0]*SS), int(box[1]*SS)))
    # перекладины рамы поверх отражения
    line(d, cam, [((wx0+wx1)/2, wy0), ((wx0+wx1)/2, wy1)], LINE, 4)
    line(d, cam, [(wx0, (wy0+wy1)/2), (wx1, (wy0+wy1)/2)], LINE, 4)

def chat_header(d, cam):
    s_ = cam.s
    d.rounded_rectangle(cam.box(960-120, 452-262, 960+120, 452-202), radius=cam.r(14),
                        fill=(44, 48, 60, 255))
    d.ellipse(cam.box(960-106, 452-252, 960-70, 452-216), fill=(110, 118, 140, 255))
    d.text(cam.p(960-58, 452-234), L["chat_name"], font=FNB(int(26*s_)),
           fill=(228, 232, 242, 255), anchor="lm")
    return cam.p(960-112, 452-178)

def typing_dots(d, cam, ox, y, t, alpha):
    if alpha <= 2: return
    s_ = cam.s
    for k in range(3):
        pa = int(alpha*(0.45+0.55*abs(math.sin(t*2.2-k*0.6))))
        d.ellipse([ox+112*s_+k*24*s_-5*s_, y+24*s_-5*s_,
                   ox+112*s_+k*24*s_+5*s_, y+24*s_+5*s_], fill=(150, 158, 174, pa))

def phone_flat(d, cam, cx, cy, w=70):
    """Телефон экраном вниз на столе."""
    d.rounded_rectangle(cam.box(cx-w/2, cy-11, cx+w/2, cy+11), radius=cam.r(8),
                        fill=(30, 33, 42, 255), outline=(12, 12, 14, 255),
                        width=max(2, int(cam.r(4))))
    d.rounded_rectangle(cam.box(cx-w/2+8, cy-5, cx+w/2-8, cy+5), radius=cam.r(4),
                        fill=(44, 48, 58, 255))

def wave_pose(t):
    """Девушка машет: рука поднята, кисть качается."""
    p = dict(POSES["stand"])
    # рука уходит ВНЕШНЕЙ стороной, иначе кисть прячется за длинными волосами
    # (поймано предпросмотром 12.11: при -62° машущей руки не было видно)
    p["ua_l"] = -150; p["fa_l"] = -100 + math.sin(t*5.2)*18
    return p

def walk_phone(phase):
    """Идёт, уткнувшись в телефон: ноги шагают, рука держит экран у лица."""
    p = walk_pose(phase)
    p["ua_r"] = 58; p["fa_r"] = -54; p["head"] = 10; p["lean"] = 4 + math.sin(phase)*1.2
    return p

# ---------- кадр ----------
def frame(i):
    t = i/FPS/SPEED
    im, d = new_frame((6, 7, 10, 255))

    if inside(t, "clock"):
        l = lt(t, "clock")
        big_clock(im, d, "23:41", t, W/2, H/2-70, 120, fade(t, 0.4, 6.0, 1.4, 0.6), 0.6)
        narr(d, [(L["n01a"], False), (L["n01b"], True)],
             fade(t, 1.8, 6.0, 0.9, 0.6), im, y=H/2+110)

    elif inside(t, "street1"):
        l = lt(t, "street1")
        cam = Cam(lerp(1.00, 1.06, smoother(l/13)), 960, 640)
        walk = -160 + l*58
        pan = walk*0.85
        street_evening(im, d, cam, t, warm=0.34, pan=pan)
        gcam = cam3.plane(cam, pan, cam3.K_GROUND)
        ph = l*3.1
        hero_x, girl_x = 700+walk, 980+walk
        for fx, fh in ((hero_x, 430), (girl_x, 418)):
            cam3.ground_shadow(im, gcam, (fx, 700), fh, street_lamp_x(fx))
        cam3.figure_light(
            im, lambda lay, ld: draw_person(lay, ld, gcam, (hero_x, 700), 430,
                                            walk_pose(ph), t=t, seed=0.0,
                                            mood=talks(l, 1.0), look=0.5, **HERO),
            gcam.p(street_lamp_x(hero_x), 0)[0])
        cam3.figure_light(
            im, lambda lay, ld: draw_person(lay, ld, gcam, (girl_x, 700), 418,
                                            walk_pose(ph+2.9), t=t, seed=0.6,
                                            mood=talks(l), look=-0.5, skin=SKIN2, **GIRL),
            gcam.p(street_lamp_x(girl_x), 0)[0])
        narr(d, [(L["n02"], False)], fade(t, 7.6, 17.8, 0.9, 0.9), im)

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
        hud(d, cnt(t, 23, 30, 2417, 2436), 0, fade(t, 22.4, 30, 1.0, 0.01))
        narr(d, [(L["n03"], False)], fade(t, 20.8, 28.8, 0.9, 0.9), im)

    elif inside(t, "feed"):
        l = lt(t, "feed")
        cam = Cam(lerp(1.00, 1.07, smoother(l/10)), 960, 510)
        closeup_phone(im, d, cam, t, l*(1.2+l*1.3))
        hud(d, cnt(t, 30, 40, 2436, 2904), 0, 255)
        narr(d, [(L["n04a"], False), (L["n04b"], False)],
             fade(t, 31.6, 38.8, 0.9, 0.8), im)

    elif inside(t, "window"):
        l = lt(t, "window")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="00:12", phone_glow=(752, 600, 200, 0.26))
        # сначала — отражение в стекле, потом он уже в комнате
        window_demon(im, d, cam, t, fade(t, 41.0, 46.4, 1.8, 1.2), heat=0.8)
        dem = draw_demon(im, d, cam, (1300, 846), 420, "stand", t=t,
                         alpha=fade(t, 46.0, 50, 1.6, 0.01), heat=0.9)
        inf = draw_person(im, d, cam, (700, 790), 430,
                          pose_mix("sit_bed", "phone_face", smoother(clamp((l-2.0)/3.0))),
                          t=t, mood="wired", look=0.4, lit=0.85, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*1.6)
        hud(d, cnt(t, 40, 50, 2904, 2960), 0, 255)
        whisper(d, L["w1"], t, 47.2, hold=2.2, size=50,
                at=demon_anchor(cam, dem) if dem else None)
        narr(d, [(L["n05"], False)], fade(t, 41.0, 48.6, 0.9, 0.9), im)

    elif inside(t, "lapse"):
        # ХРОНОМЕТР: шесть статичных планов по 4 с, жёсткие склейки.
        # Часы прыгают, герой оседает, демон ближе и крупнее, камера теснее.
        l = lt(t, "lapse")
        k = min(int(l//4.0), 5); lk = l - k*4.0
        clk = ["00:12", "00:48", "01:30", "02:14", "02:51", "03:21"][k]
        cam = Cam(1.14 + k*0.04, 830 + k*8, 690 + k*3)
        bedroom(im, d, cam, t, clock_text=clk,
                phone_glow=(752, 600+k*8, 200+k*8, 0.24+k*0.02))
        dpos = [((1300, 846), 420, "stand", False, 0.9),
                ((1210, 846), 440, "stand", False, 1.0),
                ((1130, 846), 462, "stand", False, 1.05),
                ((1030, 790), 430, "sit_bed", True, 1.1),
                ((960, 790), 440, "sit_bed", True, 1.2),
                ((920, 790), 450, "sit_bed", True, 1.25)][k]
        dem = draw_demon(im, d, cam, dpos[0], dpos[1], dpos[2], t=t, flip=dpos[3],
                         heat=dpos[4])
        pose = ["phone_face", "phone_face", "sit_bed", "sit_bed", "slump", "slump"][k]
        mood = ["wired", "wired", "wired", "tired", "wired", "tired"][k]
        inf = draw_person(im, d, cam, (700, 790), 430, pose, t=t, mood=mood,
                          look=0.4 if k < 3 else 0.2, lit=0.85+k*0.03, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 0.95, l*2.0)
        hud(d, cnt(t, 50, 74, 2960, 3203), 0, 255)
        if k == 2:
            whisper(d, L["w2"], t, 58.3, hold=2.0, type_dur=1.3, size=44,
                    at=demon_anchor(cam, dem) if dem else None, max_w=470)
        if k == 4:
            whisper(d, L["w3"], t, 66.3, hold=2.0, type_dur=1.3, size=44,
                    at=demon_anchor(cam, dem) if dem else None, max_w=470)
        narr(d, [(L["n06"], False)], fade(t, 51.0, 60.6, 0.9, 0.8), im)
        narr(d, [(L["n07"], False)], fade(t, 63.0, 72.6, 0.9, 0.8), im)

    elif inside(t, "dawn"):
        l = lt(t, "dawn")
        cam = room_cam(t)
        wk = 0.12 + 0.18*smoother(clamp(l/10))
        bedroom(im, d, cam, t, warm=wk, lamp=0.0, clock_text="05:02", rain=False,
                phone_glow=(752, 610, 210, 0.22))
        dem = draw_demon(im, d, cam, (900, 790), 440, "sit_bed", t=t, flip=True,
                         heat=1.2, alpha=fade(t, 74, 84, 0.01, 2.5))
        inf = draw_person(im, d, cam, (700, 790), 430, "slump", t=t, mood="tired",
                          lit=0.8, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 0.9, l*1.4)
        hud(d, 3203, 0, 255)
        narr(d, [(T["dawn"], False)], fade(t, 75.4, 82.8, 0.9, 0.8), im)

    elif inside(t, "morning"):
        l = lt(t, "morning")
        cam = room_cam(t)
        bedroom(im, d, cam, t, warm=0.46, lamp=0.95, clock_text="07:10", rain=False)
        k = smoother(clamp((l-2.5)/4.0))
        draw_person(im, d, cam, (700, lerp(790, 866, k)), 430,
                    pose_mix("slump", "stand", k), t=t, mood="tired", look=-0.2, **HERO)
        if k < 0.25: bed_cover(d, cam)
        # будильник: часы вспыхивают ярче в такт
        add_glow(im, *cam.p(206, 668), cam.r(170), (255, 40, 50),
                 0.30*(0.5+0.5*abs(math.sin(l*6.0))) if l < 3.0 else 0.0, 2.3)
        hud(d, 3203, 0, 255)
        narr(d, [(L["n08"], False)], fade(t, 86.0, 94.6, 0.9, 0.8), im)

    elif inside(t, "street2"):
        l = lt(t, "street2")
        cam = Cam(lerp(1.00, 1.05, smoother(l/14)), 960, 640)
        street_evening(im, d, cam, t, warm=0.10)
        bus_stop(d, cam, 1460)
        # девушка машет ему — он не поднимает глаз от экрана
        gp = wave_pose(t) if 3.0 < l < 9.5 else "stand"
        draw_person(im, d, cam, (1420, 700), 400, gp, t=t, seed=1.2,
                    mood="smile" if l < 9.5 else "sad", **GIRL, look=-0.4, skin=SKIN2)
        draw_person(im, d, cam, (1620, 700), 392, "stand", t=t, seed=1.7, mood=talks(l, 0.4),
                    **GUY, look=0.4, skin=(234, 222, 206))
        walk = -300 + l*72
        inf = draw_person(im, d, cam, (520+walk, 712), 430, walk_phone(l*2.6), t=t, seed=0.0,
                          **HERO, mood="wired", look=0.0, lit=0.5)
        phone_at(im, d, cam, inf["hand_r"], 50, 0.8, l*1.8)
        hud(d, cnt(t, 96, 110, 3203, 3246), 0, 255)
        narr(d, [(T["wave"], False)], fade(t, 98.0, 107.6, 0.9, 0.8), im)

    elif inside(t, "chat"):
        l = lt(t, "chat")
        cam = Cam(lerp(1.00, 1.06, smoother(l/14)), 960, 505)
        closeup_phone(im, d, cam, t, 0, bright=0.55, chat=True)
        ox, oy = chat_header(d, cam)
        s_ = cam.s; y = oy
        if l > 1.0: y = bubble(d, L["chat_1"], ox, y, False, fade(t, 111.5, 124, 0.7, 0.01), int(24*s_))
        if l > 3.4: y = bubble(d, L["chat_2"], ox+256*s_, y, True, fade(t, 113.8, 124, 0.7, 0.01), int(24*s_))
        if l > 6.0: y = bubble(d, L["chat_3"], ox, y, False, fade(t, 116.4, 124, 0.7, 0.01), int(24*s_))
        # точки «печатает» появляются — и исчезают. Ответа не будет.
        if 8.4 < l < 11.6:
            typing_dots(d, cam, ox, y, t, fade(t, 118.4, 121.6, 0.6, 0.6))
        hud(d, 3246, 0, 255)
        narr(d, [(L["n10"], False)], fade(t, 112.5, 122.6, 0.9, 0.8), im)

    elif inside(t, "bottom"):
        l = lt(t, "bottom")
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="02:46", phone_glow=(752, 610, 230, 0.34))
        dem = draw_demon(im, d, cam, (920, 790), 440, "sit_bed", t=t, flip=True, heat=1.25)
        inf = draw_person(im, d, cam, (700, 790), 430, "slump", t=t, mood="sad",
                          lit=1.0, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*2.4)
        hud(d, cnt(t, 124, 133, 3246, 3290), 0, 255)
        whisper(d, L["w4"], t, 125.8, hold=3.0, size=46,
                at=demon_anchor(cam, dem) if dem else None, max_w=470)
        narr(d, [(L["n11"], False)], fade(t, 125.0, 132.0, 0.9, 0.8), im)

    elif inside(t, "off"):
        l = lt(t, "off")
        off = t >= 133.6                       # щелчок в звуковой дорожке
        ko = clamp((t-133.6)/1.6)
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="02:58",
                phone_glow=None if off else (752, 600, 230, 0.34))
        draw_demon(im, d, cam, (920, 790), 440, "sit_bed", t=t, flip=True,
                   alpha=int(lerp(200, 0, smoother(ko))), heat=1.0)
        inf = draw_person(im, d, cam, (700, 790), 430, "sit_bed", t=t,
                          mood="tired" if off else "sad", lit=1.0-ko, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*2.0, off=off)
        dim(im, int(96*smoother(ko)))         # комната гаснет вместе с экраном
        hud(d, 3290, 0, 255)
        narr(d, [(L["n12"], False)], fade(t, 134.2, 140.4, 0.9, 0.6), im)

    elif inside(t, "twenty"):
        # двадцать минут — цифрами часов, а не карточкой
        l = lt(t, "twenty")
        mins = 2*60 + 58 + int(clamp(l/4.0)*20)
        txt = f"{mins//60:02d}:{mins%60:02d}"
        big_clock(im, d, txt, t, W/2, H/2-60, 130, fade(t, 141, 146, 0.6, 0.5), 0.55)
        narr(d, [(L["n13"], False)], fade(t, 141.8, 146, 0.8, 0.5), im, y=H/2+120, size=46)

    elif inside(t, "relapse"):
        l = lt(t, "relapse")
        on = t >= 148.9                        # шорох в звуковой дорожке
        kn = clamp((t-148.9)/0.5)
        cam = room_cam(t)
        bedroom(im, d, cam, t, clock_text="03:18",
                phone_glow=(752, 600, 250, 0.46*kn) if on else None)
        dem = draw_demon(im, d, cam, (1110, 846), 488, "stand", t=t, heat=1.4,
                         alpha=int(255*smoother(clamp((t-148.9)/1.2))))
        inf = draw_person(im, d, cam, (700, 790), 430,
                          pose_mix("sit_bed", "phone_face", smoother(clamp((t-149.2)/1.8))),
                          t=t, mood="wired" if on else "sad", lit=kn, **HERO)
        bed_cover(d, cam)
        phone_at(im, d, cam, inf["hand_r"], 56, 1.0, l*2.6, off=not on)
        if not on: dim(im, 96)
        hud(d, cnt(t, 148.9, 153, 3290, 3341), 0, 255)
        whisper(d, L["w5"], t, 149.6, hold=2.0, type_dur=1.0, size=50,
                at=demon_anchor(cam, dem) if dem else None)
        narr(d, [(L["n14"], False)], fade(t, 149.4, 152.6, 0.8, 0.5), im)

    elif inside(t, "turn"):
        # 05:48. Он встаёт и идёт к ОКНУ, стоит против рассвета — и только
        # потом поднимает телефон. Демона в кадре нет.
        l = lt(t, "turn")
        cam = room_cam(t)
        bedroom(im, d, cam, t, warm=0.34, lamp=0.80, clock_text="05:48", rain=False)
        k = smoother(clamp((l-1.0)/3.5))
        px = lerp(700, 1300, k)
        if k < 0.98:
            draw_person(im, d, cam, (px, lerp(790, 866, k)), 430,
                        pose_mix("sit_bed", "stand", k), t=t, mood="neutral", look=0.5, **HERO)
        else:
            kr = smoother(clamp((l-6.4)/1.2))
            inf = draw_person(im, d, cam, (1300, 866), 430, pose_mix("stand", "reach", kr),
                              t=t, mood="neutral", look=lerp(0.7, 0.4, kr), **HERO)
            if kr > 0.6: phone_at(im, d, cam, inf["hand_r"], 56, 0.9, 0)
        if k < 0.25: bed_cover(d, cam)
        hud(d, 3341, 0, 255)

    elif inside(t, "chat2"):
        # та же переписка — но теперь первым пишет он
        l = lt(t, "chat2")
        cam = Cam(lerp(1.00, 1.05, smoother(l/6)), 960, 505)
        closeup_phone(im, d, cam, t, 0, bright=0.65, chat=True)
        ox, oy = chat_header(d, cam)
        s_ = cam.s; y = oy
        y = bubble(d, L["chat_3"], ox, y, False, 160, int(24*s_))
        if l > 0.8: y = bubble(d, T["my_msg"], ox+256*s_, y, True, fade(t, 162.8, 168, 0.7, 0.01), int(24*s_))
        if 2.6 < l < 4.4: typing_dots(d, cam, ox, y, t, fade(t, 164.6, 166.4, 0.5, 0.4))
        if l > 4.4: y = bubble(d, T["reply"], ox, y, False, fade(t, 166.4, 168, 0.6, 0.01), int(24*s_))
        hud(d, 3341, 0, 255)
        narr(d, [(L["n15"], False)], fade(t, 162.6, 167.6, 0.9, 0.6), im)

    elif inside(t, "nights"):
        l = lt(t, "nights")
        k = min(int(l//(8/3)), 2)
        night, dh, dal, clk = [(1, 462, 170, "01:40"), (4, 330, 80, "00:35"), (30, 0, 0, "23:05")][k]
        cam = room_cam(t)
        bedroom(im, d, cam, t, warm=0.16 if night == 30 else 0.0,
                lamp=0.5 if night == 30 else 0.0, clock_text=clk, rain=(night == 1))
        if dh > 0:
            draw_demon(im, d, cam, (1180, 846), dh, "stand", t=t, alpha=dal, heat=0.75)
        if night == 30:
            rrect(d, cam, (392, 758, 584, 852), 28, (64, 62, 76), LINE, 3.4)
            draw_person(im, d, cam, (640, 764), 360, "lie", t=t, mood="tired",
                        face_on=True, **HERO)
            rrect(d, cam, (566, 748, 1140, 886), 18, (50, 40, 34), LINE, 4)
        else:
            draw_person(im, d, cam, (700, 790), 430, "sit_bed", t=t,
                        mood="neutral" if night == 1 else "smile", look=0.3, **HERO)
            bed_cover(d, cam)
        phone_flat(d, cam, 1010, 686, 60)      # телефон экраном вниз, в ногах кровати
        hud(d, 0, 0, fade(t, 168+k*8/3, 168+(k+1)*8/3, 0.6, 0.5), night=night)

    elif inside(t, "cafe"):
        l = lt(t, "cafe")
        cam = Cam(lerp(1.02, 1.08, smoother(l/6.4)), 975, lerp(612, 600, smoother(l/6.4)))
        cafe_morning(im, d, cam, t)
        draw_person(im, d, cam, (796, 846), 460, "sit_chair", t=t, seed=0.0,
                    mood=talks(l, 1.1), look=0.6, lit=0.7, **HERO)
        draw_person(im, d, cam, (1168, 846), 448, "sit_chair", t=t, seed=0.7,
                    mood=talks(l), look=-0.6, skin=SKIN2, lit=0.7, **FRIEND)
        table_two(d, cam, t)
        cups_and_hands(d, cam, t)
        phone_flat(d, cam, 984, 792, 70)       # телефон экраном вниз, между чашками
        hud(d, 3341, 1, fade(t, 176.6, 182.4, 1.0, 0.01), strike=True, amber=True)
        a2 = fade(t, 178.0, 182.4, 0.9, 0.01)
        ftop, fbot = BOT-118, BOT+62
        flay, fd = text_band(ftop, fbot)
        for dx, dy in ((0, 3), (0, -2), (3, 1), (-3, 1)):
            fd.text((W/2+dx, BOT-58-ftop+dy), L["fin_1"], font=FN(42), fill=(0, 0, 0, 148), anchor="mm")
            fd.text((W/2+dx, BOT-ftop+dy), L["fin_2"], font=FNB(50), fill=(0, 0, 0, 158), anchor="mm")
        fd.text((W/2, BOT-58-ftop), L["fin_1"], font=FN(42), fill=(236, 238, 244, 235), anchor="mm")
        fd.text((W/2, BOT-ftop), L["fin_2"], font=FNB(50), fill=(255, 255, 255, 255), anchor="mm")
        put_band(im, flay, ftop, a2)

    else:
        a = fade(t, 182.8, 186.5, 1.0, 0.01)
        d.text((W/2, 400), L["title_1"], font=FH(92), fill=(238, 240, 246, a), anchor="mm")
        d.text((W/2, 470), L["title_vs"], font=FN(40), fill=(150, 156, 170, a), anchor="mm")
        d.text((W/2, 548), L["title_2"], font=FH(92), fill=(238, 240, 246, a), anchor="mm")
        wl = d.textlength(L["title_2"], font=FH(92))
        gr = fade(t, 183.4, 186.5, 0.9, 0.01)
        d.line([(W/2-wl/2, 632), (W/2-wl/2+wl*(gr/255), 632)], fill=RED + (255,), width=6)
        a2 = fade(t, 183.8, 186.5, 0.9, 0.01)
        d.text((W/2, 712), L["out_1"], font=FN(44), fill=(226, 228, 234, a2), anchor="mm")
        d.text((W/2, 772), L["out_2"], font=FI(40), fill=RED + (a2,), anchor="mm")

    letterbox(im)
    dim(im, cut_dim(t))
    return finish(im).save(f"{OUT}/f{i:05d}.jpg", quality=94)

if __name__ == "__main__":
    os.nice(19)
    with Pool(4) as p:
        for _ in p.imap_unordered(frame, range(int(DUR*FPS)), chunksize=16): pass
    print("кадров:", int(DUR*FPS))
