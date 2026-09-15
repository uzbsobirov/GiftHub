# ⭐ Stellar Bot — Telegram Stars, Premium & Gifts Platform

Telegram bot + Telegram Web App (Mini App) orqali Telegram Stars, Telegram Premium obunasi va Premium sovg'alarni xarid qilish xizmati.

Ushbu loyiha **`stellar-bot-tz-v2.md`**, **`stellar-bot-mockup.html`** va **`stellar-bot-admin-mockup.html`** talablari hamda Aiogram 3 shabloni asosida to'liq ishlab chiqilgan.

---

## 🚀 Asosiy Imkoniyatlar

### 👤 Foydalanuvchi Tomoni (User Web App)
- **Telegram Web App avtomatik login:** `initData` xavfsiz HMAC-SHA256 tekshiruvi.
- **Gate (Majburiy a'zolik ekrani):** Botdan foydalanishdan oldin majburiy kanallarga a'zolikni tekshirish (oddiy a'zolik, join request va tashqi soft-havolalar).
- **Hamyon balansi:** Click, Payme va AutoPayCard orqali hisobni to'ldirish, to'lovlar tarixi.
- **Xarid oqimi:**
  - Telegram Stars (50, 100, 250, 500, 1000 yoki ixtiyoriy miqdor).
  - Telegram Premium (3, 6, 12 oylik paketlar).
  - Cheklangan raqamli sovg'alar (Teddy Bear, Neon Heart, Cosmo Rocket va h.k.).
- **Buyurtmalar tarixi:** Holatlar bo'yicha filtrlash (Kutilmoqda / Bajarildi / Bekor qilingan) va qidiruv.
- **Referal tizimi:** Shaxsiy havola (`t.me/bot?start=ref_<user_id>`), taklif qilinganlar soni va xaridlardan +5% avtomatik bonus.

### ⚙ Admin Boshqaruv Paneli (Admin Web App)
- **Narx belgilash tizimi:**
  - 1 dona Stars tannarxi (TON), TON kursi (so'mda) va marja (%) asosida avtomatik hisoblash.
  - Ulgurji xaridlar uchun chegirmalar darajasi (masalan 500+ Stars uchun -5%, 1000+ Stars uchun -8%).
  - Bir tugma bilan TON kursini yangilash.
- **Statistika & Foyda hisoboti:**
  - Yangi foydalanuvchilar, jami savdo, sof foyda (marja) va referal orqali kelgan buyurtmalar.
  - Mahsulotlar kesimida daromad va tannarx tahlili.
  - CSV formatda buyurtmalar eksporti.
- **Reklama yuborish (Broadcast):**
  - Auditoriya segmentlari: Barchasi, Xarid qilmaganlar, Faol foydalanuvchilar, Referal orqali kelganlar.
  - 3 xil rejim: Yozish (matn + rasm + tugma), Kanaldan forward qilish (`copyMessage`) va PostBot'dan forward orqali qabul qilish.
  - Telegram chekloviga mos tezlik (~30 xabar/sekund).
- **Majburiy a'zolik boshqaruvi:**
  - Bot kanalga admin qilib qo'shilganda `my_chat_member` hodisasi orqali avtomatik aniqlash va majburiy qilish.
  - Tashqi havolalar (Instagram, YouTube va h.k.) qo'shish.
- **Adminlar va Rollar:**
  - Admin qo'shish: xabarni forward qilish orqali yoki `@username`/ID orqali.
  - Rollar: *Super Admin*, *Narx admin*, *Support admin*, *Marketing admin*.
  - Barcha harakatlar jurnali (**Audit Log**).
- **To'lov usullari:** Click, Payme (rasmiy) hamda AutoPayCard (zaxira, ogohlantirishlar bilan).

---

## 📁 Loyiha Tuzilmasi

```text
├── app/
│   ├── handlers/
│   │   ├── channels/          # my_chat_member va chat_join_request handlerlari
│   │   └── users/             # /start (referal bilan), help, admin_forward handlerlari
│   ├── keyboards/             # Inline va Web App tugmalari
│   ├── utils/                 # Admin xabarnomalari va bot buyruqlari
│   └── web/                   # FastAPI backend serveri & Web App API
│       ├── auth.py            # Telegram Web App initData HMAC-SHA256 validatsiyasi
│       └── server.py          # REST API va statik Web App marshrutlari
├── data/
│   ├── config.py              # Muhit o'zgaruvchilari
│   └── stellar.db             # SQLite ma'lumotlar bazasi
├── database/
│   ├── models.py              # SQLAlchemy 2.0 Async modellari (Users, Orders, Pricing, Logs...)
│   ├── db.py                  # Engine, Session va birlamchi sozlamalar
│   └── queries.py             # CRUD funksiyalari va narx hisob-kitoblari
├── middlewares/
│   ├── throttling.py          # Antiflood / so'rovlar chastotasini cheklash
│   └── user_register.py       # Yangi foydalanuvchilarni avtomatik ro'yxatga olish
├── web/
│   ├── user/index.html        # Telegram Web App (Foydalanuvchi do'koni)
│   └── admin/index.html       # Admin boshqaruv paneli
├── .env.example               # Muhit konfiguratsiyasi namunasi
├── requirements.txt           # Kerakli Python kutubxonalari
└── main.py                    # Bot va Web App serverini bir vaqtda ishga tushiruvchi asosiy fayl
```

---

## ⚡ Ishga Tushirish

1. **Bog'liqliklarni o'rnatish:**
   ```bash
   pip install -r requirements.txt
   ```

2. **`.env` faylini sozlash:**
   `.env.example` dan nusxa olib `.env` yarating va `BOT_TOKEN` hamda `ADMINS` ID larini kiriting:
   ```env
   BOT_TOKEN=BOT_TOKEN_HERE
   ADMINS=ADMIN_ID_HERE
   WEB_HOST=0.0.0.0
   WEB_PORT=8000
   WEB_APP_URL=http://localhost:8000/app
   ADMIN_APP_URL=http://localhost:8000/admin
   DB_URL=sqlite+aiosqlite:///data/stellar.db
   ```

3. **Loyiha serveri va botni ishga tushirish:**
   ```bash
   python main.py
   ```

4. **Brauzerda ko'rish:**
   - Foydalanuvchi Web App: `http://localhost:8000/app`
   - Admin Panel: `http://localhost:8000/admin`
