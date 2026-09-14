from aiogram import Dispatcher
from .start import router as user_router
from .help import router as help_router
from .admin_forward import router as admin_forward_router

def setup(dp: Dispatcher):
    dp.include_routers(
        user_router,
        admin_forward_router,
        help_router
    )