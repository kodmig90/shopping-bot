import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv
from supabase import create_client, Client

# Загрузка .env
load_dotenv()

# Настройки из переменных окружения
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase клиент
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Бот
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Команда /start
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    logging.info(f"🔍 SUPABASE_URL: {SUPABASE_URL}")
    logging.info("🔍 Trying to query Supabase...")

    # Проверяем, есть ли пользователь
    result = supabase.from_("users").select("telegram_id").eq("telegram_id", user_id).execute()

    if not result.data:
        # Если нет — добавляем
        insert_data = {
            "telegram_id": user_id,
            "first_name": first_name,
            "username": username
        }
        supabase.from_("users").insert(insert_data).execute()
        logging.info(f"✅ Новый пользователь сохранён: {user_id}")

    await message.answer("Бот работает! Привет 🙂")

# При запуске
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook установлен")

# При завершении
async def on_shutdown(dispatcher):
    await bot.delete_webhook()
    logging.info("🛑 Webhook удалён")

# Запуск
if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
