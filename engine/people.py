# -*- coding: utf-8 -*-
"""Рисованные персонажи: анатомия + чёрная обводка + проработанное лицо."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from film import (W, H, Cam, mix, lerp, clamp, blink, breathe, add_glow,
                  soft_ellipse, CREAM, RED, MAG, AMBER)

OUTLINE = (12, 12, 14)

# ---------- примитивы с обводкой ----------
class Shape:
    """Деталь фигуры. Рисуется дважды: раздутая чёрным, затем заливкой."""
    __slots__ = ("kind", "a", "fill", "r")
    def __init__(self, kind, a, fill, r=0):
        self.kind, self.a, self.fill, self.r = kind, a, fill, r

def _draw(d, cam, s, grow, color, alpha):
    x0, y0, x1, y1 = s.a
    x0 -= grow; y0 -= grow; x1 += grow; y1 += grow
    box = cam.box(x0, y0, x1, y1)
    if box[2] < box[0]: box[0], box[2] = box[2], box[0]
    if box[3] < box[1]: box[1], box[3] = box[3], box[1]
    col = color + (alpha,)
    if s.kind == "e":
        d.ellipse(box, fill=col)
    else:
        d.rounded_rectangle(box, radius=max(1, cam.r(s.r+grow)), fill=col)

def render_shapes(d, cam, shapes, stroke, alpha=255, outline=OUTLINE, oa=None):
    for s in shapes: _draw(d, cam, s, stroke, outline, oa if oa is not None else alpha)
    for s in shapes: _draw(d, cam, s, 0, s.fill, alpha)

def render_groups(d, cam, groups, stroke, alpha=255):
    """Группы обводятся раздельно и ложатся друг на друга — между рукой
    и туловищем появляется линия, как в рисованной анимации."""
    for g in groups:
        if g: render_shapes(d, cam, g, stroke, alpha)

# ---------- лицо ----------
def face(d, cam, hx, hy, hr, t=0.0, seed=0.0, alpha=255, mood="neutral",
         look=0.0, skin=CREAM, open_mouth=False, lashes=False):
    """hx,hy — центр головы; hr — её полуширина."""
    bl = blink(t, seed)
    ew = hr*0.215
    eh = hr*0.265*(1.0-bl*0.92)
    ex = hr*0.345
    ey = hy + hr*0.06
    dx = look*hr*0.09
    ink = OUTLINE + (alpha,)
    for s in (-1, 1):
        cxx = hx + s*ex + dx
        if eh < hr*0.045:
            d.line([cam.p(cxx-ew, ey), cam.p(cxx+ew, ey)], fill=ink,
                   width=max(1, int(cam.r(hr*0.055))))
            continue
        d.ellipse(cam.box(cxx-ew, ey-eh, cxx+ew, ey+eh), fill=(252, 252, 252, alpha))
        d.ellipse(cam.box(cxx-ew, ey-eh, cxx+ew, ey+eh), outline=ink,
                  width=max(1, int(cam.r(hr*0.030))))
        pr = min(ew*0.60, eh*0.70)
        px, py = cxx + look*ew*0.30, ey + eh*0.10
        d.ellipse(cam.box(px-pr, py-pr, px+pr, py+pr), fill=ink)
        d.ellipse(cam.box(px-pr*0.95+pr*0.30, py-pr*0.95+pr*0.10,
                          px-pr*0.95+pr*0.66, py-pr*0.95+pr*0.46),
                  fill=(255, 255, 255, alpha))
        if mood in ("tired", "sad"):            # опущенное веко
            d.chord(cam.box(cxx-ew, ey-eh, cxx+ew, ey+eh), 180, 360,
                    fill=skin + (alpha,))
            d.line([cam.p(cxx-ew, ey-eh*0.05), cam.p(cxx+ew, ey-eh*0.05)],
                   fill=ink, width=max(1, int(cam.r(hr*0.032))))
        if lashes:
            for k in (-1, 0, 1):
                lx = cxx + k*ew*0.62
                d.line([cam.p(lx, ey-eh*1.05), cam.p(lx+s*ew*0.18, ey-eh*1.45)],
                       fill=ink, width=max(1, int(cam.r(hr*0.028))))
    # брови
    bw = hr*0.30
    by = ey - hr*(0.40 if mood != "sad" else 0.34) - bl*hr*0.03
    for s in (-1, 1):
        inner = (hx + s*(ex-bw*0.75) + dx, by + (hr*0.075 if mood in ("sad",) else -hr*0.02))
        outer = (hx + s*(ex+bw*0.75) + dx, by - (hr*0.055 if mood in ("angry", "tired") else 0.0))
        d.line([cam.p(*inner), cam.p(*outer)], fill=ink, width=max(2, int(cam.r(hr*0.058))))
    # рот
    my = hy + hr*0.46
    mw = hr*0.22
    if open_mouth:
        d.ellipse(cam.box(hx-mw, my-mw*0.52, hx+mw, my+mw*0.78), fill=(64, 26, 30, alpha))
        d.ellipse(cam.box(hx-mw, my-mw*0.52, hx+mw, my+mw*0.78), outline=ink,
                  width=max(1, int(cam.r(hr*0.030))))
        d.chord(cam.box(hx-mw*0.72, my+mw*0.04, hx+mw*0.72, my+mw*0.92), 0, 180,
                fill=(228, 108, 118, alpha))
    elif mood == "sad":
        d.arc(cam.box(hx-mw, my-mw*0.18, hx+mw, my+mw*0.82), 200, 340, fill=ink,
              width=max(2, int(cam.r(hr*0.045))))
    elif mood == "smile":
        d.arc(cam.box(hx-mw, my-mw*0.82, hx+mw, my+mw*0.30), 20, 160, fill=ink,
              width=max(2, int(cam.r(hr*0.045))))
    else:
        d.line([cam.p(hx-mw*0.72, my), cam.p(hx+mw*0.72, my)], fill=ink,
               width=max(2, int(cam.r(hr*0.045))))

# ---------- фигуры ----------
def person_sitting_bed(im, d, cam, x, y_hip, h, t=0.0, seed=0.0, skin=CREAM,
                       mood="neutral", look=0.0, alpha=255, phone_arm=True,
                       stroke=None, lit=0.0):
    br = breathe(t, 4.6, h*0.006, seed*2.0)
    stroke = stroke if stroke is not None else h*0.013
    hr   = h*0.175
    hy   = y_hip - h*0.56 + br
    tw   = h*0.145
    ty0  = hy + hr*0.90
    ty1  = y_hip + h*0.10
    aw   = h*0.055
    torso = [Shape("r", (x-tw, ty0, x+tw, ty1), skin, tw*0.52)]
    head  = [Shape("e", (x-hr, hy-hr*1.10, x+hr, hy+hr*1.10), skin)]
    arms  = [Shape("r", (x-tw-aw*0.9, ty0+h*0.05, x-tw+aw*1.1, ty0+h*0.30), skin, aw*0.85)]
    if phone_arm:
        arms.append(Shape("r", (x+tw-aw*1.1, ty0+h*0.02, x+tw+aw*0.9, ty0+h*0.26), skin, aw*0.85))
        arms.append(Shape("e", (x+tw-aw*1.3, ty0-h*0.01, x+tw+aw*0.7, ty0+h*0.06), skin))
    render_groups(d, cam, [torso, head, arms], stroke, alpha)
    if lit > 0:
        soft_ellipse(im, *cam.p(x, hy+hr*0.25), cam.r(hr*1.5), cam.r(hr*1.6),
                     (150, 180, 255), 0.24*lit, 1.6)
    face(d, cam, x, hy, hr, t, seed, alpha, mood, look, skin)
    return (x, hy, hr, ty0)

def person_standing(im, d, cam, x, y_feet, h, t=0.0, seed=0.0, skin=CREAM,
                    mood="neutral", look=0.0, alpha=255, stroke=None,
                    step=0.0, arm_swing=0.0, lit=0.0, arms_down=True):
    br = breathe(t, 4.6, h*0.005, seed*2.0)
    stroke = stroke if stroke is not None else h*0.013
    hr  = h*0.150
    hy  = y_feet - h*0.840 + br
    tw  = h*0.118
    ty0 = hy + hr*0.92
    ty1 = y_feet - h*0.345
    lw  = h*0.050
    torso = [Shape("r", (x-tw, ty0, x+tw, ty1+h*0.06), skin, tw*0.56)]
    legs = []
    for sg, ph in ((-1, 0.0), (1, math.pi)):
        dx = math.sin(step + ph)*h*0.050
        legs.append(Shape("r", (x+sg*tw*0.44-lw+dx, ty1-h*0.02,
                                x+sg*tw*0.44+lw+dx, y_feet-h*0.028), skin, lw*0.85))
        legs.append(Shape("e", (x+sg*tw*0.44-lw*1.20+dx, y_feet-h*0.052,
                                x+sg*tw*0.44+lw*1.10+dx, y_feet), skin))
    head = [Shape("e", (x-hr, hy-hr*1.10, x+hr, hy+hr*1.10), skin)]
    aw = h*0.040
    arms = []
    for sg, ph in ((-1, math.pi), (1, 0.0)):
        dx = math.sin(arm_swing + ph)*h*0.030
        top = ty0 + h*0.075
        bot = top + (h*0.255 if arms_down else h*0.175)
        ax = x + sg*(tw-aw*0.22)
        arms.append(Shape("r", (ax-aw+dx*0.4, top, ax+aw+dx*0.4, bot), skin, aw*0.85))
        arms.append(Shape("e", (ax-aw*1.12+dx*0.7, bot-h*0.030,
                                ax+aw*1.12+dx*0.7, bot+h*0.030), skin))
    render_groups(d, cam, [torso, legs, head, arms], stroke, alpha)
    if lit > 0:
        soft_ellipse(im, *cam.p(x, hy+hr*0.25), cam.r(hr*1.5), cam.r(hr*1.6),
                     (150, 180, 255), 0.22*lit, 1.6)
    face(d, cam, x, hy, hr, t, seed, alpha, mood, look, skin)
    return (x, hy, hr)

# ---------- демон ----------
def demon_figure(im, d, cam, x, y_feet, h, t=0.0, alpha=255, grin=1.0,
                 lying=False, stroke=None):
    """Чёрный силуэт с розовым контурным свечением и лицом из розовых дуг."""
    if alpha <= 6: return
    stroke = stroke if stroke is not None else h*0.011
    sway = math.sin(t*0.62)*h*0.010
    x += sway
    hr  = h*0.138
    hy  = y_feet - h*0.862
    tw  = h*0.108
    ty0 = hy + hr*0.92
    ty1 = y_feet - h*0.330
    lw  = h*0.048
    ink = (10, 9, 14)
    torso = [Shape("r", (x-tw, ty0, x+tw, ty1+h*0.05), ink, tw*0.60)]
    legs = []
    for sg in (-1, 1):
        legs.append(Shape("r", (x+sg*tw*0.46-lw, ty1-h*0.02,
                                x+sg*tw*0.46+lw, y_feet-h*0.026), ink, lw*0.85))
        legs.append(Shape("e", (x+sg*tw*0.46-lw*1.3, y_feet-h*0.050,
                                x+sg*tw*0.46+lw*1.2, y_feet), ink))
    head = [Shape("e", (x-hr, hy-hr*1.12, x+hr, hy+hr*1.12), ink)]
    aw = h*0.046
    rise = math.sin(t*0.8)*h*0.012
    arms = []
    for sg in (-1, 1):
        top = ty0 + h*0.065 + (rise if sg < 0 else -rise)
        ax = x + sg*(tw-aw*0.20)
        arms.append(Shape("r", (ax-aw, top, ax+aw, top+h*0.27), ink, aw*0.85))
        arms.append(Shape("e", (ax-aw*1.15, top+h*0.24, ax+aw*1.15, top+h*0.30), ink))
    # контурное свечение
    a = alpha/255.0
    add_glow(im, *cam.p(x, hy), cam.r(hr*2.5), MAG, 0.40*a, 2.1)
    add_glow(im, *cam.p(x, (ty0+ty1)/2), cam.r(tw*3.2), MAG, 0.30*a, 2.3)
    allsh = torso + legs + head + arms
    # мягкий розовый ореол по форме силуэта
    bx0, by0 = cam.p(x-tw*2.4, hy-hr*1.5)
    bx1, by1 = cam.p(x+tw*2.4, y_feet+h*0.05)
    pad = int(cam.r(h*0.10))
    X0, Y0 = int(bx0-pad), int(by0-pad)
    LW, LH = max(8, int(bx1-bx0)+pad*2), max(8, int(by1-by0)+pad*2)
    if LW < 3000 and LH < 3000:
        lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay, "RGBA")
        sc = _Off(cam, X0, Y0)
        for sp in allsh: _draw(dl, sc, sp, cam.r(h*0.012)/cam.s, (255, 70, 150), 255)
        lay = lay.filter(ImageFilter.GaussianBlur(cam.r(h*0.030)))
        arr = np.asarray(lay).astype(np.float32)
        arr[..., 3] *= 0.85*(alpha/255.0)
        im.alpha_composite(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), (X0, Y0))
    render_shapes(d, cam, allsh, cam.r(h*0.004)/cam.s, alpha,
                  outline=(24, 12, 20), oa=alpha)
    # лицо розовыми дугами
    eb = 1.0 - blink(t, 0.37, 5.6, 0.12)*0.85
    ea = int(alpha*eb*(alpha/255.0)**0.5)
    if ea < 10: return
    pc = (255, 120, 190, ea)
    ex, ey = hr*0.36, hy - hr*0.06
    lw2 = max(2, int(cam.r(hr*0.085)))
    for s in (-1, 1):
        d.arc(cam.box(x+s*ex-hr*0.24, ey-hr*0.22, x+s*ex+hr*0.24, ey+hr*0.22),
              200, 340, fill=pc, width=lw2)
    if grin > 0:
        gw = hr*0.46*grin
        d.arc(cam.box(x-gw, ey+hr*0.12, x+gw, ey+hr*0.86), 20, 160, fill=pc, width=lw2)
        add_glow(im, *cam.p(x, ey+hr*0.45), cam.r(hr*0.9), MAG, 0.30*a, 2.0)


class _Off:
    """Камера со сдвигом начала координат — для подслоёв."""
    def __init__(self, cam, ox, oy): self.cam, self.ox, self.oy, self.s = cam, ox, oy, cam.s
    def p(self, x, y):
        px, py = self.cam.p(x, y); return (px-self.ox, py-self.oy)
    def r(self, v): return self.cam.r(v)
    def box(self, x0, y0, x1, y1):
        a = self.p(x0, y0); b = self.p(x1, y1); return [a[0], a[1], b[0], b[1]]

def phone_in_hand(im, d, cam, x, y, w, bright=1.0, rows=0.0, off=False, screen='feed'):
    h = w*1.95
    d.rounded_rectangle(cam.box(x-w/2, y-h/2, x+w/2, y+h/2), radius=cam.r(w*0.16),
                        fill=(30, 33, 42, 255), outline=(12, 12, 14, 255),
                        width=max(2, int(cam.r(w*0.055))))
    if off: return
    pad = w*0.085
    base = (150, 176, 226) if screen == 'feed' else (26, 29, 38)
    d.rounded_rectangle(cam.box(x-w/2+pad, y-h/2+pad, x+w/2-pad, y+h/2-pad),
                        radius=cam.r(w*0.10), fill=base + (255,))
    if screen != 'feed':
        add_glow(im, *cam.p(x, y), cam.r(w*2.6), (150, 185, 255), 0.26*bright, 2.3)
        return
    sh = h - pad*2
    rowh = sh*0.30
    o = (rows % 1.0)*rowh
    yy = y-h/2+pad-rowh+o
    i = 0
    while yy < y+h/2-pad:
        top, bot = max(yy, y-h/2+pad), min(yy+rowh*0.82, y+h/2-pad)
        if bot-top > 2:
            c = [(104, 126, 186), (138, 104, 170), (96, 134, 170)][i % 3]
            d.rounded_rectangle(cam.box(x-w/2+pad*1.5, top, x+w/2-pad*1.5, bot),
                                radius=cam.r(w*0.06), fill=c + (255,))
        yy += rowh; i += 1
    add_glow(im, *cam.p(x, y), cam.r(w*3.4), (150, 185, 255), 0.42*bright, 2.2)


def person_sitting_chair(im, d, cam, x, y_seat, h, t=0.0, seed=0.0, skin=CREAM,
                         mood="neutral", look=0.0, alpha=255, stroke=None, lit=0.0):
    """Сидит за столиком: голова, торс, руки на столе, ноги вниз от сиденья."""
    br = breathe(t, 4.6, h*0.005, seed*2.0)
    stroke = stroke if stroke is not None else h*0.013
    hr  = h*0.150
    hy  = y_seat - h*0.455 + br
    tw  = h*0.118
    ty0 = hy + hr*0.92
    ty1 = y_seat + h*0.02
    lw  = h*0.050
    torso = [Shape("r", (x-tw, ty0, x+tw, ty1), skin, tw*0.56)]
    legs = []
    for sg in (-1, 1):
        legs.append(Shape("r", (x+sg*tw*0.44-lw, ty1-h*0.03,
                                x+sg*tw*0.44+lw, y_seat+h*0.30), skin, lw*0.85))
        legs.append(Shape("e", (x+sg*tw*0.44-lw*1.2, y_seat+h*0.27,
                                x+sg*tw*0.44+lw*1.1, y_seat+h*0.33), skin))
    head = [Shape("e", (x-hr, hy-hr*1.10, x+hr, hy+hr*1.10), skin)]
    aw = h*0.040
    arms = []
    for sg in (-1, 1):
        ax = x + sg*(tw-aw*0.22)
        top = ty0 + h*0.075
        arms.append(Shape("r", (min(ax, ax+sg*h*0.10)-aw, top,
                                max(ax, ax+sg*h*0.10)+aw, top+h*0.145), skin, aw*0.85))
    render_groups(d, cam, [legs, torso, head, arms], stroke, alpha)
    if lit > 0:
        soft_ellipse(im, *cam.p(x, hy+hr*0.25), cam.r(hr*1.5), cam.r(hr*1.6),
                     (255, 206, 150), 0.22*lit, 1.6)
    face(d, cam, x, hy, hr, t, seed, alpha, mood, look, skin)
    return (x, hy, hr)
