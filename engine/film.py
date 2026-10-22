# -*- coding: utf-8 -*-
"""Движок образца v2: больше деталей, мягкое движение."""
import os, math, random
from collections import OrderedDict
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
SS = 2                      # суперсэмплинг: рисуем в SS раз крупнее и ужимаем
SW, SH = W*SS, H*SS

def _sc(xy):
    """Логические координаты -> координаты буфера."""
    if isinstance(xy, (list, tuple)) and xy and isinstance(xy[0], (list, tuple)):
        return [(p[0]*SS, p[1]*SS) for p in xy]
    if isinstance(xy, (list, tuple)) and len(xy) in (2, 4) and not isinstance(xy[0], (list, tuple)):
        return [v*SS for v in xy]
    return xy

class SDraw:
    """ImageDraw в логических координатах 1920x1080; внутрь уходит SS-буфер."""
    __slots__ = ("d",)
    def __init__(self, im, mode="RGBA"): self.d = ImageDraw.Draw(im, mode)
    def _kw(self, kw):
        if "width" in kw and kw["width"] is not None:
            kw["width"] = max(1, int(round(kw["width"]*SS)))
        if "radius" in kw and kw["radius"] is not None:
            kw["radius"] = kw["radius"]*SS
        return kw
    def text(self, xy, *a, **kw): self.d.text(_sc(xy), *a, **self._kw(kw))
    def textlength(self, *a, **kw): return self.d.textlength(*a, **kw)/SS
    def line(self, xy, **kw): self.d.line(_sc(xy), **self._kw(kw))
    def ellipse(self, xy, **kw): self.d.ellipse(_sc(xy), **self._kw(kw))
    def rectangle(self, xy, **kw): self.d.rectangle(_sc(xy), **self._kw(kw))
    def rounded_rectangle(self, xy, **kw): self.d.rounded_rectangle(_sc(xy), **self._kw(kw))
    def polygon(self, xy, **kw): self.d.polygon(_sc(xy), **self._kw(kw))
    def arc(self, xy, *a, **kw): self.d.arc(_sc(xy), *a, **self._kw(kw))
    def chord(self, xy, *a, **kw): self.d.chord(_sc(xy), *a, **self._kw(kw))

def new_frame(bg=(6, 7, 10, 255)):
    im = Image.new("RGBA", (SW, SH), bg)
    return im, SDraw(im, "RGBA")

def paste(im, layer, xy):
    """Композит слоя, координаты логические."""
    im.alpha_composite(layer, (int(xy[0]*SS), int(xy[1]*SS)))
FD = os.environ.get("SHORTFILM_FONTS", "/mnt/c/Windows/Fonts/")
if not FD.endswith("/"): FD += "/"
def font(n, s): return ImageFont.truetype(FD + n, max(1, int(round(s*SS))))
FN  = lambda s: font("calibril.ttf", s)
FNB = lambda s: font("calibri.ttf", s)
FH  = lambda s: font("bahnschrift.ttf", s)
FI  = lambda s: font("calibrili.ttf", s)
FW  = lambda s: font("segoesc.ttf", s)   # почерк демона

CREAM = (239, 231, 219)
INK   = (38, 34, 30)
AMBER = (242, 167, 75)
RED   = (255, 45, 74)
MAG   = (255, 46, 126)

# ---------- математика движения ----------
def smooth(x):   return x*x*(3-2*x)                  # мягко
def smoother(x): return x*x*x*(x*(x*6-15)+10)        # ещё мягче, без рывка на краях
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b-a)*t
def mix(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))
def ease(x): return smoother(clamp(x))

def breathe(t, period=4.6, amp=1.0, phase=0.0):
    return math.sin(t*2*math.pi/period + phase) * amp

def blink(t, seed=0.0, every=4.2, dur=0.15):
    """0 — глаз открыт, 1 — закрыт. Неравномерно, чтобы не выглядело механически."""
    k = math.floor((t + seed*3.1) / every)
    off = (math.sin(k*12.9898 + seed*7.233) * 43758.5453) % 1.0
    start = k*every + off*(every - dur*2.5)
    d = t + seed*3.1 - start
    if d < 0 or d > dur: return 0.0
    return math.sin(d/dur * math.pi) ** 0.7

