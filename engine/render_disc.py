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
import vecman as vm
from people2 import *
from render3 import phone_at          # телефон в руке — общий с первым фильмом
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_disc")
os.makedirs(OUT, exist_ok=True)

SPEED = float(os.environ.get("SHORTFILM_SPEED", "1"))
DUR = 158.0 * SPEED

# Сцен стало больше, и каждая короче: его слово 07.11 — «мало сцен, нет
# динамики, слишком долго держится». Во второй половине семь разных занятий
# вместо трёх, ни одно не висит дольше восьми секунд.
S = {
 "open":   (0,   5),    "sleep":  (5,  12),   "over":   (12, 18),
 "sofa1":  (18, 25),    "desk":   (25, 31),   "rush":   (31, 39),
 "mirror": (39, 50),    "bottom": (50, 62),   "hand":   (62, 71),
 "run":    (71, 79),    "push1":  (79, 86),   "dumb":   (86, 92),
 "bag":    (92, 100),   "tread":  (100, 106), "kettle": (106, 112),
 "push2":  (112, 118),  "climb":  (118, 127), "flash":  (127, 129),
 "summit": (129, 143),  "morning":(143, 149), "title":  (149, 158),
}
def inside(t, n): a, b = S[n]; return a <= t < b
def lt(t, n): return t - S[n][0]

CUTS = [(5, .34), (12, .26), (18, .28), (25, .28), (31, .28), (33, .18),
        (35, .18), (37, .18), (39, .34), (50, .34), (62, .34), (71, .30),
        (79, .24), (86, .24), (92, .24), (100, .24), (106, .24), (112, .24),
        (118, .30), (143, .32), (149, .36)]
def cut_dim(t):
    a = 0.0
    for tc, hw in CUTS:
        if abs(t-tc) < hw: a = max(a, 255*smoother(1-abs(t-tc)/hw))
    return a

HERO = dict()        # векторному герою не нужны ключи кожи и обводки


def hero(im, cam, hip, h, pose, t=0.0, mood="neutral", look=0.0,
         band=False, dark=False, alpha=1.0, **_ignored):
    """Герой фильма — ВЕКТОРНЫЙ (принятый прототип, РАЗБОР IFVERSE, круг 5).

    Его слово 07.11: «вот этого я бы хотел, он лучше». Углы поз те же, что у
    старого PIL-скелета, поэтому раскадровка не тронута; повязка, тёмный
    двойник и прозрачность — параметрами.
    """
    return vm.draw_vecman(im, cam, hip, h, pose, t=t, mood=mood, look=look,
                          band=band, dark=dark, alpha=alpha)
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


