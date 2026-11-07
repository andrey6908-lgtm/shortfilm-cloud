# -*- coding: utf-8 -*-
"""Экранный текст фильма, по языкам.

Язык выбирается переменной окружения SHORTFILM_LANG
(ru | pl | fr | es | it | ro | ar).
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

FR = {
    "title_1":   "LE FIL",
    "title_vs":  "vs",
    "title_2":   "LA VIE.",

    "hud_night":    "NUIT",
    "hud_scrolled": "DÉFILÉ",
    "hud_known":    "RETENU",

    "n01a": "Il a ouvert le fil  ",
    "n01b": "  une minute.  ",
    "n02":  "Avant, la soirée finissait par une conversation.",
    "n03":  "Il était vingt-trois heures.",
    "n04a": "Le fil ne finit jamais. ",
    "n04b": "C'est tout le principe.",
    "n05":  "D'abord, il choisissait quoi regarder.",
    "n06":  "Ensuite, on a choisi pour lui.",
    "n07":  "Il ne voyait plus où la nuit s'arrêtait.",
    "n08":  "Le matin est devenu une punition.",
    "n09":  "Il passait à côté des gens.",
    "n10":  "Ses amis ont cessé de demander.",
    "n11":  "Il n'y avait plus rien à attendre.",
    "n12":  "Il a éteint son téléphone.",
    "n13":  "vingt minutes plus tard…",
    "n14":  "Il l'a rallumé.",
    "n15":  "Puis il a écrit le premier.",

    "fin_1": "Il a fait défiler trois mille.",
    "fin_2": "Il se souvient d'un jour.",
    "out_1": "Pose ton téléphone.",
    "out_2": "Ou encore un swipe.",

    "cal_month": "OCT",

    "th_num":    "3 000",
    "th_or":     "OU",
    "th_one":    "1?",
    "th_nights": "3 000 NUITS",
    "th_day":    "1 JOUR?",
    "th_short":  "3 000?",
    "th_or2":    "OU",
    "th_hook":   "ENCORE UN?",

    "chat_name": "Max",
    "chat_1":    "on se voit samedi?",
    "chat_2":    "je peux pas",
    "chat_3":    "ça va?",

    "w1": "encore un.",
    "w2": "qui dort encore à ton âge?",
    "w3": "tu vois? tu n'as besoin de personne.",
    "w4": "il ne reste que toi et moi.",
    "w5": "je te l'avais dit.",
}

ES = {
    "title_1":   "EL FEED",
    "title_vs":  "vs",
    "title_2":   "LA VIDA.",

    "hud_night":    "NOCHE",
    "hud_scrolled": "DESLIZADO",
    "hud_known":    "RECORDADO",

    "n01a": "Abrió el feed  ",
    "n01b": "  un minuto.  ",
    "n02":  "Antes la noche terminaba con una charla.",
    "n03":  "Eran las once de la noche.",
    "n04a": "El feed no se acaba. ",
    "n04b": "De eso se trata.",
    "n05":  "Al principio elegía qué mirar.",
    "n06":  "Después eligieron por él.",
    "n07":  "Dejó de notar dónde acababa la noche.",
    "n08":  "La mañana se volvió un castigo.",
    "n09":  "Pasaba junto a la gente.",
    "n10":  "Los amigos dejaron de preguntar.",
    "n11":  "Ya no había nada que esperar.",
    "n12":  "Apagó el teléfono.",
    "n13":  "veinte minutos después…",
    "n14":  "Lo volvió a encender.",
    "n15":  "Después escribió él primero.",

    "fin_1": "Deslizó tres mil.",
    "fin_2": "Recordó un solo día.",
    "out_1": "Deja el teléfono.",
    "out_2": "O un swipe más.",

    "cal_month": "OCT",

    "th_num":    "3 000",
    "th_or":     "O",
    "th_one":    "¿1?",
    "th_nights": "3 000 NOCHES",
    "th_day":    "¿1 DÍA?",
    "th_short":  "¿3 000?",
    "th_or2":    "O",
    "th_hook":   "¿UNO MÁS?",

    "chat_name": "Max",
    "chat_1":    "¿nos vemos el sábado?",
    "chat_2":    "no puedo",
    "chat_3":    "¿estás bien?",

    "w1": "uno más.",
    "w2": "¿quién duerme a tu edad?",
    "w3": "¿ves? no necesitas a nadie.",
    "w4": "solo quedamos tú y yo.",
    "w5": "te lo dije.",
}

IT = {
    "title_1":   "IL FEED",
    "title_vs":  "vs",
    "title_2":   "LA VITA.",

    "hud_night":    "NOTTE",
    "hud_scrolled": "SCORSO",
    "hud_known":    "RICORDATO",

    "n01a": "Ha aperto il feed  ",
    "n01b": "  per un minuto.  ",
    "n02":  "Prima la sera finiva con una chiacchierata.",
    "n03":  "Erano le undici di sera.",
    "n04a": "Il feed non finisce. ",
    "n04b": "È tutto qui il punto.",
    "n05":  "All'inizio sceglieva cosa guardare.",
    "n06":  "Poi hanno scelto per lui.",
    "n07":  "Ha smesso di accorgersi dove finiva la notte.",
    "n08":  "La mattina è diventata una punizione.",
    "n09":  "Passava accanto alle persone.",
    "n10":  "Gli amici hanno smesso di chiedere.",
    "n11":  "Non c'era più niente da aspettare.",
    "n12":  "Ha spento il telefono.",
    "n13":  "venti minuti dopo…",
    "n14":  "L'ha riacceso.",
    "n15":  "Poi ha scritto per primo.",

    "fin_1": "Ha scorso tremila.",
    "fin_2": "Ha ricordato un giorno.",
    "out_1": "Posa il telefono.",
    "out_2": "O un altro swipe.",

    "cal_month": "OTT",

    "th_num":    "3 000",
    "th_or":     "O",
    "th_one":    "1?",
    "th_nights": "3 000 NOTTI",
    "th_day":    "1 GIORNO?",
    "th_short":  "3 000?",
    "th_or2":    "O",
    "th_hook":   "UN ALTRO?",

    "chat_name": "Max",
    "chat_1":    "ci vediamo sabato?",
    "chat_2":    "non posso",
    "chat_3":    "tutto ok?",

    "w1": "ancora uno.",
    "w2": "chi dorme alla tua età?",
    "w3": "vedi? non ti serve nessuno.",
    "w4": "siamo rimasti solo io e te.",
    "w5": "te l'avevo detto.",
}

RO = {
    "title_1":   "FEEDUL",
    "title_vs":  "vs",
    "title_2":   "VIAȚA.",

    "hud_night":    "NOAPTE",
    "hud_scrolled": "DERULAT",
    "hud_known":    "REȚINUT",

    "n01a": "A deschis feedul  ",
    "n01b": "  un minut.  ",
    "n02":  "Înainte, seara se termina cu o discuție.",
    "n03":  "Era unsprezece seara.",
    "n04a": "Feedul nu se termină. ",
    "n04b": "Asta e toată ideea.",
    "n05":  "La început alegea ce să vadă.",
    "n06":  "Apoi au ales alții pentru el.",
    "n07":  "A încetat să observe unde se termină noaptea.",
    "n08":  "Dimineața a devenit o pedeapsă.",
    "n09":  "Trecea pe lângă oameni.",
    "n10":  "Prietenii au încetat să mai întrebe.",
    "n11":  "Nu mai era nimic de așteptat.",
    "n12":  "A închis telefonul.",
    "n13":  "douăzeci de minute mai târziu…",
    "n14":  "L-a pornit din nou.",
    "n15":  "Apoi a scris el primul.",

    "fin_1": "A derulat trei mii.",
    "fin_2": "Și-a amintit o zi.",
    "out_1": "Lasă telefonul.",
    "out_2": "Sau încă un swipe.",

    "cal_month": "OCT",

    "th_num":    "3 000",
    "th_or":     "SAU",
    "th_one":    "1?",
    "th_nights": "3 000 DE NOPȚI",
    "th_day":    "O ZI?",
    "th_short":  "3 000?",
    "th_or2":    "SAU",
    "th_hook":   "ÎNCĂ UNUL?",

    "chat_name": "Max",
    "chat_1":    "ne vedem sâmbătă?",
    "chat_2":    "nu pot",
    "chat_3":    "ești bine?",

    "w1": "încă unul.",
    "w2": "cine mai doarme la vârsta ta?",
    "w3": "vezi? nu ai nevoie de nimeni.",
    "w4": "am rămas doar eu și tu.",
    "w5": "ți-am spus eu.",
}

# Арабский. Пишется справа налево и соединяется в вязь: PIL ничего этого не
# умеет, поэтому ВСЕ строки таблицы прогоняются через arabic_reshaper и
# python-bidi в момент выбора языка (см. ниже) — раскадровку это не трогает.
AR = {
    "title_1":   "التمرير",
    "title_vs":  "vs",
    "title_2":   "الحياة.",

    "hud_night":    "ليل",
    "hud_scrolled": "تم التمرير",
    "hud_known":    "تذكّر",

    "n01a": "فتح التطبيق  ",
    "n01b": "  لدقيقة.  ",
    "n02":  "كان المساء ينتهي بحديث.",
    "n03":  "كانت الساعة الحادية عشرة ليلاً.",
    "n04a": "التمرير لا ينتهي. ",
    "n04b": "هذه هي الفكرة كلها.",
    "n05":  "في البداية كان يختار ما يشاهد.",
    "n06":  "ثم صاروا يختارون له.",
    "n07":  "لم يعد يلاحظ أين ينتهي الليل.",
    "n08":  "صار الصباح عقاباً.",
    "n09":  "كان يمرّ بجانب الناس.",
    "n10":  "توقّف الأصدقاء عن السؤال.",
    "n11":  "لم يبقَ ما ينتظره.",
    "n12":  "أطفأ الهاتف.",
    "n13":  "بعد عشرين دقيقة…",
    "n14":  "أعاد تشغيله.",
    "n15":  "ثم كتب هو أولاً.",

    "fin_1": "مرّر ثلاثة آلاف.",
    "fin_2": "تذكّر يوماً واحداً.",
    "out_1": "ضع الهاتف.",
    "out_2": "أو تمريرة أخرى.",

    "cal_month": "أكت",

    "th_num":    "٣٠٠٠",
    "th_or":     "أم",
    "th_one":    "١؟",
    "th_nights": "ليلة ٣٠٠٠",
    "th_day":    "يوم واحد؟",
    "th_short":  "٣٠٠٠؟",
    "th_or2":    "أم",
    "th_hook":   "واحدة أخرى؟",

    "chat_name": "ماكس",
    "chat_1":    "نلتقي السبت؟",
    "chat_2":    "لا أستطيع",
    "chat_3":    "هل أنت بخير؟",

    "w1": "واحدة أخرى.",
    "w2": "من ينام في عمرك؟",
    "w3": "أرأيت؟ لا تحتاج أحداً.",
    "w4": "لم يبقَ سوانا.",
    "w5": "قلت لك.",
}


# Шрифт почерка демона. По умолчанию Segoe Script, но в нём НЕТ румынской
# буквы ț (проверено разбором cmap 26.10: ș есть, ț нет). Для румынского —
# Segoe Print: тоже рукописный и держит весь набор. Проверять КАЖДЫЙ новый
# язык разбором cmap, а не на глаз: отсутствующая буква рисуется пустым
# квадратом и в логе рендера ничем себя не выдаёт.
HAND_FONT = {"ro": "segoepr.ttf", "ar": "tahoma.ttf", "fr": "segoepr.ttf",
             "es": "segoeprb.ttf", "it": "inkfree.ttf"}

# НАБОР ШРИФТОВ НА ЯЗЫК. Версии для разных каналов обязаны отличаться не
# только текстом, но и начертанием (прямое слово пользователя 06.11), поэтому
# у каждого языка свой набор. Все наборы проверены растровой сверкой с .notdef
# на полном тексте своего языка — не на глаз.
#   FN  основной тонкий   FNB обычный   FH  узкий для счётчика   FI курсив
FONTS = {
    "ru": ("calibril.ttf", "calibri.ttf",  "bahnschrift.ttf", "calibrili.ttf"),
    "pl": ("calibril.ttf", "calibri.ttf",  "bahnschrift.ttf", "calibrili.ttf"),
    "fr": ("candara.ttf",  "candarab.ttf", "framd.ttf",       "candarali.ttf"),
    "es": ("corbel.ttf",   "corbelb.ttf",  "trebucbd.ttf",    "corbeli.ttf"),
    "it": ("trebuc.ttf",   "trebucbd.ttf", "verdanab.ttf",    "trebucit.ttf"),
    "ro": ("georgia.ttf",  "georgiab.ttf", "tahomabd.ttf",    "georgiai.ttf"),
    "ar": ("segoeui.ttf",  "segoeuib.ttf", "tahomabd.ttf",    "segoeuil.ttf"),
}


# Шрифт заголовка ОБЛОЖКИ. Arial Black не держит арабский вовсе — буквы
# выходят пустыми квадратами, и ни лог, ни статус прогона об этом не скажут
# (поймано глазами на готовой обложке 07.11). Заодно развели обложки по
# языкам: у каждой версии свой характер заголовка.
THUMB_FONT = {"ru": "ariblk.ttf", "pl": "ariblk.ttf", "fr": "framd.ttf",
              "es": "trebucbd.ttf", "it": "verdanab.ttf", "ro": "georgiab.ttf",
              "ar": "tahomabd.ttf"}


def thumb_font():
    """Шрифт заголовка обложки текущего языка."""
    return THUMB_FONT.get(LANG, "ariblk.ttf")


def fonts():
    """Четыре шрифта текущего языка: тонкий, обычный, узкий, курсив."""
    return FONTS.get(LANG, FONTS["ru"])

TABLES = {"ru": RU, "pl": PL, "fr": FR, "es": ES, "it": IT, "ro": RO, "ar": AR}
LANG = os.environ.get("SHORTFILM_LANG", "ru").lower()
if LANG not in TABLES:
    raise SystemExit(f"неизвестный язык SHORTFILM_LANG={LANG}, есть: {', '.join(TABLES)}")
L = TABLES[LANG]

RTL = LANG in ("ar",)
if RTL:
    # Без этого PIL нарисует арабский слева направо разорванными буквами —
    # и ни лог, ни статус прогона об этом не скажут (та же мина, что с cmap).
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:
        raise SystemExit("для арабского нужны arabic-reshaper и python-bidi")
    def _shape(v):
        # base_dir="R" обязателен: направление строки bidi берёт по первому
        # СИЛЬНОМУ символу, а цифра таковой не является — строка «3 000 ليلة»
        # без этого разворачивается наизнанку и число уезжает влево
        # (поймано на готовой обложке 07.11).
        return get_display(arabic_reshaper.reshape(v), base_dir="R") if isinstance(v, str) else v
    L = {k: _shape(v) for k, v in L.items()}

# проверка полноты: таблица языка должна покрывать русскую целиком
_missing = [k for k in RU if k not in L]
if _missing:
    raise SystemExit(f"в таблице '{LANG}' не хватает строк: {', '.join(_missing)}")


def hand_font(default="segoesc.ttf"):
    """Файл шрифта для почерка демона в текущем языке."""
    return HAND_FONT.get(LANG, default)
