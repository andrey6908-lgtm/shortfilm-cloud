# -*- coding: utf-8 -*-
"""Рендер всех кадров сцены: shard.py <модуль сцены>"""
import os, sys, time, importlib
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sc = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "scene1")
os.makedirs(sc.OUT, exist_ok=True)
n = int(os.environ.get("WORKERS", os.cpu_count() or 2))
total = int(round(sc.DUR*sc.FPS))
t0 = time.time()
with Pool(n) as p:
    for _ in p.imap_unordered(sc.frame, range(total), chunksize=8): pass
dt = time.time() - t0
print(f"кадров {total}, {dt:.1f} c, {dt/total:.2f} c/кадр, воркеров {n}")
