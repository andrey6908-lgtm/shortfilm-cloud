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


def background(im, d):
    # холодная половина слева, тёплая справа — сюжет читается до текста
    for i in range(72):
        k = i/71.0
        x0, x1 = W*k, W*(k+1/71.0)+2
        c = mix((13, 17, 28), (40, 24, 14), clamp((k-0.46)/0.34))
        d.rectangle([x0, 0, x1, H], fill=c + (255,))
    add_glow(im, W*0.17, H*0.52, 760, (90, 130, 255), 0.30, 2.1)
    add_glow(im, W*0.86, H*0.46, 720, AMBER, 0.42, 2.0)

    # слева: вереница лент, уходящая в глубину
    for k in range(9):
        q = k/8.0
        w = lerp(150, 36, q); h = lerp(300, 74, q)
        x = lerp(60, 520, q); y = lerp(760, 560, q)
        a = int(lerp(230, 70, q))
        d.rounded_rectangle([x-w/2, y-h/2, x+w/2, y+h/2], radius=w*0.18,
                            fill=(120, 170, 255, a), outline=(16, 20, 32, 255),
                            width=max(2, int(8*(1-q))))
        for r in range(3):
            ry = y - h*0.28 + r*h*0.26
            d.rounded_rectangle([x-w*0.33, ry-h*0.06, x+w*0.33, ry+h*0.06],
                                radius=h*0.05, fill=(28, 40, 72, a))
        add_glow(im, x, y, w*1.7, (110, 160, 255), 0.26*(1-q*0.6), 2.0)

    # справа: столик и чашка — тёплая половина
    d.rounded_rectangle([W*0.72, H*0.74, W*1.02, H*0.80], radius=14,
                        fill=(92, 58, 34, 255), outline=(44, 28, 16, 255), width=5)


def build():
    im, d = new_frame((10, 12, 20, 255))
    background(im, d)
    cam = Cam(1.0, W/2, H/2)

    # демон — за плечом героя, в холодной части
    draw_demon(im, d, cam, (470, 1216), 980, "stand", t=1.1, heat=1.45)

    # друг в тёплой части: тот, к кому герой так и не поднял глаза
    draw_person(im, d, cam, (1706, 1236), 880, "sit_chair", t=0.4, seed=0.7,
                mood="smile", look=-0.5, skin=(222, 204, 182),
                cloth=(92, 118, 102), lit=0.75)

    # герой крупно: выпученные глаза, синий отсвет телефона снизу
    inf = draw_person(im, d, cam, (1010, 1560), 1240, "sit_bed", t=0.0,
                      mood="wired", look=0.25, lit=0.95)
    hx, hy = inf["head"]
    hr = inf["hr"]
    add_glow(im, hx, hy + hr*1.9, hr*2.2, (120, 170, 255), 0.5, 2.0)

    big_text(d, "3 000", W*0.33, 168, 168)
    big_text(d, "ИЛИ", W*0.545, 168, 118, fill=(255, 210, 90))
    big_text(d, "1?", W*0.70, 168, 168)

    im.alpha_composite(vignette(), (0, 0))
    out = im.convert("RGB").resize((W, H), Image.LANCZOS)
    p = os.path.join(OUT, "thumb.jpg")
    out.save(p, quality=95)
    print("обложка готова:", p)


if __name__ == "__main__":
    build()