# ---------- свечение / тень ----------
_BASE_R = 128                      # базовый спрайт 257x257 на сочетание (цвет, сила, спад)
_base_cache = {}
def _base_sprite(color, strength, falloff):
    key = (tuple(color), round(strength, 2), round(falloff, 2))
    sp = _base_cache.get(key)
    if sp is None:
        r = _BASE_R
        y, x = np.ogrid[-r:r+1, -r:r+1]
        d = np.sqrt(x*x + y*y) / r
        a = np.clip(1.0 - d, 0, 1) ** falloff * 255 * strength
        img = np.zeros((2*r+1, 2*r+1, 4), dtype=np.uint8)
        img[..., 0], img[..., 1], img[..., 2] = color
        img[..., 3] = a.astype(np.uint8)
        sp = Image.fromarray(img, "RGBA")
        _base_cache[key] = sp
    return sp

# профиль альфы задан в НОРМИРОВАННОМ радиусе, поэтому масштабирование базового
# спрайта даёт тот же результат, что и пересчёт numpy, но без гигабайтных кэшей
_SPRITE_BUDGET = 192*1024*1024     # потолок кэша масштабированных спрайтов, байт
_sprite_cache = OrderedDict()
_sprite_bytes = 0
def _scaled_sprite(color, strength, falloff, w, h):
    global _sprite_bytes
    key = (tuple(color), round(strength, 2), round(falloff, 2), w, h)
    sp = _sprite_cache.get(key)
    if sp is not None:
        _sprite_cache.move_to_end(key)
        return sp
    sp = _base_sprite(color, strength, falloff).resize((w, h), Image.BILINEAR)
    _sprite_cache[key] = sp
    _sprite_bytes += w*h*4
    while _sprite_bytes > _SPRITE_BUDGET and len(_sprite_cache) > 1:
        _, dead = _sprite_cache.popitem(last=False)
        _sprite_bytes -= dead.width*dead.height*4
    return sp

def glow(radius, color, strength=1.0, falloff=2.2):
    r = max(2, int(radius))
    return _scaled_sprite(color, strength, falloff, 2*r+1, 2*r+1)

def add_glow(base, cx, cy, radius, color, strength=1.0, falloff=2.2):
    if strength <= 0.004 or radius < 1: return
    g = glow(radius*SS, color, strength, falloff)
    base.alpha_composite(g, (int(cx*SS - g.width/2), int(cy*SS - g.height/2)))

def soft_ellipse(base, cx, cy, rx, ry, color, strength=1.0, falloff=2.0):
    """Мягкое пятно (тень под фигурой, блик на теле)."""
    cx, cy = cx*SS, cy*SS
    rx_, ry_ = max(2, int(rx*SS)), max(2, int(ry*SS))
    e = _scaled_sprite(color, strength, falloff, 2*rx_+1, 2*ry_+1)
    base.alpha_composite(e, (int(cx - e.width/2), int(cy - e.height/2)))

# ---------- камера ----------
class Cam:
    def __init__(self, scale=1.0, cx=W/2, cy=H/2):
        self.s, self.cx, self.cy = scale, cx, cy
    def p(self, x, y): return (W/2 + (x-self.cx)*self.s, H/2 + (y-self.cy)*self.s)
    def r(self, v): return v*self.s
    def box(self, x0, y0, x1, y1):
        a = self.p(x0, y0); b = self.p(x1, y1)
        return [a[0], a[1], b[0], b[1]]

def drift(t, t0, dur, s0, s1, cx, cy):
    """Один непрерывный наезд, ~1%/с, без обратного хода."""
    return Cam(lerp(s0, s1, ease((t-t0)/dur)), cx, cy)

