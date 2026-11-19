# Ovoz Bot 🎧🔊

Telegram bot:

- **Ovoz → matn.** Ovozli xabar, audio fayl, video-doira yoki video yuborsangiz, bot uni matnga aylantirib beradi.
  Javob ostida ikkita tugma bor:
  - **📝 Konspekt** — vaqt belgilari bilan qisqa konspekt (`00:00 — Salomlashish ...`)
  - **🔊 Ovozga** — matnni qaytadan ovozli xabar qilib beradi
- **Matn → ovoz.** Oddiy matn yozsangiz, bot uni ovozli xabar qilib qaytaradi.
  Ovozni `/ovoz` buyrug'i bilan tanlaysiz: Madina (o'zbek, ayol), Sardor (o'zbek, erkak), Svetlana (rus), Jenny (ingliz).

| Vazifa | Xizmat | Narx |
|---|---|---|
| Ovoz → matn, konspekt | Google Gemini API | bepul limit bor |
| Matn → ovoz | Microsoft Edge TTS (`edge-tts`) | bepul, kalit kerak emas |

## 1. Kalitlarni olish

1. **Bot tokeni:** Telegramda [@BotFather](https://t.me/BotFather) → `/newbot` → bot nomi va username kiriting → token beriladi.
2. **Gemini kaliti:** [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → *Create API key*.

## 2. Ishga tushirish (kompyuterda)

Kerak: Python 3.10+ va [ffmpeg](https://ffmpeg.org/download.html).

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

`.env` faylini oching va `BOT_TOKEN` hamda `GEMINI_API_KEY` ni yozing. Keyin:

```bash
python bot.py
```

Windows'da ffmpeg o'rnatish: `winget install ffmpeg` (keyin terminalni qayta oching).

## 3. Serverda doimiy ishlatish (Docker)

```bash
docker build -t ovoz-bot .
```

```bash
docker run -d --name ovoz-bot --restart unless-stopped --env-file .env -v $(pwd)/data:/app/data ovoz-bot
```

Railway, Render, Fly.io kabi xizmatlarga ham `Dockerfile` orqali joylash mumkin — u yerda `BOT_TOKEN` va `GEMINI_API_KEY` ni muhit o'zgaruvchilari (Variables) sifatida kiriting.

## Sozlamalar (`.env`)

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | @BotFather tokeni (majburiy) |
| `GEMINI_API_KEY` | Gemini kaliti. Bo'lmasa, faqat matn → ovoz ishlaydi |
| `GEMINI_MODEL` | Model nomi, standart `gemini-flash-latest` (eng yangi Flash). Aniq versiya kerak bo'lsa, masalan `gemini-2.5-flash` |
| `DEFAULT_VOICE` | Standart ovoz: `madina`, `sardor`, `svetlana`, `jenny` |
| `DATA_DIR` | Foydalanuvchi sozlamalari saqlanadigan papka (standart `data`) |

## Eslatmalar

- Telegram botlar 20 MB gacha fayllarni yuklab ola oladi (ovozli xabar uchun bu ~1 soatdan ortiq).
- Matnga aylantirilgan xabarlar tugmalar uchun xotirada saqlanadi; bot qayta ishga tushsa, eski xabarlardagi tugmalar ishlamaydi — audioni qayta yuborish kifoya.
- Matn → ovoz faqat shaxsiy chatda ishlaydi (guruhda har bir xabarga ovoz yubormasligi uchun). Ovoz → matn guruhlarda ham ishlaydi.

## Tuzilishi

```
bot.py               — ishga tushirish
ovozbot/handlers.py  — Telegram xabarlari va tugmalar
ovozbot/stt.py       — ovoz → matn va konspekt (Gemini)
ovozbot/tts.py       — matn → ovoz (edge-tts)
ovozbot/media.py     — ffmpeg konvertatsiyalari
ovozbot/storage.py   — sozlamalar va kesh
```
