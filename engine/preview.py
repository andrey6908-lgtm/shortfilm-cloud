# -*- coding: utf-8 -*-
"""Предпросмотр: рисует НАЗВАННЫЕ кадры и клеит из них контактный лист.

    python3 preview.py 480,1200,3600 [папка]

Нужен, чтобы смотреть правки глазами, НЕ трогая машину автора (его слово 22.10).
Один процесс, сотни мегабайт, секунды на кадр.
"""
import os, sys, time
from PIL import Image, ImageDraw, ImageFont
import importlib
render3 = importlib.import_module(os.environ.get("SHORTFILM_FILM", "render3"))
import film

nums = [int(x) for x in sys.argv[1].split(",") if x.strip()]
out = sys.argv[2] if len(sys.argv) > 2 else "preview"
os.makedirs(out, exist_ok=True)
render3.OUT = out

# ВРЕМЯ КАДРА ПЕЧАТАЕТСЯ ЧИСЛОМ (06.11). Иначе цену новой сцены назвать
# нечем: мерить на машине автора нельзя, а раннер до сих пор говорил только
# «готов». Среднее по кадрам — это и есть «сколько секунд машины стоит кадр».
spent = []
for n in nums:
    t0 = time.perf_counter()
    render3.frame(n)
    dt = time.perf_counter() - t0
    spent.append(dt)
    print(f"кадр {n} готов за {dt:.2f} с")
if spent:
    print("СРЕДНЕЕ НА КАДР: %.2f с (кадров %d, всего %.1f с)"
          % (sum(spent) / len(spent), len(spent), sum(spent)))

cols = 1 if len(nums) <= 3 else 2
rows = (len(nums) + cols - 1)//cols
tw = 960 if cols == 1 else 760
th = int(tw*film.H/film.W)
sheet = Image.new("RGB", (tw*cols, (th+26)*rows), (24, 24, 28))
d = ImageDraw.Draw(sheet)
try: f = ImageFont.truetype(os.environ.get("SHORTFILM_FONTS", ".") + "/calibri.ttf", 20)
except Exception: f = ImageFont.load_default()
for k, n in enumerate(nums):
    im = Image.open(f"{out}/f{n:05d}.jpg").resize((tw, th), Image.LANCZOS)
    x, y = (k % cols)*tw, (k//cols)*(th+26)
    sheet.paste(im, (x, y+26))
    d.text((x+8, y+4), f"кадр {n} — {n/film.FPS:.1f} с", font=f, fill=(230, 230, 230))
sheet.save(f"{out}/sheet.jpg", quality=93)
print("лист собран:", f"{out}/sheet.jpg")
