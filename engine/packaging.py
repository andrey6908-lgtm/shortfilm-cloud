# -*- coding: utf-8 -*-
"""Название, описание, главы и теги языковой версии — одним файлом в её папку.

Главы берутся из той же таблицы lang.py, что и экранный текст (двух строк в
русском оригинале там нет — они заданы здесь), а их таймкоды тянутся темпом
версии: у каждой версии свой --speed, и готовые тайминги русского описания к
ней не подходят.
"""
import os, sys

# времена глав русского оригинала (186 с), в секундах
CHAPTERS = [(0, "n01"), (18, "n03"), (44, "demon"), (70, "n07"), (82, "n08"),
            (106, "n10"), (132, "n12"), (142, "n14"), (149, "n15"), (174, "fin_2")]

# то, чего нет в экранном тексте: строка про приход демона и хвост описания
EXTRA = {
    "ru": dict(demon="Он пришёл не один",
               title="ЛЕНТА vs ЖИЗНЬ | Анимационная короткометражка",
               lead="ЛЕНТА vs ЖИЗНЬ — короткометражка о ночи, которая началась «на минуту»,\nи о человеке, который разучился поднимать глаза.",
               hook="Лента отдаёт тебе всех. Жизнь просит одного.",
               made="Каждый кадр этого фильма нарисован с нуля. Ни одного стокового изображения.",
               tags="лента вместо жизни, залип в телефоне, цифровая зависимость, скроллинг, экранное время, самоконтроль, анимационная короткометражка, короткометражка без слов"),
    "pl": dict(demon="Nie przyszedł sam",
               title="SCROLL vs ŻYCIE | Krótkometrażowy film animowany",
               lead="SCROLL vs ŻYCIE — film krótkometrażowy o nocy, która zaczęła się\n„na minutę”, i o człowieku, który oduczył się podnosić wzrok.",
               hook="Scroll daje ci wszystkich. Życie prosi o jednego.",
               made="Każdy kadr narysowany od zera. Ani jednego zdjęcia stockowego.",
               tags="uzależnienie od telefonu, scrollowanie, czas przed ekranem, samokontrola, film animowany, krótki metraż, bez słów"),
    "fr": dict(demon="Il n'est pas venu seul",
               title="LE FIL vs LA VIE | Court-métrage d'animation",
               lead="LE FIL vs LA VIE — un court-métrage sur une nuit commencée\n« pour une minute », et sur un homme qui a désappris à lever les yeux.",
               hook="Le fil te donne tout le monde. La vie n'en demande qu'un.",
               made="Chaque image est dessinée de zéro. Aucune banque d'images.",
               tags="addiction au téléphone, scroll, temps d'écran, discipline, court-métrage animé, film sans paroles, animation"),
    "es": dict(demon="No vino solo",
               title="EL FEED vs LA VIDA | Cortometraje de animación",
               lead="EL FEED vs LA VIDA — un cortometraje sobre una noche que empezó\n«un minuto», y sobre un hombre que olvidó levantar la mirada.",
               hook="El feed te da a todos. La vida pide uno solo.",
               made="Cada fotograma dibujado desde cero. Ni una sola imagen de stock.",
               tags="adicción al móvil, scroll infinito, tiempo de pantalla, autocontrol, cortometraje animado, animación, sin diálogos"),
    "it": dict(demon="Non è arrivato solo",
               title="IL FEED vs LA VITA | Cortometraggio d'animazione",
               lead="IL FEED vs LA VITA — un cortometraggio su una notte iniziata\n«per un minuto», e su un uomo che ha disimparato ad alzare lo sguardo.",
               hook="Il feed ti dà tutti. La vita ne chiede uno.",
               made="Ogni fotogramma disegnato da zero. Nessuna immagine di stock.",
               tags="dipendenza da smartphone, scroll, tempo davanti allo schermo, autocontrollo, cortometraggio animato, animazione, senza parole"),
    "ro": dict(demon="N-a venit singur",
               title="FEEDUL vs VIAȚA | Scurtmetraj de animație",
               lead="FEEDUL vs VIAȚA — un scurtmetraj despre o noapte începută\n„pentru un minut” și despre un om care a uitat să ridice privirea.",
               hook="Feedul ți-i dă pe toți. Viața cere unul singur.",
               made="Fiecare cadru desenat de la zero. Nicio imagine de stoc.",
               tags="dependență de telefon, scroll, timp în fața ecranului, autocontrol, scurtmetraj de animație, animație, fără cuvinte"),
    "ar": dict(demon="لم يأتِ وحده",
               title="التمرير مقابل الحياة | فيلم رسوم متحركة قصير",
               lead="التمرير مقابل الحياة — فيلم قصير عن ليلة بدأت «لدقيقة واحدة»،\nوعن رجل نسي أن يرفع عينيه.",
               hook="التمرير يمنحك الجميع. الحياة تطلب واحداً.",
               made="كل لقطة مرسومة من الصفر. ولا صورة واحدة جاهزة.",
               tags="إدمان الهاتف, التمرير اللانهائي, وقت الشاشة, ضبط النفس, فيلم رسوم متحركة قصير, رسوم متحركة, بلا كلام"),
}


def build(lang, speed, out_path, video_name, duration):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ["SHORTFILM_LANG"] = lang
    sys.modules.pop("lang", None)
    import lang as L
    e, t = EXTRA[lang], L.L

    def chapter(key):
        if key == "demon": return e["demon"]
        if key == "n01":   return (t["n01a"] + t["n01b"]).strip()
        return t[key].rstrip(".").strip()

    lines = []
    for sec, key in CHAPTERS:
        s = int(sec * speed)
        lines.append(f"{s // 60}:{s % 60:02d} {chapter(key)}")

    body = f"""НАЗВАНИЕ И ОПИСАНИЕ — версия «{lang.upper()}»
Файл: {video_name}   ({int(duration) // 60}:{int(duration) % 60:02d})
Темп версии: {speed} — таймкоды глав пересчитаны под него.

НАЗВАНИЕ (одной строкой):
{e['title']}

ОПИСАНИЕ (целиком):
----------------------------------------------------------------
{e['lead']}

{e['hook']}

""" + "\n".join(lines) + f"""

{e['made']}
----------------------------------------------------------------

ТЕГИ (через запятую):
----------------------------------------------------------------
{e['tags']}
----------------------------------------------------------------
"""
    with open(out_path, "w", encoding="utf-8-sig") as f:
        f.write(body)
    return out_path


if __name__ == "__main__":
    lang, speed, out, name, dur = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4], float(sys.argv[5])
    print(build(lang, speed, out, name, dur))