# ---------- персонажи ----------
def blob(im, d, cam, cx, cy_bottom, h, color=CREAM, eyes=INK, brows=False,
         sad=False, arms=True, alpha=255, look=0.0, t=0.0, seed=0.0,
         shadow=True, lit=0.0, tilt=0.0):
    bl = blink(t, seed)
    by = breathe(t, 4.6, h*0.008, seed*2.0)
    cy_bottom += by*0.35
    h2 = h - by*0.5
    r  = h2*0.26
    top = cy_bottom - h2
    bw = r*1.22
    col = color + (alpha,)
    if shadow:
        soft_ellipse(im, *cam.p(cx, cy_bottom+h2*0.02), cam.r(bw*1.5), cam.r(h2*0.055),
                     (0, 0, 0), 0.50, 1.7)
    d.rounded_rectangle(cam.box(cx-bw, top+r*1.15, cx+bw, cy_bottom),
                        radius=cam.r(bw*0.78), fill=col)
    hx = cx + tilt*r*0.10
    d.ellipse(cam.box(hx-r, top, hx+r, top+2*r), fill=col)
    if arms:
        aw = breathe(t, 5.3, h2*0.006, seed)
        d.ellipse(cam.box(cx-bw-r*0.42, cy_bottom-h2*0.40+aw, cx-bw+r*0.30, cy_bottom-h2*0.10+aw),
                  fill=col)
        d.ellipse(cam.box(cx+bw-r*0.30, cy_bottom-h2*0.40-aw, cx+bw+r*0.42, cy_bottom-h2*0.10-aw),
                  fill=col)
    if lit > 0:
        soft_ellipse(im, *cam.p(hx, top+r*1.25), cam.r(r*1.25), cam.r(r*1.45),
                     (150, 180, 255), 0.26*lit, 1.6)
    er = r*0.135
    ey = top + r*0.88
    ex = r*0.40
    dx = look*r*0.18
    ec = eyes + (alpha,)
    for s in (-1, 1):
        eh = er*1.15*(1.0 - bl*0.94)
        if eh < er*0.16:
            d.line([cam.p(hx+s*ex-er*1.05+dx, ey), cam.p(hx+s*ex+er*1.05+dx, ey)],
                   fill=ec, width=max(1, int(cam.r(er*0.52))))
        else:
            d.ellipse(cam.box(hx+s*ex-er+dx, ey-eh, hx+s*ex+er+dx, ey+eh), fill=ec)
    if brows:
        lift = -er*0.35*bl
        for s in (-1, 1):
            y_in  = ey - er*(3.4 if sad else 2.4) + lift
            y_out = ey - er*2.6 + lift
            a = cam.p(hx+s*ex-er*1.5, y_out if s < 0 else y_in)
            b = cam.p(hx+s*ex+er*1.5, y_in if s < 0 else y_out)
            d.line([a, b], fill=ec, width=max(1, int(cam.r(er*0.55))))
    if sad:
        d.arc(cam.box(hx-r*0.30, ey+r*0.55, hx+r*0.30, ey+r*1.15),
              start=200, end=340, fill=ec, width=max(1, int(cam.r(er*0.5))))

class _Shift:
    """Та же камера, но с началом координат в углу подслоя."""
    def __init__(self, cam, ox, oy): self.cam, self.ox, self.oy = cam, ox, oy
    def p(self, x, y):
        px, py = self.cam.p(x, y); return (px-self.ox, py-self.oy)
    def r(self, v): return self.cam.r(v)
    def box(self, x0, y0, x1, y1):
        a = self.p(x0, y0); b = self.p(x1, y1); return [a[0], a[1], b[0], b[1]]