def day_badge(d, n, alpha=1.0, mark=None):
    """Счётчик дней с пометкой — главный приём фильма.

    Пометка «ПРОПУЩЕН» / «СДЕЛАН» добавлена 07.11: без неё зритель не
    понимал, что именно считается (его слово: «не уловил сюжета»).
    """
    if alpha <= 0.004: return
    d.text((80, 112), f'{L["day"]} {n}', font=FH(46),
           fill=(232, 236, 246, int(240*alpha)))
    if mark == "skip":
        d.text((82, 166), L["skipped"], font=FH(30), fill=RED + (int(230*alpha),))
    elif mark == "done":
        d.text((82, 166), L["done"], font=FH(30), fill=(120, 214, 140, int(235*alpha)))


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

    # ------------------------------------------- 5:00, «ЕЩЁ ПЯТЬ МИНУТ»
    elif inside(t, "sleep"):
        l = lt(t, "sleep")
        cam = Cam(lerp(1.10, 1.20, smoother(l/7)), 820, 690)
        bedroom(im, d, cam, t, clock_text="5:00", rain=False)
        hero(im, cam, (700, 790), 430, "lie", t=t, mood="tired",
                    look=0.2, **HERO)
        add_glow(im, *cam.p(206, 668), cam.r(210), RED, 0.40*flicker(t, 9.0), 2.4)
        whisper(d, L["w0"], t, 7.4, hold=3.2, size=46, at=(1020, 300))

    # ------------------------------------------------ ПРОСПАЛ: ДЕНЬ ПРОПУЩЕН
    elif inside(t, "over"):
        l = lt(t, "over")
        cam = Cam(1.22, 300, 660)
        bedroom(im, d, cam, t, clock_text="5:08" if l < 2.4 else "7:40", rain=False)
        hero(im, cam, (700, 790), 430, "lie", t=t, mood="tired", **HERO)
        for k in range(2):
            yy = 470 - k*52 - (l*8) % 40
            d.text(cam.p(840+k*26, yy), "z", font=FI(30+k*10), fill=(196, 204, 222, 150))
        day_badge(d, 1, alpha=clamp((l-2.6)/0.8), mark="skip")

    # ------------------------------------------------------- ДИВАН, «ЗАВТРА»
    elif inside(t, "sofa1"):
        l = lt(t, "sofa1")
        cam = Cam(lerp(1.06, 1.15, smoother(l/7)), 900, 700)
        _sofa(im, d, cam, t)
        inf = hero(im, cam, (820, 800), 420, "phone_face", t=t,
                          mood="wired", look=0.4, lit=0.8, **HERO)
        phone_at(im, d, cam, inf["hand_r"], 54, 1.0, l*1.4)
        draw_demon(im, d, cam, (1290, 846), 430, "stand", t=t,
                   alpha=int(255*fade(t, 19.0, 25, 1.4, 0.01)), heat=0.95)
        day_badge(d, 2, mark="skip")
        whisper(d, L["w1"], t, 19.8, hold=3.0, at=(1180, 310))

    # --------------------------------------------------- СТОЛ, «ТЫ УСТАЛ»
    elif inside(t, "desk"):
        l = lt(t, "desk")
        cam = Cam(lerp(1.04, 1.14, smoother(l/6)), 940, 700)
        rd.desk_night(im, d, cam, t, lamp=1.0)
        hero(im, cam, (900, 870), 420, "sit_chair", t=t,
                    mood="tired", look=0.3, lit=0.9, **HERO)
        draw_demon(im, d, cam, (560, 880), 440, "reach", t=t,
                   alpha=int(255*fade(t, 26.0, 31, 1.4, 0.01)), heat=1.0)
        day_badge(d, 47, mark="skip")
        whisper(d, L["w3"], t, 26.6, hold=2.8, at=(430, 340))

    # ------------------------------------ ГОД ЗА ВОСЕМЬ СЕКУНД: ТРИ СКЛЕЙКИ
    elif inside(t, "rush"):
        l = lt(t, "rush")
        # Быстрая нарезка: одно и то же место, разные ночи, счётчик летит.
        k = int(l // 2.0)
        if k == 0:
            cam = Cam(1.18, 900, 700); _sofa(im, d, cam, t)
            inf = hero(im, cam, (860, 800), 420, "slump", t=t,
                              mood="wired", lit=0.85, **HERO)
            phone_at(im, d, cam, inf["hand_r"], 54, 1.0, l*3.0)
            day_badge(d, 112, mark="skip")
        elif k == 1:
            cam = Cam(1.26, 760, 700)
            bedroom(im, d, cam, t, clock_text="4:12", rain=False)
            hero(im, cam, (700, 790), 430, "lie", t=t, mood="tired", **HERO)
            day_badge(d, 200, mark="skip")
        elif k == 2:
            cam = Cam(1.14, 940, 700); rd.desk_night(im, d, cam, t, lamp=0.6)
            hero(im, cam, (900, 870), 420, "slump", t=t,
                        mood="tired", lit=0.5, **HERO)
            day_badge(d, 340, mark="skip")
        else:
            cam = Cam(1.30, 760, 700)
            bedroom(im, d, cam, t, clock_text="5:00", rain=False)
            hero(im, cam, (700, 790), 430, "lie", t=t, mood="tired", **HERO)
            add_glow(im, *cam.p(206, 668), cam.r(220), RED, 0.46, 2.4)
            day_badge(d, 365, mark="skip")
        caption(d, im, L["year"], fade(t, 33.4, 38.6, 0.8, 0.8), y=250, bold=True)

    # ------------------------------------------------------------ ЗЕРКАЛО
    elif inside(t, "mirror"):
        l = lt(t, "mirror")
        cam = Cam(lerp(1.00, 1.16, smoother(l/11)), 980, 620)
        crack = clamp((l-6.4)/1.6)
        mx, my, mrx, mry = rd.mirror(im, d, cam, t, crack=crack,
                                     glow_k=0.5+0.6*crack)
        # В отражении НЕ демон, а он сам — только чёрный. Иначе непонятно,
        # кто это и почему (его слово 07.11: «что она символизирует?»).
        step = smoother(clamp((l-0.4)/3.0))
        hero_x = lerp(430, 700, step)
        refl_a = int(240*clamp((l-2.2)/1.6))
        if refl_a > 6:
            hero(im, cam, (mx, my+mry*0.82), 400, "stand", t=t,
                        mood="angry", look=-0.4, dark=True, alpha=refl_a/255.0)
            add_glow(im, *cam.p(mx, my), cam.r(mrx*1.3), MAG, 0.22, 2.6)
        hero(im, cam, (hero_x, 880), 430, "stand", t=t, mood="tired",
                    look=0.6, lit=0.5, **HERO)
        if l > 6.0:
            f = FW(126)
            w = d.textlength(L["w4"], font=f)
            d.text((W/2-w/2, 280), L["w4"], font=f,
                   fill=RED + (int(245*clamp((l-6.0)/0.5)),))

    # --------------------------------------------------------------- ДНО
    elif inside(t, "bottom"):
        l = lt(t, "bottom")
        rd.spotlight(im, d, Cam(1.0), 960, 980, k=clamp(l/1.4))
        cam = Cam(lerp(0.96, 1.08, smoother(l/12)), 960, 760)
        hero(im, cam, (960, 960), 330, "curl", t=t, mood="tired",
                    look=0.0, lit=0.9, **HERO)
        caption(d, im, L["mid_1"], fade(t, 51.0, 56.4, 0.9, 0.9), y=420)
        caption(d, im, L["mid_2a"], fade(t, 57.2, 61.6, 0.9, 0.7), y=400)
        caption(d, im, L["mid_2b"], fade(t, 58.4, 61.8, 0.9, 0.7), y=460, bold=True)

    # ------------------------------------------------------- ПЕРЕЛОМ: ДЕНЬ 1
    elif inside(t, "hand"):
        l = lt(t, "hand")
        if l < 5.6:
            # Будильник крупно, рука тянется к кнопке и ЗАМИРАЕТ над ней.
            sh = math.sin(t*34)*7*clamp((2.0-l)/2.0)
            cam = Cam(2.6, 206+sh, 668)
            bedroom(im, d, cam, t, clock_text="5:00", rain=False)
            add_glow(im, *cam.p(206, 668), cam.r(300), RED, 0.55, 2.2)
            reach = smoother(clamp((l-1.0)/1.6)) * (1.0 - smoother(clamp((l-3.4)/1.4)))
            hxp = lerp(560, 300, reach)
            capsule(d, cam, (hxp+150, 690), (hxp, 700), 26, CREAM, 255)
            ellipse_at(d, cam, (hxp, 700), 30, 28, CREAM, 255)
        else:
            cam = Cam(lerp(1.30, 1.14, smoother((l-5.6)/3.4)), 820, 700)
            bedroom(im, d, cam, t, clock_text="5:00", rain=False)
            hero(im, cam, (700, 790), 430,
                        pose_mix("lie", "sit_bed", smoother(clamp((l-5.8)/1.8))),
                        t=t, mood="neutral", look=0.4, lit=0.6, **HERO)
            day_badge(d, 1, alpha=clamp((l-7.4)/1.0), mark="done")

    # ------------------------------------------------------------- ПАХОТА
    elif inside(t, "run"):
        l = lt(t, "run")
        cam = Cam(lerp(1.02, 1.10, smoother(l/8)), 960, 560)   # проводка с наездом
        rd.city(im, d, cam, t, pan=l*170)
        ph = l*3.4
        soft_ellipse(im, *cam.p(960, 772), cam.r(120), cam.r(18), (0, 0, 0), 0.45)
        draw_demon(im, d, cam, (1420, 790), 430, "stand", t=t,
                   alpha=int(235*fade(t, 72.0, 79, 1.2, 0.01)), heat=1.0)
        whisper(d, L["w6"], t, 73.0, hold=2.6, size=48, at=(1300, 250))
        inf = hero(im, cam, (960, 760), 400,
                          pose_mix("run_a", "run_b", 0.5+0.5*math.sin(ph)),
                          t=t, mood="angry", look=0.5, band=True)
        day_badge(d, 3)

    elif inside(t, "push1"):
        l = lt(t, "push1")
        cam = Cam(lerp(1.00, 1.12, smoother(l/6)), 940, 830)
        rd.pull_bar(d, cam, 1320, 240, 980)
        line(d, cam, [(100, 980), (1820, 980)], LINE, 3.2)
        soft_ellipse(im, *cam.p(900, 972), cam.r(230), cam.r(22), (0, 0, 0), 0.40)
        k = 0.5+0.5*math.sin(l*3.0)
        inf = hero(im, cam, (900, 988), 400,
                          pose_mix("pushup_up", "pushup_dn", k), t=t,
                          mood="angry", look=0.3, band=True)
        day_badge(d, 12)
        if l > 1.6:                                          # счёт повторов
            n = 1 + int((l-1.6)*1.4)
            f = FNB(150)
            w = d.textlength(str(n), font=f)
            d.text((W/2-w/2, 230), str(n), font=f,
                   fill=CREAM + (int(235*fade(t, 80.6, 84.8, 0.4, 0.5)),))

    elif inside(t, "bag"):
        l = lt(t, "bag")
        cam = Cam(lerp(1.00, 1.08, smoother(l/8)), 1010, 660)
        hit = max(0.0, math.sin(l*2.8))**3
        rd.heavy_bag(im, d, cam, t, hit=hit, speed_lines=clamp((l-1.0)/2.0)*0.7,
                     hero_x=900, floor=980)
        inf = hero(im, cam, (900, 860), 420,
                          pose_mix("guard", "punch", hit), t=t, mood="angry",
                          look=0.6, **HERO)
        draw_demon(im, d, cam, (480, 920), 240, "stand", t=t, alpha=170, heat=0.8)
        day_badge(d, 64)
        whisper(d, L["w5"], t, 93.0, hold=2.6, size=52, at=(1300, 250))

    elif inside(t, "dumb"):                                  # ДЕНЬ 28 — гантели
        l = lt(t, "dumb")
        cam = Cam(lerp(1.06, 1.16, smoother(l/6)), 960, 700)
        rd.pull_bar(d, cam, 700, 250, 980)
        line(d, cam, [(100, 980), (1820, 980)], LINE, 3.2)
        k = 0.5 + 0.5*math.sin(l*3.2)
        inf = hero(im, cam, (960, 900), 420,
                          pose_mix("curl_dn", "curl_up", k), t=t, mood="angry",
                          look=0.4, **HERO)
        rd.dumbbell(d, cam, inf["hand_l"], 26)
        rd.dumbbell(d, cam, inf["hand_r"], 26)
        soft_ellipse(im, *cam.p(960, 972), cam.r(150), cam.r(20), (0, 0, 0), 0.45)
        draw_demon(im, d, cam, (1480, 900), 300, "stand", t=t, alpha=190, heat=0.85)
        day_badge(d, 28)

    elif inside(t, "tread"):                                 # ДЕНЬ 96 — дорожка
        l = lt(t, "tread")
        cam = Cam(lerp(1.00, 1.09, smoother(l/6)), 960, 700)
        rd.treadmill(im, d, cam, t, x=960, floor=980, speed=1.0)
        ph = l*4.2
        inf = hero(im, cam, (900, 934), 400,
                          pose_mix("run_a", "run_b", 0.5+0.5*math.sin(ph)),
                          t=t, mood="angry", look=0.5, band=True)
        draw_demon(im, d, cam, (1560, 960), 170, "stand", t=t, alpha=140, heat=0.7)
        day_badge(d, 96)

    elif inside(t, "kettle"):                                # ДЕНЬ 138 — гиря
        l = lt(t, "kettle")
        cam = Cam(lerp(1.04, 1.12, smoother(l/6)), 960, 720)
        line(d, cam, [(100, 980), (1820, 980)], LINE, 3.2)
        rd.pull_bar(d, cam, 1340, 240, 980)
        k = 0.5 + 0.5*math.sin(l*2.6)
        inf = hero(im, cam, (900, 900), 420,
                          pose_mix("kettle_dn", "kettle_up", k), t=t,
                          mood="angry", look=0.5, band=True)
        hx = (inf["hand_l"][0]+inf["hand_r"][0])/2
        hy = (inf["hand_l"][1]+inf["hand_r"][1])/2
        rd.kettlebell(d, cam, (hx, hy+26), 34)
        soft_ellipse(im, *cam.p(900, 972), cam.r(160), cam.r(20), (0, 0, 0), 0.45)
        draw_demon(im, d, cam, (1600, 964), 110, "stand", t=t, alpha=110, heat=0.6)
        day_badge(d, 138)

    elif inside(t, "push2"):
        l = lt(t, "push2")
        cam = Cam(1.1, 960, 820)
        line(d, cam, [(200, 980), (1720, 980)], LINE, 3.2)
        k = 0.5+0.5*math.sin(l*3.6)
        inf = hero(im, cam, (900, 988), 400,
                          pose_mix("pushup_up", "pushup_dn", k), t=t, mood="angry", band=True)
        draw_demon(im, d, cam, (1660, 972), 70, "stand", t=t, alpha=80, heat=0.5)
        day_badge(d, 190)

    # ---------------------------------------------------------- ПОСЛЕДНИЙ БОЙ
    elif inside(t, "climb"):
        l = lt(t, "climb")
        # Его слово 07.11: «почему лестница идёт, он не идёт». Теперь герой
        # ВЗБИРАЕТСЯ: он поднимается по ступеням в мировых координатах, а
        # камера идёт за ним. Фон уезжает вниз — видно, сколько пройдено.
        ph = l*2.0
        step = int(ph)                                  # сколько ступеней прошёл
        frac = ph - step
        hero_x = 420 + step*150 + frac*150
        hero_y = 980 - step*92 - frac*92
        cam = Cam(1.0, hero_x + 140, hero_y - 250)
        rd.stairs(im, d, cam, t, shift=0)
        inf = hero(im, cam, (hero_x, hero_y), 400,
                          pose_mix("climb", "stand", 0.5+0.5*math.sin(ph*math.pi)),
                          t=t, mood="angry", look=0.5, band=True)
        soft_ellipse(im, *cam.p(hero_x, hero_y-6), cam.r(90), cam.r(14), (0, 0, 0), 0.45)
        day_badge(d, 270)
        # Демон стоит выше по лестнице и преграждает. Когда герой доходит до
        # него, он ПРОХОДИТ СКВОЗЬ: демон слабеет и гаснет (его слово 07.11 —
        # бордовая фигура была непонятна, теперь это сцена, а не пятно).
        dstep = 5
        dx = 420 + dstep*150
        dy = 980 - dstep*92
        near = clamp((hero_x - (dx - 420))/420)          # 0 далеко → 1 вплотную
        dem_a = int(230*clamp((l-1.0)/1.2)*(1.0 - near))
        if dem_a > 6:
            draw_demon(im, d, cam, (dx, dy), 430, "stand", t=t,
                       alpha=dem_a, heat=1.1)
            whisper(d, L["w5"], t, 120.0, hold=2.6, size=50,
                    at=cam.p(dx - 300, dy - 500))
        caption(d, im, L["keep"], fade(t, 122.0, 126.6, 1.0, 0.8), y=250, bold=True)

    elif inside(t, "flash"):
        rd.flash(im, clamp(1.0 - abs(lt(t, "flash") - 0.7)/0.7))

    # ------------------------------------------------------------- ВЕРШИНА
    elif inside(t, "summit"):
        l = lt(t, "summit")
        # Его слово 07.11: «стоит эта сцена, нет динамики, не на чем залипнуть».
        # Теперь здесь всё движется: камера наезжает, солнце ВСХОДИТ, облака
        # идут, ветер сносит повязку, герой поворачивается к рассвету.
        cam = Cam(lerp(1.00, 1.14, smoother(l/14)), 960, 640)
        rd.summit(im, d, cam, t, k=1.0, rise=smoother(clamp(l/12)))
        turn = smoother(clamp((l-5.0)/3.0))
        inf = hero(im, cam, (900, 700), 300, "stand", t=t,
                          mood="neutral", look=lerp(-0.2, 0.7, turn), band=True)
        soft_ellipse(im, *cam.p(900, 704), cam.r(80), cam.r(12), (0, 0, 0), 0.35)
        rd.flash(im, clamp((1.2-l)/1.2)*0.9)
        caption(d, im, L["save_1"], fade(t, 131.0, 137.0, 1.0, 0.8), y=250)
        caption(d, im, L["save_2"], fade(t, 137.6, 142.6, 1.0, 0.8), y=250, bold=True)

    # ------------------------------------------------------------ УТРО
    elif inside(t, "morning"):
        l = lt(t, "morning")
        # Рифма с началом: та же спальня, тот же будильник — но он УЖЕ сидит,
        # а часы ещё не зазвонили (4:58). Демон уходит за край кадра.
        cam = Cam(lerp(1.20, 1.10, smoother(l/6)), 820, 700)
        bedroom(im, d, cam, t, warm=0.55, clock_text="4:58", rain=False)
        hero(im, cam, (700, 790), 430, "sit_bed", t=t, mood="neutral",
                    look=0.4, lit=0.7, **HERO)
        gone = smoother(clamp((l-1.4)/3.4))
        draw_demon(im, d, cam, (1320 + gone*520, 900), 120, "stand", t=t,
                   alpha=int(150*(1.0-gone)), heat=0.5)

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


def _band(d, cam, info, ph=0.0):
    """Красная повязка на голове — знак второй половины фильма.

    Кладётся по голове, которую ВЕРНУЛ draw_person: считать её положение
    самому нельзя, оно зависит от позы (поймано 07.11 — повязка висела в
    воздухе справа от бегущего).
    """
    hx, hy = info["head"]; r = info["hr"]
    d.line([cam.p(hx-r*1.06, hy-r*0.30), cam.p(hx+r*1.06, hy-r*0.30)],
           fill=rd.RED_D + (255,), width=_w(cam, r*0.40))
    d.line([cam.p(hx+r*0.86, hy-r*0.26), cam.p(hx+r*1.62, hy+r*0.26+ph*7)],
           fill=rd.RED_D + (235,), width=_w(cam, r*0.24))
