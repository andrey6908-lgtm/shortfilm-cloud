# -*- coding: utf-8 -*-
"""Рендер ОТРЕЗКА кадров — один шард облачной матрицы.

    python3 cloud_render.py <первый кадр> <за последним> [папка]

Шрифты берутся из SHORTFILM_FONTS, число воркеров — из WORKERS.
"""
import os, sys, time
from multiprocessing import Pool

a, b = int(sys.argv[1]), int(sys.argv[2])
import render3
if len(sys.argv) > 3:
    render3.OUT = sys.argv[3]
os.makedirs(render3.OUT, exist_ok=True)

n = int(os.environ.get("WORKERS", os.cpu_count() or 4))
t0 = time.time()
with Pool(n) as p:
    for _ in p.imap_unordered(render3.frame, range(a, b), chunksize=8): pass
dt = time.time() - t0
print(f"кадры {a}..{b-1}: {b-a} шт, {dt:.1f} c, {dt/max(1,b-a):.2f} c/кадр, воркеров {n}")
