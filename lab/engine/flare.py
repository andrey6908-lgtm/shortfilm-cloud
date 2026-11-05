# -*- coding: utf-8 -*-
"""АНАМОРФНЫЙ БЛИК В ОБЪЕКТИВ. Фактура «снято камерой», а не нарисовано.

Почему это дёшево. Блик — не предмет сцены, а свет, размазанный ОПТИКОЙ, и
считать его в супердискретизации (3840x2160) незачем: он гладкий. Поэтому
блик кладётся ПОСЛЕ сборки кадра, на готовые 1920x1080 — вчетверо меньше
пикселей.

Второй приём на экономию: полоса и ореол СЕПАРАБЕЛЬНЫ. Яркость полосы
`exp(-(dy/h)^2) * exp(-|dx|/L)` — это произведение функции от y на функцию от
x, то есть внешнее произведение двух одномерных массивов (`np.outer`), а не
расчёт по каждому пикселю. Ореол так же. Призраки считаются только в своих
маленьких окнах. Итого блик стоит единицы процентов времени кадра.

Что в блике (всё по классике анаморфной оптики):
* горизонтальная ПОЛОСА через источник — холодная, голубая;
* тонкое ядро полосы, яркое;
* ОРЕОЛ вокруг источника — тёплый;
* ПРИЗРАКИ: кольца по линии «источник — центр кадра» и дальше за центр, в
  разных цветах и слабые;
* ВУАЛЬ: едва заметное общее осветление, когда источник близко к оси.
"""
import numpy as np
from film import W, H, clamp

STREAK = np.array([0.42, 0.62, 1.00])      # цвет полосы: холодный голубой
CORE   = np.array([0.80, 0.90, 1.00])
HALO   = np.array([1.00, 0.84, 0.60])      # ореол: тёплый
VEIL   = np.array([0.52, 0.66, 0.90])
# призраки: доля пути от источника через центр, радиус, цвет, сила
GHOSTS = ((-0.34,  34.0, (0.45, 0.95, 0.88), 0.055),
          ( 0.26,  58.0, (1.00, 0.78, 0.42), 0.075),
          ( 0.58,  88.0, (0.40, 0.80, 1.00), 0.060),
          ( 0.92,  46.0, (1.00, 0.55, 0.70), 0.050),
          ( 1.28, 120.0, (0.55, 0.90, 0.75), 0.040))

_X = np.arange(W, dtype=np.float32)
_Y = np.arange(H, dtype=np.float32)


def _ring(buf, cx, cy, r0, col, amp):
    """Кольцо-призрак: считается только в своём окне, не на всём кадре."""
    r = r0*1.9
    x0, x1 = int(max(0, cx - r)), int(min(W, cx + r))
    y0, y1 = int(max(0, cy - r)), int(min(H, cy + r))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    dx = _X[x0:x1] - cx
    dy = _Y[y0:y1] - cy
    rr = np.sqrt(dy[:, None]**2 + dx[None, :]**2)
    prof = (np.exp(-((rr - r0)/(0.40*r0))**2)*0.95 +
            np.exp(-(rr/(0.72*r0))**2)*0.22).astype(np.float32)
    buf[y0:y1, x0:x1] += prof[:, :, None]*(np.asarray(col, dtype=np.float32)*amp)


def add(img, sources, limit=4):
    """img — готовый кадр PIL RGB 1920x1080. sources — (x, y, сила, радиус)."""
    src = [s for s in sources if s[2] > 0.012]
    if not src:
        return img
    src.sort(key=lambda s: -s[2])
    a = np.asarray(img, dtype=np.float32)
    buf = np.zeros((H, W, 3), dtype=np.float32)

    for x, y, k, rad in src[:limit]:
        k = float(min(k, 1.0))
        # полоса: внешнее произведение, не попиксельный расчёт
        gy = np.exp(-((_Y - y)/(4.6 + 2.2*k))**2).astype(np.float32)
        fx = np.exp(-np.abs(_X - x)/(260.0 + 420.0*k)).astype(np.float32)
        band = np.outer(gy, fx)
        buf += band[:, :, None]*(STREAK*(0.50*k))
        gy = np.exp(-((_Y - y)/1.7)**2).astype(np.float32)
        buf += np.outer(gy, fx)[:, :, None]*(CORE*(0.40*k))
        # ореол вокруг источника
        hr = rad*0.55 + 26.0
        gy = np.exp(-((_Y - y)/hr)**2).astype(np.float32)
        gx = np.exp(-((_X - x)/hr)**2).astype(np.float32)
        buf += np.outer(gy, gx)[:, :, None]*(HALO*(0.55*k))
        # призраки по линии «источник — центр кадра»
        vx, vy = W/2.0 - x, H/2.0 - y
        for f, gr, col, amp in GHOSTS:
            _ring(buf, x + vx*(1.0 + f), y + vy*(1.0 + f), gr*(0.6 + 0.7*k),
                  col, amp*k)
        # вуаль: тем заметнее, чем ближе источник к оси кадра
        ax = 1.0 - clamp((abs(vx)/(W*0.55) + abs(vy)/(H*0.55))*0.5)
        buf += (VEIL*(0.030*k*ax))[None, None, :]

    np.clip(a + buf*255.0, 0.0, 255.0, out=a)
    from PIL import Image
    return Image.fromarray(a.astype(np.uint8), "RGB")


def sources_from_lamps(cam, lamps, h=520.0, near=420.0, far=3200.0):
    """Экранные источники из фонарей сцены: сила падает с удалением и с уходом
    от оси кадра (фонарь у края кадра бликует слабее — так и в объективе)."""
    out = []
    for x, z in lamps:
        p = cam.pr((x, h + 26.0, z))
        if p[2] <= near*0.35:
            continue
        kd = clamp(1.0 - (p[2] - near)/(far - near))          # удаление
        rx = abs(p[0] - W/2.0)/(W*0.72); ry = abs(p[1] - H/2.0)/(H*0.72)
        ka = clamp(1.0 - (rx*rx + ry*ry))                     # уход от оси
        if min(p[0], p[1]) < -W*0.25 or p[0] > W*1.25 or p[1] > H*1.25:
            continue
        out.append((p[0], p[1], kd*ka*1.05, cam.rad(34.0, p[2])))
    return out
