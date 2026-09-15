from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from data import config

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = []

    # Telegram WebAppInfo faqat HTTPS havolalarini qabul qiladi.
    if config.WEB_APP_URL.startswith("https://"):
        buttons.append([
            InlineKeyboardButton(
                text="⭐ Stellar Web App",
                web_app=WebAppInfo(url=config.WEB_APP_URL)
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="⭐ Stellar Web App (Brauzerda)",
                url=config.WEB_APP_URL
            )
        ])

    # Yangiliklar va Yordam (Support) faqat sozlangan bo'lsa chiqariladi
    extra_row = []
    if config.NEWS_CHANNEL_URL:
        extra_row.append(
            InlineKeyboardButton(
                text="📣 Yangiliklar",
                url=config.NEWS_CHANNEL_URL
            )
        )
    if config.SUPPORT_URL:
        support_link = config.SUPPORT_URL if config.SUPPORT_URL.startswith("http") else f"https://t.me/{config.SUPPORT_URL.lstrip('@')}"
        extra_row.append(
            InlineKeyboardButton(
                text="🛟 Yordam",
                url=support_link
            )
        )
    if extra_row:
        buttons.append(extra_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Faqat /admin komandasi orqali adminlarga yuboriladi"""
    buttons = []
    if config.ADMIN_APP_URL.startswith("https://"):
        buttons.append([
            InlineKeyboardButton(
                text="⚙ Admin Panel (Web App)",
                web_app=WebAppInfo(url=config.ADMIN_APP_URL)
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="⚙ Admin Panel (Brauzerda)",
                url=config.ADMIN_APP_URL
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_gate_keyboard(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"➕ {ch.get('title', ch.get('username_or_link'))}",
                url=ch.get("link", "https://t.me")
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="✅ A'zolikni tekshirish",
            callback_data="check_subscription"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
