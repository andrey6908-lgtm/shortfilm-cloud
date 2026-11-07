# -*- coding: utf-8 -*-
"""ВЕКТОРНЫЙ ПЕРСОНАЖ — принятый прототип (РАЗБОР IFVERSE, круг 5), но живой.

Прототип был одной статичной картинкой. Здесь те же пропорции и формы
собираются ПО СКЕЛЕТУ: углы суставов те же, что у people2.POSES, поэтому
раскадровка не меняется ни на строку — меняется только рисовальщик.

Почему вектор: PIL не умеет сглаживания, на каждой дуге остаётся лесенка
(замер 05.11, `edges2.jpg`). cairosvg даёт гладкий край, в упор неотличимый
от оригинала.

Пропорции (от hr — радиуса головы, 1/7 роста):
    плечи      1,24 hr в полуширину, линия плеча ПОКАТАЯ
    рукав      конус 0,40 hr → 0,32 hr, кисть — его тёмное продолжение
    штанина    конус 0,42 hr → 0,30 hr
    голова     круг, черты кремовые: два глаза-полумесяца и рот
"""
import io, math
import cairosvg
from PIL import Image
from film import breathe, blink

# ПАЛИТРА. Взято лучшее из двух школ: пропорции и гладкий вектор — из
# принятого прототипа, светлое тело с чёрной обводкой и живое лицо — из хита
# ниши. Тёмный герой прототипа на ЧЁРНОМ фоне тонул (сверка 07.11,
# СРАВНЕНИЕ-С-ОРИГИНАЛОМ.jpg): у Ifverse фон вагона светлый, у Day One чёрный.
SKIN   = "#F0EADC"      # тело и лицо — светлые, читаются на чёрном
OUTL   = "#15151C"      # обводка каждой части, как у них
CLOTH1 = "#5A8AE8"
CLOTH2 = "#3F68C4"
SLEEVE = "#4A79D8"
PANTS  = "#3E4868"
FACE   = "#15151C"      # черты лица — тёмные по светлой голове
BAND   = "#D62C34"      # повязка второй половины фильма


def _rot(a_deg, ln):
    a = math.radians(a_deg)
    return (math.cos(a)*ln, math.sin(a)*ln)


def _add(p, v): return (p[0]+v[0], p[1]+v[1])


def _limb(p0, p1, p2, r0, r1, r2):
    """Конечность из двух конусных сегментов со скруглением в суставах."""
    out = []
    for (a, b, ra, rb) in ((p0, p1, r0, r1), (p1, p2, r1, r2)):
        vx, vy = b[0]-a[0], b[1]-a[1]
        ln = math.hypot(vx, vy) or 1.0
        nx, ny = -vy/ln, vx/ln
        out.append(f'M {a[0]+nx*ra:.1f} {a[1]+ny*ra:.1f} '
                   f'L {b[0]+nx*rb:.1f} {b[1]+ny*rb:.1f} '
                   f'L {b[0]-nx*rb:.1f} {b[1]-ny*rb:.1f} '
                   f'L {a[0]-nx*ra:.1f} {a[1]-ny*ra:.1f} Z')
    return " ".join(out)


def _dot(p, r): return f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r:.1f}"'


def _st(w):
    """Чёрная обводка части тела: без неё фигура сливается в пятно."""
    return f' stroke="{OUTL}" stroke-width="{w:.1f}" stroke-linejoin="round"'


def build_svg(W, H, cam, hip, h, pose, flip=False, mood="neutral", look=0.0,
              band=False, dark=False, alpha=1.0, t=0.0, seed=0.0):
    """SVG фигуры: скелет в мировых координатах, проекция камерой."""
    P = cam.p
    f = -1 if flip else 1
    hr_w = h*0.143                       # в мире
    L_th, L_sh = h*0.205, h*0.200
    L_ua, L_fa = h*0.150, h*0.142
    sw = hr_w*1.24
    k = cam.r(1.0)                       # мир → экран
    hr = hr_w*k
    r_leg, r_arm = hr*0.40, hr*0.34

    world = {}
    # ЖИЗНЬ: тело дышит, голова чуть качается. Без этого фигура мёртвая —
    # его слово 07.11: «не моргает, бровью никто не ведёт, динамики нет».
    br = breathe(t, 4.6, h*0.006, seed*2.0)
    nod = breathe(t, 6.1, 1.6, seed*3.7)          # наклон головы, градусы
    hx, hy = hip[0], hip[1] + pose.get("hip_y", 0.0)*h + br
    lean = pose["lean"]*f
    axis = -90 + lean
    nrm = _rot(axis + 90, 1.0)
    sh_c = _add((hx, hy), _rot(axis, h*0.325))
    head = _add(sh_c, _rot(axis + pose["head"]*f + nod*f, hr_w*0.82))

    legs, arms, hands, feet = [], [], [], []
    for side, (ta, sa) in (("l", (pose["thigh_l"], pose["shin_l"])),
                           ("r", (pose["thigh_r"], pose["shin_r"]))):
        off = (-1 if side == "l" else 1)*sw*0.34*f
        p0 = (hx + nrm[0]*off, hy + nrm[1]*off)
        p1 = _add(p0, _rot(ta if not flip else 180-ta, L_th))
        p2 = _add(p1, _rot(sa if not flip else 180-sa, L_sh))
        legs.append(_limb(P(*p0), P(*p1), P(*p2), r_leg, r_leg*0.84, r_leg*0.72))
        feet.append((P(*p2), r_leg*0.72))
    for side, (ua, fa) in (("l", (pose["ua_l"], pose["fa_l"])),
                           ("r", (pose["ua_r"], pose["fa_r"]))):
        off = (-1 if side == "l" else 1)*sw*0.74*f
        along = _rot(axis, -h*0.040)
        p0 = (sh_c[0] + nrm[0]*off + along[0], sh_c[1] + nrm[1]*off + along[1])
        p1 = _add(p0, _rot(ua if not flip else 180-ua, L_ua))
        p2 = _add(p1, _rot(fa if not flip else 180-fa, L_fa))
        arms.append(_limb(P(*p0), P(*p1), P(*p2), r_arm, r_arm*0.88, r_arm*0.78))
        hands.append((P(*p2), r_arm*0.78))
        world["hand_" + side] = p2

    # корпус: покатые плечи, книзу чуть уже
    tnx, tny = nrm
    sx0, sy0 = P(sh_c[0] - tnx*sw*0.80, sh_c[1] - tny*sw*0.80)
    sx1, sy1 = P(sh_c[0] + tnx*sw*0.80, sh_c[1] + tny*sw*0.80)
    hx0, hy0 = P(hx - tnx*sw*0.68, hy - tny*sw*0.68)
    hx1, hy1 = P(hx + tnx*sw*0.68, hy + tny*sw*0.68)
    neck = P(*_add(sh_c, _rot(axis, hr*0.30)))
    world["head"] = head
    head = P(*head)
    sh_scr = P(*sh_c)
    torso = (f'M {hx0:.1f} {hy0:.1f} L {sx0:.1f} {sy0:.1f} '
             f'Q {neck[0]:.1f} {neck[1]:.1f} {sx1:.1f} {sy1:.1f} '
             f'L {hx1:.1f} {hy1:.1f} Z')

    sk = "#1C1C26" if dark else SKIN
    cl1 = "#20202C" if dark else CLOTH1
    cl2 = "#16161F" if dark else CLOTH2
    sle = "#1A1A24" if dark else SLEEVE
    pnt = "#14141C" if dark else PANTS
    out = "#6A2630" if dark else OUTL
    sw_line = hr*0.17                    # толщина обводки от размера головы

    g = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}">',
         f'<defs><linearGradient id="cl" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{cl1}"/>'
         f'<stop offset="1" stop-color="{cl2}"/></linearGradient></defs>',
         f'<g opacity="{alpha:.3f}" stroke-linecap="round">']

    def part(path, fill):
        g.append(f'<path d="{path}" fill="{fill}" stroke="{out}" '
                 f'stroke-width="{sw_line:.1f}" stroke-linejoin="round"/>')

    # порядок как у них: дальние конечности → корпус → ближние → голова
    part(legs[0], pnt)
    g.append(_dot(feet[0][0], feet[0][1]) + f' fill="{sk}" stroke="{out}" stroke-width="{sw_line:.1f}"/>')
    part(arms[0], sle)
    g.append(_dot(hands[0][0], hands[0][1]) + f' fill="{sk}" stroke="{out}" stroke-width="{sw_line:.1f}"/>')
    part(torso, "url(#cl)")
    g.append(_dot(sh_scr, sw*0.80*k) + f' fill="url(#cl)" stroke="{out}" stroke-width="{sw_line:.1f}"/>')
    part(legs[1], pnt)
    g.append(_dot(feet[1][0], feet[1][1]) + f' fill="{sk}" stroke="{out}" stroke-width="{sw_line:.1f}"/>')
    part(arms[1], sle)
    g.append(_dot(hands[1][0], hands[1][1]) + f' fill="{sk}" stroke="{out}" stroke-width="{sw_line:.1f}"/>')
    g.append(_dot(head, hr) + f' fill="{sk}" stroke="{out}" stroke-width="{sw_line*1.15:.1f}"/>')

    # ЛИЦО: глаза с веком, брови и рот — по ним читается состояние
    fc = "#2A2A36" if dark else FACE
    ex, ey = hr*0.34, hr*0.06
    gaze = breathe(t, 5.3, 0.26, seed*5.1)        # взгляд живёт, а не замер
    dx = (look + gaze)*hr*0.11*f
    lid = {"tired": 0.52, "sad": 0.40, "wired": 0.0}.get(mood, 0.18)
    bl = blink(t, seed)                            # 0 открыт, 1 закрыт
    lid = min(0.96, lid + bl*(1.0 - lid))
    eh = hr*0.30*(1.0 - lid*0.92)
    for s_ in (-1, 1):
        cxe = head[0] + s_*ex + dx
        cye = head[1] + ey + hr*lid*0.10
        g.append(f'<ellipse cx="{cxe:.1f}" cy="{cye:.1f}" rx="{hr*0.155:.1f}" '
                 f'ry="{eh/2:.1f}" fill="{fc}"/>')
        if lid > 0.3:                       # веко: усталость и момент моргания
            g.append(f'<path d="M {cxe-hr*0.19:.1f} {cye-eh*0.42:.1f} '
                     f'h {hr*0.38:.1f}" stroke="{fc}" stroke-width="{hr*0.10:.1f}" '
                     f'fill="none"/>')
    # брови ходят: подрагивают всё время и подскакивают на моргании
    brow_y = head[1] - hr*0.30 + breathe(t, 3.1, hr*0.035, seed*9.4) - bl*hr*0.06
    for s_ in (-1, 1):
        x0 = head[0] + s_*ex - hr*0.21 + dx
        tilt = {"angry": 0.20, "sad": -0.15, "tired": -0.09, "wired": 0.10}.get(mood, 0.0)
        # внутренний конец брови — тот, что ближе к центру лица
        y_out = brow_y - tilt*hr*0.5
        y_in  = brow_y + tilt*hr*0.5
        if s_ < 0:
            g.append(f'<path d="M {x0:.1f} {y_out:.1f} l {hr*0.42:.1f} {y_in-y_out:.1f}" '
                     f'stroke="{fc}" stroke-width="{hr*0.105:.1f}" fill="none"/>')
        else:
            g.append(f'<path d="M {x0:.1f} {y_in:.1f} l {hr*0.42:.1f} {y_out-y_in:.1f}" '
                     f'stroke="{fc}" stroke-width="{hr*0.105:.1f}" fill="none"/>')
    mw = hr*0.42
    mouth = {"angry": -hr*0.10, "sad": hr*0.12}.get(mood, 0.0)
    # на усилии рот приоткрывается в такт движению
    effort = max(0.0, breathe(t, 1.15, 1.0, seed*2.9)) if mood == "angry" else 0.0
    if effort > 0.45:
        g.append(f'<ellipse cx="{head[0]:.1f}" cy="{head[1]+hr*0.48:.1f}" '
                 f'rx="{mw*0.42:.1f}" ry="{hr*(0.06+0.09*effort):.1f}" fill="{fc}"/>')
    else:
        g.append(f'<path d="M {head[0]-mw/2:.1f} {head[1]+hr*0.46:.1f} '
                 f'q {mw/2:.1f} {mouth:.1f} {mw:.1f} 0" stroke="{fc}" '
                 f'stroke-width="{hr*0.09:.1f}" fill="none"/>')
    if band:
        bx0 = head[0]-hr*1.06
        g.append(f'<path d="M {bx0:.1f} {head[1]-hr*0.52:.1f} '
                 f'h {hr*2.12:.1f}" stroke="{BAND}" stroke-width="{hr*0.30:.1f}" '
                 f'fill="none"/>')
        g.append(f'<path d="M {head[0]+hr*0.92:.1f} {head[1]-hr*0.48:.1f} '
                 f'l {hr*0.72:.1f} {hr*0.36:.1f}" stroke="{BAND}" '
                 f'stroke-width="{hr*0.18:.1f}" fill="none"/>')
    g.append("</g></svg>")
    return "".join(g), head, hr, world


