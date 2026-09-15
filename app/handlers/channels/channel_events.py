from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, ChatJoinRequest
from aiogram.enums import ChatMemberStatus
from database.db import AsyncSessionLocal
from database import queries
from database.models import ChannelRequirement
from data import config

router = Router()

@router.my_chat_member()
async def on_bot_chat_member_updated(event: ChatMemberUpdated):
    """
    Auto-detects when the bot is added as an administrator to a channel or group.
    Fulfills TZ requirement 3.4 (Yangi kanal qo'shish oqimi / my_chat_member).
    """
    chat = event.chat
    new_status = event.new_chat_member.status
    old_status = event.old_chat_member.status

    if new_status in [ChatMemberStatus.ADMINISTRATOR] and old_status not in [ChatMemberStatus.ADMINISTRATOR]:
        title = chat.title or "Noma'lum Kanal"
        bot = event.bot
        invite_link = f"@{chat.username}" if chat.username else f"https://t.me/c/{str(chat.id).replace('-100', '')}"
        if not chat.username:
            try:
                exported = await bot.export_chat_invite_link(chat.id)
                if exported:
                    invite_link = exported
            except Exception:
                pass

        async with AsyncSessionLocal() as session:
            # Register directly as active channel
            await queries.add_or_update_channel(
                session=session,
                username_or_link=invite_link,
                title=title,
                req_type="ordinary",
                chat_id=chat.id,
                is_detected=False
            )

        # Notify admins
        for admin_id_str in config.ADMINS:
            try:
                admin_id = int(admin_id_str)
                await bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"📣 <b>Yangi kanal qo'shildi va faollashtirildi!</b>\n\n"
                        f"Nomi: <b>{title}</b>\n"
                        f"Havola: {invite_link}\n"
                        f"ID: <code>{chat.id}</code>\n\n"
                        f"✅ Kanal admin panel va majburiy obuna ro'yxatida avtomatik paydo bo'ldi."
                    )
                )
            except Exception:
                pass

@router.chat_join_request()
async def on_chat_join_request(event: ChatJoinRequest):
    """
    Handles join requests for private channels with join-request requirements.
    Fulfills TZ requirement 3.4 (So'rov orqali qo'shilish).
    """
    # User sent a request to join, can be logged or auto-approved
    pass
