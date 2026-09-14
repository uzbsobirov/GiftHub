from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import CommandStart, CommandObject
from database.db import AsyncSessionLocal
from database import queries
from app.keyboards.inline import get_main_menu_keyboard, get_gate_keyboard
from app.keyboards.reply import get_reply_main_keyboard
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

    # First send reply keyboard so it's permanently pinned at the bottom
    await message.answer(
        text="Quyidagi menyu orqali do'konga o'ting:",
        reply_markup=get_reply_main_keyboard(is_admin=is_admin)
    )

    # Then send main menu inline card
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )

@router.message(F.text.in_(["👤 Profil", "Profil"]))
async def user_profile_msg(message: Message):
    async with AsyncSessionLocal() as session:
        user = await queries.get_user_by_id(session, message.from_user.id)
        bal = round(user.balance) if user else 0
        ref_count = user.referrals_count if user else 0
    await message.answer(
        f"👤 <b>Sizning profilingiz:</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💰 Balansingiz: <b>{bal:,} so'm</b>\n"
        f"👥 Taklif qilgan do'stlaringiz: <b>{ref_count} ta</b>\n\n"
        f"Barcha xizmatlardan foydalanish uchun <b>⭐ Do'konni ochish</b> tugmasini bosing.",
        reply_markup=get_main_menu_keyboard(is_admin=(user and user.role != 'user'))
    )

@router.message(F.text.in_(["🛟 Yordam", "Yordam"]))
async def user_help_msg(message: Message):
    await message.answer(
        "🛟 <b>Qo'llab-quvvatlash xizmati</b>\n\n"
        "Savollaringiz yoki to'lov bo'yicha yordam kerak bo'lsa, ma'muriyatga murojaat qiling:\n"
        "👉 @stellar_support\n"
        "📣 Yangiliklar: @stellar_news"
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