_cache = {}
class _SS:
    """Камера движка работает в логических координатах, а буфер в SS раз
    крупнее: оборачиваем проекцию, чтобы SVG лёг ровно в буфер."""
    __slots__ = ("c", "s")
    def __init__(self, cam, ss): self.c, self.s = cam, ss
    def p(self, x, y):
        a = self.c.p(x, y); return (a[0]*self.s, a[1]*self.s)
    def r(self, v): return self.c.r(v)*self.s


def draw_vecman(im, cam, hip, h, pose, t=0.0, mood="neutral", look=0.0,
                flip=False, band=False, dark=False, alpha=1.0, ss=2, seed=0.0):
    """Нарисовать векторного персонажа прямо в кадр движка."""
    from people2 import POSES
    if isinstance(pose, str): pose = POSES[pose]
    W, H = im.width, im.height
    svg, head, hr, world = build_svg(W, H, _SS(cam, ss), hip, h, pose, flip=flip,
                                     mood=mood, look=look, band=band, dark=dark,
                                     alpha=alpha, t=t, seed=seed)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=W, output_height=H)
    im.alpha_composite(Image.open(io.BytesIO(png)).convert("RGBA"), (0, 0))
    return dict(head=world["head"], hr=hr/ss,
                hand_l=world.get("hand_l"), hand_r=world.get("hand_r"))
