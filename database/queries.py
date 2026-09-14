import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func, desc, String
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    User, PricingSetting, Order, Transaction, ChannelRequirement,
    AdminAuditLog, ReferralSetting, PaymentSetting, BroadcastDraft,
    PromoCode, PromoCodeUsage
)

# ================= USER QUERIES ================= #

async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    photo_url: Optional[str] = None,
    referrer_id: Optional[int] = None
) -> User:
    user = await session.get(User, user_id)
    if not user:
        # Check if referrer is valid
        valid_referrer = None
        if referrer_id and referrer_id != user_id:
            ref_user = await session.get(User, referrer_id)
            if ref_user:
                valid_referrer = referrer_id
                ref_user.referrals_count += 1

        user = User(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            photo_url=photo_url,
            referrer_id=valid_referrer,
            balance=0.0
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        # Update details if changed
        updated = False
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if username and user.username != username:
            user.username = username
            updated = True
        if photo_url and user.photo_url != photo_url:
            user.photo_url = photo_url
            updated = True
        if updated:
            await session.commit()
    return user

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)

async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    clean_username = username.lstrip("@").strip()
    res = await session.execute(select(User).where(func.lower(User.username) == clean_username.lower()))
    return res.scalars().first()

async def list_users(session: AsyncSession, search: Optional[str] = None, limit: int = 50) -> List[User]:
    query = select(User).order_by(desc(User.created_at))
    if search:
        search_term = f"%{search.strip().lower()}%"
        query = query.where(
            func.lower(User.first_name).like(search_term) |
            func.lower(User.username).like(search_term) |
            User.id.cast(String).like(search_term)
        )
    res = await session.execute(query.limit(limit))
    return list(res.scalars().all())

async def update_user_balance(
    session: AsyncSession,
    user_id: int,
    amount: float,
    tx_type: str,
    method: str = "balance",
    note: Optional[str] = None
) -> Optional[User]:
    user = await session.get(User, user_id)
    if not user:
        return None
    user.balance += amount
    tx = Transaction(
        user_id=user_id,
        amount=amount,
        tx_type=tx_type,
        method=method,
        status="success",
        note=note
    )
    session.add(tx)
    await session.commit()
    await session.refresh(user)
    return user

# ================= PRICING QUERIES ================= #

async def get_pricing(session: AsyncSession) -> PricingSetting:
    pricing = await session.get(PricingSetting, 1)
    if not pricing:
        pricing = PricingSetting(id=1)
        session.add(pricing)
        await session.commit()
        await session.refresh(pricing)
    return pricing

async def update_pricing(
    session: AsyncSession,
    stars_cost_ton: float,
    ton_rate_uzs: float,
    margin_percent: float,
    star_unit_price_uzs: Optional[float] = None,
    stars_discounts_json: Optional[str] = None,
    premium_prices_json: Optional[str] = None,
    gifts_json: Optional[str] = None
) -> PricingSetting:
    pricing = await get_pricing(session)
    pricing.stars_cost_ton = stars_cost_ton
    pricing.ton_rate_uzs = ton_rate_uzs
    pricing.margin_percent = margin_percent
    if star_unit_price_uzs is not None and star_unit_price_uzs > 0:
        pricing.star_unit_price_uzs = star_unit_price_uzs
    if stars_discounts_json is not None:
        pricing.stars_discounts_json = stars_discounts_json
    if premium_prices_json is not None:
        pricing.premium_prices_json = premium_prices_json
    if gifts_json is not None:
        pricing.gifts_json = gifts_json
    await session.commit()
    await session.refresh(pricing)
    return pricing

