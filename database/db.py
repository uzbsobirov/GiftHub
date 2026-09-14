import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from data import config
from database.models import (
    Base, PricingSetting, ReferralSetting, PaymentSetting, ChannelRequirement, User, PromoCode
)

# SQLite path check if relative
db_url = config.DB_URL
if db_url.startswith("sqlite+aiosqlite:///"):
    relative_path = db_url.replace("sqlite+aiosqlite:///", "")
    if not os.path.isabs(relative_path):
        abs_db_path = os.path.join(config.BASE_DIR, relative_path).replace("\\", "/")
        db_url = f"sqlite+aiosqlite:///{abs_db_path}"
    data_dir = os.path.dirname(db_url.replace("sqlite+aiosqlite:///", ""))
    os.makedirs(data_dir, exist_ok=True)

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize default settings if not exists
    async with AsyncSessionLocal() as session:
        # Check PricingSetting
        pricing = await session.get(PricingSetting, 1)
        if not pricing:
            pricing = PricingSetting(
                id=1,
                stars_cost_ton=0.0021,
                ton_rate_uzs=14800.0,
                margin_percent=15.0
            )
            session.add(pricing)

        # Check ReferralSetting
        referral = await session.get(ReferralSetting, 1)
        if not referral:
            referral = ReferralSetting(
                id=1,
                bonus_percent=5.0,
                min_purchase_uzs=20000.0,
                auto_reward=True,
                require_purchase=True
            )
            session.add(referral)

        # Check PaymentSetting
        payment = await session.get(PaymentSetting, 1)
        if not payment:
            payment = PaymentSetting(
                id=1,
                click_active=True,
                payme_active=True,
                autopaycard_active=False
            )
            session.add(payment)

        # Ensure default demo channels
        from sqlalchemy import select
        res = await session.execute(select(ChannelRequirement))
        if not res.scalars().first():
            ch1 = ChannelRequirement(
                username_or_link="@stellar_news",
                title="Stellar Rasmiy Yangiliklar",
                req_type="ordinary",
                is_active=True
            )
            ch2 = ChannelRequirement(
                username_or_link="@stellar_chat",
                title="Stellar VIP Guruh",
                req_type="join_request",
                is_active=True
            )
            session.add_all([ch1, ch2])

        # Seed default demo promo codes
        res_promo = await session.execute(select(PromoCode))
        if not res_promo.scalars().first():
            p1 = PromoCode(
                code="STELLAR10",
                reward_type="discount_percent",
                reward_value=10.0,
                max_uses=500,
                min_order_amount=5000.0,
                is_active=True
            )
            p2 = PromoCode(
                code="WELCOME5K",
                reward_type="balance_bonus",
                reward_value=5000.0,
                max_uses=1000,
                is_active=True
            )
            session.add_all([p1, p2])

        # Seed super admins from config
        for admin_id_str in config.ADMINS:
            try:
                admin_id = int(admin_id_str.strip())
                user = await session.get(User, admin_id)
                if not user:
                    user = User(
                        id=admin_id,
                        first_name="Super Admin",
                        username="superadmin",
                        role="super_admin",
                        balance=500000.0
                    )
                    session.add(user)
                else:
                    if user.role != "super_admin":
                        user.role = "super_admin"
            except ValueError:
                pass

        await session.commit()
