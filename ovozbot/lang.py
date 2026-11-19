"""Matn tilini aniqlash (uz / ru / en) — tez, bepul, API'siz evristika."""
import re

_UZ_CYR_ONLY = set("ўқғҳЎҚҒҲ")
_APOS = "'ʻʼ‘’`"
_UZ_APOS_RE = re.compile(rf"\b\w*[og][{_APOS}]\w*", re.IGNORECASE)
_WORD_RE = re.compile(r"[^\W\d_]+(?:[" + _APOS + r"][^\W\d_]+)*", re.UNICODE)

_UZ_WORDS = {
    "va", "bu", "men", "sen", "u", "biz", "siz", "ular", "uchun", "bilan", "emas", "ham", "bor",
    "yoq", "nima", "qanday", "kerak", "edi", "boladi", "juda", "lekin", "endi", "yana", "hozir",
    "salom", "rahmat", "mana", "shu", "bir", "yaxshi", "qachon", "qayerda", "nega", "kim", "menga",
    "sizga", "keyin", "oldin", "kun", "bugun", "ertaga", "assalomu", "alaykum", "iltimos", "albatta",
    "ammo", "chunki", "agar", "hamma", "barcha", "bilan", "uni", "buni", "shunday", "mumkin",
    "qiling", "qildim", "dedi", "deb", "esa", "yo", "xop", "ha", "yoki", "ekan", "bolsa", "qilib",
}
_EN_WORDS = {
    "the", "and", "is", "are", "you", "i", "to", "of", "in", "it", "that", "this", "for", "with",
    "what", "how", "was", "have", "be", "not", "my", "your", "hello", "thanks", "please", "we",
    "they", "he", "she", "on", "at", "do", "does", "can", "will", "would", "a", "an", "but", "or",
    "if", "so", "there", "here", "about", "from", "me", "our", "all", "just", "like", "know",
}


def detect_language(text: str) -> str:
    cyr = sum(1 for ch in text if "а" <= ch.lower() <= "я" or ch in "ёЁ" or ch in _UZ_CYR_ONLY)
    lat = sum(1 for ch in text if "a" <= ch.lower() <= "z")
    if cyr > lat:
        return "uz-cyrl" if any(ch in _UZ_CYR_ONLY for ch in text) else "ru"

    words = [w.lower() for w in _WORD_RE.findall(text)]
    if not words:
        return "uz"
    normalized = [re.sub(f"[{_APOS}]", "", w) for w in words]
    uz = sum(1 for w in normalized if w in _UZ_WORDS) + 2 * len(_UZ_APOS_RE.findall(text))
    uz += 0.5 * sum(1 for w in normalized if "q" in w or ("x" in w and not w.startswith("ex")))
    en = sum(1 for w in words if w in _EN_WORDS)
    en += 0.5 * sum(1 for w in words if w.endswith(("ing", "tion", "ed")) or "th" in w or "w" in w)
    return "en" if en > uz else "uz"


_UZ_CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "ъ": "'", "ь": "",
    "ы": "i", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h", "щ": "sh",
}
_VOWELS = set("аеёиоуэюяў")


def uz_cyrillic_to_latin(text: str) -> str:
    """O'zbek kirill matnini lotinga o'giradi (o'zbek TTS ovozi lotin matnni yaxshiroq o'qiydi)."""
    out: list[str] = []
    prev = ""
    for ch in text:
        low = ch.lower()
        if low == "е":
            lat = "ye" if (not prev or prev.lower() in _VOWELS or not prev.isalpha()) else "e"
        else:
            lat = _UZ_CYR_TO_LAT.get(low)
        if lat is None:
            out.append(ch)
        else:
            out.append(lat.capitalize() if ch.isupper() and lat else lat)
        prev = ch
    return "".join(out)
