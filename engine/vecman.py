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

INK    = "#0B0C16"      # «чёрный», тонированный в синеву
CLOTH1 = "#3C69CE"
CLOTH2 = "#24479A"
SLEEVE = "#27499F"
PANTS  = "#1E2A44"
FACE   = "#F2ECDC"
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


def build_svg(W, H, cam, hip, h, pose, flip=False, mood="neutral", look=0.0,
              band=False, dark=False, alpha=1.0):
    """SVG фигуры: скелет в мировых координатах, проекция камерой."""
    P = cam.p
    f = -1 if flip else 1
    hr_w = h*0.143                       # в мире
    L_th, L_sh = h*0.185, h*0.175
    L_ua, L_fa = h*0.145, h*0.135
    sw = hr_w*1.24
    k = cam.r(1.0)                       # мир → экран
    hr = hr_w*k
    r_leg, r_arm = hr*0.42, hr*0.40

    world = {}
    hx, hy = hip[0], hip[1] + pose.get("hip_y", 0.0)*h
    lean = pose["lean"]*f
    axis = -90 + lean
    nrm = _rot(axis + 90, 1.0)
    sh_c = _add((hx, hy), _rot(axis, h*0.300))
    head = _add(sh_c, _rot(axis + pose["head"]*f, hr*1.16))

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
        off = (-1 if side == "l" else 1)*sw*0.92*f
        along = _rot(axis, -h*0.018)
        p0 = (sh_c[0] + nrm[0]*off + along[0], sh_c[1] + nrm[1]*off + along[1])
        p1 = _add(p0, _rot(ua if not flip else 180-ua, L_ua))
        p2 = _add(p1, _rot(fa if not flip else 180-fa, L_fa))
        arms.append(_limb(P(*p0), P(*p1), P(*p2), r_arm, r_arm*0.88, r_arm*0.78))
        hands.append((P(*p2), r_arm*0.78))
        world["hand_" + side] = p2

    # корпус: покатые плечи, книзу чуть уже
    tnx, tny = nrm
    sx0, sy0 = P(sh_c[0] - tnx*sw*0.96, sh_c[1] - tny*sw*0.96)
    sx1, sy1 = P(sh_c[0] + tnx*sw*0.96, sh_c[1] + tny*sw*0.96)
    hx0, hy0 = P(hx - tnx*sw*0.86, hy - tny*sw*0.86)
    hx1, hy1 = P(hx + tnx*sw*0.86, hy + tny*sw*0.86)
    neck = P(*_add(sh_c, _rot(axis, hr*0.30)))
    world["head"] = head
    head = P(*head)
    sh_scr = P(*sh_c)
    torso = (f'M {hx0:.1f} {hy0:.1f} L {sx0:.1f} {sy0:.1f} '
             f'Q {neck[0]:.1f} {neck[1]:.1f} {sx1:.1f} {sy1:.1f} '
             f'L {hx1:.1f} {hy1:.1f} Z')

    skin = "#141420" if dark else CLOTH1
    skin2 = "#0E0E18" if dark else CLOTH2
    sle = "#101020" if dark else SLEEVE
    pnt = "#0D0D16" if dark else PANTS
    ink = "#241018" if dark else INK

    g = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}">',
         f'<defs><linearGradient id="cl" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{skin}"/>'
         f'<stop offset="1" stop-color="{skin2}"/></linearGradient></defs>',
         f'<g opacity="{alpha:.3f}">']
    for p in legs: g.append(f'<path d="{p}" fill="{pnt}"/>')
    for p, r in feet: g.append(_dot(p, r) + f' fill="{ink}"/>')
    g.append(f'<path d="{torso}" fill="url(#cl)"/>')
    g.append(_dot(sh_scr, sw*0.96) + f' fill="url(#cl)"/>')
    for p in arms: g.append(f'<path d="{p}" fill="{sle}"/>')
    for p, r in hands: g.append(_dot(p, r) + f' fill="{ink}"/>')
    g.append(_dot(head, hr) + f' fill="{ink}"/>')

    # черты лица: два глаза и рот, кремовые — как в принятом прошлом круге
    ex, ey = hr*0.38, hr*0.10
    dx = look*hr*0.12*f
    lid = {"tired": 0.42, "sad": 0.30}.get(mood, 0.0)
    for s_ in (-1, 1):
        cxe = head[0] + s_*ex + dx
        cye = head[1] + ey
        g.append(f'<rect x="{cxe-hr*0.21:.1f}" y="{cye-hr*0.085+hr*lid*0.12:.1f}" '
                 f'width="{hr*0.42:.1f}" height="{hr*0.17*(1-lid*0.5):.1f}" '
                 f'rx="{hr*0.07:.1f}" fill="{FACE}"/>')
    mw = hr*(0.50 if mood != "angry" else 0.36)
    g.append(f'<rect x="{head[0]-mw/2:.1f}" y="{head[1]+hr*0.50:.1f}" '
             f'width="{mw:.1f}" height="{hr*0.075:.1f}" rx="{hr*0.037:.1f}" '
             f'fill="{FACE}"/>')
    if mood == "angry":                       # брови домиком — злость
        for s_ in (-1, 1):
            x0 = head[0] + s_*ex - hr*0.20
            g.append(f'<path d="M {x0:.1f} {head[1]-hr*0.20:.1f} '
                     f'l {hr*0.40:.1f} {s_*hr*0.10:.1f}" stroke="{FACE}" '
                     f'stroke-width="{hr*0.075:.1f}" stroke-linecap="round" fill="none"/>')
    if band:
        bx0 = head[0]-hr*1.04
        g.append(f'<path d="M {bx0:.1f} {head[1]-hr*0.30:.1f} '
                 f'h {hr*2.08:.1f}" stroke="{BAND}" stroke-width="{hr*0.34:.1f}" '
                 f'stroke-linecap="butt" fill="none"/>')
        g.append(f'<path d="M {head[0]+hr*0.90:.1f} {head[1]-hr*0.26:.1f} '
                 f'l {hr*0.70:.1f} {hr*0.34:.1f}" stroke="{BAND}" '
                 f'stroke-width="{hr*0.20:.1f}" stroke-linecap="round" fill="none"/>')
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
                flip=False, band=False, dark=False, alpha=1.0, ss=2):
    """Нарисовать векторного персонажа прямо в кадр движка."""
    from people2 import POSES
    if isinstance(pose, str): pose = POSES[pose]
    W, H = im.width, im.height
    svg, head, hr, world = build_svg(W, H, _SS(cam, ss), hip, h, pose, flip=flip,
                                     mood=mood, look=look, band=band, dark=dark,
                                     alpha=alpha)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=W, output_height=H)
    im.alpha_composite(Image.open(io.BytesIO(png)).convert("RGBA"), (0, 0))
    return dict(head=world["head"], hr=hr/ss,
                hand_l=world.get("hand_l"), hand_r=world.get("hand_r"))