def calculate_stars_price(amount: int, pricing: PricingSetting) -> Dict[str, Any]:
    # Determine base unit cost
    if getattr(pricing, "star_unit_price_uzs", None) and pricing.star_unit_price_uzs > 0:
        unit_cost_uzs = pricing.star_unit_price_uzs
    else:
        unit_cost_uzs = pricing.stars_cost_ton * pricing.ton_rate_uzs

    unit_sell_uzs = unit_cost_uzs * (1.0 + (pricing.margin_percent / 100.0))

    base_total = unit_sell_uzs * amount
    cost_total = unit_cost_uzs * amount

    # Apply volume discounts if applicable
    applied_discount = 0.0
    try:
        discounts = json.loads(pricing.stars_discounts_json)
        # sort descending by min_amount
        discounts.sort(key=lambda x: x.get("min_amount", 0), reverse=True)
        for d in discounts:
            if amount >= d.get("min_amount", 0):
                applied_discount = float(d.get("discount_pct", 0))
                break
    except Exception:
        pass

    final_total = base_total * (1.0 - (applied_discount / 100.0))
    return {
        "amount": amount,
        "unit_cost_uzs": round(unit_cost_uzs, 2),
        "unit_sell_uzs": round(unit_sell_uzs, 2),
        "discount_percent": applied_discount,
        "total_price_uzs": round(final_total),
        "cost_total_uzs": round(cost_total)
    }

# ================= ORDERS & TRANSACTIONS ================= #

async def create_order(
    session: AsyncSession,
    user_id: int,
    product_type: str,
    item_title: str,
    amount: int,
    total_price: float,
    cost_price: float,
    recipient_username: Optional[str] = None
) -> Order:
    user = await session.get(User, user_id)
    if not user or user.balance < total_price:
        raise ValueError("Mablag' yetarli emas!")

    # Deduct balance
    user.balance -= total_price
    tx = Transaction(
        user_id=user_id,
        amount=-total_price,
        tx_type="purchase",
        method="balance",
        status="success",
        note=f"{item_title} xaridi"
    )
    session.add(tx)

    # Generate unique order code
    import random
    order_code = f"#{random.randint(10000, 99999)}"

    order = Order(
        order_code=order_code,
        user_id=user_id,
        product_type=product_type,
        item_title=item_title,
        amount=amount,
        unit_price=round(total_price / amount, 2) if amount else total_price,
        total_price=total_price,
        cost_price=cost_price,
        status="done",  # Auto-completed in simulation mode or instant delivery
        recipient_username=recipient_username,
        completed_at=datetime.utcnow()
    )
    session.add(order)
    await session.flush()

    # Process referral bonus if eligible
    bonus, referrer = await process_referral_reward(session, user, total_price)

    await session.commit()
    await session.refresh(order)
    return order, bonus, referrer

async def process_referral_reward(session: AsyncSession, buyer: User, purchase_amount: float):
    if not buyer.referrer_id:
        return 0.0, None
    ref_settings = await session.get(ReferralSetting, 1)
    if not ref_settings:
        return 0.0, None

    # Check minimum purchase threshold
    if ref_settings.require_purchase and purchase_amount < ref_settings.min_purchase_uzs:
        return 0.0, None

    bonus = purchase_amount * (ref_settings.bonus_percent / 100.0)
    referrer = await session.get(User, buyer.referrer_id)
    if referrer and bonus > 0:
        referrer.referral_earnings += bonus
        if ref_settings.auto_reward:
            referrer.balance += bonus
            tx = Transaction(
                user_id=referrer.id,
                amount=bonus,
                tx_type="referral_bonus",
                method="balance",
                status="success",
                note=f"Referal bonusi ({buyer.first_name} xarididan)"
            )
            session.add(tx)
            return bonus, referrer
    return 0.0, None

async def list_user_orders(session: AsyncSession, user_id: int, status: Optional[str] = None) -> List[Order]:
    query = select(Order).where(Order.user_id == user_id).order_by(desc(Order.created_at))
    if status and status != "all":
        query = query.where(Order.status == status)
    res = await session.execute(query)
    return list(res.scalars().all())

async def list_all_orders(session: AsyncSession, search: Optional[str] = None, limit: int = 100) -> List[Order]:
    query = select(Order).order_by(desc(Order.created_at))
    if search:
        s = f"%{search.strip().lower()}%"
        query = query.where(
            Order.order_code.like(s) |
            func.lower(Order.item_title).like(s) |
            Order.user_id.cast(String).like(s)
        )
    res = await session.execute(query.limit(limit))
    return list(res.scalars().all())

async def update_order_status(session: AsyncSession, order_id: int, new_status: str) -> Optional[Order]:
    order = await session.get(Order, order_id)
    if not order:
        return None

    # If cancelling, refund balance
    if new_status == "cancel" and order.status != "cancel":
        user = await session.get(User, order.user_id)
        if user:
            user.balance += order.total_price
            tx = Transaction(
                user_id=user.id,
                amount=order.total_price,
                tx_type="refund",
                method="balance",
                status="success",
                note=f"Bekor qilingan buyurtma uchun qaytarildi: {order.order_code}"
            )
            session.add(tx)

    order.status = new_status
    if new_status == "done":
        order.completed_at = datetime.utcnow()
    await session.commit()
    await session.refresh(order)
    return order