def demon(im, d, cam, cx, cy_bottom, h, alpha=255, grin=1.0, t=0.0,
          opacity=0.80, soft=3.6):
    """Сквозная дымная фигура: тело прозрачно, глаза горят поверх."""
    if alpha <= 6: return
    sway = math.sin(t*0.62)*h*0.012
    cx += sway
    r  = h*0.21
    bw = h*0.33

    add_glow(im, *cam.p(cx, cy_bottom-h*0.60), cam.r(h*0.80),
             MAG, 0.24*(alpha/255)*(0.82+0.18*math.sin(t*2.1)), 2.7)

    # --- тело рисуем в свой подслой, чтобы размыть края и сделать сквозным ---
    x0s, y0s = cam.p(cx-bw-h*0.26, cy_bottom-h*1.06)
    x1s, y1s = cam.p(cx+bw+h*0.26, cy_bottom+h*0.09)
    pad = 26
    X0, Y0 = int(x0s-pad), int(y0s-pad)
    LW, LH = max(8, int(x1s-x0s)+pad*2), max(8, int(y1s-y0s)+pad*2)
    if LW > 4000 or LH > 4000: LW, LH = min(LW, 4000), min(LH, 4000)
    layer = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer, "RGBA")
    sc = _Shift(cam, X0, Y0)
    body = (6, 7, 13, 255)
    for i in range(6):                                   # дым у основания
        ph = t*0.75 + i*1.19
        sx = cx + math.sin(ph)*bw*0.75
        sy = cy_bottom - abs(math.sin(ph*0.6))*h*0.16
        sw = bw*(0.26 + 0.10*math.sin(ph*1.7))
        dl.ellipse(sc.box(sx-sw, sy-h*0.045, sx+sw, sy+h*0.030), fill=(6, 7, 13, 185))
    pts = [(cx-bw, cy_bottom), (cx-bw*0.96, cy_bottom-h*0.46),
           (cx-bw*0.72, cy_bottom-h*0.66), (cx-r*1.02, cy_bottom-h*0.80),
           (cx-r*0.86, cy_bottom-h*0.92), (cx-r*0.30, cy_bottom-h*1.0),
           (cx+r*0.30, cy_bottom-h*1.0), (cx+r*0.86, cy_bottom-h*0.92),
           (cx+r*1.02, cy_bottom-h*0.80), (cx+bw*0.72, cy_bottom-h*0.66),
           (cx+bw*0.96, cy_bottom-h*0.46), (cx+bw, cy_bottom)]
    dl.polygon([sc.p(*q) for q in pts], fill=body)
    for sg in (-1, 1):                                   # руки-отростки
        ax = cx + sg*bw*0.90
        rise = math.sin(t*0.8 + (0 if sg < 0 else 1.6))*h*0.012
        dl.polygon([sc.p(ax, cy_bottom-h*0.52), sc.p(ax+sg*h*0.17, cy_bottom-h*0.40+rise),
                    sc.p(ax+sg*h*0.15, cy_bottom-h*0.26+rise), sc.p(ax, cy_bottom-h*0.30)],
                   fill=body)
    # ядро — чуть плотнее в середине туловища
    dl.ellipse(sc.box(cx-bw*0.56, cy_bottom-h*0.72, cx+bw*0.56, cy_bottom-h*0.06),
               fill=(6, 7, 13, 90))
    layer = layer.filter(ImageFilter.GaussianBlur(cam.r(soft)))
    a = np.asarray(layer).astype(np.float32)
    grad = np.linspace(0.94, 0.68, LH, dtype=np.float32).reshape(LH, 1)  # книзу растворяется
    a[..., 3] *= grad*opacity*(alpha/255.0)
    layer = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    im.alpha_composite(layer, (X0, Y0))

    # --- глаза и ухмылка: поверх, в полную силу ---
    eb = 1.0 - blink(t, 0.37, 5.6, 0.12)*0.85
    ey = cy_bottom - h*0.845
    ex = r*0.46
    ea = int(alpha*eb*(alpha/255.0)**0.7)
    if ea > 8:
        ec = RED + (ea,)
        for sg in (-1, 1):
            add_glow(im, *cam.p(cx+sg*ex, ey), cam.r(r*0.62), RED, 0.70*(ea/255), 2.1)
            q = [(cx+sg*ex-sg*r*0.30, ey+r*0.10), (cx+sg*ex+sg*r*0.30, ey-r*0.11),
                 (cx+sg*ex+sg*r*0.30, ey+r*0.02), (cx+sg*ex-sg*r*0.30, ey+r*0.23)]
            d.polygon([cam.p(*w) for w in q], fill=ec)
        if grin > 0:
            gw = r*0.40*grin
            d.arc(cam.box(cx-gw, ey+r*0.46, cx+gw, ey+r*1.06), start=28, end=152,
                  fill=RED + (int(ea*0.52),), width=max(1, int(cam.r(r*0.050))))

