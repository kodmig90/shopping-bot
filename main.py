import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Загрузка .env
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# /start — регистрация пользователя
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    try:
        result = supabase.from_("users").select("telegram_id").eq("telegram_id", user_id).execute()

        if not result.data:
            supabase.from_("users").insert({
                "telegram_id": user_id,
                "first_name": first_name,
                "username": username
            }).execute()
            logging.info(f"✅ Новый пользователь сохранён: {user_id}")

        await message.answer("Бот работает! Привет 🙂\n\nДоступные команды:\n/add 2 Молоко\n/list\n/delete Молоко")
    except Exception:
        logging.error("❌ Ошибка при обращении к Supabase:", exc_info=True)
        await message.answer("Произошла ошибка при обращении к базе данных.")

# /add — добавление товара
@dp.message_handler(commands=["add"])
async def cmd_add(message: types.Message):
    user_id = message.from_user.id
    try:
        args = message.get_args().split(" ", 1)
        if len(args) < 2:
            await message.answer("❗ Пример: /add 2 Молоко")
            return

        quantity = int(args[0])
        item = args[1]

        supabase.from_("shopping_list").insert({
            "telegram_id": user_id,
            "item": item,
            "quantity": quantity,
            "added_at": datetime.utcnow().isoformat()
        }).execute()

        await message.answer(f"✅ Добавлено: {quantity} × {item}")
    except Exception:
        logging.error("❌ Ошибка при добавлении товара:", exc_info=True)
        await message.answer("Ошибка при добавлении. Проверь формат команды.")

# /list — просмотр списка
@dp.message_handler(commands=["list"])
async def cmd_list(message: types.Message):
    user_id = message.from_user.id
    try:
        result = supabase.from_("shopping_list").select("*").eq("telegram_id", user_id).order("added_at", desc=False).execute()
        items = result.data

        if not items:
            await message.answer("🛒 Список покупок пуст.")
            return

        text = "📝 Твой список покупок:\n"
        for item in items:
            text += f"{item['quantity']} × {item['item']}\n"

        await message.answer(text)
    except Exception:
        logging.error("❌ Ошибка при получении списка:", exc_info=True)
        await message.answer("Ошибка при получении списка.")

# /delete — удаление товара
@dp.message_handler(commands=["delete"])
async def cmd_delete(message: types.Message):
    user_id = message.from_user.id
    try:
        item = message.get_args()
        if not item:
            await message.answer("❗ Пример: /delete Молоко")
            return

        result = supabase.from_("shopping_list").delete().eq("telegram_id", user_id).eq("item", item).execute()
        deleted = result.data

        if deleted:
            await message.answer(f"🗑 Удалено: {item}")
        else:
            await message.answer("❗ Такой товар не найден.")
    except Exception:
        logging.error("❌ Ошибка при удалении товара:", exc_info=True)
        await message.answer("Ошибка при удалении товара.")

# Webhook события
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook установлен")

async def on_shutdown(dispatcher):
    await bot.delete_webhook()
    logging.info("🛑 Webhook удалён")

# Точка входа
if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='0.0.0.0',
        port=int(os.getenv("PORT", 3000))
    )
