from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from data import config

def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = []

    # Telegram WebAppInfo faqat HTTPS havolalarini qabul qiladi.
    # Agar havola https bo'lsa - Mini App sifatida Telegram ichida ochiladi,
    # Agar http (localhost) bo'lsa - xatolik bermasligi uchun oddiy havola sifatida beriladi.
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

    if is_admin:
        if config.ADMIN_APP_URL.startswith("https://"):
            buttons.append([
                InlineKeyboardButton(
                    text="⚙ Admin Panel",
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

    buttons.append([
        InlineKeyboardButton(
            text="📣 Yangiliklar",
            url="https://t.me/stellar_news"
        ),
        InlineKeyboardButton(
            text="🛟 Yordam",
            url="https://t.me/stellar_support"
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
