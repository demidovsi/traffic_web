from common import get
from deep_translator import GoogleTranslator
import time
import json
import os

road = [
    {"0": "Начальная точка"},
    {"1": "Конечная точка"},
    {"2": "Рассчитать маршрут"},
    {"3": "Время начала"},
    {"4": "Расстояние км"},
    {"5": "Время пути"},
    {"6": "Суммарный вес"},
    {"7": "Все точки маршрута"},
    {"8": "Только точки аварий"},
    {"9": "Коэффициент"},
    {"10": "Безопасно"},
    {"11": "Внимание"},
    {"12": "Аварийно"},
    {"13": "Прогноз на поездку"},
]

lang = dict()
lang_busy = False


def get_lang(user_id, form, array_text):
    to_lang = get(user_id, 'select_language')
    return get_value_language(form, array_text, to_lang)


def get_value_language(key, array_text, to_lang):
    global lang
    if to_lang not in lang:
        lang[to_lang] = {}
    if key not in lang[to_lang]:
        lang[to_lang][key] = translate_array(array_text, to_lang)
        save_lang()
    return lang[to_lang][key]


def translate_array(array, to_lang):
    try:
        result = list()
        if to_lang == 'he':
            to_lang = 'iw'
        for unit in array:
            for key in unit.keys():
                result.append(GoogleTranslator(target=to_lang).translate(unit[key]))
        return result
    except Exception as er:
        print(f"{er}")
        return array


def save_lang():
    global lang, lang_busy
    while lang_busy:
        time.sleep(1)
    lang_busy = True
    try:
        f = open('static/language.json', 'w', encoding='utf-8')
        with f:
            f.write(json.dumps(lang, indent=4, ensure_ascii=False, sort_keys=True))
    except Exception as er:
        print(f"{er}")
    lang_busy = False


def load_lang():
    global lang, lang_busy
    while lang_busy:
        time.sleep(1)
    lang_busy = True
    if os.path.exists('static/language.json'):
        f = open('static/language.json', 'r', encoding='utf-8')
        with f:
            lang = f.read()
            if lang:
                lang = json.loads(lang)
            else:
                lang = dict()
    lang_busy = False


"""
Сокращения возможных языков
{'afrikaans': 'af', 'albanian': 'sq', 'amharic': 'am', 'arabic': 'ar', 'armenian': 'hy', 'assamese': 'as', 
'aymara': 'ay', 'azerbaijani': 'az', 'bambara': 'bm', 'basque': 'eu', 'belarusian': 'be', 'bengali': 'bn', 
'bhojpuri': 'bho', 'bosnian': 'bs', 'bulgarian': 'bg', 'catalan': 'ca', 'cebuano': 'ceb', 'chichewa': 'ny', 
'chinese (simplified)': 'zh-CN', 'chinese (traditional)': 'zh-TW', 'corsican': 'co', 'croatian': 'hr', 'czech': 'cs', 
'danish': 'da', 'dhivehi': 'dv', 'dogri': 'doi', 'dutch': 'nl', 'english': 'en', 'esperanto': 'eo', 'estonian': 'et', 
'ewe': 'ee', 'filipino': 'tl', 'finnish': 'fi', 'french': 'fr', 'frisian': 'fy', 'galician': 'gl', 'georgian': 'ka', 
'german': 'de', 'greek': 'el', 'guarani': 'gn', 'gujarati': 'gu', 'haitian creole': 'ht', 'hausa': 'ha', 
'hawaiian': 'haw', 'hebrew': 'iw', 'hindi': 'hi', 'hmong': 'hmn', 'hungarian': 'hu', 'icelandic': 'is', 'igbo': 'ig', 
'ilocano': 'ilo', 'indonesian': 'id', 'irish': 'ga', 'italian': 'it', 'japanese': 'ja', 'javanese': 'jw', 
'kannada': 'kn', 'kazakh': 'kk', 'khmer': 'km', 'kinyarwanda': 'rw', 'konkani': 'gom', 'korean': 'ko', 'krio': 'kri', 
'kurdish (kurmanji)': 'ku', 'kurdish (sorani)': 'ckb', 'kyrgyz': 'ky', 'lao': 'lo', 'latin': 'la', 'latvian': 'lv', 
'lingala': 'ln', 'lithuanian': 'lt', 'luganda': 'lg', 'luxembourgish': 'lb', 'macedonian': 'mk', 'maithili': 'mai', 
'malagasy': 'mg', 'malay': 'ms', 'malayalam': 'ml', 'maltese': 'mt', 'maori': 'mi', 'marathi': 'mr', 
'meiteilon (manipuri)': 'mni-Mtei', 'mizo': 'lus', 'mongolian': 'mn', 'myanmar': 'my', 'nepali': 'ne', 
'norwegian': 'no', 'odia (oriya)': 'or', 'oromo': 'om', 'pashto': 'ps', 'persian': 'fa', 'polish': 'pl', 
'portuguese': 'pt', 'punjabi': 'pa', 'quechua': 'qu', 'romanian': 'ro', 'russian': 'ru', 'samoan': 'sm', 
'sanskrit': 'sa', 'scots gaelic': 'gd', 'sepedi': 'nso', 'serbian': 'sr', 'sesotho': 'st', 'shona': 'sn', 
'sindhi': 'sd', 'sinhala': 'si', 'slovak': 'sk', 'slovenian': 'sl', 'somali': 'so', 'spanish': 'es', 'sundanese': 'su', 
'swahili': 'sw', 'swedish': 'sv', 'tajik': 'tg', 'tamil': 'ta', 'tatar': 'tt', 'telugu': 'te', 'thai': 'th', 
'tigrinya': 'ti', 'tsonga': 'ts', 'turkish': 'tr', 'turkmen': 'tk', 'twi': 'ak', 'ukrainian': 'uk', 'urdu': 'ur', 
'uyghur': 'ug', 'uzbek': 'uz', 'vietnamese': 'vi', 'welsh': 'cy', 'xhosa': 'xh', 'yiddish': 'yi', 'yoruba': 'yo', 
'zulu': 'zu'}
"""