# ---------- предметы ----------
def phone(im, d, cam, cx, cy, w, screen=None, bright=1.0, rows=0.0, off=False, t=0.0):
    h = w*2.02
    d.rounded_rectangle(cam.box(cx-w/2, cy-h/2, cx+w/2, cy+h/2), radius=cam.r(w*0.14),
                        fill=(16, 18, 24, 255), outline=(78, 86, 104, 255),
                        width=max(1, int(cam.r(w*0.012))))
    pad = w*0.045
    sx0, sy0, sx1, sy1 = cx-w/2+pad, cy-h/2+pad, cx+w/2-pad, cy+h/2-pad
    if off:
        d.rounded_rectangle(cam.box(sx0, sy0, sx1, sy1), radius=cam.r(w*0.11),
                            fill=(9, 10, 14, 255))
        return
    d.rounded_rectangle(cam.box(sx0, sy0, sx1, sy1), radius=cam.r(w*0.11),
                        fill=mix((11, 13, 20), (28, 32, 44), bright) + (255,))
    if w > 150:   # статус-бар виден только на крупном плане
        fs = max(7, int(cam.r(w*0.055)))
        d.text(cam.p(sx0+w*0.10, sy0+w*0.075), "0:47", font=FH(fs),
               fill=(150, 158, 176, 255), anchor="lm")
        for k in range(3):
            bx = sx1-w*0.10-k*w*0.045
            d.rectangle(cam.box(bx-w*0.015, sy0+w*0.052, bx, sy0+w*0.098),
                        fill=(150, 158, 176, 255))
    if screen == "feed":
        sh = sy1-sy0
        rowh = sh*0.235
        o = (rows % 1.0)*rowh
        y = sy0 - rowh + o
        i = 0
        while y < sy1:
            top, bot = max(y, sy0), min(y+rowh*0.88, sy1)
            if bot-top > 4:
                c = [(96, 108, 142), (122, 86, 148), (78, 112, 140), (146, 92, 104)][i % 4]
                cc = mix(c, (236, 242, 255), 0.30*bright)
                d.rounded_rectangle(cam.box(sx0+w*0.05, top, sx1-w*0.05, bot),
                                    radius=cam.r(w*0.05), fill=cc + (255,))
                if w > 150 and bot-top > rowh*0.5:
                    d.ellipse(cam.box(sx0+w*0.11, bot-w*0.17, sx0+w*0.19, bot-w*0.09),
                              fill=mix(cc, (255, 255, 255), 0.45) + (255,))
                    d.rounded_rectangle(cam.box(sx0+w*0.23, bot-w*0.15, sx0+w*0.52, bot-w*0.11),
                                        radius=cam.r(w*0.02),
                                        fill=mix(cc, (255, 255, 255), 0.30) + (255,))
            y += rowh; i += 1
        if w > 150:
            d.rounded_rectangle(cam.box(sx1-w*0.035, sy0+sh*((rows*0.07) % 0.78),
                                        sx1-w*0.018, sy0+sh*(((rows*0.07) % 0.78)+0.18)),
                                radius=cam.r(w*0.009), fill=(120, 130, 152, 150))
    add_glow(im, *cam.p(cx, cy), cam.r(w*1.7), (176, 198, 255), 0.30*bright, 2.3)

def hands(d, cam, cx, cy, w, color=CREAM, t=0.0):
    col = color + (255,)
    for sg in (-1, 1):
        px = cx + sg*w*0.68 + math.sin(t*0.9 + sg)*w*0.006
        d.rounded_rectangle(cam.box(px-w*0.16, cy+w*0.52, px+w*0.16, cy+w*2.2),
                            radius=cam.r(w*0.155), fill=col)
        for k in range(3):
            fy = cy + w*0.62 + k*w*0.235
            xa, xb = px, px - sg*w*0.26
            d.rounded_rectangle(cam.box(min(xa, xb), fy, max(xa, xb), fy+w*0.135),
                                radius=cam.r(w*0.067), fill=col)

def clock(im, d, cam, x, y, text, size=30, color=RED, t=0.0):
    d.rounded_rectangle(cam.box(x-size*1.5, y-size*0.62, x+size*1.5, y+size*0.62),
                        radius=cam.r(size*0.2), fill=(12, 13, 18, 255))
    sep = ":" if (t % 2.0) < 1.0 else " "
    d.text(cam.p(x, y), text.replace(":", sep), font=FH(max(8, int(cam.r(size)))),
           fill=color + (255,), anchor="mm")
    add_glow(im, *cam.p(x, y), cam.r(size*2.2), color, 0.18, 2.6)

