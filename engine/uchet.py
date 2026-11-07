# -*- coding: utf-8 -*-
"""Бухгалтерия короткометражек: что сделано, на каких языках, чем отличается.

Книга собирается ИЗ ФАКТОВ НА ДИСКЕ (длительность берётся ffprobe, размер и
дата — у файла), поэтому её можно пересобрать в любой момент и она не врёт:
    python3 uchet.py
"""
import os, subprocess, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = "/mnt/d/YouTube/ОБРАЗЕЦ DAY ONE"
OUT  = "/mnt/d/YouTube/УЧЁТ-КОРОТКОМЕТРАЖЕК.xlsx"

# тема -> (папка, язык, как отличается эта версия)
ROWS = [
    ("ЛЕНТА vs ЖИЗНЬ", "РУССКИЙ",     "русский",     "оригинал, без коррекции",       "нет",  "1,00",  "нет",    "Calibri + Bahnschrift"),
    ("ЛЕНТА vs ЖИЗНЬ", "ПОЛЬСКИЙ",    "польский",    "холодная синь",                 "да",   "1,03",  "drift",  "Calibri + Bahnschrift"),
    ("ЛЕНТА vs ЖИЗНЬ", "ФРАНЦУЗСКИЙ", "французский", "тёплая сепия",                  "да",   "0,97",  "breath", "Candara + Franklin"),
    ("ЛЕНТА vs ЖИЗНЬ", "ИСПАНСКИЙ",   "испанский",   "янтарь, контраст выше",         "нет",  "1,035", "push",   "Corbel + Trebuchet"),
    ("ЛЕНТА vs ЖИЗНЬ", "ИТАЛЬЯНСКИЙ", "итальянский", "оливковая ночь",                "да",   "1,02",  "float",  "Trebuchet + Verdana"),
    ("ЛЕНТА vs ЖИЗНЬ", "РУМЫНСКИЙ",   "румынский",   "холодный фиолет",               "нет",  "0,98",  "sway",   "Georgia + Tahoma"),
    ("ЛЕНТА vs ЖИЗНЬ", "АРАБСКИЙ",    "арабский",    "песок и медь",                  "да",   "1,05",  "glide",  "Segoe UI + Tahoma"),
    ("ДИСЦИПЛИНА",     "ДИСЦИПЛИНА",  "русский",     "оригинал, без коррекции",       "нет",  "1,00",  "нет",    "Calibri + Bahnschrift"),
]

LANGS = ["русский", "польский", "французский", "испанский", "итальянский",
         "румынский", "арабский"]

HEAD_BG  = PatternFill("solid", fgColor="1F3864")
HEAD_FG  = Font(color="FFFFFF", bold=True, size=11)
OK_BG    = PatternFill("solid", fgColor="C6EFCE")
NO_BG    = PatternFill("solid", fgColor="F2F2F2")
WAIT_BG  = PatternFill("solid", fgColor="FFF2CC")
TITLE_FT = Font(bold=True, size=14, color="1F3864")
THIN     = Border(*[Side("thin", color="BFBFBF")]*4)


def probe(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                              "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True, timeout=60).stdout.strip()
        return float(out)
    except Exception:
        return 0.0


def mmss(sec):
    sec = int(round(sec))
    return f"{sec//60}:{sec%60:02d}"


def scan():
    data = []
    for tema, folder, lang, tone, mirror, speed, cam, font in ROWS:
        d = os.path.join(BASE, folder)
        if not os.path.isdir(d): continue
        vids = sorted(f for f in os.listdir(d) if f.endswith(".mp4"))
        if not vids:
            data.append(dict(tema=tema, folder=folder, lang=lang, file="", dur=0, size=0,
                             date="", obl=0, pack=0, tone=tone, mirror=mirror,
                             speed=speed, cam=cam, font=font)); continue
        last = vids[-1]                                   # в работу идёт свежая версия
        p = os.path.join(d, last)
        st = os.stat(p)
        obl = len([f for f in os.listdir(d) if f.lower().endswith(".jpg") and "oblozh" in f.lower()])
        pack = len([f for f in os.listdir(d) if f.endswith(".txt")])
        data.append(dict(tema=tema, folder=folder, lang=lang, file=last,
                         dur=probe(p), size=st.st_size, versions=len(vids),
                         date=datetime.date.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y"),
                         obl=obl, pack=pack, tone=tone, mirror=mirror,
                         speed=speed, cam=cam, font=font))
    return data


def style_head(ws, row=1, upto=None):
    for c in ws[row]:
        if upto and c.column > upto: break
        c.fill, c.font = HEAD_BG, HEAD_FG
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = THIN


def autosize(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def build():
    data = scan()
    wb = Workbook()

    # ------------------------------------------------------------ СВОДКА
    ws = wb.active; ws.title = "СВОДКА"
    ws["A1"] = "КОРОТКОМЕТРАЖКИ: ЧТО СДЕЛАНО"; ws["A1"].font = TITLE_FT
    ws["A2"] = f"Собрано из файлов на диске {datetime.date.today().strftime('%d.%m.%Y')}. " \
               f"Папка: {BASE}"
    ws["A2"].font = Font(italic=True, size=10, color="595959")

    ws.append([]); ws.append(["ТЕМА"] + [l.upper() for l in LANGS] + ["ВСЕГО ВЕРСИЙ"])
    style_head(ws, 4)
    temas = []
    for t in [r[0] for r in ROWS]:
        if t not in temas: temas.append(t)
    for tema in temas:
        row = [tema]
        cnt = 0
        for lang in LANGS:
            got = [d for d in data if d["tema"] == tema and d["lang"] == lang and d["file"]]
            if got:
                row.append(f'готов · {mmss(got[0]["dur"])}'); cnt += 1
            else:
                row.append("—")
        row.append(cnt)
        ws.append(row)
    for r in ws.iter_rows(min_row=5, max_row=ws.max_row, max_col=len(LANGS)+2):
        for c in r:
            c.border = THIN
            c.alignment = Alignment(horizontal="center", vertical="center")
            if isinstance(c.value, str) and c.value.startswith("готов"): c.fill = OK_BG
            elif c.value == "—": c.fill = NO_BG
        r[0].alignment = Alignment(horizontal="left", vertical="center")
        r[0].font = Font(bold=True)
    autosize(ws, [22] + [15]*len(LANGS) + [14])
    ws.freeze_panes = "B5"

    n = ws.max_row + 2
    ws.cell(n, 1, "ИТОГО").font = Font(bold=True, size=12)
    ws.cell(n, 2, f"{len([d for d in data if d['file']])} готовых роликов, "
                  f"{len(temas)} темы, {len(set(d['lang'] for d in data if d['file']))} языков")

    # ------------------------------------------------------------ РОЛИКИ
    ws = wb.create_sheet("РОЛИКИ")
    cols = ["ТЕМА", "ЯЗЫК", "ФАЙЛ", "ДЛИТЕЛЬНОСТЬ", "РАЗМЕР, МБ", "ВЕРСИЙ",
            "ДАТА", "ОБЛОЖЕК", "УПАКОВКА", "ГАММА", "ЗЕРКАЛО", "ТЕМП",
            "КАМЕРА", "ШРИФТЫ", "ПАПКА"]
    ws.append(cols); style_head(ws)
    for d in data:
        if not d["file"]: continue
        ws.append([d["tema"], d["lang"], d["file"], mmss(d["dur"]),
                   round(d["size"]/1048576, 1), d.get("versions", 1), d["date"],
                   d["obl"], "есть" if d["pack"] else "нет", d["tone"],
                   d["mirror"], d["speed"], d["cam"], d["font"],
                   f'{BASE}\\{d["folder"]}'.replace("/mnt/d", "D:").replace("/", "\\")])
    for r in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(cols)):
        for c in r:
            c.border = THIN
            if c.column in (4, 5, 6, 7, 8, 11, 12): c.alignment = Alignment(horizontal="center")
        if r[8].value == "нет": r[8].fill = WAIT_BG
        if r[7].value == 0: r[7].fill = WAIT_BG
    autosize(ws, [20, 13, 34, 14, 12, 9, 12, 10, 11, 22, 10, 8, 10, 24, 46])
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"

    # ---------------------------------------------------------- ИСТОЧНИК
    ws = wb.create_sheet("ОТКУДА ТЕМЫ")
    ws["A1"] = "ЦИФРЫ КОНКУРЕНТОВ — ПО НИМ ВЫБИРАЕМ, ЧТО ДЕЛАТЬ"; ws["A1"].font = TITLE_FT
    ws["A2"] = "Живые выдачи каналов, замер 22.10 и 07.11.2026. Берём то, что уже залетело."
    ws["A2"].font = Font(italic=True, size=10, color="595959")
    ws.append([]); ws.append(["КАНАЛ", "РОЛИК", "ТЕМА ПО-РУССКИ", "ПРОСМОТРОВ", "ДЛИНА", "У НАС"])
    style_head(ws, 4)
    src = [
        ("Day One Films",  "DISCIPLINE",                "дисциплина против лени",   5910000, "2:39", "СДЕЛАНО 07.11"),
        ("Monk Mode Films","LUST VS LOVE",              "похоть против любви",      1500000, "2:51", "—"),
        ("Day One Films",  "Lust Is Killing You",       "порно убивает тебя",        537000, "3:21", "—"),
        ("Monk Mode Films","LUST PART 2",               "похоть, часть 2",           431000, "3:32", "—"),
        ("Day One Films",  "DOPAMINE",                  "дофамин, короткие видео",   434000, "2:41", "—"),
        ("Day One Films",  "Motivation Will Fail You",  "мотивация подведёт",        278000, "3:29", "—"),
        ("Monk Mode Films","LUST",                      "похоть",                    258000, "3:20", "—"),
        ("Day One Films",  "Stop Overthinking",         "хватит себя накручивать",   127000, "4:07", "—"),
        ("Day One Films",  "ROOTS",                     "корни, откуда ты",          120000, "4:01", "—"),
        ("Monk Mode Films","MONK MODE",                 "режим монаха",               52000, "3:22", "—"),
        ("наш",            "ЛЕНТА vs ЖИЗНЬ",            "лента вместо жизни",             0, "3:06", "СДЕЛАНО, 7 языков"),
    ]
    for r in src: ws.append(list(r))
    for r in ws.iter_rows(min_row=5, max_row=ws.max_row, max_col=6):
        for c in r: c.border = THIN
        r[3].number_format = "# ##0"
        r[3].alignment = Alignment(horizontal="right")
        r[4].alignment = Alignment(horizontal="center")
        if str(r[5].value).startswith("СДЕЛАНО"): r[5].fill = OK_BG
    autosize(ws, [20, 30, 30, 15, 10, 22])
    ws.freeze_panes = "A5"

    # --------------------------------------------------------- ЧТО ДАЛЬШЕ
    ws = wb.create_sheet("ЧТО ДАЛЬШЕ")
    ws["A1"] = "ОТКРЫТЫЕ ХВОСТЫ"; ws["A1"].font = TITLE_FT
    ws.append([]); ws.append(["ЧТО", "ПОДРОБНО", "ЧЬЁ РЕШЕНИЕ"])
    style_head(ws, 3)
    rows = [
        ("«ДИСЦИПЛИНА» на шесть языков",
         "Движок уже умеет: нужны 24 строки текста на язык в lang_disc.py, "
         "остальное (гамма, зеркало, темп, камера, шрифты) берётся готовым.", "твоё — говорить ли делать"),
        ("Обложка «ДИСЦИПЛИНЫ»",
         "Не делал: обложки ты забрал себе 26.10. Схема конкурента разобрана — "
         "крупное лицо, четыре знака текста, подсветка снизу, три зоны.", "твоё"),
        ("Залив на каналы",
         "Семь роликов «ЛЕНТА vs ЖИЗНЬ» и «ДИСЦИПЛИНА» лежат готовые, "
         "с названиями, описаниями и тегами. Ни один не залит.", "твоё"),
        ("Следующая тема из списка",
         "По цифрам следующая — похоть/LUST (1,5 млн у клона) или ДОФАМИН "
         "(434 тыс.). Обе свободны в русском сегменте.", "твоё"),
        ("Фигура героя корявая",
         "Его слово 07.11: рука не так, ноги не так, нелепый человечек. "
         "Претензия к анатомии — пропорции и посадка рук и ног, касается "
         "обоих фильмов. Сказано фиксировать и не трогать.", "твоё — когда делать"),
        ("Прототип стиля Ifverse",
         "Доведён до круга 5 (фон, посадка, цвет). Ждёт твоего глаза: "
         "РАЗБОР IFVERSE\\ИТОГ-КРУГ-5.jpg", "твоё"),
    ]
    for r in rows: ws.append(list(r))
    for r in ws.iter_rows(min_row=4, max_row=ws.max_row, max_col=3):
        for c in r:
            c.border = THIN; c.alignment = Alignment(vertical="top", wrap_text=True)
        r[0].font = Font(bold=True)
    autosize(ws, [34, 74, 24])
    ws.freeze_panes = "A4"

    wb.save(OUT)
    return OUT, len([d for d in data if d["file"]])


if __name__ == "__main__":
    path, n = build()
    print(f"готово: {path} — роликов в учёте: {n}")
