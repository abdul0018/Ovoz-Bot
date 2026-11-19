# Ovoz Bot — AI ovozli yordamchi 🎙📝

Ikki tomonlama ishlaydigan Telegram bot:

**Ovoz → Matn → Konspekt**
- Ovozli xabar, audio fayl (MP3, WAV, M4A, OGG, FLAC, AAC, AMR...), video va video-doirani qabul qiladi.
- Nutq tilini o'zi aniqlaydi (o'zbek, rus, ingliz va boshqa tillar), tinish belgilari va abzaslarni saqlaydi.
- Javob boshida davomiylik va til ko'rsatiladi: `🎧 0:07 · 🇺🇿 O'zbekcha`.
- Uzun yozuvlar 10 daqiqalik bo'laklarga ajratilib, **parallel** tanib olinadi. Jarayon holat xabarida ko'rinadi: `🎧 Tinglayapman... 2/5 qism tayyor`.
- Matn uzun bo'lsa, qisqa ko'rinishi va to'liq **TXT fayl** (vaqt belgilari bilan) yuboriladi.
- Matn ostidagi tugmalar:
  - 📝 **Qisqa xulosa**
  - 🕒 **Konspekt** — vaqt belgilari bilan (`00:00 — Salomlashish ...`)
  - 💡 **Asosiy g'oyalar**
  - ✅ **Vazifalar** — muhim nuqtalar va bajarilishi kerak bo'lgan ishlar
  - 🔊 **Ovozli xabar qilish**

**Matn → Ovoz**
- Istalgan matn yoki `.txt` fayl yuborsangiz, tabiiy ovozli **voice message** qaytaradi (oddiy audio fayl emas).
- Matn tili avtomatik aniqlanadi: o'zbek (lotin va kirill), rus, ingliz.
- Uzun matn bir nechta ovozli xabarga bo'linadi (`🔊 1/3`, `🔊 2/3`...).
- `/ovoz` — ayol yoki erkak ovozini tanlash.

Hech qanday buyruq shart emas — bot xabar turini o'zi aniqlaydi.

| Vazifa | Texnologiya | Narx |
|---|---|---|
| Ovoz → matn, tahlil | Google Gemini (Flash) | arzon, bepul limit bor |
| Matn → ovoz | Microsoft Edge neyron ovozlari (`edge-tts`) | bepul, kalit kerak emas |
| Ovozlar | 🇺🇿 Madina / Sardor · 🇷🇺 Svetlana / Dmitry · 🇬🇧 Ava / Andrew | |

## 🚀 Bepul serverga joylash (Render) — 5 daqiqa

**1. Bot tokenini oling.** Telegramda [@BotFather](https://t.me/BotFather) → `/newbot` → bot nomini va username'ini (oxiri `bot` bilan tugashi kerak) yozing → bergan tokenni nusxalang (`123456789:AA...` ko'rinishida).

**2. Gemini kalitini oling.** [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → Google akkaunt bilan kiring → **Create API key** → kalitni nusxalang (`AIza...` ko'rinishida).

**3. Render'ga joylang.** Quyidagi tugmani bosing:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/abdul0018/Ovoz-Bot/tree/main)

- GitHub akkauntingiz bilan ro'yxatdan o'ting (karta talab qilinmaydi).
- Ochilgan sahifada `BOT_TOKEN` va `GEMINI_API_KEY` maydonlariga 1- va 2-qadamdagi qiymatlarni joylang.
- **Deploy Blueprint** (yoki **Apply**) tugmasini bosing.

3-5 daqiqadan keyin loglarda `Bot webhook rejimida ishga tushdi` yozuvi chiqadi — botingizga Telegramda `/start` yozing. ✅

`main` branchga har bir yangi o'zgarish Render'da avtomatik qayta joylanadi.

> **Bepul tarif haqida.** 15 daqiqa xabar kelmasa, server uxlaydi; keyingi birinchi xabarga javob 30-60 soniya kechikadi, so'ng odatdagidek tez ishlaydi. Uxlab qolganda eski xabarlardagi tugmalar ishlamasligi mumkin — audioni qayta yuborish kifoya.
> Uxlamasligi uchun (ixtiyoriy): [UptimeRobot](https://uptimerobot.com) da bepul monitor qo'shing — `https://<servis-nomingiz>.onrender.com/health` manzilini har 5 daqiqada tekshirsin.

## 💻 Kompyuterda ishga tushirish