# ---------- локации ----------
def room(im, d, cam, warm=0.0, t=0.0, lamp=0.0, rain=True):
    wall  = mix((22, 27, 40), (58, 39, 25), warm)
    floor = mix((12, 15, 23), (36, 24, 16), warm)
    edge  = mix((34, 41, 58), (80, 56, 36), warm)
    d.rectangle(cam.box(-500, -400, W+500, H*0.715), fill=wall + (255,))
    d.rectangle(cam.box(-500, H*0.715, W+500, H+400), fill=floor + (255,))
    d.rectangle(cam.box(-500, H*0.700, W+500, H*0.715), fill=edge + (255,))
    # ковёр
    d.rounded_rectangle(cam.box(430, 930, 1340, 1060), radius=cam.r(14),
                        fill=mix((18, 22, 33), (46, 31, 20), warm) + (255,))
    # постер на стене
    px0, py0, px1, py1 = 418, 214, 616, 462
    d.rectangle(cam.box(px0, py0, px1, py1), fill=mix((24, 29, 43), (56, 38, 24), warm) + (255,))
    d.rectangle(cam.box(px0+12, py0+12, px1-12, py1-12),
                fill=mix((16, 20, 30), (40, 27, 17), warm) + (255,))
    for k in range(4):
        d.rectangle(cam.box(px0+32, py0+54+k*44, px1-32-k*30, py0+70+k*44),
                    fill=mix((30, 37, 52), (70, 48, 30), warm) + (255,))
    # окно
    wx0, wy0, wx1, wy1 = 1210, 150, 1600, 545
    d.rectangle(cam.box(wx0-16, wy0-16, wx1+16, wy1+22),
                fill=mix((30, 36, 52), (74, 52, 34), warm) + (255,))
    d.rectangle(cam.box(wx0, wy0, wx1, wy1), fill=mix((7, 10, 19), (26, 19, 14), warm) + (255,))
    rnd = random.Random(7)
    for i in range(30):
        lx = rnd.uniform(wx0+14, wx1-26); ly = rnd.uniform(wy0+20, wy1-24)
        sz = rnd.uniform(5, 10)
        tw = 0.5 + 0.5*math.sin(t*0.55 + i*1.7)
        d.rectangle(cam.box(lx, ly, lx+sz, ly+sz*1.25),
                    fill=mix((34, 41, 58), AMBER, 0.30+0.40*tw) + (255,))
    if rain:
        rr = random.Random(31)
        for i in range(34):
            spd = rr.uniform(170, 265)
            x0 = rr.uniform(wx0+6, wx1-6)
            y0 = (rr.uniform(0, 1)*(wy1-wy0) + t*spd) % (wy1-wy0) + wy0
            ln = rr.uniform(16, 30)
            if y0+ln > wy1: ln = wy1-y0
            if ln < 3: continue
            d.line([cam.p(x0, y0), cam.p(x0-ln*0.22, y0+ln)],
                   fill=mix((60, 72, 96), (140, 110, 80), warm) + (120,),
                   width=max(1, int(cam.r(2))))
    gc = mix((30, 36, 52), (74, 52, 34), warm) + (255,)
    d.line([cam.p((wx0+wx1)/2, wy0), cam.p((wx0+wx1)/2, wy1)], fill=gc, width=max(2, int(cam.r(9))))
    d.line([cam.p(wx0, (wy0+wy1)/2), cam.p(wx1, (wy0+wy1)/2)], fill=gc, width=max(2, int(cam.r(9))))
    # кровать
    d.rounded_rectangle(cam.box(300, 560, 372, 900), radius=cam.r(12),
                        fill=mix((30, 36, 52), (66, 46, 30), warm) + (255,))
    d.rounded_rectangle(cam.box(312, 690, 1180, 900), radius=cam.r(20),
                        fill=mix((40, 47, 66), (82, 58, 38), warm) + (255,))
    d.rounded_rectangle(cam.box(352, 648, 580, 716), radius=cam.r(28),
                        fill=mix((58, 66, 88), (108, 80, 54), warm) + (255,))
    # тумбочка + мелочи
    d.rounded_rectangle(cam.box(140, 726, 300, 906), radius=cam.r(10),
                        fill=mix((28, 34, 48), (58, 40, 26), warm) + (255,))
    d.line([cam.p(158, 812), cam.p(282, 812)],
           fill=mix((16, 20, 30), (36, 24, 16), warm) + (255,), width=max(1, int(cam.r(4))))
    bk = mix((46, 54, 74), (96, 66, 42), warm)
    d.rectangle(cam.box(150, 700, 236, 714), fill=bk + (255,))
    d.rectangle(cam.box(156, 686, 230, 700), fill=mix(bk, (255, 255, 255), 0.12) + (255,))
    d.rounded_rectangle(cam.box(252, 676, 292, 712), radius=cam.r(5),
                        fill=mix((54, 62, 84), (104, 74, 46), warm) + (255,))
    d.arc(cam.box(286, 684, 306, 704), start=300, end=60,
          fill=mix((54, 62, 84), (104, 74, 46), warm) + (255,), width=max(1, int(cam.r(4))))
    # провод зарядки
    d.line([cam.p(300, 756), cam.p(360, 800), cam.p(420, 846), cam.p(470, 858)],
           fill=mix((20, 25, 36), (44, 30, 20), warm) + (255,), width=max(1, int(cam.r(5))), joint="curve")
    if lamp > 0:
        add_glow(im, *cam.p(1040, 300), cam.r(560), AMBER, 0.22*lamp, 2.4)

