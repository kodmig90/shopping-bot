import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from supabase import create_client, Client

# Настройки из переменных окружения (берутся из Render)
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

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    logger.info("🔍 SUPABASE_URL: %s", SUPABASE_URL)
    logger.info("🔍 Trying to query Supabase for user %s...", user_id)

    try:
        result = supabase.from_("users").select("telegram_id").eq("telegram_id", user_id).execute()

        if not result.data:
            insert_data = {
                "telegram_id": user_id,
                "first_name": first_name,
                "username": username
            }
            supabase.from_("users").insert(insert_data).execute()
            logger.info("✅ Новый пользователь сохранён: %s", user_id)
        else:
            logger.info("👤 Пользователь уже есть: %s", user_id)

        await message.answer("Бот работает! Привет 🙂")

    except Exception as e:
        logger.exception("❌ Ошибка при обращении к Supabase:")
        await message.answer("Произошла ошибка при обращении к базе данных.")

# При запуске
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("✅ Webhook установлен")

# При завершении
async def on_shutdown(dispatcher):
    await bot.delete_webhook()
    logger.info("🛑 Webhook удалён")

# Запуск
if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
