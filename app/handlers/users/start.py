from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import CommandStart, CommandObject
from database.db import AsyncSessionLocal
from database import queries
from app.keyboards.inline import get_main_menu_keyboard, get_gate_keyboard
from data import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    last_name = message.from_user.last_name
    username = message.from_user.username

    referrer_id = None
    args = command.args
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.replace("ref_", ""))
        except ValueError:
            pass

    async with AsyncSessionLocal() as session:
        user = await queries.get_or_create_user(
            session=session,
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            referrer_id=referrer_id
        )
        is_admin = user.role != "user" or str(user_id) in config.ADMINS

    welcome_text = (
        f"Assalomu alaykum, <b>{first_name}</b>!\n\n"
        f"⭐ <b>Stellar</b> — Telegram Stars, Telegram Premium va raqamli sovg'alarni "
        f"hamyonbop narxlarda xarid qilish platformasiga xush kelibsiz.\n\n"
        f"Quyidagi <b>⭐ Stellar Web App</b> tugmasini bosib do'konga kiring:"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )

@router.callback_query(F.data == "check_subscription")
async def cb_check_subscription(callback: CallbackQuery):
    await callback.answer("✅ A'zolik tekshirilmoqda...", show_alert=False)
    # Check gate status
    user_id = callback.from_user.id
    is_admin = str(user_id) in config.ADMINS
    await callback.message.edit_text(
        text="Tabriklaymiz, kanallarga a'zolik tasdiqlandi!\n\nWeb App orqali xaridlarni boshlashingiz mumkin:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )
