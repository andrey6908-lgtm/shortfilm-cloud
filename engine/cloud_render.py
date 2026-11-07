# -*- coding: utf-8 -*-
"""Рендер ОТРЕЗКА кадров — один шард облачной матрицы.

    python3 cloud_render.py <первый кадр> <за последним> [папка]

Шрифты берутся из SHORTFILM_FONTS, число воркеров — из WORKERS.

ГОЧА 01.11 (лечение перенесено из camera-lab/engine/shard.py 06.11): на
раннерах встал python 3.14, где способ запуска по умолчанию — forkserver, а
он ЗАНОВО импортирует __main__ в каждом рабочем процессе. Без
`if __name__ == "__main__"` пул рождал пул и джоб падал за 20 с с
ConnectionResetError. Поэтому: и защита __main__, и явный fork — он к тому же
дешевле, кэши film.py (вигнетка, зерно) достаются дочерним процессам
готовыми.
"""
import os, sys, time, multiprocessing as mp

def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    a, b = int(sys.argv[1]), int(sys.argv[2])
    # Фильмов в движке больше одного: SHORTFILM_FILM выбирает раскадровку
    # (render3 — «ЛЕНТА vs ЖИЗНЬ», render_disc — «ДИСЦИПЛИНА»).
    import importlib
    render3 = importlib.import_module(os.environ.get("SHORTFILM_FILM", "render3"))
    if len(sys.argv) > 3:
        render3.OUT = sys.argv[3]
    os.makedirs(render3.OUT, exist_ok=True)

    n = int(os.environ.get("WORKERS", os.cpu_count() or 4))
    t0 = time.time()
    with mp.Pool(n) as p:
        for _ in p.imap_unordered(render3.frame, range(a, b), chunksize=8): pass
    dt = time.time() - t0
    print(f"кадры {a}..{b-1}: {b-a} шт, {dt:.1f} c, {dt/max(1,b-a):.2f} c/кадр, воркеров {n}")

if __name__ == "__main__":
    try: mp.set_start_method("fork")
    except RuntimeError: pass
    main()
