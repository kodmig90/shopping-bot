import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Токен и вебхук
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")  # например: https://shopping-bot.onrender.com
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Логирование
logging.basicConfig(level=logging.INFO)

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Бот работает! Привет 🙂")

# При запуске
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("Webhook установлен")

# При остановке
async def on_shutdown(dispatcher):
    await bot.delete_webhook()
    logging.info("Webhook удалён")

# Запуск
if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",  # ← ОБЯЗАТЕЛЬНО для Render
        port=int(os.environ.get('PORT', 5000))  # ← Render подставляет свой порт через переменную окружения
    )