def dust(im, cam, cx, cy, r, t, n=22, color=(190, 210, 255), strength=0.5):
    rr = random.Random(99)
    for i in range(n):
        a = rr.uniform(0, 6.28); rad = rr.uniform(0.15, 1.0)*r
        dx = math.cos(a)*rad
        dy = math.sin(a)*rad - ((t*rr.uniform(6, 18) + i*30) % (r*1.6)) + r*0.5
        tw = 0.35 + 0.65*abs(math.sin(t*rr.uniform(0.6, 1.6) + i))
        px, py = cam.p(cx+dx, cy+dy)
        add_glow(im, px, py, cam.r(rr.uniform(2.6, 5.4)), color, strength*tw, 1.6)

def city(im, d, cam, warm=1.0, t=0.0):
    sky_top = mix((16, 20, 30), (48, 26, 16), warm)
    sky_bot = mix((28, 33, 46), (238, 158, 78), warm)
    arr = np.zeros((H, 1, 3), dtype=np.uint8)
    for y in range(H): arr[y, 0] = mix(sky_top, sky_bot, (y/H) ** 1.7)
    im.alpha_composite(Image.fromarray(arr, "RGB").resize((W, H)).convert("RGBA"), (0, 0))
    # облака
    rc = random.Random(5)
    for i in range(7):
        cxx = (rc.uniform(-200, W) + t*rc.uniform(3, 9)) % (W+600) - 300
        cyy = rc.uniform(120, 360)
        soft_ellipse(im, cxx, cyy, rc.uniform(180, 320), rc.uniform(26, 52),
                     mix((40, 48, 66), (255, 196, 128), warm), 0.26, 1.5)
    add_glow(im, W*0.70, H*0.62, 680, AMBER, 0.50*warm, 2.0)
    rnd = random.Random(21)
    for layer, (col, hmin, hmax) in enumerate([((36, 22, 15), 240, 470), ((22, 14, 10), 150, 330)]):
        c = mix((16, 20, 30), col, warm)
        x = -150
        while x < W+150:
            bw_ = rnd.uniform(100, 165); bh = rnd.uniform(hmin, hmax)
            d.rectangle([x, H*0.735-bh, x+bw_, H*0.80], fill=c + (255,))
            if layer == 0:
                for k in range(int(bh//78)):
                    for j in range(2):
                        lit = (math.sin(k*3.1 + j*1.7 + x*0.01) > -0.4)
                        d.rectangle([x+22+j*44, H*0.735-bh+26+k*78, x+42+j*44, H*0.735-bh+54+k*78],
                                    fill=mix(c, AMBER, 0.45 if lit else 0.14) + (255,))
            x += bw_ + rnd.uniform(18, 46)
    d.rectangle([0, H*0.785, W, H], fill=mix((12, 15, 22), (44, 27, 17), warm) + (255,))
    d.rectangle([0, H*0.785, W, H*0.80], fill=mix((20, 25, 36), (86, 56, 32), warm) + (255,))
    # фонари
    for lx in (250, 760, 1300, 1790):
        d.rectangle([lx-5, H*0.60, lx+5, H*0.79], fill=mix((14, 17, 25), (36, 23, 14), warm) + (255,))
        add_glow(im, lx, H*0.595, 54, (255, 214, 150), 0.55, 2.0)

# ---------- интерфейс ----------
_blur_cache = {}
def blurred_room(im, key="n", warm=0.0, scale=1.12):
    if key not in _blur_cache:
        tmp = Image.new("RGBA", (SW, SH), (8, 10, 15, 255))
        td = SDraw(tmp, "RGBA")
        room(tmp, td, Cam(scale, W/2, H*0.56), warm=warm, t=0.0, rain=False)
        _blur_cache[key] = tmp.filter(ImageFilter.GaussianBlur(26*SS))
    im.alpha_composite(_blur_cache[key], (0, 0))

_scrim_cache = {}
def lower_scrim(im, strength=0.80, top=0.70):
    """Плавное затемнение низа кадра под подпись.

    ГОЧА 22.10, стоила правки вслепую: ImageDraw.Draw(im, "RGBA") по RGBA-кадру
    НЕ смешивает, а ЗАМЕЩАЕТ пиксель вместе с альфой. Поэтому попытка рисовать
    шторку полосами дала не градиент, а чёрную стену, срезавшую треть кадра.
    Смешивать может только alpha_composite — он здесь и стоит.

    Память бережём иначе: слой хранится РАЗМЕРОМ С ОБЛАСТЬ (треть кадра), а не
    во весь кадр, и ключей не больше восьми — это ~10 МБ на ключ вместо 33, и
    кэш не может разрастись на гигабайты, как было до 22.10.
    """
    key = (round(strength, 2), round(top, 2))
    if key not in _scrim_cache:
        y0 = int(SH*top); h = SH - y0
        y = np.linspace(0, 1, h).reshape(h, 1)
        a = np.clip(y, 0, 1) ** 1.5 * 255 * strength
        sc = np.zeros((h, SW, 4), dtype=np.uint8)
        sc[..., 3] = np.repeat(a.astype(np.uint8), SW, axis=1)
        layer = Image.fromarray(sc, "RGBA")
        if len(_scrim_cache) < 8: _scrim_cache[key] = (layer, y0)
        else: return im.alpha_composite(layer, (0, y0))
    layer, y0 = _scrim_cache[key]
    im.alpha_composite(layer, (0, y0))

def dim(im, a):
    """Затемнение в чёрный на склейках. Только alpha_composite — см. гочу выше:
    прямоугольник через ImageDraw замещал кадр и превращал плавный провал в
    резкую склейку."""
    if a <= 1: return
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, int(min(255, a)))), (0, 0))