Kerak: Python 3.10+ va [ffmpeg](https://ffmpeg.org/download.html) (Windows: `winget install ffmpeg`, macOS: `brew install ffmpeg`, Ubuntu: `sudo apt install ffmpeg`).

```bash
git clone https://github.com/abdul0018/Ovoz-Bot.git
```

```bash
cd Ovoz-Bot
```

```bash
pip install -r requirements.txt
```

```bash
cp .env.example .env
```

`.env` faylida `BOT_TOKEN` va `GEMINI_API_KEY` ni to'ldiring, keyin:

```bash
python bot.py
```

## 🐳 O'z serveringizda (Docker)

```bash
docker compose up -d --build
```

Loglarni ko'rish:

```bash
docker compose logs -f
```

Bot `WEBHOOK_URL` berilmasa polling rejimida ishlaydi (ochiq port shart emas). `WEBHOOK_URL` (yoki Render'dagi `RENDER_EXTERNAL_URL`) berilsa — webhook rejimida, `PORT` portida.

## Sozlamalar (`.env`)

| O'zgaruvchi | Standart | Tavsif |
|---|---|---|
| `BOT_TOKEN` | — | @BotFather tokeni (majburiy) |
| `GEMINI_API_KEY` | — | Gemini kaliti. Bo'lmasa faqat matn → ovoz ishlaydi |
| `GEMINI_MODEL` | `gemini-flash-latest` | Model nomi; aniq versiya uchun masalan `gemini-2.5-flash` |
| `DEFAULT_VOICE_GENDER` | `female` | `female` yoki `male` |
| `MAX_AUDIO_MINUTES` | `180` | Bundan uzun audio rad etiladi (xarajat nazorati) |
| `MAX_CONCURRENT_JOBS` | `4` | Bir vaqtda qayta ishlanadigan audio soni, qolganlari navbatda |
| `DATA_DIR` | `data` | SQLite bazasi papkasi |
| `WEBHOOK_URL` | — | Tashqi manzil (masalan `https://bot.example.com`) — webhook rejimini yoqadi. Render'da avtomatik |
| `PORT` | `8080` | Webhook rejimida HTTP port |
| `TELEGRAM_API_SERVER` | — | O'z [Bot API serveringiz](https://github.com/tdlib/telegram-bot-api) manzili |

## Cheklovlar va ularni hal qilish

- **Fayl hajmi.** Oddiy Telegram Bot API botlarga 20 MB gacha faylni yuklab olishga ruxsat beradi (ovozli xabar uchun bu bir necha soat, video uchun esa bir necha daqiqa). Kattaroq fayllar uchun o'zingizning [telegram-bot-api](https://github.com/tdlib/telegram-bot-api) serveringizni `--local` rejimida ishga tushirib, `TELEGRAM_API_SERVER` ni ko'rsating — chegara 2 GB gacha oshadi (server va bot bir xil fayl tizimini ko'rishi kerak).
- **Xarajat.** Audio Gemini'ga yuborishdan oldin 16 kHz mono 32 kbit/s ga siqiladi; konspekt va boshqa tahlillar faqat tugma bosilganda tayyorlanadi va bazada keshlanadi — qayta bosilganda API chaqirilmaydi.
- **Saqlash.** Transkripsiyalar 30 kun saqlanadi, shuning uchun bot qayta ishga tushsa ham tugmalar ishlayveradi.
- Matn → ovoz guruhlarda o'chirilgan (har bir xabarga ovoz yubormasligi uchun); ovoz → matn guruhlarda ham ishlaydi.

## Testlar

```bash
pip install -r requirements-dev.txt
```

```bash
pytest
```

Testlar Telegram, Gemini va TTS'ni soxtalashtirib ishlaydi — tarmoq yoki kalit kerak emas (faqat ffmpeg).

## Tuzilishi

```
bot.py                     — ishga tushirish, sozlash
ovozbot/
  config.py                — .env sozlamalari
  ai.py                    — Gemini: transkripsiya va tahlil (xulosa, konspekt, g'oyalar, vazifalar)
  transcription.py         — konvertatsiya → bo'laklash → parallel tanib olish → birlashtirish
  tts.py                   — matn → ovoz (edge-tts), matnni bo'lish
  lang.py                  — matn tilini aniqlash, o'zbek kirill → lotin
  media.py                 — ffmpeg yordamchilari
  storage.py               — SQLite: sozlamalar va transkripsiyalar
  models.py                — ma'lumot modellari
  texts.py, keyboards.py   — o'zbekcha interfeys matnlari va tugmalar
  handlers/                — start, audio, actions (tugmalar), text
tests/                     — unit va to'liq oqim testlari
```
