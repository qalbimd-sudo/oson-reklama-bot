# OSON REKLAMA Agentligi Telegram Boti

Ushbu bot **OSON REKLAMA** agentligi uchun buyurtmalarni qabul qilish va mijozlarga AI yordamida xizmat ko'rsatish uchun mo'ljallangan.

## Xususiyatlari
- **Google Gemini API**: Mijozlarning so'rovlarini tahlil qilish va xizmat turini aniqlash uchun ishlatiladi.
- **SQLite Ma'lumotlar Bazasi**: Foydalanuvchilar, buyurtmalar va suhbat tarixini saqlaydi.
- **24/7 Ishlash**: Cloud serverlarda doimiy ishlash uchun moslashtirilgan.
- **Admin Panel**: Yangi buyurtmalar haqida adminni xabardor qiladi.

## O'rnatish va Ishga tushirish

### 1. Mahalliy kompyuterda ishga tushirish
1. Python o'rnatilganligiga ishonch hosil qiling.
2. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. `config.py` fayliga o'z ma'lumotlaringizni kiriting (Bot Token, Gemini API Key, Admin Chat ID).
4. Botni ishga tushiring:
   ```bash
   python main.py
   ```

### 2. Cloud serverga deploy qilish (Render.com / Koyeb.com)
Ushbu platformalarda GitHub-siz deploy qilish uchun:
1. Platformada yangi "Web Service" yoki "Worker" yarating.
2. Dockerfile orqali deploy qilishni tanlang.
3. Loyiha fayllarini yuklang.

### 3. Railway.app orqali deploy qilish
1. Railway CLI-ni o'rnating.
2. Terminalda loyiha papkasiga kiring va:
   ```bash
   railway login
   railway init
   railway up
   ```

## Fayllar tuzilishi
- `main.py`: Botning asosiy mantiqi va Gemini API integratsiyasi.
- `database.py`: SQLite bazasi bilan ishlash (foydalanuvchilar, buyurtmalar, tarix).
- `config.py`: Bot sozlamalari va API kalitlari.
- `Dockerfile`: Docker konteyner yaratish uchun.
- `requirements.txt`: Kerakli Python kutubxonalari.
- `Procfile`: Cloud platformalar uchun ishga tushirish buyrug'i.

## Muallif
**Manus AI** tomonidan OSON REKLAMA agentligi uchun tayyorlandi.