# ---------- финал кадра ----------
_vig = None
def vignette():
    global _vig
    if _vig is None:
        y, x = np.ogrid[0:SH, 0:SW]
        dx = (x-SW/2)/(SW/2); dy = (y-SH/2)/(SH/2)
        r = np.sqrt(dx*dx + dy*dy)/1.42
        a = (np.clip(r, 0, 1) ** 2.1)*150
        v = np.zeros((SH, SW, 4), dtype=np.uint8); v[..., 3] = a.astype(np.uint8)
        _vig = Image.fromarray(v, "RGBA")
    return _vig

_noise = np.random.default_rng(3).integers(-5, 6, (H, W, 1), dtype=np.int16)
def finish(im):
    im.alpha_composite(vignette(), (0, 0))
    small = im.convert("RGB").resize((W, H), Image.LANCZOS)
    a = np.asarray(small).astype(np.int16) + _noise
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


_lb = None
def letterbox(im, frac=0.085):
    """Чёрные кинополосы сверху и снизу."""
    global _lb
    if _lb is None or _lb[0] != frac:
        bar = int(SH*frac)
        lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.rectangle([0, 0, SW, bar], fill=(0, 0, 0, 255))
        dd.rectangle([0, SH-bar, SW, SH], fill=(0, 0, 0, 255))
        _lb = (frac, lay)
    im.alpha_composite(_lb[1], (0, 0))
