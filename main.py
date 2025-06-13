import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo
from aiogram.utils.executor import start_webhook
from aiogram.dispatcher.webhook import get_new_configured_app

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Бот и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app_button = types.KeyboardButton(
        text="🛒 Открыть список покупок",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    keyboard.add(web_app_button)
    await message.answer("Привет! Нажми кнопку ниже, чтобы открыть список покупок:", reply_markup=keyboard)

# При запуске
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

# При выключении
async def on_shutdown(dp):
    await bot.delete_webhook()

# Запуск
if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path='')  # 👈 важно!
    start_webhook(
        dispatcher=dp,
        webhook_path='',
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        app=app  # 👈 сюда тоже
    )
