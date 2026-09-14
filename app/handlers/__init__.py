from aiogram import Dispatcher
from app.handlers import users, groups, channels

def setup(dp: Dispatcher):
    users.setup(dp)
    channels.setup(dp)
