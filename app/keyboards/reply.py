from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from data import config

def get_reply_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Foydalanuvchi doimiy ravishda Telegram pastki panelida ko'rib turishi uchun Reply klaviatura.
    Admin panel tugmasi bu yerdan olib tashlangan (faqat /admin komandasi orqali ochiladi).
    Yordam bo'limi faqat SUPPORT_URL sozlangan bo'lsa chiqadi.
    """
    keyboard = []
    if config.WEB_APP_URL.startswith("https://"):
        keyboard.append([
            KeyboardButton(
                text="⭐ Do'konni ochish (Web App)",
                web_app=WebAppInfo(url=config.WEB_APP_URL)
            )
        ])
    else:
        keyboard.append([KeyboardButton(text="⭐ Do'konni ochish")])

    row2 = [KeyboardButton(text="👤 Profil")]
    if config.SUPPORT_URL:
        row2.append(KeyboardButton(text="🛟 Yordam"))

    keyboard.append(row2)

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
