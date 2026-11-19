"""Foydalanuvchiga ko'rinadigan barcha matnlar (o'zbek tilida)."""

WELCOME = (
    "Assalomu alaykum! 👋\n"
    "Men sizning AI ovozli yordamchingizman.\n\n"
    "🎙 Ovozli xabar, audio yoki video yuboring — men uni matnga aylantiraman.\n\n"
    "📝 Matn yuboring — men uni tabiiy ovozga aylantirib, ovozli xabar qilib qaytaraman.\n\n"
    "✨ Qo‘shimcha ravishda audio uchun qisqa konspekt va vaqt belgilari bilan muhim "
    "ma'lumotlarni ham tayyorlay olaman.\n\n"
    "Boshlash uchun audio yoki matn yuboring!"
)

HELP = (
    "<b>Qanday foydalaniladi?</b>\n\n"
    "🎙 <b>Ovoz → matn</b>\n"
    "Ovozli xabar, audio fayl (MP3, WAV, M4A, OGG...), video yoki video-doira yuboring. "
    "Tilni o'zim aniqlayman: o'zbek, rus, ingliz va boshqalar.\n"
    "Matn ostidagi tugmalar orqali qisqa xulosa, vaqt belgilari bilan konspekt, asosiy g'oyalar "
    "va vazifalar ro'yxatini olasiz.\n\n"
    "📝 <b>Matn → ovoz</b>\n"
    "Istalgan matnni yozing yoki .txt fayl yuboring — ovozli xabar qilib qaytaraman. "
    "Matn tili (o'zbek, rus, ingliz) avtomatik aniqlanadi.\n\n"
    "🗣 Ovozni tanlash (ayol / erkak): /ovoz\n\n"
    "ℹ️ Fayl hajmi — {max_mb} MB gacha, audio uzunligi — {max_min} daqiqagacha."
)

LANG_NAMES = {
    "uz": "🇺🇿 O‘zbekcha",
    "ru": "🇷🇺 Ruscha",
    "en": "🇬🇧 Inglizcha",
    "tr": "🇹🇷 Turkcha",
    "kk": "🇰🇿 Qozoqcha",
    "ky": "🇰🇬 Qirg‘izcha",
    "tg": "🇹🇯 Tojikcha",
    "tk": "🇹🇲 Turkmancha",
    "ar": "🇸🇦 Arabcha",
    "de": "🇩🇪 Nemischa",
    "fr": "🇫🇷 Fransuzcha",
    "es": "🇪🇸 Ispancha",
    "ko": "🇰🇷 Koreyscha",
    "zh": "🇨🇳 Xitoycha",
    "fa": "🇮🇷 Forscha",
    "hi": "🇮🇳 Hindcha",
}

ACTION_TITLES = {
    "summary": "📝 Qisqa xulosa",
    "notes": "🕒 Vaqt belgilari bilan konspekt",
    "ideas": "💡 Asosiy g‘oyalar",
    "tasks": "✅ Muhim nuqtalar va vazifalar",
}

QUEUED = "⏳ Navbatda... Birozdan keyin boshlayman."
DOWNLOADING = "⏳ Fayl yuklab olinmoqda..."
LISTENING = "🎧 Tinglayapman..."
LISTENING_DUR = "🎧 Tinglayapman... ({dur} audio)"
LISTENING_PROGRESS = "🎧 Tinglayapman... {done}/{total} qism tayyor"
FULL_TEXT_IN_FILE = "📄 <i>Matn uzun bo‘lgani uchun to‘liq variantini fayl qilib yubordim.</i>"
FILE_CAPTION = "📄 To‘liq transkripsiya"

NO_SPEECH = "🤷 Bu audioda nutq topilmadi. Ovoz aniq eshitiladigan yozuv yuboring."
TOO_BIG = (
    "⚠️ Fayl juda katta ({size} MB). Men {max_mb} MB gacha fayllarni qabul qila olaman.\n"
    "💡 Maslahat: videoni siqib yoki audiosini alohida ajratib yuboring."
)
TOO_LONG = "⚠️ Audio juda uzun ({dur}). Hozircha {max_min} daqiqagacha bo‘lgan yozuvlarni qayta ishlayman."
BAD_FILE = "⚠️ Bu faylni o‘qib bo‘lmadi. U buzilgan yoki ichida audio yo‘q. Boshqa formatda yuborib ko‘ring."
AI_ERROR = "⚠️ Matnga aylantirishda xatolik yuz berdi. Iltimos, birozdan keyin qayta yuboring."
STT_DISABLED = "⚠️ Ovozni matnga aylantirish hozircha sozlanmagan."
UNSUPPORTED = "🤔 Bu turdagi xabarni tushunmadim.\n🎙 Audio/video yoki 📝 matn yuboring."
UNKNOWN_COMMAND = "Bunday buyruq yo‘q. Shunchaki audio yoki matn yuboring 🙂"

ACTION_WORKING = "⏳ Tayyorlanmoqda..."
ACTION_BUSY = "⏳ Allaqachon tayyorlanmoqda, biroz kuting."
ACTION_EXPIRED = "Bu ma'lumot eskirgan. Audioni qayta yuboring."
ACTION_ERROR = "⚠️ Tayyorlab bo‘lmadi. Birozdan keyin qayta urinib ko‘ring."

TTS_EMPTY = "🤔 Ovozga aylantiradigan matn topilmadi."
TTS_ERROR = "⚠️ Ovozga aylantirib bo‘lmadi. Birozdan keyin qayta urinib ko‘ring."
TTS_TRUNCATED = "✂️ Matn juda uzun — uning dastlabki qismini ovozlashtirdim."
TXT_TOO_BIG = "⚠️ Matn fayli juda katta. 1 MB gacha .txt fayl yuboring."

VOICE_PICK = "🗣 Matnlarni qaysi ovozda o‘qiy?\n<i>Til (o‘zbek, rus, ingliz) avtomatik aniqlanadi.</i>"
VOICE_SET = "Tanlandi: {name}"
