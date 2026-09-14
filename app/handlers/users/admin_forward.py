from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import AsyncSessionLocal
from database import queries
from data import config

router = Router()

def is_admin_check(user_id: int) -> bool:
    return str(user_id) in config.ADMINS

@router.message(F.forward_origin)
async def handle_admin_forward(message: Message):
    """
    Handles forwarded messages by admins:
    1. If forwarded from a user -> Admin nomination candidate flow (TZ 3.7)
    2. If forwarded from a channel/bot -> Broadcast draft intake (TZ 3.5)
    """
    if not is_admin_check(message.from_user.id):
        return

    origin = message.forward_origin
    origin_type = origin.type

    # Forwarded from User
    if origin_type == "user":
        sender = origin.sender_user
        uid = sender.id
        name = sender.full_name
        uname = f"@{sender.username}" if sender.username else "mavjud emas"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 Super Admin", callback_data=f"make_adm:{uid}:super_admin"),
                InlineKeyboardButton(text="₮ Narx Admin", callback_data=f"make_adm:{uid}:price_admin")
            ],
            [
                InlineKeyboardButton(text="🛟 Support Admin", callback_data=f"make_adm:{uid}:support_admin"),
                InlineKeyboardButton(text="📣 Marketing Admin", callback_data=f"make_adm:{uid}:marketing_admin")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_adm")
            ]
        ])

        await message.reply(
            text=(
                f"👤 <b>Adminlikka nomzod aniqlandi!</b>\n\n"
                f"Ism: <b>{name}</b>\n"
                f"Username: {uname}\n"
                f"User ID: <code>{uid}</code>\n\n"
                f"Ushbu foydalanuvchiga qaysi rolni bermoqchisiz?"
            ),
            reply_markup=kb
        )

    # Forwarded from Channel or Chat
    elif origin_type in ["channel", "chat"]:
        chat = getattr(origin, "chat", None)
        title = chat.title if chat else "Kanal"
        msg_id = getattr(origin, "message_id", message.message_id)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Barcha foydalanuvchilarga yuborish", callback_data=f"send_bc_fwd:{msg_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_adm")
            ]
        ])

        await message.reply(
            text=(
                f"📥 <b>Broadcast uchun post qabul qilindi!</b>\n\n"
                f"Manba: <b>{title}</b>\n"
                f"Xabar ID: <code>{msg_id}</code>\n\n"
                f"Ushbu xabarni barcha foydalanuvchilarga forward / copyMessage orqali tarqatishni xohlaysizmi?"
            ),
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("make_adm:"))
async def cb_assign_admin(callback: CallbackQuery):
    parts = callback.data.split(":")
    uid = int(parts[1])
    role = parts[2]

    async with AsyncSessionLocal() as session:
        # Check if user exists in db
        user = await queries.get_user_by_id(session, uid)
        if not user:
            user = await queries.get_or_create_user(
                session=session,
                user_id=uid,
                first_name=f"Admin {uid}"
            )

        await queries.set_user_role(session, uid, role)
        await queries.log_admin_action(
            session=session,
            admin_id=callback.from_user.id,
            admin_username=callback.from_user.username,
            action=f"Yangi admin tayinladi (Forward orqali): ID {uid}",
            details=f"Rol: {role}"
        )

    await callback.message.edit_text(
        text=f"✅ Foydalanuvchi (ID: <code>{uid}</code>) muvaffaqiyatli <b>{role}</b> etib tayinlandi!"
    )

@router.callback_query(F.data == "cancel_adm")
async def cb_cancel_adm(callback: CallbackQuery):
    await callback.message.edit_text("Amal bekor qilindi.")
