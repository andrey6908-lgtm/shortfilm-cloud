# -*- coding: utf-8 -*-
"""Экранный текст фильма, по языкам.

Язык выбирается переменной окружения SHORTFILM_LANG (ru | pl).
Весь текст, который виден на экране, лежит ТОЛЬКО здесь — в раскадровке
литералов больше нет. Чтобы добавить язык, допиши словарь и проверь, что
шрифты держат его диакритику (см. SKILL.md, раздел «ЯЗЫКОВЫЕ ВЕРСИИ»).
"""
import os

RU = {
    # заголовок
    "title_1":   "ЛЕНТА",
    "title_vs":  "vs",
    "title_2":   "ЖИЗНЬ.",
    # счётчик-HUD
    "hud_night":    "НОЧЬ",
    "hud_scrolled": "ПРОЛИСТАНО",
    "hud_known":    "ЗАПОМНИЛ",
    # повествование
    "n01a": "Он открыл ленту  ",
    "n01b": "  на минуту.  ",
    "n02":  "Раньше вечер заканчивался разговором.",
    "n03":  "Это было в одиннадцать вечера.",
    "n04a": "Лента не кончается. ",
    "n04b": "В этом вся идея.",
    "n05":  "Сначала он выбирал, что смотреть.",
    "n06":  "Потом выбирали за него.",
    "n07":  "Он перестал замечать, где кончается ночь.",
    "n08":  "Утро стало наказанием.",
    "n09":  "Он шёл мимо людей.",
    "n10":  "Друзья перестали спрашивать.",
    "n11":  "Ждать стало нечего.",
    "n12":  "Он выключил телефон.",
    "n13":  "через двадцать минут…",
    "n14":  "Он включил его снова.",
    "n15":  "Потом он написал первым.",
    # финал
    "fin_1": "Он пролистал три тысячи.",
    "fin_2": "Он запомнил один день.",
    "out_1": "Положи телефон.",
    "out_2": "Или ещё один свайп.",
    # календарь на стене спальни (три буквы)
    "cal_month": "ОКТ",
    # обложка YouTube
    "th_num":    "3 000",
    "th_or":     "ИЛИ",
    "th_one":    "1?",
    "th_nights": "3 000 НОЧЕЙ",
    "th_day":    "1 ДЕНЬ?",
    "th_short":  "3 000?",
    "th_or2":    "ИЛИ",
    "th_hook":   "ЕЩЁ ОДИН?",
    # переписка на экране телефона
    "chat_name": "Макс",
    "chat_1":    "встретимся в субботу?",
    "chat_2":    "не могу",
    "chat_3":    "ты норм?",
    # шёпот демона (строчными — это его почерк)
    "w1": "ещё один.",
    "w2": "кто вообще спит в твоём возрасте?",
    "w3": "видишь? тебе никто и не нужен.",
    "w4": "остались только мы с тобой.",
    "w5": "я же говорил.",
}

PL = {
    "title_1":   "SCROLL",
    "title_vs":  "vs",
    "title_2":   "ŻYCIE.",

    "hud_night":    "NOC",
    "hud_scrolled": "PRZEWINIĘTE",
    "hud_known":    "ZAPAMIĘTANE",

    "n01a": "Otworzył kanał  ",
    "n01b": "  na minutę.  ",
    "n02":  "Kiedyś wieczór kończył się rozmową.",
    "n03":  "To było o jedenastej wieczorem.",
    "n04a": "Scroll się nie kończy. ",
    "n04b": "O to właśnie chodzi.",
    "n05":  "Najpierw sam wybierał, co ogląda.",
    "n06":  "Potem wybierano za niego.",
    "n07":  "Przestał zauważać, gdzie kończy się noc.",
    "n08":  "Poranek stał się karą.",
    "n09":  "Mijał ludzi.",
    "n10":  "Znajomi przestali pytać.",
    "n11":  "Nie było już na co czekać.",
    "n12":  "Wyłączył telefon.",
    "n13":  "dwadzieścia minut później…",
    "n14":  "Włączył go z powrotem.",
    "n15":  "Potem odezwał się pierwszy.",

    "fin_1": "Przewinął trzy tysiące.",
    "fin_2": "Zapamiętał jeden dzień.",
    "out_1": "Odłóż telefon.",
    "out_2": "Albo jeszcze jeden scroll.",

    "cal_month": "PAŹ",

    "th_num":    "3 000",
    "th_or":     "CZY",
    "th_one":    "1?",
    "th_nights": "3 000 NOCY",
    "th_day":    "1 DZIEŃ?",
    "th_short":  "3 000?",
    "th_or2":    "CZY",
    "th_hook":   "JESZCZE JEDEN?",

    "chat_name": "Marek",
    "chat_1":    "widzimy się w sobotę?",
    "chat_2":    "nie dam rady",
    "chat_3":    "wszystko ok?",

    "w1": "jeszcze jeden.",
    "w2": "kto w twoim wieku w ogóle śpi?",
    "w3": "widzisz? nikt ci nie jest potrzebny.",
    "w4": "zostaliśmy tylko ty i ja.",
    "w5": "a nie mówiłem?",
}

# Шрифт почерка демона. По умолчанию Segoe Script, но в нём НЕТ румынской
# буквы ț (проверено разбором cmap 26.10: ș есть, ț нет). Для румынского —
# Segoe Print: тоже рукописный и держит весь набор. Проверять КАЖДЫЙ новый
# язык разбором cmap, а не на глаз: отсутствующая буква рисуется пустым
# квадратом и в логе рендера ничем себя не выдаёт.
HAND_FONT = {"ro": "segoepr.ttf"}

TABLES = {"ru": RU, "pl": PL}
LANG = os.environ.get("SHORTFILM_LANG", "ru").lower()
if LANG not in TABLES:
    raise SystemExit(f"неизвестный язык SHORTFILM_LANG={LANG}, есть: {', '.join(TABLES)}")
L = TABLES[LANG]

# проверка полноты: польская таблица должна покрывать русскую целиком
_missing = [k for k in RU if k not in L]
if _missing:
    raise SystemExit(f"в таблице '{LANG}' не хватает строк: {', '.join(_missing)}")


def hand_font(default="segoesc.ttf"):
    """Файл шрифта для почерка демона в текущем языке."""
    return HAND_FONT.get(LANG, default)