# ================= MANDATORY CHANNELS ================= #

async def list_channels(session: AsyncSession, active_only: bool = False) -> List[ChannelRequirement]:
    query = select(ChannelRequirement).order_by(ChannelRequirement.id)
    if active_only:
        query = query.where(ChannelRequirement.is_active == True, ChannelRequirement.is_detected == False)
    res = await session.execute(query)
    return list(res.scalars().all())

async def add_or_update_channel(
    session: AsyncSession,
    username_or_link: str,
    title: str,
    req_type: str = "ordinary",
    chat_id: Optional[int] = None,
    is_detected: bool = False
) -> ChannelRequirement:
    # Check if already exists
    res = await session.execute(
        select(ChannelRequirement).where(ChannelRequirement.username_or_link == username_or_link)
    )
    ch = res.scalars().first()
    if ch:
        ch.title = title
        ch.req_type = req_type
        if chat_id:
            ch.chat_id = chat_id
        ch.is_active = True
        ch.is_detected = is_detected
    else:
        ch = ChannelRequirement(
            chat_id=chat_id,
            username_or_link=username_or_link,
            title=title,
            req_type=req_type,
            is_active=True,
            is_detected=is_detected
        )
        session.add(ch)
    await session.commit()
    await session.refresh(ch)
    return ch

async def delete_channel(session: AsyncSession, channel_id: int):
    ch = await session.get(ChannelRequirement, channel_id)
    if ch:
        await session.delete(ch)
        await session.commit()

# ================= ADMINS & AUDIT LOGS ================= #

async def log_admin_action(
    session: AsyncSession,
    admin_id: int,
    action: str,
    details: Optional[str] = None,
    admin_username: Optional[str] = None
):
    log = AdminAuditLog(
        admin_id=admin_id,
        admin_username=admin_username,
        action=action,
        details=details
    )
    session.add(log)
    await session.commit()

async def list_audit_logs(session: AsyncSession, limit: int = 30) -> List[AdminAuditLog]:
    res = await session.execute(
        select(AdminAuditLog).order_by(desc(AdminAuditLog.created_at)).limit(limit)
    )
    return list(res.scalars().all())

async def list_admins(session: AsyncSession) -> List[User]:
    res = await session.execute(
        select(User).where(User.role != "user").order_by(desc(User.created_at))
    )
    return list(res.scalars().all())

async def set_user_role(session: AsyncSession, user_id: int, new_role: str) -> Optional[User]:
    user = await session.get(User, user_id)
    if user:
        user.role = new_role
        await session.commit()
        await session.refresh(user)
    return user

# ================= BROADCAST AUDIENCE ================= #

async def get_broadcast_recipients(session: AsyncSession, segment: str = "all") -> List[int]:
    if segment == "all":
        res = await session.execute(select(User.id).where(User.is_blocked == False))
        return list(res.scalars().all())
    elif segment == "non_buyers":
        # Users with 0 orders
        subq = select(Order.user_id).distinct()
        res = await session.execute(select(User.id).where(User.id.not_in(subq), User.is_blocked == False))
        return list(res.scalars().all())
    elif segment == "active":
        # Users with at least 1 completed order
        subq = select(Order.user_id).where(Order.status == "done").distinct()
        res = await session.execute(select(User.id).where(User.id.in_(subq), User.is_blocked == False))
        return list(res.scalars().all())
    elif segment == "referral":
        # Users who were invited by someone
        res = await session.execute(select(User.id).where(User.referrer_id.isnot(None), User.is_blocked == False))
        return list(res.scalars().all())
    return []

# ================= PROMO CODES ================= #

async def list_promo_codes(session: AsyncSession) -> List[PromoCode]:
    res = await session.execute(select(PromoCode).order_by(desc(PromoCode.created_at)))
    return list(res.scalars().all())

