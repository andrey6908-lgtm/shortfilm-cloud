# -*- coding: utf-8 -*-
"""Звуковая дорожка «ДИСЦИПЛИНЫ»: эффект на каждое действие.

Замер оригинала 07.11: у них 176 звуковых всплесков на 158 с — один звук
каждые 0,9 с. У нас было пять на весь ролик, отсюда «бу-бу-бу, заснуть
хочется». Здесь дорожка собирается по таблице событий сцен.

    python3 sound_disc.py <папка со звуками> <выход.wav>
"""
import sys, os, wave
import numpy as np

SR = 44100


def load(path):
    w = wave.open(path); n = w.getnframes()
    a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32)/32768
    if w.getnchannels() == 2: a = a.reshape(-1, 2).mean(1)
    if w.getframerate() != SR:                       # грубая, но честная подгонка
        idx = np.linspace(0, len(a)-1, int(len(a)*SR/w.getframerate()))
        a = np.interp(idx, np.arange(len(a)), a)
    return a


# событие: (время, звук, громкость, [растянуть до N секунд])
EVENTS = [
    # --- петля: будильник и «ещё пять минут» ---
    (5.0, "alarm", 0.85), (7.4, "alarm", 0.7), (9.2, "cloth", 0.5),
    (11.6, "btn", 0.9), (12.2, "cloth", 0.45),
    (16.2, "cloth", 0.4),
    # --- шёпот демона: шипение под каждую реплику ---
    (19.0, "hiss", 0.5), (19.8, "tick", 0.5),
    (26.0, "hiss", 0.5), (26.6, "tick", 0.45),
    (31.4, "cloth", 0.4), (33.4, "tick", 0.4), (35.4, "tick", 0.4),
    (37.4, "tick", 0.4), (38.0, "alarm", 0.5),
    # --- зеркало ---
    (39.6, "step", 0.5), (40.6, "step", 0.5), (41.6, "step", 0.5),
    (45.0, "hiss", 0.6), (45.6, "crack", 0.8),
    (47.2, "crack", 0.9), (47.9, "shatter", 1.0),
    # --- дно ---
    (50.4, "heart", 0.7), (53.0, "heart", 0.6), (56.0, "heart", 0.55),
    (59.0, "heart", 0.5),
    # --- решение ---
    (62.0, "alarm", 0.9), (64.4, "alarm", 0.8), (66.6, "btn", 1.0),
    (67.4, "cloth", 0.6), (69.0, "breath", 0.7),
    # --- работа: шаги бега ---
] + [(71.6 + i*0.30, "step", 0.52) for i in range(25)] + [
    (73.0, "hiss", 0.4),
    # отжимания: выдох на каждом подъёме
] + [(79.6 + i*1.05, "breath", 0.6) for i in range(6)] + [
    # гантели: металл
] + [(86.4 + i*0.98, "metal", 0.5) for i in range(5)] + [
    # груша: удары
] + [(92.4 + i*0.92, "punch", 0.95) for i in range(8)] + [
    (93.2, "hiss", 0.45),
    # дорожка: ровный гул и шаги
    (99.6, "tread", 0.5, 6.0),
] + [(100.0 + i*0.26, "step", 0.34) for i in range(20)] + [
    # гиря: свист и металл
] + [(106.2 + i*1.15, "whoosh2", 0.6) for i in range(5)] + \
  [(106.7 + i*1.15, "metal", 0.45) for i in range(5)] + [
    # отжимания второй раз
] + [(112.4 + i*0.82, "breath", 0.65) for i in range(6)] + [
    # лестница: шаги вверх
] + [(118.4 + i*0.46, "step", 0.6) for i in range(18)] + [
    (120.2, "hiss", 0.5),
    # вспышка и вершина
    (127.2, "whoosh2", 1.0), (129.0, "wind", 0.55, 14.0),
    (131.0, "breath", 0.5),
    # утро и титр
    (143.4, "cloth", 0.5), (145.0, "btn", 0.5),
    (149.4, "whoosh2", 0.7),
]


def build(fx_dir, out_path, dur=158.0):
    track = np.zeros(int(SR*dur) + SR, np.float32)
    cache = {}
    for ev in EVENTS:
        t0, name, vol = ev[0], ev[1], ev[2]
        stretch = ev[3] if len(ev) > 3 else None
        f = os.path.join(fx_dir, name + ".wav")
        if not os.path.exists(f): continue
        if name not in cache: cache[name] = load(f)
        a = cache[name]
        if stretch:                                   # зациклить до нужной длины
            need = int(SR*stretch)
            a = np.tile(a, int(need/len(a)) + 1)[:need]
            fade = int(SR*0.5)
            a[:fade] *= np.linspace(0, 1, fade); a[-fade:] *= np.linspace(1, 0, fade)
        s = int(SR*t0)
        e = min(len(track), s + len(a))
        track[s:e] += a[:e-s]*vol
    track = track[:int(SR*dur)]
    m = np.abs(track).max()
    if m > 0: track = track/m*0.82
    w = wave.open(out_path, "w"); w.setnchannels(1); w.setsampwidth(2)
    w.setframerate(SR); w.writeframes((track*32767).astype(np.int16).tobytes()); w.close()
    return len(EVENTS)


if __name__ == "__main__":
    n = build(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 158.0)
    print(f"дорожка собрана: {n} событий, один звук на {158.0/n:.2f} с")
