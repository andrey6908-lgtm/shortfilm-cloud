# -*- coding: utf-8 -*-
"""Круг 2 стиля Ifverse: ФОН + ПОСАДКА ФИГУРЫ + ЦВЕТ одним заходом.
Вектор (SVG + cairosvg), считается в облаке.

Замеры оригинала, на которые опирается файл (РАЗБОР.md):
  цвет       одна сцена = один тон; белого нет (99-й перцентиль 122-233,
             медиана 170); насыщенность 0,18-0,40; чёрный #09080D нас.0,38
  фон        боке, но сквозь него читаются двери, сиденья, поручни, массовка
  фигура     покатые плечи, рукава к кистям, план по бёдра, а не по грудь
  контур     дуга 13 px при 1440 цветом источника, с одной стороны
  зерна нет, кинополосы 5,7%
"""
import io, os
import cairosvg
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

W, H = 1920, 1080
LB = int(H * 0.057)                 # кинополосы 5,7%

INK    = "#0B0C16"                  # «чёрный», тонированный в синеву
CLOTH  = "#2D55B7"
GOLD   = "#EFC44E"
PLATE  = "#171209"
LIGHT  = "#9EC8DF"                  # источник сцены — окно вагона

FONTS = [("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "Liberation Sans"),
         ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVu Sans"),
         ("/mnt/c/Windows/Fonts/arialbd.ttf", "Arial")]
FPATH, FFAM = next((p, n) for p, n in FONTS if os.path.exists(p))


def png(svg, w=W, h=H):
    return Image.open(io.BytesIO(cairosvg.svg2png(
        bytestring=svg.encode(), output_width=w, output_height=h))).convert("RGBA")


def x(f): return int(W * f)
def y(f): return int(H * f)


# ============================================================ ФОН: ВАГОН
# Среда строится ЧИТАЕМОЙ: двери со стыком, ряд сидений с разделителями,
# поручни (труба с петлями и две стойки), окна тоннеля, рекламная панель,
# пассажир в боке со своим числом. Боке кладётся сверху, детали проступают.
bg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
<defs>
 <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#48606B"/><stop offset="0.62" stop-color="#354A55"/>
  <stop offset="1" stop-color="#25363F"/>
 </linearGradient>
 <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2E4A59"/><stop offset="1" stop-color="#1B2C36"/>
 </linearGradient>
 <linearGradient id="seat" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#427A90"/><stop offset="1" stop-color="#2C4F60"/>
 </linearGradient>
 <linearGradient id="lamp" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#C2D6DA"/><stop offset="1" stop-color="#7E9AA3"/>
 </linearGradient>
 <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#283B45"/><stop offset="1" stop-color="#1F2E37"/>
 </linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#wall)"/>

<!-- потолок и световая панель на всю длину вагона -->
<rect x="0" y="0" width="{W}" height="{y(0.115)}" fill="#3A4F59"/>
<rect x="{x(0.06)}" y="{y(0.040)}" width="{x(0.88)}" height="{y(0.030)}" rx="{y(0.015)}" fill="url(#lamp)"/>
<rect x="{x(0.06)}" y="{y(0.070)}" width="{x(0.88)}" height="{y(0.012)}" fill="#55707A" opacity="0.7"/>

<!-- рекламная панель над окнами -->
<rect x="{x(0.52)}" y="{y(0.145)}" width="{x(0.36)}" height="{y(0.072)}" rx="8" fill="#5A7682"/>
<rect x="{x(0.545)}" y="{y(0.163)}" width="{x(0.20)}" height="{y(0.015)}" rx="7" fill="#7C98A2"/>
<rect x="{x(0.545)}" y="{y(0.187)}" width="{x(0.11)}" height="{y(0.013)}" rx="6" fill="#64818C"/>
'''

# двустворчатые двери со стыком и резиновым уплотнителем
dx0, dx1 = x(0.025), x(0.265)
bg += (f'<rect x="{dx0}" y="{y(0.145)}" width="{dx1-dx0}" height="{y(0.60)}" rx="10" fill="#52707C"/>'
       f'<rect x="{dx0+14}" y="{y(0.168)}" width="{(dx1-dx0)//2-24}" height="{y(0.30)}" rx="8" fill="url(#glass)"/>'
       f'<rect x="{dx0+(dx1-dx0)//2+10}" y="{y(0.168)}" width="{(dx1-dx0)//2-24}" height="{y(0.30)}" rx="8" fill="url(#glass)"/>'
       f'<rect x="{dx0+(dx1-dx0)//2-7}" y="{y(0.145)}" width="14" height="{y(0.60)}" fill="#1C282F"/>'
       f'<rect x="{dx0}" y="{y(0.145)}" width="{dx1-dx0}" height="10" fill="#5C777F"/>'
       f'<rect x="{dx0+20}" y="{y(0.50)}" width="{dx1-dx0-40}" height="{y(0.022)}" rx="6" fill="#536E78"/>')

# ряд окон тоннеля с рамами и косым бликом
for i in range(3):
    wx = x(0.30) + i * x(0.235)
    bg += (f'<rect x="{wx}" y="{y(0.165)}" width="{x(0.205)}" height="{y(0.275)}" rx="14" fill="#5A7682"/>'
           f'<rect x="{wx+12}" y="{y(0.178)}" width="{x(0.205)-24}" height="{y(0.249)}" rx="10" fill="url(#glass)"/>'
           f'<path d="M {wx+30} {y(0.425)} L {wx+x(0.11)} {y(0.180)} L {wx+x(0.155)} {y(0.180)}'
           f' L {wx+75} {y(0.425)} Z" fill="#7FA6B6" opacity="0.30"/>')

# ряд сидений с разделителями и тенью под ними
bg += (f'<rect x="0" y="{y(0.575)}" width="{W}" height="{y(0.135)}" rx="16" fill="url(#seat)"/>'
       f'<rect x="0" y="{y(0.575)}" width="{W}" height="{y(0.016)}" fill="#44708280"/>')
for i in range(9):
    sx = x(0.02) + i * x(0.113)
    bg += (f'<rect x="{sx}" y="{y(0.578)}" width="10" height="{y(0.128)}" fill="#1E3744"/>'
           f'<rect x="{sx+14}" y="{y(0.586)}" width="{x(0.098)}" height="{y(0.030)}" rx="12" fill="#3E6A7D" opacity="0.55"/>')
bg += f'<rect x="0" y="{y(0.710)}" width="{W}" height="{y(0.030)}" fill="#152028" opacity="0.8"/>'

# поручни: труба под потолком с петлями + две вертикальные стойки
bg += f'<rect x="0" y="{y(0.212)}" width="{W}" height="11" rx="5" fill="#8099A2"/>'
for i in range(7):
    hx = x(0.07) + i * x(0.145)
    bg += (f'<path d="M {hx} {y(0.222)} q 0 {y(0.055)} {x(0.016)} {y(0.055)}'
           f' q {x(0.016)} 0 {x(0.016)} -{y(0.055)}" fill="none" stroke="#6F878F" stroke-width="7"/>')
for sx in (x(0.335), x(0.715)):
    bg += f'<rect x="{sx}" y="{y(0.115)}" width="13" height="{y(0.62)}" rx="6" fill="#748C95"/>'

# пол
bg += f'<rect x="0" y="{y(0.740)}" width="{W}" height="{y(0.26)}" fill="url(#floor)"/>'

# пассажир в боке со своим числом — как у них в каждом плане
px_, py_ = x(0.175), y(0.455)
bg += (f'<circle cx="{px_}" cy="{py_}" r="78" fill="#0E131C"/>'
       f'<path d="M {px_-104} {y(0.95)} L {px_-96} {py_+112} Q {px_-70} {py_+52} {px_} {py_+44}'
       f' Q {px_+70} {py_+52} {px_+96} {py_+112} L {px_+104} {y(0.95)} Z" fill="#3C6270"/>'
       f'<rect x="{px_-54}" y="{py_-146}" width="108" height="56" rx="28" fill="{PLATE}" stroke="{GOLD}" stroke-width="4"/>'
       f'<text x="{px_}" y="{py_-106}" font-family="{FFAM}" font-weight="bold" font-size="34"'
       f' fill="{GOLD}" text-anchor="middle">12</text>')

# мотивированный источник: пятно света из окна слева сверху
bg += (f'<defs><radialGradient id="src"><stop offset="0" stop-color="#9EC8DF" stop-opacity="0.26"/>'
       f'<stop offset="1" stop-color="#9EC8DF" stop-opacity="0"/></radialGradient></defs>'
       f'<ellipse cx="{x(0.37)}" cy="{y(0.30)}" rx="{x(0.34)}" ry="{y(0.40)}" fill="url(#src)"/>')
bg += "</svg>"

im = png(bg).filter(ImageFilter.GaussianBlur(9)).convert("RGBA")

# ======================================================= ФИГУРА: ПОСАДКА
# План по бёдра (голова вдвое мельче прошлого круга), плечи покатые,
# рукава сужаются к кистям, кисти видны. Корпус сужается книзу, не трапеция.
cx, cy, hr = 960, 452, 132
sw = hr * 1.24                      # плечи узкие: у них толстовка облегает

body = (f'M {cx-sw*1.14} {H} '
        f'L {cx-sw*1.00} {cy+hr*2.10} '
        f'Q {cx-sw*0.96} {cy+hr*1.08} {cx-hr*0.56} {cy+hr*0.78} '   # покатое плечо
        f'Q {cx} {cy+hr*0.46} {cx+hr*0.56} {cy+hr*0.78} '
        f'Q {cx+sw*0.96} {cy+hr*1.08} {cx+sw*1.00} {cy+hr*2.10} '
        f'L {cx+sw*1.14} {H} Z')

def sleeve(s_):
    """Рукав полосой вдоль корпуса, сужается к кисти, кисть — его продолжение."""
    o, i = s_*sw*1.02, s_*sw*0.62          # внешний и внутренний край у плеча
    o2, i2 = s_*sw*1.10, s_*sw*0.74        # у кисти
    return (f'M {cx+o} {cy+hr*1.00} '
            f'Q {cx+o*1.06} {cy+hr*2.20} {cx+o2} {cy+hr*3.14} '
            f'Q {cx+(o2+i2)/2} {cy+hr*3.52} {cx+i2} {cy+hr*3.10} '
            f'Q {cx+i*1.02} {cy+hr*2.12} {cx+i} {cy+hr*1.16} Z')

def hand(s_):
    hx = cx + s_*sw*0.92
    return (f'<path d="M {hx-sw*0.155} {cy+hr*3.18} '
            f'Q {hx} {cy+hr*3.70} {hx+sw*0.155} {cy+hr*3.14} '
            f'Q {hx} {cy+hr*3.34} {hx-sw*0.155} {cy+hr*3.18} Z" fill="{INK}"/>')

fig = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
<defs>
 <linearGradient id="cl" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#3C69CE"/><stop offset="1" stop-color="#24479A"/>
 </linearGradient>
</defs>
<path d="{body}" fill="url(#cl)"/>
<path d="{sleeve(-1)}" fill="#27499F"/>
<path d="{sleeve(+1)}" fill="#27499F"/>
{hand(-1)}
{hand(+1)}
<path d="M {cx-hr*0.56} {cy+hr*0.80} Q {cx} {cy+hr*1.22} {cx+hr*0.56} {cy+hr*0.80}"
      fill="none" stroke="#1C3A84" stroke-width="8" stroke-linecap="round"/>
<path d="M {cx-hr*0.24} {cy+hr*1.08} L {cx-hr*0.28} {cy+hr*2.02}" stroke="#D8DEEA"
      stroke-width="6" stroke-linecap="round" fill="none"/>
<path d="M {cx+hr*0.24} {cy+hr*1.08} L {cx+hr*0.28} {cy+hr*2.02}" stroke="#D8DEEA"
      stroke-width="6" stroke-linecap="round" fill="none"/>
<circle cx="{cx}" cy="{cy}" r="{hr}" fill="{INK}"/>
<g fill="#F2ECDC">
  <path d="M {cx-hr*0.60} {cy+hr*0.06} h {hr*0.44} a {hr*0.22} {hr*0.16} 0 0 1 0 {hr*0.20}
           h -{hr*0.44} a {hr*0.22} {hr*0.16} 0 0 1 0 -{hr*0.20} Z"/>
  <path d="M {cx+hr*0.16} {cy+hr*0.06} h {hr*0.44} a {hr*0.22} {hr*0.16} 0 0 1 0 {hr*0.20}
           h -{hr*0.44} a {hr*0.22} {hr*0.16} 0 0 1 0 -{hr*0.20} Z"/>
  <rect x="{cx-hr*0.26}" y="{cy+hr*0.52}" width="{hr*0.52}" height="{hr*0.075}" rx="{hr*0.037}"/>
</g>
</svg>'''
figim = png(fig)

# ----- контурный свет: дуга цветом источника, с одной стороны, по всей фигуре
mask = figim.split()[3]
px = 13                              # 13 px при 1440 → ~17 при 1920 по ширине кадра
sh = Image.new("L", mask.size, 0)
sh.paste(mask, (-int(px * 0.8), -int(px * 1.0)))
arc = np.clip(np.asarray(sh).astype(np.int16) - np.asarray(mask).astype(np.int16), 0, 255)
arc = np.asarray(Image.fromarray(arc.astype(np.uint8))
                 .filter(ImageFilter.GaussianBlur(px * 0.26))).astype(np.float32)
ys = np.linspace(0, 1, arc.shape[0])[:, None]
top = float(np.argmax(np.asarray(mask).max(1) > 0)) / arc.shape[0]
arc *= np.clip(1.25 - (ys - top) * 1.45, 0.10, 1)     # слабеет книзу, но доходит до кистей
rim = Image.new("RGBA", mask.size, (158, 200, 223, 0))
rim.putalpha(Image.fromarray(arc.astype(np.uint8)))
im.alpha_composite(rim)
im.alpha_composite(figim)

# ================================================================= HUD
def plate_svg(text, size, pad=0.62):
    f = ImageFont.truetype(FPATH, size)
    w = int(ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(text, font=f))
    pw, ph = w + int(size * pad * 2), int(size * 1.72)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {pw} {ph}">'
            f'<rect x="3" y="3" width="{pw-6}" height="{ph-6}" rx="{(ph-6)/2}"'
            f' fill="{PLATE}" stroke="{GOLD}" stroke-width="5"/>'
            f'<rect x="11" y="11" width="{pw-22}" height="{ph-22}" rx="{(ph-22)/2}"'
            f' fill="none" stroke="#2E2410" stroke-width="3"/>'
            f'<text x="{pw/2}" y="{ph*0.70}" font-family="{FFAM}" font-weight="bold"'
            f' font-size="{size}" fill="{GOLD}" text-anchor="middle">{text}</text></svg>', pw, ph)

