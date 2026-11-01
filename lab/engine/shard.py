# -*- coding: utf-8 -*-
"""Рендер всех кадров сцены: shard.py <модуль сцены>

ГОЧА 01.11: на раннерах встал python 3.14, где способ запуска по умолчанию —
forkserver, а он ЗАНОВО импортирует __main__ в каждом рабочем процессе. Без
`if __name__ == "__main__"` пул рождал пул и падал с ConnectionResetError.
Поэтому: и защита __main__, и явный fork — он к тому же дешевле, кэши film.py
(вигнетка, зерно) достаются дочерним процессам готовыми.
"""
import os, sys, time, importlib, multiprocessing as mp

def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sc = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "scene1")
    os.makedirs(sc.OUT, exist_ok=True)
    n = int(os.environ.get("WORKERS", os.cpu_count() or 2))
    total = int(round(sc.DUR*sc.FPS))
    t0 = time.time()
    with mp.Pool(n) as p:
        for _ in p.imap_unordered(sc.frame, range(total), chunksize=8): pass
    dt = time.time() - t0
    print(f"кадров {total}, {dt:.1f} c, {dt/total:.2f} c/кадр, воркеров {n}")

if __name__ == "__main__":
    try: mp.set_start_method("fork")
    except RuntimeError: pass
    main()
