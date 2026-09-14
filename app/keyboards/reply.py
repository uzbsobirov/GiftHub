from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from data import config

def get_reply_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Foydalanuvchi doimiy ravishda Telegram pastki panelida ko'rib turishi uchun Reply klaviatura.
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

    row2 = [
        KeyboardButton(text="👤 Profil"),
        KeyboardButton(text="🛟 Yordam")
    ]
    keyboard.append(row2)

    if is_admin:
        if config.ADMIN_APP_URL.startswith("https://"):
            keyboard.append([
                KeyboardButton(
                    text="⚙ Admin Panel (Web App)",
                    web_app=WebAppInfo(url=config.ADMIN_APP_URL)
                )
            ])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
