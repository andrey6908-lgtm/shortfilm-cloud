# -*- coding: utf-8 -*-
"""Обложка ролика (превью для YouTube). Рисуется тем же движком, что и фильм.

    python3 thumb.py [папка]     → <папка>/thumb.jpg, 1920×1080

Схема взята у конкурентов (Day One / Monk Mode): крупное лицо героя по центру,
слева — то, от чего он зависим, справа — то, что он теряет, вопрос числом
вверху. Цвета строго наши: холодная синь зависимости против тёплого янтаря
живой жизни, демон — розовый.

Запускать ТОЛЬКО в облаке (слово пользователя 22.10: на его машине не считать
ничего). Локально разрешена лишь проверка импорта.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film import *
from people2 import *
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "thumb"
os.makedirs(OUT, exist_ok=True)

FB = lambda s: font("ariblk.ttf", s)      # Arial Black — заголовок обложки
COLD = (36, 58, 104)
WARM = (150, 86, 34)


def big_text(d, text, x, y, size, fill=(255, 255, 255), ring=(0, 0, 0), rw=11):
    """Жирная надпись с чёрной обводкой — язык обложек, не фильма.

    В самом ролике обводка запрещена (см. SKILL.md), здесь она обязательна:
    превью читается в ленте размером с ноготь, и без канта белое по светлому
    пропадает. Обводка рисуется кольцом смещений: stroke_width PIL при нашем
    суперсэмплинге даёт неровную толщину.
    """
    f = FB(size)
    for a in range(0, 360, 15):
        dx, dy = math.cos(a*math.pi/180)*rw, math.sin(a*math.pi/180)*rw
        d.text((x+dx, y+dy), text, font=f, fill=ring + (255,), anchor="mm")
    d.text((x, y), text, font=f, fill=fill + (255,), anchor="mm")


def title(d, parts, y, size):
    """Заголовок из кусков разного цвета, выровненный как единый блок.

    Ширины меряются заранее: первая версия обложки слепила «3 000ИЛИ», потому
    что куски ставились по долям ширины кадра на глаз.
    """
    f = FB(size)
    gap = size*0.30
    ws = [d.textlength(t, font=f) for t, _ in parts]
    x = W/2 - (sum(ws) + gap*(len(parts)-1))/2
    for (txt, col), w in zip(parts, ws):
        big_text(d, txt, x + w/2, y, size, fill=col)
        x += w + gap


# ГОЧА, стоила двух прогонов 22.10: голова фигуры лежит НЕ на 0,8h выше таза,
# как кажется по кадрам фильма, а на 0,418h — из draw_person: торс 0,265h плюс
# шея-голова 0,153h; радиус головы ровно 0,15h. Для обложки считать так:
#     hip_y = нужный_y_головы + 0.418*h,   h = нужный_радиус/0.15
# При h=1460 и тазе на 1860 голова уезжала на y=1250, то есть за нижний край.
HEAD_UP = 0.418
HR_K = 0.150

def put(head_y, hr):
    """Рост и точку таза по желаемому положению и размеру головы."""
    h = hr/HR_K
    return h, head_y + HEAD_UP*h


def background(im, d):
    # холодная половина слева, тёплая справа — сюжет читается до текста
    for i in range(96):
        k = i/95.0
        c = mix((12, 16, 26), (44, 26, 15), clamp((k-0.44)/0.30))
        d.rectangle([W*k, 0, W*(k+1/95.0)+2, H], fill=c + (255,))
    add_glow(im, W*0.14, H*0.60, 820, (80, 125, 255), 0.34, 2.1)
    add_glow(im, W*0.88, H*0.44, 760, AMBER, 0.46, 2.0)

    # слева: лента уходит в глубину за спину демона
    for k in range(8):
        q = k/7.0
        w = lerp(176, 52, q); h = lerp(330, 100, q)
        x = lerp(58, 470, q); y = lerp(742, 548, q)
        a = int(lerp(255, 95, q))
        add_glow(im, x, y, w*1.9, (105, 160, 255), 0.40*(1-q*0.5), 2.0)
        d.rounded_rectangle([x-w/2, y-h/2, x+w/2, y+h/2], radius=w*0.16,
                            fill=(138, 182, 255, a), outline=(10, 14, 24, 255),
                            width=max(3, int(9*(1-q*0.6))))
        for r in range(3):
            ry = y - h*0.26 + r*h*0.25
            d.rounded_rectangle([x-w*0.32, ry-h*0.055, x+w*0.32, ry+h*0.055],
                                radius=h*0.045, fill=(26, 38, 70, a))

    # справа: столик кафе под тёплым светом
    d.rounded_rectangle([W*0.69, H*0.845, W*1.03, H*0.90], radius=14,
                        fill=(104, 66, 38, 255), outline=(46, 29, 17, 255), width=6)
    add_glow(im, W*0.84, H*0.26, 300, (255, 206, 128), 0.5, 2.0)


def build():
    im, d = new_frame((10, 12, 20, 255))
    background(im, d)
    cam = Cam(1.0, W/2, H/2)

    # демон за левым плечом героя, ореол на максимуме
    h, hipy = put(head_y=648, hr=152)
    draw_demon(im, d, cam, (436, hipy), h, "stand", t=1.1, heat=1.5)

    # друг в тёплой части: тот, к кому герой так и не поднял глаз
    h, hipy = put(head_y=706, hr=134)
    draw_person(im, d, cam, (1688, hipy), h, "sit_chair", t=0.4, seed=0.7,
                mood="smile", look=-0.55, skin=(222, 204, 182),
                cloth=(92, 118, 102), lit=0.8)

    # герой крупно: выпученные глаза и синий отсвет телефона снизу
    h, hipy = put(head_y=606, hr=204)
    inf = draw_person(im, d, cam, (952, hipy), h, "sit_bed", t=0.0,
                      mood="wired", look=0.22, lit=1.0)
    hx, hy = inf["head"]; hr = inf["hr"]
    add_glow(im, hx, hy + hr*1.9, hr*2.3, (120, 170, 255), 0.55, 2.0)

    title(d, [("3 000", (255, 255, 255)), ("ИЛИ", (255, 206, 86)),
              ("1?", (255, 255, 255))], 168, 180)

    im.alpha_composite(vignette(), (0, 0))
    out = im.convert("RGB").resize((W, H), Image.LANCZOS)
    p = os.path.join(OUT, "thumb.jpg")
    out.save(p, quality=95)
    print("обложка готова:", p)


if __name__ == "__main__":
    build()