for text, size, pos in (("УРОВЕНЬ 1", 46, (62, LB + 28)), ("1", 54, None)):
    svg, pw, ph = plate_svg(text, size)
    p = png(svg, pw, ph)
    im.alpha_composite(p, pos if pos else (cx - pw // 2, cy - hr - ph - 24))

# ============================================================== ЦВЕТ
a = np.asarray(im.convert("RGB")).astype(np.float32)

# один тон на сцену: всё, что не фигура, стягивается к сине-зелёной оси
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
a *= np.clip(1.03 - 0.20 * np.clip(r - 0.55, 0, None) ** 1.5, 0, 1)[..., None]

# белого в кадре нет: верх зажат, как у них (99-й перцентиль 122-233)
a = 228.0 * (a / 255.0) ** 0.92
# чёрный не чистый, а тонированный в синеву — пол по каналам, не общий
a = np.maximum(a, np.array([5.0, 5.0, 9.0]))

out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(out)
d.rectangle([0, 0, W, LB], fill=(0, 0, 0))
d.rectangle([0, H - LB, W, H], fill=(0, 0, 0))
out.save("vec5.jpg", quality=95)

# ============================================================= ЗАМЕР
b = np.asarray(out).astype(np.float32)
g = b.mean(2)
core = b[int(H * 0.07):int(H * 0.93)]
mx, mn = core.max(2), core.min(2)
s = np.where(mx > 8, (mx - mn) / np.maximum(mx, 1), 0)
print("круг 5: ярк %.1f  медиана %.0f  99-й перц %.0f  насыщ %.3f  провалов в чёрный %.1f%%"
      % (g.mean(), np.median(g), np.percentile(g, 99), s.mean(), ((mx / 255.0) < 0.06).mean() * 100))
print("цель Ifverse: медиана 170  99-й перц 122-233  насыщ 0,18-0,40  провалов 3,3%")