async def create_promo_code(
    session: AsyncSession,
    code: str,
    reward_type: str = "discount_percent",
    reward_value: float = 10.0,
    max_uses: int = 100,
    min_order_amount: float = 0.0,
    is_active: bool = True,
    expires_at: Optional[datetime] = None
) -> PromoCode:
    clean_code = code.strip().upper()
    existing = await session.execute(select(PromoCode).where(PromoCode.code == clean_code))
    if existing.scalars().first():
        raise ValueError("Bu promo-kod allaqachon mavjud!")

    promo = PromoCode(
        code=clean_code,
        reward_type=reward_type,
        reward_value=reward_value,
        max_uses=max_uses,
        current_uses=0,
        min_order_amount=min_order_amount,
        is_active=is_active,
        expires_at=expires_at
    )
    session.add(promo)
    await session.commit()
    await session.refresh(promo)
    return promo

async def delete_promo_code(session: AsyncSession, promo_id: int) -> bool:
    promo = await session.get(PromoCode, promo_id)
    if promo:
        await session.delete(promo)
        await session.commit()
        return True
    return False

async def toggle_promo_code(session: AsyncSession, promo_id: int) -> Optional[PromoCode]:
    promo = await session.get(PromoCode, promo_id)
    if promo:
        promo.is_active = not promo.is_active
        await session.commit()
        await session.refresh(promo)
    return promo

async def apply_promo_code(
    session: AsyncSession,
    code: str,
    user_id: int,
    order_total: float = 0.0
) -> Dict[str, Any]:
    clean_code = code.strip().upper()
    res = await session.execute(select(PromoCode).where(PromoCode.code == clean_code))
    promo = res.scalars().first()

    if not promo:
        return {"success": False, "detail": "Promo-kod topilmadi"}

    if not promo.is_active:
        return {"success": False, "detail": "Ushbu promo-kod faol emas"}

    if promo.expires_at and datetime.utcnow() > promo.expires_at:
        return {"success": False, "detail": "Promo-kodning amal qilish muddati tugagan"}

    if promo.current_uses >= promo.max_uses:
        return {"success": False, "detail": "Promo-koddan foydalanish limiti tugagan"}

    # Check if user already used this promo code
    usage_res = await session.execute(
        select(PromoCodeUsage).where(
            PromoCodeUsage.promo_code_id == promo.id,
            PromoCodeUsage.user_id == user_id
        )
    )
    if usage_res.scalars().first():
        return {"success": False, "detail": "Siz bu promo-koddan allaqachon foydalangansiz"}

    if promo.reward_type == "discount_percent":
        if order_total < promo.min_order_amount:
            return {
                "success": False,
                "detail": f"Ushbu chegirma faqat kamida {promo.min_order_amount:,.0f} so'mlik xaridlar uchun amal qiladi"
            }
        discount_sum = round(order_total * (promo.reward_value / 100.0))
        new_total = max(0.0, order_total - discount_sum)

        # Record usage
        promo.current_uses += 1
        usage = PromoCodeUsage(
            promo_code_id=promo.id,
            user_id=user_id,
            benefit_amount=discount_sum
        )
        session.add(usage)
        await session.commit()

        return {
            "success": True,
            "reward_type": "discount_percent",
            "percent": promo.reward_value,
            "discount_amount": discount_sum,
            "original_total": order_total,
            "new_total": new_total,
            "message": f"🎉 {promo.reward_value:.0f}% chegirma qo'llandi! (-{discount_sum:,.0f} so'm)"
        }

    elif promo.reward_type == "balance_bonus":
        bonus_sum = promo.reward_value
        updated_user = await update_user_balance(
            session=session,
            user_id=user_id,
            amount=bonus_sum,
            tx_type="topup",
            method="balance",
            note=f"Promo-kod ({clean_code}) orqali bonus"
        )

        promo.current_uses += 1
        usage = PromoCodeUsage(
            promo_code_id=promo.id,
            user_id=user_id,
            benefit_amount=bonus_sum
        )
        session.add(usage)
        await session.commit()

        return {
            "success": True,
            "reward_type": "balance_bonus",
            "bonus_amount": bonus_sum,
            "new_balance": round(updated_user.balance),
            "message": f"🎁 Hamyoningizga +{bonus_sum:,.0f} so'm bonus qo'shildi!"
        }

    return {"success": False, "detail": "Noma'lum promo-kod turi"}

